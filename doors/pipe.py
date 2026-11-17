"""The pipe door: one JSON request a line in, one JSON answer a line out.

{"read": "when does the first frost come"}
{"propose": true}
{"leave": "/path/outside/the/box/served.md"}

python doors/pipe.py --box DIR < requests.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


def answer(box: Path, line: str) -> dict:
    try:
        req = json.loads(line)
    except json.JSONDecodeError:
        return {"state": "refused", "why": "not a JSON line"}
    if not isinstance(req, dict) or len(req) != 1:
        return {"state": "refused", "why": 'one request a line: {"verb": argument}'}
    verb, arg = next(iter(req.items()))
    return {"verb": verb, **runtime.call(box, verb, arg, door="pipe")}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print("usage: pipe.py --box DIR < requests.jsonl", file=sys.stderr)
        return 2
    box = Path(argv[1])
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(answer(box, line)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
