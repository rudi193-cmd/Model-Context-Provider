"""A report of the person's own files at a model's door: that there is one,
until the person seals it; then exactly the words they sealed, and no
others (the person's ruling of 2026-11-17)."""

import json
import time

import pytest
from test_leave import seal

import runtime


@pytest.fixture
def folk(box):
    """The box's folder, with two people in it: Kati three times, Priya once."""
    pile = box.parent / "pile"
    (pile / "log.md").write_text(
        "2026-01-02 Kati came by.\nthanks kati!\nmet Priya at the market\n"
    )
    (pile / "mail").mkdir()
    (pile / "mail" / "2026-02-01.txt").write_text("KATI'S invoice attached\n")
    return box


def test_the_people_report_is_a_line_a_person_and_no_place_they_are_mentioned(folk):
    got = runtime.call(folk, "report", "people", door="pipe")
    lines = got["text"].splitlines()
    assert lines[0] == "people: names 2 people, by how often your files do"
    assert lines[1] == "  Kati  3 mentions in 2 files, 2026-01-02 to 2026-02-01"
    assert lines[2].startswith("  Priya  1 mention in 1 file")
    assert len(lines) == 3  # most mentioned first, and nothing else
    for word in ("came by", "invoice", "market", "log.md", "mail/"):
        assert word not in got["text"]


def test_a_model_learns_there_is_a_people_report_and_no_name_in_it(folk):
    got = runtime.call(folk, "report", "people", door="mcp")
    assert (got["state"], got["report"]) == ("waiting", "people")
    told = json.dumps(got) + (runtime.state(folk) / "sent.jsonl").read_text()
    assert "Kati" not in told and "Priya" not in told
    (owed,) = runtime.waiting(folk)["waiting"]
    assert "which names people" in owed["claim"]  # said before they seal
    seal(folk, got["seal"])
    page = runtime.call(folk, "report", "people", door="mcp")["page"]
    assert page == owed["words"] and "Kati  3 mentions" in page


def test_a_name_the_person_listed_is_withheld_from_the_people_report(folk):
    (runtime.state(folk) / "names.txt").write_text("Kati\n")
    got = runtime.call(folk, "report", "people", door="mcp")
    (owed,) = runtime.waiting(folk)["waiting"]
    assert "Kati" not in owed["words"] and "[withheld: name]" in owed["words"]
    seal(folk, got["seal"])
    page = runtime.call(folk, "report", "people", door="mcp")["page"]
    assert "Kati" not in page and "Priya" in page


def test_a_folder_left_out_is_counted_in_no_ones_line(folk):
    (runtime.state(folk) / "report-skip.txt").write_text("mail\n")
    text = runtime.call(folk, "report", "people", door="pipe")["text"]
    assert "  Kati  2 mentions in 1 file, 2026-01-02 to 2026-01-02" in text
    (runtime.state(folk) / "report-skip.txt").write_text("mail\nlog.md\n")
    assert runtime.call(folk, "report", "people", door="mcp") == {
        "state": "empty", "report": "people"}  # fmt: skip


def test_a_folder_that_names_no_one_has_no_people_report(box):
    """Willow's people exits 42 for no one, with a report that says so: an
    exit code says what was found, never that the report failed."""
    assert runtime.call(box, "report", "people", door="mcp") == {
        "state": "empty", "report": "people"}  # fmt: skip
    assert runtime.waiting(box)["state"] == "empty"


def test_coming_up_is_a_report_of_the_dates_ahead(box):
    assert runtime.call(box, "report", "coming-up", door="mcp") == {
        "state": "empty", "report": "coming-up"}  # fmt: skip
    soon = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 3 * 86400))
    (box.parent / "pile" / "diary.md").write_text(
        f"Dentist on {soon}, bring the form.\n"
    )
    theirs = runtime.call(box, "report", "coming-up", door="pipe")
    assert theirs["state"] == "populated" and f"## {soon}" in theirs["text"]
    got = runtime.call(box, "report", "coming-up", door="mcp")
    assert got["state"] == "waiting" and "Dentist" not in json.dumps(got)
    seal(box, got["seal"])
    page = runtime.call(box, "report", "coming-up", door="mcp")["page"]
    assert "diary.md:1" in page and "bring the form" in page


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


