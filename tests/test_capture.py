"""capture: one thing handed in to keep, for the person's seal, and the one
place it is kept once they seal it."""

import json

from test_guard import guard
from test_leave import seal

import runtime

FROST = "when does the first frost come"
NOTE = "The dahlias did best in the bed by the wall."


def test_a_models_note_waits_on_the_seal_and_is_kept_nowhere_until_then(box):
    got = runtime.call(box, "capture", NOTE, door="mcp")
    assert got["state"] == "waiting" and got["path"].startswith("captured/note-")
    assert not (box / "written").exists()
    assert [w["seal"] for w in runtime.waiting(box)["waiting"]] == [got["seal"]]


def test_sealed_it_is_in_the_one_place_and_the_person_reads_it_there(box):
    got = runtime.call(box, "capture", NOTE, door="mcp")
    seal(box, got["seal"])
    assert (box / "written" / got["path"]).read_text() == NOTE + "\n"
    kept = runtime.call(box, "captured", door="pipe")
    assert kept["kept"] == [{"path": got["path"], "words": NOTE + "\n"}]
    assert kept["waiting"] == []


def test_a_model_cannot_read_what_was_kept(box):
    seal(box, runtime.call(box, "capture", NOTE, door="mcp")["seal"])
    assert runtime.call(box, "captured", door="mcp")["code"] == "no_verb"
    for verb in ("read", "context"):
        got = runtime.call(box, verb, "which bed did the dahlias do best in", door="mcp")  # fmt: skip
        assert "wall" not in json.dumps(got)


def test_a_capture_never_stands_in_for_a_page_sealed_for_a_question(box):
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    seal(box, runtime.call(box, "capture", NOTE, door="mcp")["seal"])
    page = runtime.call(box, "context", FROST, door="hook")
    assert page["state"] == "left" and "late October" in page["page"]


def test_a_propose_after_a_capture_scopes_no_earlier_read(box):
    runtime.call(box, "read", FROST, door="mcp")
    runtime.call(box, "capture", NOTE, door="mcp")
    got = runtime.call(box, "propose", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "nothing_to_scope")


def test_the_same_note_is_handed_in_once_and_an_empty_one_never(box):
    assert runtime.call(box, "capture", NOTE, door="mcp")["state"] == "waiting"
    assert runtime.call(box, "capture", NOTE, door="mcp")["code"] == "capture_refused"
    assert runtime.call(box, "capture", "", door="mcp")["code"] == "capture_refused"


def test_a_note_handed_in_is_on_the_sent_log_and_reads_as_what_it_is(box):
    runtime.call(box, "capture", NOTE, door="mcp")
    (line,) = runtime.call(box, "shared", door="pipe")["lines"]
    assert "a note handed in to keep" in line
    assert NOTE not in (runtime.state(box) / "sent.jsonl").read_text()


def test_a_moment_the_person_names_is_kept_whole_for_their_seal(box):
    failed = {"hook_event_name": "PostToolUseFailure", "session_id": "s1",
              "tool_name": "Bash", "tool_input": {"command": "make test"},
              "error": "Exit code 2"}  # fmt: skip
    assert guard(box, failed).returncode == 0
    assert runtime.waiting(box)["state"] == "empty"  # not asked for: not kept
    (runtime.state(box) / "capture.txt").write_text("PostToolUseFailure\n")
    run = guard(box, failed)
    assert (run.returncode, run.stdout) == (0, "")  # the model is told nothing
    (owed,) = runtime.call(box, "captured", door="pipe")["waiting"]
    assert owed["path"].startswith("captured/event-posttoolusefailure-")
    seal(box, owed["seal"])
    (kept,) = runtime.call(box, "captured", door="pipe")["kept"]
    assert json.loads(kept["words"]) == failed


def test_a_moment_being_kept_never_changes_what_the_guard_decides(box):
    (runtime.state(box) / "capture.txt").write_text("PreToolUse\n")
    call = {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": "Write",
            "tool_input": {"file_path": str(box / "record.jsonl"), "content": "x"}}  # fmt: skip
    run = guard(box, call)
    assert run.returncode == 2 and "rule box-write" in run.stderr
