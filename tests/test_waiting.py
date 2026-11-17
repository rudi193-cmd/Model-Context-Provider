"""What waits on the person, said so they can seal it knowing what it is."""

from test_leave import seal

import runtime

FROST = "when does the first frost come"


def waits(box):
    return runtime.call(box, "waiting", door="pipe")


def test_nothing_waits_on_a_new_box(box):
    assert waits(box) == {"state": "empty", "waiting": []}


def test_a_scope_waits_and_says_it_is_one(box):
    runtime.call(box, "read", FROST, door="mcp")
    subj = runtime.call(box, "propose", door="mcp")["seal"]
    (w,) = waits(box)["waiting"]
    assert w["seal"] == subj and w["claim"]


def test_a_models_sentence_waits_in_its_own_words(box):
    runtime.call(box, "read", FROST, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    (sid,) = [b["id"] for b in runtime.boxes_of(page)]
    said = f"The first frost comes in late October [{sid}]."
    got = runtime.call(box, "answer", said, door="mcp")
    (w,) = waits(box)["waiting"]
    assert (w["seal"], w["path"], w["words"]) == (got["seal"], got["path"], said + "\n")
    seal(box, w["seal"])
    assert waits(box)["state"] == "empty"


def test_a_model_cannot_see_what_waits_on_the_person(box):
    assert runtime.call(box, "waiting", door="mcp")["state"] == "refused"
