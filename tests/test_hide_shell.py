"""hide-shell: with it on, a shell command the guards allow is handed back
to the host as the same command through doors/hide.py, which runs it with
the box, its key, the runtime's folder and what hide.txt names gone, and
everything else as the person's own shell has it."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import runtime

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "doors" / "guard.py"
DOOR = ROOT / "doors" / "hide.py"


def can_sandbox() -> bool:
    """Whether bubblewrap makes a sandbox here: not where it is missing, nor
    inside another sandbox that forbids one."""
    if not shutil.which("bwrap"):
        return False
    run = subprocess.run(["bwrap", "--dev-bind", "/", "/", "true"],
                         capture_output=True, check=False)  # fmt: skip
    return run.returncode == 0


SANDBOX = pytest.mark.skipif(
    not can_sandbox(), reason="bubblewrap makes no sandbox here"
)


def guard(box, sent):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    return subprocess.run([sys.executable, str(GUARD), "--box", str(box)],
                          input=json.dumps(sent), capture_output=True, text=True,
                          check=False, env=env)  # fmt: skip


def bash(command, cwd, **given):
    return {"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(cwd),
            "tool_name": "Bash", "tool_input": {"command": command, **given}}  # fmt: skip


def through(box, command):
    return [sys.executable, str(DOOR), "--box", str(box), "--command", command]


def door(box, command, cwd, **more):
    return subprocess.run(through(box, command), capture_output=True, text=True,
                          check=False, cwd=cwd, **more)  # fmt: skip


def handed(run) -> str:
    return json.loads(run.stdout)["hookSpecificOutput"]["updatedInput"]["command"]


@pytest.fixture
def hiding(box):
    runtime.hooks_set(box, {"on": ["hide-shell"]})
    return box


def test_on_an_allowed_command_is_handed_back_through_the_hide_door(hiding, tmp_path):
    run = guard(hiding, bash("ls -la", tmp_path, timeout=5000, description="look"))
    assert run.returncode == 0, run.stderr
    out = json.loads(run.stdout)["hookSpecificOutput"]
    assert "permissionDecision" not in out  # the host still asks the person
    assert out["updatedInput"] == {
        "command": shlex.join(through(hiding, "ls -la")),
        "timeout": 5000, "description": "look"}  # fmt: skip


def test_off_or_blocked_nothing_is_handed_back(box, tmp_path):
    assert guard(box, bash("ls", tmp_path)).stdout == ""
    runtime.hooks_set(box, {"on": ["hide-shell"]})
    run = guard(box, bash(f"cat {box.parent / 'test.key'}", tmp_path))
    assert run.returncode == 2 and run.stdout == ""


def test_a_command_already_through_the_door_is_judged_by_what_is_inside(
    hiding, tmp_path
):
    assert guard(hiding, bash(shlex.join(through(hiding, "ls")), tmp_path)).stdout == ""
    inside = shlex.join(through(hiding, f"cat {hiding.parent / 'test.key'}"))
    assert guard(hiding, bash(inside, tmp_path)).returncode == 2
    # a door for another box, or another program by the door's name, is a
    # command like any other: wrapped as one
    for other in (through(tmp_path, "ls"),
                  [sys.executable, "/tmp/hide.py", *through(hiding, "ls")[2:]]):  # fmt: skip
        run = guard(hiding, bash(shlex.join(other), tmp_path))
        assert handed(run) == shlex.join(through(hiding, shlex.join(other)))


def test_with_both_on_kart_contains_and_a_hide_door_is_wrapped_again(hiding, tmp_path):
    runtime.hooks_set(hiding, {"on": ["kart-shell"]})
    got = handed(guard(hiding, bash("ls", tmp_path)))
    assert str(runtime.SHELL_DOOR) in got and str(runtime.HIDE_DOOR) not in got
    got = handed(guard(hiding, bash(shlex.join(through(hiding, "ls")), tmp_path)))
    assert shlex.split(got)[1] == str(runtime.SHELL_DOOR)


def test_cursors_shell_is_held_where_it_cant_be_handed_a_command(hiding, tmp_path):
    sent = {"hook_event_name": "beforeShellExecution", "conversation_id": "c1",
            "command": "ls", "cwd": str(tmp_path)}  # fmt: skip
    run = guard(hiding, sent)
    assert "rule hide-shell" in run.stdout + run.stderr
    sent["command"] = shlex.join(through(hiding, "ls"))
    run = guard(hiding, sent)
    assert "rule hide-shell" not in run.stdout + run.stderr


def test_what_is_gone_and_what_is_held(box, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "vault").mkdir()
    (tmp_path / "one.txt").write_text("1\n")
    (runtime.state(box) / "hide.txt").write_text(
        "~/vault  # mine\n\n# a remark\n~/one.txt\n~/not-there\n")  # fmt: skip
    key = Path(json.loads((box / "kernel.json").read_text())["key"]).resolve()
    gone, held = runtime.hide_places(box)
    assert gone == [box.resolve(), runtime.state(box).resolve(),
                    tmp_path / "vault", tmp_path / "one.txt", key]  # fmt: skip
    assert held == [runtime.HERE.resolve(), runtime.WILLOW.resolve()]
    args, why = runtime.hide_argv(box, tmp_path, "echo hi")
    assert why == "" and args[:4] == ["bwrap", "--dev-bind", "/", "/"]
    assert args[-6:] == ["--chdir", str(tmp_path), "--", "bash", "-c", "echo hi"]
    text = " ".join(args)
    assert (
        f"--tmpfs {tmp_path / 'vault'}" in text and f"--tmpfs {box.resolve()}" in text
    )
    assert f"--ro-bind /dev/null {tmp_path / 'one.txt'}" in text
    assert f"--ro-bind /dev/null {key}" in text
    assert text.index("--ro-bind " + str(runtime.HERE)) < text.index("--tmpfs")
    # nothing runs in a folder that is gone, and the machine can't be
    assert runtime.hide_argv(box, tmp_path / "vault", "ls")[0] is None
    assert runtime.hide_argv(box, box, "ls")[0] is None
    (runtime.state(box) / "hide.txt").write_text("/\n")
    assert "whole machine" in runtime.hide_argv(box, tmp_path, "ls")[1]


def test_the_door_run_wrong_or_without_bubblewrap_runs_nothing(box, tmp_path):
    for argv in ([], ["--box", str(box)], ["--command", "ls", "--box", str(box)]):
        run = subprocess.run([sys.executable, str(DOOR), *argv], capture_output=True,
                             text=True, check=False)  # fmt: skip
        assert run.returncode == 126 and "usage: hide.py" in run.stderr
    run = door(box, "echo ran > ran.txt", tmp_path,
               env={**os.environ, "PATH": str(tmp_path)})  # fmt: skip
    assert run.returncode == 126 and "bubblewrap (bwrap) isn't installed" in run.stderr
    assert not (tmp_path / "ran.txt").exists()


@SANDBOX
def test_through_the_door_all_is_as_it_was_but_the_box_is_gone(box, tmp_path):
    home = tmp_path / "home"
    (home / "vault").mkdir(parents=True)
    (home / "vault" / "other").write_text("another\n")
    (home / "one.txt").write_text("1\n")
    (home / "notes.txt").write_text("milk\n")
    (runtime.state(box) / "hide.txt").write_text("~/vault\n~/one.txt\n")
    record = box / "record.jsonl"
    key = json.loads((box / "kernel.json").read_text())["key"]
    before = record.read_text()
    probe = (
        "pwd; echo $MINE; cat ~/notes.txt; echo made > ~/made.txt; "
        f"cat {record} {key} ~/vault/other ~/one.txt 2>/dev/null | wc -c; "
        f"find {box} {runtime.state(box)} ~/vault -mindepth 1 2>/dev/null | wc -l; "
        f"(echo x >> {runtime.HERE}/FILES.md) 2>/dev/null && echo changed || echo held; "
        f"head -c 7 {runtime.HERE}/FILES.md; echo; echo oops >&2; exit 3"
    )
    run = door(box, probe, home, env={**os.environ, "HOME": str(home), "MINE": "kept"})
    assert (run.returncode, run.stderr) == (3, "oops\n")
    first = (runtime.HERE / "FILES.md").read_text()[:7]
    assert run.stdout.splitlines() == [
        str(home), "kept", "milk", "0", "0", "held", first]  # fmt: skip
    assert (home / "made.txt").read_text() == "made\n"  # home is theirs, to write too
    assert record.read_text() == before  # the session's own shell: no row
    run = door(box, "ls", box)
    assert run.returncode == 126 and "is hidden from an assistant's shell" in run.stderr
