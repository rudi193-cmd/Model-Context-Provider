# What is kept, and bringing things in

Notes, tasks, shelves, what piles up beside your record, and importing from elsewhere. Part of the [README](../README.md).

## One place to keep things

`capture` hands in one thing to keep: a note, a decision, a finding. It is
proposed under a question of its own, so it never stands in for a page you
sealed for a question, and it waits on your seal like anything else. Sealed,
the kernel writes it under `written/captured/` in your record, and
`{"captured": true}` on your door reads what is there and what still waits.
A model can hand a note in; it can't seal it. Once you have sealed it, a model
can read it back with `notes`, as the next section says.

A note is at most 20,000 characters, about what you'd read before keeping
it; a long piece of work goes on the shelf instead. At most 50 notes wait
on you at once: past that, a new one is refused until you have sealed or
declined some, so what waits is never more than you can get through.

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
still closed over for one seal. A session you let in
([One yes for a session](session.md)) adds a task for its own folder with no seal: it is that
session's note of work, shown to you as "not sealed by you", and given
only to sessions you let in there.

| | Before your seal | After it |
|---|---|---|
| `tasks` (a model) | only that a task it handed in waits, or that nothing does: never your own tasks, a count or words | the tasks sealed for this project (or for any), each open, claimed or done, with its words if not done |
| `task_claim` | refused as a task that doesn't exist | the first session to claim holds it; another is refused and told which and when |
| `task_done` | refused, as above | with the claim held, puts its result on this project's shelf as `task-ID.md` (no seal; nothing leaves) |

A task you dropped (`task_drop`, which needs no seal of yours) is never given
to a model again and its claim is freed; one you declined never was. A task
for another project is refused as one that doesn't exist. **A long list is
given in part.** `tasks` gives at most 20,000 characters of words at once:
the oldest tasks that fit. If more were left off the answer says
`more: true`, and nothing else about them, never how many. It is not refused
whole, as the notes are: a session that is given no task can take none up.
Finishing a task frees its words (a task done has none), so finish the ones
given, then ask again. Only tasks that session may see are weighed: one still
waiting on your seal, one you dropped and one for another project make no
difference to it. Who claimed what,
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
- **Not without end.** A thing on a shelf is at most a million characters,
  and a project's shelf holds 200 things or 50 MB, whichever comes first.
  A full shelf refuses what comes next, plainly, until something is taken
  off: by you (`remove` or `archive`, below) or by a session you let in.
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

## What is kept, and taking it away

