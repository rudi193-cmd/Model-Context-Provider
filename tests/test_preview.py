"""The page a scope would let leave, shown to the person before they seal it."""

from test_leave import seal

import runtime

FROST = "when does the first frost come"


def proposed(box):
    (runtime.state(box) / "names.txt").write_text("dahlias\n")
    runtime.call(box, "read", FROST, door="pipe")
    return runtime.call(box, "propose", door="pipe")["seal"]


def test_what_is_shown_before_the_seal_is_what_leaves_after_it(box):
    subject = proposed(box)
    got = runtime.call(box, "preview", subject, door="pipe")
    assert got["state"] == "preview", got
    (one,) = got["previews"]
    assert one["seal"] == subject and one["passages"] == 1
    assert "late October" in one["page"] and "garden.md" in one["page"]
    seal(box, subject)
    page = runtime.call(box, "leave", door="mcp")["page"]
    left = sorted(b["text"].strip() for b in runtime.boxes_of(page))
    assert left == runtime.scopes(box)[subject]
    assert all(t in one["page"] for t in left)


def test_a_preview_is_withheld_as_the_page_will_be(box):
    page = runtime.call(box, "preview", proposed(box), door="pipe")["previews"][0][
        "page"
    ]
    assert "dahlias" not in page and "[withheld: name]" in page


def test_with_no_seal_named_every_scope_waiting_is_shown(box):
    subject = proposed(box)
    got = runtime.call(box, "preview", True, door="pipe")
    assert [p["seal"] for p in got["previews"]] == [subject]
    seal(box, subject)
    assert runtime.call(box, "preview", True, door="pipe")["state"] == "empty"
    assert runtime.call(box, "preview", subject, door="pipe")["state"] == "preview"


def test_waiting_points_at_the_preview(box):
    subject = proposed(box)
    (item,) = runtime.call(box, "waiting", door="pipe")["waiting"]
    assert item["preview"] == {"preview": subject}


def test_a_preview_seals_nothing_and_sends_nothing(box):
    subject = proposed(box)
    log = runtime.state(box) / "sent.jsonl"
    before = log.read_bytes() if log.exists() else b""
    runtime.call(box, "preview", subject, door="pipe")
    assert (log.read_bytes() if log.exists() else b"") == before
    assert [
        w["seal"] for w in runtime.call(box, "waiting", door="pipe")["waiting"]
    ] == [subject]


def test_a_seal_not_proposed_here_is_refused(box):
    got = runtime.call(box, "preview", "proposal:" + "0" * 64, door="pipe")
    assert got["state"] == "refused" and got["code"] == "not_a_scope"


def test_a_model_cannot_preview(box):
    subject = proposed(box)
    got = runtime.call(box, "preview", subject, door="mcp")
    assert got["state"] == "refused" and got["code"] == "no_verb"
