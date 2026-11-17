# For agents

Read [README.md](README.md) first: the two lines are the whole design.

- **Never seal, never read the person's key.** No door has a verb to seal.
  The key is the user's.
- **A door decides nothing.** It imports `runtime` and nothing else that
  decides; `tests/test_doors.py` fails it otherwise. A new door gets a line
  in `runtime.FACES`, or it is treated as facing a model.
- **Willow by its command line only.** Nothing here imports or changes
  Willow's `kernel.py`.
- **After a change:** `ruff check . && ruff format --check . && python -m pytest tests`.
