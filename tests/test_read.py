import runtime


def test_reading_needs_no_grant_and_cites_where(box):
    got = runtime.read(box, "when does the first frost come")
    assert got["state"] == "populated"
    assert [s["where"] for s in got["served"]] == ["garden.md:1"]


def test_a_question_the_pile_cannot_answer_is_empty_not_invented(box):
    assert runtime.read(box, "what colour is the boat")["state"] == "empty"
