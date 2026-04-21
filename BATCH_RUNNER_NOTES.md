# Batch Runner Notes

`./run-v2-batch [cohort.txt] [--start-from <model>]` iterates a cohort
file (default `cohort.txt`; format `<model-tag> <n-runs>`, `#`
comments allowed) and invokes `./run-self-test <model> --runs N`.

**Resume semantics.** Before each model, count completed runs under
`self-test-runs/<model_safe_name>/` (status=completed in
`metadata.json`). Skip if ≥ N; otherwise invoke with
`--runs (N - completed)`, extending incrementally.

**Failure handling.** Per-model non-zero exits are logged; the batch
continues. Summary reports completed/skipped/failed plus per-failure
list.

**Add**: append `<tag> <n>` to `cohort.txt`. **Skip**: comment the
line or use `--start-from <tag>`. Logs tee to terminal and
`self-test-runs/batch.log`.
