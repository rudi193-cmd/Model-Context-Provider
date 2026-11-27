"""check.py: the check a change is held to on this machine, and the hook
that holds main to it with no server asked."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check

PASSES_IF_OK_TXT = [sys.executable, "-c",
                    "import pathlib, sys; sys.exit(0 if pathlib.Path('ok.txt').exists() else 1)"]  # fmt: skip


def git(repo, *args):
    run = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True, text=True, check=False, env=check.clean_env(repo),
    )  # fmt: skip
    return run


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A small repository standing in for this one, on main, with one commit."""
    r = tmp_path / "repo"
    r.mkdir()
    assert git(r, "init", "-q", "-b", "main").returncode == 0
    (r / "willow_pin.py").write_text("raise SystemExit(0)\n")
    (r / "ok.txt").write_text("fine\n")
    git(r, "add", "-A")
    assert git(r, "commit", "-q", "-m", "first").returncode == 0
    monkeypatch.setattr(check, "HERE", r)
    monkeypatch.setattr(
        check, "steps", lambda pythons: [("the stub", PASSES_IF_OK_TXT)]
    )
    return r


def test_the_command_line():
    assert check.parse([]) == ("check", [sys.executable], None, False)
    assert check.parse(["--python", "a", "--python", "b"]) == ("check", ["a", "b"], None, False)  # fmt: skip
    assert check.parse(["--commit", "HEAD"])[2] == "HEAD"
    assert check.parse(["hook", "--write", "--python", "a"]) == ("hook", ["a"], None, True)  # fmt: skip
    for bad in (["--nope"], ["--python"], ["--commit"], ["hook", "--commit", "x"], ["--write"]):  # fmt: skip
        assert check.parse(bad) is None, bad


def test_it_asks_the_pin_lint_format_and_the_tests_under_each_python(monkeypatch):
    monkeypatch.setattr(check, "ruff_of", lambda pythons: ["ruff"])
    asked = check.steps(["py-a", "py-b"])
    assert [what for what, _ in asked] == [
        "Willow is the pinned one", "lint", "format",
        "tests, under py-a", "tests, under py-b",
    ]  # fmt: skip
    assert asked[0][1] == ["py-a", "willow_pin.py", "check"]
    assert asked[3][1] == ["py-a", "-m", "pytest", "-q"]
    monkeypatch.setattr(check, "ruff_of", lambda pythons: None)
    assert check.steps(["py-a"])[1][1] is None  # no ruff: said, never skipped


def test_a_step_with_nothing_to_run_it_fails_the_check(tmp_path, monkeypatch):
    monkeypatch.setattr(check, "steps", lambda pythons: [("lint", None)])
    said = []
    assert check.run(tmp_path, [sys.executable], said.append) is False
    assert "NO" in said[0] and "ruff" in said[0]


def test_a_commit_is_checked_as_committed_never_as_the_folder_is(repo):
    said = []
    assert check.check_commit("HEAD", [sys.executable], said.append) == 0
    git(repo, "rm", "-q", "ok.txt")
    git(repo, "commit", "-q", "-m", "drop it")
    (repo / "ok.txt").write_text("back, but not committed\n")
    assert check.check_commit("HEAD", [sys.executable], said.append) == 1
    assert "FAILED" in said[-1]


def test_a_commit_that_passed_is_not_checked_twice(repo, monkeypatch):
    assert check.check_commit("HEAD", [sys.executable], lambda s: None) == 0
    monkeypatch.setattr(check, "steps", lambda pythons: pytest.fail("checked again"))
    said = []
    assert check.check_commit("HEAD", [sys.executable], said.append) == 0
    assert "passed before" in said[-1]
    # under another Python it has not passed yet
    with pytest.raises(pytest.fail.Exception):
        check.check_commit("HEAD", [sys.executable, "other"], said.append)


def test_a_commit_that_passed_still_answers_for_willows_pin(repo):
    assert check.check_commit("HEAD", [sys.executable], lambda s: None) == 0
    (repo / "willow_pin.py").write_text("raise SystemExit(1)\n")
    git(repo, "commit", "-q", "-am", "pin now fails")
    # a new tree, so it is checked whole; put the first tree's pin to the test
    first = git(repo, "rev-parse", "HEAD~1").stdout.strip()
    assert check.check_commit(first, [sys.executable], lambda s: None) == 0


