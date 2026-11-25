"""Lay a Willow box over each repository, and run the stacks over each.

    python boxes/lay.py --to WORK [--repos DIR] [--only NAME,...] [--across]
                        [--cbm BINARY] [--jobs N] [--no-stacks] [--again]

For each repository in repos.json, found under --repos (by default the
folder holding this checkout), it makes, under WORK:

    piles/NAME/NAME.list    the repository's files, pointed at, never copied
    mirrors/NAME/comments   its comments and docstrings, by file and line
    mirrors/NAME/history    its commit messages, dated by the commit
    mirrors/NAME/graph      its call graph, when --cbm names a built
                            codebase-memory-mcp (graphdb/NAME holds the graph)
    boxes/NAME              the record, laid from the list and the mirrors
    keys/NAME.key           its key: the kernel writes it, and this never
                            opens it
    indexes/NAME/SOURCE     an index of each source, kept by index-cache and
                            rebuilt only when a file in it changed; the code's
                            is of the repository's folder, a little wider than
                            its list (index-cache reads a folder, not a list)
    runs/NAME/STACK.md      each stack's page, and STACK/ as it ran

--across lays one more box, boxes/across, from every repository's list and
mirrors, and runs stacks/across.md over it.

A box that is already there is used as it is: its sources are pointers, so
it follows the files. --again lays a new one beside it (NAME-STAMP), never
over it, since a box may hold the person's seals.

Willow is the checkout WILLOW names (or --willow), run where it is: the
add-ons here are Willow's tools for reading a folder, not the runtime's,
so they are not in willow.pin.json. Nothing here seals, declines or reads
a key. Exit 0 when every box was laid and every stack ran; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
STACKS = HERE / "stacks"
WORDS = HERE / "code-words.txt"
REPOS = HERE / "repos.json"
EACH = ("orient", "owes")

ADDON = {
    "gather": "adapters/stdlib/gather/gather.py",
    "comments": "adapters/stdlib/code-comments/code_comments.py",
    "history": "adapters/stdlib/git-history/git_history.py",
    "graph": "adapters/stdlib/codebase-memory/codebase_memory.py",
    "stack": "adapters/stdlib/stack/stack.py",
    "index": "adapters/stdlib/index-cache/index_cache.py",
}


def say(name: str, what: str) -> None:
    print(f"{name}: {what}", flush=True)


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> tuple[int, str]:
    """Run one command; its exit code and the last line it printed."""
    got = subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True, check=False
    )
    lines = (got.stdout + got.stderr).strip().splitlines()
    return got.returncode, lines[-1] if lines else ""


def willow_tool(willow: Path, tool: str) -> list[str]:
    return [sys.executable, str(willow / ADDON[tool])]


def point(willow: Path, work: Path, name: str, repo: Path, spec: dict) -> Path:
    """The list of the repository's files, written by gather --point."""
    pile = work / "piles" / name
    cmd = willow_tool(willow, "gather")
    cmd += ["--from", str(repo), "--to", str(pile), "--keep", spec["keep"]]
    if spec.get("skip"):
        cmd += ["--skip", spec["skip"]]
    got = subprocess.run(
        cmd + ["--point"], cwd=willow, capture_output=True, text=True, check=False
    )
    first = (got.stdout.strip().splitlines() or [str(got.returncode)])[0]
    say(name, first)
    return pile / f"{name}.list"


def mirror(willow: Path, work: Path, name: str, repo: Path, cbm: str | None) -> dict:
    """The mirrors a step makes from the repository: name -> folder."""
    out = work / "mirrors" / name
    made = {}
    jobs = {
        "comments": willow_tool(willow, "comments") + ["mirror", "--from", str(repo)],
        "history": willow_tool(willow, "history")
        + ["mirror", "--from", str(repo), "--messages"],
    }
    for kind, cmd in jobs.items():
        code, last = run(cmd + ["--to", str(out / kind)], willow)
        say(name, f"{kind} mirror: {last or code}")
        if code == 0:
            made[kind] = out / kind
    if cbm:
        db = work / "graphdb" / name
        db.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, CBM_CACHE_DIR=str(db))
        args = json.dumps({"repo_path": str(repo)})
        code, _ = run([cbm, "cli", "index_repository", args], repo, env)
        if code == 0:
            cmd = willow_tool(willow, "graph") + ["mirror", "--from", str(db)]
            code, last = run(cmd + ["--to", str(out / "graph")], willow)
            say(name, f"graph mirror: {last or code}")
            if code == 0:
                made["graph"] = out / "graph"
        else:
            say(name, f"graph: codebase-memory-mcp exited {code}, no graph")
    elif (out / "graph").is_dir():
        made["graph"] = out / "graph"  # made by an earlier run with --cbm
        say(name, "graph mirror: the one an earlier run made")
    return made


def index(willow: Path, work: Path, name: str, repo: Path, made: dict) -> list[Path]:
    """An index of each source, brought current by index-cache, so a question
    is answered in a second rather than by reading the whole box again."""
    at = work / "indexes" / name
    at.mkdir(parents=True, exist_ok=True)
    out = []
    for source, folder in [(name, repo)] + [
        (f"{name}-{k}", v) for k, v in made.items()
    ]:
        cmd = willow_tool(willow, "index") + [
            "--from",
            str(folder),
            "--to",
            str(at / source),
        ]
        code, last = run(cmd, willow)
        say(name, f"index {source}: {last.split(';')[0] or code}")
        if code == 0:
            out.append(at / source)
    return out


def words(work: Path) -> Path:
    """The words list, copied beside the boxes as the kernel wants it: 600."""
    at = work / "code-words.txt"
    if not at.exists():
        shutil.copyfile(WORDS, at)
        at.chmod(0o600)
    return at


