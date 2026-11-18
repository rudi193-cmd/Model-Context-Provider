"""A report of the person's own files at a model's door: that there is one,
until the person seals it; then exactly the words they sealed, and no
others (the person's ruling of 2026-11-17)."""

import json

import pytest
from test_leave import seal

import runtime


@pytest.fixture
def chores(box):
    """The box's folder, with two things written down to do."""
    pile = box.parent / "pile"
    (pile / "chores.md").write_text(
        "TODO: order the dahlia tubers.\n\nRemember to book the MOT for March.\n"
    )
    return box


def test_the_person_reads_a_report_as_it_is(chores):
    got = runtime.call(chores, "report", "todo", door="pipe")
    assert got["state"] == "populated"
    assert "chores.md:1" in got["text"] and "order the dahlia tubers" in got["text"]
    assert (
        runtime.waiting(chores)["state"] == "empty"
    )  # their own read asks for no seal


def test_a_model_learns_there_is_one_and_not_a_line_of_it(chores):
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert sorted(got) == ["report", "seal", "state"]
    assert (got["state"], got["report"]) == ("waiting", "todo")
    told = json.dumps(got) + (runtime.state(chores) / "sent.jsonl").read_text()
    for word in ("dahlia", "MOT", "chores", "2 lines"):
        assert word not in told


def test_nothing_to_report_is_all_a_model_hears_and_nothing_waits(box):
    got = runtime.call(box, "report", "todo", door="mcp")
    assert got == {"state": "empty", "report": "todo"}
    assert runtime.waiting(box)["state"] == "empty"


def test_what_waits_is_the_reports_own_words_for_the_person_to_read(chores):
    got = runtime.call(chores, "report", "todo", door="mcp")
    (owed,) = runtime.waiting(chores)["waiting"]
    assert owed["seal"] == got["seal"] and owed["path"].startswith("reports/todo-")
    assert "order the dahlia tubers" in owed["words"]


def test_sealed_the_model_is_given_exactly_what_was_sealed(chores):
    sealed = runtime.call(chores, "report", "todo", door="mcp")["seal"]
    (owed,) = runtime.waiting(chores)["waiting"]
    seal(chores, sealed)
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert got["state"] == "left"
    assert got["page"] == owed["words"]  # the words that waited, and no others
    theirs = runtime.call(chores, "report", "todo", door="pipe")["text"]
    assert got["page"].strip() == theirs.strip()  # nothing here to withhold
    (kept,) = (chores / "written" / "reports").glob("todo-*.md")
    assert kept.read_text() == got["page"]  # the kernel kept what was sealed


def test_asking_twice_before_the_seal_proposes_it_once(chores):
    first = runtime.call(chores, "report", "todo", door="mcp")
    again = runtime.call(chores, "report", "todo", door="mcp")
    assert (again["state"], "seal" in again) == ("waiting", False)
    assert [w["seal"] for w in runtime.waiting(chores)["waiting"]] == [first["seal"]]


def test_a_report_that_would_read_differently_now_waits_on_a_seal_of_its_own(chores):
    seal(chores, runtime.call(chores, "report", "todo", door="mcp")["seal"])
    (chores.parent / "pile" / "more.md").write_text("FIXME: the gate latch.\n")
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert got["state"] == "waiting" and "latch" not in json.dumps(got)
    seal(chores, got["seal"])
    assert "gate latch" in runtime.call(chores, "report", "todo", door="mcp")["page"]


def test_what_leaves_is_withheld_as_a_page_is(chores):
    (chores.parent / "pile" / "calls.md").write_text(
        "Need to ring Aoife on 07700 900123 about the fence.\n"
    )
    (runtime.state(chores) / "names.txt").write_text("Aoife\n")
    got = runtime.call(chores, "report", "todo", door="mcp")
    (owed,) = runtime.waiting(chores)["waiting"]
    assert "Aoife" not in owed["words"] and "900123" not in owed["words"]
    seal(chores, got["seal"])
    page = runtime.call(chores, "report", "todo", door="mcp")["page"]
    assert "[withheld: name]" in page and "Aoife" not in page and "900123" not in page
    assert "the fence" in page


