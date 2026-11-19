"""The pipe door: one JSON request a line in, one JSON answer a line out.

{"read": "when does the first frost come"}
{"propose": true}
{"leave": "/path/outside/the/box/served.md"}

python doors/pipe.py --box DIR < requests.jsonl

Or one request by words, answered so a person can read it (set_up.py
--write command saves this as `provider`, with your record filled in):

python doors/pipe.py --box DIR waiting
python doors/pipe.py --box DIR timeline mould landlord
python doors/pipe.py --box DIR share_send answers=last for=Walt note="As asked"
python doors/pipe.py --box DIR '{"report": "todo"}'

No word after the verb asks it plainly ({"waiting": true}); words like
name=value make its argument; anything else is its argument as it reads.
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


def worded(words: list[str]) -> str:
    """One request, as a JSON line, from the words of a command line."""
    if len(words) == 1 and words[0].lstrip().startswith("{"):
        return words[0]  # already a request
    verb, rest = words[0], words[1:]
    if not rest:
        return json.dumps({verb: True})
    if len(rest) == 1 and rest[0].lstrip()[:1] in ("{", "["):
        try:
            return json.dumps({verb: json.loads(rest[0])})
        except json.JSONDecodeError:
            return rest[0]  # refused below as not a JSON line
    if all("=" in w and w.split("=", 1)[0].isidentifier() for w in rest):
        pairs = (w.split("=", 1) for w in rest)
        return json.dumps(
            {verb: {k: {"true": True, "false": False}.get(v, v) for k, v in pairs}}
        )
    return json.dumps({verb: " ".join(rest)})


def shown(got: dict) -> str:
    """An answer for a person to read: a refusal in its plain words, a long
    text as itself, and the rest set out a field a line."""
    if got.get("state") == "refused" and got.get("say"):
        return f"{got['say']} {got.get('next', '')}".strip()
    text = got.get("text") if isinstance(got.get("text"), str) else None
    rest = {k: v for k, v in got.items() if not (k == "text" and text)}
    out = json.dumps(rest, indent=2, ensure_ascii=False)
    return f"{out}\n{text.rstrip()}" if text else out


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "--box":
        print("usage: pipe.py --box DIR < requests.jsonl\n"
              "       pipe.py --box DIR VERB [WORDS | NAME=VALUE ...]",
              file=sys.stderr)  # fmt: skip
        return 2
    box = Path(argv[1])
    if argv[2:]:
        got = answer(box, worded(argv[2:]))
        print(shown(got))
        return 2 if got.get("state") == "refused" else 0
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(answer(box, line)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
