"""A report of the person's own files at a model's door: that there is one
(the person's ruling of 2026-11-17); the report itself, as it reads now,
to a session they let in. No report waits on a seal of its own (2026-11-18)."""

import json
import time

import pytest
from test_leave import seal

import runtime


LET = {"door": "mcp", "where": "/work/a", "session": "s1"}


def let_in(box):
    """The person's one yes, for the session in LET."""
    seal(box, runtime.call(box, "grant", **LET)["seal"])


def given(box, name):
    """The report, asked for by that session."""
    return runtime.call(box, "report", name, **LET)


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
    assert got == {"state": "populated", "report": "people"}
    told = json.dumps(got) + (runtime.state(folk) / "sent.jsonl").read_text()
    assert "Kati" not in told and "Priya" not in told
    assert runtime.waiting(folk)["state"] == "empty"  # nothing waits on a seal
    let_in(folk)
    page = given(folk, "people")["page"]
    assert page.splitlines()[0].startswith("people: names 2 people")
    assert "Kati  3 mentions" in page


def test_a_name_the_person_listed_is_withheld_from_the_people_report(folk):
    (runtime.state(folk) / "names.txt").write_text("Kati\n")
    let_in(folk)
    page = given(folk, "people")["page"]
    assert "Kati" not in page and "[withheld: name]" in page and "Priya" in page


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
    assert got["state"] == "populated" and "Dentist" not in json.dumps(got)
    let_in(box)
    page = given(box, "coming-up")["page"]
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
    assert got == {"state": "populated", "report": "todo"}
    told = json.dumps(got) + (runtime.state(chores) / "sent.jsonl").read_text()
    for word in ("dahlia", "MOT", "chores", "2 lines"):
        assert word not in told


def test_nothing_to_report_is_all_a_model_hears_and_nothing_waits(box):
    got = runtime.call(box, "report", "todo", door="mcp")
    assert got == {"state": "empty", "report": "todo"}
    assert runtime.waiting(box)["state"] == "empty"


def test_no_report_waits_on_a_seal_of_its_own(chores):
    """The owner, 2026-11-18: one report is not sealed on its own. A seal of
    it went stale the day the report read differently; the yes is the
    session's. So asking proposes nothing, however often."""
    for _ in range(2):
        runtime.call(chores, "report", "todo", door="mcp")
        given(chores, "todo")  # a session's own name changes nothing: not let in
    assert runtime.waiting(chores)["state"] == "empty"
    assert not (runtime.state(chores) / "reports.json").exists()
    assert not (chores / "written" / "reports").exists()


def test_let_in_the_model_is_given_the_report_as_it_reads_now(chores):
    let_in(chores)
    got = given(chores, "todo")
    assert (got["state"], got["by"]) == ("left", "grant")
    theirs = runtime.call(chores, "report", "todo", door="pipe")["text"]
    assert got["page"].strip() == theirs.strip()  # nothing here to withhold
    (chores.parent / "pile" / "more.md").write_text("FIXME: the gate latch.\n")
    assert (
        "gate latch" in given(chores, "todo")["page"]
    )  # and tomorrow, as it reads then
    # only that session, in that folder: any other still learns only that there is one
    assert "page" not in runtime.call(chores, "report", "todo", door="mcp")
    assert "page" not in runtime.call(
        chores, "report", "todo", **{**LET, "session": "s2"}
    )


def test_what_leaves_is_withheld_as_a_page_is(chores):
    tail = "900" + "123"  # a made-up number, put together here
    (chores.parent / "pile" / "calls.md").write_text(
        f"Need to ring Aoife on 07700 {tail} about the fence.\n"
    )
    (runtime.state(chores) / "names.txt").write_text("Aoife\n")
    let_in(chores)
    page = given(chores, "todo")["page"]
    assert "[withheld: name]" in page and "Aoife" not in page and tail not in page
    assert "the fence" in page


def test_a_report_stops_leaving_when_the_session_is_no_longer_let_in(chores):
    let_in(chores)
    assert "page" in given(chores, "todo")
    runtime.grant_end(chores, LET["session"])
    assert given(chores, "todo") == {"state": "populated", "report": "todo"}


def test_a_report_is_never_a_page_a_model_can_answer(chores):
    let_in(chores)
    assert "dahlia" in given(chores, "todo")["page"]
    assert runtime.call(chores, "leave", door="mcp")["state"] == "refused"
    got = runtime.call(chores, "propose", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "nothing_to_scope")


def test_the_sent_log_reads_as_what_happened(chores):
    runtime.call(chores, "report", "todo", door="mcp")
    assert (
        "that there is a todo report, and nothing of it"
        in (runtime.call(chores, "shared", door="pipe")["lines"][-1])
    )
    let_in(chores)
    given(chores, "todo")
    assert (
        "the todo report, under the yes you gave its session"
        in (runtime.call(chores, "shared", door="pipe")["lines"][-1])
    )


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
    let_in(chores)
    page = given(chores, "todo")["page"]
    assert "squash" not in page and "gate latch" in page


