# Open: what was asked, what was built, what is left

This began as the handoff Grok wrote on 2026-11-17, copied out so each line
could be ticked and noted, and Grok's words are kept as they were. It has
since grown into the project's working list: what the owner threw in
along the way, what was found when each line was held to the code, and
the owner's rulings. A box is ticked when the thing is built here. A line
starting **Note** was added afterwards: what was found, and what it still
needs. Last held to the code on 2026-11-18. What is still open is
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
  backup, chained sent log + pin/check.
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
    from beside it, so both are pinned. It reads the box's main folder
    only, not extra sources. Not yet tried in a real session.
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
    without them `job` is refused and everything else runs. The pin is at
    Willow `e2d539ce`, which so far exists only on this machine.

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
  code from Claude Code's `error`. Committed on this machine; not pushed.
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
    (0.1.3 to 0.1.7). Here: `job`, and `job_later` with `job_result` for a
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
    add-ons, `todo`, `people`, `hook-guard`, `kart`, `timeline`, `removed`) are on this machine
    only; the owner said to save that pull request for later.
- [ ] **Quoted speech in the todo report.** About a dozen of the 91 lines
  are the owner quoted saying "I need to…" in a past session, not tasks.
  - **Needs:** the owner's yes; it is a change to Willow's `todo`, and it
    would also drop a real task that happens to be quoted.
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
  assistant's own shell tool does not.
- [ ] Push the Willow commits, or the GitHub workflow can't find the pinned
  commit.
- [ ] `hook-shell` is off until there is a `deny.txt` beside the record.
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

Nothing, as of 2026-11-18. Still under "Not yet seen in a real client"
above, for whenever the owner is at the keys: the desktop dialog, a
folder skill, `share_forward` and a correction, a job that travels,
`stored`/`remove`/`archive`, and the `mail` and `sms` importers.

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
  - `timeline` with `since` says `empty` when no line falls in those days,
    yet writes the whole timeline to a file (150 KB here) and names it.
    Each asking leaves a file in `made/`.
  - `report` names are held to their exact case (`Todo` is refused).
  - `minutes` is over the most shared at once on the real folder, and a
    report has no parts as a timeline has, so a session let in gets none
    of it.
  - A timeline counts front-matter lines (`metadata:`, `node_type:`) as
    lines about the matter. Willow's `timeline`, by passage.
  - After a reconnect the client still showed the older descriptions of
    `report`, `context` and `skill`. Seen once; whether the door should
    send the list-changed notice when its own words change is not looked
    into.

- A strict answer must cite every passage on its page, which can force a
  clause that has nothing to do with the question (seen 2026-11-18). To
  let a model answer from some of the passages loosens a check: the
  owner's to rule on. The description now says what the check holds.

- Fewer rows on the record still: a read-only way to ask the kernel what
  is sealed and what waits (a Willow add-on), and a switch for which hooks
  are on, as the tool groups have. Measure what is left first.
- More importers that fit by their card, none run by hand yet: `mastodon`,
  `goodreads`, `karakeep`, `opml`, `takeout`, `bookmarks`, `zotero`.
- Not looked at: `milestones`, `projects`, `handover`. `pile-store` was
  measured and left out (no gain on the real folder).
- Willow's `rss-out` can write inside the record's folder; the runtime
  refuses that, the add-on itself does not.

### The owner's to decide (changes to Willow)

- An early exit in the kernel's date reader: `on-this-day`, `coming-up`
  and `people` still take 16 to 22 seconds on the real folder there.
- Quoted speech in the `todo` report.
- The privacy filter reading a run of four-digit numbers as a card.
- What Kartikeya's scan of a job missed (written up above).

### The owner's own

Name socratic-fork as a folder; an `ask-here` file to turn the dialog on;
a `deny.txt` for `hook-shell`; a copy of `share.id` kept somewhere safe;
the Willow commits pushed when the time comes.
