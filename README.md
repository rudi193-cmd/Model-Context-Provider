# Model Context Provider

MCP, the Model Context *Protocol*, names a wire: how a model reaches tools and
context. This is a Model Context *Provider*: the one place that decides what a
model is given from a person's own files, whatever wire carries it.

The difference is who holds what. Over a plain MCP server, the model holds the
tools and reaches for context. Here the model never sees the person's files.
It learns only whether their files hold a question. It is given one page, and
only the page the person sealed. And it can send back one sentence, which code
checks and the person seals. The wire, whether MCP, an editor hook or a pipe,
is only a door.

It runs on the person's own machine, over [Willow](https://github.com/willow-memory/Willow),
with the standard library and nothing else.

## The two lines

1. **A grant guards what leaves, never what is read.**
   Reading the person's own material never needs a grant. What leaves the
   machine (the question, the payload, the context handed to a model) does,
   and that is where the gate sits.

2. **Hooks are doors, not verbs: one local runtime decides.**
   Every way in (an MCP server, an editor hook, a pipe, a page) is a shim
   that hands over and takes back. None of them decides what the model is
   given. One local runtime does, the same way for every door.

## How a question goes

Say the person's notes say the first frost comes in late October, and an AI
assistant is asked when it comes.

1. **The model asks.** It learns `populated`: the files hold something. It
   gets no passage, no file name and no count.
2. **The runtime proposes a scope:** the passages that read served, waiting
   on the person.
3. **The person seals it,** with their key. Nothing else can.
4. **The page leaves.** The model gets one page: the sealed passages, under
   ids it can't guess. Names the person listed, and numbers, emails and keys,
   are withheld. The page leaves only whole; if a sealed passage has changed
   since, nothing leaves.
5. **The model answers** in one sentence, citing the page's ids. Willow's
   sentence-check holds it there: every cite was on the page, every passage
   is cited, and the sentence adds nothing the page lacks. A struck sentence
   goes nowhere.
6. **The answer waits** for the person's seal, like everything else.

Every step that reached the model is written down, by hash, on a chained log
beside the person's record.

## What each side can do

| The person's door | A model's door |
|---|---|
| `read`: passages, with file and line | `read`: whether the files hold it, nothing more |
| `propose`: a question to share | `propose`: the same, waiting on the person |
| `leave`: the sealed page, as a file | `leave`: the sealed page, as the one thing it may read |
| `waiting`: what waits on their seal, and what each one is | `answer`: one sentence, checked, then waiting |
| `scopes`: every question proposed, and where each stands | `draft`: ask a model for that sentence |
| `stop`: never let a scope leave again | `context`: the sealed page for this question, if there is one |
| `preview`: the page a scope would let leave, before they seal it | `capture`: one thing to keep, waiting on the person; never read back |
| `capture`, `captured`: hand in a thing to keep, and read what was kept | `shelve`, `shelf`, `take`: what it made, on its project's shelf, with no seal |
| `shelves`, `take`: every project's shelf, and anything on one | |
| `later`, `back`: not now, and bring it back; never on the record | |
| `shared`: what left, as places, not hashes | |
| `close`: this session's actions, for one seal | |
| `owed`: what waits on their seal, in one line | |
| `restore`: what `backup` kept beside the record, put back, never over a file | |
| `draft`, `models`, `backup`, `pin`, `check`, `sent` | |

