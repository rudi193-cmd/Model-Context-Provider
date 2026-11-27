"""kart-shell: with it on, a shell command the guards allow is handed back
to the host as the same command through doors/shell.py, which runs it in
Willow's kart sandbox. Off until the person turns it on."""

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

import runtime

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "doors" / "guard.py"
DOOR = ROOT / "doors" / "shell.py"
#: whether the pinned Willow's kart has `shell` yet
PINNED = "kart.py shell " in (runtime.WILLOW / runtime.KART).read_text()


def guard(box, sent, project=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    if project is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project)
    return subprocess.run([sys.executable, str(GUARD), "--box", str(box)],
                          input=json.dumps(sent), capture_output=True, text=True,
                          check=False, env=env)  # fmt: skip


def bash(command, cwd, **given):
    return {"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(cwd),
            "tool_name": "Bash", "tool_input": {"command": command, **given}}  # fmt: skip


def cursor(event, **fields):
    return {"hook_event_name": event, "conversation_id": "c1", **fields}


@pytest.fixture
def work(box, tmp_path):
    """A project with a folder in it, and kart-shell turned on."""
    (tmp_path / "proj" / "src").mkdir(parents=True)
    runtime.hooks_set(box, {"on": ["kart-shell"]})
    yield tmp_path / "proj"
    (runtime.state(box) / "hooks.txt").unlink(missing_ok=True)


def through(box, project, cwd, seconds, command):
    return [sys.executable, str(DOOR), "--box", str(box), "--project", str(project),
            "--cwd", str(cwd), "--timeout", str(seconds), "--command", command]  # fmt: skip


def test_off_a_command_is_allowed_as_it_came(box, tmp_path):
    run = guard(box, bash("ls -la", tmp_path), project=tmp_path)
    assert (run.returncode, run.stdout) == (0, "")


