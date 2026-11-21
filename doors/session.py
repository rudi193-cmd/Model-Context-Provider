"""The session door: session start/end hooks facing the person.

Claude Code (default):

    {"hooks": {
      "SessionStart": [{"hooks": [{"type": "command",
        "command": "python3 …/doors/session.py --box DIR"}]}],
      "SessionEnd": [{"hooks": [{"type": "command", "timeout": 60,
        "command": "python3 …/doors/session.py --box DIR"}]}]}}

Cursor:

    python3 …/doors/session.py --host cursor --box DIR

At a session's end it asks the runtime to close the session: the record's
rows since the last close, as one proposal for the person to seal once. At a
session's start it tells the person what waits on their seal — Claude Code
as systemMessage (shown to them, never the turn); Cursor as user_message
plus a desktop notice, and after this server's MCP tools the same notice
when something waits. It prints nothing a model should take as data. It
always exits 0, and never crashes on what it is sent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime

HOSTS = frozenset({"claude-code", "cursor"})


def told(got: dict, host: str = "claude-code") -> str:
    """What to show the person: Claude Code gets the one-line say (never
    passage words); Cursor gets the card with each claim and seal line."""
    if got.get("state") == "waiting":
        if host == "cursor":
            return got.get("card") or got.get("say") or ""
        return got.get("say") or ""
    if got.get("state") == "refused":
        return f"{got.get('say', '')} {got.get('next', '')}".strip()
    return ""


def parse(argv: list[str]) -> tuple[str, Path] | None:
    if len(argv) == 4 and argv[0] == "--host" and argv[2] == "--box":
        return argv[1], Path(argv[3])
    if len(argv) == 2 and argv[0] == "--box":
        return "claude-code", Path(argv[1])
    return None


def event_of(host: str, sent: dict) -> str | None:
    """Which moment this host is in, from what it sent on stdin."""
    if host == "claude-code":
        name = sent.get("hook_event_name")
        return name if isinstance(name, str) else None
    # Cursor: sessionEnd carries reason; sessionStart carries session_id;
    # afterMCPExecution carries tool_name / result_json.
    if "tool_name" in sent or "result_json" in sent:
        return "afterMCPExecution"
    if "reason" in sent and "session_id" in sent:
        return "sessionEnd"
    if "session_id" in sent:
        return "sessionStart"
    return None


def show(host: str, line: str) -> None:
    """Put the card where this host shows it to the person, never the turn."""
    if not line:
        return
    if host == "claude-code":
        sys.stdout.write(json.dumps({"systemMessage": line}) + "\n")
        return
    if host == "cursor":
        sys.stdout.write(json.dumps({"user_message": line}) + "\n")
        runtime.nudge(line)
        return


def main(argv: list[str]) -> int:
    try:
        parsed = parse(argv)
        if parsed is None:
            return 0
        host, box = parsed
        if host not in HOSTS:
            print(f"model-context-provider session: no host called {host}",
                  file=sys.stderr)  # fmt: skip
            return 0
        sent = json.loads(sys.stdin.read() or "{}")
        if not isinstance(sent, dict):
            return 0
        event = event_of(host, sent)
        if event in ("SessionEnd", "sessionEnd"):
            runtime.call(box, "close", sent.get("session_id"), door="session")
        elif event in ("SessionStart", "sessionStart"):
            show(host, told(runtime.call(box, "owed", door="session"), host))
        elif event == "afterMCPExecution":
            # Only nudge when this server left something waiting.
            server = str(sent.get("mcp_server_name") or "")
            if server and server != "model-context-provider":
                return 0
            got = runtime.call(box, "owed", door="session")
            if got.get("state") == "waiting":
                runtime.nudge(told(got, "cursor"))
    except Exception as why:  # noqa: BLE001 - a crashed hook gets in the person's way
        print(f"model-context-provider session: {type(why).__name__}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
