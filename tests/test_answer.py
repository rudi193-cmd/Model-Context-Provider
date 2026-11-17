"""Line 3 (grove one-script README:166): the model returns only proposed rows,
and the human seals."""

import json

from test_leave import seal

import runtime

Q = "when does the first frost come"


def handed(box):
    """A model's whole way in: read, propose, the person seals, the page leaves."""
    runtime.call(box, "read", Q, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    (sid,) = [b["id"] for b in runtime.boxes_of(page)]
    return sid


def test_a_sentence_that_stands_is_proposed_and_waits_for_the_seal(box):
    sid = handed(box)
    got = runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "waiting", got
    rows = [json.loads(r) for r in (box / "record.jsonl").read_text().splitlines()]
    assert rows[-1]["kind"] == "proposal" and rows[-1]["verdict"] == "pass"
    assert not (box / "written" / got["path"]).exists()  # nothing written until sealed


def test_a_sentence_that_adds_to_the_page_is_struck_and_goes_nowhere(box):
    sid = handed(box)
    before = (box / "record.jsonl").read_text()
    got = runtime.call(box, "answer", f"The first frost comes in early October [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "struck"
    assert got["checks"]["nothing the boxes lack"].startswith("failed")
    assert (box / "record.jsonl").read_text() == before


def test_a_cite_the_model_was_never_given_is_struck(box):
    handed(box)
    got = runtime.call(box, "answer", "The first frost comes in late October [zzz].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "struck"


def test_an_answer_before_anything_left_is_refused(box):
    got = runtime.call(box, "answer", "The frost comes in October.", door="mcp")
    assert got["state"] == "refused"


def test_the_person_door_has_no_answer_verb(box):
    assert runtime.call(box, "answer", "x", door="pipe")["state"] == "refused"


def test_the_whole_way_round_ends_in_a_file_only_the_person_sealed(box):
    sid = handed(box)
    sentence = f"The first frost comes in late October [{sid}]."
    got = runtime.call(box, "answer", sentence, door="mcp")
    seal(box, got["seal"])
    assert (box / "written" / got["path"]).read_text() == sentence + "\n"


def test_reading_again_after_the_page_left_means_the_old_page_is_not_answerable(box):
    sid = handed(box)
    runtime.call(box, "read", "when is the car's MOT due", door="mcp")
    got = runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "refused"
