"""boxes/: the maintainer's boxes over the repositories built beside this.
Held here: every repository has its questions, every stack's steps sit
under a pool and fill in only what lay.py or the stack add-on fills in, the
words list is in the kernel's format, and lay.py neither seals nor opens a
key, and refuses to run without Willow."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOXES = ROOT / "boxes"
STEP = re.compile(r"^- ([a-z0-9-]+) -- (.*)$")


def stacks():
    return sorted((BOXES / "stacks").rglob("*.md"))


def test_every_repository_has_its_questions():
    repos = json.loads((BOXES / "repos.json").read_text())["repos"]
    for name, spec in repos.items():
        assert (BOXES / "stacks" / "ask" / f"{name}.md").exists(), name
        assert spec["keep"].startswith("."), name
    asked = {p.stem for p in (BOXES / "stacks" / "ask").glob("*.md")}
    assert asked == set(repos), "a question stack for a repository not listed"


def test_each_step_sits_under_a_pool_and_fills_in_only_what_is_filled():
    for page in stacks():
        pool, steps = None, 0
        for line in page.read_text().splitlines():
            if line.startswith("## "):
                pool = line
            m = STEP.match(line)
            if not m:
                continue
            assert pool, f"{page.name}: a step before any pool: {line}"
            steps += 1
            holes = set(re.findall(r"\{(\w+)\}", m.group(2)))
            allowed = {"box"} if page.name == "across.md" else {"box", "repo"}
            assert holes <= allowed, f"{page.name}: {line}"
        assert steps, f"{page.name} has no step"


def test_the_words_list_is_in_the_kernels_format():
    for line in (BOXES / "code-words.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        word, _, means = line.partition("=")
        assert re.fullmatch(r"[a-z0-9]+", word.strip()), line
        for each in means.split(","):
            assert re.fullmatch(r"[a-z0-9]+", each.strip()), line


def test_lay_neither_seals_nor_opens_a_key():
    text = (BOXES / "lay.py").read_text()
    code = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    )
    for verb in ('"seal"', '"decline"', "'seal'", "'decline'"):
        assert verb not in code
    assert ".key" in code  # it names the key's path for the kernel to write
    assert not re.search(r"open\([^)]*key|keys?\b[^\n]*\.read_", code)


def test_lay_refuses_without_willow(tmp_path):
    got = subprocess.run(
        [sys.executable, str(BOXES / "lay.py"), "--to", str(tmp_path / "w")],
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
        check=False,
    )
    assert got.returncode == 2
    assert "WILLOW" in got.stderr
