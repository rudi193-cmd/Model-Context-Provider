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

## Built since

- **Preview before sealing**: `preview` shows the page a scope would let
  leave, withheld, by place, from the texts the runtime holds a sealed page
  to before it leaves; `waiting` points at it, since a scope's own words are
  a hash. It seals, sends and writes nothing.
- **Restore**: `restore` puts the runtime's zip back beside the box, after
  checking it the way Willow's `restore-drill` checks a box backup (flat
  names, every CRC, no key, no box, the sent log's chain). It never writes
  over a file: one that differs refuses the whole restore. The box itself
  is still restored by hand, as Willow's `backup` README says: unzip it,
  copy the key back.
- **Two sealed questions**, **a sealed passage that changed**: Willow's
  approved-only now serves a sealed scope by name (`--scope`) and refuses
  one that isn't whole (Willow branch `ccr-cddfc117-zpl0tu`, `d7c40dd`); the
  runtime serves each question its own scope, and `scopes` says out loud
  which one changed in the files since it was sealed.
- **"I didn't mean to share that"**: `stop` keeps a scope from ever leaving
  again, by any door, with no key; sharing it again means sealing it anew.
