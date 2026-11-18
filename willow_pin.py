"""willow_pin.py: the Willow this was built on, held to its pin. Python 3.9+.

    python willow_pin.py check [--willow DIR]
    python willow_pin.py repin [--willow DIR]

The runtime runs Willow's kernel and a few of its add-ons where they live, in
a Willow checkout. willow.pin.json pins them: Willow's commit, and every file
of what runs, by SHA-256. `problems` names each file that is missing,
different, or new in a pinned add-on; the runtime refuses to run on a Willow
with any. Nothing else in Willow matters to the pin.

`repin` is the one way to move the pin, done on purpose: it pins the
checkout's commit, refuses one whose pinned files have changes not committed
(so the pin always names bytes a commit holds), and says what moved.

Willow is never imported or changed here: its files are only read and hashed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIN = HERE / "willow.pin.json"

#: what the runtime runs, and what each of those loads from beside it
ADD_ONS = (
    "approved-only",
    "backup",
    "batch-ask",  # index-cache and claude-code load its scan
    "box-health",
    "calendar",  # an importer: loads only the kernel
    "claude-code",
    "coming-up",  # loads pieces
    "digest",  # loads coming-up and stale-answers
    "hook-errors",
    "hook-feedback",
    "hook-guard",
    "hook-handoff",
    "hook-leaks",  # loads privacy
    "hook-read-first",
    "hook-shell",
    "index-cache",
    "local-model",
    "notes",  # an importer: loads only the kernel
    "on-this-day",
    "openai-compatible",  # local-model loads it
    "people",  # loads only the kernel
    "rss-out",  # loads only the kernel
    "pieces",  # coming-up loads it from beside it
    "privacy",
    "sentence-check",
    "session-seal",
    "share",  # kart loads it: a job that came in a package, a result sent back
    "stale-answers",  # digest loads it; it loads pieces
    "timeline",  # loads only the kernel
    "todo",  # batch-ask's scan loads it
)

#: add-ons that need a package installed, under adapters/deps: Kartikeya runs
#: a sealed job in its sandbox, in a Python that has it
DEPS = ("kart",)


def default_root() -> Path:
    """Where the runtime looks: WILLOW, else a sibling folder named Willow."""
    return Path(os.environ.get("WILLOW", HERE.parent / "Willow"))


def files(root: Path) -> list[str]:
    """The files the pin covers in this checkout, as paths inside it: the
    kernel, and every file of each add-on but its tests, those that need a
    package (adapters/deps) with the rest."""
    out = ["kernel.py"] if (root / "kernel.py").is_file() else []
    dirs = [root / "adapters" / "stdlib" / name for name in ADD_ONS]
    for d in dirs + [root / "adapters" / "deps" / name for name in DEPS]:
        if d.is_dir():
            out += [
                p.relative_to(root).as_posix()
                for p in sorted(d.rglob("*"))
                if p.is_file()
                and "__pycache__" not in p.parts
                and not p.name.startswith("test_")
            ]
    return out


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(pin: Path = PIN) -> dict:
    return json.loads(pin.read_text())


def problems(root: Path, pin: Path = PIN) -> list[str]:
    """Each way this checkout isn't the pinned Willow; none when it is."""
    try:
        want = load(pin)["files"]
    except (OSError, ValueError, KeyError):
        return [f"no pin at {pin}"]
    out = []
    for rel, h in sorted(want.items()):
        p = root / rel
        if not p.is_file():
            out.append(f"missing: {rel}")
        elif sha(p) != h:
            out.append(f"differs: {rel}")
    out += [f"not pinned: {rel}" for rel in files(root) if rel not in want]
    return out


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def repin(root: Path, pin: Path = PIN) -> tuple[int, str]:
    """(exit, what was said). Pins the checkout's commit and its files' bytes."""
    head = git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return 2, f"refused: {root} isn't a Willow git checkout"
    have = files(root)
    if "kernel.py" not in have:
        return 2, f"refused: no kernel.py in {root}"
    dirty = git(root, "status", "--porcelain", "--", *have).stdout.strip()
    if dirty:
        return 2, "refused: changes not committed in pinned files:\n" + dirty
    try:
        old = load(pin).get("files", {})
    except (OSError, ValueError):
        old = {}
    new = {rel: sha(root / rel) for rel in have}
    doc = {
        "_what": "The Willow this runtime was built on: its commit, and every "
        "file of what runs, by SHA-256. willow_pin.py refuses a checkout whose "
        "files differ; repin is the one way to move it.",
        "willow": "https://github.com/willow-memory/Willow",
        "commit": head.stdout.strip(),
        "add_ons": list(ADD_ONS),
        "deps": list(DEPS),
        "files": new,
    }
    pin.write_text(json.dumps(doc, indent=2) + "\n")
    moved = sorted(
        [f"changed: {r}" for r in new if r in old and old[r] != new[r]]
        + [f"added: {r}" for r in new if r not in old]
        + [f"gone: {r}" for r in old if r not in new]
    )
    said = f"pinned Willow {doc['commit'][:12]}, {len(new)} files"
    return 0, "\n".join([said, *moved])


def main(argv: list[str]) -> int:
    verb, rest = (argv[0], argv[1:]) if argv else ("", [])
    if verb not in ("check", "repin") or not (
        rest == [] or (len(rest) == 2 and rest[0] == "--willow" and rest[1])
    ):
        print("usage: willow_pin.py check|repin [--willow DIR]", file=sys.stderr)
        return 2
    root = Path(rest[1]) if rest else default_root()
    if argv[0] == "repin":
        code, said = repin(root)
        print(said, file=sys.stderr if code else sys.stdout)
        return code
    off = problems(root)
    if off:
        print(f"{root} isn't the pinned Willow:", *off, sep="\n  ")
        return 1
    print(f"{root} is the pinned Willow, {load()['commit'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