def lay(
    willow: Path, work: Path, name: str, sources: list[str], again: bool
) -> Path | None:
    """The box, laid from sources; one already there is used as it is."""
    box = work / "boxes" / name
    if (box / "kernel.json").exists():
        if not again:
            say(name, f"box already laid, used as it is: {box}")
            return box
        box = box.with_name(f"{name}-{time.strftime('%Y%m%d-%H%M%S')}")
    keys = work / "keys"
    keys.mkdir(parents=True, exist_ok=True)
    keys.chmod(0o700)
    cmd = [sys.executable, str(willow / "kernel.py"), "init", "--box", str(box)]
    for source in sources:
        cmd += ["--from", source]
    cmd += ["--key", str(keys / f"{box.name}.key"), "--words", str(words(work))]
    code, last = run(cmd, willow)
    say(name, f"box: {last or code}")
    return box if code == 0 else None


def stack(
    willow: Path,
    work: Path,
    name: str,
    box: Path,
    page: Path,
    repo: Path | None,
    indexes: list[Path],
) -> bool:
    """One stack file over one box: {repo} and {indexes} filled in here,
    {box} by stack. {indexes} is an --index for each source's index and the
    words list. A repository's own questions (stacks/ask/NAME.md) run as
    "ask"."""
    stem = "ask" if page.parent.name == "ask" else page.stem
    runs = work / "runs" / name
    runs.mkdir(parents=True, exist_ok=True)
    text = page.read_text(encoding="utf-8")
    if repo is not None:
        text = text.replace("{repo}", str(repo))
    given = " ".join(f"--index {i}" for i in indexes)
    text = text.replace("{indexes}", f"{given} --words {words(work)}")
    filled = runs / f"{stem}.stack.md"
    filled.write_text(text, encoding="utf-8")
    cmd = willow_tool(willow, "stack") + ["--box", str(box), "--stack", str(filled)]
    ran = runs / stem
    if ran.exists():
        shutil.rmtree(ran)
    cmd += ["--to", str(ran)]
    got = subprocess.run(cmd, cwd=willow, capture_output=True, text=True, check=False)
    (runs / f"{stem}.md").write_text(got.stdout, encoding="utf-8")
    tail = (got.stdout.strip().splitlines() or [""])[-1]
    say(name, f"stack {stem}: exit {got.returncode}, {tail}")
    return got.returncode in (0, 42)


def one(
    args, willow: Path, work: Path, name: str, spec: dict
) -> tuple[bool, list[str], list[Path]]:
    """Lay one repository's box, index its sources and run its stacks;
    whether all went, and the box's sources and indexes, for the box across
    them all."""
    repo = args.repos / spec.get("path", name)
    if not (repo / ".git").exists():
        say(name, f"not a git checkout, left out: {repo}")
        return False, [], []
    listed = point(willow, work, name, repo, spec)
    made = mirror(willow, work, name, repo, args.cbm)
    sources = [f"{name}=@{listed}"] + [f"{name}-{k}={v}" for k, v in made.items()]
    box = lay(willow, work, name, sources, args.again)
    if box is None:
        return False, sources, []
    indexes = index(willow, work, name, repo, made)
    if args.no_stacks:
        return True, sources, indexes
    pages = [STACKS / f"{each}.md" for each in EACH]
    asked = STACKS / "ask" / f"{name}.md"
    if asked.exists():
        pages.append(asked)
    ok = [stack(willow, work, name, box, page, repo, indexes) for page in pages]
    return all(ok), sources, indexes


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="lay.py", description=__doc__.split("\n")[0])
    p.add_argument("--to", type=Path, required=True, help="where the boxes go")
    p.add_argument("--repos", type=Path, default=HERE.parent.parent)
    p.add_argument("--willow", type=Path, default=os.environ.get("WILLOW"))
    p.add_argument("--only", default="", help="NAME,NAME: these repositories")
    p.add_argument("--across", action="store_true", help="and one box over all")
    p.add_argument("--cbm", help="a built codebase-memory-mcp, for the call graph")
    p.add_argument("--jobs", type=int, default=2)
    p.add_argument("--no-stacks", action="store_true")
    p.add_argument("--again", action="store_true", help="lay new boxes beside")
    args = p.parse_args(argv)
    if args.willow is None or not (args.willow / "kernel.py").exists():
        print("lay: name Willow's checkout with WILLOW or --willow", file=sys.stderr)
        return 2
    willow = args.willow.resolve()
    args.repos = args.repos.resolve()
    work = args.to.resolve()
    work.mkdir(parents=True, exist_ok=True)
    repos = json.loads(REPOS.read_text(encoding="utf-8"))["repos"]
    if args.only:
        wanted = args.only.split(",")
        unknown = [n for n in wanted if n not in repos]
        if unknown:
            print(f"lay: not in repos.json: {', '.join(unknown)}", file=sys.stderr)
            return 2
        repos = {n: repos[n] for n in wanted}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        done = list(pool.map(lambda n: one(args, willow, work, n, repos[n]), repos))
    ok = all(went for went, _, _ in done)
    if args.across:
        sources = [s for _, each, _ in done for s in each]
        indexes = [i for _, _, each in done for i in each]
        box = lay(willow, work, "across", sources, args.again) if sources else None
        ok = ok and box is not None
        if box is not None and not args.no_stacks:
            page = STACKS / "across.md"
            ok = stack(willow, work, "across", box, page, None, indexes) and ok
    print(
        f"lay: {'done' if ok else 'done, with some left out'}; pages under {work / 'runs'}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
