# Contributing

Read [README.md](README.md) first: the two lines are the whole design.

1. **A grant guards what leaves, never what is read.**
2. **Hooks are doors, not verbs: one local runtime decides.**

## The rules a change is held to

- **Nothing seals, and nothing reads the person's key.** No door has a verb
  to seal or decline; sealing is the person's, with their key, outside any
  door. The key is the user's.
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
  every file of it by hash. To move it, commit in Willow, then
  `python3 willow_pin.py repin`: it says what moved, and the commit goes
  with the change that needs it. A new add-on the runtime runs goes in
  `willow_pin.ADD_ONS`, with what it loads from beside it.
- **Never loosen a check to get green.** No skipped test, no loosened
  assertion.

## Before you push

    ruff check . && ruff format --check .
    WILLOW=/path/to/Willow python -m pytest -q

`ruff format` reflows lines, so a scripted find-and-replace written against
the text before formatting can match nothing, silently: check that each one
matched.

Add a line to [CHANGELOG.md](CHANGELOG.md) under Unreleased.
