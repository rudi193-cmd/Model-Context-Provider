# Changelog

## Unreleased

The first cut, built one piece at a time on 2026-11-17, each with its tests.

- **Your seal pins the sent log's end.** A chained log can't vouch for its
  last line, so a cut there showed only against a pin kept by hand. Each
  session's close now hands Willow's session-seal the log (`--log`), and
  the one proposal you seal holds its lines and its last line's hash; the
  claim says "and your log's N lines". `check` with no pin holds the log to
  the last session you sealed (holds, cut short, rewritten, or not sealed
  yet), and `status` says it under Shared. A log that doesn't hold is left
  out of the seal, and close says so. The kernel reads your key; this never
  does. Pinned to Willow `9446bf9`, on its branch until it merges.
- **Setup says who can read your key.** From the file's owner and mode,
  never its bytes: the account setup runs as is the one any assistant runs
  as, so a key it can read is one a script the assistant writes can read.
  The key in an account of its own, with sealing across it, is designed in
  `docs/OPEN.md`, not built, with a fourth way: the key in a password
  manager behind its ask-every-time switch, which waits on a key pair in
  the kernel. Each port's library, and the cost measured: Ed25519 checks
  at 2.3 to 4.2 ms a seal in pure Python, a non-issue for questions once
  `bite` checks only its own question's seals.
- **The guard door where an assistant can't switch it off.** In
  `~/.claude/settings.json` an assistant allowed to edit `~/.claude` could
  unwire it. `set_up.py --write managed` writes the same hooks for Claude
  Code's managed settings (a drop-in, `managed-settings.d/`) and prints the
  `sudo` line that installs them; `set_up.py` says which of the two the
  guard door is in. The Grove's one-box design, threat 3.
- **A record made from several places is told, not shown a traceback.**
  Backup, `coming-up`, `pii-audit`, `secrets-audit`, `ref-check` and
  `timeline` refuse in plain words (`reads_one_folder`) on a record made
  with `init --from`, whose Willow add-ons read one folder (Willow #383).
- **The guard door refuses the person's own door.** A model's tool call
  that runs the pipe, the `provider` command, the seal page or the seal
  prompt is blocked by the runtime, before Willow's guards, naming the door;
  the pipe had handed back passages with no seal, and takes `stop`,
  `restore` and `share_send`. Reading their files is let by.
- **The guard door refuses a seal.** A model's shell could run the
  kernel's `seal` or `decline`, which read the key themselves (Willow bug
  #91); the pin moves to Willow's `0c07be1` (#387), whose `hook-guard`
  refuses it, and `tests/test_guard.py` holds that through the guard door.
- **A record with no words list is told how to give it one.** Willow's
  `kernel.py words` (willow-memory/Willow#386) lets a record take its list
  after it was made; `set_up.py`'s "your words: none" prints the two lines
  that do it, with the record's own paths (`starter.py copy`, then
  `kernel.py words`), and the stack notice and README no longer say a
  record takes its list only when it is made. The pin is on `abf3b0b`.
- **A model on the person's own rig, designed.** `docs/OPEN.md`: a rig
  on the home network is refused today like a cloud server. The way that
  works now (an SSH tunnel, so the Provider asks loopback), and the way to
  build: the rig named once and sealed, by Willow's cards (`weights-card`
  and `weights-pin` on the rig, `model-exam` on the person's sealed
  answers, `model-card` on the record, `model-drift` now and then), over a
  tunnel or pinned TLS. Not built.
- **The base Jarvis page, corrected and widened.** The base is the
  Grove, as the owner decided on 2026-09-01 (quoted from the Grove's
  phone-surface notes); with the rules it inherits (no inside names reach
  the person, a conversation, an age gate, small models each on a slice)
  and the gaps none of the four piles answers: a lost key, other people's
  words, a household, the phone's plaintext.
- **A base Jarvis, written down.** `docs/base-jarvis.md`: everyone's base
  assistant as the Grove's five layers (voice, desk, tools, memory,
  trust), what already fills each across Willow, this Provider, Die-Namic
  and the Grove, the rule it inherits (record choices, never people), what
  is left to build, and what Willow's forge gave when asked (hand built).
- **The seal page fits a phone.** A model's sentence quotes its page's
  seal, a 70-character id with no break, and at a phone's width the page
  ran 137 pixels too wide and scrolled sideways. A card's text now breaks a
  word that can't fit. Seen by rendering the page's own HTML, with its own
  headers, in headless Chromium: never served, nothing clicked; the policy
  let no script run and nothing load but its stylesheet.
