# Every file

Every file in the repo, and what it is. `tests/test_files.py` fails if this
tree and the folder ever disagree: a file added, moved or removed must be
added, moved or removed here too, with a few words saying what it is.
Caches, the dev lock file and anything hidden (but `.github` and
`.gitignore`) are left out. [README.md](README.md) is the front page.

```
model-context-provider/
├── README.md                               the front page: the two lines, how a question goes, set-up, and where to read more
├── FILES.md                                this file
├── CHANGELOG.md                            what changed, newest first
├── CONTRIBUTING.md                         the rules a change is held to
├── AGENTS.md                               for AI agents: the four rules that matter most
├── CLAUDE.md                               one line: read AGENTS.md
├── SECURITY.md                             what counts as a hole, and how to report one
├── LICENSE                                 Apache-2.0
├── runtime.py                              the one local runtime: every door calls it, and nothing else decides
├── seal_page.py                            the seal page: the person's click carries out the kernel's seal, on this machine only
├── seal_prompt.py                          one question in a desktop dialog: the person's yes to a session
├── set_up.py                               checks Willow, the record and the words, and prints what to paste into a client
├── hosts.py                                the assistants that take an MCP server, and where each keeps its settings
├── check.py                                the check a change is held to: the pin, lint, format and the tests
├── willow_pin.py                           holds Willow to its pin, and is the only way to move it
├── willow.pin.json                         the Willow commit this runs on, and every file of it by SHA-256
├── pyproject.toml                          the project's name and its dev tools; nothing to install to run it
├── ruff.toml                               lint and format settings
├── .gitignore                              caches, built packages, and never a key, an identity or a machine's settings
├── doors/                                  the ways in: each turns its own wire into a call to the runtime
│   ├── __init__.py                         what a door is, and that it decides nothing
│   ├── mcp.py                              the MCP door: stdio, one JSON-RPC message a line
│   ├── pipe.py                             the person's own door: one JSON request a line in, one answer out
│   ├── hook.py                             the prompt hook: adds a sealed page to a prompt, as data
│   ├── session.py                          session start and end: tells the person what waits, closes a session
│   └── guard.py                            the guard: Willow's hooks around what an assistant does
├── boxes/                                  the maintainer's Willow boxes over the repositories built beside this, and their stacks
│   ├── README.md                           what each box is laid from, what each stack asks, and what waits on the person
│   ├── lay.py                              lays every box and runs its stacks in one command; never seals, never opens a key
│   ├── repos.json                          the repositories, the kinds of file kept and the folders left out
│   ├── code-words.txt                      a words list that reads a question's words as the code's
│   └── stacks/                             the stacks, each step with what it is for and what it misreads
│       ├── orient.md                       before a first change: instruction files, what they name that is gone, what nothing pins
│       ├── owes.md                         TODOs, risky lines, secrets in plain files, stale references
│       ├── across.md                       one box over all: where one repository leans on another
│       └── ask/                            each repository's standing questions, each source answering in turn
│           ├── codebase-memory-mcp.md              questions about codebase-memory-mcp
│           ├── cpython-fork.md                     questions about cpython-fork
│           ├── Model-Context-Provider.md           questions about Model-Context-Provider
│           ├── pyperformance-fork.md               questions about pyperformance-fork
│           ├── Willow.md                           questions about Willow
│           └── willow-mcp.md                       questions about willow-mcp
├── docs/                                   the README's longer sections, and the working notes
│   ├── doors.md                            what each side can do, the doors, the guard, and what a model's door lists and offers
│   ├── session.md                          one yes for a session, and one seal that closes it
│   ├── seal-page.md                        the seal page
│   ├── reports.md                          reports of your files, a timeline and a feed
│   ├── skills.md                           instructions you name for a model to follow
│   ├── sharing.md                          sending a sealed sentence, or a job, to another person
│   ├── keeping.md                          notes, tasks, shelves, what is kept, and bringing things in
│   ├── background.md                       what it stands on, what stays on the machine, what has been seen working
│   ├── base-jarvis.md                      everyone's base assistant: the layers, what fills each, what is left to build
│   ├── OPEN.md                             what was asked, what was built, and what is left
│   └── NOTES.md                            design notes that fit nowhere else
├── tests/                                  one file a subject; each docstring says what it holds the code to
│   ├── conftest.py                         a box over a small pile with a test key, and what every test shares
│   ├── test_answer.py                      a model returns one sentence, and the person seals it
│   ├── test_backup.py                      the box and what is kept beside it, copied and checked
│   ├── test_boxes.py                               the boxes' stacks, words and lay.py, which never seals
│   ├── test_bring_in.py                    notes, a calendar, an export, email or texts brought into the folder
│   ├── test_capture.py                     one thing handed in to keep, for the person's seal
│   ├── test_check.py                       check.py, and the hook that holds main to it
│   ├── test_checks_kept.py                 the checks run on a model's sentence are kept and shown
│   ├── test_doors.py                       a door imports the runtime and nothing that decides
│   ├── test_draft.py                       a sentence drafted by the client's model, over the sealed page only
│   ├── test_files.py                       FILES.md names every file here, and no file that isn't
│   ├── test_grant.py                       one yes for one session in one folder
│   ├── test_guard.py                       the guard door, decided by the runtime
│   ├── test_hook.py                        the prompt hook gives a sealed page, or only whether the files hold it
│   ├── test_hosts.py                       the hosts table, pointed at the MCP door
│   ├── test_index.py                       a question answered from an index of the folder, kept current
│   ├── test_leave.py                       a page leaves only once sealed, whole
│   ├── test_listed.py                      the resources and prompts a model's door lists
│   ├── test_local_model.py                 a model on this machine, held to the same check
│   ├── test_made.py                        a timeline of one matter, and a feed of what was sealed
│   ├── test_pin.py                         the sent log's end, pinned where the runtime can't reach
│   ├── test_plain.py                       every refusal in plain words, with one next step
│   ├── test_preview.py                     the page a scope would let leave, shown before the seal
│   ├── test_promises.py                    what a model can never do, each with the test that holds it
│   ├── test_read.py                        a read says whether the files hold a question, and no more
│   ├── test_report.py                      a report of the person's files at a model's door
│   ├── test_rows.py                        a row is written only when something happened
│   ├── test_scopes.py                      every question asked to be shared, and a stop
│   ├── test_seal_page.py                   the seal page, and that only the person's browser can click it
│   ├── test_seal_prompt.py                 the desktop dialog for a session's yes
│   ├── test_sent.py                        what left, written down as it leaves
│   ├── test_session.py                     one seal a session, and telling the person what waits
│   ├── test_setup.py                       set-up checks, prints, and with --write finishes a client
│   ├── test_share.py                       sharing with another person, and a job that travels
│   ├── test_shared.py                      the sent log as a person reads it
│   ├── test_shelf.py                       the shelf: what a session makes for its project
│   ├── test_skill.py                       a skill, given only while it reads as it did when named
│   ├── test_stale.py                       a sealed scope leaves whole or not at all
│   ├── test_status.py                      how things stand, in one look
│   ├── test_stored.py                      what is kept beside the record, removed or archived, its hole kept
│   ├── test_tasks.py                       the task queue, and the notes read back
│   ├── test_tools.py                       the tools a model is offered, in groups the person switches
│   ├── test_waiting.py                     what waits on the person, said so they know what it is
│   ├── test_willow_pin.py                  Willow held to its pin, by every file of what runs
│   ├── test_withhold.py                    names, numbers and addresses kept out of a page
│   └── test_words.py                       a box made with the person's own words
└── .github/                                GitHub's copies of the check: a second opinion, never the gate
    ├── dependabot.yml                      keeps the workflow's actions current
    ├── pull_request_template.md            what a pull request should say
    └── workflows/                          the one workflow
        └── tests.yml                       runs check.py's commands on GitHub
```
