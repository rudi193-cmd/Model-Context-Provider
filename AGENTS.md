# For agents

Read [README.md](README.md) first: the two lines are the whole design.

- **Never seal, never read the person's key.** No door has a verb to seal,
  and the runtime has none either. `seal_page.py` alone carries out a seal
  or a decline, on the person's click, by the kernel's own command; it is no
  door, no door imports it, and the kernel reads the key, never this code.
  Never start it, open its link or click it for the person. The key is the
  user's.
- **A door decides nothing.** It imports `runtime` and nothing else that
  decides; `tests/test_doors.py` fails it otherwise. A new door gets a line
  in `runtime.FACES`, or it is treated as facing a model.
- **Willow by its command line only, and by its pin.** Nothing here imports
  or changes Willow's `kernel.py`; `willow.pin.json` names the Willow it
  runs on, and `willow_pin.py repin` is the only way to move it.
- **After a change:** `ruff check . && ruff format --check . && python -m pytest`,
  with `WILLOW` pointing at Willow. CONTRIBUTING.md has the rest.
