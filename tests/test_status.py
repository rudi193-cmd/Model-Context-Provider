"""status: how things stand, in one look, for the person. It gathers what
the other verbs say, and two of Willow's own reports; it decides nothing."""

import json

from test_leave import seal

import runtime
import seal_page

FROST = "when does the first frost come"


def rows(got, name):
    """A group's rows as {where: what}; {} when the group isn't there."""
    for g in got["groups"]:
        if g["name"] == name:
            return {r["where"]: r["what"] for r in g["rows"]}
    return {}


def test_a_quiet_box_says_nothing_waits_and_that_it_is_all_right(box):
    got = runtime.call(box, "status", door="pipe")
    assert got["state"] == "populated" and got["said"] == "nothing waits on your seal"
    assert rows(got, "Waiting on your seal") == {}
    fine = rows(got, "Is it all right")
    assert fine["Willow"].startswith("the pinned one, ")
    assert "couldn't look" not in fine["your record"]
    assert fine["the sent log"] == "0 lines, each naming the one before"
    assert got["text"].startswith("status: nothing waits on your seal\n## ")


def test_each_thing_that_waits_is_counted_as_what_it_is(box):
    (box.parent / "pile" / "chores.md").write_text("TODO: order the dahlia tubers.\n")
    runtime.call(box, "read", FROST, door="mcp")
    runtime.call(box, "propose", door="mcp")
    runtime.call(box, "report", "todo", door="mcp")
    runtime.call(box, "capture", "The dahlias did best by the wall.", door="mcp")
    aside = runtime.call(box, "capture", "A second note.", door="mcp")["seal"]
    runtime.call(box, "later", aside, door="pipe")
    got = runtime.call(box, "status", door="pipe")
    assert got["said"] == "3 things waiting on your seal"
    assert rows(got, "Waiting on your seal") == {
        "a page to share": "1", "a report to share": "1", "a note to keep": "1",
        "set aside": "1, still waiting",
    }  # fmt: skip


def test_what_was_shared_kept_and_shelved_is_said(box, tmp_path):
    runtime.call(box, "read", FROST, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    runtime.call(box, "leave", door="mcp")
    seal(box, runtime.call(box, "capture", "Keep this.", door="mcp")["seal"])
    runtime.call(box, "shelf_add", {"name": "report.md", "text": "found\n"},
                 door="mcp", where=str(tmp_path / "proj"))  # fmt: skip
    got = runtime.call(box, "status", door="pipe")
    shared = rows(got, "Shared")
    assert shared["pages"] == "1 sealed"
    assert shared["a model was told or given something"] == "5 times"
    assert "put on its project's shelf" in shared["the last time"]
    assert rows(got, "Kept") == {"notes you sealed": "1"}
    assert rows(got, "Shelves") == {str(tmp_path / "proj"): "1 thing"}


def test_how_it_is_set_is_said_from_the_files_beside_the_box(box):
    got = runtime.call(box, "status", door="pipe")
    was = rows(got, "How this is set")
    assert was["names withheld"] == "none listed (names.txt)"
    assert was["commands denied"] == "none (deny.txt), so that guard isn't asked"
    for name, text in (("names.txt", "Aoife\nBrigid\n"), ("deny.txt", "# mine\nrm -rf\n"),
                       ("report-skip.txt", "commits\ncode/\n"),
                       ("capture.txt", "Stop\n")):  # fmt: skip
        (runtime.state(box) / name).write_text(text)
    now = rows(runtime.call(box, "status", door="pipe"), "How this is set")
    assert now["names withheld"] == "2 names"
    assert now["commands denied"] == "1 command"
    assert now["left out of reports"] == "commits, code"
    assert now["moments kept as sent"] == "Stop"


def test_the_folders_own_needs_come_from_willows_digest_less_what_is_left_out(box):
    import time

    soon = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 3 * 86400))
    pile = box.parent / "pile"
    (pile / "diary.md").write_text(f"Dentist on {soon}, bring the form.\n")
    (pile / "commits").mkdir()
    (pile / "commits" / "a.txt").write_text(f"Release planned for {soon}.\n")
    got = runtime.call(box, "status", door="pipe")
    (name,) = [g["name"] for g in got["groups"] if g["name"].startswith("Coming up")]
    assert set(rows(got, name)) == {"diary.md:1", "commits/a.txt:1"}
    (runtime.state(box) / "report-skip.txt").write_text("commits\n")
    assert set(rows(runtime.call(box, "status", door="pipe"), name)) == {"diary.md:1"}


def test_a_part_that_cannot_be_looked_at_says_so_and_the_rest_still_shows(
    box, monkeypatch
):
    monkeypatch.setattr(runtime, "DIGEST", "no/such/digest.py")
    monkeypatch.setattr(runtime, "BOX_HEALTH", "no/such/health.py")
    got = runtime.call(box, "status", door="pipe")
    assert got["state"] == "populated"
    assert "couldn't look" in rows(got, "Your folder")
    assert rows(got, "Is it all right")["your record"].startswith("couldn't look: ")
    assert "How this is set" in [g["name"] for g in got["groups"]]


def test_it_is_the_persons_alone_and_writes_nothing_down_as_sent(box):
    for door in ("mcp", "hook", "guard"):
        assert runtime.call(box, "status", door=door)["code"] == "no_verb"
    runtime.call(box, "status", door="pipe")
    assert not (runtime.state(box) / "sent.jsonl").exists()


def test_a_record_that_will_not_open_is_said_in_plain_words(box):
    (box / "record.jsonl").write_text("not a record\n")
    got = runtime.call(box, "status", door="pipe")
    assert (got["state"], got["code"]) == ("refused", "record_broken") and got["say"]


def test_the_seal_page_shows_it_escaped_and_with_nothing_to_click_but_close(box):
    (runtime.state(box) / "report-skip.txt").write_text("<script>alert(1)</script>\n")
    html = seal_page.status_page(box, "tok")
    assert "<h1>How things stand</h1>" in html
    assert "Nothing waits on your seal." in html
    assert "<script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert html.count("<form") == 1 and 'value="quit"' in html
    for href in ('href="/"', 'href="/shared"'):
        assert href in html  # the way to the other two pages
    assert "/status" in seal_page.PAGES and json.dumps(html)
