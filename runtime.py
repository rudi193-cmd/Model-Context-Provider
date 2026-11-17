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
import re
import subprocess
import sys
import tempfile
import time
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


def sent(box: Path, door: str, verb: str, got: dict) -> dict:
    """Write down what just reached the far side of a door that faces a model,
    or a file leaving: the door, the verb, the state, and for a page each
    passage's hash and its page's hash, never the text. Each line names the
    hash of the one before it, so a cut or an edit shows. Returns got."""
    f = state(box) / "sent.jsonl"
    lines = f.read_text().splitlines() if f.exists() else []
    prev = hashlib.sha256(lines[-1].encode()).hexdigest() if lines else ""
    row = {"n": len(lines), "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "door": door, "verb": verb, "state": got.get("state"), "prev": prev}  # fmt: skip
    page = got.get("page")
    if page is not None:
        row["page"] = hashlib.sha256(page.encode()).hexdigest()
        row["passages"] = [
            hashlib.sha256(b["text"].encode()).hexdigest() for b in boxes_of(page)
        ]
    if got.get("to"):
        row["to"] = got["to"]
    with f.open("a") as out:
        out.write(json.dumps(row, sort_keys=True) + "\n")
    return got


def sent_log(box: Path) -> dict:
    """What has left, oldest first, and whether the log still holds: each line
    names the hash of the one before it. The last line has no later one to
    vouch for it, so a cut or edit there doesn't show here: pin_sent keeps
    the newest hash somewhere the log can't reach, and check_sent holds the
    log to it (Willow's tip-pin, for this log)."""
    f = state(box) / "sent.jsonl"
    lines = f.read_text().splitlines() if f.exists() else []
    rows, breaks = [], []
    for i, line in enumerate(lines):
        row = json.loads(line)
        want = hashlib.sha256(lines[i - 1].encode()).hexdigest() if i else ""
        if row.get("prev") != want or row.get("n") != i:
            breaks.append(i)
        rows.append(row)
    return {"state": "populated" if rows else "empty", "rows": rows, "breaks": breaks}


def pin_sent(box: Path, to: Path) -> dict:
    """Where the sent log ends, written to a file the person keeps out of the
    runtime's reach (Willow's tip-pin, for this log): how many lines, and the
    hash of the last. Never written over, and never inside the box."""
    got = sent_log(box)
    if got["breaks"]:
        return {
            "state": "refused",
            "why": f"the log doesn't hold at line {got['breaks'][0]}",
        }
    if to.exists():
        return {
            "state": "refused",
            "why": f"{to} is there already; a pin is never written over",
        }
    if to.resolve().is_relative_to(box.parent.resolve()):
        return {
            "state": "refused",
            "why": "a pin beside the box is in the runtime's reach",
        }
    lines = (state(box) / "sent.jsonl").read_text().splitlines() if got["rows"] else []
    tip = hashlib.sha256(lines[-1].encode()).hexdigest() if lines else ""
    to.write_text(json.dumps({"rows": len(lines), "tip": tip}) + "\n")
    return {"state": "pinned", "rows": len(lines), "tip": tip, "to": str(to)}


def check_sent(box: Path, pin: Path) -> dict:
    """The sent log against a pin: holds (perhaps with lines since), cut short,
    or rewritten where the pin ended."""
    try:
        want = json.loads(pin.read_text())
        rows, tip = int(want["rows"]), str(want["tip"])
    except (OSError, ValueError, KeyError, TypeError):
        return {"state": "refused", "why": f"{pin} is not a pin"}
    got = sent_log(box)
    if got["breaks"]:
        return {
            "state": "refused",
            "why": f"the log doesn't hold at line {got['breaks'][0]}",
        }
    lines = (state(box) / "sent.jsonl").read_text().splitlines() if got["rows"] else []
    if len(lines) < rows:
        return {"state": "cut short", "pinned": rows, "now": len(lines)}
    if rows and hashlib.sha256(lines[rows - 1].encode()).hexdigest() != tip:
        return {"state": "rewritten", "at": rows - 1}
    return {"state": "holds", "pinned": rows, "since": len(lines) - rows}


def read(box: Path, question: str) -> dict:
    """Ask the box. Reading never needs a grant: this is the kernel's bite,
    as the kernel answers it."""
    run = willow("kernel.py", "bite", "--box", str(box), question)
    if run.returncode == 2:
        return {"state": "refused", "why": run.stderr.strip()}
    got = json.loads(run.stdout)
    if "served" in got:  # kept beside the box, to hold a model's answer to it
        (state(box) / "last-read.json").write_text(json.dumps(got["served"]))
    return got


APPROVED_ONLY = "adapters/stdlib/approved-only/approved_only.py"


def propose(box: Path) -> dict:
    """Propose what may leave: the passages the last read served, as one scope
    for the person to seal. The runtime only proposes; it never seals."""
    run = willow(APPROVED_ONLY, "scope", "--box", str(box))
    subject = next((w for w in run.stdout.split() if w.startswith("proposal:")), None)
    if run.returncode == 2 or subject is None:
        return {"state": "refused", "why": (run.stderr or run.stdout).strip()}
    # what this scope holds, kept beside the box, so a page can be matched to it
    f = state(box) / "scopes.json"
    scopes = json.loads(f.read_text()) if f.exists() else {}
    served = json.loads((state(box) / "last-read.json").read_text())
    scopes[subject] = sorted(
        s.strip() for s in withhold(box, [s["text"] for s in served])
    )
    f.write_text(json.dumps(scopes))
    return {"state": "waiting", "seal": subject}


def serve(box: Path, to: Path) -> dict:
    """Willow's approved-only: the last sealed scope as one file, or refused."""
    run = willow(APPROVED_ONLY, "--box", str(box), "--to", str(to))
    if run.returncode != 0:
        return {"state": "refused", "why": run.stderr.strip()}
    return {"state": "left", "to": str(to)}


def leave(box: Path, to: Path) -> dict:
    """Let context leave as a file. Line 1: only a scope the person sealed,
    whole and withheld, the same page a model would get; never into the box
    or the folder it reads."""
    pile = Path(json.loads((box / "kernel.json").read_text()).get("pile", box))
    for name, root in (("the box", box), ("your folder", pile)):
        if to.resolve().is_relative_to(root.resolve()):
            return {"state": "refused", "why": f"{to} is inside {name}"}
    got = sealed_page(box)
    if got["state"] != "left":
        return got
    to.write_text(got["page"])
    return {"state": "left", "to": str(to)}


#: who is on the far side of each door. A door not named here faces a model:
#: an unknown door fails closed.
FACES = {"pipe": "person", "mcp": "model", "hook": "model"}


SENTENCE_CHECK = "adapters/stdlib/sentence-check/sentence_check.py"


PRIVACY = "adapters/stdlib/privacy/privacy.py"
SPLIT = "\n\x1eunnamed-split\x1e\n"


def names(box: Path) -> list[str]:
    """The names the person wants kept out of anything that leaves, one a
    line in names.txt beside the box."""
    f = state(box) / "names.txt"
    if not f.exists():
        return []
    return [n.strip() for n in f.read_text().splitlines() if n.strip()]


def withhold(box: Path, texts: list[str]) -> list[str]:
    """Texts as they may leave: Willow's privacy scrub (numbers, emails, keys),
    then each name the person listed, as [withheld: name]. One pass for all,
    so a page and what it is compared with are withheld the same way."""
    run = subprocess.run(
        [sys.executable, PRIVACY, "scrub"], cwd=WILLOW, input=SPLIT.join(texts),
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    if run.returncode != 0:
        raise RuntimeError("privacy scrub failed: " + run.stderr.strip()[:200])
    out = run.stdout.removesuffix("\n").split(SPLIT)
    for name in names(box):
        pat = re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.IGNORECASE)
        out = [pat.sub("[withheld: name]", s) for s in out]
    return out


def sealed_page(box: Path) -> dict:
    """The sealed scope's one file, as text, written outside the box and
    removed; or the refusal."""
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "served.md"
        got = serve(box, page)
        if got["state"] != "left":
            return got
        try:
            (text,) = withhold(box, [page.read_text()])
        except RuntimeError as why:  # can't withhold: nothing leaves
            return {"state": "refused", "why": str(why)}
    # approved-only drops a sealed passage that has since changed in the files,
    # and serves the rest without saying so: a page leaves only whole, as a
    # scope this runtime proposed
    f = state(box) / "scopes.json"
    scopes = json.loads(f.read_text()) if f.exists() else {}
    held = sorted(b["text"].strip() for b in boxes_of(text))
    if held not in scopes.values():
        return {"state": "refused",
                "why": "the sealed scope is not whole: a passage of it changed in "
                       "the files since it was sealed, or this runtime never "
                       "proposed it; nothing leaves until a scope is sealed again"}  # fmt: skip
    return {"state": "left", "page": text}


def leave_to_model(box: Path) -> dict:
    """Line 1 at a model's door: the sealed scope's one file, handed over as
    text. The model names no path. The runtime keeps a copy, to hold the
    model's answer to it."""
    got = sealed_page(box)
    if got["state"] == "left":
        (state(box) / "last-page.md").write_text(got["page"])
    return got


def context(box: Path, question: str) -> dict:
    """What a model may be given with a prompt: the sealed page, when the
    kernel says these words are sealed by a scope the runtime proposed and the
    page holds exactly that scope; else only whether the files hold it. A page
    sealed for another question stays out."""
    got = read(box, question)
    if got["state"] == "sealed":
        f = state(box) / "scopes.json"
        scope = (json.loads(f.read_text()) if f.exists() else {}).get(got.get("by"))
        page = sealed_page(box)
        if scope and page["state"] == "left":
            held = sorted(b["text"].strip() for b in boxes_of(page["page"]))
            if held == scope:
                (state(box) / "last-page.md").write_text(page["page"])
                return page
        return {"state": "populated"}
    return {"state": got["state"]}


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
    out = withhold(box, [s["text"] for s in served]) if served else []
    by_text = {w.strip(): s["id"] for w, s in zip(out, served)}
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
        "sent": lambda box, arg: sent_log(box),
        "pin": lambda box, arg: pin_sent(box, Path(str(arg))),
        "check": lambda box, arg: check_sent(box, Path(str(arg))),
    },
    "model": {
        # read is open, but its passages would leave to the model: it gets the
        # state alone, never a passage, a place or a count
        "read": lambda box, arg: {"state": read(box, str(arg))["state"]},
        "propose": lambda box, arg: propose(box),
        "leave": lambda box, arg: leave_to_model(box),
        "answer": lambda box, arg: answer(box, str(arg)),
        "context": lambda box, arg: context(box, str(arg)),
    },
}


def call(box: Path, verb: str, arg=None, door: str = "") -> dict:
    """What every door calls: one verb, decided here, by who the door faces.
    Whatever reaches a model, and every file that leaves, is written down."""
    faces = FACES.get(door, "model")
    verbs = VERBS[faces]
    if verb not in verbs:
        return {"state": "refused", "why": f"no verb {verb!r}; one of {sorted(verbs)}"}
    got = verbs[verb](box, arg)
    if got.get("state") != "refused" and (faces == "model" or verb == "leave"):
        sent(box, door or "unknown", verb, got)
    return got
