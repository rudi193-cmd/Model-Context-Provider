import runtime


def test_reading_needs_no_grant_and_cites_where(box):
    got = runtime.read(box, "when does the first frost come")
    assert got["state"] == "populated"
    assert [s["where"] for s in got["served"]] == ["garden.md:1"]


def test_a_question_the_pile_cannot_answer_is_empty_not_invented(box):
    assert runtime.read(box, "what colour is the boat")["state"] == "empty"


def test_a_question_with_no_words_is_refused_as_that_and_asks_nothing(box):
    rows = len((box / "record.jsonl").read_text().splitlines())
    # each door's own verbs: the pipe has no context, the hook no read
    for door, verb in (("mcp", "read"), ("mcp", "context"), ("pipe", "read"),
                       ("hook", "context")):  # fmt: skip
        got = runtime.call(box, verb, "  ", door=door)
        assert (got["state"], got["code"]) == ("refused", "no_question"), (door, verb)
        assert "record" not in got["say"]  # the record is fine
    assert len((box / "record.jsonl").read_text().splitlines()) == rows  # no row
