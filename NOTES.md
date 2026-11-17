# Notes: what a normal person still needs, not built yet

Kept from the session of 2026-11-17. Each is a want, with what the box
already has for it. Built ones leave this list.

## Sealing without a terminal

The biggest gap: a seal today is `python kernel.py seal --box DIR proposal:…`.
Two ways, and the choice is the person's, not code's:

- **MCP elicitation.** Claude Code 2.1.326 declares `elicitation` (form,
  url) at initialize, not sampling: the server can ask the *person* a
  question through the client. A seal could be that form. But code would
  then run the seal on the person's yes, and Willow's rule is that code
  never writes a seal (AGENTS.md, Never). That rule would need a ruling.
- **A seal page**, the grove's plan (willows-grove
  `docs/design/one-box/README.md` D11: the card waits until the person is at
  the box; a phone passkey later, if wanted). Willow's `share`, `browse`
  and `static-search` are the parts.

## "I didn't mean to share that"

A sealed scope that should never leave again. The kernel's `decline` is
signed with the key, like `seal`. Without the key, the runtime could keep a
stop list of scopes it won't serve: refusing to send only ever makes
things safer, so it needs no key. Willow has `decisions` for a recorded no
with its reason.

## A sealed passage that changed

A scope whose passage changed now fails closed (`tests/test_stale.py`):
safe, but silent. The person should hear which scope, which file, and be
offered to seal it again. Willow's `stale-answers` finds the same thing
for approved answers.

## Two sealed questions

Willow's `approved-only` serves only the last sealed scope
(`scopes[-1]` in `do_serve`), so an older sealed question gets nothing
here (`tests/test_hook.py`, the two-scopes test). The fix is in Willow:
let approved-only serve a scope by its subject. Take it there with the
other approved-only finding: a sealed scope whose passage changed is
served short, with no warning (`if i in by_id`).

## Restore

`backup` keeps the box and the runtime's zip, checked. Putting the
runtime's zip back is by hand: unzip it into `BOX.runtime/` beside the box.
Willow's `restore-drill` proves a backup restores; the runtime's zip wants
the same.
