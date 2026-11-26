"""check.py: the check a change is held to, on this machine. Python 3.9+.

    python check.py [--python PY ...] [--all] [--jobs N]
    python check.py --commit REV [--python PY ...] [--all] [--jobs N]
    python check.py hook [--python PY ...] [--write]

It asks three things, and says pass or fail for each:

    Willow      the checkout WILLOW names is the one willow.pin.json pins
    lint        ruff check, and ruff format --check
    tests       the tests, once under each Python named (--python, as often
                as wanted; with none, the Python running this)

The tests run in parts, as many at once as this machine has cores (--jobs N
for another number; 1 is one run, as before). Willow's test-shards cuts the
parts by how long each test file took last time, so they end about
together; with no Willow add-on to ask, it is one run.

A pass is remembered by everything the tests can read: every file here but
the words of the docs (a `.md` counts by its name alone). While none of
that has changed, the tests aren't run again: only the one that holds
FILES.md to the folder is, since the docs are all that moved. --all runs
everything regardless. The pin and the lint are asked every time.

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
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRANCH = "refs/heads/main"
MARK = "# model-context-provider: main is held here (check.py hook)"
TESTS = "tests, under "
#: said on the command line: how many parts at once (0: one a core), and
#: whether to run every test though nothing they read has changed
JOBS, EVERYTHING = 0, False
#: Willow's add-on that cuts a suite into parts by each file's past time
SHARDS = "adapters/stdlib/test-shards/shards.py"
#: the tests that read the docs: run even when nothing else has changed
DOCS_TESTS = ["tests/test_files.py"]
#: never an input of a test: git's own, caches, and a machine's own settings
NOT_READ = {".git", ".venv", ".claude", "__pycache__", ".pytest_cache",
            ".ruff_cache", "uv.lock"}  # fmt: skip


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


def inputs_key(root: Path, pythons: list[str]) -> str:
    """Everything the tests can read, as one fingerprint: each file's path
    and bytes, but for a doc (.md) its path alone, since no test reads a
    doc's words but the ones in DOCS_TESTS; and the Pythons they run under."""
    h = hashlib.sha256("\n".join(pythons).encode())
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if NOT_READ & set(rel.parts) or not p.is_file() or p.is_symlink():
            continue
        h.update(b"\0" + rel.as_posix().encode() + b"\0")
        if p.suffix != ".md":
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def kept() -> Path | None:
    """Where passes and past times are kept: this checkout's git folder, or
    nowhere when this isn't a checkout."""
    d = remembered().parent
    return d if d.is_dir() else None


def parts_of(py: str, root: Path, jobs: int, env: dict) -> list[list[str]] | None:
    """The test files in `jobs` parts that should end about together, as
    Willow's test-shards cuts them by their past times; None when there is
    nothing to ask, or it can't say (then the tests are one run)."""
    shards = willow_root() / SHARDS
    if jobs < 2 or not shards.is_file():
        return None
    past = (
        sorted((kept() / "model-context-provider-times").glob("*.xml"))
        if kept()
        else []
    )
    out = []
    for k in range(1, jobs + 1):
        got = subprocess.run(
            [py, str(shards), *[a for p in past for a in ("--past", str(p))],
             "--shard", f"{k}/{jobs}", "tests"],
            cwd=root, env=env, capture_output=True, text=True, check=False,
        )  # fmt: skip
        if got.returncode != 0:
            return None
        out.append([ln for ln in got.stdout.splitlines() if ln.strip()])
    return [p for p in out if p]


#: how long one part of the tests may run before it is stopped: the whole
#: of a part takes under a minute here, so a part this long has hung, and a
#: check that waits on it never ends (seen 2026-11-26: a test that read a
#: line that never came)
PART_SECONDS = 600
#: how long one test may run before pytest prints where every thread is,
#: so a part that is stopped says where it was
STACK_SECONDS = 120


