# Changelog

## Unreleased

The first cut, built one piece at a time on 2026-11-17, each with its tests.

- **A report of your files.** `report` gives a model one of Willow's
  reports over the person's files, `todo` or `on-this-day`, the way a
  question goes (the person's ruling of 2026-11-17): unsealed, the model
  learns only that there is one; the report's own words, withheld, are
  proposed under a question that names those exact words and wait on the
  seal; sealed, they leave as one page. A report that would read
  differently now waits on a seal of its own. `stop` covers a report, the
  seal page shows one as "A report to share", and the person's `report`
  gives it as it is. `on-this-day` joins the pin. The first real `todo`
  report ran to 571 lines, most of them prose, so: `report-skip.txt` beside
  the record leaves folders and files out of every report; a report over
  20,000 characters is never proposed, and a model is told so without its
  size; and the pin moves to Willow `fca52619`, where `todo` 0.1.2 counts a
  mark only as it is written to mark something.
- **A shelf for each project.** A session puts what it makes (a report, a
  list, working notes) on the shelf of the folder it is working in:
  `shelve`, `shelf` and `take` on a model's door, with no seal, since
  nothing on a shelf was ever the person's files and nothing on it leaves.
  Shelves live under `BOX.runtime/shelf/`, beside the record and outside
  the folder questions read; nothing on one is written over; each thing
  says which session put it there; `backup` and `restore` carry them; and
  `shelves` and `take` on the person's door read any of it. A moment named
  in `capture.txt` now goes on the shelf, not to the seal. The MCP door
  tells the runtime the folder it was started in, and its tools can take
  two strings.
- **The check runs here.** `python check.py` is the check a change is held
  to, on this machine: Willow at its pin, lint, format, and the tests under
  each Python named. `--commit REV` checks a commit as committed, unpacked
  elsewhere. `check.py hook --write` saves a git hook that checks whatever
  is about to become `main` and refuses it when the check fails, with no
  server asked; the workflow on GitHub is a second opinion.
- **One place to keep things.** `capture` hands in one thing to keep (a
  note, a finding), from a model's door or the person's: it is proposed
  under a question of its own and waits on the seal. Sealed, the kernel
  writes it under `written/captured/` in the box, and `captured`, on the
  person's door only, reads it there. A model can't read it back.
- **A guard door.** `doors/guard.py` carries Claude Code's hooks around what
  the assistant does to one new verb, `event`, decided in the runtime by
  seven of Willow's hooks, now pinned. Before a tool call: `hook-guard` (the
  key, the record), `hook-leaks` (a secret in what is written), `hook-shell`
  (the commands in `deny.txt` beside the record), `hook-read-first` (an edit
  of a file not read) and `hook-errors` (a command that failed twice). At a
  prompt, through the prompt hook: `hook-feedback` proposes a correction for
  the person's seal. At a turn's end and the next start: `hook-handoff`. At
  a session's start and before a summary the model is told how many things
  wait on the seal, as a count. A blocked call goes on the sent log; a guard
  that can't run blocks; only a tool call is ever blocked. The two hook
  doors now face a host, with `context` and `event` and none of a model's
  verbs. `set_up.py` prints and writes the hooks. Not yet seen in a real
  client.
- **A seal page.** `python seal_page.py --box DIR` prints a link and opens a
  page, on this machine only, showing what waits on the person's seal: a
  session's actions, a page as it would leave, a model's sentence, each with
  the bytes the key would sign folded under it. **Seal** and **Decline** are
  the kernel's own commands, proved with the key the kernel reads; **Not
  now** writes nothing on the record. It is not a door, no door can import
  it, and the runtime still has no verb to seal. Held to Willow browse's
  table of who can reach it (127.0.0.1 only, a secret for each start as
  cookie and form field, Origin and Host checked, never framed, no script),
  in the tests and in a real Chrome.
