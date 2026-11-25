# Contributing

Read [README.md](README.md) first: the two lines are the whole design.

1. **A grant guards what leaves, never what is read.**
2. **Hooks are doors, not verbs: one local runtime decides.**

## The rules a change is held to

- **Nothing decides a seal, and nothing reads the person's key.** No door
  has a verb to seal or decline, and neither has the runtime; sealing is the
  person's, with their key, outside any door. One file carries a seal out:
  `seal_page.py`, on the person's click, by the kernel's own command line
  (the person's ruling of 2026-11-17: code may carry out a seal decided
  where no model's door reaches). It is no door, and no door may import it.
  A change to it is held to the table at its top, and to
  `tests/test_seal_page.py`. The key is the user's.
- **A door decides nothing.** It imports `runtime` and nothing else that
  decides, and never calls Willow itself; `tests/test_doors.py` fails it
  otherwise. A new door gets a line in `runtime.FACES`, or it faces a model.
- **What reaches a model, or leaves as a file, is written down** on the sent
  log, by `runtime.call`; a new way out goes through it.
- **Every refusal is plain.** A new one gets a code, a line in `PLAIN`, and a
  scenario in `tests/test_plain.py`, which fails a code without one.
- **Willow by its command line only.** Nothing here imports or changes
  Willow's `kernel.py`; when Willow lacks something, the fix goes to Willow.
- **Willow by its pin.** `willow.pin.json` names the Willow this runs on,
  every file of it by hash. What runs is a copy of that commit, made from
  the git `WILLOW` names and kept in its git folder, so the checkout there
  can be on any branch. To move it, `python3 willow_pin.py follow
  [COMMIT] [-- CHECK ARGS]`: it fetches, repins at COMMIT (origin/main
  when none is named), runs `check.py`, and commits the pin only if it
  passes, else puts it back; it never pushes. `repin --at COMMIT` moves it
  without the check; with no `--at` it pins the checkout's own commit. It
  says what moved, and the commit goes with the change that needs it.
  `prune [--days N]` lets go of copies nothing has run for N days (14 by
  default), never this pin's; one let go is made again when it is wanted. It pins kernel.py and every file of each
  add-on the pin names but its tests, so an add-on's new file comes in by
  itself. A new add-on the runtime runs comes in with
  `repin --add NAME` (from `adapters/stdlib`, or `adapters/deps` when it
  needs a package), and with it what it loads from beside it; `--drop NAME`
  lets one go. Some are pinned only because another loads them:
  batch-ask (index-cache and claude-code load its scan), todo (batch-ask's
  scan), coming-up and pieces (digest; coming-up loads pieces),
  stale-answers (digest; it loads pieces), habits (minutes), privacy
  (secrets-audit and hook-leaks), openai-compatible (local-model), share
  (kart: a job that came in a package, a result sent back), starter-words
  (set_up prints its copy), test-shards (check.py cuts the tests by it).
  Kart is under deps: Kartikeya runs a sealed job in a Python that has it.
- **Never loosen a check to get green.** No skipped test, no loosened
  assertion.

## Before a change lands

    WILLOW=/path/to/Willow python check.py

It holds Willow to its pin and runs `ruff check`, `ruff format --check` and
the tests, here on this machine; `--python PY` (as often as wanted) names
the Pythons to run the tests under. That is the check that counts. The
workflow on GitHub runs the same, as a second opinion, and `check.py hook
--write` holds `main` to it in a checkout with no server asked.

`ruff format` reflows lines, so a scripted find-and-replace written against
the text before formatting can match nothing, silently: check that each one
matched.

Add a line to [CHANGELOG.md](CHANGELOG.md) under Unreleased. A file added,
moved or removed is added, moved or removed in [FILES.md](FILES.md) too,
with a few words saying what it is; `tests/test_files.py` fails otherwise.
