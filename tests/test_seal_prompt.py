"""seal_prompt.py: the person's yes to a session, asked in a dialog on their
own desktop. Here a script stands in for pinentry and answers as a click
would; no dialog is ever opened by these tests."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import facts
import runtime
import seal_prompt

ROOT = Path(__file__).resolve().parents[1]
FROST = "when does the first frost come"
CONFIRMED = "OK"
DECLINED = "ERR 83886194 Not confirmed <Pinentry>"
CANCELLED = "ERR 83886179 Operation cancelled <Pinentry>"


def clicks(tmp_path, answer, greeting="OK Pleased to meet you"):
    """A pinentry that says what a real one says, and writes down what it
    was asked."""
    f = tmp_path / f"pinentry-{abs(hash(answer + greeting))}"
    f.write_text(
        "#!/bin/sh\n"
        f"echo '{greeting}'\n"
        "while read -r line; do\n"
        f'  echo "$line" >> {tmp_path / "asked.txt"}\n'
        '  case "$line" in\n'
        f"    CONFIRM) echo '{answer}' ;;\n"
        "    BYE) echo OK; exit 0 ;;\n"
        "    *) echo OK ;;\n"
        "  esac\n"
        "done\n"
    )
    f.chmod(0o755)
    return str(f)


def asked(box, where="/work/a", session="s1"):
    got = runtime.call(box, "grant", door="mcp", where=where, session=session)
    assert got["state"] == "waiting", got
    return got["seal"]


def decided(box):
    """The rows only the person's key makes."""
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    return [r["kind"] for r in rows if r["kind"] in ("seal", "decline")]


def run(box, subject, program):
    return subprocess.run(
        [sys.executable, str(ROOT / "seal_prompt.py"), "--box", str(box),
         "--seal", subject, "--pinentry", program],
        capture_output=True, text=True, check=False, cwd=ROOT,
        env={**os.environ, "WILLOW": str(runtime.WILLOW)},
    )  # fmt: skip


def context(box):
    return runtime.call(
        box, "context", FROST, door="mcp", where="/work/a", session="s1"
    )


def test_a_yes_seals_the_grant_and_the_session_is_answered(box, tmp_path):
    subject = asked(box)
    got = run(box, subject, clicks(tmp_path, CONFIRMED))
    assert got.returncode == 0 and got.stdout.strip() == f"sealed {subject}", got.stderr
    assert context(box)["state"] == "left"
    said = (tmp_path / "asked.txt").read_text()
    assert "SETDESC An assistant session working in%0A/work/a%0Aasks to read" in said
    assert "SETOK Seal: yes, for this session" in said and "SETNOTOK Decline" in said
    assert "SETCANCEL Not now" in said and "GETPIN" not in said  # never a passphrase
    for word in ("frost", "October", "garden"):
        assert word not in said


def test_a_no_declines_it_for_good(box, tmp_path):
    subject = asked(box)
    got = run(box, subject, clicks(tmp_path, DECLINED))
    assert got.returncode == 0 and got.stdout.strip() == f"declined {subject}"
    assert facts(context(box)) == {"state": "populated"}
    assert runtime.waiting(box)["state"] == "empty"


@pytest.mark.parametrize(
    "answer",
    [
        CANCELLED,
        "ERR 83886142 Timeout",
        "ERR",
        "what",
        "",
        "OKAY then",
        "ERR 83886194x",
    ],
)
def test_not_now_or_anything_unclear_changes_nothing(box, tmp_path, answer):
    subject = asked(box)
    got = run(box, subject, clicks(tmp_path, answer))
    assert got.returncode == 42 and "waits on your seal page" in got.stdout
    assert decided(box) == []
    assert [w["seal"] for w in runtime.waiting(box)["waiting"]] == [subject]
    assert facts(context(box)) == {"state": "populated"}


def test_a_dialog_that_never_came_up_is_not_a_yes(box, tmp_path):
    subject = asked(box)
    for program in (clicks(tmp_path, CONFIRMED, greeting="ERR 1 no display"),
                    "/bin/true", "/bin/false"):  # fmt: skip
        assert run(box, subject, program).returncode == 42, program
    got = run(box, subject, str(tmp_path / "no-such-pinentry"))
    assert got.returncode == 2 and "no pinentry program" in got.stderr
    assert decided(box) == []


def test_it_asks_about_a_sessions_grant_and_nothing_else(box, tmp_path):
    runtime.read(box, FROST)
    page = runtime.propose(box)["seal"]  # a page to share: read on the seal page
    yes = clicks(tmp_path, CONFIRMED)
    for subject in (page, "proposal:" + "0" * 64, "nonsense"):
        got = run(box, subject, yes)
        assert got.returncode == 2 and "isn't a session's grant" in got.stderr, subject
    assert not (tmp_path / "asked.txt").exists()  # nothing was even asked
    assert [w["seal"] for w in runtime.waiting(box)["waiting"]] == [page]
    for argv in (
        [],
        ["--box", str(box)],
        ["--box", str(box), "--seal", page, "--yes", "1"],
    ):
        got = subprocess.run([sys.executable, str(ROOT / "seal_prompt.py"), *argv],
                             capture_output=True, text=True, check=False, cwd=ROOT)  # fmt: skip
        assert got.returncode == 2 and "seal_prompt.py --box" in got.stderr


def test_the_words_asked_are_carried_whole_on_one_line():
    assert seal_prompt.esc("50% of\r\nit") == "50%25 of%0Ait"


def test_the_runtime_starts_it_only_where_the_person_turned_it_on(
    box, tmp_path, monkeypatch
):
    started = []
    monkeypatch.setattr(runtime, "launch", started.append)
    subject = asked(box)
    assert started == []  # no ask-here beside the box: nothing is started
    (runtime.state(box) / "ask-here").write_text("")
    again = asked(box)  # the same asking: not started twice
    assert again == subject and started == []
    other = asked(box, session="s2")
    (argv,) = started
    assert argv[1:] == [
        str(ROOT / "seal_prompt.py"),
        "--box",
        str(box),
        "--seal",
        other,
    ]
    start = {"hook_event_name": "SessionStart", "session_id": "s3", "cwd": "/work/a"}
    runtime.call(box, "event", start, door="guard")
    assert len(started) == 2 and started[1][-1].startswith("proposal:")
    # and it is the person's door alone that can't be made to start it
    for door in ("pipe", "mcp", "hook", "guard"):
        got = runtime.call(box, "ask_here", subject, door=door)
        assert got["code"] == "no_verb"
    assert json.loads((runtime.state(box) / "grants.json").read_text())
    assert time.time() > 0
