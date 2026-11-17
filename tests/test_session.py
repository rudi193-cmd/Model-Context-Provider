"""One seal a session: the session door closes each session as one proposal
(Willow's session-seal), and tells the person, never the model, what waits."""

import json
import subprocess
import sys
from pathlib import Path

from test_leave import seal

import runtime

DOOR = Path(__file__).resolve().parents[1] / "doors" / "session.py"
FROST = "when does the first frost come"


def door(box, stdin):
    return subprocess.run(
        [sys.executable, str(DOOR), "--box", str(box)],
        input=stdin, capture_output=True, text=True, check=False,
    )  # fmt: skip


def event(box, name, **more):
    return door(box, json.dumps({"hook_event_name": name, **more}))


def a_session(box):
    """What a model does in a session: reads, and proposes what it read."""
    runtime.call(box, "read", FROST, door="mcp")
    return runtime.call(box, "propose", door="mcp")["seal"]


def test_closing_a_session_proposes_it_for_one_seal(box):
    a_session(box)
    got = runtime.call(box, "close", door="pipe")
    assert got["state"] == "waiting" and got["seal"].startswith("proposal:")
    (w,) = [w for w in runtime.waiting(box)["waiting"] if w["seal"] == got["seal"]]
    assert w["path"].startswith("sessions/") and "these were my actions" in w["claim"]


def test_closing_proposes_and_never_seals(box):
    a_session(box)
    subj = runtime.call(box, "close", door="pipe")["seal"]
    assert subj in {w["seal"] for w in runtime.waiting(box)["waiting"]}
    seal(box, subj)  # the person's act, with their key
    assert subj not in {w["seal"] for w in runtime.waiting(box)["waiting"]}


def test_a_session_with_nothing_since_the_last_close_has_nothing_to_seal(box):
    a_session(box)
    runtime.call(box, "close", door="pipe")
    assert runtime.call(box, "close", door="pipe") == {"state": "empty"}


def test_after_a_close_a_model_reads_again_before_it_can_propose(box):
    a_session(box)
    runtime.call(box, "close", door="pipe")
    got = runtime.call(box, "propose", door="mcp")
    assert got["state"] == "refused" and got["code"] == "nothing_to_scope"
    assert a_session(box)  # a fresh read proposes again


def test_what_waits_is_said_in_one_line_sessions_counted_apart(box):
    a_session(box)
    runtime.call(box, "close", door="pipe")
    got = runtime.call(box, "owed", door="pipe")
    assert (got["state"], got["sessions"], got["other"]) == ("waiting", 1, 1)
    assert "1 session and 1 page or sentence" in got["say"]
    assert "pipe.py" in got["say"] and '{"waiting": true}' in got["say"]


def test_nothing_waits_on_a_new_box(box):
    assert runtime.call(box, "owed", door="pipe")["state"] == "empty"


def test_a_model_can_neither_close_a_session_nor_see_what_waits(box):
    for verb in ("close", "owed"):
        assert runtime.call(box, verb, door="mcp")["state"] == "refused"
        assert runtime.call(box, verb, door="hook")["state"] == "refused"
    assert {"close", "owed"}.isdisjoint(runtime.VERBS["model"])


def test_the_door_closes_at_session_end_and_says_nothing(box):
    a_session(box)
    run = event(box, "SessionEnd", reason="prompt_input_exit")
    assert (run.returncode, run.stdout) == (0, "")
    assert runtime.call(box, "owed", door="pipe")["sessions"] == 1


def test_at_session_start_the_person_is_told_and_the_turn_gets_nothing(box):
    a_session(box)
    event(box, "SessionEnd")
    run = event(box, "SessionStart", source="startup")
    assert run.returncode == 0
    (line,) = run.stdout.splitlines()
    doc = json.loads(line)  # JSON, so Claude Code puts none of it in the turn
    assert list(doc) == ["systemMessage"]  # shown to the person only
    assert "Waiting on your seal" in doc["systemMessage"]
    assert "October" not in run.stdout and "garden" not in run.stdout


def test_at_session_start_with_nothing_waiting_it_says_nothing(box):
    assert event(box, "SessionStart", source="startup").stdout == ""


def test_whatever_it_is_sent_it_exits_0_and_puts_nothing_in_the_turn(box):
    for stdin in ["", "not json", "[1, 2]", '{"hook_event_name": null}', "{" * 100000]:
        run = door(box, stdin)
        assert (run.returncode, run.stdout) == (0, ""), stdin[:20]
    assert runtime.call(box, "owed", door="pipe")["state"] == "empty"