Neither side can seal or decline. Sealing is the person's, with their key,
outside every door: typed, or clicked on [the seal page](#the-seal-page).
Every refusal says what happened in plain words, and the one thing to do
next.

## Set it up

You need Python 3.9 or newer and a Willow checkout at the commit
[willow.pin.json](willow.pin.json) names. The pin holds every file of Willow
this runs (the kernel and eighteen add-ons) by its SHA-256, and nothing runs
on a Willow whose files differ: `python3 willow_pin.py check` says which.
Nothing else in Willow matters to it. Make your record in Willow's UI: pick
your folders, type your own words into the words step, seal it, and press
**Start it**. Then:

    python set_up.py --stack PATH/TO/YOUR/STACK

It checks Willow, your record and your words, and prints what to paste:

- the `claude mcp add --scope user …` line for Claude Code;
- the hooks for `~/.claude/settings.json`: the prompt hook, the session
  door on SessionStart and SessionEnd, and [the guard door](#the-guard-door)
  around what the assistant does;
- Cursor and the other assistants from Willow's hosts table
  (`hosts.py show cursor --box BOX`).

By default it changes nothing of your client's. To finish one:

    python set_up.py --box BOX --write cursor
    python set_up.py --box BOX --write claude-code
    python set_up.py --box BOX --write all

`--write` merges the MCP door into that assistant's home settings (and for
Cursor, the session hooks that tell you what waits). It never overwrites an
entry by our name that already differs. To draft answers with a model on this
machine (Ollama, llama.cpp, LM Studio…), add `--model
http://127.0.0.1:11434/v1 NAME`. That writes `model.json` beside your record,
and nothing else. A model off this machine is refused.

Your own door, for everything a model can't do:

    python doors/pipe.py --box BOX
    {"waiting": true}
    {"preview": true}
    {"shared": true}
    {"backup": "/media/usb"}
    {"restore": "/media/usb/model-context-provider-20261117-120000.zip"}

## The doors

| Door | Faces | What it is |
|---|---|---|
| `doors/pipe.py` | the person | one JSON request a line in, one answer a line out |
| `doors/mcp.py` | a model | MCP over stdio, by hand; asks the client's model through sampling when the client offers it |
| `doors/hook.py` | a model, through its host | Prompt hook (Claude Code, and `--host` for Gemini/Codex/OpenCode): the sealed page, or one line saying nothing is sealed. Cursor cannot inject; use MCP |
| `doors/guard.py` | a model, through its host | Claude Code's hooks around what the assistant does: before and after a tool call, at a turn's end, at a session's start, before a summary |
| `doors/session.py` | the person | Session start/end: each session closed for one seal; at the next start the person is told what waits (Claude `systemMessage`, Cursor `user_message` + desktop notice). Cursor also nudges after this server's MCP tools |

## The guard door

The two hook doors face the assistant's own program, calling at a moment of
its session. They have two verbs, `context` and `event`, and none of a
model's. `event` is decided in the runtime, by Willow's own hooks, each a
fixed rule and never a reading of what the assistant meant:

| When | What happens | Willow's |
|---|---|---|
| before a tool call | blocked if it names your key, or changes a file in your record other than through the kernel | `hook-guard` |
| | blocked if what it writes or runs holds a key, a password or a card number; the value is never shown | `hook-leaks` |
| | blocked if it runs a command you denied, read the way the shell reads it | `hook-shell` |
| | blocked if it edits a file the assistant hasn't read this session, or that changed since | `hook-read-first` |
| | blocked if the same command already failed twice this session the same way | `hook-errors` |
| after a command | a failure is kept on your record by the command's hash and exit code, never its words | `hook-errors` |
| at a prompt | a correction ("no", "wrong", "I said") is proposed, and waits on your seal like anything else | `hook-feedback` |
| at a turn's end | where the session ended is kept: its id and folder | `hook-handoff` |
| at the next session's start, or first prompt | the model is told that, once: "session S ended in FOLDER" | `hook-handoff` |
| at a session's start, and before a summary | the model is told how many things wait on your seal: a count, and nothing of what they are | the runtime |

A blocked call is told why, in the guard's own words, and that goes on the
sent log (by hash). An allowed call says nothing and logs nothing. A guard
that can't run blocks the call: one that broke can't say it is safe. Only a
tool call is ever blocked; a turn can always end.

The commands you deny are yours to list, one a line, in `deny.txt` beside
your record (`BOX.runtime/deny.txt`): `rm -rf`, `git push --force`. With no
such file that guard isn't asked.

What these hand a model is a rule's name, a session's id and folder, or a
count. None of them hands it a word of your files: Willow's `hook-start`,
`hook-compact` and `hook-impact`, which do, are not used.

Seen in Claude Code on 2026-11-17, over a real record: a session opened
with the count and no words; a write holding a made-up key was blocked by
`hook-leaks`; a second edit of a file without reading it again was blocked
by `hook-read-first`; and the third try of a command that had failed twice
was blocked by `hook-errors`. That last one failed at first: Claude Code
sends a failed command as `PostToolUseFailure` with `"error": "Exit code
2\n…"` and no `exit_code` field, where Willow's `hook-errors` looked. The
payload was kept with `capture`, the fix went to Willow (`hook-errors`
0.1.2, commit `14efe16d`, not yet in a Willow pull request), and the pin
moved to it. A correction and a denied command have not been tried.

## One place to keep things

`capture` hands in one thing to keep: a note, a decision, a finding. It is
proposed under a question of its own, so it never stands in for a page you
sealed for a question, and it waits on your seal like anything else. Sealed,
the kernel writes it under `written/captured/` in your record, and
`{"captured": true}` on your door reads what is there and what still waits.
A model can hand a note in; it can't seal it, and it can't read it back.

## A shelf for each project

A session makes things as it works: a report, a list, working notes. Those
are not yours to seal one by one, and they are not your files. They go on a
shelf:

- **One shelf a project.** A project is the folder the session is working
  in. Every session on that folder adds to the same shelf, and each thing
  on it says when it was put there and by which session.
- **No seal, either way.** A model puts something on its project's shelf
  (`shelve`), lists it (`shelf`) and reads it back (`take`). It was written
  by a model and it leaves nothing, so line 1 isn't crossed: your files stay
  behind the seal as before. Each of the three is on the sent log, by hash.
- **Beside your record, never in it.** Shelves live under
  `BOX.runtime/shelf/`, outside the folder your questions read, so a
  model's report is never served back as something you wrote. They go in
  `backup` and come back with `restore`.
- **Never written over.** A name already there is kept beside it as
  `NAME.2`.
- **Yours to read.** `{"shelves": true}` on your door lists every
  project's shelf; `{"take": {"project": "FOLDER", "name": "NAME"}}` reads
  one thing.

A model reaches only the shelf of the folder its door was started in. That
is the folder the client says, not a lock: a program running as you can
read any of it, as it can read your files.

To see what the assistant's host sends at a moment of the session, name the
moment in `capture.txt` beside your record, one a line
(`PostToolUseFailure`). Each one is then put whole on the shelf of the
folder it happened in, until you take the line out. It holds the command
that ran.

## The seal page

    python seal_page.py --box BOX

It prints a link and opens it in your browser. The page shows what waits on
your seal, each as what it is:

- **a session**: which rows of your record, and what was done in them;
- **a page to share**: the page as it would leave, withheld, by file and
  line (the runtime's `preview`);
- **a model's sentence**: its words, and where it would be kept.

Under each, "Exactly what you'd be sealing" unfolds the bytes your key
signs, and three buttons:

| Button | What it does |
|---|---|
| **Seal** | the kernel's own `seal`, proved with your key |
| **Decline** | the kernel's own `decline`, proved with your key, and final; it asks for a tick first |
| **Not now** | nothing on your record and no key: it still waits, and you aren't told about it again until you bring it back |

A second page, **What you've shared**, lists every page you were asked to
share, by file and line, and where each stands: waiting, sealed, changed in
your files since, or stopped. **Stop sharing this** is the runtime's `stop`:
the page is never given to a model again, by any door, and it needs no key.
Under them is what has left, to whom and when (the runtime's `shared`).

**Close this page** stops it. To start it with a double-click:

    python seal_page.py launcher --box BOX --write

That saves a launcher for this machine: on Linux an entry named "Seal page"
in your applications menu, on macOS and Windows a file on your Desktop.
Without `--write` it prints all three and where each goes, and writes
nothing. It never writes over a file that differs. A page started that way
stops itself after half an hour with nobody asking (`--idle 30`). The
launcher holds no secret: each start makes its own. Only the Linux one has
been run; the macOS and Windows files are untried.

It is not a door, and it decides nothing. The decision is your click; the
seal is the kernel's, run by its command line as if you had typed it; the
kernel reads your key, and this project never does. No door imports the
page, and the runtime still has no verb to seal, so nothing a model's door
can ask for ends in a seal. Start it in a terminal of your own: the link
holds a secret made at each start, and it is printed nowhere else.

Who can reach it (the table Willow's `browse` is held to, the code written
here):

| Way in | What stops it |
|---|---|
| Another computer | It listens on 127.0.0.1 only. |
| Another website, in a browser you've opened it in | The secret is an HttpOnly, SameSite=Strict cookie, and every form carries it too; without both, 403. A form whose Origin isn't this page, or is missing or `null`, gets 403. |
| A website that renames itself as this machine | A Host that isn't `127.0.0.1:PORT` or `localhost:PORT` gets 403. |
| A website that frames it under a button | `frame-ancestors 'none'` and `X-Frame-Options: DENY`. |
| Words in a passage or a model's sentence | Every one is escaped, and the page allows no script at all. |
| A program already running as you | Nothing. It could run `kernel.py seal` itself; that includes an assistant you've given a shell or your browser. |

Checked in a real Chrome on 2026-11-17, over a made-up folder: the person's
Seal, Not now and Decline each did what they say; a page on another port
that framed it was refused by the CSP, and its form got 403 and left the
record as it was.

## One seal a session

A seal at every step is a lot to ask. At a session's end the session door
asks the runtime to `close` it: Willow's `session-seal` bundles the record's
rows since the last close (each by number, kind and hash, no words) as one
proposal, "yes, these were my actions". At the next start, the person is
told what waits on them: a one-line count (Claude Code's `systemMessage`),
and a card naming each claim with its seal line and the seal page's command
(Cursor's `user_message`, a desktop notice when the OS has one, and
`BOX.runtime/needs-you.txt`). Nothing of that is put in the model's turn:
the model gets a count, from [the guard door](#the-guard-door).

It proposes; it never seals. Sealing a session says the actions were the
person's; it doesn't let a page leave. A page still leaves only on its own
seal, and a sealed one keeps being given for its question, session after
session, until it changes in the files or the person stops it. So the seals
fall away: one a session, and one a question, once.

SessionEnd hooks get 1.5 seconds unless they say otherwise, so the line
`set_up.py` prints gives it 60, the most Claude Code allows.

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
| the kernel: `bite`, `propose`, `seal`, the record | reading, proposing, and the person's seal |
| `approved-only` | the sealed scope as one page, by name, only whole |
| `sentence-check` | holding the model's sentence to its page |
| `privacy` | withholding numbers, emails and keys |
| `backup`, `local-model` | the record's backup, and finding models on this machine |
| `session-seal` | one seal over a session's actions |
| `index-cache`, `claude-code`'s `bite` | a bite answered from an index of the folder |
| `hook-guard`, `hook-leaks`, `hook-shell`, `hook-read-first`, `hook-errors` | the rules a tool call is held to before it runs |
| `hook-handoff`, `hook-feedback` | where a session ended, and a correction kept for the person's seal |

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

## Working on it

    WILLOW=/path/to/Willow python check.py

That is the check a change is held to, and it runs here: Willow held to
its pin, `ruff check`, `ruff format --check`, and the tests. Name each
Python to run the tests under (`--python PY`, as often as wanted; Willow's
kernel promises 3.9). `--commit REV` checks that commit as it was
committed, unpacked somewhere else, so a change not yet committed can't
pass for it.

To hold `main` to it on this machine, with no server asked:

    python check.py hook --python PY --python PY39 --write

That saves a git hook in this checkout. Whatever is about to become `main`
(by a commit, a merge, a fast-forward or a pull) is checked first, and
refused if it fails. A commit that passed is remembered and not checked
twice. The workflow on GitHub runs the same commands, as a second opinion:
it can only see a Willow commit that has been pushed.

[CONTRIBUTING.md](CONTRIBUTING.md) has the rules a change is held to;
[AGENTS.md](AGENTS.md) is the short form for an agent;
[SECURITY.md](SECURITY.md) says what counts as a hole. Apache-2.0.

Nothing here reads the person's key: the kernel does, when the person
seals. The key is the user's.
