"""The guard door: the assistant's own hooks around what it does.

Claude Code, in ~/.claude/settings.json (set_up.py prints it whole):

    {"hooks": {
      "PreToolUse": [{"matcher": "Write|Edit|…|Bash", "hooks": [{"type": "command",
        "command": "python3 …/doors/guard.py --box DIR"}]}],
      "PostToolUse": [{"matcher": "Bash", "hooks": [… the same command …]}],
      "Stop": [{"hooks": [… the same …]}],
      "SessionStart": [{"hooks": [… the same …]}],
      "PreCompact": [{"hooks": [… the same …]}]}}

At each of those moments it hands the runtime what the host sent and takes
back what the runtime decided. Before a tool call that is allowed or
blocked: a blocked call exits 2, which is how the host is told to stop it,
with the reason on standard error. A call the runtime couldn't judge is
blocked too. At any other moment it never blocks: it exits 0, and prints
only what the runtime says to hand over (where the last session ended, how
much waits on the person's seal).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime

#: the one moment a hook's exit code stops something
BEFORE = "PreToolUse"


def moment(raw: str) -> str | None:
    """Which moment the host says this is; None when it can't be read."""
    try:
        sent = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    name = sent.get("hook_event_name") if isinstance(sent, dict) else None
    return name if isinstance(name, str) else None


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print("usage: guard.py --box DIR", file=sys.stderr)
        return 2
    raw = sys.stdin.read()
    name = moment(raw)
    stops = name in (BEFORE, None)  # what can't be read can't be called safe
    try:
        got = runtime.call(Path(argv[1]), "event", raw, door="guard")
    except Exception as why:  # noqa: BLE001 - a guard that broke lets nothing through
        print(f"model-context-provider guard: {type(why).__name__}", file=sys.stderr)
        return 2 if stops else 0
    state = got.get("state")
    if state == "blocked":
        print(got.get("says", "blocked"), file=sys.stderr)
        return 2 if stops else 0
    if state == "refused":
        print(f"{got.get('say', '')} {got.get('next', '')}".strip(), file=sys.stderr)
        return 2 if stops else 0
    if state == "handed" and name == "SessionStart":
        out = {"hookSpecificOutput": {"hookEventName": name,
                                      "additionalContext": got["says"]}}  # fmt: skip
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    elif state == "handed":
        sys.stdout.write(got["says"] + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
