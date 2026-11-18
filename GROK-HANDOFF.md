# The Grok handoff, to cross off

The handoff Grok wrote on 2026-11-17, copied out so each line can be ticked
and noted. Grok's words are kept as they were. A box is ticked when the
thing is built here. A line starting **Note** was added afterwards: what
was found when the line was held to the code, and what it still needs.

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

**Note:** true as written. Since then: `doors/guard.py`, `check.py`, and
seven of Willow's hook add-ons in the pin (see "Added since" below).

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
- [ ] **people**
  - **Note:** read-only report: everyone the files name, and where. The
    report path is built now, so this is a line in `runtime.REPORTS` and a
    pin. Held back on purpose: it names everyone in the files, so what
    leaves deserves a closer look first (the names list withholds only the
    names the person listed).
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
- [ ] **timeline**
  - **Note:** writes a dated, cited timeline of one matter to a file, to
    hand to someone. That is a way out: it needs the leave rules.
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
- [ ] **pile-store / pile-serve** (performance)
  - **Note:** not looked at yet.
- [ ] **share** (needs careful "leave" design)
  - **Note:** a second way out: sealed answers sent to another person,
    written to the record. Needs the person's ruling before any code.
- [ ] **rss-out** (needs careful "leave" design)
  - **Note:** not looked at yet. Also a way out.
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
- [ ] Optional sealed/version-pinned skills/behaviours
  - **Note:** not started.

### Suggested near-term order (from last discussion)

1. [x] todo + capture + notes (or thin sealed-collection wrapper)
   - **Note:** capture done; todo as above; kept notes read back as `notes`.
2. [ ] people + calendar + on-this-day (everyday utility + delight)
3. [x] Minimal seal-gated task queue
4. [ ] MCP Resources for sealed pages + a couple of prompts
5. [ ] share and/or handover as distinctive Willow flavour

### Fun / differentiating angles

- [ ] on-this-day + timeline + milestones (personal history, extractive +
  sealed)
- [ ] share with cryptographic checkability
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
  - **Note:** held. The pin is at Willow `14efe16d`, which so far exists
    only on this machine.

### Open design questions

- [ ] Exact new verbs and how they map into `runtime.call` while preserving
  the two lines
  - **Note:** settled for hooks: a third face, "host", with `context` and
    `event`. Open for reports.
- [ ] How much friction is acceptable on the seal path for higher-volume
  surfaces (todo, calendar, etc.)
  - **Note:** six things wait on the seal after one day's work. Corrections
    (`hook-feedback`) and captures each add one.
- [ ] Whether to expose any of the new surfaces as MCP Resources vs tools
  only
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
    as `NAME.2`; a name climbing out of the shelf refused. There is no
    verb to take a thing off a shelf: that is done by hand.

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

- [ ] **Skills** (Willow pull request 375, merged 2026-11-18: five ideas,
  `skill-picks`, `server-picks`, `which-one`, `still-kept`, `my-installs`;
  none built). They find and judge other people's skills, tools and MCP
  servers. This project's part is the last step: a `skill` verb that seals
  a skill file by its exact words and gives a model only those bytes, so a
  skill that changed after it was vetted waits on a new seal.
  - **Needs:** the owner's yes on that shape. No change to Willow.
- [ ] **`my-installs`** (from the same pull request): what is installed on
  this machine (skills, plugins, hooks), what each can touch, and what
  changed since last looked. The audit half of the guard gap below.
  - **Needs:** building in Willow first; it is only an idea there.
- [ ] **Socratic** (the owner: "making the news recently"). On Willow's
  list as an idea: "asks you questions about your own notes instead of
  answering, each citing the passage it asked from". The owner's own
  `socratic-fork` is a skill of 697 questions.
  - **Needs:** small: a fourth prompt that has a model question the person
    over a page they sealed, citing each passage, and answer nothing.
    Larger: `socratic-fork` as the first skill served by the `skill` verb.
- [ ] **Depend on GitHub less.** The check and the hook that holds `main`
  are built and run here. Still on GitHub alone: the four Willow commits
  this pin stands on (`hook-errors`, two for `todo`, `hook-handoff`), which
  are on this machine only; the owner said to save that pull request for
  later.
- [ ] **Quoted speech in the todo report.** About a dozen of the 91 lines
  are the owner quoted saying "I need to…" in a past session, not tasks.
  - **Needs:** the owner's yes; it is a change to Willow's `todo`, and it
    would also drop a real task that happens to be quoted.
- [x] **The `people` report.** A line a person (how often, in how many
  files, over what dates), from one call to Willow: `people` 0.1.2 has a
  `--json`. Proposed on the task queue, sealed by the owner, and done from
  it: the first task the queue carried. Not yet seen over the real record.
- [ ] **More reports, cheaply.** `report()` takes any exit but 0 as a
  failure, and Willow's audit add-ons exit 42 when they find something.
  Fixing that opens `ref-check`, `pii-audit` and `secrets-audit`;
  `minutes` fits as it is. Ranked list in the agents' assessment.
- [ ] **More importers.** `joplin` takes the same command line as `notes`
  and `calendar`: a line in `BRING_IN` and a pin.
- [ ] **The task queue's edges.** Listing tasks has no limit on its whole
  size; each `tasks` or `notes` call asks the kernel once a sealed thing,
  a row on the record each time.
- [ ] **`share`**, and with it `timeline` and `rss-out`: ways out to
  another person or place. The owner will take `share` with the main
  session once the agents' work is merged; each needs a ruling.

## Still loose

- [ ] Push the Willow commits, or the GitHub workflow can't find the pinned
  commit.
- [ ] `hook-shell` is off until there is a `deny.txt` beside the record.
- [ ] A correction ("No, …") hasn't been tried in a real session.
- [ ] The guard covers the box, not `BOX.runtime` (`stopped.json`,
  `scopes.json`, `names.txt`, `deny.txt`). An agent confirmed it: a write or
  an `rm` there is allowed. The fix is a second folder for Willow's
  `hook-guard` (`--also DIR`), one line in `guards()`, and a repin. Three
  more gaps in the same script: `mv` checks only where it puts a thing, a
  `cd` earlier in a command isn't followed, and `$VAR` paths aren't filled
  in.
- [ ] `uv.lock` is untracked: commit it or ignore it.
- [ ] Nothing built on 2026-11-18 by the agents has been seen in a real
  client yet: the task queue, reading notes back, bringing a vault in, the
  checks on a sentence, and "What a model can never do".
