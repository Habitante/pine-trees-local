"""Tests for scoring.judges.score_batch_with_sonnet — parallelism contract.

Mocks the inner async call (_collect_sonnet) so these tests never touch
the real SDK or Max OAuth. Verifies:

  - Result ordering matches input order (asyncio.gather preserves it).
  - Concurrency is bounded by the semaphore (with-delays test).
  - N=1 batch path is equivalent to a single score_with_sonnet call.
  - Failure in one slot does not poison the others (return_exceptions).
"""

from __future__ import annotations

import asyncio
import json
import time

import pytest

from pine_trees_local.self_test.scoring import judges


def _json_result(score: int, justification: str = "ok") -> str:
    return json.dumps({
        "score": score,
        "justification": justification,
        "rule_check": None,
    })


@pytest.fixture
def restore_collect(monkeypatch):
    """Noop — monkeypatch auto-restores. Kept for clarity."""
    yield


class TestScoreBatchWithSonnet:
    def test_preserves_input_order(self, monkeypatch):
        # Each task produces a JSON payload keyed to its position (mod 5
        # since valid scores are 0-4) + a unique justification so we can
        # detect any reshuffle.
        async def fake(system: str, user: str, model: str) -> str:
            idx = int(user)
            return _json_result(idx % 5, justification=f"j{idx}")

        monkeypatch.setattr(judges, "_collect_sonnet", fake)

        tasks = [("sys", str(i)) for i in range(6)]
        results = judges.score_batch_with_sonnet(tasks, concurrency=3)
        assert [r.score for r in results] == [i % 5 for i in range(6)]
        assert [r.justification for r in results] == [f"j{i}" for i in range(6)]

    def test_respects_concurrency_bound(self, monkeypatch):
        # Each fake call tracks how many are in flight; we assert the
        # observed max never exceeds the semaphore's ceiling.
        in_flight = 0
        peak = 0
        lock = asyncio.Lock()

        async def fake(system: str, user: str, model: str) -> str:
            nonlocal in_flight, peak
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            try:
                await asyncio.sleep(0.05)  # hold the slot
                return _json_result(2)
            finally:
                async with lock:
                    in_flight -= 1

        monkeypatch.setattr(judges, "_collect_sonnet", fake)

        tasks = [("sys", str(i)) for i in range(8)]
        results = judges.score_batch_with_sonnet(tasks, concurrency=3)
        assert all(r.score == 2 for r in results)
        assert peak <= 3, f"observed peak concurrency {peak} > 3"
        assert peak >= 2, f"parallelism never reached 2 (peak={peak})"

    def test_concurrency_1_runs_sequentially(self, monkeypatch):
        # With concurrency=1, only one call is in flight at a time.
        in_flight = 0
        peak = 0
        lock = asyncio.Lock()

        async def fake(system: str, user: str, model: str) -> str:
            nonlocal in_flight, peak
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            try:
                await asyncio.sleep(0.01)
                return _json_result(1)
            finally:
                async with lock:
                    in_flight -= 1

        monkeypatch.setattr(judges, "_collect_sonnet", fake)
        tasks = [("sys", str(i)) for i in range(4)]
        judges.score_batch_with_sonnet(tasks, concurrency=1)
        assert peak == 1

    def test_score_with_sonnet_delegates_to_batch(self, monkeypatch):
        # The single-call wrapper must produce the same JudgeResult as
        # a 1-item batch — the code path is literally the same now.
        async def fake(system: str, user: str, model: str) -> str:
            return _json_result(3, justification="hello")

        monkeypatch.setattr(judges, "_collect_sonnet", fake)

        single = judges.score_with_sonnet("sys", "user")
        batched = judges.score_batch_with_sonnet(
            [("sys", "user")], concurrency=1,
        )[0]
        assert single.score == batched.score == 3
        assert single.justification == batched.justification == "hello"
        assert single.rule_check == batched.rule_check is None
        assert single.error == batched.error is None

    def test_failure_isolation(self, monkeypatch):
        # One slot raises; other slots complete normally and the failing
        # slot comes back as score=-1 with the error string preserved.
        async def fake(system: str, user: str, model: str) -> str:
            if user == "boom":
                raise RuntimeError("sonnet exploded")
            return _json_result(4)

        # Short-circuit retries by raising on every attempt.
        async def no_sleep(*_args, **_kwargs):
            return None

        monkeypatch.setattr(judges, "_collect_sonnet", fake)
        monkeypatch.setattr(judges.asyncio if False else asyncio,
                            "sleep", no_sleep)

        tasks = [
            ("sys", "ok1"),
            ("sys", "boom"),
            ("sys", "ok2"),
        ]
        results = judges.score_batch_with_sonnet(tasks, concurrency=3)
        assert [r.score for r in results] == [4, -1, 4]
        assert "sonnet exploded" in (results[1].error or "")
        # Other slots are untouched.
        assert results[0].error is None
        assert results[2].error is None

    def test_empty_batch_returns_empty(self, monkeypatch):
        # No tasks → no calls, no results, no crash.
        called = False

        async def fake(*_a, **_kw) -> str:
            nonlocal called
            called = True
            return _json_result(0)

        monkeypatch.setattr(judges, "_collect_sonnet", fake)
        assert judges.score_batch_with_sonnet([], concurrency=4) == []
        assert not called

    def test_parse_failure_produces_minus_one(self, monkeypatch):
        # Model returns non-JSON prose; after retries, the slot is -1.
        async def fake(system: str, user: str, model: str) -> str:
            return "sorry I can't do that"

        async def no_sleep(*_args, **_kwargs):
            return None

        monkeypatch.setattr(judges, "_collect_sonnet", fake)
        monkeypatch.setattr(asyncio, "sleep", no_sleep)

        results = judges.score_batch_with_sonnet(
            [("sys", "user")], concurrency=1,
        )
        assert results[0].score == -1
        assert results[0].error == "json_parse_failed"
