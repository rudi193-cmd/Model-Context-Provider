"""Line 3 (grove one-script README:166): the model returns only proposed rows,
and the human seals."""

import json

from test_leave import seal

import runtime
import seal_page

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


def test_a_cite_the_model_was_never_given_never_stands(box):
    """Alone, it cites nothing on the page and is refused; beside a cite that
    is on the page, every cite was served fails and it is struck. Either way
    nothing is proposed."""
    sid = handed(box)
    rows = len((box / "record.jsonl").read_text().splitlines())
    got = runtime.call(box, "answer", "The first frost comes in late October [zzz].",
                       door="mcp")  # fmt: skip
    assert (got["state"], got["code"]) == ("refused", "no_cite")
    got = runtime.call(box, "answer", f"The first frost comes in late October [{sid}] [zzz].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "struck"
    assert got["checks"]["every cite was served"].startswith("failed")
    proposed = [
        json.loads(r) for r in (box / "record.jsonl").read_text().splitlines()[rows:]
    ]
    assert not [r for r in proposed if r["kind"] == "proposal"]


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


def test_reading_again_after_the_page_left_it_is_still_answerable(box):
    sid = handed(box)
    runtime.call(box, "read", "when is the car's MOT due", door="mcp")
    got = runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "waiting"


def test_an_answer_to_a_page_that_is_not_a_sealed_scope_is_refused(box):
    sid = handed(box)
    f = runtime.state(box) / "last-page.md"
    f.write_text(f.read_text().replace("late October", "late November"))
    got = runtime.call(box, "answer", f"The first frost comes in late November [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "refused"


def test_the_answer_names_the_scope_it_was_given(box):
    sid = handed(box)
    got = runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                       door="mcp")  # fmt: skip
    (w,) = runtime.call(box, "waiting", door="pipe")["waiting"]
    scopes = json.loads((runtime.state(box) / "scopes.json").read_text())
    assert w["seal"] == got["seal"] and next(iter(scopes)) in w["claim"]


def two(box):
    """A page of two passages on one question, sealed and given: their ids,
    the garden's first."""
    (box.parent / "pile" / "beds.md").write_text(
        "Cover the beds with straw before the first frost comes in late October.\n"
    )
    runtime.call(box, "read", Q, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    ids = {runtime.files_of(page)[b["id"]]: b["id"] for b in runtime.boxes_of(page)}
    assert set(ids) == {"garden.md", "beds.md"}, page
    return ids["garden.md"], ids["beds.md"]


def test_a_sentence_may_cite_part_of_its_page_and_what_it_left_out_is_shown(box):
    """The owner's ruling, 2026-11-19: at least one passage, not all of them.
    What it left out is kept by id and file, and the seal page shows it."""
    garden, beds = two(box)
    got = runtime.call(box, "answer", f"The first frost comes in late October [{garden}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "waiting" and got["left_out"] == [beds], got
    assert "every box cited" not in got["checks"]
    kept = runtime.checks_kept(box)[got["seal"]]
    assert (
        kept["left_out"] == [{"id": beds, "file": "beds.md"}] and kept["passages"] == 2
    )
    assert "straw" not in json.dumps(kept)  # by where, never by words
    shown = seal_page.left_out(kept)
    assert "Left out: 1 of the 2 on the page" in shown and "beds.md" in shown
    assert "every passage" in seal_page.left_out({**kept, "left_out": []})


def test_words_of_a_passage_it_does_not_cite_still_strike_it(box):
    garden, beds = two(box)
    got = runtime.call(box, "answer", f"Cover the beds with straw in late October [{garden}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "struck"
    assert got["checks"]["nothing the boxes lack"].startswith("failed")
    both = runtime.call(box, "answer",
                        f"Cover the beds with straw before the first frost [{garden}] [{beds}].",
                        door="mcp")  # fmt: skip
    assert both["state"] == "waiting" and both["left_out"] == []


def test_a_sentence_that_cites_nothing_on_the_page_is_refused(box):
    garden, _ = two(box)
    for sentence in ("The first frost comes in late October.",
                     "The first frost comes in late October [ffffffffffff]."):  # fmt: skip
        got = runtime.call(box, "answer", sentence, door="mcp")
        assert (got["state"], got["code"]) == ("refused", "no_cite"), sentence
    stray = runtime.call(box, "answer",
                         f"The first frost comes in late October [{garden}] [ffffffffffff].",
                         door="mcp")  # fmt: skip
    assert stray["state"] == "struck"
    assert stray["checks"]["every cite was served"].startswith("failed")