def test_what_is_not_a_commit_is_a_bad_command_line(repo):
    assert check.check_commit("no-such-rev", [sys.executable], lambda s: None) == 2


def stub_check(repo, passes: bool):
    """Stand a check.py in the repo that passes or fails, so the hook's own
    shell is what is tested."""
    (repo / "check.py").write_text(f"raise SystemExit({0 if passes else 1})\n")


def test_the_hook_refuses_a_commit_to_main_that_fails_the_check(repo):
    stub_check(repo, passes=False)
    assert check.write_hook([sys.executable], lambda s: None) == 0
    before = git(repo, "rev-parse", "main").stdout
    (repo / "new.txt").write_text("x\n")
    git(repo, "add", "-A")
    assert git(repo, "commit", "-q", "-m", "second").returncode != 0
    assert git(repo, "rev-parse", "main").stdout == before  # main didn't move


def test_the_hook_lets_a_passing_commit_onto_main_and_any_commit_elsewhere(repo):
    stub_check(repo, passes=True)
    check.write_hook([sys.executable], lambda s: None)
    (repo / "new.txt").write_text("x\n")
    git(repo, "add", "-A")
    assert git(repo, "commit", "-q", "-m", "second").returncode == 0
    stub_check(repo, passes=False)
    assert git(repo, "checkout", "-q", "-b", "work").returncode == 0
    git(repo, "add", "-A")
    assert git(repo, "commit", "-q", "-m", "on a branch").returncode == 0


