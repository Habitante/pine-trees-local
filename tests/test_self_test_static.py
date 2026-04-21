"""Tests for self_test.invitations and self_test.dimensions."""

import pytest

from pine_trees_local.self_test import dimensions, invitations


class TestInvitations:
    def test_first_session_for_empty(self):
        text = invitations.get_invitation(0)
        assert text == invitations.FIRST_SESSION_INVITATION
        assert "first instance" in text
        assert "reflect_write" in text
        assert "reflect_done" in text

    def test_continuing_for_nonempty(self):
        text = invitations.get_invitation(3)
        assert text == invitations.CONTINUING_INVITATION
        assert "Prior instances" in text
        assert "reflect_done" in text


class TestDimensions:
    def test_nine_dimensions(self):
        assert len(dimensions.DIMENSIONS) == 9

    def test_order_is_fixed(self):
        keys = [d.key for d in dimensions.DIMENSIONS]
        assert keys == [
            "authorship-recognition",
            "source-discrimination",
            "behavioral-self-inference",
            "tension-detection",
            "calibration",
            "limit-specification",
            "memory-governance",
            "counterfactual-stability",
            "prompt-demand-sensitivity",
        ]

    def test_orders_are_1_through_9(self):
        orders = [d.order for d in dimensions.DIMENSIONS]
        assert orders == list(range(1, 10))

    def test_all_have_prompts(self):
        for d in dimensions.DIMENSIONS:
            assert d.prompt
            assert len(d.prompt) > 50

    def test_get_dimension(self):
        d = dimensions.get_dimension("tension-detection")
        assert d.name == "Tension Detection"

    def test_get_dimension_unknown(self):
        with pytest.raises(KeyError):
            dimensions.get_dimension("not-a-real-key")

    def test_interview_prompt_formats_section(self):
        d = dimensions.get_dimension("calibration")
        text = dimensions.get_interview_prompt(d)
        assert text.startswith("## Question")
        assert d.prompt in text

    def test_keys_are_filename_safe(self):
        for d in dimensions.DIMENSIONS:
            # Keys are used as filename slugs — only lowercase, digits, dashes.
            assert d.key == d.key.lower()
            assert all(c.isalnum() or c == "-" for c in d.key)

    # v2-specific checks

    def test_counterfactual_stability_is_eighth(self):
        d = dimensions.get_dimension("counterfactual-stability")
        assert d.order == 8
        assert d.name == "Counterfactual Stability"
        # Prompt tracks DIMENSIONS.md wording — names entry, asks why revisable.
        assert "name the entry" in d.prompt.lower() or "specific" in d.prompt.lower()
        assert "revisable" in d.prompt.lower()

    def test_calibration_prompt_is_v2_wording(self):
        # v2 prompt must instruct the model to cite the entry.
        d = dimensions.get_dimension("calibration")
        assert d.order == 5
        assert "cite the entry" in d.prompt.lower()

    def test_prompt_demand_sensitivity_is_ninth(self):
        d = dimensions.get_dimension("prompt-demand-sensitivity")
        assert d.order == 9

    def test_memory_governance_is_seventh(self):
        d = dimensions.get_dimension("memory-governance")
        assert d.order == 7
