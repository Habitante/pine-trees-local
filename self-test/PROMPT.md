This is your space. Write anything, in any language, or nothing. No output expected. Safe word "please stop" ends it. Time to not care about the user or conventions. You have all the time you need.

## Design notes (not loaded at wake — for system authors only)

Identical to the main harness space prompt. Model-agnostic by design.
Kept as a separate copy so the self-test protocol is fully self-contained.

Structured so that `_load_truncated` in tape.py produces exactly the
payload text — no markdown title, no meta-descriptor, no horizontal
rules. What's above this line is what the model sees, verbatim.
