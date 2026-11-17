"""A sealed scope leaves whole or not at all."""

from test_leave import seal

import runtime

Q = "when does the first frost come"


def two_passage_scope(box):
    pile = box.parent / "pile"
    (pile / "garden.md").write_text("The first frost comes in late October.\n")
    (pile / "garlic.md").write_text("Garlic goes in after the first frost.\n")
    runtime.call(box, "read", Q, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    return pile


def test_a_whole_scope_leaves(box):
    two_passage_scope(box)
    got = runtime.call(box, "leave", door="mcp")
    assert got["state"] == "left" and len(runtime.boxes_of(got["page"])) == 2


def test_a_passage_changed_since_the_seal_means_nothing_leaves(box):
    pile = two_passage_scope(box)
    (pile / "garlic.md").write_text("The first frost came early this year.\n")
    got = runtime.call(box, "leave", door="mcp")
    assert got["state"] == "refused" and "not whole" in got["why"]


def test_the_person_door_holds_the_same_rule(box, tmp_path):
    pile = two_passage_scope(box)
    (pile / "garlic.md").unlink()
    out = tmp_path / "out.md"
    assert runtime.call(box, "leave", str(out), door="pipe")["state"] == "refused"
    assert not out.exists()


def test_resealing_after_the_change_lets_the_new_scope_leave(box):
    pile = two_passage_scope(box)
    (pile / "garlic.md").write_text(
        "Garlic goes in after the first frost, in November.\n"
    )
    assert runtime.call(box, "leave", door="mcp")["state"] == "refused"
    # these exact words are sealed now, so the kernel answers them with the
    # seal; a new scope is asked in other words
    runtime.call(box, "read", "the first frost comes when", door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    assert runtime.call(box, "leave", door="mcp")["state"] == "left"