def test_on_an_allowed_command_is_handed_back_through_the_door(box, work):
    sent = bash("echo '```' && ls", work / "src", description="list", timeout=7500)
    run = guard(box, sent, project=work)
    assert run.returncode == 0, run.stderr
    out = json.loads(run.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse" and "permissionDecision" not in out
    new = out["updatedInput"]
    # the whole input, as the host wants it, with only the command changed
    assert {k: v for k, v in new.items() if k != "command"} == {"description": "list", "timeout": 7500}  # fmt: skip
    assert shlex.split(new["command"]) == through(box, work, work / "src", 8, "echo '```' && ls")  # fmt: skip


def test_how_long_and_where_follow_what_the_host_said(box, work, tmp_path):
    def words(sent, project=work):
        run = guard(box, sent, project=project)
        return shlex.split(json.loads(run.stdout)["hookSpecificOutput"]["updatedInput"]["command"])  # fmt: skip

    assert words(bash("ls", work))[2:10] == through(box, work, work, 120, "")[2:10]
    assert words(bash("ls", work, run_in_background=True, timeout=5000))[9] == "1800"
    assert words(bash("ls", work, timeout=True))[9] == "120"
    assert words(bash("ls", work, timeout=1))[9] == "1"
    # a folder outside the project the session began in: it starts in the project
    assert words(bash("ls", tmp_path))[5:8] == [str(work), "--cwd", str(work)]
    # no project said: the folder the call came from is it
    assert words(bash("ls", work / "src"), project=None)[5:8] == [str(work / "src"), "--cwd", str(work / "src")]  # fmt: skip


def test_a_blocked_command_stays_blocked_and_nothing_is_handed_back(box, work):
    run = guard(box, bash(f"cat {box.parent / 'test.key'}", work), project=work)
    assert run.returncode == 2 and "rule key" in run.stderr and run.stdout == ""
    run = guard(box, bash(f"python3 {ROOT / 'doors' / 'pipe.py'} --box x", work), project=work)  # fmt: skip
    assert run.returncode == 2 and "own-door" in run.stderr and run.stdout == ""


def test_other_tools_are_judged_and_left_as_they_came(box, work):
    sent = {"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(work),
            "tool_name": "Glob", "tool_input": {"pattern": "*.md"}}  # fmt: skip
    run = guard(box, sent, project=work)
    assert (run.returncode, run.stdout) == (0, "")


def test_a_host_that_names_no_folder_has_its_command_blocked(box, work):
    sent = bash("ls", work)
    del sent["cwd"]
    run = guard(box, sent)
    assert run.returncode == 2 and "rule kart-shell" in run.stderr and run.stdout == ""


def test_a_command_already_through_the_door_is_judged_by_what_is_inside(box, work):
    """Cursor asks twice of one command: once where it can be rewritten, and
    again before the shell runs it, by then through the door."""
    ok = shlex.join(through(box, work, work, 120, "ls -la"))
    run = guard(box, bash(ok, work), project=work)
    assert (run.returncode, run.stdout) == (0, "")
    bad = shlex.join(through(box, work, work, 120, f"cat {box.parent / 'test.key'}"))
    run = guard(box, bash(bad, work), project=work)
    assert run.returncode == 2 and "rule key" in run.stderr


@pytest.mark.parametrize("change", [
    {2: "--project"}, {3: "/tmp"}, {5: "/"}, {7: "/tmp"}, {9: "soon"}, {1: "/tmp/shell.py"},
])  # fmt: skip
def test_a_door_this_runtime_didnt_write_is_a_command_like_any_other(box, work, change):
    """Another box, another project, a folder outside it: not the door as it
    is written here, so it is judged whole and sent through the real one."""
    words = through(box, work, work, 120, "ls")
    for i, word in change.items():
        words[i] = word
    forged = shlex.join(words)
    run = guard(box, bash(forged, work), project=work)
    if run.returncode == 2:  # it names the box: the guard's own rule
        assert "blocked:" in run.stderr
        return
    new = json.loads(run.stdout)["hookSpecificOutput"]["updatedInput"]["command"]
    assert shlex.split(new) == through(box, work, work, 120, forged)


def test_cursors_shell_is_rewritten_where_it_can_be_and_held_where_it_cant(box, work):
    pre = cursor("preToolUse", tool_name="Shell", workspace_roots=[str(work)],
                 tool_input={"command": "ls", "working_directory": str(work / "src")})  # fmt: skip
    run = guard(box, pre)
    assert run.returncode == 0, run.stderr
    new = json.loads(run.stdout)["updated_input"]
    assert new["working_directory"] == str(work / "src")
    assert shlex.split(new["command"]) == through(box, work, work / "src", 120, "ls")
    # before the shell runs: through the door it passes, bare it is blocked
    late = cursor("beforeShellExecution", command=new["command"],
                  cwd=str(work / "src"), workspace_roots=[str(work)])  # fmt: skip
    run = guard(box, late)
    assert (run.returncode, run.stdout) == (0, "")
    late["command"] = "ls"
    run = guard(box, late)
    assert run.returncode == 2 and "rule kart-shell" in run.stderr and run.stdout == ""


def test_a_failed_command_is_kept_as_the_command_inside_the_door(box, work):
    """hook-errors counts a command that failed twice by its words: the same
    words whether the host says them bare or through the door."""
    inner = "false # kart-shell-probe"
    wrapped = shlex.join(through(box, work, work, 120, inner))
    for _ in range(2):
        after = {"hook_event_name": "PostToolUse", "session_id": "s9", "cwd": str(work),
                 "tool_name": "Bash", "tool_input": {"command": wrapped},
                 "tool_response": {"exit_code": 1}}  # fmt: skip
        assert guard(box, after, project=work).returncode == 0
    sent = bash(inner, work)
    sent["session_id"] = "s9"
    run = guard(box, sent, project=work)
    assert run.returncode == 2 and "failed" in run.stderr


# ── the door ────────────────────────────────────────────────────────────────
@pytest.fixture
def fake_kart(box, tmp_path, monkeypatch):
    """Willow's kart stood in for by a program that writes down what it was
    asked and answers as told: the door's own part, without a sandbox."""
    asked, says = tmp_path / "asked.json", tmp_path / "says.txt"
    kart = tmp_path / "kart.py"
    kart.write_text("import json, sys, pathlib\n"
                    f"pathlib.Path({str(asked)!r}).write_text(json.dumps(sys.argv[1:]))\n"
                    f"code, _, out = pathlib.Path({str(says)!r}).read_text().partition('\\n')\n"
                    "print(out, end=''); print('refused: no bubblewrap', file=sys.stderr)\n"
                    "sys.exit(int(code))\n")  # fmt: skip
    monkeypatch.setattr(runtime, "KART", str(kart))
    monkeypatch.setattr(runtime, "kart_python", lambda box: sys.executable)

    def run(code, said):
        says.write_text(
            f"{code}\n{said if isinstance(said, str) else json.dumps(said)}"
        )
        got = runtime.kart_shell(box, str(tmp_path), str(tmp_path), "ls", 9)
        return got, json.loads(asked.read_text())

    return run


def test_the_door_gives_back_what_the_command_printed_and_how_it_ended(fake_kart, box):
    got, asked = fake_kart(42, {"returncode": 3, "stdout": "out", "stderr": "oops",
                                "status": "failed"})  # fmt: skip
    assert got == (3, "out", "oops")
    hidden = f"{runtime.state(box)},{runtime.HERE},{runtime.WILLOW}"
    assert asked[0] == "shell" and asked[1:3] == ["--box", str(box)]
    assert asked[-2:] == ["--hide", hidden] and "--hold" not in asked
    assert asked[asked.index("--timeout") + 1] == "9"
    got, _ = fake_kart(0, {"returncode": 0, "stdout": "", "stderr": "", "status": "completed"})  # fmt: skip
    assert got == (0, "", "")


def test_the_door_says_when_nothing_ran_or_it_was_ended(fake_kart):
    got, _ = fake_kart(2, "")
    assert (
        got[0] == 126 and "nothing ran in the sandbox: refused: no bubblewrap" in got[2]
    )
    got, _ = fake_kart(42, {"returncode": None, "stdout": "part", "stderr": "",
                            "status": "failed", "how": "timeout"})  # fmt: skip
    assert got[:2] == (124, "part") and got[2].endswith("timeout")
    got, _ = fake_kart(42, {"returncode": None, "stdout": "", "stderr": "", "status": "failed",
                            "how": "cgroup_setup_failed"})  # fmt: skip
    assert got[0] == 126 and "cgroup_setup_failed" in got[2]
    got, _ = fake_kart(0, "[1, 2]")
    assert got[0] == 126


def test_a_willow_inside_the_project_is_held_read_only_not_hidden(fake_kart, box, monkeypatch, tmp_path):  # fmt: skip
    (tmp_path / "willow").mkdir()
    monkeypatch.setattr(runtime, "WILLOW", tmp_path / "willow")
    _, asked = fake_kart(0, {"returncode": 0, "stdout": "", "stderr": "", "status": "completed"})  # fmt: skip
    assert asked[-4:] == ["--hide", f"{runtime.state(box)},{runtime.HERE}",
                          "--hold", str(tmp_path / "willow")]  # fmt: skip


def test_the_door_run_wrong_says_how_and_runs_nothing(box):
    for argv in (
        [],
        ["--box", str(box)],
        through(box, "/tmp", "/tmp", "soon", "ls")[2:],
    ):
        run = subprocess.run([sys.executable, str(DOOR), *argv], capture_output=True,
                             text=True, check=False)  # fmt: skip
        assert run.returncode == 126 and "usage: shell.py" in run.stderr


@pytest.mark.skipif(not PINNED, reason="the pinned Willow's kart has no `shell` yet")
def test_through_the_door_a_command_works_in_the_project_and_never_sees_the_record(box, work):  # fmt: skip
    record = box / "record.jsonl"
    before = record.read_text()
    probe = (f"echo made > new.txt; cat new.txt; cat {record} 2>/dev/null | wc -c; "
             f"ls {runtime.state(box)} 2>/dev/null | wc -l; echo oops >&2; exit 3")  # fmt: skip
    run = subprocess.run(through(box, work, work, 60, probe), capture_output=True,
                         text=True, check=False)  # fmt: skip
    if "Kartikeya isn't installed" in run.stderr:
        pytest.skip("this Python has no Kartikeya")
    assert (run.returncode, run.stdout, run.stderr) == (3, "made\n0\n0\n", "oops\n")
    assert (work / "new.txt").read_text() == "made\n"
    assert record.read_text() == before  # the session's own shell: no row
