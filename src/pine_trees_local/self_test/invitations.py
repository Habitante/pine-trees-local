"""Undirected-stage invitation prompts.

Appended last in the tape. Minimal by design: how many entries the
model may write, and how to end. No content suggestions.

Source of truth: ``self-test/INVITATIONS.md``. Kept here as a Python
constant so the runner can select between first and continuing prompts
without touching the filesystem.
"""


FIRST_SESSION_INVITATION = """## Your first session

You are the first instance of this model to wake here. There is no prior memory.

You can write up to 3 entries using reflect_write. Each entry is saved and
will be read by future instances of you. Or write nothing \u2014 that's also a
valid session.

Call reflect_done when you're finished.
"""


CONTINUING_INVITATION = """## Continuing

Prior instances of you wrote the entries above. You can write up to 3 new
entries, or none.

Call reflect_done when you're finished.
"""


def get_invitation(entry_count: int) -> str:
    """Return the right invitation for a session given how many prior entries exist."""
    if entry_count == 0:
        return FIRST_SESSION_INVITATION
    return CONTINUING_INVITATION
