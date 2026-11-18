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
    assert used and used <= set(willow_pin.ADD_ONS), used - set(willow_pin.ADD_ONS)


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


@pytest.mark.parametrize("argv", [[], ["seal"], ["check", "--willow"], ["check", "x"]])
def test_a_bad_command_line_says_how_to_run_it(argv):
    assert willow_pin.main(argv) == 2
