"""check.py: the check a change is held to, on this machine. Python 3.9+.

    python check.py [--python PY ...]
    python check.py --commit REV [--python PY ...]
    python check.py hook [--python PY ...] [--write]

It asks three things, and says pass or fail for each:

    Willow      the checkout WILLOW names is the one willow.pin.json pins
    lint        ruff check, and ruff format --check
    tests       the tests, once under each Python named (--python, as often
                as wanted; with none, the Python running this)

With no --commit it checks the folder as it is. With --commit it checks
that commit and nothing else: its files are unpacked somewhere else and the
checks run there, so a change not yet committed can't pass for it. A commit
that passed is remembered by its tree, and isn't checked twice.

`hook` is how main is held here, with no server asked: it prints a git
hook (reference-transaction) that runs `--commit` on whatever is about to
become main, by a commit, a merge, a fast-forward or a pull, and refuses it
when the check fails. `--write` saves it in this checkout's hooks folder,
and never over a file that differs.

Exit codes: 0 passed (or the hook printed or written); 1 failed; 2 a bad
command line, or a hook that is there already and differs.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRANCH = "refs/heads/main"
MARK = "# model-context-provider: main is held here (check.py hook)"


def willow_root() -> Path:
    """Where Willow is: WILLOW, else a sibling folder named Willow."""
    return Path(os.environ.get("WILLOW", HERE.parent / "Willow")).resolve()


def clean_env(willow: Path) -> dict:
    """The environment a check runs in: WILLOW named, and nothing of git's,
    since a hook's GIT_DIR would point every git a test runs at this repo."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["WILLOW"] = str(willow)
    return env


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(HERE), *args], capture_output=True, text=True,
        check=False, env=clean_env(willow_root()),
    )  # fmt: skip


def ruff_of(pythons: list[str]) -> list[str] | None:
    """How to run ruff: as a module of the first Python that has it, else
    the one on the path."""
    for py in pythons:
        probe = subprocess.run([py, "-m", "ruff", "--version"],
                               capture_output=True, check=False)  # fmt: skip
        if probe.returncode == 0:
            return [py, "-m", "ruff"]
    found = shutil.which("ruff")
    return [found] if found else None


def steps(pythons: list[str]) -> list[tuple[str, list[str] | None]]:
    """What is asked, in order: (what it is called, the command; None when
    there is nothing on this machine to run it with)."""
    ruff = ruff_of(pythons)
    out: list[tuple[str, list[str] | None]] = [
        ("Willow is the pinned one", [pythons[0], "willow_pin.py", "check"]),
        ("lint", [*ruff, "check", "."] if ruff else None),
        ("format", [*ruff, "format", "--check", "."] if ruff else None),
    ]
    for py in pythons:
        out.append((f"tests, under {py}", [py, "-m", "pytest", "-q"]))
    return out


def run(root: Path, pythons: list[str], say=print) -> bool:
    """Every step, in the folder at root. Each is said as it ends; a failed
    one says its last lines. True when all passed."""
    env, passed = clean_env(willow_root()), True
    for what, argv in steps(pythons):
        if argv is None:
            say(f"  NO   {what}: no ruff on this machine (pip install ruff==0.16.7)")
            passed = False
            continue
        try:
            got = subprocess.run(argv, cwd=root, env=env, capture_output=True,
                                 text=True, check=False)  # fmt: skip
        except OSError as why:
            say(f"  NO   {what}: {argv[0]} can't be run ({type(why).__name__})")
            passed = False
            continue
        if got.returncode == 0:
            say(f"  ok   {what}")
            continue
        passed = False
        say(f"  NO   {what}")
        for line in (got.stdout + got.stderr).strip().splitlines()[-15:]:
            say(f"       {line}")
    return passed


def remembered() -> Path:
    """The trees that passed, kept in this checkout's git folder."""
    d = git("rev-parse", "--git-common-dir").stdout.strip() or ".git"
    return (HERE / d).resolve() / "model-context-provider-checked"


def key_of(tree: str, pythons: list[str]) -> str:
    """One passed check: this tree, this Willow pin's bytes being the tree's
    own, under these Pythons."""
    return hashlib.sha256("\n".join([tree, *pythons]).encode()).hexdigest()


