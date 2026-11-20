# One yes for a session

The one yes a session asks for, what its tools give under it, and the one seal that closes a session. Part of the [README](../README.md).

## One yes for a session

Sealing each page and each answer is the strict way, and it is still
here. Day to day there is one yes:

- **A session asks once**, when it starts, to read from your files while it
  works in its folder. It shows on your seal page as "A session asking to
  read your files".
- **While that yes stands, its tools answer directly.** `context` gives what
  your files hold on a question, with where each passage is from. `job`
  runs a shell job over your folder in a sandbox and gives what it printed.
  Names and numbers are withheld from both, and nothing waits on you.
  It is given what it asks for: the prompt hook, which asks at every
  prompt, still adds only a page you sealed for those words. When your
  files hold something on a prompt and no page is sealed for it, the hook
  tells a session that asked to be let in to use the `context` tool, and
  any other that it is given none of it.
- **The rest of its tools answer the same way:**

  | Tool | Under that yes |
  |---|---|
  | `report` | the report as it reads now. This is the only way a model is given one |
  | `skill` | a skill you named, as it reads now, even if its file changed since you named it; never one you stopped |
  | `notes` | the notes you sealed, and the ones handed in that still wait, marked as waiting; keeping one is still your seal |
  | `task_add` | a task for the session's own folder is open at once, kept beside your record as the model's own words, and marked as not sealed by you |
  | `tasks`, `task_claim`, `task_done` | those tasks too, for sessions you let in to that folder; `{"tasks": true}` lists them and `task_drop` removes one |

  A task for another folder, a note to keep, a sentence back and a page
  that leaves as a file still wait on your seal.
- **It ends when the session ends**, and never opens again: a session that
  starts again, resumed or new, asks anew. `stop` ends it sooner, with no
  key. `{"grants": true}` lists each one and where it stands.
- **Everything given is written down**, by hash, on the shared page.
- **Your record isn't written to be told what it already said.** Whether a
  session's yes stands is the kernel's to say, and asking it writes a row.
  So a yes the kernel gave is remembered by the door that asked, in its own
  memory and nowhere else, for as long as the proposal it was for reads
  exactly as it did; if that file changes it is asked again. A no is never
  remembered, so a seal you make is seen at once, and what you stopped, or
  a session that ended, is still checked on every call. The same goes for a
  sealed task and a kept note. What waits on your seal is asked
  once while a call is answered, not two or three times.

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

**A long print comes in part.** What a job printed is given up to 4,000
characters. Over that, the answer holds the first whole lines that fit, and
says so (`cut`): how much is given, of how much, and how to get all of it.
Ask again with `more: yes` for up to 20,000 characters. For `run` that
runs the job again, so one that prints something different each time may
differ; for `result` it reads the same print again and runs nothing. Over
20,000 characters nothing is given, as before, and the model is told to ask
for less. It is withheld before it is cut, so nothing is given that wasn't
withheld.

Kartikeya needs Python 3.11 or later and `bwrap`. If the Python your doors
run on doesn't have it, name one that does, on one line, in `kart-python`
beside your record. Without it a job is refused and says so.

That Python's own packages are mounted in the sandbox with it, read-only,
under the path they are installed at: a job can see what is installed there
and where. Name one that holds nothing you mind a job listing.

## One seal a session

A seal at every step is a lot to ask. At a session's end the session door
asks the runtime to `close` it: Willow's `session-seal` bundles the record's
rows since the last close (each by number, kind and hash, no words) as one
proposal, "yes, these were my actions". What the person said that session
to correct the assistant goes in with it, in their words (`--with`), so
those are sealed with the session, once, rather than a card each. At the
next start, the person is
told what waits on them: a one-line count (Claude Code's `systemMessage`),
and a card naming each claim with its seal line and the seal page's command
(Cursor's `user_message`, a desktop notice when the OS has one, and
`BOX.runtime/needs-you.txt`). Nothing of that is put in the model's turn:
the model gets a count, from [the guard door](doors.md#the-guard-door).

It proposes; it never seals. Sealing a session says the actions were the
person's; it doesn't let a page leave. A page still leaves only on its own
seal, and a sealed one keeps being given for its question, session after
session, until it changes in the files or the person stops it. So the seals
fall away: one a session, and one a question, once.

SessionEnd hooks get 1.5 seconds unless they say otherwise, so the line
`set_up.py` prints gives it 60, the most Claude Code allows.
