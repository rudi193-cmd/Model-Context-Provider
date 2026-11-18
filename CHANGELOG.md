# Changelog

## Unreleased

The first cut, built one piece at a time on 2026-11-17, each with its tests.

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
