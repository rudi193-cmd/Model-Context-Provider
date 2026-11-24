"""willow_pin.py: the Willow this was built on, held to its pin. Python 3.9+.

    python willow_pin.py check [--willow DIR]
    python willow_pin.py repin [--willow DIR] [--add NAME ...] [--drop NAME ...]

The runtime runs Willow's kernel and a few of its add-ons where they live, in
a Willow checkout. willow.pin.json pins them: Willow's commit, the add-ons by
name, and every file of what runs, by SHA-256. `problems` names each file
that is missing, different, or new in a pinned add-on; the runtime refuses to
run on a Willow with any. Nothing else in Willow matters to the pin.

`repin` is the one way to move the pin, done on purpose: it pins the
checkout's commit. What is pinned is kernel.py and, for each add-on the pin
names, every file Willow's git holds in its folder but its tests, so an
add-on's new file comes in by itself. `--add` pins another add-on (from
adapters/stdlib, or adapters/deps when it needs a package), `--drop` lets one
go. It refuses a checkout whose pinned files have changes not committed (so
the pin always names bytes a commit holds), and an add-on the commit doesn't
have; then it says what moved.

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

#: where an add-on lives in Willow: adapters/stdlib, or adapters/deps for one
#: that needs a package installed (Kartikeya runs a sealed job in a Python
#: that has it); the pin names them as "add_ons" and "deps"
KINDS = (("stdlib", "add_ons"), ("deps", "deps"))
KERNEL = "kernel.py"


def pinned(name: str) -> bool:
    """A test, or what pytest reads beside them, is never pinned."""
    return not name.startswith("test_") and name != "conftest.py"


def default_root() -> Path:
    """Where the runtime looks: WILLOW, else a sibling folder named Willow."""
    return Path(os.environ.get("WILLOW", HERE.parent / "Willow"))


def files(root: Path, pin: Path = PIN) -> list[str]:
    """The files the pin covers in this checkout, as paths inside it: the
    kernel, and every file of each add-on the pin names but its tests."""
    doc = load(pin)
    out = [KERNEL] if (root / KERNEL).is_file() else []
    for kind, key in KINDS:
        for name in doc.get(key, []):
            d = root.joinpath("adapters", kind, name)
            if d.is_dir():
                out += [
                    p.relative_to(root).as_posix()
                    for p in sorted(d.rglob("*"))
                    if p.is_file() and "__pycache__" not in p.parts and pinned(p.name)
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
    out += [f"not pinned: {rel}" for rel in files(root, pin) if rel not in want]
    return out


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def of_add_on(tracked: list[str], name: str) -> tuple[str, list[str]]:
    """(the pin's key for it, its files as the pin holds them) for an add-on
    in the commit's tree; ("", []) when the commit has none by that name."""
    for kind, key in KINDS:
        top = "adapters/%s/%s/" % (kind, name)  # noqa: UP031
        got = [f for f in tracked if f.startswith(top)]
        if got:
            return key, [f for f in got if pinned(f.rsplit("/", 1)[-1])]
    return "", []


def in_order(old: list[str], new: list[str]) -> list[str]:
    """NEW in the pin's own order: what it held stays where it was, and a new
    file goes after the last one of its folder, or at the end."""
    keep = [f for f in old if f in new]
    for f in (f for f in new if f not in old):
        folder = f.rsplit("/", 1)[0] + "/"
        at = max((i for i, g in enumerate(keep) if g.startswith(folder)), default=len(keep) - 1)  # fmt: skip
        keep.insert(at + 1, f)
    return keep


def repin(root: Path, pin: Path = PIN, add: list[str] = (), drop: list[str] = ()) -> tuple[int, str]:  # fmt: skip
    """(exit, what was said). Pins the checkout's commit and its files' bytes."""
    head = git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return 2, f"refused: {root} isn't a Willow git checkout"
    commit = head.stdout.strip()
    tracked = git(root, "ls-tree", "-r", "--name-only", commit).stdout.split()
    if KERNEL not in tracked:
        return 2, f"refused: no {KERNEL} in Willow {commit[:12]}"
    try:
        old = load(pin)
    except (OSError, ValueError):
        return 2, f"refused: no pin at {pin} to move"
    names = {key: [n for n in old.get(key, []) if n not in drop] for _, key in KINDS}
    gone = [n for n in drop if not any(n in old.get(key, []) for _, key in KINDS)]
    if gone:
        return 2, f"refused: {gone[0]} isn't an add-on the pin names"
    for n in add:
        key = of_add_on(tracked, n)[0] or "add_ons"  # one it lacks is refused below
        if n not in names[key]:
            later = next(
                (i for i, m in enumerate(names[key]) if m > n), len(names[key])
            )
            names[key].insert(later, n)
    have, folders = [KERNEL], [KERNEL]
    for kind, key in KINDS:
        for n in names[key]:
            got = of_add_on(tracked, n)[1]
            if not got:
                return 2, f"refused: Willow {commit[:12]} has no add-on {n}"
            have += got
            folders.append("adapters/%s/%s" % (kind, n))  # noqa: UP031
    # what isn't committed in a pinned folder, new files too, its tests aside
    dirty = [
        line
        for line in git(
            root, "status", "--porcelain", "--untracked-files=all", "--", *folders
        ).stdout.splitlines()  # fmt: skip
        if pinned(line[3:].rsplit("/", 1)[-1])
    ]
    if dirty:
        return 2, "refused: changes not committed in pinned files:\n" + "\n".join(dirty)
    new = {}
    for rel in in_order(list(old.get("files", {})), have):
        blob = subprocess.run(["git", "-C", str(root), "show", commit + ":" + rel], capture_output=True, check=False)  # fmt: skip
        new[rel] = hashlib.sha256(blob.stdout).hexdigest()
    doc = {**old, "commit": commit, **names, "files": new}
    pin.write_text(json.dumps(doc, indent=2) + "\n")
    was = old.get("files", {})
    moved = sorted(
        [f"changed: {r}" for r in new if r in was and was[r] != new[r]]
        + [f"added: {r}" for r in new if r not in was]
        + [f"gone: {r}" for r in was if r not in new]
    )
    said = f"pinned Willow {commit[:12]}, {len(new)} files"
    return 0, "\n".join([said, *moved])


USAGE = "usage: willow_pin.py check [--willow DIR] | repin [--willow DIR] [--add NAME ...] [--drop NAME ...]"  # fmt: skip


def main(argv: list[str]) -> int:
    verb, it = (argv[0] if argv else ""), iter(argv[1:])
    root, add, drop, bad = None, [], [], verb not in ("check", "repin")
    for a in it:
        got = next(it, "")
        if a == "--willow" and got and root is None:
            root = Path(got)
        elif a in ("--add", "--drop") and got and verb == "repin":
            (add if a == "--add" else drop).append(got)
        else:
            bad = True
    if bad:
        print(USAGE, file=sys.stderr)
        return 2
    root = root or default_root()
    if verb == "repin":
        code, said = repin(root, add=add, drop=drop)
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