def test_with_everything_left_out_a_model_hears_only_that_there_is_nothing(chores):
    (runtime.state(chores) / "report-skip.txt").write_text("chores.md\n")
    got = runtime.call(chores, "report", "todo", door="mcp")
    assert got == {"state": "empty", "report": "todo"}  # and no count of what was
    assert runtime.call(chores, "report", "todo", door="pipe")["left_out"] == 2


def test_a_report_too_long_to_read_is_never_given(chores, monkeypatch):
    monkeypatch.setattr(runtime, "REPORT_MOST", 40)
    let_in(chores)
    got = given(chores, "todo")
    assert (got["state"], got["code"]) == ("refused", "report_too_long")
    assert "report-skip.txt" in got["next"]
    assert not any(ch.isdigit() for ch in got["why"] + got["say"])  # no size said
    # their own read is never cut short
    assert runtime.call(chores, "report", "todo", door="pipe")["state"] == "populated"


def test_on_this_day_is_a_report_too(box):
    assert runtime.call(box, "report", "on-this-day", door="mcp")["state"] in ("empty", "populated")  # fmt: skip
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
    assert got == {"state": "populated", "report": name}
    told = json.dumps(got) + (runtime.state(leaky) / "sent.jsonl").read_text()
    for word in heard + SECRETS + NUMBERS:
        assert word not in told


def test_let_in_a_ref_check_gives_the_places_that_do_not_hold(leaky):
    let_in(leaky)
    page = given(leaky, "ref-check")["page"]
    assert page.splitlines()[0] == "ref-check: 2 references checked, 1 doesn't hold"
    assert "index.md:1  trips/2019.md: not there" in page


def test_the_minutes_say_in_their_first_line_that_they_name_people(leaky):
    """The owner of an action is a name. The rows stay decisions and actions:
    only `people` is a line a person."""
    let_in(leaky)
    page = given(leaky, "minutes")["page"]
    assert page.splitlines()[0].endswith(", which names people")
    assert "## decisions" in page and "## actions open" in page
    assert "board.md:3  2026-03-02  Ana  send the figures" in page


def test_a_name_the_person_listed_is_withheld_from_the_minutes(leaky):
    (runtime.state(leaky) / "names.txt").write_text("Ana\n")
    let_in(leaky)
    page = given(leaky, "minutes")["page"]
    assert "Ana" not in page and "[withheld: name]" in page


@pytest.mark.parametrize("name", ["pii-audit", "secrets-audit"])
def test_an_audit_never_shows_the_value_it_found_to_anyone(leaky, name):
    """Willow's audits list where, never what. Nothing here may bring a value
    back in: not the person's own read, what a session let in is given, nor
    anything written down on the way. The one thing the person's own door
    keeps is the last digits of a number, as Willow shows them; a model is
    never given even those."""
    mine = runtime.call(leaky, "report", name, door="pipe")["text"]
    got = runtime.call(leaky, "report", name, door="mcp")
    let_in(leaky)
    page = given(leaky, name)["page"]
    kept = "".join(
        f.read_text()
        for f in leaky.rglob("*")
        if f.is_file() and f.suffix in (".md", ".json", ".jsonl", ".txt")
    )
    assert "deploy.md" in page
    for value in SECRETS + NUMBERS:  # what a model reads: not a digit
        assert value not in page
    # what is written down holds hashes, where three digits turn up by
    # chance: there it is the whole value that must never appear
    for text in (json.dumps(got), kept):
        for value in (*SECRETS, NHS):
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


def test_a_record_of_several_places_is_told_a_report_reads_one_folder(tmp_path):
    """A record made with init --from reads its files where they are; Willow's
    reports that read one folder are refused by the kernel there (Willow
    #383), and the person is told so in words, never shown the traceback."""
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "notes.md").write_text("2026-12-01 dentist appointment\n")
    (b / "garden.md").write_text("Tomatoes want sun.\n")
    box = tmp_path / "box"
    made = runtime.willow("kernel.py", "init", "--box", str(box), "--from", f"a={a}",
                          "--from", f"b={b}", "--key", str(tmp_path / "k.key"))  # fmt: skip
    assert made.returncode == 0, made.stderr
    for got in (runtime.call(box, "report", "coming-up", door="pipe"),
                runtime.call(box, "report", "pii-audit", door="mcp"),
                runtime.call(box, "timeline", "dentist", door="pipe")):  # fmt: skip
        assert got["state"] == "refused" and got["code"] == "reads_one_folder", got
        assert "Traceback" not in json.dumps(got), got
    # a report that reads the record's passages is made as on any record
    assert runtime.call(box, "report", "todo", door="pipe")["state"] != "refused"


def test_a_report_is_named_in_any_case(box):
    """Todo, TODO and todo are one report: a model or a person need not
    know the case it is spelled in."""
    for name in ("Todo", "TODO", " todo "):
        got = runtime.call(box, "report", name, door="pipe")
        assert got.get("code") != "no_report", (name, got)
    assert runtime.call(box, "report", "Nope", door="pipe")["code"] == "no_report"
