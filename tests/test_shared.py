"""What did I share? The sent log as a person reads it: places, not hashes."""

import re

from test_leave import seal

import runtime

FROST = "when does the first frost come"


def shared(box):
    return runtime.call(box, "shared", door="pipe")


def test_nothing_shared_says_so(box):
    assert shared(box) == {"state": "empty", "lines": []}


def test_the_one_bit_reads_as_a_yes_or_no(box):
    runtime.call(box, "read", FROST, door="mcp")
    runtime.call(box, "read", "what colour is the boat", door="mcp")
    lines = shared(box)["lines"]
    assert lines[0].endswith(
        "the AI assistant (MCP): whether your files hold the question: yes"
    )
    assert lines[1].endswith(": no")


def test_a_page_reads_as_the_places_it_held_never_a_hash(box):
    runtime.call(box, "read", FROST, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    runtime.call(box, "leave", door="mcp")
    text = "\n".join(shared(box)["lines"])
    assert "the page you sealed: garden.md:1" in text
    assert not re.search(r"[0-9a-f]{32}", text) and "MOT" not in text


def test_a_page_sent_to_a_named_model_says_where_it_went(box):
    runtime.call(box, "read", FROST, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])

    def model(system, user):
        sid = re.search(r"`([0-9a-f]{12})`", user).group(1)
        return f"The first frost comes in late October [{sid}]."

    model.to = "gemma3:4b at http://127.0.0.1:11434/v1 (this machine)"
    runtime.call(box, "draft", FROST, door="mcp", ask=model)
    lines = shared(box)["lines"]
    assert any("gemma3:4b at http://127.0.0.1:11434/v1 (this machine): the page you sealed: garden.md:1" in ln for ln in lines)  # fmt: skip
    assert lines[-1].endswith("a sentence back, waiting on your seal")


def test_a_model_cannot_read_what_was_shared(box):
    assert runtime.call(box, "shared", door="mcp")["state"] == "refused"
