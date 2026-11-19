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

## Set it up

You need Python 3.9 or newer and a Willow checkout at the commit
[willow.pin.json](willow.pin.json) names. The pin holds every file of Willow
this runs (the kernel and each add-on it uses) by its SHA-256, and nothing runs
on a Willow whose files differ: `python3 willow_pin.py check` says which.
Nothing else in Willow matters to it. Make your record in Willow's UI: pick
your folders, type your own words into the words step, seal it, and press
**Start it**. Then:

    python set_up.py --stack PATH/TO/YOUR/STACK

It checks Willow, your record and your words, and prints what to paste:

- the `claude mcp add --scope user …` line for Claude Code;
- the hooks for `~/.claude/settings.json`: the prompt hook, the session
  door on SessionStart and SessionEnd, and [the guard door](docs/doors.md#the-guard-door)
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

Your own door, for everything a model can't do, is easiest as a command:

    python set_up.py --box BOX --write command

That saves `provider` in `~/.local/bin`, with your record filled in. Then:

    provider waiting
    provider shared
    provider timeline mould landlord
    provider share_send answers=last for=Walt note="As asked"

No word after the verb asks it plainly; `name=value` words make its
argument; anything else is its argument as it reads. The same door takes
one JSON request a line, which is how the rest of these pages write it
(`{"waiting": true}` is `provider waiting`):

    python doors/pipe.py --box BOX
    {"waiting": true}
    {"preview": true}
    {"shared": true}
    {"backup": "/media/usb"}
    {"restore": "/media/usb/model-context-provider-20261117-120000.zip"}

## The rest, by what you want to do

| To read about | See |
|---|---|
| What each side of the runtime can do, the doors that carry it, and what a model's door lists and offers | [docs/doors.md](docs/doors.md) |
| The one yes a session asks for, what its tools give under it, and the one seal that closes a session | [docs/session.md](docs/session.md) |
| The page where you read what waits and seal or decline it | [docs/seal-page.md](docs/seal-page.md) |
| Reports of your own files, and the two files made to hand on | [docs/reports.md](docs/reports.md) |
| Instructions you name for a model to follow | [docs/skills.md](docs/skills.md) |
| Sending a sealed sentence, or a job, to another person | [docs/sharing.md](docs/sharing.md) |
| Notes, tasks, shelves, what piles up beside your record, and importing from elsewhere | [docs/keeping.md](docs/keeping.md) |
| What it runs on, what stays on the machine, what has been seen working, and where the design comes from | [docs/background.md](docs/background.md) |
| What was asked, what was built and what is left | [docs/OPEN.md](docs/OPEN.md) |
| What changed, and when | [CHANGELOG.md](CHANGELOG.md) |
| Every file, and what it is | [FILES.md](FILES.md) |
| Design notes | [docs/NOTES.md](docs/NOTES.md) |

## Working on it

    WILLOW=/path/to/Willow python check.py

That is the check a change is held to, and it runs here: Willow held to
its pin, `ruff check`, `ruff format --check`, and the tests. Name each
Python to run the tests under (`--python PY`, as often as wanted; Willow's
kernel promises 3.9). `--commit REV` checks that commit as it was
committed, unpacked somewhere else, so a change not yet committed can't
pass for it.

It is made to be quick enough to run every time:

- **The tests run in parts, one a core.** Willow's `test-shards` cuts the
  test files by how long each took last time, so the parts end about
  together. `--jobs N` runs another number at once; `--jobs 1` is one run.
- **A pass is remembered by what the tests can read**: every file here but
  the words of the docs. While none of that has changed, the tests aren't
  run again; only the one that holds [FILES.md](FILES.md) to the folder
  is. So a change to the docs alone is checked in seconds. `--all` runs
  every test regardless. The pin and the lint are asked every time.

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
