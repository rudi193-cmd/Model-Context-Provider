"""Names, numbers and addresses kept out of a page, even a sealed one."""

import pytest
from test_leave import seal

import runtime

Q = "when does the first frost come"


def page(box):
    runtime.call(box, "read", Q, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    return runtime.call(box, "leave", door="mcp")


def with_neighbour(box):
    (box.parent / "pile" / "garden.md").write_text(
        "The first frost comes in late October; Aoife on 07700 900123 says so.\n"
    )


def test_numbers_and_emails_are_withheld_from_a_sealed_page(box):
    with_neighbour(box)
    got = page(box)["page"]
    assert "07700" not in got and "[withheld: phone]" in got


def test_a_name_the_person_listed_is_withheld_wherever_it_sits(box):
    with_neighbour(box)
    (runtime.state(box) / "names.txt").write_text("aoife\n")
    got = page(box)["page"]
    assert "Aoife" not in got and "[withheld: name]" in got
    assert "first frost comes in late October" in got


def test_a_name_inside_another_word_is_left(box):
    (box.parent / "pile" / "garden.md").write_text(
        "The first frost comes in late October; Annabel saw it.\n"
    )
    (runtime.state(box) / "names.txt").write_text("Anna\n")
    assert "Annabel" in page(box)["page"]


def test_a_withheld_page_can_still_be_answered(box):
    with_neighbour(box)
    (runtime.state(box) / "names.txt").write_text("Aoife\n")
    got = page(box)
    (sid,) = [b["id"] for b in runtime.boxes_of(got["page"])]
    said = runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                        door="mcp")  # fmt: skip
    assert said["state"] == "waiting", said


def test_a_withheld_page_still_reaches_its_own_question_through_the_hook(box):
    with_neighbour(box)
    (runtime.state(box) / "names.txt").write_text("Aoife\n")
    runtime.call(box, "read", Q, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])
    got = runtime.call(box, "context", Q, door="hook")
    assert got["state"] == "left" and "Aoife" not in got["page"]


def test_a_key_with_no_end_withholds_its_own_text_and_no_other(box):
    """A private key's BEGIN with no END ran to the end of the one pass, and
    with a whole key further on, every text after it came back as the one two
    places later: a passage under another's place, and the last ones gone."""
    half = "notes: -----BEGIN RSA PRIVATE KEY----- (the old one, cut here)"
    whole = "-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----"
    texts = ["first frost", half, "the fence", whole, "the dahlias", "the gate"]
    got = runtime.withhold(box, texts)
    assert got == ["first frost", "notes: [withheld: key]", "the fence",
                   "[withheld: key]", "the dahlias", "the gate"]  # fmt: skip


def test_a_text_that_cannot_come_back_whole_lets_nothing_leave(box, monkeypatch):
    real = runtime.scrub
    monkeypatch.setattr(runtime, "scrub", lambda ts: real(ts)[:-1] or [])
    with pytest.raises(RuntimeError, match="didn't come back whole"):
        runtime.withhold(box, ["one", "two"])


def test_a_code_that_opens_something_is_withheld_and_what_it_opens_kept(box):
    """Seen on a page from a made-up phone backup, beside a phone number that
    was withheld: Willow's privacy now knows a code by what it opens."""
    (box.parent / "pile" / "garden.md").write_text(
        "The first frost comes in late October. Gate code is 4471.\n"
    )
    got = page(box)["page"]
    assert "4471" not in got and "Gate code is [withheld: code]" in got
