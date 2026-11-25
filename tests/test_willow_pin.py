"""The Willow this was built on, held to its pin: by every file of what runs."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

import runtime
import willow_pin

FROST = "when does the first frost come"


def copy(tmp_path):
    """A copy of the pinned files of the Willow under test, as a git checkout."""
    root = tmp_path / "Willow"
    for rel in willow_pin.load()["files"]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(runtime.WILLOW / rel, root / rel)
    for args in (["init", "-q"], ["add", "."],
                 ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "w"]):  # fmt: skip
        subprocess.run(["git", "-C", str(root), *args], check=True)
    return root


def test_the_willow_under_test_is_the_pinned_one():
    assert willow_pin.problems(runtime.WILLOW) == []


def test_every_add_on_the_runtime_runs_is_pinned():
    src = "".join(Path(f).read_text() for f in ("runtime.py", "set_up.py", "hosts.py"))
    used = set(re.findall(r"adapters/stdlib/([a-z0-9-]+)/", src))
    pinned = set(willow_pin.load()["add_ons"])
    assert used and used <= pinned, used - pinned


def test_a_changed_missing_or_new_file_is_named(tmp_path):
    root = copy(tmp_path)
    assert willow_pin.problems(root) == []
    (root / "kernel.py").write_text("# not the kernel\n")
    (root / "adapters/stdlib/privacy/privacy.py").unlink()
    (root / "adapters/stdlib/backup/extra.py").write_text("")
    assert willow_pin.problems(root) == [
        "missing: adapters/stdlib/privacy/privacy.py",
        "differs: kernel.py",
        "not pinned: adapters/stdlib/backup/extra.py",
    ]


def test_a_change_elsewhere_in_willow_does_not_matter(tmp_path):
    root = copy(tmp_path)
    (root / "adapters/stdlib/garden").mkdir(parents=True)
    (root / "adapters/stdlib/garden/garden.py").write_text("")
    (root / "adapters/stdlib/backup/test_more.py").write_text("")
    assert willow_pin.problems(root) == []


def test_repin_names_what_moved_and_refuses_what_isnt_committed(tmp_path):
    root = copy(tmp_path)
    pin = tmp_path / "pin.json"
    shutil.copyfile(willow_pin.PIN, pin)
    (root / "kernel.py").write_text("# a newer kernel\n")
    code, said = willow_pin.repin(root, pin)
    assert code == 2 and "kernel.py" in said
    assert pin.read_bytes() == willow_pin.PIN.read_bytes()
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qam", "newer"], check=True)  # fmt: skip
    code, said = willow_pin.repin(root, pin)
    assert code == 0 and said.splitlines()[1:] == ["changed: kernel.py"], said
    assert willow_pin.problems(root, pin) == []
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()  # fmt: skip
    assert willow_pin.load(pin)["commit"] == head


def commit(root):
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-qm", "more"], check=True)  # fmt: skip


def a_pin(tmp_path):
    pin = tmp_path / "pin.json"
    shutil.copyfile(willow_pin.PIN, pin)
    return pin


def test_repin_at_the_pinned_bytes_moves_only_the_commit(tmp_path):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    code, said = willow_pin.repin(root, pin)
    assert code == 0 and "\n" not in said, said
    old, new = willow_pin.load(), willow_pin.load(pin)
    assert list(new) == list(old) and new["commit"] != old["commit"]
    assert {k: v for k, v in new.items() if k != "commit"} == {k: v for k, v in old.items() if k != "commit"}  # fmt: skip


def test_a_new_file_of_a_pinned_add_on_comes_in_and_its_tests_do_not(tmp_path):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    backup = root / "adapters/stdlib/backup"
    (backup / "extra.py").write_text("x = 1\n")
    (backup / "test_more.py").write_text("")
    (backup / "conftest.py").write_text("")
    commit(root)
    code, said = willow_pin.repin(root, pin)
    assert code == 0 and said.splitlines()[1:] == ["added: adapters/stdlib/backup/extra.py"], said  # fmt: skip
    names = list(willow_pin.load(pin)["files"])
    assert names[names.index("adapters/stdlib/backup/extra.py") - 1].startswith("adapters/stdlib/backup/")  # fmt: skip
    assert willow_pin.problems(root, pin) == []


def test_add_and_drop_name_an_add_on_where_it_lives(tmp_path):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    for kind, name in (("stdlib", "garden"), ("deps", "greenhouse")):
        d = root / "adapters" / kind / name
        d.mkdir(parents=True)
        (d / (name + ".py")).write_text("x = 1\n")
        (d / ("test_" + name + ".py")).write_text("")
    commit(root)
    code, said = willow_pin.repin(root, pin, add=["garden", "greenhouse"], drop=["sms"])
    assert code == 0, said
    doc = willow_pin.load(pin)
    assert "garden" in doc["add_ons"] and "greenhouse" in doc["deps"] and "sms" not in doc["add_ons"]  # fmt: skip
    i = doc["add_ons"].index("garden")
    assert doc["add_ons"][i - 1] < "garden" < doc["add_ons"][i + 1]  # in its place
    assert "added: adapters/stdlib/garden/garden.py" in said
    assert "added: adapters/deps/greenhouse/greenhouse.py" in said
    assert any(
        line.startswith("gone: adapters/stdlib/sms/") for line in said.splitlines()
    )
    assert not [f for f in doc["files"] if "/test_" in f]
    assert willow_pin.problems(root, pin) == []


def test_repin_refuses_and_leaves_the_pin_as_it_was(tmp_path):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    (tmp_path / "nowhere").mkdir()
    for where, more, why in (
        (tmp_path / "nowhere", {}, "isn't a Willow git checkout"),
        (root, {"add": ["no-such"]}, "has no add-on no-such"),
        (root, {"drop": ["no-such"]}, "no-such isn't an add-on the pin names"),
    ):
        code, said = willow_pin.repin(where, pin, **more)
        assert code == 2 and why in said, said
    (root / "adapters/stdlib/backup/test_later.py").write_text(
        ""
    )  # a test: never pinned
    other = tmp_path / "other"
    other.mkdir()
    assert willow_pin.repin(root, a_pin(other))[0] == 0
    (root / "adapters/stdlib/backup/new.py").write_text(
        ""
    )  # in a pinned folder, not committed
    code, said = willow_pin.repin(root, pin)
    assert code == 2 and "adapters/stdlib/backup/new.py" in said, said
    (root / "adapters/stdlib/backup/new.py").unlink()
    (root / "kernel.py").write_text("# changed, not committed\n")
    code, said = willow_pin.repin(root, pin)
    assert code == 2 and "kernel.py" in said, said
    assert pin.read_bytes() == willow_pin.PIN.read_bytes()


def test_no_door_runs_on_a_willow_it_wasnt_built_on(box, tmp_path, monkeypatch):
    pin = tmp_path / "pin.json"
    doc = willow_pin.load()
    doc["files"]["kernel.py"] = "0" * 64
    pin.write_text(__import__("json").dumps(doc))
    monkeypatch.setattr(runtime, "PIN", pin)
    before = (box / "record.jsonl").read_bytes()
    for door in ("pipe", "mcp", "hook", "session"):
        got = runtime.call(box, "read", FROST, door=door)
        assert got["state"] == "refused" and got["code"] == "willow_unpinned", got
        assert "kernel.py" in got["why"]
    assert (box / "record.jsonl").read_bytes() == before


def head(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()  # fmt: skip


def test_what_runs_is_the_pinned_commit_whatever_the_checkout_is_on(
    tmp_path, monkeypatch
):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    assert willow_pin.repin(root, pin)[0] == 0
    pinned = head(root)
    (root / "kernel.py").write_text("# a newer kernel\n")
    commit(root)  # the checkout moves on; the pin stays
    (root / "adapters/stdlib/backup/half.py").write_text("")  # and is mid-change
    monkeypatch.setenv("WILLOW", str(root))
    got = willow_pin.default_root(pin)
    assert (
        got == root / ".git/willow-pinned" / pinned
        and (got / willow_pin.DONE).is_file()
    )
    assert willow_pin.problems(got, pin) == []
    assert willow_pin.problems(root, pin) != []  # the checkout itself isn't it
    assert willow_pin.default_root(pin) == got  # made once
    other = tmp_path / "other-worktree"
    subprocess.run(["git", "-C", str(root), "worktree", "add", "-q", "--detach", str(other)], check=True)  # fmt: skip
    monkeypatch.setenv("WILLOW", str(other))
    assert willow_pin.default_root(pin) == got  # every checkout of that git shares it


def test_a_willow_that_isnt_git_is_run_where_it_is(tmp_path, monkeypatch):
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.setenv("WILLOW", str(plain))
    assert willow_pin.default_root() == plain and list(plain.iterdir()) == []


def test_a_commit_its_git_lacks_makes_no_copy(tmp_path):
    root = copy(tmp_path)
    assert willow_pin.pinned_copy(root, "0" * 40) is None
    assert not (root / ".git/willow-pinned").exists() or not list((root / ".git/willow-pinned").iterdir())  # fmt: skip


def test_repin_at_a_commit_reads_git_not_the_checkout(tmp_path):
    root, pin = copy(tmp_path), a_pin(tmp_path)
    first = head(root)
    (root / "kernel.py").write_text("# a newer kernel\n")
    commit(root)
    (root / "kernel.py").write_text("# changed, not committed\n")
    code, said = willow_pin.repin(root, pin, at=first)
    assert code == 0 and willow_pin.load(pin)["commit"] == first, said
    assert willow_pin.load(pin)["files"] == willow_pin.load()["files"]
    code, said = willow_pin.repin(root, pin, at="no-such-branch")
    assert code == 2 and "has no commit no-such-branch" in said


def a_repo(tmp_path, pin):
    """A repo of this one's that holds only the pin, to commit it in, with
    its own name for git, as CI has none."""
    here = tmp_path / "here"
    here.mkdir()
    shutil.copyfile(pin, here / "willow.pin.json")
    commit_all = ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "p"]
    for args in (["init", "-q"], ["add", "."], commit_all,
                 ["config", "user.name", "t"], ["config", "user.email", "t@t"]):  # fmt: skip
        subprocess.run(["git", "-C", str(here), *args], check=True)
    return here


@pytest.mark.parametrize("passes", [True, False])
def test_follow_commits_the_pin_only_when_the_check_passes(
    tmp_path, monkeypatch, passes
):
    root = copy(tmp_path)
    here = a_repo(tmp_path, willow_pin.PIN)
    pin = here / "willow.pin.json"
    (root / "kernel.py").write_text("# a newer kernel\n")
    commit(root)
    monkeypatch.setenv("WILLOW", str(root))
    monkeypatch.setattr(willow_pin, "HERE", here)
    monkeypatch.setattr(willow_pin, "CHECK", ["python3", "-c", f"raise SystemExit({int(not passes)})"])  # fmt: skip
    before, was = head(here), pin.read_bytes()
    code, said = willow_pin.follow("HEAD", pin)
    if passes:
        assert code == 0 and said.endswith("committed, not pushed"), said
        assert willow_pin.load(pin)["commit"] == head(root)
        assert (
            head(here) != before and (root / ".git/willow-pinned" / head(root)).is_dir()
        )
        assert willow_pin.follow("HEAD", pin)[1].endswith("nothing moved")
    else:
        assert code == 1 and "back as it was" in said, said
        assert pin.read_bytes() == was and head(here) == before


def test_prune_lets_go_of_old_copies_but_this_pins(tmp_path, monkeypatch):
    import os
    import time

    root = copy(tmp_path)
    first = head(root)
    (root / "kernel.py").write_text("# a newer kernel\n")
    commit(root)
    second = head(root)
    old, new = willow_pin.pinned_copy(root, first), willow_pin.pinned_copy(root, second)
    month = time.time() - 30 * willow_pin.DAY
    for at in (old, new):
        os.utime(at / willow_pin.DONE, (month, month))
    assert willow_pin.prune(root, keep=second) == [first]
    assert not old.exists() and new.is_dir()
    assert willow_pin.prune(root, keep="", days=60) == []  # not old enough
    assert willow_pin.pinned_copy(root, first) == old and old.is_dir()  # made again
    os.utime(old / willow_pin.DONE, (month, month))
    willow_pin.pinned_copy(root, first)  # run: marked as used today
    assert willow_pin.prune(root, keep=second) == []


def test_settings_name_willows_git_never_the_copy():
    import hosts

    assert hosts.env() == {"WILLOW": str(runtime.WILLOW_SOURCE)}
    assert str(runtime.WILLOW_SOURCE) in hosts.session_command("claude", Path("box"))


@pytest.mark.parametrize("argv", [[], ["seal"], ["check", "--willow"], ["check", "x"],
                                  ["check", "--add", "x"], ["repin", "--add"], ["repin", "--drop"],
                                  ["repin", "--at"], ["check", "--at", "x"],
                                  ["follow", "a", "b"], ["follow", "--all"],
                                  ["prune", "x"], ["prune", "--days"], ["prune", "--days", "x"]])  # fmt: skip
def test_a_bad_command_line_says_how_to_run_it(argv):
    assert willow_pin.main(argv) == 2
