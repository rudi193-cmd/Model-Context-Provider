# Open: what was asked, what was built, what is left

This began as the handoff Grok wrote on 2026-11-17, copied out so each line
could be ticked and noted, and Grok's words are kept as they were. It has
since grown into the project's working list: what the owner threw in
along the way, what was found when each line was held to the code, and
the owner's rulings. A box is ticked when the thing is built here. A line
starting **Note** was added afterwards: what was found, and what it still
needs. Last held to the code on 2026-11-21. What is still open is
gathered at the end, under "Open now".

## Handoff: Model-Context-Provider (MCP → Provider)

**Repo:** `rudi193-cmd/Model-Context-Provider`
**Related:** Built on `willow-memory/Willow` (pinned commit + specific add-ons)
**Owner intent:** Evolve the baseline Provider into something *useful
day-to-day*, with the practical surface people expect from mature MCP
servers, while selectively pulling distinctive Willow strengths so it stands
out. Preserve the two core lines.

### The two lines (non-negotiable)

1. **A grant guards what leaves, never what is read.** Reading the person's
   material needs no grant. Only what leaves the machine is gated.
2. **Hooks/doors are doors, not verbs.** One local runtime decides. MCP,
   prompt hooks, pipe, session start/end are only transport.

Model never sees raw files. It only ever receives a sealed page (after human
seal with personal key). Answers are forced through sentence-check, then
proposed back and wait for another human seal.

### Current state of the repo

- Core: `runtime.py` (single decision point), thin doors (`doors/mcp.py`,
  `hook.py`, `pipe.py`, `session.py`), `seal_page.py` (human-only local UI),
  `set_up.py` + `hosts.py`, `willow_pin.py` + `willow.pin.json`.
- Already wired from Willow: approved-only, sentence-check, session-seal,
  index-cache, privacy/withhold, local-model/openai-compatible paths,
  backup, chained sent log + pin/check, its end sealed with each session.
- Design is intentionally inverted vs typical MCP: model proposes → human
  seals → only then does a page leave. Pure stdlib + pinned Willow. Doors
  decide nothing (enforced by tests).

**Note:** true as written, with one change since: a session the person let
in (one yes, for one session in one folder) is answered directly, withheld,
with no page sealed first. Also since: `doors/guard.py`, `check.py`,
`seal_prompt.py`, seven of Willow's hook add-ons and its `kart` in the pin
(see "Added since" and "Thrown in" below).

### Goal for next work

Move from "strong privacy baseline" to "useful every day" while keeping the
trust model:

- Have the things mature MCP servers have (memory/knowledge surface,
  task/work queue, better context injection, local drafting,
  status/overview, MCP Resources + Prompts).
- Pull selective Willow strengths so it is clearly different from the
  generic crowd.

### What's already built in Willow that can be added with relatively low work

High-leverage, already-complete stdlib add-ons that fit the pin + CLI
pattern:

- [x] **todo**
  - **Note:** not a task list. It is a read-only report of TODO, FIXME and
    "need to" lines already in the folder. Built as `report todo` on both
    doors: the person reads it as it is; a model learns there is one and is
    given it once the person seals it. Seen in a real session on
    2026-11-17: asked, sealed on the seal page, given. It was 571 lines of
    mostly prose, so there is now a skip list (`report-skip.txt`), a limit
    of 20,000 characters, and tighter marks in Willow's `todo` (0.1.2).
    Needs: the person's `report-skip.txt` for this record (commits, code
    and graph were 362 of the 571 lines).
- [x] **notes**
  - **Note:** an importer, not a notes surface: built as `bring_in` with
    `{"kind": "notes", ...}` and `brought_in`, on the person's door only. The
    mirror lands in `brought-in/notes-NAME/` in the folder the box reads. A
    second run over the same folder is safe (it overwrites, removes
    nothing); a different folder under the same name is refused. Not yet
    tried on a real vault.
- [x] **capture**
  - **Note:** built as `capture` / `captured`, but not with Willow's
    add-on. Willow's `capture` writes straight into the folder and caps a
    note at 500 characters; here a note is proposed through the kernel and
    waits on the seal, then lands under `written/captured/`. A model can
    hand one in, and read it back only once the person has sealed it
    (`notes`, below).
- [x] **people**
  - **Note:** built as `report people`: a line a person (how often, in how
    many files, over what dates), and its proposal says plainly that it
    names people. See "The `people` report" below.
- [x] **calendar**
  - **Note:** an importer (`.ics` events and `.vcf` contacts as dated
    lines), not a calendar: built with notes, as `bring_in` with
    `{"kind": "calendar", ...}`, into `brought-in/calendar-NAME/`. A
    recurring event is written once under its first date, so `coming-up`
    still counts each repeat. Not yet tried on a real calendar.
