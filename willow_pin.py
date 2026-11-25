"""willow_pin.py: the Willow this was built on, held to its pin. Python 3.9+.

    python willow_pin.py check [--willow DIR]
    python willow_pin.py repin [--willow DIR] [--at COMMIT] [--add NAME ...] [--drop NAME ...]
    python willow_pin.py follow [COMMIT] [-- CHECK ARGS ...]

The runtime runs Willow's kernel and a few of its add-ons by their command
line. willow.pin.json pins them: Willow's commit, the add-ons by name, and
every file of what runs, by SHA-256. `problems` names each file that is
missing, different, or new in a pinned add-on; the runtime refuses to run on
a Willow with any. Nothing else in Willow matters to the pin.

WILLOW names where Willow's git is (else a sibling folder named Willow): any
checkout of it, on any branch. The runtime never runs that checkout. It runs
a copy of the pinned commit, made from git by `pinned_copy` the first time
it is wanted and kept in Willow's git folder, named by the commit (so every
checkout of that git shares them, and Die-Namic's too), so whatever the
checkout is switched to, the runtime is on the commit its pin names. A
WILLOW that isn't a git checkout is run where it is, held to the pin.

`repin` is the one way to move the pin, done on purpose: it pins the
checkout's commit, or with --at any commit its git has (a branch, a tag,
origin/main), read from git, never from the files checked out. What is pinned is kernel.py and, for each add-on the pin
names, every file Willow's git holds in its folder but its tests, so an
add-on's new file comes in by itself. `--add` pins another add-on (from
adapters/stdlib, or adapters/deps when it needs a package), `--drop` lets one
go. It refuses a checkout whose pinned files have changes not committed (so
the pin always names bytes a commit holds), and an add-on the commit doesn't
have; then it says what moved.

`follow` is the whole move in one: it fetches, repins at COMMIT (origin/main
when none is named), makes its copy, and runs this repo's check on it (python check.py, with
whatever follows a -- on its command line). Only
if the check passes does it commit willow.pin.json, on the branch you're on;
if it fails, the pin is put back as it was and nothing is committed. It
never pushes.

Willow is never imported or changed here: its files are only read and hashed.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
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


def source() -> Path:
    """Where Willow's git is: WILLOW, else a sibling folder named Willow."""
    return Path(os.environ.get("WILLOW", HERE.parent / "Willow"))


def copies(src: Path) -> Path | None:
    """Where the pinned copies of SRC's commits are kept, one folder per
    commit: in its git's own folder, where every checkout of that git finds
    them; None when SRC isn't a git checkout. Read without running git, as
    every hook asks it."""
    dot = src / ".git"
    try:
        if dot.is_file():  # a worktree: its git folder, then the one they share
            wt = Path(dot.read_text().split("gitdir:", 1)[1].strip())
            wt = wt if wt.is_absolute() else (src / wt)
            common = (
                (wt / "commondir").read_text().strip()
                if (wt / "commondir").is_file()
                else "."
            )
            dot = (wt / common).resolve()
    except (OSError, IndexError):
        return None
    return dot / "willow-pinned" if (dot / "objects").is_dir() else None


#: written last into a copy, so a copy cut short is never taken for one
DONE = ".willow-pinned"


def pinned_copy(src: Path, commit: str) -> Path | None:
    """Willow at COMMIT, made from SRC's git once and kept; None when SRC
    isn't a git checkout or its git doesn't have the commit."""
    home = copies(src)
    if home is None:
        return None
    at = home / commit
    if (at / DONE).is_file():
        return at
    tree = git(src, "rev-parse", "--verify", "--quiet", commit + "^{commit}")
    if tree.returncode != 0:
        return None
    at.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=commit[:12] + ".", dir=at.parent))
    try:
        tar = work / "tree.tar"
        got = git(src, "archive", "--format=tar", "-o", str(tar), commit)
        if got.returncode != 0:
            return None
        with tarfile.open(tar) as t:
            # git's own archive of Willow; "data" where this Python has it
            safe = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
            t.extractall(work / "tree", **safe)
        (work / "tree" / DONE).write_text(commit + "\n")
        try:
            (work / "tree").rename(at)
        except OSError:  # another made it first: theirs is the same commit
            if not (at / DONE).is_file():
                raise
        return at
    finally:
        shutil.rmtree(work, ignore_errors=True)


