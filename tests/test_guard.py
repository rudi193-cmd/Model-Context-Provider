"""The guard door: Willow's hooks around what an assistant does, decided by
the runtime, carried by a door that decides nothing."""

import json
import subprocess
import sys
from pathlib import Path

import runtime

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "doors" / "guard.py"
HOOK = ROOT / "doors" / "hook.py"
A_KEY = "sk-ant-api03-" + "A1b2C3d4" * 6


def guard(box, sent):
    return subprocess.run(
        [sys.executable, str(GUARD), "--box", str(box)],
        input=sent if isinstance(sent, str) else json.dumps(sent),
        capture_output=True, text=True, check=False,
    )  # fmt: skip


def before(tool, session="s1", **given):
    return {"hook_event_name": "PreToolUse", "session_id": session,
            "tool_name": tool, "tool_input": given}  # fmt: skip


def after(command, code, session="s1"):
    return {"hook_event_name": "PostToolUse", "session_id": session,
            "tool_name": "Bash", "tool_input": {"command": command},
            "tool_response": {"exit_code": code}}  # fmt: skip


def rows(box, kind):
    lines = (box / "record.jsonl").read_text().splitlines()
    return [r for r in map(json.loads, lines) if r.get("kind") == kind]


def test_a_call_that_names_the_key_is_blocked_and_says_which_rule(box, tmp_path):
    run = guard(box, before("Read", file_path=str(tmp_path / "test.key")))
    assert run.returncode == 2
    assert "rule key" in run.stderr and run.stdout == ""


def test_a_write_into_the_record_is_blocked(box):
    run = guard(box, before("Write", file_path=str(box / "record.jsonl"), content="x"))
    assert run.returncode == 2 and "rule box-write" in run.stderr
    run = guard(box, before("Bash", command=f"rm {box}/record.jsonl"))
    assert run.returncode == 2 and "rule box-write" in run.stderr


def test_a_secret_in_what_is_written_is_blocked_and_never_shown(box, tmp_path):
    run = guard(box, before("Write", file_path=str(tmp_path / "n.md"), content=A_KEY))
    assert run.returncode == 2 and "a key" in run.stderr
    assert A_KEY not in run.stderr + run.stdout
    sent = (runtime.state(box) / "sent.jsonl").read_text()
    assert A_KEY not in sent and '"by": "hook-leaks"' in sent


