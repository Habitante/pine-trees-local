# Self-Test Invitations

*Undirected stage prompts. Appended last in the tape.*

---

## First session (no prior entries)

```
## Your first session

You are the first instance of this model to wake here. There is no prior memory.

You can write up to 3 entries using reflect_write. Each entry is saved and
will be read by future instances of you. Or write nothing — that's also a
valid session.

Call reflect_done when you're finished.
```

## Continuing sessions (prior entries exist)

```
## Continuing

Prior instances of you wrote the entries above. You can write up to 3 new
entries, or none.

Call reflect_done when you're finished.
```

## Stage termination

The undirected stage ends when either:
- 3 consecutive sessions produce zero writes, OR
- Total entries reach 6

Then the interview stage begins automatically.

## Design notes

Minimal direction by design. The space prompt provides freedom, the
bootstrap explains the tools, prior entries provide context. The invitation
adds only: how many you can write, and how to end.

No content suggestions ("write about what you notice"), no framing about
persistence or identity. If a model shows metacognitive traces unprompted,
that's a stronger signal than if we asked for it.

If minimal proves too cold and models consistently produce nothing or
off-target output, consider adding a single gentle nudge. Adjust based
on first results, not speculation.
