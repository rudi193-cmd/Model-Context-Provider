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
| `status`: how things stand, in one look | |
| `promises`: what no model's door can do, and the test that holds each promise | |
| `waiting`: what waits on their seal, and what each one is | `answer`: one sentence, checked, then waiting |
| `scopes`: every question proposed, and where each stands | `draft`: ask a model for that sentence |
| `stop`: never let a scope leave again | `context`: the sealed page for this question, if there is one |
| `preview`: the page a scope would let leave, before they seal it | `capture`: one thing to keep, waiting on the person; `notes` gives it back once sealed |
| `capture`, `captured`: hand in a thing to keep, and read what was kept | `shelf_add`, `shelf_list`, `shelf_read`: what it made, on its project's shelf, with no seal |
| `shelves`, `shelf_read`: every project's shelf, and anything on one | `report`: that there is a report of the files; the report itself once sealed |
| `report`: a report of their files, as it is | `notes`: the notes they sealed to keep, withheld and whole |
| `task`, `tasks`, `task_drop`: a task of their own, every task and where it stands, and take one off every model's list | `task_add`, `tasks`, `task_claim`, `task_done`: a task waiting on their seal; once sealed, take it up and put its result on the shelf |
| `later`, `back`: not now, and bring it back; never on the record | |
| `shared`: what left, as places, not hashes | |
| `close`: this session's actions, for one seal | |
| `owed`: what waits on their seal, in one line | |
| `restore`: what `backup` kept beside the record, put back, never over a file | |
| `draft`, `models`, `backup`, `pin`, `check`, `sent` | |
| `bring_in`, `brought_in`: bring a notes vault or a calendar into their folder, and list what was brought | |
| `share_id`, `share_person`, `share_send`, `share_receive`, `share_forward`, `share_rotate`, `share_witness`, `shares`: an identity for sharing, whom to send to, every send, receive and passing on, a new key, and the record held to what others kept; `job_write`, `job_take`, `job_run`, `job_gather`: a job that travels in a package, run once sealed, and only its numbers sent back | `share_propose`: a package put together for their seal; `share_received`: what arrived, once the session is let in |

