# The doors, and what each side can do

What each side of the runtime can do, the doors that carry it, and what a model's door lists and offers. Part of the [README](../README.md).

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
| `shelves`, `shelf_read`: every project's shelf, and anything on one | `report`: that there is a report of the files; the report itself once its session is let in |
| `report`: a report of their files, as it is | `notes`: the notes they sealed to keep, withheld and whole |
| `task`, `tasks`, `task_drop`: a task of their own, every task and where it stands, and take one off every model's list | `task_add`, `tasks`, `task_claim`, `task_done`: a task waiting on their seal; once sealed, take it up and put its result on the shelf |
| `later`, `back`: not now, and bring it back; never on the record | |
| `shared`: what left, as places, not hashes | |
| `close`: this session's actions, for one seal | |
| `owed`: what waits on their seal, in one line | |
| `restore`: what `backup` kept beside the record, put back, never over a file | |
| `draft`, `models`, `backup`, `pin`, `check`, `sent` | |
| `bring_in`, `brought_in`: bring a notes vault, a calendar, or a Joplin, Evernote or Google Keep export into their folder, and list what was brought | |
| `timeline`: one matter in date order, each line cited, as a file to hand on; `feed`: what they sealed, as an RSS file | `timeline`, `feed`: the same, made for the person once the session is let in |
| `stored`, `remove`, `archive`: what is kept beside the record, deleted or packed away, its hole left on the record; `changed`: what is new or gone in their own folder | `shelf_remove`: one thing off its own project's shelf, once the session is let in |
| `tools`: which groups of tools a model is offered, and the switch for each | |
| `share_id`, `share_person`, `share_send`, `share_receive`, `share_forward`, `share_rotate`, `share_witness`, `shares`: an identity for sharing, whom to send to, every send, receive and passing on, a new key, and the record held to what others kept; `job_write`, `job_take`, `job_run`, `job_gather`: a job that travels in a package, run once sealed, and only its numbers sent back | `share_propose`: a package put together for their seal; `share_received`: what arrived, once the session is let in |

A model's client is not shown 26 verbs. It is offered twelve tools, nine
of them unless you say otherwise: [the tools a model is offered](#the-tools-a-model-is-offered).

Neither side can seal or decline. Sealing is the person's, with their key,
outside every door: typed, or clicked on [the seal page](seal-page.md#the-seal-page).
Every refusal says what happened in plain words, and the one thing to do
next.

## The doors

| Door | Faces | What it is |
|---|---|---|
| `doors/pipe.py` | the person | one JSON request a line in, one answer a line out |
| `doors/mcp.py` | a model | MCP over stdio, by hand: its tools, and [its resources and prompts](#listed-and-started-by-you); asks the client's model through sampling when the client offers it |
| `doors/hook.py` | a model, through its host | Prompt hook (Claude Code, and `--host` for Gemini/Codex/OpenCode): the sealed page, or one line saying nothing is sealed; for a session that asked to be let in, one line pointing at the `context` tool instead. Cursor cannot inject; use MCP |
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
| at a prompt | a correction ("no", "wrong", "nope", "I said", by `hook-feedback`'s words list; never "no thanks" or "no worries") is kept beside your record for the session, 50 at most, and goes nowhere else; at the session's end it is sealed with the session, once, its words on the session's card. Your own words list goes in `BOX.runtime/corrections.txt` | `hook-feedback` (`match`), `session-seal` (`--with`) |
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
`rm`, `mv`, `cp`, `tee`, `sed -i` and the like on it, `find` with `-delete`
or `-exec rm` from it, `git -C` on it with `clean`, `checkout` or `reset`,
and `tar` or `unzip` unpacking into it. It does not stop code
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
| `provider://report/todo`, `…/coming-up`, `…/on-this-day`, `…/people`, `…/ref-check`, `…/pii-audit`, `…/secrets-audit`, `…/minutes` | `report` | the report, for a session you let in; otherwise only whether there is one |
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

## The tools a model is offered

A model keeps track of a short list better than a long one, and every
tool's description is sent to it at the start of every session. So its
verbs are grouped into tools: one for the shelf, with an action, where
there were four. The verbs are unchanged underneath; each action is one of
them, decided and written down exactly as before, and your shared page
still names what was done by its verb.

What else the door tells a model's client, before any tool is called:

- **How the tools go together**, once, at the start (MCP's
  `instructions`): the two ways in, that sealing is yours, and how to read
  an action's arguments in a description.
- **What each tool does to your machine** (MCP's annotations): which only
  read, that only the shelf's `remove` takes anything away, and that none
  reaches past this machine. A client can ask you less often for a tool
  that only reads.
- **The limits, in each tool's schema**: a note's 20,000 characters, a
  shelf name's letters, the report names, a date's form. A model keeps
  inside them instead of finding them by being refused.
- **Which Provider it is**: its version and the Willow commit it is pinned
  to, as `0.1.0+willow.4c1ab7cc6112`.

| Tool | Actions | Group | On |
|---|---|---|---|
| `grant` | | core | always |
| `context` | | core | always |
| `page` | `read`, `propose`, `leave`, `answer`, `draft` | page | yes |
| `report` | | reports | yes |
| `timeline` | | reports | yes |
| `note` | `keep`, `list` | notes | yes |
| `task` | `add`, `list`, `claim`, `done` | tasks | yes |
| `shelf` | `add`, `list`, `read`, `remove` | shelf | yes |
| `job` | `run`, `later`, `result` (each may ask `more`) | jobs | yes |
| `share` | `propose`, `received` | sharing | once you use it |
| `feed` | | sharing | once you use it |
| `skill` | | skills | once you use it |

Nine tools and about 1,200 tokens by default, where there were 26 and
about 3,000.

**The groups are yours to switch.** The seal page has a page for it,
**What a model is offered**: a card for each group, with what it is for,
the tools in it, whether it is on and why, and a button. On your own door
it is `{"tools": true}` to list them and
`{"tools": {"off": ["jobs"], "on": ["sharing"]}}` to change them. Either
way it is kept in `tools.txt` beside your record. Sharing comes on by
itself when you make a sharing identity, and skills when you name one;
what you say wins either way. The core can't be turned off: without it a
session could never ask.

**Off means refused, not only unlisted.** A model that calls a tool of a
group you turned off is refused, by any door that faces a model, and so is
reading it as a listed resource; its prompts are not offered. A client
that has the list open is told when it changes. Your own door is not
affected: the switch is about what a model is offered.

A call that names no action, an action the tool doesn't take, or leaves
out what the action needs is refused before any verb is reached, and says
which.
