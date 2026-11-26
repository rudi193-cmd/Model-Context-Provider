"""The person's switch for the hooks around what an assistant does, as the
tool groups have one: each on unless they turn it off, kept beside the box.
Fewer hooks, fewer rows on the record. The guard of the key and the record
is never off, and nothing here is a model's to switch."""

import json

import runtime


def hooks(box, arg=None):
    return runtime.call(box, "hooks", arg, door="pipe")


def on(box):
    return {h["hook"]: h["on"] for h in hooks(box)["hooks"]}


def test_every_hook_is_on_until_the_person_turns_one_off(box):
    got = hooks(box)
    assert got["state"] == "listed" and all(h["on"] for h in got["hooks"])
    assert [h["hook"] for h in got["hooks"]] == list(runtime.HOOKS)
    assert all(h["what"] and h["why"] for h in got["hooks"])
    assert not (runtime.state(box) / "hooks.txt").exists()  # asked, nothing written


def test_turned_off_it_stays_off_and_says_why(box):
    hooks(box, {"off": ["hook-read-first", "hook-handoff"]})
    assert on(box)["hook-read-first"] is False and on(box)["hook-handoff"] is False
    why = {h["hook"]: h["why"] for h in hooks(box)["hooks"]}
    assert why["hook-read-first"] == "you turned it off"
    hooks(box, {"on": "hook-read-first"})
    assert on(box)["hook-read-first"] is True and on(box)["hook-handoff"] is False


def test_the_guard_of_the_key_is_never_off(box):
    got = hooks(box, {"off": ["hook-guard"]})
    assert got["state"] == "refused" and got["code"] == "hooks_refused"
    (runtime.state(box) / "hooks.txt").write_text("-hook-guard\n")  # by hand
    assert on(box)["hook-guard"] is True
    assert "hook-guard" in [n for n, _ in runtime.guards(box)]


def test_a_name_that_isnt_a_hook_or_both_ways_at_once_is_refused(box):
    assert hooks(box, {"off": ["no-such-hook"]})["code"] == "hooks_refused"
    got = hooks(box, {"on": ["hook-errors"], "off": ["hook-errors"]})
    assert got["code"] == "hooks_refused"
    assert not (runtime.state(box) / "hooks.txt").exists()


def test_a_guard_turned_off_isnt_asked(box):
    before = [n for n, _ in runtime.guards(box)]
    assert "hook-read-first" in before and "hook-leaks" in before
    hooks(box, {"off": ["hook-read-first", "hook-leaks"]})
    after = [n for n, _ in runtime.guards(box)]
    assert after == [n for n in before if n not in ("hook-read-first", "hook-leaks")]


def edit_unread(box, tmp_path):
    f = tmp_path / "never-read.txt"
    f.write_text("x\n")
    return {"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": "s1",
            "cwd": str(tmp_path), "tool_input": {"file_path": str(f),
            "old_string": "x", "new_string": "y"}}  # fmt: skip


def test_an_edit_of_a_file_not_read_is_let_by_once_read_first_is_off(box, tmp_path):
    sent = edit_unread(box, tmp_path)
    assert runtime.call(box, "event", sent, door="guard")["state"] == "blocked"
    hooks(box, {"off": ["hook-read-first"]})
    assert runtime.call(box, "event", sent, door="guard")["state"] == "allowed"


def kinds(box):
    rows = (box / "record.jsonl").read_text().splitlines()
    return [json.loads(r).get("kind") for r in rows]


def test_a_hook_turned_off_writes_nothing_on_the_record(box, tmp_path):
    stop = {"hook_event_name": "Stop", "session_id": "s1", "cwd": str(tmp_path)}
    failed = {"hook_event_name": "PostToolUseFailure", "session_id": "s1",
              "cwd": str(tmp_path), "tool_name": "Bash",
              "tool_input": {"command": "false"}, "error": "Exit code 1"}  # fmt: skip
    hooks(box, {"off": ["hook-handoff", "hook-errors"]})
    n = len(kinds(box))
    assert runtime.call(box, "event", stop, door="guard")["state"] == "empty"
    assert runtime.call(box, "event", failed, door="guard")["state"] == "empty"
    assert len(kinds(box)) == n
    hooks(box, {"on": ["hook-handoff", "hook-errors"]})
    runtime.call(box, "event", stop, door="guard")
    runtime.call(box, "event", failed, door="guard")
    assert {"hook-handoff", "hook-errors"} <= set(kinds(box)[n:])


def test_prompt_context_off_asks_the_files_nothing(box):
    asked = "when does the first frost come"
    assert runtime.call(box, "context", asked, door="hook")["state"] != "off"
    n = len(kinds(box))
    hooks(box, {"off": ["prompt-context"]})
    assert runtime.call(box, "context", asked, door="hook") == {"state": "off"}
    assert len(kinds(box)) == n  # no bite


def test_a_model_has_no_switch(box):
    got = runtime.call(box, "hooks", {"off": ["hook-leaks"]}, door="mcp")
    assert got["state"] == "refused" and got["code"] == "no_verb"
    assert on(box)["hook-leaks"] is True
