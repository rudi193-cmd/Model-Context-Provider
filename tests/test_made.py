"""Two files to hand on, by Willow's timeline and rss-out: one matter in
date order, and a feed of what was sealed. The person makes either on
their own door; a session they let in may have one made for them."""

import json

from test_leave import seal
from test_share import sentence

import runtime


def pipe(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="pipe")


def model(box, verb, arg=None, session="s1"):
    return runtime.call(box, verb, arg, door="mcp", where="/work/a", session=session)


def tenancy(box):
    pile = box.parent / "pile"
    (pile / "tenancy.md").write_text(
        "2026-03-01 Reported the mould in the back bedroom to Aoife Byrne.\n"
        "The landlord said someone would come.\n"
        "2026-04-02 Still no visit from the landlord; mould spreading.\n"
    )
    (runtime.state(box) / "names.txt").write_text("Aoife Byrne\n")


def test_the_person_makes_a_timeline_whole_in_a_file_of_their_own(box, tmp_path):
    tenancy(box)
    got = pipe(box, "timeline", "mould landlord")
    assert got["state"] == "written", got
    assert got["text"] == open(got["file"]).read()
    assert "2026-03-01" in got["text"] and "tenancy.md:1" in got["text"]
    assert "Aoife Byrne" in got["text"]  # their own copy: nothing withheld
    made = runtime.Path(got["file"])
    assert made.parent == runtime.state(box) / "made"
    to = tmp_path / "for-the-council.txt"
    named = pipe(box, "timeline", {"about": "mould landlord", "to": str(to)})
    assert named["file"] == str(to) and to.read_text() == got["text"]
    assert pipe(box, "timeline", {"about": "mould landlord", "to": str(to)})[
        "code"
    ] == ("timeline_refused")  # never over a file
    inside = pipe(box, "timeline", {"about": "mould", "to": str(box / "t.txt")})
    assert inside["code"] == "timeline_refused"
    assert pipe(box, "timeline", "zzqx nothing holds this")["state"] == "empty"
    assert pipe(box, "timeline", "x" * 301)["code"] == "timeline_refused"


def test_a_session_let_in_has_one_made_and_is_given_it_withheld(box):
    tenancy(box)
    told = model(box, "timeline", "mould landlord")
    assert (told["state"], told["code"]) == ("refused", "no_grant")
    assert not (runtime.state(box) / "made").exists()  # nothing was made
    seal(box, model(box, "grant")["seal"])
    got = model(box, "timeline", "mould landlord")
    assert got["state"] == "left" and got["by"] == "grant", got
    assert "2026-03-01" in got["page"] and "Aoife Byrne" not in got["page"]
    assert "Aoife Byrne" in open(got["file"]).read()  # the person's copy is whole
    assert "a timeline of one matter" in pipe(box, "shared")["lines"][-1]
    assert model(box, "timeline", "zzqx nothing")["state"] == "empty"
    assert "page" not in model(box, "timeline", "mould landlord", session="s2")


def test_a_long_timeline_is_given_in_parts_of_whole_lines(box, monkeypatch):
    tenancy(box)
    seal(box, model(box, "grant")["seal"])
    whole = model(box, "timeline", "mould landlord")
    assert whole["lines"] == 3 and whole["given"] == "1 to 3" and "after" not in whole
    monkeypatch.setattr(runtime, "REPORT_MOST", 260)
    first = model(box, "timeline", "mould landlord")
    assert first["state"] == "left" and first["lines"] == 3 and first["after"] < 3
    assert first["page"].startswith("Timeline: mould landlord")
    rest = model(
        box, "timeline", {"about": "mould landlord", "after": str(first["after"])}
    )
    assert "after" not in rest and rest["given"].endswith("to 3")
    body = lambda got: got["page"].split("\n\n", 1)[1].splitlines()  # noqa: E731
    assert body(first) + body(rest) == body(whole)  # every line, once, whole
    past = model(box, "timeline", {"about": "mould landlord", "after": "3"})
    assert past["state"] == "empty"
    # asked again and again, the person has one file, not one a call
    assert len(list((runtime.state(box) / "made").iterdir())) == 1
    assert first["file"] == rest["file"] == whole["file"]


def test_what_the_person_leaves_out_of_reports_is_left_out_of_a_sessions_part(box):
    tenancy(box)
    pile = box.parent / "pile"
    (pile / "commits").mkdir()
    (pile / "commits" / "a.txt").write_text("2026-03-05 fix: mould landlord letter\n")
    seal(box, model(box, "grant")["seal"])
    assert model(box, "timeline", "mould landlord")["lines"] == 4
    (runtime.state(box) / "report-skip.txt").write_text("commits\n")
    got = model(box, "timeline", "mould landlord")
    assert got["lines"] == 3 and got["left_out"] == 1 and "commits/" not in got["page"]
    assert "commits/a.txt" in open(got["file"]).read()  # the person's file is whole
    assert "   " not in got["page"]  # and no column padding in a session's part


