"""The one local runtime. Every door calls this; nothing else decides.

Line 1: a grant guards what leaves, never what is read. Reading goes through
Willow's kernel and needs no grant.

Willow is used by its command line only (kernel.py and its add-ons), so the
kernel is never changed or imported here. WILLOW names the checkout; the
default is a sibling folder named Willow.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WILLOW = Path(os.environ.get("WILLOW", HERE.parent / "Willow"))


def willow(*args: str) -> subprocess.CompletedProcess:
    """Run one of Willow's commands, its output caught."""
    return subprocess.run(
        [sys.executable, *args], cwd=WILLOW, capture_output=True, text=True, check=False
    )


def state(box: Path) -> Path:
    """Where the runtime keeps what it handed a model: beside the box, never in it."""
    d = box.parent / (box.name + ".runtime")
    d.mkdir(exist_ok=True)
    return d


def read(box: Path, question: str) -> dict:
    """Ask the box. Reading never needs a grant: this is the kernel's bite,
    as the kernel answers it."""
    run = willow("kernel.py", "bite", "--box", str(box), question)
    if run.returncode == 2:
        return {"state": "refused", "why": run.stderr.strip()}
    got = json.loads(run.stdout)
    # kept beside the box, for holding a model's answer to what was served
    (state(box) / "last-read.json").write_text(json.dumps(got.get("served", [])))
    return got


APPROVED_ONLY = "adapters/stdlib/approved-only/approved_only.py"


def propose(box: Path) -> dict:
    """Propose what may leave: the passages the last read served, as one scope
    for the person to seal. The runtime only proposes; it never seals."""
    run = willow(APPROVED_ONLY, "scope", "--box", str(box))
    subject = next((w for w in run.stdout.split() if w.startswith("proposal:")), None)
    if run.returncode == 2 or subject is None:
        return {"state": "refused", "why": (run.stderr or run.stdout).strip()}
    return {"state": "waiting", "seal": subject}


def leave(box: Path, to: Path) -> dict:
    """Let context leave. Line 1: only a scope the person sealed leaves, as the
    one file the model reads; without one, nothing is written and it says so."""
    run = willow(APPROVED_ONLY, "--box", str(box), "--to", str(to))
    if run.returncode != 0:
        return {"state": "refused", "why": run.stderr.strip()}
    return {"state": "left", "to": str(to)}


#: who is on the far side of each door. A door not named here faces a model:
#: an unknown door fails closed.
FACES = {"pipe": "person", "mcp": "model"}


SENTENCE_CHECK = "adapters/stdlib/sentence-check/sentence_check.py"


def leave_to_model(box: Path) -> dict:
    """Line 1 at a model's door: the sealed scope's one file, handed over as
    text. The model names no path. The runtime keeps a copy, to hold the
    model's answer to it."""
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "served.md"
        got = leave(box, page)
        if got["state"] != "left":
            return got
        text = page.read_text()
    (state(box) / "last-page.md").write_text(text)
    return {"state": "left", "page": text}


def boxes_of(page: str) -> list[dict]:
    """The boxes a served page holds: each passage's opaque id and its text."""
    boxes, cur = [], None
    for line in page.splitlines():
        if line.startswith("- `") and line.endswith("human-sealed"):
            cur = {"id": line.split("`")[1], "lines": []}
            boxes.append(cur)
        elif cur is not None and line.startswith("  ") and line.strip() != "```":
            cur["lines"].append(line[2:])
    return [{"id": b["id"], "text": "\n".join(b["lines"])} for b in boxes]


def answer(box: Path, sentence: str) -> dict:
    """The model's way back: one sentence about the page it was given. Code
    holds it to that page (Willow's sentence-check: every cite served, every
    box cited, nothing the boxes lack); a sentence that stands is proposed
    through the kernel and waits for the person's seal. The model never
    writes, and a struck sentence goes nowhere."""
    page = state(box) / "last-page.md"
    if not page.exists():
        return {"state": "refused", "why": "nothing has left to you to answer"}
    boxes = boxes_of(page.read_text())
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "boxes.json"
        f.write_text(json.dumps(boxes))
        run = willow(
            SENTENCE_CHECK, "--sentence", sentence, "--boxes", str(f), "--json"
        )
    if run.returncode not in (0, 42):
        return {"state": "refused", "why": run.stderr.strip()}
    report = json.loads(run.stdout)
    checks = {r["where"]: r["what"] for g in report["groups"] for r in g["rows"]}
    if run.returncode == 42:
        return {"state": "struck", "checks": checks}
    served = json.loads((state(box) / "last-read.json").read_text())
    by_text = {s["text"].strip(): s["id"] for s in served}
    cites = [by_text.get(b["text"].strip()) for b in boxes]
    if None in cites:
        return {"state": "refused", "why": "the page is not what the last read served"}
    prop = {"path": "answers/" + hashlib.sha256(sentence.encode()).hexdigest()[:12] + ".md",
            "data": sentence + "\n", "cites": cites,
            "claim": "a model's sentence on a sealed page; sentence-check held it"}  # fmt: skip
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "suggestions.jsonl"
        f.write_text(json.dumps(prop) + "\n")
        run = willow("kernel.py", "propose", "--box", str(box), "--file", str(f))
    if run.returncode == 2 or "refused" in run.stdout:
        return {"state": "refused", "why": (run.stderr or run.stdout).strip()}
    subject = next((w for w in run.stdout.split() if w.startswith("proposal:")), None)
    return {"state": "waiting", "seal": subject, "checks": checks, "path": prop["path"]}


#: the verbs, the same for every door. There is no verb to seal.
VERBS = {
    "person": {
        "read": lambda box, arg: read(box, str(arg)),
        "propose": lambda box, arg: propose(box),
        "leave": lambda box, arg: leave(box, Path(str(arg))),
    },
    "model": {
        # read is open, but its passages would leave to the model: it gets the
        # state alone, never a passage, a place or a count
        "read": lambda box, arg: {"state": read(box, str(arg))["state"]},
        "propose": lambda box, arg: propose(box),
        "leave": lambda box, arg: leave_to_model(box),
        "answer": lambda box, arg: answer(box, str(arg)),
    },
}


def call(box: Path, verb: str, arg=None, door: str = "") -> dict:
    """What every door calls: one verb, decided here, by who the door faces."""
    verbs = VERBS[FACES.get(door, "model")]
    if verb not in verbs:
        return {"state": "refused", "why": f"no verb {verb!r}; one of {sorted(verbs)}"}
    return verbs[verb](box, arg)
