import json
import subprocess
import sys
from pathlib import Path

from test_leave import seal

import runtime

HOOK = Path(__file__).resolve().parents[1] / "doors" / "hook.py"
FROST = "when does the first frost come"


def hook(box, stdin):
    return subprocess.run(
        [sys.executable, str(HOOK), "--box", str(box)],
        input=stdin, capture_output=True, text=True, check=False,
    )  # fmt: skip


def prompt(box, text):
    return hook(
        box, json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": text})
    )


def test_unsealed_the_model_is_told_only_that_the_files_hold_it(box):
    run = prompt(box, FROST)
    assert run.returncode == 0
    assert "nothing is sealed" in run.stdout
    assert "October" not in run.stdout


def test_sealed_for_this_question_the_page_goes_in_framed_as_data(box):
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    run = prompt(box, FROST)
    assert "<sealed-page>" in run.stdout
    assert "first frost comes in late October" in run.stdout
    assert "MOT" not in run.stdout


def test_a_page_sealed_for_another_question_stays_out(box):
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    run = prompt(box, "when is the car's MOT due")
    assert "October" not in run.stdout and "<sealed-page>" not in run.stdout


def test_a_question_the_files_do_not_hold_adds_nothing(box):
    assert prompt(box, "what colour is the boat").stdout == ""


def test_whatever_it_is_sent_it_exits_0_and_says_nothing(box):
    for stdin in ["", "not json", "[1, 2]", '{"prompt": null}', "{" * 100000]:
        run = hook(box, stdin)
        assert (run.returncode, run.stdout) == (0, ""), stdin[:20]


def test_two_scopes_sealed_each_question_gets_its_own_page(box):
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    runtime.read(box, "when is the car's MOT due")
    seal(box, runtime.propose(box)["seal"])
    frost = prompt(box, FROST).stdout  # the older scope, served by its name
    assert "first frost comes in late October" in frost and "MOT" not in frost
    mot = prompt(box, "when is the car's MOT due").stdout
    assert "MOT" in mot and "frost" not in mot


def test_a_session_that_asked_to_be_let_in_is_pointed_at_the_context_tool(box):
    """Told at every prompt that it is given nothing, a session let in would
    be told something untrue. Whether it asked is read beside the box alone:
    the hook's line gives nothing, and writes no row to choose its words."""
    sent = {"hook_event_name": "UserPromptSubmit", "prompt": FROST,
            "cwd": "/work/a", "session_id": "s1"}  # fmt: skip
    assert "nothing is sealed" in hook(box, json.dumps(sent)).stdout
    asked = runtime.call(box, "grant", door="mcp", where="/work/a", session="s1")
    rows = len((box / "record.jsonl").read_text().splitlines())
    said = hook(box, json.dumps(sent)).stdout
    assert "The context tool gives what this session may have" in said
    assert "nothing is sealed" not in said and "October" not in said
    kinds = [json.loads(ln)["kind"]
             for ln in (box / "record.jsonl").read_text().splitlines()[rows:]]  # fmt: skip
    assert (
        kinds.count("bite") <= 1
    )  # the read for the question, and no asking of the yes
    # another session, another folder, or one whose yes was stopped: as before
    for other in ({"session_id": "s2"}, {"cwd": "/work/b"}):
        assert "nothing is sealed" in hook(box, json.dumps({**sent, **other})).stdout
    runtime.call(box, "stop", asked["seal"], door="pipe")
    assert "nothing is sealed" in hook(box, json.dumps(sent)).stdout
