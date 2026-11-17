"""The session door: Claude Code's SessionStart and SessionEnd hooks, facing
the person.

    {"hooks": {
      "SessionStart": [{"hooks": [{"type": "command",
        "command": "python3 /path/to/model-context-provider/doors/session.py --box DIR"}]}],
      "SessionEnd": [{"hooks": [{"type": "command", "timeout": 60,
        "command": "python3 /path/to/model-context-provider/doors/session.py --box DIR"}]}]}}

At a session's end it asks the runtime to close the session: the record's
rows since the last close, as one proposal for the person to seal once. At a
session's start it tells the person what waits on their seal, as Claude
Code's systemMessage, which is shown to the person and never put in the
turn. It prints nothing else, since anything else a SessionStart hook prints
goes to the model. It always exits 0, and never crashes on what it is sent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


def told(got: dict) -> str:
    """The one line for the person at a session's start, or nothing."""
    if got.get("state") == "waiting":
        return got["say"]
    if got.get("state") == "refused":
        return f"{got['say']} {got['next']}".strip()
    return ""


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2 or argv[0] != "--box":
            return 0
        sent = json.loads(sys.stdin.read() or "{}")
        event = sent.get("hook_event_name") if isinstance(sent, dict) else None
        box = Path(argv[1])
        if event == "SessionEnd":
            runtime.call(box, "close", door="session")
        elif event == "SessionStart":
            line = told(runtime.call(box, "owed", door="session"))
            if line:
                sys.stdout.write(json.dumps({"systemMessage": line}) + "\n")
    except Exception as why:  # noqa: BLE001 - a crashed hook gets in the person's way
        # stderr, which Claude Code shows the person, never the turn
        print(f"model-context-provider session: {type(why).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
