"""A reply that isn't a refusal still says what to do next: something that
waits on the person, a struck sentence, a bare "populated". A struck one
names the passage, on the page but not cited, that holds the word it added.
The words added never carry a word of the files, and the person's own door
is answered as it was."""

from test_answer import Q, handed, two

import runtime


def model(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="mcp", where="/work/a", session="s1")


def test_a_reply_that_waits_says_on_whom_and_where(box):
    got = model(box, "grant")
    assert got["state"] == "waiting"
    assert "a session asking to read your files" in got["say"]
    assert got["next"].startswith("Tell the person:") and "seal page" in got["next"]


def test_a_bare_populated_says_the_two_ways_on(box):
    got = model(box, "context", Q)
    assert got["state"] == "populated" and "grant" in got["next"]
    assert "page, action propose" in got["next"]


def test_a_struck_sentence_names_the_passage_holding_the_word_it_added(box):
    garden, beds = two(box)
    got = model(box, "answer", f"Cover the beds with straw in late October [{garden}].")
    assert got["state"] == "struck"
    assert got["in_uncited"] == {"cover": beds, "beds": beds, "straw": beds}
    assert f"[{beds}]" in got["next"] and "Cite that passage too" in got["next"]
    assert got["say"].startswith("Your sentence was struck, and goes nowhere: ")


def test_a_struck_sentence_with_nothing_on_the_page_says_to_keep_to_its_cites(box):
    sid = handed(box)
    got = model(box, "answer", f"The first frost comes in early October [{sid}].")
    assert got["state"] == "struck" and "in_uncited" not in got
    assert "only what the passages you cite hold" in got["next"]


def test_the_words_added_carry_no_word_of_the_files(box):
    for got in (model(box, "context", Q), model(box, "grant")):
        words = got["say"] + " " + got["next"]
        for w in ("frost", "October", "dahlias", "garden", "MOT", "car.md"):
            assert w not in words, (w, words)


def test_the_persons_door_is_answered_as_it_was(box):
    got = runtime.call(box, "waiting", door="pipe")
    assert "next" not in got or got.get("state") == "refused"