# the audits and the minutes: the same report shape, found in Willow's add-ons.
# Anything shaped like a secret is put together here, so no file of this
# project holds one.
LABEL = "".join(["pa", "ss", "wo", "rd"])
SECRET_PASSWORD = "".join(["hun", "ter", "2xyz"])
SECRET_KEY = "".join(["sk", "_li", "ve_", "A1b2C3d4E5f6G7h8I9j0K1l2"])
CARD = " ".join(["4242"] * 4)
NHS = "943 476 5919"
SECRETS = (SECRET_PASSWORD, SECRET_KEY, CARD)
NUMBERS = (CARD, "4242", NHS, "5919", "476")


@pytest.fixture
def leaky(box):
    """A folder with a password, a key, a card and an NHS number in it, a link
    that leads nowhere, and a meeting's minutes."""
    pile = box.parent / "pile"
    (pile / "wifi.txt").write_text(f"router\n{LABEL}: {SECRET_PASSWORD}\n")
    (pile / "deploy.md").write_text(f"token {SECRET_KEY} here\ncard {CARD}\n")
    (pile / "p60.txt").write_text(f"nhs number {NHS}\n")
    (pile / "index.md").write_text("[trip](trips/2019.md) and [ok](deploy.md)\n")
    (pile / "board.md").write_text(
        "# March 2026-03-02\n- Decision: Move the AGM to May.\n"
        "- Action: Ana to send the figures by 2026-03-09\n"
    )
    return box


@pytest.mark.parametrize("name", ["ref-check", "pii-audit", "secrets-audit", "minutes"])
def test_a_folder_with_nothing_for_the_report_to_find_has_none(box, name):
    assert runtime.call(box, "report", name, door="mcp") == {
        "state": "empty", "report": name}  # fmt: skip
    assert runtime.call(box, "report", name, door="pipe")["state"] == "empty"
    assert runtime.waiting(box)["state"] == "empty"


@pytest.mark.parametrize(
    ("name", "found"),
    [
        ("ref-check", "index.md:1  trips/2019.md: not there"),
        ("pii-audit", "## an NHS number\n  p60.txt:1"),
        ("secrets-audit", "wifi.txt:2  value not shown"),
        ("minutes", "board.md:2  2026-03-02  Move the AGM to May."),
    ],
)
def test_each_new_report_is_the_persons_to_read_as_it_is(leaky, name, found):
    got = runtime.call(leaky, "report", name, door="pipe")
    assert got["state"] == "populated" and found in got["text"]
    assert runtime.waiting(leaky)["state"] == "empty"  # their own read asks no seal


@pytest.mark.parametrize(
    ("name", "heard"),
    [
        ("ref-check", ("trips", "2019", "index.md")),
        ("pii-audit", ("p60", "NHS", "deploy.md")),
        ("secrets-audit", ("wifi", "deploy", "value not shown")),
        ("minutes", ("AGM", "Ana", "board.md")),
    ],
)
def test_a_model_learns_only_that_there_is_one_of_the_new_reports(leaky, name, heard):
    got = runtime.call(leaky, "report", name, door="mcp")
    assert sorted(got) == ["report", "seal", "state"]
    assert (got["state"], got["report"]) == ("waiting", name)
    told = json.dumps(got) + (runtime.state(leaky) / "sent.jsonl").read_text()
    for word in heard + SECRETS + NUMBERS:
        assert word not in told


def test_a_sealed_ref_check_gives_the_places_that_do_not_hold(leaky):
    got = runtime.call(leaky, "report", "ref-check", door="mcp")
    (owed,) = runtime.waiting(leaky)["waiting"]
    assert "which names people" not in owed["claim"]
    seal(leaky, got["seal"])
    page = runtime.call(leaky, "report", "ref-check", door="mcp")["page"]
    assert page == owed["words"]
    assert page.splitlines()[0] == "ref-check: 2 references checked, 1 doesn't hold"
    assert "index.md:1  trips/2019.md: not there" in page