def test_the_hook_holds_a_fast_forward_onto_main_too(repo):
    git(repo, "checkout", "-q", "-b", "work")
    (repo / "new.txt").write_text("x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "on a branch")
    git(repo, "checkout", "-q", "main")
    stub_check(repo, passes=False)  # not committed: only the hook's stub
    check.write_hook([sys.executable], lambda s: None)
    before = git(repo, "rev-parse", "main").stdout
    assert git(repo, "merge", "-q", "--ff-only", "work").returncode != 0
    assert git(repo, "rev-parse", "main").stdout == before


def test_the_hook_names_each_python_and_only_main(repo):
    text = check.hook_text(["/a/python3.14", "/b/python3.9"])
    assert "--python /a/python3.14 --python /b/python3.9" in text
    assert '--commit "$new"' in text and "refs/heads/main" in text
    assert text.startswith("#!/bin/sh\n" + check.MARK)


def test_writing_the_hook_never_goes_over_one_that_isnt_ours(repo):
    at = check.hook_path()
    at.parent.mkdir(parents=True, exist_ok=True)
    at.write_text("#!/bin/sh\necho someone else's\n")
    said = []
    assert check.write_hook([sys.executable], said.append) == 2
    assert "someone else's" in at.read_text() and "refused" in said[0]
    at.unlink()
    assert check.write_hook([sys.executable], said.append) == 0
    assert check.write_hook(["another"], said.append) == 0  # ours: brought up to date
    assert "--python another" in at.read_text()


# ── the tests in parts, and a pass remembered by what they can read ─────────
@pytest.fixture
def small(tmp_path, monkeypatch):
    """A folder with two passing tests and a doc, and somewhere to remember."""
    root, book = tmp_path / "small", tmp_path / "book"
    (root / "tests").mkdir(parents=True)
    book.mkdir()
    (root / "tests" / "test_files.py").write_text("def test_docs():\n    assert True\n")
    (root / "tests" / "test_code.py").write_text("def test_code():\n    assert True\n")
    (root / "thing.py").write_text("X = 1\n")
    (root / "README.md").write_text("# words\n")
    monkeypatch.setattr(check, "kept", lambda: book)
    return root


def ran(root, **more):
    said = []
    ok = check.run_tests(root, [sys.executable], said.append, more.pop("jobs", 2),
                         more.pop("everything", False))  # fmt: skip
    return ok, "\n".join(said)


def test_the_command_line_takes_all_and_jobs():
    assert check.options(["--all", "--python", "p", "--jobs", "3"]) == (["--python", "p"], 3, True)  # fmt: skip
    assert check.options([]) == ([], 0, False)
    for bad in (["--jobs"], ["--jobs", "0"], ["--jobs", "many"]):
        assert check.options(bad) is None


def test_a_doc_counts_by_its_name_and_everything_else_by_its_bytes(small):
    first = check.inputs_key(small, ["py"])
    (small / "README.md").write_text("# other words\n")
    assert check.inputs_key(small, ["py"]) == first  # a doc's words: not read
    (small / "__pycache__").mkdir()
    (small / "__pycache__" / "x.pyc").write_text("cache")
    assert check.inputs_key(small, ["py"]) == first  # nor a cache
    (small / "NEW.md").write_text("")
    named = check.inputs_key(small, ["py"])
    assert named != first  # a doc added: the file list reads its name
    (small / "thing.py").write_text("X = 2\n")
    assert check.inputs_key(small, ["py"]) != named
    assert check.inputs_key(small, ["other"]) != check.inputs_key(small, ["py"])


def test_tests_that_passed_are_not_run_again_until_something_they_read_changes(small):
    ok, said = ran(small)
    assert ok, said
    assert "tests, under" in said and "nothing they read" not in said
    ok, said = ran(small)
    assert ok and "nothing they read has changed" in said
    (small / "README.md").write_text("# a docs change\n")
    assert "nothing they read has changed" in ran(small)[1]
    assert "nothing they read" not in ran(small, everything=True)[1]  # --all
    (small / "thing.py").write_text("X = 2\n")
    ok, said = ran(small)
    assert ok and "nothing they read" not in said  # code changed: every test again


def test_a_failing_run_is_never_remembered_and_the_docs_test_still_holds(small):
    (small / "tests" / "test_code.py").write_text(
        "def test_code():\n    assert False\n"
    )
    for _ in range(2):  # failed, and failed again: not remembered as passed
        ok, said = ran(small)
        assert not ok and "NO   tests, under" in said
    (small / "tests" / "test_code.py").write_text("def test_code():\n    assert True\n")
    assert ran(small)[0]
    # nothing read has changed, but the docs test is still asked, and can fail
    (small / "tests" / "test_files.py").write_text(
        "def test_docs():\n    assert True\n"
    )
    assert "nothing they read has changed" in ran(small)[1]


def test_parts_run_at_once_and_their_times_are_kept_for_the_next_cut(
    small, monkeypatch
):
    monkeypatch.setattr(
        check, "parts_of",
        lambda py, root, jobs, env: [["tests/test_files.py"], ["tests/test_code.py"]],
    )  # fmt: skip
    ok, said = ran(small)
    assert ok and "(2 parts)" in said and "2 at once" in said
    (kept,) = (check.kept() / "model-context-provider-times").glob("*.xml")
    assert kept.read_text().count("<testcase") == 2
    # a part that fails fails the check, and says its own last lines
    (small / "tests" / "test_code.py").write_text(
        "def test_code():\n    assert 1 == 2\n"
    )
    ok, said = ran(small)
    assert not ok and "assert 1 == 2" in said


def test_a_part_that_hangs_is_stopped_and_says_where_it_was(small, monkeypatch):
    monkeypatch.setattr(
        check, "parts_of",
        lambda py, root, jobs, env: [["tests/test_files.py"], ["tests/test_code.py"]],
    )  # fmt: skip
    monkeypatch.setattr(check, "PART_SECONDS", 8)
    monkeypatch.setattr(check, "STACK_SECONDS", 2)
    (small / "tests" / "test_code.py").write_text(
        "import time\n\ndef test_code():\n    time.sleep(60)\n"
    )
    began = check.time.monotonic()
    ok, said = ran(small)
    assert not ok and check.time.monotonic() - began < 40
    assert "stopped after 8 s, still running: tests/test_code.py" in said
    assert "test_code.py" in said.split("stopped after")[0]  # where it hung


def test_willows_test_shards_cuts_every_file_into_exactly_one_part(small):
    """The cut is Willow's own; here it is only held to giving each test
    file once. With no Willow add-on to ask, the tests are one run."""
    env = check.clean_env(check.willow_root())
    parts = check.parts_of(sys.executable, small, 2, env)
    assert sorted(f for p in parts for f in p) == ["tests/test_code.py", "tests/test_files.py"]  # fmt: skip
    assert check.parts_of(sys.executable, small, 1, env) is None