def test_every_word_first_then_half_and_it_says_which(box):
    tenancy(box)
    (box.parent / "pile" / "shed.md").write_text("2026-05-01 Mould on the shed roof.\n")
    both = pipe(box, "timeline", "mould landlord")
    assert "loose" not in both and "shed.md" not in both["text"]
    assert "holds every one of these words" in both["text"]
    half = pipe(box, "timeline", {"about": "mould landlord", "loose": True})
    assert half["loose"] is True and "shed.md:1" in half["text"]
    fell = pipe(box, "timeline", "mould zebra")  # no passage holds both
    assert fell["state"] == "written" and fell["loose"] is True
    assert "shed.md:1" in fell["text"]
    seal(box, model(box, "grant")["seal"])
    got = model(box, "timeline", "mould zebra")
    assert got["loose"] is True and "shed.md:1" in got["page"]
    assert "loose" not in model(box, "timeline", "mould landlord")


def test_a_sessions_part_drops_where_a_date_was_taken_from(box):
    tenancy(box)
    seal(box, model(box, "grant")["seal"])
    got = model(box, "timeline", "mould landlord")
    assert "(date from line 1)" in open(got["file"]).read()  # in the person's file
    assert "date from" not in got["page"]
    assert "The landlord said someone would come." in got["page"]
    assert runtime.timeline_short("2026-03-09  a.md:1    Wrote.  (date from line 3; filed 2026-03-10)") == (
        "2026-03-09  a.md:1  Wrote.  (filed 2026-03-10)")  # fmt: skip
    assert runtime.timeline_short("undated  a.md:1  A sum (see above)") == (
        "undated  a.md:1  A sum (see above)")  # fmt: skip


def test_a_timeline_is_narrowed_to_the_days_asked_for(box):
    tenancy(box)
    seal(box, model(box, "grant")["seal"])
    april = model(box, "timeline", {"about": "mould landlord", "since": "2026-04-01"})
    assert april["lines"] == 1 and "2026-04-02" in april["page"]
    assert "2026-03-01" not in april["page"].split("\n\n", 1)[1]
    march = model(box, "timeline", {"about": "mould landlord", "until": "2026-03-31"})
    assert march["lines"] == 2 and "2026-04-02" not in march["page"]
    assert "2026-04-02" in open(march["file"]).read()  # the person's copy is whole
    none = model(box, "timeline", {"about": "mould landlord", "since": "2030-01-01"})
    assert none["state"] == "empty"
    for bad in ({"since": "April"}, {"until": "2026-4-1"}, {"after": "two"}):
        got = model(box, "timeline", {"about": "mould landlord", **bad})
        assert (got["state"], got["code"]) == ("refused", "timeline_refused"), bad


def test_the_feed_holds_the_sentences_the_person_sealed_and_nothing_else(box, tmp_path):
    subject = sentence(box)
    note = runtime.call(box, "capture", "the gate sticks in the wet", door="mcp")
    seal(box, note["seal"])
    got = pipe(box, "feed")
    assert got["state"] == "written" and got["items"] == 1, got
    text = open(got["file"]).read()
    assert subject in text and "late October" in text and "gate sticks" not in text
    assert text.startswith("<?xml") and text.rstrip().endswith("</rss>")
    everything = pipe(box, "feed", {"all": True, "to": str(tmp_path / "all.xml")})
    assert (
        everything["items"] > 1 and "gate sticks" in (tmp_path / "all.xml").read_text()
    )
    again = pipe(box, "feed", {"to": str(tmp_path / "all.xml")})
    assert again["code"] == "feed_refused"  # never over a file
    assert (tmp_path / "all.xml").read_text().count("<item>") == everything["items"]
    for inside in (box / "feed.xml", box.parent / "pile" / "feed.xml"):
        assert pipe(box, "feed", {"to": str(inside)})["code"] == "feed_refused"
        assert not inside.exists()  # never in the record or the folder it reads
    later = pipe(box, "feed", {"since": "2999-01-01"})
    assert later["state"] == "written" and later["items"] == 0


def test_a_session_let_in_has_the_feed_written_and_is_given_none_of_it(box):
    sentence(box)
    assert model(box, "feed")["code"] == "tool_off"  # not offered until it is wanted
    pipe(box, "tools", {"on": ["sharing"]})
    assert model(box, "feed")["code"] == "no_grant"
    seal(box, model(box, "grant")["seal"])
    got = model(box, "feed")
    assert got["state"] == "written" and got["items"] == 1 and got["by"] == "grant"
    assert "late October" not in json.dumps(got)
    assert "a feed of what you sealed" in pipe(box, "shared")["lines"][-1]