def check_commit(rev: str, pythons: list[str], say=print) -> int:
    """That commit's files, unpacked beside nothing of this folder's, and
    checked there."""
    tree = git("rev-parse", "--verify", "--quiet", f"{rev}^{{tree}}").stdout.strip()
    if not tree:
        say(f"check: {rev} isn't a commit here")
        return 2
    key, book = key_of(tree, pythons), remembered()
    seen = book.read_text().split() if book.is_file() else []
    # Willow's own state isn't in the tree, so its pin is asked every time
    if key in seen:
        ok = run_one(HERE, tree, pythons, say, only_pin=True)
        say(f"check: {rev[:12]} passed before (tree {tree[:12]})")
        return 0 if ok else 1
    ok = run_one(HERE, tree, pythons, say)
    if ok:
        with book.open("a") as f:
            f.write(key + "\n")
    say(f"check: {rev[:12]} {'passed' if ok else 'FAILED'} (tree {tree[:12]})")
    return 0 if ok else 1


def run_one(repo: Path, tree: str, pythons: list[str], say, only_pin=False) -> bool:
    with tempfile.TemporaryDirectory(prefix="model-context-provider-check-") as d:
        tar = Path(d) / "tree.tar"
        got = subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", "-o", str(tar), tree],
            capture_output=True, text=True, check=False, env=clean_env(willow_root()),
        )  # fmt: skip
        if got.returncode != 0:
            say(f"  NO   the commit's files couldn't be read: {got.stderr.strip()}")
            return False
        root = Path(d) / "tree"
        with tarfile.open(tar) as t:
            t.extractall(root)  # noqa: S202 - git's own archive of this repo
        if only_pin:
            env = clean_env(willow_root())
            got = subprocess.run([pythons[0], "willow_pin.py", "check"], cwd=root,
                                 env=env, capture_output=True, text=True, check=False)  # fmt: skip
            if got.returncode != 0:
                say("  NO   Willow is the pinned one")
                say(f"       {(got.stdout + got.stderr).strip()[-400:]}")
            return got.returncode == 0
        return run(root, pythons, say)


def hook_text(pythons: list[str]) -> str:
    """The reference-transaction hook: when main is about to move to a
    commit, check that commit; refuse the move if the check fails. Every
    other ref, and main being deleted, pass straight through."""
    cmd = shlex.join(
        [sys.executable, str(HERE / "check.py"), "--commit", "COMMIT",
         *[a for py in pythons for a in ("--python", py)]]
    ).replace("COMMIT", '"$new"')  # fmt: skip
    return "\n".join([
        "#!/bin/sh",
        MARK,
        "# Git runs this as refs are about to change. Nothing here asks a server.",
        '[ "$1" = prepared ] || exit 0',
        "while read -r old new ref; do",
        f'  [ "$ref" = {BRANCH} ] || continue',
        '  case "$new" in *[!0]*) ;; *) continue ;; esac',
        f"  WILLOW={shlex.quote(str(willow_root()))} {cmd} </dev/null >&2 || exit 1",
        "done",
        "exit 0",
        "",
    ])  # fmt: skip


def hook_path() -> Path:
    d = git("rev-parse", "--git-path", "hooks").stdout.strip() or ".git/hooks"
    return (HERE / d).resolve() / "reference-transaction"


def write_hook(pythons: list[str], say=print) -> int:
    text, at = hook_text(pythons), hook_path()
    if at.exists() and at.read_text() != text:
        if MARK not in at.read_text():
            say(f"refused: {at} is there already and isn't this hook; never written over")  # fmt: skip
            return 2
    at.parent.mkdir(parents=True, exist_ok=True)
    at.write_text(text)
    at.chmod(0o755)
    say(f"wrote {at}")
    say(f"main is now held here: a commit that fails the check can't become {BRANCH}.")
    return 0


def parse(argv: list[str]) -> tuple[str, list[str], str | None, bool] | None:
    """(verb, pythons, commit, write); None for a bad command line."""
    verb, rest = ("hook", argv[1:]) if argv[:1] == ["hook"] else ("check", argv)
    pythons, commit, write, it = [], None, False, iter(rest)
    for a in it:
        if a == "--python":
            py = next(it, "")
            if not py:
                return None
            pythons.append(py)
        elif a == "--commit" and verb == "check":
            commit = next(it, "") or None
            if commit is None:
                return None
        elif a == "--write" and verb == "hook":
            write = True
        else:
            return None
    return verb, pythons or [sys.executable], commit, write


def main(argv: list[str]) -> int:
    parsed = parse(argv)
    if parsed is None:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    verb, pythons, commit, write = parsed
    if verb == "hook":
        if write:
            return write_hook(pythons)
        print(hook_text(pythons), end="")
        print(
            f"\n# It goes in {hook_path()} (run again with --write).", file=sys.stderr
        )
        return 0
    if commit:
        return check_commit(commit, pythons)
    ok = run(HERE, pythons)
    print(f"check: this folder {'passed' if ok else 'FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
