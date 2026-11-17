"""The one local runtime. Every door calls this; nothing else decides.

Line 1: a grant guards what leaves, never what is read. Reading goes through
Willow's kernel and needs no grant.

Willow is used by its command line only (kernel.py and its add-ons), so the
kernel is never changed or imported here. WILLOW names the checkout; the
default is a sibling folder named Willow.
"""

from __future__ import annotations

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


def read(box: Path, question: str) -> dict:
    """Ask the box. Reading never needs a grant: this is the kernel's bite,
    as the kernel answers it."""
    run = willow("kernel.py", "bite", "--box", str(box), question)
    if run.returncode == 2:
        return {"state": "refused", "why": run.stderr.strip()}
    return json.loads(run.stdout)


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


def leave_to_model(box: Path) -> dict:
    """Line 1 at a model's door: the sealed scope's one file, handed over as
    text. The model names no path; the file is written outside the box, read
    and removed."""
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "served.md"
        got = leave(box, page)
        if got["state"] != "left":
            return got
        return {"state": "left", "page": page.read_text()}


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
    },
}


def call(box: Path, verb: str, arg=None, door: str = "") -> dict:
    """What every door calls: one verb, decided here, by who the door faces."""
    verbs = VERBS[FACES.get(door, "model")]
    if verb not in verbs:
        return {"state": "refused", "why": f"no verb {verb!r}; one of {sorted(verbs)}"}
    return verbs[verb](box, arg)