def default_root(pin: Path = PIN) -> Path:
    """The Willow the runtime runs: the copy of the pinned commit, when
    WILLOW is a git checkout that has it; else WILLOW itself, which the pin
    then holds file by file."""
    src = source()
    try:
        commit = load(pin)["commit"]
    except (OSError, ValueError, KeyError):
        return src
    return pinned_copy(src, commit) or src


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


def repin(root: Path, pin: Path = PIN, add: list[str] = (), drop: list[str] = (), at: str = "") -> tuple[int, str]:  # fmt: skip
    """(exit, what was said). Pins the checkout's commit, or AT, and its
    files' bytes as the commit holds them."""
    if git(root, "rev-parse", "--git-dir").returncode != 0:
        return 2, f"refused: {root} isn't a Willow git checkout"
    head = git(root, "rev-parse", "--verify", "--quiet", (at or "HEAD") + "^{commit}")
    if head.returncode != 0:
        return 2, f"refused: Willow's git at {root} has no commit {at}"
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
    if dirty and not at:  # AT is read from git alone: the checkout is no matter
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


#: this repo's check, run by `follow` on the Willow it pins
CHECK = [sys.executable, "check.py"]


def follow(rev: str = "", pin: Path = PIN, check: list[str] = ()) -> tuple[int, str]:  # fmt: skip
    """(exit, what was said). Repin at REV (origin/main when none is
    named), run CHECK with CHECK's own arguments after it, and commit the
    pin only if the check passes."""
    src = source()
    git(src, "fetch", "-q", "origin")  # offline, what git has is followed
    was = pin.read_bytes()
    code, said = repin(src, pin, at=rev or "origin/main")
    if code:
        return code, said
    commit = load(pin)["commit"]
    if was == pin.read_bytes():
        return 0, f"the pin is on Willow {commit[:12]} already: nothing moved"
    got = pinned_copy(src, commit)
    off = problems(got, pin) if got else ["no copy made"]
    ran = None
    if not off:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        ran = subprocess.run([*CHECK, *check], cwd=HERE, env={**env, "WILLOW": str(src)},
                             capture_output=True, text=True, check=False)  # fmt: skip
    if off or ran.returncode != 0:
        pin.write_bytes(was)
        why = "; ".join(off) if off else (ran.stdout + ran.stderr).strip()[-2000:]
        return 1, f"{said}\nthe check didn't pass, so the pin is back as it was:\n{why}"
    msg = f"pin: Willow {commit[:12]}\n\n" + "\n".join(said.splitlines()[1:])
    done = subprocess.run(
        ["git", "-C", str(HERE), "commit", "-q", "-m", msg.strip() + "\n", "--", pin.name],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    if done.returncode != 0:
        return (
            1,
            f"{said}\nthe check passed, but the commit didn't: {done.stderr.strip()}",
        )
    return 0, f"{said}\nthe check passed; committed, not pushed"


USAGE = "usage: willow_pin.py check [--willow DIR] | repin [--willow DIR] [--at COMMIT] [--add NAME ...] [--drop NAME ...] | follow [COMMIT] [-- CHECK ARGS]"  # fmt: skip


def main(argv: list[str]) -> int:
    verb, it = (argv[0] if argv else ""), iter(argv[1:])
    if verb == "follow":
        rest = argv[1:]
        more = rest[rest.index("--") + 1 :] if "--" in rest else []
        rest = rest[: rest.index("--")] if "--" in rest else rest
        if len(rest) > 1 or any(not a or a.startswith("-") for a in rest):
            print(USAGE, file=sys.stderr)
            return 2
        code, said = follow(rest[0] if rest else "", check=more)
        print(said, file=sys.stderr if code else sys.stdout)
        return code
    root, at, add, drop, bad = None, "", [], [], verb not in ("check", "repin")
    for a in it:
        got = next(it, "")
        if a == "--willow" and got and root is None:
            root = Path(got)
        elif a == "--at" and got and not at and verb == "repin":
            at = got
        elif a in ("--add", "--drop") and got and verb == "repin":
            (add if a == "--add" else drop).append(got)
        else:
            bad = True
    if bad:
        print(USAGE, file=sys.stderr)
        return 2
    if verb == "repin":
        code, said = repin(root or source(), add=add, drop=drop, at=at)
        print(said, file=sys.stderr if code else sys.stdout)
        return code
    root = root or default_root()
    off = problems(root)
    if off:
        print(f"{root} isn't the pinned Willow:", *off, sep="\n  ")
        return 1
    print(f"{root} is the pinned Willow, {load()['commit'][:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
