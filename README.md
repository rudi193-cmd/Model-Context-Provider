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

## What is built

| Piece | What it does | Held by |
|---|---|---|
| `runtime.py` | The one place that decides. Reads through Willow's kernel (no grant); proposes a scope; lets out only a scope the person sealed | `tests/test_read.py`, `tests/test_leave.py` |
| `runtime.FACES` | Who is on the far side of each door. A model's door gets whether the files hold a question, never the passages; those reach it only as the sealed scope's one page. A door the runtime doesn't know faces a model | `tests/test_doors.py` |
| `runtime.answer` | A model's only way back: one sentence about the page it was given, held by Willow's sentence-check, then proposed through the kernel to wait for the person's seal | `tests/test_answer.py` |
| `doors/pipe.py` | A person's door: one JSON request a line | `tests/test_doors.py` |
| `doors/mcp.py` | A model's door: MCP over stdio, by hand, the shape of Willow's mcp-lite | `tests/test_doors.py` |

A door imports the runtime and nothing that decides, and never calls Willow
itself; a test fails any door that does.

    WILLOW=/path/to/Willow python -m pytest tests
    python doors/mcp.py --box DIR

### In a real client

Claude Code, with only this door and nothing else of yours:

    cat > mcp.json <<'JSON'
    {"mcpServers": {"unnamed": {"type": "stdio", "command": "python3",
      "args": ["/path/to/unnamed/doors/mcp.py", "--box", "/path/to/box"],
      "env": {"WILLOW": "/path/to/Willow"}}}}
    JSON
    claude -p "When does the first frost come in my files?" \
      --strict-mcp-config --mcp-config mcp.json \
      --allowedTools "mcp__unnamed__read,mcp__unnamed__propose,mcp__unnamed__leave,mcp__unnamed__answer"

Run on 2026-11-17 over a made-up pile, Claude Code 2.1.326: read gave
`{"state":"populated"}` and no passage; propose waited on the seal; leave was
refused, "no sealed scope; nothing served"; and the model would not call
answer, since it had no page or ids: "Anything I sent would have been made up." It
stopped at the seal, which is the person's.

Then the scope was sealed (the seal was the user's word, given in chat, for
this demo box and its scratch key), and the client ran again. leave gave it
the one page, the garden passage under an opaque id and nothing of the car.
Its first answer, "The first frost comes in late October, which is when the
dahlias come up [bd84e5143742].", was struck: "which, when are no box's".
Its second, in the page's own words, held all four checks and was proposed
through the kernel, where it waits for the person's seal.

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