- **A session's corrections go in the backup.** They wait beside the
  record until the session ends, in `corrections/`, which `backup` and
  `restore` didn't carry; now they do, held to the same names.
- **Under a session's yes, a question you sealed a page for gives that
  page.** The kernel answers a sealed question with its seal and serves no
  passage, and under a yes `context` passed that on as a bare
  `{"state": "sealed"}`: nothing a model could use, and no word that the
  page was stopped when it was. It now gives the page, as `leave` does, and
  a page you stopped is refused as `stopped`.
- **The pin is on Willow's main.** willow-memory/Willow#380 merged as
  6714ea5; the pin names that commit, and no pinned file differs from the
  branch commit it named before.
- **A record is pointed at a words list before it is made.** A record
  takes its words list only when it is made, and Willow's UI ticks the
  starter list only when the stack holds `starter-words`; nothing here
  said so, and `set_up.py` called "your words: none" ok. Now `set_up.py
  --stack` on a stack with no record yet and no `starter-words` gives the
  one command that adds it, a record with no words is a notice (`--`) that
  says what it costs and stops nothing, a record with words is told it
  can add its own lines any time, and the README's setup says to keep the
  starter list ticked.
- **Corrections are sealed with their session, once.** Each correction the
  person typed was a card of its own on the seal page, past any cap, and
  "No thanks, that's fine" or "no worries" counted as one while "nope,
  not that" didn't. On the owner's word: a correction is known by Willow's
  `hook-feedback` words list (`match`, which writes nothing; a list of
  your own in `BOX.runtime/corrections.txt`), kept beside the record for
  its session, 50 at most and once each, and handed to `session-seal
  --with` at the session's end, so it is in the session's one proposal.
  The session's card lists them. The pin moves to Willow's
  `hook-feedback` 0.1.1 and `session-seal` 0.3.1 (#380).
- **The guard reads a command run on the record by another.** Probed with
  34 direct calls, the guard door refused 33; `find BOX -delete` went
  through, and so did `find -exec rm`, `git -C BOX clean`, `tar -C BOX` and
  `unzip -d BOX`. The pin moves to Willow's `hook-guard` 0.1.2
  (willow-memory/Willow#380), which reads each; `find`, `git status`,
  `tar -t` and `unzip -l` still pass.
- **A page can't close its own frame.** The prompt hook frames a sealed
  page in `<sealed-page>` tags. A page holding those tags itself (a note,
  or another person's email brought in with `mail`) closed the frame
  early, so what followed looked to stand outside it. The frame's name
  inside a page now has its hyphen made a non-breaking one: it reads the
  same, and the frame closes once, at its end.
- **A client that reconnects is told the list changed.** After a
  reconnect a client could still show older tool descriptions: the door
  sent `list_changed` only when a tool's name changed, and only within one
  run. It now keeps, beside the record, the fingerprint of the whole list
  it last sent (names, words, schemas, hints); a new session whose list
  differs is told at once, and a change within a session to any of those
  is told as a name's was.
- **A sentence cites the passages it comes from, and what it left out is
  shown.** On the owner's ruling (2026-11-19), a strict answer cites at
  least one passage on its page and need not cite them all: citing every
  one forced clauses that had nothing to do with the question. The
  passages it cites are sentence-check's boxes, every check held over
  them; the rest are its earlier boxes, whose words count only when cited,
  so a word from a passage it leaves out still strikes it. A sentence that
  cites nothing on its page is refused (`no_cite`). Kept with its checks,
  by id and file and never words, is what it left out, and the seal page
  shows it beside the sentence ("Left out: 1 of the 2 on the page").
- **A refusal names what you type.** Its next step named a verb on your
  door in brackets, as `(waiting)` or `(stored)`, which a model passed on
  as "Tell the person: look at what waits on you (waiting)". Each now names
  the command, `provider waiting`, and the seal page where it does the
  same. Three that spoke of you as "the person" on your own door (a tool
  turned off, no identity to share with, nobody by that name) now speak to
  you, with the words to type: `provider tools on=GROUP`, `provider
  share_id`, `provider share_person name=NAME key=KEY`.
- **A model's client is told more before it calls anything.** The door's
  `initialize` said nothing of how its tools go together, and named itself
  version `0`. Now it gives `instructions` (the two ways in, that sealing
  is the person's, and that with the Provider's hooks what they seal
  comes into a later turn by itself, while without them a model calls
  again; how to read `read (question)`), and its version with
  the Willow commit it is pinned to. Each tool carries MCP's annotations
  (none reaches past this machine; only the shelf takes anything away;
  `context` and `report` only read), and its schema holds the runtime's
  own limits: a note's length, a shelf or skill name's pattern, the report
  names, a date's form. The nine everyday tools are 6,172 characters, under
  the 7,000 they are held to.
- **What a model hands in has an end.** A model never let in could write
  without limit beside the person's record: a note of any size, any number
  of them (each kept in the record's proposals, each waiting on the seal
  page), and a shelf of any number of things a megabyte each. 40 MB went in
  seconds. Now a note is at most 20,000 characters (`note_too_long`), at
  most 50 wait at once (`notes_waiting`), and a project's shelf holds 200
  things or 50 MB (`shelf_full`); each refusal is plain, with its next step.
- **A batch is answered.** A JSON-RPC batch, or a line that is JSON but no
  object, had no reply, so a client waited on it for ever. It is now told
  `invalid request` (MCP has had no batches since 2025-06-18).
- **A code that opens something is withheld.** The pin moves to Willow's
  `privacy` 0.1.1 (willow-memory/Willow#380): a gate, door or alarm code, a
  passcode, a PIN or a combination, 3 to 10 digits after what it opens,
  the label kept (`Gate code is [withheld: code]`). Two files differ, its
  code and its card; the card says what it still misses, a few digits with
  nothing before them saying what they open.
- **Withholding hands back every text, in its place.** `withhold` scrubs
  many texts in one pass, joined by a separator. Willow's pattern for a
  private key runs to its END, or to the end of what it is given when
  there is none, so a key cut short took the separators after it: with a
  whole key further on, each text after it came back as the one two places
  later (a passage under another's place on a session's page) and the
  last ones were gone. Seen in a folder skill whose `id_ed25519` hid the
  file after it. When fewer texts come back than went in, each is now
  scrubbed alone; if one still doesn't come back whole, nothing leaves.
- **A key is never listed in a skill.** A folder skill skipped only a
  `.key` file and the box's own key, so `id_ed25519` was listed and given
  (its words withheld by the scrub). Now a key by its kind (`.key`,
  `.pem`, `.p12`, `.pfx`) or by a private key's words is never listed, nor
  named as a skill of its own.
- **Nothing to share says why it can be.** `nothing_to_scope` told the
  person "no question has found anything in your files", even straight
  after a read that found something and a second that found nothing. It
  now says the last question found nothing, or something else was asked of
  them since; a model's door says to read again with a question their files
  hold, then propose straight after.
- **Both repos have a pull request.** Willow's commits this was built on
  are willow-memory/Willow#379. Its rule is one version step for each
  add-on a pull request changes, so `kart` (stepped to 0.1.7 a commit at a
  time), `timeline` and `todo` (to 0.1.3) are numbered kart 0.1.3,
  timeline 0.1.2 and todo 0.1.2 there. The pin moves to that commit:
  three add-on cards differ by their version line, and nothing else.
- **A model is told what is its own to fix.** A refusal's next step began
  "Tell the person:" at a model's door whatever it was. For the ones a
  model can put right itself (a report's name, a question with no words,
  a missing argument, a date not written year-month-day, a task or shelf
  name that isn't there, a grant not yet asked for) it is now said to the
  model, in words written for it. What only the person can fix is still
  passed on to them.
- **A check quick enough to run every time.** The tests took six minutes
  under each Python: six hundred of them, each starting a few programs,
  one after another on one core. `check.py` now runs them in parts, one a
  core, cut by Willow's `test-shards` (in the pin) from each file's past
  time; and a pass is remembered by everything the tests can read, so a
  change to the docs alone runs only the test that holds `FILES.md`.
  `--all` runs everything; `--jobs N` sets how many at once.
- **Two refusals that gave the wrong cause.** A question with no words was
  refused as a record that wouldn't open; it is now refused as a question
  with no words, before the kernel is asked. `answer` after a read under a
  grant blamed `WILLOW`; it now says there is no sealed page to answer.
- **The ignore file says what it relied on others for.** `.venv/` and
  `.ruff_cache/` (each ignored only by its own tool), an assistant's
  settings for this machine (ignored only by the owner's own global
  file), and what must never be committed from here: `*.key`, `share.id`
  and `.env`.
- **Easier to use, from one day's friction.** The person's door takes one
  request by words (`pipe.py --box DIR waiting`, `name=value` for an
  argument) and answers so a person can read it; `set_up.py --write
  command` saves it as `provider` with the record filled in. `share_send`
  takes `"answers": "last"`, and `shares` lists the sentences that could
  go by their first words. The prompt hook no longer tells a session that
  asked to be let in that it is given nothing: it points at the `context`
  tool, decided beside the box with no row written. The `page` tool's
  description says what its check holds a sentence to. What `share_receive`
  and `shares` say names a key by the name the person gave it.
- **A short front page, and a list of every file.** The README keeps the
  two lines, how a question goes and set-up; its other sections moved,
  word for word, into `docs/`, with the open list (`docs/OPEN.md`, once
  `GROK-HANDOFF.md`) and the design notes. `FILES.md` names every file
  and what it is, and `tests/test_files.py` fails when it and the folder
  disagree, as Willow's own does.
- **Two seal paths gone (the owner's rulings, 2026-11-18).** On the real
  record the per-item reading seals had been used five times, against four
  sessions let in. *A report* no longer waits on a seal of its own: a model
  is told there is one, and a session let in is given it as it reads now.
  `reports.json` is no longer written, and a report still waiting from
  before says so on the seal page. *A skill*: naming it, on the person's
  door, is the yes. Its fingerprint is kept beside the box, a model is
  given it while the file still reads that way, and `{"stop": "NAME"}`
  stops it until it is named again. One sealed before stands by that seal.
  Still sealed one at a time: a page for a question, a kept note, a task, a
  kept answer, a package to share, and a session's own yes.
- **Three rulings of the owner's, 2026-11-18.** A task a session took up
  is always listed and weighs nothing toward the task list's limit, so
  claimed work never crowds out what is still to do. The `plate` prompt
  asks for `minutes` too, and says only its open actions. `bring_in` takes
  `mail` (`.eml` and `.mbox`) and `sms` (a phone's backup of its texts and
  calls, with `me` and `tz` handed on), both Willow's add-ons, in the pin.
- **Fewer rows on the record.** A third of a day's rows were this runtime
  asking the kernel what it had already said: whether a grant, a task, a
  note or a skill is sealed (a row each time), and what waits (a row each
  time, often twice a call). A yes is now remembered by the door that
  asked, in memory only, with the fingerprint of the proposal file it was
  for, and stands only while that file reads the same (Willow's forge:
  put to the person once and remembered; stale seals, asked again). A no
  is never remembered. What waits is asked once while a call is answered.
- **Four more reports.** `ref-check` (links and `file:line` places that no
  longer hold), `pii-audit` (where personal numbers sit), `secrets-audit`
  (where passwords and keys sit) and `minutes` (decisions and actions from
  meeting notes), each one of Willow's add-ons, each a line in the reports
  and in the pin (with `habits`, which `minutes` loads; `privacy` was
  already there). The audits list a kind and a place and never the value:
  Willow's `pii-audit` shows the last digits of a number; the person's own
  door keeps them, and for a model this leaves
  them out, and a test fails if any digit or secret comes back. `minutes`
  names who owns each action, so it says it names people, like `people`,
  but its rows stay decisions and actions.
- **Three more things to bring in: Joplin, Evernote and Google Keep.**
  `bring_in` takes `joplin` (a `.jex` export), `evernote` (`.enex` files)
  and `google-keep` (the `.json` notes of a Takeout), each by Willow's
  add-on of that name, run by its command line as `notes` is: a text mirror
  in `brought-in/KIND-NAME/`, the original never changed, and the same
  folder again under the same name safe. Still the person's door only. The
  three add-ons load only the kernel, and join the pin.
- **A limit on the whole task list.** `tasks` gives a model at most 20,000
  characters of words at once. Over it, the oldest tasks that fit are given
  and the answer says `more: true`: never how many, and only tasks that
  session may see are weighed. Not refused whole, as the notes are, since a
  session given no task can take none up. Finish a task and ask again for
  the rest. Tasks are now given oldest first.
- **A smaller default for what a job prints.** `job` and `job_result` give
  4,000 characters, not 20,000. A longer print is cut at a whole line and
  says so, and how to get the rest: `more: yes` gives up to 20,000 (`run`
  runs the job again; `result` reads the same print again). It is still
  withheld before it is cut, and `clipped` and `how` are unchanged.

- **A page for the tool groups.** The seal page's fifth page, **What a
  model is offered**, shows each group, the tools in it, whether it is on
  and why, with a button to switch it. It is held to the same table as
  every other page; the core has no button.
- **Twelve tools, not 26.** A model's verbs are grouped into tools with an
  action each (`shelf`, `task`, `job`, `page`, `note`, `share`), in groups
  the person switches with `tools`: nine tools and about 1,200 tokens by
  default, from 26 and about 3,000. Sharing and skills come on when they
  are used. A group that is off is refused at every door that faces a
  model, not only left off the list; its resources and prompts go with it;
  a client is told when the list changes. The verbs, and what is written
  down, are unchanged. Refusals and prompts name the tool a model has.
- **What is kept, and taking it away.** `stored` shows what is kept beside
  the record; `remove` deletes what the person names and `archive` packs
  it into a tarball first. Before a file goes, its name, size and
  fingerprint are written on the record by Willow's new `removed` add-on,
  never its words; if that row can't be written, nothing is removed. A
  session the person let in can take a thing off its own shelf
  (`shelf_remove`). `changed`, and every session's start (at most once an
  hour), runs Willow's `what-changed`, so a file deleted from the folder
  leaves its hole too. (The owner, 2026-11-18: it is the person's data to
  delete or archive; the hole stays in the record.)
- **Faster over a big folder.** The pin moves to Willow's `timeline`
  and `todo` as they read only the files that matter for dates: 35
  seconds to 8, and 18 to 7, over 190,000 passages, the output unchanged.
  `pile-store` was measured and left out: reading the folder takes 1.4
  seconds, loading a store 2.3.
- **Two files to hand on.** `timeline` writes one matter from the folder
  in date order, each line cited (Willow's `timeline`); `feed` writes the
  sentences the person sealed as an RSS file (Willow's `rss-out`), or
  everything sealed on their word. Both are on the person's door, and a
  session they let in can have either made for them; a timeline comes
  back to it withheld, a feed not at all. The pin now covers both add-ons.
  A long timeline comes to a session in parts of whole lines, by date if
  it asks, without what the person leaves out of reports. The pin moves to
  Willow's `timeline` 0.1.2: `--every`, used first here, and no line that
  holds no letter or digit (found reading a 787-line timeline, 2026-11-18).
- **A job that travels, and corrections.** On the person's door,
  `job_write`, `job_take`, `job_run` and `job_gather` carry Willow's kart
  round trip: a job sealed and sent, taken and sealed where it lands, run
  in the sandbox, its result sealed and sent back, the results added up.
  A run is always held to whole numbers, and `share_send` refuses a result
  that isn't (the owner's ruling of 2026-11-18). `replaces` on a send, a
  forward or a model's proposal makes a correction, and `share_receive`
  says where the package it replaces went next.
- **A new key, and a record held to what others kept.** `share_rotate`
  makes a new sharing identity signed by the old one, keeps the old file
  under another name, and every later package carries the rotation.
  `share_witness` holds the record to packages signed over where it stood:
  holds, rewritten or cut short. `backup` now leaves the identity out.
  `uv.lock` is ignored.
- **Sharing with another person**, by Willow's `share`. On the person's
  door: `share_id` (an identity that is not the seal key), `share_person`,
  `share_send`, `share_receive`, `share_forward`, `shares`. Only a sentence
  the person sealed goes in a package. A model may put one together for
  the person's seal (`share_propose`), for someone they named, by name and
  never by key; sealed, it is packed once and the file is the person's to
  send. A package that arrived and held is read by a session the person
  let in (`share_received`), checked again each time. (The owner's rulings
  of 2026-11-18.)
- **The rest of a model's tools, under that yes.** While a session's grant
  stands, `report` gives the report as it reads now, `skill` gives a skill
  the person named as it reads now (never one they declined or stopped),
  `notes` reads back a note still waiting, marked so, and a task a model
  adds for its own folder is open at once to sessions the person let in
  there, marked as not sealed. Nothing is proposed for any of them. A task
  for another folder, a note to keep, a sentence back and a file that
  leaves still wait on the seal.
- **A skill can be a folder.** Naming a folder that holds a `SKILL.md`
  seals its words and, under them, each other text file by the fingerprint
  of its words. A model asks for a file by its name on that list and is
  given it only while it reads as listed; a file changed, added or removed
  unseals the folder. Links, hidden files, keys and anything outside the
  folder are never listed.
- **One yes for a session.** A session asks once, at its start, to read
  from the person's files while it works in its folder; sealed, `context`
  answers it directly, withheld, until the session ends or the person
  stops it. A session that starts again asks anew. Without it, everything
  is as before. (The owner, 2026-11-17: a seal should be something the
  person really needs to do.)
- **Asked where you are.** `seal_prompt.py` asks for a session's grant in a
  pinentry dialog on the person's desktop (seal, decline, not now) and
  carries out the click by the kernel's command. It is no door, asks about
  nothing else, and runs only where `ask-here` sits beside the box. An
  answer that isn't a clear yes or no is never a yes.
- **`job_later` and `job_result`.** A job too long to wait on is queued in
  the session's own queue (Kartikeya's SQLite queue, through Willow's kart
  0.1.6) and worked in the background; the worker stops when the queue is
  empty and the queue goes with the session. A worker that refused (no
  sandbox, a resource group that isn't ready) is said with the job that
  still waits. The pin moves to a kart that puts back the limits a
  reload of systemd empties out of the resource group.
- **A job says how it ended.** One that ended badly says how; one whose
  output Kartikeya clipped says so; the runtime no longer waits on a job
  without a limit. The pin moves to Willow's kart 0.1.5, which keeps a
  failed job's last printed line off the record (found putting kart
  through its paces, 2026-11-18).
- **`job`, under that yes.** A shell job over the folder in Kartikeya's
  sandbox, by Willow's `kart try`: read-only, no network, no box, no key.
  The pin now covers `share` and `adapters/deps/kart`, and moves to Willow
  ba274db5 (kart 0.1.4).
- **A skill, sealed by its words.** `skill_add`, on the person's door
  alone, names a file of instructions; its words as it reads now wait on
  the seal. A model's `skill` asks by name and is given exactly the sealed
  words, from the kernel, and never a file it named. A skill whose file
  changed since is given to no one until it is named again and sealed as it
  then reads; `stop` covers it; `skills` says where each stands; the seal
  page shows one as instructions to read first.
- **`question_me`, a fourth prompt.** Over a page the person sealed, the
  model asks three questions one at a time, each naming its passage, and
  answers nothing for them (Willow's `socratic` idea, as a prompt).
- **The guard now covers `BOX.runtime`.** A model with file tools could write,
  or `rm`, `stopped.json`, `names.txt`, `sent.jsonl` and the rest of what the
  runtime keeps beside the box, and so un-stop a page or cut the sent log. The
  guard gives Willow's `hook-guard` that folder (`--also`) and the pin moves to
  a Willow where it holds it, and where a `mv` out of the box is refused too.
  Reading the folder is still fine, and the runtime still writes there. It
  stops a careless or direct tool call, not code a model runs that builds a
  path at run time.
- **`people`, a fourth report.** Everyone the person's files name, a line
  each: how often, in how many files, over what dates; never every place
  they are mentioned. Its first line and its claim on the seal page say it
  names people. It is one call to Willow: the pin moves to a Willow whose
  `people` 0.1.2 gives its roster and every drill-down as one report
  (`--json`), where asking a person at a time read the whole folder once a
  person. Proposed as a task on the queue, sealed by the person, and done
  from it.
- **A report's exit code says what it found.** `report` took any exit but
  0 for a failure; Willow's reports exit 42 when something waits on the
  person, or when there is nothing. 0 and 42 are both read by what the
  report says.
- **`promises`: what a model can never do, to look at.** On the person's
  door, and a fourth page of the seal page. It lists the verbs each kind of
  door has, read from the code as it stands; what no model's door can do
  (no verb to seal or decline, the verbs only the person has, an unknown
  door treated as a model's); and fifteen promises, each with the test that
  holds it. A test fails if a named test is gone, or if the list of verbs
  drifts from the code. Nothing on the page but Close. No model's door has
  it, and it writes nothing to the sent log.
- **The checks on a sentence, shown on its card.** When a model's sentence
  stands and is proposed, the runtime keeps each check `sentence-check` ran
  and what it said, with the hash of the page it was held to and none of the
  page's words, in `checks.json` beside the box. `waiting` hands them on, and
  the seal page lists them under the sentence in plain words. A sentence with
  no kept checks says its record isn't kept, never that it passed.
- **`bring_in` and `brought_in`: a notes vault or a calendar, brought into
  your folder.** On the person's door only: Willow's `notes` and `calendar`
  add-ons write a text mirror of an Obsidian or Logseq vault, or of .ics and
  .vcf files, into `brought-in/KIND-NAME/` in the folder the record reads,
  so the next question finds it. The original is never changed. A `from`
  inside the record or the folder, a name that is not one plain folder name,
  and a mirror that is already there from somewhere else are refused. The
  same folder again under the same name is safe: files are written again
  and none removed. What was brought in is kept in `brought-in.json` beside
  the record (so `backup` carries it), listed by `brought_in` and shown in
  `status`. `notes` and `calendar` join the pin.
- **A task queue, and the notes you kept.** A model can read back the notes
  you sealed to keep (`notes`, the person's ruling of 2026-11-17): each is
  asked of the kernel under its own question and given only when sealed,
  withheld, whole, and never over 20,000 characters (then refused, not cut).
  A task is proposed by you (`task`) or a model (`task_add`) for your seal,
  which means "yes, do this" and grants nothing else. A model is given only
  sealed tasks of its own project (`tasks`), takes one up (`task_claim`, the
  first wins) and finishes it (`task_done`, the result on the project's shelf).
  `task_drop` takes one off every list and needs no seal. Before a seal a model
  learns only that its own task waits. Nothing under `written/` is read on
  trust, nothing runs a task, and the seal page, `owed` and `status` show a
  task as a task. Five new refusals in plain words. `capture` no longer says
  a model cannot read a note back.

- **`status`: how things stand, in one look.** On the person's door, and a
  third page of the seal page: what waits on the seal, counted by what each
  thing is; what the folder needs (Willow's `digest`, less the folders left
  out of reports); what was shared and kept, and each project's shelf; how
  this is set; and whether the record is all right (Willow's `box-health`).
  A part that couldn't be looked at says so and the rest still shows.
  `digest`, `stale-answers` and `box-health` join the pin. No model's door
  has it.
- **A propose scopes its own read.** One record hears every session, and
  another session's question could land on it between this door's read and
  its propose: the propose then refused with nothing to share, or scoped
  the other question's passages (which failed closed when the page was
  asked for). The question is now asked again at the propose, from this
  process's memory and nowhere written down.
- **Prompts that say what to type.** Each prompt's menu line says what to
  type after it and what comes back; `ask` no longer needs its question
  typed after the command: run bare, the assistant asks for it.
- **Resources and prompts.** The MCP door lists what it can be asked for
  (the reports by name, the page last sealed, this project's shelf) and
  reads each as the verb it stands for (`report`, `leave`, `shelf_read`), so a
  read is decided, refused and written down as that verb is, and the list
  says nothing of the person's files. It also lists three prompts the
  person can start from their own client: `plate` (what's on my plate),
  `ask` (a question, by its sealed page) and `wrap_up` (keep what a session
  found). Neither list is a tool: a model is never offered them to call.
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
- **`coming-up`, a third report.** Every line of the person's folder that
  holds a date in the next 14 days, soonest first, sealed like the others.
  Willow's `coming-up` and the `pieces` it loads join the pin.
- **A session hears its own folder's handoff.** One record hears every
  project's sessions, and a session here was told to pick up where one in
  another project had stopped. The pin moves to a Willow where
  `hook-handoff` 0.1.1 gives the last handoff that ended in the asking
  session's folder, and `todo` no longer counts a checkbox that opens with a
  template's blank (`- [ ] {item}`).
- **The seal page fills its window.** It was held to a fixed width, which
  made a long report hard to read; only running prose keeps a short line.
- **A shelf for each project.** A session puts what it makes (a report, a
  list, working notes) on the shelf of the folder it is working in:
  `shelf_add`, `shelf_list` and `shelf_read` on a model's door, with no seal, since
  nothing on a shelf was ever the person's files and nothing on it leaves.
  Shelves live under `BOX.runtime/shelf/`, beside the record and outside
  the folder questions read; nothing on one is written over; each thing
  says which session put it there; `backup` and `restore` carry them; and
  `shelves` and `shelf_read` on the person's door read any of it. A moment named
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
  person's door only, reads it there. A model reads back only what was
  sealed, through `notes`.
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