Things pile up beside your record: what sessions shelved, timelines and
feeds, packages, old job queues. They are yours to delete or pack away,
and the record keeps the hole: before a file goes, its name, size and
fingerprint are written on a row (Willow's `removed`), never its words.

| On your door | What it does |
|---|---|
| `{"stored": true}` | each kind kept beside your record: how many files, how big, the oldest and the newest. `{"stored": "made"}` lists one kind's files by name |
| `{"remove": {"kind": "made", "names": ["made/..."]}}` | deletes those. Or `"older": "2026-11-01"` for everything last changed before a day, or `"all": true` |
| `{"archive": {"kind": "shelf", "all": true, "to": "FILE.tar.gz"}}` | the same, packed into a tarball first; the row keeps the archive's own fingerprint, so it can be held to your record later |
| `{"changed": true}` | what is new, edited or gone in your own folder since the last check (Willow's `what-changed`), one row of paths and fingerprints |

- **The kinds** are `shelf`, `made`, `packages`, `identities`, `jobs` and
  `index`. The index leaves no hole: it holds nothing your folder doesn't,
  and is built again when next needed. The runtime's own books (the log
  of what left, what you sealed to share, your names list) are never
  removed this way.
- **If the hole can't be written, nothing is removed.**
- **A session you let in can take a thing off its own project's shelf**
  (`shelf_remove`), and nothing else: it made those. The hole is recorded
  the same way.
- **Your own folder is checked at a session's start**, at most once an
  hour, on its own so the session never waits. So a file you deleted with
  any tool of yours leaves its hole, and `stale-answers` can say which
  sealed answer cited it. The first check fingerprints every file, in one
  row as large as the folder's list of names.

## Bringing in your notes, a calendar, or an export

Your Obsidian or Logseq vault, your calendar and contact files, or a Joplin,
Evernote or Google Keep export, can be written out as plain text in the
folder the record reads, so the next question finds them. This is yours to do, on your own files, so only your
door has it; a model's door and the assistant's hooks do not, and so can
never cause a file to be written into your folder.

    {"bring_in": {"kind": "notes", "from": "/path/to/vault", "as": "garden"}}
    {"bring_in": {"kind": "calendar", "from": "/path/to/calendars", "as": "family"}}
    {"bring_in": {"kind": "joplin", "from": "/path/to/folder/with/the/jex", "as": "joplin"}}
    {"brought_in": true}

The mirror goes in `brought-in/KIND-NAME/` inside the folder the record
reads, made by Willow's add-on for that kind, run by its command line. The answer says what it said: how many files were written and how
many skipped. The original is never written to or changed, here or by the
add-on. `brought_in` lists what was brought in, from where and when, and
`status` shows it under "Brought in". The list is `brought-in.json` beside
the record, so `backup` and `restore` carry it.

The kinds, and what each reads from the folder you point at:

| Kind | Reads |
|---|---|
| `notes` | an Obsidian or Logseq vault (`.md` files) |
| `calendar` | `.ics` events and `.vcf` contacts |
| `joplin` | a Joplin export (`.jex`), each note with its notebook and dates; the trash is left out |
| `evernote` | Evernote exports (`.enex`), each note with its notebook, tags and dates |
| `google-keep` | Google Keep notes from a Takeout (`.json`), each with its day and labels |
| `mastodon` | a Mastodon or Pixelfed archive's `outbox.json`: your posts as dated lines |
| `goodreads` | a Goodreads or StoryGraph export (`.csv`): what you read, when, and what you thought |
| `karakeep` | a Karakeep export (`.json`): bookmarks, notes and tags |
| `opml` | feed and podcast lists (`.opml`), a line a feed under its folder, and outliner exports |
| `takeout` | a Google Takeout's My Activity and YouTube history, as dated lines |
| `bookmarks` | browser bookmarks (an HTML or Firefox JSON export) and history, from a copy of its SQLite file |
| `zotero` | a copy of `zotero.sqlite`: items, notes and annotations, each with its citation |
| `code-graph` | codebase-memory-mcp's graph (a `.db` copy): each function, its file and line, and what it calls |
| `mail` | email files (`.eml`) and mailboxes (`.mbox`), each message with its sender, recipients, date and subject above its body; attachments are named, never read |
| `sms` | a phone's backup of its texts and calls (Android's SMS Backup & Restore files, or an iPhone backup's messages database), a section a person, a line a message |

Two of these hold other people's words, so think before you bring them in.
Email addresses and numbers are withheld from anything a model is given,
as everywhere; a name is withheld only if it is on your names list. Willow's
`mail` also keeps a map of where each passage came from, in a hidden folder
of the mirror (`.places/`); the kernel never reads it, so no question finds
it. For `sms` you may add `"me"` with your name (your own messages are `me`
otherwise) and `"tz"` with the zone they were sent in, such as
`America/Denver` (this machine's own otherwise).

It is refused, in plain words, when `from` is inside the record or your
folder, or holds them, or is the mirror itself; when the name is not one
plain folder name; when there is nothing it can read; and when a mirror of
that name is already there and was not made from the same folder (never
written over, and a folder you made yourself is never taken for one of its
own).

**A second run** over the same folder, under the same name, is safe, as the
add-ons make it: each note, calendar or export is written again with its
present text, a new one is added, and nothing is removed. A note you deleted from
the vault since stays in the mirror until you delete the mirror file
yourself. Nothing needs doing about the index: every question brings it
current first, and rebuilds it only when a file in the folder changed.
