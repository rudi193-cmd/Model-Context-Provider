# For agents

Read [README.md](README.md) first: the two lines are the whole design.

- **Never seal, never read the person's key.** No door has a verb to seal,
  and the runtime has none either. Two programs carry out a seal or a
  decline, each on the person's click, by the kernel's own command:
  `seal_page.py`, and `seal_prompt.py`, which asks in a desktop dialog about
  a session's grant and nothing else. Neither is a door, no door imports
  either, and the kernel reads the key, never this code. The runtime starts
  `seal_prompt.py` only where the person turned it on (`ask-here` beside the
  box). Never start either yourself, open the page's link, or click or
  answer either for the person, with any tool. The key is the user's.
- **A door decides nothing.** It imports `runtime` and nothing else that
  decides; `tests/test_doors.py` fails it otherwise. A new door gets a line
  in `runtime.FACES`, or it is treated as facing a model.
- **Willow by its command line only, and by its pin.** Nothing here imports
  or changes Willow's `kernel.py`; `willow.pin.json` names the Willow it
  runs on, and `willow_pin.py repin` (or `follow`, which repins, checks and
  commits) is the only way to move it. What runs is a copy of the pinned
  commit, made from Willow's git; `WILLOW` names that git, on any branch.
- **After a change:** `python check.py`, with `WILLOW` pointing at Willow:
  the pin, `ruff check`, `ruff format --check` and the tests, on this
  machine. That is the check that counts; a pull request or a workflow
  elsewhere is not the gate. CONTRIBUTING.md has the rest.