- **What you've shared, on the seal page.** A second page lists each page
  the person was asked to share and where it stands, with **Stop sharing
  this** (the runtime's `stop`), and what has left, to whom and when (its
  `shared`). Held to the same table as the first.
- **A launcher for the seal page.** `seal_page.py launcher --box DIR` prints
  a double-click file for macOS, Windows and Linux; `--write` saves this
  machine's, never over one that differs. **Close this page** stops the
  page, and `--idle MINUTES` stops it when nobody has asked for that long.
- **Not now.** The person's `later` sets one waiting thing aside, beside
  the record and never on it, and `back` brings it back. `owed` and the
  needs-you card leave out what was set aside; `waiting` still shows it. One
  new refusal in plain words: `not_waiting`.
- **The needs-you card names the seal page**, as a command for the person's
  own terminal, never a link or its secret.
- **Setup that finishes.** `hosts.py` keeps Willow's hosts table (Cursor,
  Copilot, Codex, Gemini, OpenCode, Windsurf, Zed) pointed at `doors/mcp.py`.
  `set_up.py --write cursor` (or `claude-code`, or `all`) merges the MCP door
  into the home settings file and refuses when an entry by our name already
  differs; default still only prints. Cursor also gets session hooks.
- **Something needs you, in the client.** `owed` keeps the one-line count and
  adds a card of each waiting claim with its seal line, written to
  `needs-you.txt`. The session door takes `--host cursor`: `user_message` at
  session start, a desktop notice, and the same notice after this server's
  MCP tools. Claude Code still gets `systemMessage` only, never passage words.
- **Willow by its pin.** `willow.pin.json` pins Willow's commit and every
  file this runs (the kernel and twelve add-ons) by SHA-256. Every door
  refuses, in plain words, to run on a Willow whose files differ;
  `set_up.py` says so first; `willow_pin.py check` names each file, and
  `repin` is the one way to move it. CI checks out the pinned commit.
- **Preview before sealing.** The person's `preview` shows each waiting
  scope's page as it would leave, withheld, by place: the same texts a sealed
  page is held to. `waiting` points at it. Nothing is sealed or sent.
- **Restore.** The person's `restore` puts the runtime's zip from a backup
  back beside the box: checked first (flat names, every CRC, no key, no box,
  the sent log's chain), never written over a file that differs, each file
  read back. Three new refusals in plain words: `no_box`, `not_backup`,
  `restore_over`.
- **The runtime and its two lines.** Reading through Willow's kernel needs no
  grant; only a scope the person sealed leaves, whole, as one page.
- **Doors:** a pipe for the person; MCP over stdio and Claude Code's prompt
  hook for a model. A model's door learns whether the files hold a question,
  never what they say, until a page is sealed.
- **The model's way back:** one sentence, held by Willow's sentence-check,
  proposed through the kernel to wait for the person's seal. `draft` asks a
  model for it: the client's (MCP sampling) or one on this machine
  (`model.json`).
- **What leaves is written down**, chained, and can be pinned and checked;
  `shared` reads it back as places. Names, numbers and addresses are
  withheld from every page.
- **The person's verbs:** `waiting`, `scopes`, `stop`, `backup`, `models`,
  `pin`, `check`; every refusal in plain words with a next step; `set_up.py`
  prints what to paste into a client.
- **One seal a session.** `doors/session.py`, Claude Code's SessionEnd and
  SessionStart hooks, facing the person: the runtime's `close` bundles each
  session's actions with Willow's `session-seal` for one seal, and `owed`
  tells the person at the next start, in one line shown only to them, what
  waits. `set_up.py` prints both hooks. After a close, a model reads again
  before it can propose.
- **An index of the folder**, kept beside the box by Willow's
  `index-cache`: each read, and each session's close, is answered from it
  by `claude-code`'s `bite` while it is current, the kernel's own answer in
  seconds instead of half a minute. The kernel reads the folder when the
  index can't answer.
