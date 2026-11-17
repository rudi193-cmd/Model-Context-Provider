# unnamed

A model context provider: what a model is given, decided in one place, with
the wire that carries it left as a detail. It starts from two lines.

## The two lines

1. **A grant guards what leaves, never what is read.**
   Reading the person's own material never needs a grant. What leaves the
   machine (the question, the payload, the context handed to a model) does,
   and that is where the gate sits.

2. **Hooks are doors, not verbs: one local runtime decides.**
   Every way in (an MCP server, an editor hook, a pipe, a page) is a shim
   that hands over and takes back. None of them decides what the model is
   given. One local runtime does, the same way for every door.

Both are proposals. Nothing here is sealed.

## Where they come from

Both are rules of the one-box plan in willows-grove,
`docs/design/one-box/README.md` (at `fc724c1`):

- line 139: "**Egress is about what leaves, not what comes in** (operator,
  2026-10-01: "It's not about bringing information in, it's the egress
  saying that your information is now going to the outside world."). The
  grant guards the outbound flow: the question, the payload, the context
  that leaves the box. Reading local material (the corpus, almanac clones,
  files) never needs a grant."
- line 151: "**Hooks are doors, not verbs.** The front end is a shim; one
  local runtime decides."

A claim-check of all four repos (Willow, willow-mcp, willow-bot,
willows-grove) found each held whole only there. The rest of the security
core already made it into Willow.

## What it stands on, and doesn't redo

| Already built | Where |
|---|---|
| The model never sees a box; holding the file is the permission | Willow `docs/design/serve.md`, `adapters/stdlib/approved-only` |
| A passage is served only when it holds half the question's words | Willow `kernel.py` |
| Every cite served, every box cited, nothing the boxes lack | Willow `adapters/stdlib/sentence-check` |
| The human seals; code only proposes | Willow `kernel.py` (`propose`, `seal`) |

Nothing here reads the person's key. The key is the user's.
