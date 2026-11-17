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

## Restore

`backup` keeps the box and the runtime's zip, checked. Putting the
runtime's zip back is by hand: unzip it into `BOX.runtime/` beside the box.
Willow's `restore-drill` proves a backup restores; the runtime's zip wants
the same.

## Built since

- **Two sealed questions**, **a sealed passage that changed**: Willow's
  approved-only now serves a sealed scope by name (`--scope`) and refuses
  one that isn't whole (Willow branch `ccr-cddfc117-zpl0tu`, `d7c40dd`); the
  runtime serves each question its own scope, and `scopes` says out loud
  which one changed in the files since it was sealed.
- **"I didn't mean to share that"**: `stop` keeps a scope from ever leaving
  again, by any door, with no key; sharing it again means sealing it anew.