def test_a_report_the_person_stopped_never_leaves_again(chores):
    subject = runtime.call(chores, "report", "todo", door="mcp")["seal"]
    seal(chores, subject)
    assert runtime.call(chores, "stop", subject, door="pipe")["state"] == "stopped"
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "stopped")


def test_a_sealed_report_is_never_given_for_a_question(chores):
    seal(chores, runtime.call(chores, "report", "todo", door="mcp")["seal"])
    for verb in ("read", "context"):
        got = runtime.call(chores, verb, "what do I need to order", door="mcp")
        assert "dahlia" not in json.dumps(got)
    assert runtime.call(chores, "leave", door="mcp")["state"] == "refused"


def test_a_propose_after_a_report_scopes_no_earlier_read(chores):
    runtime.call(chores, "read", "when does the first frost come", door="mcp")
    runtime.call(chores, "report", "todo", door="mcp")
    got = runtime.call(chores, "propose", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "nothing_to_scope")


def test_the_sent_log_reads_as_what_happened(chores):
    seal(chores, runtime.call(chores, "report", "todo", door="mcp")["seal"])
    runtime.call(chores, "report", "todo", door="mcp")
    first, second = runtime.call(chores, "shared", door="pipe")["lines"]
    assert "that there is a todo report, waiting on your seal" in first
    assert "the todo report you sealed" in second


def test_a_folder_the_person_leaves_out_is_in_no_report(chores):
    pile = chores.parent / "pile"
    (pile / "commits").mkdir()
    (pile / "commits" / "abc.txt").write_text("TODO: squash these before merging.\n")
    (pile / "commits-old").mkdir()
    (pile / "commits-old" / "keep.txt").write_text("FIXME: the gate latch.\n")
    (pile / "scratch.md").write_text("TODO: nothing anyone needs to see.\n")
    assert "squash" in runtime.call(chores, "report", "todo", door="pipe")["text"]
    (runtime.state(chores) / "report-skip.txt").write_text(
        "# machine-made\ncommits/\nscratch.md\n"
    )
    theirs = runtime.call(chores, "report", "todo", door="pipe")
    assert theirs["left_out"] == 2
    for gone in ("squash", "nothing anyone needs"):
        assert gone not in theirs["text"]
    for kept in ("dahlia", "MOT", "gate latch"):  # commits-old isn't commits
        assert kept in theirs["text"]
    assert theirs["text"].splitlines()[0] == "todo: 3 lines"
    seal(chores, runtime.call(chores, "report", "todo", door="mcp")["seal"])
    page = runtime.call(chores, "report", "todo", door="mcp")["page"]
    assert "squash" not in page and "gate latch" in page


def test_with_everything_left_out_a_model_hears_only_that_there_is_nothing(chores):
    (runtime.state(chores) / "report-skip.txt").write_text("chores.md\n")
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert got == {"state": "empty", "report": "todo"}  # and no count of what was
    assert runtime.call(chores, "report", "todo", door="pipe")["left_out"] == 2


def test_a_report_too_long_to_read_is_never_proposed(chores, monkeypatch):
    monkeypatch.setattr(runtime, "REPORT_MOST", 40)
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "report_too_long")
    assert "report-skip.txt" in got["next"]
    assert not any(ch.isdigit() for ch in got["why"] + got["say"])  # no size said
    assert runtime.waiting(chores)["state"] == "empty"
    # their own read is never cut short
    assert runtime.call(chores, "report", "todo", door="pipe")["state"] == "populated"


def test_on_this_day_is_a_report_too(box):
    assert runtime.call(box, "report", "on-this-day", door="mcp")["state"] in ("empty", "waiting")  # fmt: skip
    assert runtime.call(box, "report", "on-this-day", door="pipe")["state"] in ("empty", "populated")  # fmt: skip


def test_a_report_this_does_not_make_is_refused_in_plain_words(box):
    got = runtime.call(box, "report", "horoscope", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "no_report")
    assert runtime.call(box, "report", None, door="pipe")["code"] == "no_report"