def test_the_minutes_say_before_the_seal_that_they_name_people(leaky):
    """The owner of an action is a name. The rows stay decisions and actions:
    only `people` is a line a person."""
    got = runtime.call(leaky, "report", "minutes", door="mcp")
    (owed,) = runtime.waiting(leaky)["waiting"]
    assert "which names people" in owed["claim"]
    assert owed["words"].splitlines()[0].endswith(", which names people")
    seal(leaky, got["seal"])
    page = runtime.call(leaky, "report", "minutes", door="mcp")["page"]
    assert page == owed["words"]
    assert "## decisions" in page and "## actions open" in page
    assert "board.md:3  2026-03-02  Ana  send the figures" in page


def test_a_name_the_person_listed_is_withheld_from_the_minutes(leaky):
    (runtime.state(leaky) / "names.txt").write_text("Ana\n")
    got = runtime.call(leaky, "report", "minutes", door="mcp")
    (owed,) = runtime.waiting(leaky)["waiting"]
    assert "Ana" not in owed["words"] and "[withheld: name]" in owed["words"]
    seal(leaky, got["seal"])
    assert "Ana" not in runtime.call(leaky, "report", "minutes", door="mcp")["page"]


@pytest.mark.parametrize("name", ["pii-audit", "secrets-audit"])
def test_an_audit_never_shows_the_value_it_found_to_anyone(leaky, name):
    """Willow's audits list where, never what. Nothing here may bring a value
    back in: not the person's own read, what waits, what is sealed, what a
    grant is given, nor anything written down on the way. The one thing the
    person's own door keeps is the last digits of a number, as Willow shows
    them; a model is never given even those."""
    mine = runtime.call(leaky, "report", name, door="pipe")["text"]
    got = runtime.call(leaky, "report", name, door="mcp")
    (owed,) = runtime.waiting(leaky)["waiting"]
    seal(leaky, got["seal"])
    page = runtime.call(leaky, "report", name, door="mcp")["page"]
    let_in = runtime.report_to_model(leaky, name, let_in=True)["page"]
    kept = "".join(
        f.read_text()
        for f in leaky.rglob("*")
        if f.is_file() and f.suffix in (".md", ".json", ".jsonl", ".txt")
    )
    assert page == owed["words"] and "deploy.md" in page
    for text in (owed["words"], page, let_in, json.dumps(got), kept):
        for value in SECRETS + NUMBERS:
            assert value not in text
    for value in (*SECRETS, NHS):  # whole, to no one: not even the person's read
        assert value not in mine


def test_the_pii_audit_keeps_the_last_digits_for_the_person_and_never_for_a_model(
    leaky,
):
    lines = runtime.call(leaky, "report", "pii-audit", door="pipe")["text"].splitlines()
    assert lines[0].startswith("pii-audit: 2 personal numbers in 2 of")
    assert [ln.split()[0] for ln in lines[1:]] == [
        "##",
        "deploy.md:2",
        "##",
        "p60.txt:1",
    ]
    assert lines[2].endswith("4242") and lines[4].endswith("5919")  # which card it is
    assert CARD not in "\n".join(lines) and NHS not in "\n".join(lines)  # never whole
    page = runtime.report_to_model(leaky, "pii-audit", let_in=True)["page"].splitlines()
    assert page[1:] == [
        "## a card number", "  deploy.md:2",
        "## an NHS number", "  p60.txt:1",
    ]  # fmt: skip


def test_the_secrets_audit_gives_a_place_a_kind_and_never_the_value(leaky):
    text = runtime.call(leaky, "report", "secrets-audit", door="pipe")["text"]
    assert text.splitlines()[0].endswith("values are never shown")
    for kind in ("a password typed with its label", "a key or token", "a card number"):
        assert f"## {kind}" in text
    assert "wifi.txt:2  value not shown" in text and "deploy.md:1" in text
