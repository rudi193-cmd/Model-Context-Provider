# Background

What it runs on, what stays on the machine, what has been seen working, and where the design comes from. Part of the [README](../README.md).

## A big folder

The kernel reads every file at every bite: on 190,000 passages, half a
minute. So the runtime keeps an index of the folder beside the box
(`BOX.runtime/index`), brought current at each read by Willow's
`index-cache`, which rebuilds only when a file changed. While it is
current, `claude-code`'s bite answers from it, the same JSON and the same
row on the record as the kernel's, and a session closes from it too. Over
one real folder: a read 27 seconds before, 3 after; the first one, which
builds the index, 19. The index never goes in a backup, and with a Willow
too old to have that bite, the kernel reads the folder as before.

A door imports the runtime and nothing that decides, and never calls Willow
itself. `tests/test_doors.py` fails any door that does. A door the runtime
doesn't know is treated as facing a model.

## What stays on the machine

- **The files, and everything read from them.** Reading needs no grant
  because nothing read leaves.
- **The person's words list.** It helps the kernel find their files from
  their own words ("inspection" finds "MOT"). It is never sent.
- **The sent log**, chained line to line. `pin` writes its end somewhere the
  runtime can't reach, and `check` holds the log to it. `shared` reads it
  back as "garden.md:1, to the AI assistant, at 08:22".
- **Where each passage lives**, kept beside the record so the log can be
  read as places.

What leaves: one sealed page at a time, withheld and whole, to the client's
model or to a model on this machine. Each is logged before it is sent.

## Seen in a real client

On 2026-11-17, over a made-up folder (garden notes and a car's MOT), with
Claude Code 2.1.326 and nothing else of the person's loaded:

- **Before the seal:** `read` gave `{"state":"populated"}` and no passage.
  `propose` waited on the seal, and `leave` was refused. The model would not
  call `answer`: "Anything I sent would have been made up." It stopped at the
  seal.
- **After the seal:** `leave` gave the one page, the garden passage under an
  opaque id and nothing of the car. The model's first sentence was struck
  ("which, when are no box's"). Its second, in the page's own words, held all
  four checks and waits for the person's seal.
- **The prompt hook** added one line for each question, saying nothing was
  sealed, and no file content.
- **`set_up.py`'s `claude mcp add` line** registered the door, and Claude Code
  reported it connected.

Claude Code 2.1.326 doesn't offer MCP sampling, so `draft` there uses a model
named in `model.json`.

## What it stands on

| From Willow | Used for |
|---|---|
| `notes`, `calendar`, `joplin`, `evernote`, `google-keep`, `mail`, `sms` | bringing in a vault, calendar files, an export, email or a phone's texts, as a text mirror in the folder |
| the kernel: `bite`, `propose`, `seal`, the record | reading, proposing, and the person's seal |
| `approved-only` | the sealed scope as one page, by name, only whole |
| `sentence-check` | holding the model's sentence to its page |
| `privacy` | withholding numbers, emails and keys |
| `backup`, `local-model` | the record's backup, and finding models on this machine |
| `session-seal` | one seal over a session's actions |
| `index-cache`, `claude-code`'s `bite` | a bite answered from an index of the folder |
| `todo`, `coming-up` (with `pieces`), `on-this-day`, `people`, `ref-check`, `pii-audit`, `secrets-audit` (with `privacy`), `minutes` (with `habits`) | the reports of the person's files |
| `hook-guard`, `hook-leaks`, `hook-shell`, `hook-read-first`, `hook-errors` | the rules a tool call is held to before it runs |
| `hook-handoff`, `hook-feedback` | where a session ended, and a correction kept for the person's seal |
| `digest` (with `stale-answers`), `box-health` | what the folder needs from the person, and whether the record is all right, in `status` |

It uses Willow by its command line only, and never imports or changes
Willow's kernel. When Willow lacks something, the fix goes to Willow:
`approved-only`'s `--scope` and its whole-scope check came from building
this ([willow-memory/Willow#373](https://github.com/willow-memory/Willow/pull/373)).

## Not yet

- **Sealing away from the box.** The seal page is on this machine only; a
  phone is not built. Nor is a seal through the client (MCP elicitation):
  that form would sit on a model's door. [NOTES.md](NOTES.md) has both.
- **Models off this machine** are refused. Sending even a sealed page to
  someone else's server is a bigger step, and would be the person's
  explicit line in `model.json`.

## Where the two lines come from

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

A claim-check of Willow, willow-mcp, willow-bot and willows-grove found each
of the two held whole only there. The rest of the security core was already
in Willow: the model never sees a box (`docs/design/serve.md`), and the
person seals while code only proposes.