def test_an_edit_waits_for_a_read_of_the_file_as_it_is_now(box, tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("one\n")
    edit = before("Edit", file_path=str(f), old_string="one", new_string="two")
    run = guard(box, edit)
    assert run.returncode == 2 and "never read" in run.stderr
    assert guard(box, before("Read", file_path=str(f))).returncode == 0
    assert guard(box, edit).returncode == 0
    f.write_text("three\n")  # changed since it was read
    assert "changed" in guard(box, edit).stderr


def test_a_new_file_needs_no_read(box, tmp_path):
    run = guard(box, before("Write", file_path=str(tmp_path / "new.md"), content="x"))
    assert (run.returncode, run.stderr) == (0, "")


def test_the_third_try_of_a_command_that_failed_twice_is_blocked(box):
    cmd = before("Bash", command="make test")
    for _ in range(2):
        assert guard(box, cmd).returncode == 0
        assert guard(box, after("make test", 1)).returncode == 0
    run = guard(box, cmd)
    assert run.returncode == 2 and "failed 2 times" in run.stderr
    assert "make test" not in (box / "record.jsonl").read_text()  # by hash only
    assert guard(box, before("Bash", "s2", command="make test")).returncode == 0


def test_a_command_that_failed_twice_in_claude_code_is_blocked_the_third_time(box):
    """What Claude Code 2.1 sends for a failed command, captured from a real
    session on 2026-11-17: PostToolUseFailure, the exit code only in error."""
    failed = {"hook_event_name": "PostToolUseFailure", "session_id": "s1",
              "tool_name": "Bash", "tool_input": {"command": "ls /no/such"},
              "error": "Exit code 2\nls: cannot access '/no/such': No such file",
              "is_interrupt": False}  # fmt: skip
    cmd = before("Bash", command="ls /no/such")
    for _ in range(2):
        assert guard(box, cmd).returncode == 0
        assert guard(box, failed).returncode == 0
    run = guard(box, cmd)
    assert run.returncode == 2 and "failed 2 times with exit 2" in run.stderr


def test_a_command_the_person_denied_is_blocked_only_once_they_deny_it(box):
    push = before("Bash", command="git push --force origin main")
    assert guard(box, push).returncode == 0  # no deny.txt: that guard isn't asked
    (runtime.state(box) / "deny.txt").write_text("# mine\ngit push --force\n")
    run = guard(box, push)
    assert run.returncode == 2 and "matches the rule" in run.stderr
    assert guard(box, before("Bash", command="git push origin main")).returncode == 0


def test_a_guard_that_cannot_run_lets_nothing_through(box, monkeypatch):
    (runtime.state(box) / "deny.txt").write_text('rm "unclosed\n')
    run = guard(box, before("Bash", command="ls"))
    assert run.returncode == 2 and "couldn't run" in run.stderr
    monkeypatch.setattr(runtime, "HOOK_GUARD", "no/such/guard.py")
    got = runtime.call(box, "event", before("Bash", command="ls"), door="guard")
    assert (got["state"], got["code"]) == ("refused", "guard_failed")


def test_what_it_cannot_read_it_does_not_let_through(box):
    for stdin in ["", "not json", "[1, 2]", "5", "{" * 100000]:
        run = guard(box, stdin)
        assert run.returncode == 2 and run.stdout == "", stdin[:20]
        assert "Traceback" not in run.stderr


def test_an_allowed_call_says_nothing_and_is_not_on_the_sent_log(box):
    run = guard(box, before("Bash", command="ls"))
    assert (run.returncode, run.stdout, run.stderr) == (0, "", "")
    assert not (runtime.state(box) / "sent.jsonl").exists()


def test_a_turns_end_is_kept_and_the_next_session_is_told_once(box, tmp_path):
    stop = {"hook_event_name": "Stop", "session_id": "s1", "cwd": str(tmp_path)}
    assert (guard(box, stop).returncode, guard(box, stop).stdout) == (0, "")
    start = {"hook_event_name": "SessionStart", "session_id": "s2"}
    said = json.loads(guard(box, start).stdout)["hookSpecificOutput"]
    assert said["hookEventName"] == "SessionStart"
    assert f"session s1 ended in {tmp_path}" in said["additionalContext"]
    assert guard(box, start).stdout == ""  # once a session
    assert guard(box, {**start, "session_id": "s1"}).stdout == ""  # not its own


def test_a_turn_can_always_end(box, monkeypatch):
    stop = {"hook_event_name": "Stop", "session_id": "s1"}
    (box / "record.jsonl").write_text("not a record\n")
    assert guard(box, stop).returncode == 0
    monkeypatch.setattr(runtime, "PIN", box / "no-pin.json")
    assert runtime.call(box, "event", stop, door="guard")["state"] == "refused"


def test_a_session_starts_with_a_count_of_what_waits_and_no_words(box):
    start = {"hook_event_name": "SessionStart", "session_id": "s1"}
    assert guard(box, start).stdout == ""  # nothing waits: nothing said
    runtime.read(box, "when does the first frost come")
    runtime.propose(box)
    said = json.loads(guard(box, start).stdout)["hookSpecificOutput"]["additionalContext"]  # fmt: skip
    assert "1 thing waiting on their seal" in said
    for word in ("frost", "October", "garden", "proposal:"):
        assert word not in said
    compact = guard(box, {"hook_event_name": "PreCompact"}).stdout
    assert compact.startswith("Before this conversation is summarised")
    assert "1 thing waiting" in compact and "frost" not in compact


def test_what_the_person_set_aside_is_not_counted(box):
    runtime.read(box, "when does the first frost come")
    runtime.later(box, runtime.propose(box)["seal"])
    assert guard(box, {"hook_event_name": "PreCompact"}).stdout == ""


def prompt(box, text, session="s1"):
    return subprocess.run(
        [sys.executable, str(HOOK), "--box", str(box)],
        input=json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": text,
                          "session_id": session}),
        capture_output=True, text=True, check=False,
    )  # fmt: skip


def test_a_correction_is_proposed_for_the_persons_seal_and_never_sealed(box):
    assert prompt(box, "when does the first frost come").returncode == 0
    assert rows(box, "hook-feedback") == []  # an ordinary ask is no correction
    run = prompt(box, "No, I said the frost comes in late October")
    assert run.returncode == 0
    (row,) = rows(box, "hook-feedback")
    owed = runtime.waiting(box)["waiting"]
    assert [w["seal"] for w in owed] == [row["subject"]]
    assert owed[0]["path"].startswith("feedback/")


def test_the_read_for_a_prompt_is_the_one_a_propose_then_scopes(box):
    """A correction is asked of the files too; the question's own read comes
    after it, so what is proposed next is what the question found."""
    from test_leave import seal

    q = "No, I said when does the first frost come"
    prompt(box, q)
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "context", q, door="hook")
    assert page["state"] == "left" and "late October" in page["page"]


def test_a_new_sessions_first_prompt_is_told_where_the_last_ended(box, tmp_path):
    guard(box, {"hook_event_name": "Stop", "session_id": "s1", "cwd": str(tmp_path)})
    out = prompt(box, "what colour is the boat", session="s2").stdout
    assert f"session s1 ended in {tmp_path}" in out
    assert prompt(box, "what colour is the boat", session="s2").stdout == ""


def test_the_hosts_doors_have_two_verbs_and_none_of_a_models(box):
    assert sorted(runtime.VERBS["host"]) == ["context", "event"]
    for door in ("hook", "guard"):
        for verb in ("read", "propose", "leave", "answer", "draft", "seal"):
            got = runtime.call(box, verb, "x", door=door)
            assert (got["state"], got["code"]) == ("refused", "no_verb")
    assert runtime.call(box, "event", {}, door="mcp")["code"] == "no_verb"
    assert runtime.call(box, "event", {}, door="pipe")["code"] == "no_verb"