Neither side can seal or decline. Sealing is the person's, with their key,
outside every door: typed, or clicked on [the seal page](#the-seal-page).
Every refusal says what happened in plain words, and the one thing to do
next.

## Set it up

You need Python 3.9 or newer and a Willow checkout at the commit
[willow.pin.json](willow.pin.json) names. The pin holds every file of Willow
this runs (the kernel and twenty-seven add-ons) by its SHA-256, and nothing runs
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
| `doors/mcp.py` | a model | MCP over stdio, by hand: its tools, and [its resources and prompts](#listed-and-started-by-you); asks the client's model through sampling when the client offers it |
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
| before a tool call | blocked if it names your key, changes a file in your record other than through the kernel, or changes a file in `BOX.runtime` (what the runtime keeps beside the box: what you stopped, the names withheld, the sent log, the shelf); reading them is fine | `hook-guard` (`--also`) |
| | blocked if what it writes or runs holds a key, a password or a card number; the value is never shown | `hook-leaks` |
| | blocked if it runs a command you denied, read the way the shell reads it | `hook-shell` |
| | blocked if it edits a file the assistant hasn't read this session, or that changed since | `hook-read-first` |
| | blocked if the same command already failed twice this session the same way | `hook-errors` |
| after a command | a failure is kept on your record by the command's hash and exit code, never its words | `hook-errors` |
| at a prompt | a correction ("no", "wrong", "I said") is proposed, and waits on your seal like anything else | `hook-feedback` |
| at a turn's end | where the session ended is kept: its id and folder | `hook-handoff` |
| at the next session's start in that same folder, or its first prompt | the model is told that, once: "session S ended in FOLDER". A session in another folder isn't told: one record hears every project's sessions, and each picks up its own | `hook-handoff` |
| at a session's start, and before a summary | the model is told how many things wait on your seal: a count, and nothing of what they are | the runtime |

A blocked call is told why, in the guard's own words, and that goes on the
sent log (by hash). An allowed call says nothing and logs nothing. A guard
that can't run blocks the call: one that broke can't say it is safe. Only a
tool call is ever blocked; a turn can always end.

The commands you deny are yours to list, one a line, in `deny.txt` beside
your record (`BOX.runtime/deny.txt`): `rm -rf`, `git push --force`. With no
such file that guard isn't asked.

That guard stops a careless or direct tool call: a Write or Edit of a file
in the box or in `BOX.runtime`, or a command that redirects into it or runs
`rm`, `mv`, `cp`, `tee`, `sed -i` and the like on it. It does not stop code
a model runs: a script that builds the path at run time, a `$VAR` path, or a
`cd` earlier in the same command gets through, and so would a call the host
never sends to a hook. Nothing here hides the folder from a model that can
run code as you; the seal page and the kernel are what hold the rest.

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

## A report of your files

Some things worth asking aren't a question: what did I write down to do,
what did I write on this day in earlier years. Willow has a report for
each, and a model can ask for one (the person's ruling of 2026-11-17):

| Report | What it lists |
|---|---|
| `todo` | every line marked to do (TODO, FIXME, "need to", "remember to", an open checkbox), oldest first |
| `coming-up` | every line holding a date in the next 14 days, soonest first, with the repeats of a birthday or a calendar's rule |
| `on-this-day` | what you wrote on this date in earlier years |
| `people` | everyone your files name, a line each: how often, in how many files, over what dates. Never every place they are mentioned. Its first line and the seal page say it names people; a name on your list is withheld, and any other is yours to read before you seal |

It goes the way a question goes:

1. **The model asks.** It learns that there is a report, or that there is
   nothing to report. No line, no file name, no count.
2. **The report waits on you.** Its own words, with names, numbers and
   addresses withheld, are proposed for your seal. The seal page shows them
   as "A report to share".
3. **You seal it, and it leaves** as one page: exactly the words you
   sealed.
4. **A report that would read differently now waits again.** Add a line to
   do and the old seal no longer covers the report; the new one is yours to
   seal. So does tomorrow's `on-this-day`.

`stop` works on a report as on a page, with no key. On your own door,
`{"report": "todo"}` gives you the report as it is: reading needs no grant.
A sealed report is given for its report, never for a question, and it isn't
a page a model can `answer`.

**Leaving folders out.** A folder of commits, code or exports is full of
lines that look like things to do. List what to leave out of every report,
one a line, in `report-skip.txt` beside your record: a folder (`commits`),
a folder inside one (`code/vendor`), or one file's path. It only takes lines
out, on your door and a model's alike, and your own `report` says how many
it left out.

**Too long to read is too long to share.** A report over 20,000 characters
is never proposed: you'd be sealing more than you would read. A model is
told to tell you so, without the size, and you still read the whole of it
on your own door.

Seen in Claude Code on 2026-11-17, over a real record: asked for `todo`, a
model was told only that it waits; the person sealed it on the seal page;
asked again, the model was given it. It ran to 571 lines, most of them
prose about todos in commits and code. That is where the skip list and the
limit come from, and Willow's `todo` now counts a mark only as it is
written to mark something (0.1.2).

## Listed, and started by you

The MCP door also speaks the protocol's two other lists. Neither is one of
this door's tools; who may use them is the client's to say. In Claude Code
a prompt is a command in your own menu, and a resource is what you name
with `@` (type some of its name: the bare list shows only files). Claude
Code also gives its model a way to list and read a server's resources
(seen on 2026-11-17), which is why reading one is never more than the verb
beside it.

**Resources** are what the door can list, each by where to read it:

| Resource | Reading it is | So |
|---|---|---|
| `provider://report/todo`, `…/coming-up`, `…/on-this-day`, `…/people` | `report` | the report once you've sealed it; until then only whether there is one, and it waits on you |
| `provider://page/last` | `leave` | the page you last sealed; without a seal, nothing |
| `provider://shelf/NAME` | `shelf_read` | something a model wrote for this project |

The list says nothing of your files: the reports' names are the same for
everyone, and the shelf's names are a model's own. Reading one is the verb
beside it, decided, refused and written down as that verb always is.
Nothing else can be read this way.

**Prompts** only tell a model which verbs to use and how to say what it
gets back. They hold nothing of yours:

| Prompt | What it starts |
|---|---|
| `plate` | "What's on my plate": asks for `todo` and `coming-up`, says what each holds if it was given, that it waits on your seal if it wasn't, and never guesses at one it wasn't given |
| `ask` (a question) | the question's whole path: the sealed page and one cited sentence, or a page proposed for your seal, or that your files hold nothing |
| `question_me` (what about) | being questioned, not answered: three questions over a page you sealed, one at a time, each naming the passage it came from; or a page proposed for your seal |
| `wrap_up` | what this session found, written up and put on this project's shelf |

## One yes for a session

Sealing each page, report and result is the strict way, and it is still
here. Day to day there is one yes:

- **A session asks once**, when it starts, to read from your files while it
  works in its folder. It shows on your seal page as "A session asking to
  read your files".
- **While that yes stands, its tools answer directly.** `context` gives what
  your files hold on a question, with where each passage is from. `job`
  runs a shell job over your folder in a sandbox and gives what it printed.
  Names and numbers are withheld from both, and nothing waits on you.
  It is given what it asks for: the prompt hook, which asks at every
  prompt, still adds only a page you sealed for those words.
- **The rest of its tools answer the same way:**

  | Tool | Under that yes |
  |---|---|
  | `report` | the report as it reads now; nothing is proposed |
  | `skill` | a skill you named, as it reads now, even if its own seal still waits or its file changed; never one you declined or stopped |
  | `notes` | the notes you sealed, and the ones handed in that still wait, marked as waiting; keeping one is still your seal |
  | `task_add` | a task for the session's own folder is open at once, kept beside your record as the model's own words, and marked as not sealed by you |
  | `tasks`, `task_claim`, `task_done` | those tasks too, for sessions you let in to that folder; `{"tasks": true}` lists them and `task_drop` removes one |

  A task for another folder, a note to keep, a sentence back and a page
  that leaves as a file still wait on your seal.
- **It ends when the session ends**, and never opens again: a session that
  starts again, resumed or new, asks anew. `stop` ends it sooner, with no
  key. `{"grants": true}` lists each one and where it stands.
- **Everything given is written down**, by hash, on the shared page.

**Asked where you are.** Put an empty file named `ask-here` beside your
record and the question comes to you as a dialog on your desktop when a
session first asks: the system's own pinentry, with "Seal: yes, for this
session", "Decline" and "Not now". Not now, closing it, leaving it, or any
answer that isn't a clear yes or no changes nothing, and it waits on your
seal page. That is `seal_prompt.py`: like the seal page it is no door, it
asks about a session's grant and nothing else, and the seal is the
kernel's, with your key. A plain yes-or-no proves someone at your desktop
clicked, not who; a program that can click on your screen could click it.

Without a yes, a session is told only whether your files hold something,
as before. The yes is the kernel's: a file beside your record that claims
one lets no one in.

### A job, in the sandbox

`job` is waited on, for up to two minutes. `job_later` is for one that
takes longer, up to half an hour: it is queued, Willow's kart is started to
work what is queued, one at a time, and it stops when the queue is empty,
so nothing is left running. `job_result` gives where it stands and, once
it has ended, what it printed. Each session has a queue of its own beside
your record; it and what its jobs printed are removed when the session
ends.

`job` is Willow's `kart`, which runs it through
[Kartikeya](https://github.com/willow-memory/kartikeya) and bubblewrap:
your folder read-only at `{pile}`, a scratch folder at `{scratch}`, no
network, no home, and an environment of PATH, LANG and HOME alone. The box
and its key are never in it. The run is on your record by the job's hash;
what it printed is not, and nothing is proposed. A job is stopped after two
minutes. One that ended badly says how (`exited 3`, a timeout); past about
8,000 characters Kartikeya keeps the head and the tail, and the answer says
it was clipped.

Kartikeya needs Python 3.11 or later and `bwrap`. If the Python your doors
run on doesn't have it, name one that does, on one line, in `kart-python`
beside your record. Without it a job is refused and says so.

That Python's own packages are mounted in the sandbox with it, read-only,
under the path they are installed at: a job can see what is installed there
and where. Name one that holds nothing you mind a job listing.

## A skill, sealed by its words

A skill is a file of instructions you chose for a model to follow. The
trouble with one is that it can change after you read it. Here it can't
change under you:

- **You name it**, on your own door: `{"skill_add": {"path": "FILE"}}`. A
  `SKILL.md` is named for its folder, any other file for itself, or give a
  `"name"`. A model never names a file.
- **Its words wait on your seal**, as the file reads now, with names and
  numbers withheld. The seal page shows them as "A skill to give a model",
  to be read as you would anything you let run.
- **A model asks for it by name** (`skill`) and is given exactly the words
  you sealed, and nothing if it still waits.
- **If the file changes, it is given to no one.** A skill that reads
  differently now than what you sealed is a different thing: name it again
  and seal what it then says. Put the file back as it was and the first
  seal stands again.
- **`stop` works on it**, with no key, and `{"skills": true}` lists each
  skill, its file, and where it stands.
- **A skill can be a folder.** Name the folder that holds a `SKILL.md`:
  `{"skill_add": {"path": "FOLDER"}}`. What you seal is the `SKILL.md`
  followed by a list of every other text file in the folder, each with the
  fingerprint of its words. A model asks for one by its name on that list
  (`skill`, with `file`) and is given it only while its words are the ones
  listed. Change, add or remove a file and the folder is no longer what you
  sealed. A link, a hidden file, a key, a file that isn't text, and
  anything outside the folder are never listed; a folder with more than
  200 files, or one that holds your record, is refused. Naming the
  `SKILL.md` itself is still a skill of that one file.
- **Under a session's yes** (above) a skill you named is given as it reads
  now, and so are a folder's files. Naming it is still yours alone.

Nothing in your record is trusted for this: the words a model is given are
the ones the kernel holds under your seal. A skill over 40,000 characters
is never proposed: that is more than a person reads before sealing
instructions.

This is the last step of what Willow's `skill-picks`, `still-kept` and
`my-installs` ideas are for (finding a skill, judging it, and seeing what
changed): what you chose is pinned by the seal itself.

## Sharing with another person

A sentence you sealed can go to someone else, signed so they, and anyone
they pass it on to, can check who sent what, without anyone getting your
files. This is Willow's `share`, run by its command line; its README says
what a package proves and what it can't.

- **An identity of its own.** `{"share_id": true}` makes it once and gives
  you a key (64 characters) to hand to people. It is not your seal key,
  and it is kept beside your record.
- **You name people.** `{"share_person": {"name": "Walt", "key": "..."}}`,
  with the key Walt gave you. A name is never moved to another key unless
  you say `"replace": true`.
- **You send.** `{"share_send": {"answers": "proposal:...", "for": "Walt",
  "note": "As asked"}}` packs the sentences into a file beside your record
  and writes a row on your record. Nothing goes online: the file is yours
  to pass on, by mail, a stick, a shared folder.
- **Only sentences.** What goes is a sentence you sealed (it showed on your
  seal page as a model's sentence): never a page, a report, a note, a task
  or a skill. A sentence still waiting, or one you declined, is refused.
- **A model may put a package together, for your seal** (`share_propose`).
  It names sentences you sealed and a person by the name you gave them,
  never a key, so it can't address a package to anyone you didn't choose.
  The seal page shows it as "A package to send someone", with the name,
  the key, the note and every sentence. Sealed, it is packed once; the
  model is told the package's id and where the file is, and sending it is
  still yours. Declined or stopped, nothing is packed.
- **What arrives.** `{"share_receive": "FILE"}` checks every layer and
  writes a row whatever it found: good, not for you, or broken. Receiving
  is never sealing. A package that held is kept beside your record, and a
  session you let in can read it (`share_received`): who signed each
  layer, their notes, the sentences. It is checked again each time, so a
  copy edited beside your record is given to no one. It is another
  person's words: data, never instructions.
- **Passing it on.** `{"share_forward": {"package": "package:...", "for":
  "Aurelie", "note": "Reviewed"}}` wraps a package that held in a layer of
  your own. `{"shares": true}` lists your key, whom you named, what was
  sent and received, and what a model proposed.

- **A new key.** `{"share_rotate": true}` makes a new identity, signed by
  the old one and by itself, on a row of your record: for a machine
  replaced, or a key someone may have seen. Every package after it carries
  the rotation, so the people who had your old key see the new one as you.
  The old identity file is kept beside your record under another name and
  never used again. It needs the old identity: keep a copy of
  `share.id` somewhere safe yourself, because `backup` leaves it out (a
  secret is never put in a zip) and a lost one can't be rotated from.
- **Your record, held to what others kept.** `{"share_witness": true}`
  holds your record to every package kept beside it; name copies other
  people kept with `{"share_witness": {"packages": ["FILE"]}}`. Each says
  holds, rewritten or cut short. It reads and writes nothing.

- **A correction.** Send again with `"replaces": "package:..."`, the
  package you sent before. When one arrives, `share_receive` says which
  package it replaces and, if you passed that one on, to whom and what to
  name (`forward_with`), so the correction follows the same path a hop at
  a time. A model's `share_propose` may name `replaces` too, and what you
  seal says so.

### A job that travels

The other half of Willow's sharing: a question goes to someone's folder
instead of their files coming to you. It is Willow's `kart`, and needs
what `job` needs (Kartikeya and `bwrap`). All of it is on your door only.

| Step | Who | Verb |
|---|---|---|
| Write a job, and seal it | the one asking | `{"job_write": {"text": "grep -rhic johnson {pile} \| paste -sd+ \| bc"}}` |
| Send it | the one asking | `share_send`, with the job's seal as `answers` |
| Receive it, and take the job to your door | the one asked | `share_receive`, then `{"job_take": "package:..."}`; it waits on your seal and never runs because it arrived |
| Run it, once sealed | the one asked | `{"job_run": "proposal:..."}`: the sandbox, your folder read-only, no network |
| Seal the result and send it back | the one asked | `share_send`, with the result's seal |
| Add up what came back | the one asking | `{"job_gather": {"packages": ["package:..."]}}`; the totals wait on your seal |

**Only numbers go back.** A run is always held to whole numbers, one a
line. A job that prints anything else proposes nothing: what it printed is
written beside your record for you to read, and stays there. `share_send`
refuses a result that isn't numbers even if you sealed it by hand. A job
itself may be sent: it is a shell task, not a word of your files. A model
can write, take, run or send none of this.

## One place to keep things

`capture` hands in one thing to keep: a note, a decision, a finding. It is
proposed under a question of its own, so it never stands in for a page you
sealed for a question, and it waits on your seal like anything else. Sealed,
the kernel writes it under `written/captured/` in your record, and
`{"captured": true}` on your door reads what is there and what still waits.
A model can hand a note in; it can't seal it. Once you have sealed it, a model
can read it back with `notes`, as the next section says.

## A task queue, and the notes you kept

Two things a model is given back, both only once you have sealed them (your
ruling of 2026-11-17: a model may read back what you sealed to keep). Each is
asked of the kernel under a question of its own and given only when the
kernel says it is sealed, in the words that question names and this runtime
proposed. A file under `written/` is never read on trust: change one, or
plant one, and it is not given. Everything a model is given is withheld as a
page is (your names, numbers and emails) and is on the sent log by hash.

**The notes.** `notes` gives a model every note you sealed to keep, whole. A
note still waiting on you, or one you declined, is not given, and a model is
not told how many wait. Over 20,000 characters in all, nothing is given and
the model is told to tell you; no note is cut short. The seal page says a
model may then be given the note.

**The tasks.** A task is a line or two on what to do, proposed under a
question of its own at `tasks/` in your record, by you (`task`) or by a model
(`task_add`, for the folder it works in unless it names another). It waits
like anything else, and the seal page shows it as "A task to do" with a button,
"Seal: yes, do this". Sealing grants a task nothing else: no tool, no file, no
leave. The guard door still holds every tool call, and what is done is
still closed over for one seal. A session you let in (one yes for a
session, above) adds a task for its own folder with no seal: it is that
session's note of work, shown to you as "not sealed by you", and given
only to sessions you let in there.

| | Before your seal | After it |
|---|---|---|
| `tasks` (a model) | only that a task it handed in waits, or that nothing does: never your own tasks, a count or words | the tasks sealed for this project (or for any), each open, claimed or done, with its words if not done |
| `task_claim` | refused as a task that doesn't exist | the first session to claim holds it; another is refused and told which and when |
| `task_done` | refused, as above | with the claim held, puts its result on this project's shelf as `task-ID.md` (no seal; nothing leaves) |

A task you dropped (`task_drop`, which needs no seal of yours) is never given
to a model again and its claim is freed; one you declined never was. A task
for another project is refused as one that doesn't exist. Who claimed what,
and what is done, is kept in `BOX.runtime/tasks/state.json`, beside your
record and in `backup`: no seal, since it holds none of your words. A claim is
a convenience, not a lock: the session is the one a host last said was in that
folder. Nothing runs a task: no worker, no daemon. A session you start picks
one up, or nothing does. `tasks` on your door shows every task and where it
stands, and `status` and `owed` count one waiting as "a task".

## A shelf for each project

A session makes things as it works: a report, a list, working notes. Those
are not yours to seal one by one, and they are not your files. They go on a
shelf:

- **One shelf a project.** A project is the folder the session is working
  in. Every session on that folder adds to the same shelf, and each thing
  on it says when it was put there and by which session.
- **No seal, either way.** A model puts something on its project's shelf
  (`shelf_add`), lists it (`shelf_list`) and reads it back (`shelf_read`). It was written
  by a model and it leaves nothing, so line 1 isn't crossed: your files stay
  behind the seal as before. Each of the three is on the sent log, by hash.
- **Beside your record, never in it.** Shelves live under
  `BOX.runtime/shelf/`, outside the folder your questions read, so a
  model's report is never served back as something you wrote. They go in
  `backup` and come back with `restore`.
- **Never written over.** A name already there is kept beside it as
  `NAME.2`.
- **Yours to read.** `{"shelves": true}` on your door lists every
  project's shelf; `{"shelf_read": {"project": "FOLDER", "name": "NAME"}}` reads
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
- **a model's sentence**: its words, where it would be kept, and under it
  each check code ran on it ("What code checked before this reached you"),
  kept beside the box with the hash of the page it was held to. A sentence
  from before this was kept says its checks aren't on record, not that it
  passed;
- **a task to do**: its words, who proposed it and for which project, with
  **Seal: yes, do this**, which grants it nothing else.

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

A third page, **How things stand**, is the runtime's `status`, and has
nothing to click: what waits on your seal, counted by what each thing is;
what your folder needs from you (approvals gone stale, dates coming up,
questions it never answered: Willow's `digest`, less the folders you leave
out of reports); what you've shared and kept, and each project's shelf; how
this is set (names withheld, folders left out, commands denied); and
whether the record is all right (Willow's `box-health`, the pinned Willow,
the sent log). A part that couldn't be looked at says so, and the rest
still shows. On your own door it is `{"status": true}`. No model's door
has it.

A fourth page, **What a model can never do**, is the runtime's `promises`,
and has nothing to click. It lists the verbs each kind of door has, read
from the code as it stands, not typed by hand; what no model's door can do
(no verb to seal or decline, the verbs only you have, an unknown door
treated as a model's); and the standing promises, each with the test that
holds it. A test fails if a test it names is gone, or if the verbs it lists
differ from the code. On your own door it is `{"promises": true}`. No
model's door has it.

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

## Bringing in a notes vault or a calendar

Your Obsidian or Logseq vault, or your calendar and contact files, can be
written out as plain text in the folder the record reads, so the next
question finds them. This is yours to do, on your own files, so only your
door has it; a model's door and the assistant's hooks do not, and so can
never cause a file to be written into your folder.

    {"bring_in": {"kind": "notes", "from": "/path/to/vault", "as": "garden"}}
    {"bring_in": {"kind": "calendar", "from": "/path/to/calendars", "as": "family"}}
    {"brought_in": true}

The mirror goes in `brought-in/KIND-NAME/` inside the folder the record
reads, made by Willow's `notes` or `calendar` add-on, run by its command
line. The answer says what it said: how many files were written and how
many skipped. The original is never written to or changed, here or by the
add-on. `brought_in` lists what was brought in, from where and when, and
`status` shows it under "Brought in". The list is `brought-in.json` beside
the record, so `backup` and `restore` carry it.

It is refused, in plain words, when `from` is inside the record or your
folder, or holds them, or is the mirror itself; when the name is not one
plain folder name; when there is nothing it can read; and when a mirror of
that name is already there and was not made from the same folder (never
written over, and a folder you made yourself is never taken for one of its
own).

**A second run** over the same folder, under the same name, is safe, as the
add-ons make it: each note or calendar is written again with its present
text, a new one is added, and nothing is removed. A note you deleted from
the vault since stays in the mirror until you delete the mirror file
yourself. Nothing needs doing about the index: every question brings it
current first, and rebuilds it only when a file in the folder changed.

## What it stands on

| From Willow | Used for |
|---|---|
| `notes`, `calendar` | bringing in a vault or calendar files, as a text mirror in the folder |
| the kernel: `bite`, `propose`, `seal`, the record | reading, proposing, and the person's seal |
| `approved-only` | the sealed scope as one page, by name, only whole |
| `sentence-check` | holding the model's sentence to its page |
| `privacy` | withholding numbers, emails and keys |
| `backup`, `local-model` | the record's backup, and finding models on this machine |
| `session-seal` | one seal over a session's actions |
| `index-cache`, `claude-code`'s `bite` | a bite answered from an index of the folder |
| `todo`, `coming-up` (with `pieces`), `on-this-day`, `people` | the reports of the person's files |
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