- [x] **on-this-day**
  - **Note:** built as `report on-this-day`, the same way as todo. Its
    sibling `coming-up` (dates in the next 14 days) wasn't in the list and
    is built too, as `report coming-up`; it loads Willow's `pieces` add-on
    from beside it, so both are pinned. On a record made from several
    places (`init --from`) it says, in plain words, that it reads one folder
    (`reads_one_folder`, Willow #383). Not yet tried in a real session.
- [x] **timeline**
  - **Note:** built 2026-11-18 as `timeline` on both doors: the person's
    writes the file whole; a session they let in has it made for them and
    is given it withheld. The owner's word: it is up to the person what
    goes in and out.
  - **Note:** tried over the real record the same day. Three loose words
    gave 787 lines, so: a session is given it in parts and by date, without
    what `report-skip.txt` leaves out; every word must be held before half
    is tried; and Willow's `timeline` 0.1.2 drops lines with no letter or
    digit.
- [ ] **milestones**
  - **Note:** a child's firsts by age, from notes. Read-only.
- [ ] **projects**
  - **Note:** about Willow stacks (a folder's records, stacks and runs),
    not general projects.
- [ ] **handover**
  - **Note:** also about Willow stacks: where one project's runs stand.
    Not a session-to-session handover; that is `hook-handoff`, now built.
- [ ] **batch-ask**
  - **Note:** already in the pin; index-cache and claude-code load its
    scan. Nothing more to wire unless asking many questions at once is
    wanted.
- [x] **pile-store / pile-serve** (performance)
  - **Note:** measured on the real folder 2026-11-18 (13,875 files,
    190,367 passages) and left out: reading the folder takes 1.4 seconds,
    loading a store and checking it 2.3. The time was elsewhere: `timeline`
    and `todo` dated every line of the folder, fixed in Willow (35 seconds
    to 8, 18 to 7). `on-this-day`, `coming-up` and `people` still take 16
    to 22 seconds, in the kernel's date reader; an early exit for a line
    with no four digits in a row would speed all three, and is the owner's
    to decide, being the kernel.
- [x] **share** (needs careful "leave" design)
  - **Note:** built 2026-11-18 on three rulings of the owner's: the person
    sends, and a model may put a package together for their seal; only
    sealed sentences go; what arrives is the person's to receive, then
    read by a session they let in. See "`share`" below.
- [x] **rss-out** (needs careful "leave" design)
  - **Note:** built 2026-11-18 as `feed` on both doors: sentences by
    default, everything sealed on the person's word. Nothing is served.
- [ ] **local-model / openai-compatible, mcp-lite, mcp-sampling, privacy,
  etc.** (many already partially used)
  - **Note:** local-model, openai-compatible and privacy are pinned and
    used. The MCP door is written by hand in the shape of mcp-lite and
    already does sampling.

### What still needs building / more design

- [x] First-class **sealed collection / knowledge surface** (model reads
  only after seal; can only propose writes)
  - **Note:** built. Proposing writes is `capture`; `notes` gives a model
    back the notes the person sealed, each asked of the kernel under its own
    question, withheld, whole, capped at 20,000 characters (the person's
    ruling of 2026-11-17). Nothing under `written/` is trusted. A thin
    wrapper over Willow's `notes` or `capture` add-ons did not fit: those
    mirror a vault and write straight into the folder. Not yet seen in a
    real client.
- [x] **Seal-gated task / work queue** (even a minimal one)
  - **Note:** built: `task_add`, `tasks`, `task_claim`, `task_done` for a
    model; `task`, `tasks`, `task_drop` for the person. The seal means "yes,
    do this" and grants nothing else; claims and results are bookkeeping
    and the shelf. Nothing in Willow holds a claim or a done state
    (night-batch, make-it-so, decisions, handover, projects), so this is new
    code with no new add-on. No worker. Not yet seen in a real client.
- [x] Proper **MCP Resources + Prompts**
  - **Note:** built. Resources: the three reports, the page last sealed,
    this project's shelf; each read is its verb. Prompts: `plate`, `ask`,
    `wrap_up`. Seen in Claude Code on 2026-11-17: a resource named with
    `@` gave the sealed todo report, and `plate` ran from the menu. Claude
    Code also gives its model a tool to list and read resources. `ask` was
    confusing to use, so each prompt's menu line now says what to type.
- [x] Richer single **status / overview** verb
  - **Note:** built as `status` on the person's door and a third page of
    the seal page, on top of Willow's own `digest` and `box-health`. Not
    yet seen on a real record.
- [x] Optional sealed/version-pinned skills/behaviours
  - **Note:** built as `skill_add`, `skills` and `skill`: a file, or a
    folder, sealed by its exact words. See "Skills" and "A skill as a
    folder" below.

### Suggested near-term order (from last discussion)

1. [x] todo + capture + notes (or thin sealed-collection wrapper)
   - **Note:** capture done; todo as above; kept notes read back as `notes`.
2. [x] people + calendar + on-this-day (everyday utility + delight)
3. [x] Minimal seal-gated task queue
4. [x] MCP Resources for sealed pages + a couple of prompts
5. [x] share and/or handover as distinctive Willow flavour
   - **Note:** `share` is built, and with it a job that travels in a
     package (kart's `write`, `take`, `run` and `gather`).

### Fun / differentiating angles

- [ ] on-this-day + timeline + milestones (personal history, extractive +
  sealed)
- [x] share with cryptographic checkability
- [ ] handover as multi-session primitive
  - **Note:** the session-to-session part is built (`hook-handoff`: a new
    session is told once where the last one ended).
- [x] sentence-check as a hard, visible guarantee
  - **Note:** hard (a struck sentence goes nowhere) and visible: the seal
    page lists each check run on a waiting sentence, from `checks.json`.
- [x] "What the model can never do" made inspectable
  - **Note:** done: `promises` on the person's door, and "What a model can
    never do" on the seal page. The verbs of each door are read from the
    code, and each promise names the test that holds it; a test fails if a
    named test is gone. `shared` still reads the sent log back in plain
    words.
- [x] Keep pure-stdlib + pin discipline
  - **Note:** held, with one stated exception: a job needs the `kartikeya`
    package and `bwrap`, on a Python the person names beside the record;
    without them `job` is refused and everything else runs. The pin is on
    Willow's main at `0c07be1` (#387), held by `willow_pin.py check`.

### Open design questions

- [x] Exact new verbs and how they map into `runtime.call` while preserving
  the two lines
  - **Note:** settled: three faces (person, model, host), each with its own
    verbs, and `call` passes the door's folder and session so a grant can
    be held to both.
- [x] How much friction is acceptable on the seal path for higher-volume
  surfaces (todo, calendar, etc.)
  - **Note:** the owner's ruling of 2026-11-17: a seal is for what the
    person truly needs to decide. One yes for a session covers reading;
    six things waiting after a day's work was too many.
- [x] Whether to expose any of the new surfaces as MCP Resources vs tools
  only
  - **Note:** both: reports, the last page, the shelf and skills are listed
    as resources, and each read is its verb.
- [ ] How aggressively to lean into Willow's personal-history add-ons vs
  more "work" oriented ones first

### Key files to look at first in the other session

- `README.md`, `AGENTS.md`, `NOTES.md`, `CHANGELOG.md`
- `runtime.py` (especially `call`, `read`/`propose`/`leave`/`answer`,
  `withhold`, `sent`)
- `doors/mcp.py`
- `seal_page.py`
- `willow.pin.json` + currently pinned add-ons
- Willow's `adapters/stdlib/{todo,notes,capture,people,calendar,on-this-day,handover,share,...}`

## Added since (not in the handoff)

- [x] **A shelf for each project** (`shelf_add`, `shelf_list`, `shelf_read`; `shelves`
  for the person): where a session puts the reports and working notes it
  makes for the project it is on. No seal, beside the record, never
  written over. The person's ruling of 2026-11-17: filed under the
  project; a model may read its own project's shelf back without a seal;
  it lives beside the record.
  - **Note:** seen in a real Claude Code session on 2026-11-17: a report
    shelved, listed and read back with no seal; the same name again kept
    as `NAME.2`; a name climbing out of the shelf refused.
  - **Note:** `shelf_remove` built 2026-11-18, for a session let in, with
    `stored`, `remove`, `archive` and `changed` on the person's door. The
    hole of what was removed goes on the record (Willow's new `removed`).

- [x] **Hooks around what the assistant does** (`doors/guard.py`, the
  `event` verb): hook-guard, hook-leaks, hook-shell, hook-read-first,
  hook-errors, hook-handoff, hook-feedback, and a count of what waits at a
  session's start and before a summary. Seen in a real Claude Code session.
- [x] **A fix in Willow:** hook-errors 0.1.2 reads a failed command's exit
  code from Claude Code's `error`. On Willow's main since #379.
- [x] **The check runs here** (`check.py`, and a git hook that holds `main`).

## Thrown in along the way (the owner's, 2026-11-17 and 18)

Things the owner said in passing while other work was going on, kept here
so none is lost. A box is ticked when it is built.

- [x] **Skills** (Willow pull request 375, merged 2026-11-18: five ideas,
  `skill-picks`, `server-picks`, `which-one`, `still-kept`, `my-installs`;
  none built). They find and judge other people's skills, tools and MCP
  servers. This project's part is the last step: a `skill` verb that seals
  a skill file by its exact words and gives a model only those bytes, so a
  skill that changed after it was vetted waits on a new seal.
  - **Note:** built 2026-11-18 on the owner's go: `skill_add` and `skills`
    on the person's door, `skill` on a model's. The owner named and sealed
    socratic-fork's `SKILL.md` with it the same day.
- [ ] **`my-installs`** (from the same pull request): what is installed on
  this machine (skills, plugins, hooks), what each can touch, and what
  changed since last looked. The audit half of the guard gap below.
  - **Needs:** building in Willow first; it is only an idea there.
  - **Context (2026-11-26, from the boxes):** the idea is in Willow's
    `adapters/planned.json` as `my-installs` (0.0.1, Privacy and safety,
    role `guards`, writes nothing, no network). Most of the map it needs is
    already in hand: `hosts.py` knows where 24 assistants keep their MCP
    settings, and codebase-memory-mcp's installer knows where about forty
    keep their hooks and skills too (`src/cli/cli.c` and
    `src/cli/agent_clients.c` there: Qoder's and Devin's hooks in their
    settings file, Copilot CLI's under `~/.copilot/hooks/`, Factory's in
    `~/.factory/hooks.json`, skills under `~/.agents/skills/`). Willow's
    `install-scripts` (0.1.1, the scripts a package would run on install)
    is the nearest built card. "What changed since you last looked" is
    index-cache's manifest of details and hashes, over those files.
- [ ] **Socratic** (the owner: "making the news recently"). On Willow's
  list as an idea: "asks you questions about your own notes instead of
  answering, each citing the passage it asked from". The owner's own
  `socratic-fork` is a skill of 697 questions.
  - **Note:** the prompt is built 2026-11-18, as `question_me`, and
    `socratic-fork`'s `SKILL.md` is the first skill named and sealed.
  - **Needs:** the owner to name the folder (`skill_add` with the folder's
    path), so its question files can be asked for.
- [x] **Kart** (the owner: "I completely forgot to bring Kart in, and that
  will fix a lot of our issues"; "it's got a card in Willow already").
  Willow's `adapters/deps/kart`: a job someone sent you, run in
  Kartikeya's sandbox over your own folder only once you seal it, its
  result yours to seal before it goes back. The sandbox sees the folder
  read-only and never the box or its key. It rides on `share`.
  - **Needs:** to be done with `share`, by the main session. It is what
    runs a sealed task (the queue has no worker), and what the guard can
    only approximate. It needs the `kartikeya` package and `bwrap`, run
    through Willow by command line.
  - **Note:** built 2026-11-18. Willow's kart learned `write` (a job of
    your own, sealed), `try` (run with no seal, proposing nothing) and a
    queue (`queue`, `work`, `status`), stopped a fleet's settings reaching
    a job, keeps a failed job's last line off the record, and puts back
    the limits a reload of systemd empties out of its resource group
    (all of it kart 0.1.3, once numbered as one step). Here: `job`, and `job_later` with `job_result` for a
    job too long to wait on, on a model's door, under a session's grant.
    Seen in a real session the same day: a job run, and three queued jobs
    worked in order.
- [x] **One yes for a session** (the owner, 2026-11-17: "the seal should be
  something for the user to really NEED to do, a true exit 42"; "per
  project folder, per session"; "just think of it like a normal mcp").
  - **Note:** `grant`, and `context` and `job` under it, built 2026-11-18
    beside the per-item seals, and seen in a real session: asked at the
    session's start, sealed once, and it held across a reconnect.
  - **Note:** `report`, `skill`, `notes` and the task tools answer under it
    too (2026-11-18). A task for another folder, a note to keep, a
    sentence back and a file that leaves still wait on a seal.
  - **Note:** a desktop dialog for the yes (`seal_prompt.py`, pinentry, a
    plain confirm by the owner's choice) built 2026-11-18; off until
    `ask-here` is beside the box. MCP elicitation was looked at and left
    out: a hook can answer it.
  - **Needs:** the per-item paths reviewed with the owner for what can
    go. The dialog seen once on a real desktop.
- [x] **A skill as a folder** (the owner: "yes, build the folder skill after
  kart lands"). socratic-fork's `SKILL.md` is a router to question files
  beside it that nothing could ask for.
  - **Note:** built 2026-11-18, both ways. Naming a folder seals its
    `SKILL.md` and, under it, each other text file by the fingerprint of
    its words; a model asks for a file by its name on that list. Under a
    session's grant the folder is given as it reads now.
- [ ] **Willow's demos of sharing** (the owner: "a few demos in Willow as
  well to pull how share should work"): `demo/johnson` (one report, five
  willows), `demo/shared-runs`, `demo/known-gaps`, `demo/craft-assembly`.
  - **Note:** `demo/johnson` and `share`'s README read before `share`
    was built. The other three demos have not been read.
- [x] **Depend on GitHub less.** The check and the hook that holds `main`
  are built and run here, and the check is the gate.
  - **Note:** the fifteen Willow commits this pin stands on (the hook
    add-ons, `todo`, `people`, `hook-guard`, `kart`, `timeline`, `removed`) are
    willow-memory/Willow#379, opened 2026-11-18 and merged 2026-11-19.
- [ ] **Quoted speech in the todo report.** About a dozen of the 91 lines
  are the owner quoted saying "I need to…" in a past session, not tasks.
  - **Needs:** the owner's yes; it is a change to Willow's `todo`, and it
    would also drop a real task that happens to be quoted.
  - **Context (2026-11-26, from the boxes):** Willow's `who-said` already reads a
    quote by its shape (a chat's stamp, a speech verb, or quotation marks;
    `adapters/stdlib/who-said/README.md:24`), so `todo` could leave out a
    line that shape calls a quote rather than learn quotes itself.
- [x] **The `people` report.** A line a person (how often, in how many
  files, over what dates), from one call to Willow: `people` 0.1.2 has a
  `--json`. Proposed on the task queue, sealed by the owner, and done from
  it: the first task the queue carried. Not yet seen over the real record.
- [x] **More reports, cheaply.** Built 2026-11-18: `ref-check`,
  `pii-audit`, `secrets-audit` and `minutes`, with `habits` in the pin for
  `minutes`. `pii-audit`'s last digits are kept on the person's door and left out for a model. `report()` now takes exit 42 as "found
  something", which is what Willow's audit add-ons say. That opens
  `ref-check`, `pii-audit` and `secrets-audit`; `minutes` fits as it is.
  Each is a line in `runtime.REPORTS` and a pin.
- [x] **More importers.** Built: `joplin`, `evernote` and `google-keep`,
  each by the command line `notes` takes (a line in `BRING_IN` and a pin),
  each run by hand on a small made-up export before it was added. `mail`
  and `sms` followed the same day. Others of Willow's readers also take
  that command line (`mastodon`, `goodreads`, `karakeep`, `opml`,
  `takeout` and more) and were not built here; each is the same two
  lines, once run by hand.
- [x] **The task queue's edges.** Listing tasks has no limit on its whole
  size; each `tasks` or `notes` call asks the kernel once a sealed thing,
  a row on the record each time.
  - **Note (size limit done):** `tasks` now gives at most `TASKS_MOST`
    (20,000) characters of words at once: the oldest tasks that fit, then
    `more: true` and nothing else about the rest (never a count). It is
    not refused whole, as `notes` is, since a session given no task can
    take none up. A task a session took up is always listed and weighs
    nothing (the owner's ruling, 2026-11-18).
  - **Note (rows done):** a yes the kernel gave is remembered by the door
    that asked, in memory, while the proposal it was for reads the same,
    so a sealed task or a kept note is asked of the kernel once and not on
    every call; what waits is asked once a call. A third of a day's rows
    on the real record were those two askings (2026-11-18).
- [x] **`share`**: built 2026-11-18. The person's door has `share_id`,
  `share_person`, `share_send`, `share_receive`, `share_forward` and
  `shares`; a model's has `share_propose` (a package for the person's
  seal, for someone they named, never by key) and `share_received` (under
  a session's grant).
  - **Note:** `share_rotate` and `share_witness` built the same day.
    `backup` leaves the identity out, so the owner keeps a copy of
    `share.id` themselves.
  - **Note:** corrections (`replaces`, and `forward_with` on receiving
    one) and a job that travels (`job_write`, `job_take`, `job_run`,
    `job_gather`, on the person's door) built the same day. The owner's
    ruling: only numbers go back from a job.
  - **Needs:** trying it between two real records. Not built: kart's
    `wasm` and noised counts (the third part of `demo/johnson`).
- [x] **`timeline` and `rss-out`**: built 2026-11-18 as `timeline` and
  `feed`, on both doors. Not yet tried over the real record.

- [x] **Too many tools** (the owner, 2026-11-18: "we're up to 26 tools,
  and I know there is an upper limit on what most models can keep track
  of").
  - **Note:** built the same day. Twelve tools over the same 26 verbs,
    nine on by default, in groups the person switches (`tools`); a group
    that is off is refused, not only unlisted. Not yet seen in a client
    other than Claude Code, which loads tool definitions only when needed
    and so hid the cost.

## Still loose

- [ ] The guard beside the record stops careless tool writes, not code a
  model runs: a path built at run time (`$VAR`, a substitution, a script it
  writes), a `cd` earlier in the command, and `mv -t DIR src` still get
  through. Kart's sandbox is the real fix, and `job` now runs there; the
  assistant's own shell tool does not. The system's own answer, a key and
  files the assistant's account can't touch, is designed below ("The key in
  an account of its own").
- [x] Push the Willow commits, or the GitHub workflow can't find the pinned
  commit. Done: every commit the pin names is on Willow's main.
- [ ] `hook-shell` is off until there is a `deny.txt` beside the record.
  - **Context (2026-11-26, from the boxes):** `hook-shell` takes its rules as `--deny`
    (`adapters/stdlib/hook-shell/README.md:23`). The rules Willow's own
    guard study ran with, a place to start a `deny.txt` from: `rm -rf`,
    `git push --force` and a pipe into `sh`
    (`demo/five-repos/reports/08-guards.md:13`).
- [ ] A correction ("No, …") hasn't been tried in a real session.
- [x] The guard covers the box, not `BOX.runtime` (`stopped.json`,
  `scopes.json`, `names.txt`, `deny.txt`). Closed for careless or direct
  tool calls: `guards()` gives Willow's `hook-guard` `--also BOX.runtime`, so
  a Write, Edit or a command that redirects into or runs `rm`, `mv`, `cp`,
  `tee`, `sed -i` on it is blocked (rule `beside-write`); reading it is
  fine; the runtime itself still writes there. `mv` out of a protected
  folder is now caught too. Not closed, and said so in the README: a `cd`
  earlier in a command isn't followed, `$VAR` paths aren't filled in, and
  code a model runs that builds a path at run time gets through. The pin
  moved to Willow's `hook-guard` 0.1.1.
- [x] `uv.lock` is untracked: commit it or ignore it.
  - **Note:** ignored, on the owner's word: it locks only the dev tools,
    and nothing here reads it.
- [ ] Not yet seen in a real client: reading notes back, bringing a vault
  in, the checks on a sentence, "What a model can never do", the desktop
  dialog, a folder skill, and a task added under a grant.
- [ ] **From putting kart through its paces (2026-11-18):**
  - Kartikeya's scan of a job missed a listening socket and a printed
    secret. Written up for the owner; not this project's code.
  - The privacy filter turns a run of four-digit numbers into
    `[withheld: card]`, so a job that prints years or sizes reads oddly.
  - [x] A job's output is given up to 20,000 characters; a smaller default,
    with more on asking, would cost less. Done: `job` and `job_result` give
    4,000 characters (`JOB_GIVEN`), cut at a whole line, and say so in
    `cut`; `more: yes` gives up to the 20,000 (`job` runs again, `result`
    reads again). Still refused over 20,000.
    - **Note:** 4,000 was held to what Willow's demos kept of their runs
      (`kept`, `shared-runs`, `small-models`, `want-finders`: 85 printed
      outputs, median about 1,000 characters). It gives 89% whole; 8,000
      gives 92% and 20,000 gives 96%. The owner agreed, 2026-11-18. Three
      of the 85 are over 20,000 and would be refused whole.
  - The Python the person names for jobs is visible inside the sandbox
    with its packages (said in the README).
  - A fleet on an older Kartikeya (0.3.2) runs a job with no limits when
    its resource group isn't ready, and says nothing.
  - Not yet seen live: kart putting back its limits after a reload of
    systemd, and a refused worker's words coming back with `job_result`.

## Open now

Two lists, kept apart on the owner's word (2026-11-18): what is owed, and
what was found along the way and not asked for. Something found while
working goes on the second list unless the owner says otherwise.

### Owed

Nothing, as of 2026-11-19. Still under "Not yet seen in a real client"
above, for whenever the owner is at the keys: the desktop dialog, a
folder skill, `share_forward` and a correction, a job that travels,
`stored`/`remove`/`archive`, and the `mail` and `sms` importers.

Tried 2026-11-19, through the doors in a cloud container over a made-up
record, never sealing, so not yet in a real client:
- a folder skill: a key file (`id_ed25519`) was listed and given, and hid
  the file after it; both fixed (below);
- `stored`, `remove` and `archive`: each hole on the record, the archive's
  own fingerprint kept, a second remove and a path out of the kind refused;
- the `mail` and `sms` importers: the mirrors as their cards say, an
  attachment named and never read, emails and phone numbers withheld on
  the page; "Gate code is 4471" was not, which is Willow's `privacy`
  (willow-memory/Willow#380, the pin moved with it).
Not tried there: the desktop dialog (no desktop), `share_forward` and a
correction (they need sealed sentences), and a job (kart's sandbox needs
`bwrap`, which the container had not).

Done 2026-11-19, each from that session, with tests that fail without it:
- `withhold` hands back every text in its place: an unterminated key in
  one passage took the separators after it, so later passages came back
  under other passages' places, or not at all.
- A key, by its kind or by a private key's words, is never listed in a
  skill nor named as one.
- What a model hands in has an end: a note at most 20,000 characters, at
  most 50 waiting at once, a project's shelf at most 200 things or 50 MB
  (40 MB had gone in, in seconds, from a session never let in).
- A JSON-RPC batch, or JSON that is no object, is answered `invalid
  request` rather than left without a reply.
- A model's client is told more before it calls anything: `instructions`
  at initialize (with the hooks and without), annotations on each tool,
  the runtime's limits in each schema, and a version with the pinned
  Willow commit.
- A refusal names what the person types (`provider waiting`, the seal
  page), and speaks to them on their own door.
- `nothing_to_scope` says the last question found nothing, or something
  else was asked since.
- The strict answer's cite rule, on the owner's ruling (below).
- The README says which numbers are withheld, not all of them.

Done 2026-11-18: `share` was tried between the owner's real record and a
second one made for the test (an identity each, each named on the other, a
sealed sentence sent, received and listed on both sides), and `feed` was
written from the real record. The owner ran each step and said all went
through; `timeline` had been seen over the real folder earlier that day.

Done 2026-11-18: the per-item seal paths were reviewed. A report's own
seal went, and naming a skill became the yes; a page for a question, a
kept note, a task, a kept answer and a package to share stay sealed one at
a time. Not built with it: a button on the seal page to stop a skill
(`{"stop": "NAME"}` on the pipe does it).

### Could do, not asked for

- ~~**The guard door, unwired by an assistant.**~~ Done 2026-11-21, from
  the Grove's one-box design (threat 3, "the doors can be removed"): an
  Edit of `~/.claude/settings.json` passed every guard, and removed them
  all. `set_up.py --write managed` writes the hooks for Claude Code's
  managed settings with the line that installs them, and `check` names
  where the guard door is. Not built from that design: "door missing", a
  session whose turns come with no door called, reported loudly.
- ~~**The person's own door, run by a model's shell.**~~ Done 2026-11-21:
  `runtime.own_doors_guard()`, asked before Willow's guards, blocks a tool
  call that runs the pipe, the `provider` command, the seal page or the
  seal prompt (as the program, past `env`, `timeout` and the like, or the
  script an interpreter is handed), naming the door, on the sent log by
  whom. Reading their files, and the word anywhere else, is let by. A
  script the model writes, or `python -c`, gets past it, as past
  `hook-guard`. `tests/test_guard.py` holds both sides.
- ~~**A record made with `--from` and the Provider's backup.**~~ Done
  2026-11-21, and wider than backup: on a record of two sources, backup,
  `coming-up`, `pii-audit`, `secrets-audit`, `ref-check` and `timeline`
  each passed a scrap of Willow's traceback to the person. `one_folder()`
  reads the kernel's own refusal (CONST-VI-9) in what the add-on said and
  answers `reads_one_folder` in plain words; no list of add-ons is kept,
  so each one Willow fixes under #383 simply starts working.
- The check, faster still: Willow's `test-impact` (only the tests a change
  can reach, first) and `ci-memo` are written around Willow's own layout
  and were not used; `slow-tests` reads the timing file the check now
  keeps. The largest test file (`tests/test_grant.py`) bounds a part:
  cutting by test, not by file, would even the parts further.

- **From a push on a model's tools over the real record (2026-11-18).**
  What held: the sandbox (a write into the folder and a fetch both
  failed), a path off the shelf, a job's long print cut at a whole line,
  a task already done, a missing argument named. Where they could be
  better:
  - (Fixed the same day: an empty question read as a record that
    wouldn't open, and `answer` with no sealed page blamed `WILLOW`.)
  - (Fixed the same day: a refusal a model can put right itself now says
    so to it, with no "Tell the person"; `timeline`'s says what each
    argument is.)
  - ~~`timeline` with `since` says `empty` when no line falls in those days,
    yet writes the whole timeline to a file (150 KB here) and names it.
    Each asking leaves a file in `made/`.~~ **Done 2026-11-26:** an empty answer makes no file and names none.
  - ~~`report` names are held to their exact case (`Todo` is refused).
    (The names are in the report tool's schema since 2026-11-19, so a
    model is told them before it asks; `Todo` is still refused.)~~ **Done 2026-11-26:** a name in any case.
  - `minutes` is over the most shared at once on the real folder, and a
    report has no parts as a timeline has, so a session let in gets none
    of it.
  - A timeline counts front-matter lines (`metadata:`, `node_type:`) as
    lines about the matter. Willow's `timeline`, by passage.
  - (Fixed 2026-11-19: after a reconnect the client still showed the
    older descriptions of `report`, `context` and `skill`. The door told a
    client the list changed only when a tool's name did, and only within
    one run. It now keeps the fingerprint of the whole list it last sent,
    names, words, schemas and hints, and a new session whose list differs
    is told so at once.)

- ~~A strict answer must cite every passage on its page~~, which could
  force a clause that has nothing to do with the question (seen
  2026-11-18).
  - **Ruled 2026-11-19, by the owner:** a sentence cites at least one
    passage on its page, and need not cite them all. Every other check
    stands over the passages it cites (each cite on the page, nothing they
    lack); the others are sentence-check's earlier boxes, whose words
    count only when cited. With it, as asked: the seal page lists beside
    the sentence each passage it left out, by file and id, never words.

- Fewer rows on the record still: a read-only way to ask the kernel what
  is sealed and what waits (a Willow add-on), and a switch for which hooks
  are on, as the tool groups have. Measure what is left first.
  **Context (2026-11-26, from the boxes):** the rows come from `kernel.py out`, which
  appends an `out` row each time it is asked what waits
  (`kernel.py:1202` on Willow's branch), and the runtime asks it whenever its note of what
  waits is cleared (`OWED`, `runtime.py:46`): 595 times in one run of the
  tests. A read-only add-on would answer from the same `read`, `sealed` and
  `waiting` the kernel's `out` uses, without the `append`.
- ~~More importers that fit by their card, none run by hand yet: `mastodon`,
  `goodreads`, `karakeep`, `opml`, `takeout`, `bookmarks`, `zotero`.~~
  **Done 2026-11-26:** each is a `bring_in` kind, and so is `code-graph`
  (Willow's `codebase-memory`, codebase-memory-mcp's graph), each pinned and
  held by a test that brings a small export in, finds it by a question,
  and leaves the original as it was. Not yet run on a real export.
  **Context (2026-11-26, from the boxes):** each is a built Willow card at 0.1.0 that
  writes only to its `--to`: `mastodon` (an account archive's
  `outbox.json`, posts as dated lines), `goodreads` (Goodreads and
  StoryGraph exports), `karakeep` (its JSON export), `opml` (feed and
  podcast lists, outliner exports), `takeout` (Google's My Activity and
  YouTube history), `bookmarks` (HTML and Firefox exports, and history from
  a copy of its SQLite file) and `zotero` (a copy of `zotero.sqlite`, with
  each item's citation). Wiring one is a line in `BRING_IN`
  (`runtime.py:2182`, as `mail` and `sms` are), its card added to the pin
  (`willow_pin.py repin --add NAME`), and a test that brings one in.
- Not looked at: `milestones`, `projects`, `handover`. `pile-store` was
  measured and left out (no gain on the real folder).
  **Context (2026-11-26, from the boxes):** `milestones` (0.1.1, uses `habits`) is a
  child's firsts, words and heights by age, and writes nothing. `projects`
  (0.1.1) and `handover` (0.1.2) read a folder of projects, each its own
  folder holding its record, its stack files and the folders it ran them
  into (`projects.py` `find`). Run over the boxes of `boxes/lay.py`, it
  found the nine records but none of their stacks or runs, since `lay.py`
  keeps the stacks and runs apart from the boxes. Laid one folder a
  repository (its box, `orient.md`, `owes.md`, `ask.md`, its runs),
  `handover` would say where each repository's stacks stand, with nothing
  built.
  **Done 2026-11-26:** `lay.py` lays each repository so; `projects --home
  WORK` lists every one's record, stacks and last runs, and `handover
  --project WORK/NAME` says what each stack flagged, with the run's file.
  `milestones` is left: it reads a child's notes, not these.
- Willow's `rss-out` can write inside the record's folder; the runtime
  refuses that, the add-on itself does not.
  **Context (2026-11-26, from the boxes):** still so: `rss_out.py` opens `--to` with
  `O_CREAT | O_EXCL` wherever it names (lines 147 to 157), with no check
  that it is outside the folder the box reads. index-cache's `within` is a
  check of that kind, by strings.

- **The seal page, read as the person on a phone (2026-11-20).** From its
  own HTML rendered over a throwaway record, at 390 pixels, in headless
  Chromium. Several break the plain-words rule the refusals are held to
  (no `bite`, `kernel`, `proposal:`):
  1. A session's card says what was done in the kernel's words: "2 × bite:
     empty, 4 × bite: served, 1 × boot, 4 × out, 5 × proposal: pass, 1 ×
     seal". In the person's: questions asked of their files and how many
     found something, things given to a model, things handed in, sealed.
  2. A model's sentence's card ends on "the page of proposal:" and 64 hex
     digits, "(page sha256 …); sentence-check held it". The checks above
     it say what held; it could name the question the page was sealed for.
  3. A page to share shows the page's own markup: `## car.md`, `car.md:1`
     and its code fences. The file as a heading and the passage as a quote.
  4. No count at the top, and the cards in the order they came: a session
     asking to read, the one with most at stake, can be anywhere. A line
     saying how many wait, and grants first.
  5. A note's card is headed "A suggestion" and titled "a note to keep".
  6. Each card ends in two to four grey paragraphs, so on a phone its
     buttons are far from what they decide. The detail could fold into
     "Exactly what you'd be sealing", one line left above the buttons.
  1, 2, 5 and the count are wording; 3, 4's order and 6 are layout, to be
  seen as a mock-up first. None changes what a seal does.
  **Context (2026-11-26, from the boxes):** 1 is built at `seal_page.py:418`, from a
  session's `came_of` counts in the kernel's own names; 5 is the
  `suggestion` card at `seal_page.py:534`. willow-mcp's approvals page and
  its terminal one answer "what does pressing this row do" from one module
  both use, `gates_actions.py` (`describe` and `apply`; its commit
  `bfd9a3bf`), with its tests: the shape for 4 and 6 to keep the page and
  any other way in to it saying the same thing.
  **Done 2026-11-26: 1, 2 and 5, and the count.** A session's card says
  what was done in the person's words (`done_said`: questions asked of
  their files and how many found something, things handed in for their
  seal, sealed, declined; the kernel's bookkeeping left out); a model's
  sentence names the files of the page it was said of (from the scope's
  cites and the record's bites, never a passage's words), its claim kept
  as it is sealed; a note is headed "A note to keep"; and a line says how
  many things wait. 3, 4's order and 6 wait on a mock-up.

- **The model's side, read as a model in a whole session (2026-11-20).**
  The MCP door driven from initialize to the shelf over a throwaway record,
  a page and a session's yes sealed with the test key between calls. A
  refusal carries `say` and `next`; most of what stalls is in replies that
  aren't refusals:
  1. A struck answer gives no way forward: `"nothing the boxes lack":
     "failed: comes is no box's"`, with no `say` or `next`. "Box" is
     sentence-check's word, never the model's, and the word was on the
     page, in the passage the sentence didn't cite. It could say so:
     "comes isn't in the passage you cited; it is in 5015f34a7102". With
     the ruling that a sentence may cite part of its page, that is the
     next step.
  2. A reply that waits (`propose`, `grant`, `note keep`) gives a 64-hex
     seal id and nothing to tell the person. It could carry a `next` as a
     refusal does: what waits, for which question, on their seal page.
  3. The sealed page comes as markup (ids in backticks beside
     "human-sealed", passages in code fences) that the model must take
     apart to cite. The same reply could carry the passages as data: id,
     file, text.
  4. `context` not let in says only `populated`, with no next step, where
     `timeline`'s refusal says to ask with `grant`.
  5. Under a yes, "what is left to do in the garden" gave the frost line,
     not the line marked to do: the kernel's rank, by design. Nothing
     tells a model `report todo` is for that; the tools' words could.
  1 and 2 matter most.
  **Context (2026-11-26, from the boxes):** for 1, a struck answer comes back at
  `runtime.py:1777` as its checks alone, while the passages the sentence
  left uncited are in hand above it (`left`, `runtime.py:1758`): the
  one holding the word the check names can be found there and named. The
  drafting path already turns the checks into a reason and a second try
  (`runtime.py:827` to `832`).
  **Done 2026-11-26: 1, 2 and 4.** A reply to a model that isn't a refusal
  but would leave it stuck now carries `say` and `next` (`runtime.ahead`): a
  struck sentence says what failed and names, by its id, the uncited
  passage on the page that holds each word it added (`in_uncited`); a reply
  that waits says on whom and where; a bare `populated` names `grant` and
  `page`'s `propose`. tests/test_ahead.py holds them, and that the words
  added carry none of the files'. 3 is done since 2026-11-25 (`passages`).

- **The broad fix for both lists, and other ways to see it (2026-11-20).**
  Asked of Claude after the two lists above; the owner is working on the
  fix from another angle, so these are views to weigh, not a plan.
  - **One translation at the edge.** Both lists are the inside leaking
    out: `bite`, `box`, `proposal:` and a hash, `came_of`, a page's
    markup. Refusals don't leak because they pass through `PLAIN` and
    `test_plain` holds every code to plain words. Everything else never
    did. Every state, not only a refusal, could carry `say` and `next`
    for its reader (model and person), held by a test the same way; name
    things by what they are about (the question, the folder), not by an
    id, from what is kept beside the record since the record keeps no
    question's words; prose for the reader and data for a machine (a
    page's passages as id, file, text); what is at stake first, the
    detail folded under "Exactly what you'd be sealing".
  - **The person's jobs, not the system's verbs.** List the few things the
    person comes to do (let an assistant work on these notes; what did it
    see this week; take that back) and count the steps each takes now. It
    asks whether a reply should be seen at all, not how it reads.
  - **Decisions, not screens.** Each card is a decision: show what the
    person needs to make it well (what leaves, to whom, for how long, and
    whether it can be undone) and nothing else. A grant's card says
    "until the session ends" but not what has been read so far.
  - **The model as the interface.** Most people won't open the seal page;
    they hear of it from their assistant. So a reply to a model is what it
    should say to the person: write each as that sentence. A waiting reply
    with a seal id fails at once.
  - **Dead ends, and getting out of them.** Every reply where the reader
    can't act next without knowing more (a bare `sealed`, a struck
    answer, `populated`), held by a test as `test_plain` holds refusals.
  - **Names at birth.** A scope, a grant or a note gets only a hash when
    it is made. A handle given then (the question, the folder, a note's
    first words), kept beside the record, and most of the display needs
    no translating.
  - **What the protocol already offers.** MCP has elicitation (a client
    asks the person natively) and resource subscriptions (a client is
    told something changed): a yes asked and settled in the assistant the
    person already uses, the page for review. Elicitation was left out
    because a hook can answer it, which is the right worry, so it needs
    care.
  - **Measure it, as Willow's studies do.** Freeze a few real tasks, have
    a few models and the person do them cold, count steps, dead ends and
    wrong turns, change one thing, run again: the only view that says
    whether a fix helped rather than read better.
  Claude's pairing: the translation layer with the model as the
  interface (it settles who each sentence is for, so the two lists become
  one), then measuring it.

- **From the repositories beside it (2026-11-25).** Asked of the boxes
  over the six repositories worked on beside this one and the MCP
  specification ([boxes/](../boxes/README.md)). Built that day: the seal
  page offered in the person's assistant (URL elicitation), a page's
  passages as data, and seventeen more assistants from codebase-memory-mcp's
  installer. The rest, each a lead with where it came from:
  - **The assistants left out of that table.** Kilo Code, Crush, OpenClaw,
    Pochi, Amp and Mistral Vibe write servers in shapes whose field for the
    environment isn't known (codebase-memory-mcp writes none, so its code
    can't say), and the door needs `WILLOW` there; Goose, Hermes and
    Continue keep YAML, which the standard library can't edit safely; TRAE,
    Roo Code, Sourcegraph Cody and Visual Studio have no fixed path. Each
    could be shown to paste once its environment field is confirmed.
  - **Prompt hooks for more of them.** codebase-memory-mcp installs hooks
    that add context for Qoder, Qwen Code, Devin, Factory Droid and GitLab
    Duo in Claude Code's shape (`hookSpecificOutput.additionalContext`),
    Kimi as plain text, Hermes as `{"context": …}` and Cline as
    `contextModification` (its `hook_augment.c`). `doors/hook.py --host`
    speaks three dialects now; the first five may need only the Claude
    one, each to be tried.
  - **MCP 2026-07-28, the move to plan.** The door speaks 2025-11-25 and
    older; the newest version makes the protocol stateless. No
    `initialize`: each request carries its version and the client's
    capabilities in `_meta`, and a server answers `server/discover`.
    Server-initiated requests (`sampling/createMessage`,
    `elicitation/create`) give way to multi round-trip requests: a result
    of `resultType: "input_required"` that the client answers and sends
    back. Every result carries `resultType`; list and read results carry
    `ttlMs` and `cacheScope`; `resources/subscribe` becomes
    `subscriptions/listen`; tasks move to an extension
    (`io.modelcontextprotocol/tasks`). The drafting through sampling and
    the pointing both ride on server-initiated requests, so both change
    shape. Not urgent: clients still speak the older versions.
    (`docs/specification/2026-07-28/changelog.mdx` in the spec.)
    **Context (2026-11-26, from the boxes):** the spec pages are `basic/patterns/mrtr.mdx`
    (multi round-trip requests), `server/discover.mdx` and
    `basic/patterns/subscriptions.mdx` under `docs/specification/2026-07-28`;
    the door's code they would change is `doors/mcp.py:223` (initialize),
    `:289` (`Asker`, sampling) and `:328` (`Pointer`, the seal page).
  - ~~**Tell the client when the seal is made.**~~ **Done 2026-11-26:** on
    the next request after the person seals or declines what they were
    shown, the door sends it (`runtime.settled`, from the record's own
    rows). URL elicitation has
    `notifications/elicitation/complete` for when the out-of-band part is
    done. The runtime could send it when the person seals or declines
    what they were pointed at, so their assistant can say so; it needs a
    way to see the seal land while the door waits for the next request.
    **Context (2026-11-26, from the boxes):** the notification is
    `notifications/elicitation/complete`, optional, carrying the
    `elicitationId` (`docs/specification/2025-11-25/client/elicitation.mdx:398`);
    the runtime makes that id (`point_person`), so it can say which.
  - **The tasks extension and the task queue.** SEP-1686's tasks (durable
    requests, polled) and this project's `task_add`/`task_claim`/
    `task_done` answer different questions (a long call, a job the person
    said yes to); whether one should be spoken as the other is open.
  - **willow-mcp's patterns, to read before taking.** It needs Python 3.11
    and `cryptography`, so no code comes over as it is; only its docstrings
    were read. `gates_actions` gives the live HTML page and the terminal UI
    one tested answer for what each row does: a shape for the seal page's
    layout items (grants first, a count, the detail folded). Its
    `egress_authorization` binds an approval to one task id and the exact
    task text, single-use by the row's own state: close to step 3 of "my
    rig", and to a grant that can't be used twice. `build_lease` is
    time-boxed, where a grant here lasts "until the session ends".
  - ~~**codebase-memory-mcp's graph as a report.**~~ **Done 2026-11-26**
    as the `bring_in` kind `code-graph`, a source the record reads rather
    than a report. Willow's
    `codebase-memory` add-on mirrors its SQLite graph as passages (each
    function, its file and line, what it calls); for a person whose folder
    is code, a `report` of it, or a source of the record, would answer
    "what calls this" without a page of the code.
  - **The check, by test and not by file.** cpython splits one large test
    module into a package of files so its runner can run them in parallel
    (`Lib/test/test_io/__init__.py:3`); `tests/test_grant.py`, which bounds
    a part of `check.py`, could be split the same way. Its runner also
    kills a worker that has said nothing for a while
    (`Lib/test/libregrtest/run_workers.py`), which `check.py`'s parts don't.
  - **A change past the noise.** pyperformance compares two runs with a
    two-tailed t-test at 95% (`doc/usage.rst:555`): the rule `model-drift`
    needs for "only a change past the rig's own noise counts", and the one
    a "measure it" study would use.

### A model on the person's own rig (designed 2026-11-21, not built)

**Why.** People run very large models on rigs of their own: a machine
with the GPUs in another room, reached over the home network, with the
person's laptop running the Provider. `on_this_machine()` takes only
`localhost` and loopback addresses, so a rig at `192.168.1.20` is refused
like a cloud server, though it is the person's own hardware.
[background.md](background.md) names "someone else's server" as not yet,
and not this third case. It counts more as hosted models get dearer: the
Grove's build order (the moat is context, the model last and smallest) is
the side of that bet this project is already on.

**What "only this machine" stood for.** Two questions, answered by one
address check:
- *Is this the model the person chose and tested?* Willow's cards answer
  this by what a model is, not where it runs.
- *Can anyone else read the page on its way?* The cards don't answer
  this; the path does.

**What Willow already has.** Each is a card, used as it is:

| Card | What it gives a rig |
|---|---|
| `weights-card` | a card from the weights file's own header: architecture, quantization, context length, licence and SHA-256; run on the rig |
| `weights-pin` | on the rig, in front of its server (`weights_pin.py --card … && llama-server -m …`): weights that differ from their card never run |
| `model-card` | the model behind each suggestion named on the record: weights hash, where it runs, licence |
| `model-exam` | any model scored against the answers the person already sealed, before they trust it; it reaches the endpoint they configure |
| `model-drift` | frozen questions asked again now and then, flagging answers that change while the name and card stay the same: a model swapped on the rig |
| `model-shelf`, `model-fit`, `model-quantized` | what a machine has, whether a model fits, and the smallest quantization that still gets the box's own questions right |
| `openai-compatible` | an endpoint of the person's choosing, its card saying where it reaches |

**What none of them gives.** The laptop can't see the rig's weights:
`weights-pin` runs there, so the laptop has the rig's word for the hash,
not proof. And Ollama, llama.cpp and vLLM usually serve plain HTTP, so on
a shared network anyone else on it can read a sealed page as it passes,
and another box could take the rig's address.

**The way that works today, with no code: a tunnel.**

    ssh -N -L 11434:localhost:11434 me@rig

The Provider then asks `http://127.0.0.1:11434/v1`, which is loopback, so
it is allowed. The wire is encrypted, and SSH's host key says it is the
rig, once its fingerprint has been checked the first time (before that it
is the first answer's word). Owed for it: a paragraph in the README,
`set_up.py --model`'s refusal of an address off this machine saying "a
model on another machine of yours: tunnel it", and a try end to end.

**Two holes in the tunnel as written** (found 2026-11-21, by research and
the boxes):
- *Shadowing.* Anything already listening on that loopback port (a local
  Ollama on 11434 is the usual one) passes `on_this_machine`, and a
  tunnel that failed to bind says so only in the terminal that ran it:
  the page goes to the wrong server, which is still this machine. So the
  tunnel takes `-o ExitOnForwardFailure=yes` and a port nothing else uses
  (`-L 21434:localhost:11434`), and the check at each draft is the
  sealed weights hash against what the server says it serves (Ollama's
  `/api/show` names the blob by its SHA-256), not the address.
- *The host key.* `-o StrictHostKeyChecking=yes` with a known-hosts file
  of the rig's alone, its fingerprint read once off the rig's own screen;
  the fingerprint is what step 3 seals.

**The way to build: "my rig", sealed.**
1. *On the rig:* `weights-card` writes the card, and `weights-pin` stands
   in front of the server.
2. *On the laptop:* the person runs `model-exam` against their own sealed
   answers, through the path in step 3.
3. *Named once, sealed:* the rig goes into `model.json` as a proposal
   through the kernel, like a session's grant, holding the card's SHA-256,
   the exam's score, and the path: an SSH tunnel with the rig's host-key
   fingerprint, or HTTPS with the rig's certificate pinned by its SHA-256.
   Python's standard library pins one cleanly: that certificate as the
   only trust anchor (`load_verify_locations`), or the peer certificate's
   SHA-256 compared after the handshake, which proves the rig holds its
   key. The seal names the certificate, not an address, so a Tailscale
   `100.64/10` or an IPv6 address needs no rule of its own. Plain HTTP off
   this machine stays refused, and so do redirects. A pinned certificate
   proves the rig to the laptop, not the laptop to the rig: the server
   takes an API key (`llama-server` and vLLM have `--api-key`) or mTLS,
   and Ollama, which has neither, stays behind the tunnel.
4. *Every draft:* the page goes only by that path; the sent log says "to
   your rig at …"; withholding is as it is now; the record names the model
   by `model-card`.
5. *Now and then:* `model-drift` asks its frozen questions; a changed
   answer stops the rig until the person looks, and looking is a seal.
   Temperature 0 is not deterministic (batch size, cache state, a runtime
   or driver update move it, and a seed does nothing at temperature 0), so
   each question is asked more than once at freezing, the rig's own noise
   measured, and only a change past it counts. The frozen file names the
   runtime and its version, the template and the context length
   (`num_ctx`), since an Ollama Modelfile changes all three over the same
   weights.

**What this proves, and what it doesn't.** The path keeps the page from
anyone else on the network and from a box that took the rig's address.
The hash and drift catch a swapped or changed model by accident. A rig
that lies is out of reach: it reports a hash it chose and answers a drift
question it recognises, and nothing proves the weights served at home
(confidential computing on a data-centre GPU attests the GPU, not the
weights, and no consumer card has it). That is the person's own machine;
saying so is the design.

A cloud address stays refused: the step to someone else's server is not
taken here. The Provider's own code is a check against the sealed rig
and the last drift result; every judgement in it is a Willow card's.

**Open in it, the owner's:**
- Whether naming a rig is one seal or two (the rig, then each model on
  it).
- What "now and then" is for `model-drift`, and whether a missed check
  stops the rig or only says so.
- Whether `model-exam`'s score has a floor below which a rig isn't
  offered, or only shows.
- Whether the tunnel is set up by the person, as today, or by
  `set_up.py`, which would then be running `ssh`.
- Whether the Grove's D10 (no Tailscale Funnel or cloudflared,
  `one-box/README.md:223`) covers a private tailnet, which isn't public
  ingress; until then the tunnel and a pinned certificate are the paths.
- ~~Willow's `openai-compatible`, `model-exam` and `model-drift` cards say
  temperature 0 with a fixed seed says the same thing twice. Not always:
  theirs to correct.~~ **Context (2026-11-26, from the boxes):** corrected in Willow's
  `bfb6714f` ("temperature 0 and a seed aren't the same answer every
  time"): `model-drift/README.md:62` and `openai-compatible/README.md:36`
  say so, and `model-exam` names the settings without the claim. For the
  rig's noise, Willow's `same-way` (0.1.1) already asks a model each
  question three times and counts how often its answer flips.

### The key in an account of its own (designed 2026-11-21, not built)

**Why.** Every guard here judges words: a path, a glob, a program's name.
Code an assistant writes gets past all of them, and every card says so.
The one guarantee words can't give is the system's own: a key in a file
the account the assistant runs as can't read. Any assistant runs as the
person, so that means an account of the key's own. The owner's machine
already has this shape (the vault in an account of its own); this is that
shape for anyone, on any system, with no name of ours in it.
`set_up.py` now says who can read the key, from the file's owner and mode,
never its bytes.

**The Grove's word on it** (`docs/design/one-box/README.md`, "the four
that change the design", 1): a check of which account calls keeps out
other users and sandboxes, not the model in the person's own shell; acts
only the person does (grant, seal) take a passkey every time, never an
account alone. A password every time is the weaker form that every system
has. And it goes further than the ways below: the click itself is a
**WebAuthn passkey** (`one-box/README.md:243`), its challenge the SHA-256
of what is approved and a nonce, with user verification required, so it
takes a touch or a PIN that no process on the machine can make; the
challenge hashing the content means a Yes covers those bytes and no
others (`:560`, for an outbound grant). That is the target; A to D are
the ways to it, or around it until it is built.

**Much of it without a second account: Claude Code's sandbox** (its docs,
sandboxing, checked 2026-11-21). From managed settings, with
`allowUnsandboxedCommands: false` (which makes `dangerouslyDisableSandbox`
ignored, and a project can't loosen it) and `failIfUnavailable: true`,
`filesystem.denyRead` on the key makes the system refuse the read to every
command the assistant runs, and what it starts, whatever its words: the
thing no guard of words could do. The sandbox covers shell commands only;
file tools, hooks and MCP servers run outside it, so the same paths take
managed deny rules for Read, Edit and Write. Hooks and the runtime running
outside it is what lets sealing still read the key. `set_up.py --write
managed` writes all of it now. It holds for Claude Code, not for another
assistant, nor for code the person runs; and on WSL, where
`/etc/claude-code` is the person's to write, not at all. The account of
the key's own stays the guarantee for everything else.

**The steps, for when sealing can cross** (not to follow yet: today they
would stop the seal page and the desktop prompt from sealing). The person
names the account, `KEYHOLDER`:
- *Linux:* `sudo useradd --system --no-create-home --shell /usr/sbin/nologin KEYHOLDER`
- *macOS:* a role account in Users & Groups, or `sysadminctl`
- *Windows:* a local account, and `icacls` for the file
- then the key's folder and the key to it, 700 and 600.

**Sealing across the line.** The kernel's `seal` and `decline` read the
key, so they run as `KEYHOLDER`. Three ways for the person's click to get
there:
- *A.* The seal page runs as the keyholder (`sudo -u KEYHOLDER python3
  seal_page.py --box BOX`). The page reads the box and the runtime's files,
  so those need a group both accounts share.
- *B.* The page stays the person's, and a click runs `sudo -u KEYHOLDER
  kernel.py seal`. Without a terminal that is `NOPASSWD`, which the
  assistant can use as well as the person: refused.
- *C.* A small seal helper, run as the keyholder, that the page hands a
  click to and that asks for a passkey (or a password, with sudoers'
  `timestamp_timeout=0` so no earlier ticket carries it) every time. The
  Grove's shape.

- *D.* The key in a password manager, behind its own switch: no second
  account at all. Most managers can ask the person on each read: 1Password
  and Bitwarden by Touch ID or Windows Hello, macOS Keychain by confirming
  each access, KeePassXC by confirming a client's request. That is "the
  person, every time" on every system, by a fingerprint where there is one,
  **but only in a per-request mode**: 1Password's SSH agent approves once
  per app and session by default (per request is a setting; "all
  applications" gives the guarantee up), Bitwarden's is unverified, and a
  binary on a macOS Keychain item's trusted list reads it with no prompt.
  And no agent's prompt shows *what* it signs: a process running as the
  person can ask for a signature over a forged seal row at the moment
  they expect a prompt. So the signed bytes hold the seal row's hash and a
  nonce the seal page shows beside it, as the Grove's passkey challenge
  does; the prompt is a second factor, the page the content check. On
  X11 any client can click another's dialog (XTEST), so a prompt there is
  no barrier; Wayland's is, and Yama's `ptrace_scope` at 1 or more keeps a
  process running as the person out of an unlocked agent's memory. Not
  GNOME's keyring: unlocked for the session, it answers any program
  running as the person, no better than a file. Willow has no add-on for a
  manager (2026-11-21: none built; `encrypt`, for the record at rest, is an
  idea), and the box found the question asked nowhere before.

  **The catch is the kernel.** `sealed()` reads the key on every question,
  every `verify` and every `out`, to check each seal row's proof, and the
  proofs are HMACs, which only the secret that made them can check. With
  "ask every time" on, the person would be asked at every question, not at
  each seal. **The way past it is a key pair**, which the Grove already names
  ("Keys are HMAC secrets. The real thing is passkeys or Ed25519",
  `docs/design/one-script/next-pile.md`): the private half signs a seal and
  stays in the manager behind its switch; the public half, in the box,
  checks every proof, so the manager asks exactly once a seal. That is the
  kernel's change and the law's (CONST-0-4, the human key), in all five
  ports and the vectors. Python's standard library has no Ed25519, but
  Willow does: `adapters/stdlib/share/ed25519.py`, sign and check from RFC
  8032 in the standard library alone, held to RFC 8032's vectors and to
  pyca/cryptography's. The kernel starts from it. The owner's.

  **Each port, and its standard library** (checked 2026-11-21 on this
  machine's runtimes):

  | Port | Ed25519 in its own library | What it takes |
  |---|---|---|
  | Python (`kernel.py`) | no: `hashlib` and `hmac`, no signatures | Willow's own `share/ed25519.py`, with the checks below and a faster pass |
  | Go | yes, `crypto/ed25519` (Go 1.13) | nothing; the port's floor is 1.15 |
  | TypeScript (Node) | yes, `crypto.sign`/`verify` with `ed25519` | nothing (Node 14 has it; seen on 22) |
  | Java | yes from JDK 15 (seen on 21) | its floor from JDK 11 to 15, or 17 |
  | Rust | no: `std` has no crypto, the port takes no crates | its own code, from Go's, as the port already is |
  | C# (.NET 8) | no: ECDSA, no Ed25519 | its own code, or a package the port doesn't take |

  ECDSA, which four of them have, isn't in Python or Rust either, and its
  signatures differ each time unless made deterministic, which fights the
  vectors. Ed25519 signs the same bytes everywhere; **checking is not the
  same everywhere** ("Taming the many EdDSAs", 2020): libraries differ on
  a non-canonical encoding, a small-order point and the cofactor. So the
  ports share one rule, written down:
  - refuse S ≥ L, and an A or R whose y is ≥ p;
  - refuse the eight small-order encodings for A and R;
  - check `[S]B = R + [k]A` without the cofactor;
  - check the person's public key once, when it is installed: it decodes
    and is of prime order. With that, the checks with and without the
    cofactor agree.

  Go's, Node's and Java's own checks then need only a small check of the
  bytes in front (Java compares decoded points, so the y ≥ p rule is what
  makes it agree). ZIP-215's looser rule would mean code of our own in
  every port. Willow's `ed25519.py` holds the first and third rules and
  not the small-order ones; the Grove's pinned verifier refuses
  small-order and non-canonical keys (`tests/test_onescript_sign.py`),
  which are the first edge vectors. Then Wycheproof's EdDSA vectors and
  C2SP's CCTV edge cases, beside RFC 8032's, each port's expected answer
  made by the Python rule. Rust's port needs its own SHA-512 as well.

  **Signing and checking are split.** A seal is signed once, at the
  person's click, and that need not be the kernel: 1Password, Bitwarden,
  KeePassXC and Secretive each act as an SSH agent that asks the person on
  every signature, and the agent's protocol is a few length-prefixed
  messages on a Unix socket, which the standard library speaks with no
  program of its own. The private key then never reaches the kernel at all.
  A key file signed in the kernel stays for people with no manager.
  Checking needs only the public half, so the ports' own code holds no
  secret, and the timing care hand-written signing needs doesn't arise.

  **Measured** (2026-11-21, a scratch Ed25519 from RFC 8032's reference,
  standard library only, holding its vectors 1 and 2 and refusing a changed
  message or another signature):

  | One seal | Python 3.9 | 3.13 | 3.14 |
  |---|---|---|---|
  | today's HMAC check | 0.003 ms | 0.002 ms | 0.002 ms |
  | Ed25519 check, RFC 8032's reference | 4.2 ms | 3.6 ms | 3.9 ms |
  | Ed25519 check, one pass over both scalars (Straus) | 2.8 ms | 2.3 ms | not run |
  | Ed25519 signing, once a seal | 4.0 ms | 3.4 ms | 3.7 ms |

  Every command reads the whole record, and `sealed()` checks every seal
  row: `bite` once, `propose`, `seal` and `decline` twice, `out` and
  `verify` once each, every decline row too. At 2.5 ms a row, 500 seals is
  over a second a question.

  **Two changes make it a non-issue for questions:**
  - *Check only the seals a question can use.* `bite` serves a sealed
    answer only for its own question (`asked == k`), so it can check those
    rows alone: one check or none a question, at any size of record. Worth
    doing with the HMACs now, too. `verify`, `out`, `propose` and a seal
    still read every row once: about 1 to 2.5 s for 500.
  - *Remember a checked row within one process.* A row's proof never
    changes, the record only growing, so a memo by the row's hash, in
    memory, halves `propose` and `seal`, and in a process that stays up,
    as `pile-serve` does, checks each seal once in its life. Never on disk:
    the kernel keeps no index on purpose (LIMITS.md) and trusts no file in
    the box, and a file saying "these were checked" would be one that code
    could write a forged seal into.

  **What else it costs:** the seals there are, HMACs that only the old
  secret checks, need a way across (one row proven under both keys that
  vouches for every seal before it, then the old secret retired; `share`
  already keeps a chain of rotations, each signed by both its keys, which
  is that shape); and
  passkeys are another algorithm again: Apple's, Google's and Windows
  Hello's sign with ECDSA P-256, so passkeys later mean P-256 checking in
  every port as well.

  Until then, with no code: a password manager can keep a copy of the key,
  as `backup`'s card says the key belongs somewhere other than the backup.

Claude's lean (2026-11-21, after the research): the Grove's passkey as the
target, its challenge holding the seal row's hash; the managed sandbox
now, for Claude Code; *D* where the kernel takes a key pair, in a
per-request mode, with the row's hash in what is signed; *C* with a
password where a passkey isn't there yet; *A* as the way to try it first.

**The record, shared and append-only.** The kernel writes the record as
the person while asking and as the keyholder while sealing, so the box's
folder takes a group both are in (setgid, so new files keep it). And
`chattr +a` (Linux) or `chflags uappend` (macOS) on `record.jsonl` lets
rows be added and none rewritten, by either; the chain and Willow's
`tip-pin` already show a rewrite, this stops one. Restore and Willow's
`removed` add rows, so they keep working; nothing here truncates it.

**The code, the same way: installed where only an administrator writes.**
Managed settings keep an assistant from unwiring the guard door, but not
from changing it: the hook runs `doors/guard.py` from the Provider's
folder, and that folder is the person's. `sed -i` on `runtime.py` or a door
is a command whose words name no file the guard holds (the key, the
record, `BOX.runtime`), so it is let by, and an Edit is held only until a
Read. Willow's files need nothing more: the pin refuses a Willow whose
files differ, so a changed Willow stops the runtime rather than getting
past it. But the pin is in the Provider's folder too. `set_up.py` now
says who can change this code ("who can change this code"), from each
file's and folder's owner and mode, never their bytes.

Two more, found 2026-11-21. **A hook that fails lets the call through**:
Claude Code treats a crash, a timeout or bad output as a non-blocking
error, so one bad edit to `doors/guard.py` switched the guard off with no
word. `set_up.py` now writes the guard door with `onFailure: "block"`
(Claude Code 2.1.295 and later), so a guard that can't answer is a No,
and says whether it is there. (The Grove's 2026-10-06 research says Claude
Code has no such switch; it has one now.) And **for Claude Code, managed
`denyWrite` and Edit/Write deny rules on this folder** stop the edit
before an install is built; `--write managed` writes them, so the folder
hooks run from is no longer one to work on the Provider in.

The steps, when built (the person names where):
- *Linux:* `sudo install -d -o root -g root -m 755 /opt/model-context-provider`,
  then a copy of the Provider in it, owned by root, 644 and 755; the same
  for the Willow it is pinned to, beside it.
- *macOS:* the same under `/Library/Application Support/`, owned by root.
- *Windows:* under `C:\Program Files\`, which only an administrator writes.
- then `set_up.py --write` run from that copy, so the hooks, the MCP
  configuration and the managed settings all name it, never the person's
  own checkout.

**Unlike the key, nothing crosses at run time.** The doors are read and run
as the person, and the runtime writes only beside the box (`BOX.runtime`)
and in the person's client settings, never in its own folder; Python skips
its `__pycache__` where it can't write. Only changing the code takes the
administrator: updating it, and `willow_pin.py repin`, which is on purpose.
So it doesn't wait on sealing across, and `set_up.py` could print the lines
now, as `--write managed` does. The tests and `check.py` stay in the
person's own checkout, which is where changes are made.

**Context (2026-11-26, from the boxes):** willow-mcp has built this shape for its own
trust root: `deploy/provision-uids.sh` makes login-disabled system accounts
(the trust owner, which owns its key, and the runtime), and its runbook
(`docs/deploy/dedicated-uid-deployment.md`) has the one step way *B* needs:
the person's own command builds and checks everything first, then asks sudo
to run only a narrow helper as the owning account, which never gets the
person's home, agent socket or private key, and `doctor` checks the
separation from the person's side ("uid separation: OK"). It needs Python
3.11 and `cryptography`, so the pattern comes over, not the code.

**Open in it, the owner's:**
- Whether `set_up.py` prints the code's install lines now, ahead of the
  key's, and where by default.
- A, C, D, or more than one; and a password until passkeys, or passkeys first.
- For D: a key pair in the kernel, and how, with the standard library
  holding no Ed25519 (a port of it in the kernel's own code, or a signature
  the standard library has, or the kernel calling out to one).
- Whether the box's folder is the person's with a shared group, or the
  keyholder's with the person reading it.
- Whether `chattr +a` is a step setup prints, or only said.
- Windows, where neither `sudo` nor `chattr` is.

### The owner's to decide (changes to Willow)

- An early exit in the kernel's date reader: `on-this-day`, `coming-up`
  and `people` still take 16 to 22 seconds on the real folder there.
  **Note (2026-11-26):** done on Willow's branch `ccr-8607467b-iah1ml`
  (`77a99403`, vectors `e3c98033`), waiting on the owner's merge: `newest`
  jumps to the next digit or web address, 34.6 s to 3.8 s over cpython's
  710,290 passages with every date the same, and `stem` keeps what it
  worked out. Not yet measured on the real folder.
- Quoted speech in the `todo` report.
- The privacy filter reading a run of four-digit numbers as a card.
- What Kartikeya's scan of a job missed (written up above).
- ~~**#91's fix, to main.**~~ Done 2026-11-21: willow-memory/Willow#387
  merged `hook-guard` 0.2.0, whose `seal` rule refuses a command that runs
  the kernel's `seal` or `decline` (any kernel, any port, any box). The pin
  is on `0c07be1`, and `tests/test_guard.py` holds it through the guard
  door. A script the model writes to get round it still gets through: keep
  the key where the account the assistant runs as can't read it.
- **#90, a search of the key's folder.** Fixed on Willow's
  `ccr-9265087c-pvfpcl` (`6310940`, `hook-guard` 0.2.1), not on main yet:
  a Grep over the key's folder or one above it, and a recursive Glob there
  that could name the key, are refused; a search whose own filter leaves
  the key out is let by. Its shell twin is fixed beside it (`ce79466`): a
  glob the shell expands to the key (`cat` of a star in its folder) and a
  recursive read of its folder or one above it (`grep -r`, `rg`, `cp -r`,
  `rsync -a`, `zip -r`, `tar` making an archive). The Provider's guard,
  hook and session tests pass on both. The pin moves when they land.
- ~~**The same Willow branch's other two.**~~ Done in #387 with it:
  `gh-json` 0.2.0, and the contract test that holds every add-on to
  "refuse or read" on a box of sources (#383, 37 strict xfails to fix).
- **`starter.py copy` names `init --words`.** Fixed on Willow's
  `ccr-9265087c-pvfpcl` (`9ee4693`, `starter-words` 0.1.1), not on main
  yet: the copy names `kernel.py words` for a record already made, beside
  `init --words` for a new one.
- **Willow's branch `ccr-8607467b-iah1ml`, to main** (2026-11-25):
  `index-cache --from @LIST` and `--box`, a check that reads again only
  the files whose details on disk moved, and claude-code's hook answering
  a box laid from several places from its index. The pin is on its
  `28009362` until it merges, then moves to main.
- **The kernel's `listed()` is quadratic**: it looks back along the list
  for each line, which on a list of 5,000 files was most of a check's time.
  Fixed by a set on the same branch (`77a99403`), with the date reader
  above.
- **More of #383**, met by the boxes' stacks: the forge's `suggest` crashes
  with a traceback on a box laid with `--from`, as do `instruction-files`,
  `risky-code`, `secrets-audit`, `ref-check`, `box-health` and `digest`
  (they take `--from FOLDER` instead); `browse` checks an index against
  one folder only, as the hook did; `unpinned` says a repository with a
  `pyproject.toml` has neither `package.json` nor `requirements.txt`; and
  the forge misses `git-history` for "commit history" (a line for
  `ui/search-words.txt`).
- **A "nothing hosted" check.** Run the base assistant
  ([base-jarvis.md](base-jarvis.md)) with the network off and only a model
  on this machine, and write down what works and what breaks: the kernel,
  the seal page, the person's door and `local-model` should all hold; the
  MCP door needs a client, and the voice loop is half ideas. The answer to
  "what if hosted models get dear or go", as a test rather than a claim.

### The owner's own

Name socratic-fork as a folder; an `ask-here` file to turn the dialog on;
a `deny.txt` for `hook-shell`; a copy of `share.id` kept somewhere safe.
Willow's commits are pushed: willow-memory/Willow#380 (the game-box flake,
`removed`'s mutants, `strip` showing why, `privacy`'s codes, `hook-guard`'s
find, git, tar and unzip, `hook-feedback`'s words list, `session-seal
--with`, the UI's words example) merged on 2026-11-20 as 6714ea5, and the
pin is on that commit of main. Its one red was `strip (3.14)` timing out
on shard 3, whose `test_cores.py` the timings file prices at 35 s against
139 s; `times.py write --run latest` refreshes it, and needs gh. A kernel
command to give a record its words list after it is made is the owner's,
under way. It landed on 2026-11-21 as willow-memory/Willow#386
(`abf3b0b`): `words --box DIR --words FILE` in `kernel.py` and all five
ports, held by `vectors/compare.py`'s session, `box-health` and
`record-history` reading its row, and `known-gaps`' freeze 17. The pin is
on that commit, and `set_up.py`'s "your words: none" prints the two lines
that give a record the starter list.