def run_tests(root: Path, pythons: list[str], say, jobs: int, everything: bool) -> bool:
    """The tests under each Python: in parts, at once; or, when nothing they
    read has changed since they passed, only the ones that read the docs."""
    env, book = clean_env(willow_root()), kept()
    key = inputs_key(root, pythons)
    seen = book / "model-context-provider-inputs" if book else None
    quiet = ["-m", "pytest", "-q", "-p", "no:cacheprovider",
             "-o", f"faulthandler_timeout={STACK_SECONDS}"]  # fmt: skip
    if not everything and seen and seen.is_file() and key in seen.read_text().split():
        got = subprocess.run([pythons[0], *quiet, *DOCS_TESTS], cwd=root, env=env,
                             capture_output=True, text=True, check=False)  # fmt: skip
        if got.returncode == 0:
            say("  ok   tests: nothing they read has changed since they passed; "
                "the file list was held again (--all runs every test)")  # fmt: skip
            return True
        say("  NO   tests: the file list")
        for line in (got.stdout + got.stderr).strip().splitlines()[-15:]:
            say(f"       {line}")
        return False
    began, passed = time.monotonic(), True
    with tempfile.TemporaryDirectory(prefix="model-context-provider-parts-") as d:
        work = []  # (python, its number, part number, the files or [] for all)
        for i, py in enumerate(pythons):
            parts = parts_of(py, root, jobs, env)
            work += [(py, i, k, files) for k, files in enumerate(parts or [[]])]

        def one(job):
            py, i, k, files = job
            at = Path(d) / f"{i}-{k}"
            try:
                got = subprocess.run(
                    [py, *quiet, f"--basetemp={at}", f"--junitxml={at}.xml", *files],
                    cwd=root, env=env, capture_output=True, text=True, check=False,
                    timeout=PART_SECONDS,
                )  # fmt: skip
            except OSError as why:
                return job, 1, f"{py} can't be run ({type(why).__name__})"
            except subprocess.TimeoutExpired as late:
                said = "".join(
                    x.decode(errors="replace") if isinstance(x, bytes) else x
                    for x in (late.stdout, late.stderr) if x
                )  # fmt: skip
                # where it was: the dump's lines in this folder's own files,
                # last, so they are among the lines a failed part shows
                where = [ln.strip() for ln in said.splitlines()
                         if 'File "' in ln and str(root) in ln][:5]  # fmt: skip
                return job, 1, "\n".join([said, *where, f"stopped after {PART_SECONDS} s, "
                                           f"still running: {' '.join(files) or 'every test'}"])  # fmt: skip
            return job, got.returncode, got.stdout + got.stderr

        with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
            done = list(pool.map(one, work))
        for i, py in enumerate(pythons):
            mine = [x for x in done if x[0][1] == i]
            failed = [x for x in mine if x[1] != 0]
            if not failed:
                say(f"  ok   {TESTS}{py}" + (f" ({len(mine)} parts)" if len(mine) > 1 else ""))  # fmt: skip
                continue
            passed = False
            say(f"  NO   {TESTS}{py}")
            for _, _, text in failed:
                for line in text.strip().splitlines()[-15:]:
                    say(f"       {line}")
        if passed and book:
            with seen.open("a") as f:
                f.write(key + "\n")
            keep_times(Path(d), book / "model-context-provider-times")
    if len(work) > len(pythons):
        say(f"       the tests took {time.monotonic() - began:.0f} s, {jobs} at once")
    return passed


def keep_times(run: Path, to: Path) -> None:
    """Each test file's seconds in the run that just passed, for the next
    cut: one small file pytest's own way, so Willow's test-shards reads it.
    Only the first Python's parts: one time a test is enough."""
    rows = []
    for f in sorted(run.glob("0-*.xml")):
        try:
            rows += [(c.get("classname", ""), c.get("name", ""), c.get("time", "0"))
                     for c in ET.parse(f).getroot().iter("testcase")]  # fmt: skip
        except ET.ParseError:
            return
    if not rows:
        return
    suite = ET.Element("testsuite", name="pytest", tests=str(len(rows)))
    for cls, name, secs in rows:
        ET.SubElement(suite, "testcase", classname=cls, name=name, time=secs)
    to.mkdir(exist_ok=True)
    for old in to.glob("*.xml"):
        old.unlink()
    ET.ElementTree(suite).write(to / "last.xml", encoding="utf-8", xml_declaration=True)


def run(root: Path, pythons: list[str], say=print, jobs: int = 0,
        everything: bool = False) -> bool:  # fmt: skip
    """Every step, in the folder at root. Each is said as it ends; a failed
    one says its last lines. True when all passed. The tests are run_tests'."""
    env, passed = clean_env(willow_root()), True
    asked = steps(pythons)
    for what, argv in [s for s in asked if not s[0].startswith(TESTS)]:
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
    under = [argv[0] for what, argv in asked if what.startswith(TESTS) and argv]
    if under and not run_tests(root, under, say, jobs or JOBS or os.cpu_count() or 1,
                               everything or EVERYTHING):  # fmt: skip
        passed = False
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


def options(argv: list[str]) -> tuple[list[str], int, bool] | None:
    """(the rest of the command line, --jobs N, --all); None for a bad N."""
    rest, jobs, everything, it = [], 0, False, iter(argv)
    for a in it:
        if a == "--all":
            everything = True
        elif a == "--jobs":
            n = next(it, "")
            if not n.isdigit() or int(n) < 1:
                return None
            jobs = int(n)
        else:
            rest.append(a)
    return rest, jobs, everything


def main(argv: list[str]) -> int:
    global JOBS, EVERYTHING
    opts = options(argv)
    parsed = parse(opts[0]) if opts else None
    if opts:
        JOBS, EVERYTHING = opts[1], opts[2]
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
