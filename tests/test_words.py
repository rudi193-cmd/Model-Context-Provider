"""A box made with the person's own words, as the UI's Start makes it: their
words reach their files through every door, with nothing in the runtime."""

import json
import os

import pytest
from test_leave import seal

import runtime

ASK = "when is the inspection"  # their word; the file says MOT


@pytest.fixture
def worded(tmp_path):
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "car.md").write_text("The car's MOT is due on the 3rd of March.\n")
    words = tmp_path / "my-words.txt"  # beside the box, readable only by them
    words.write_text("# your own words, as you sealed them\ninspection = mot\n")
    os.chmod(words, 0o600)

    def made(with_words):
        box = tmp_path / ("worded" if with_words else "plain")
        argv = ["kernel.py", "init", "--box", str(box), "--pile", str(pile),
                "--key", str(tmp_path / "test.key")]  # fmt: skip
        if with_words:
            argv += ["--words", str(words)]
        run = runtime.willow(*argv)
        assert run.returncode == 0, run.stderr
        return box

    return made


def test_without_their_words_the_model_hears_nothing_is_there(worded):
    assert runtime.call(worded(False), "read", ASK, door="mcp") == {"state": "empty"}


def test_with_their_words_the_same_question_finds_the_file(worded):
    assert runtime.call(worded(True), "read", ASK, door="mcp") == {"state": "populated"}


def test_their_words_carry_the_whole_way_to_a_sealed_page(worded):
    box = worded(True)
    runtime.call(box, "read", ASK, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    assert "MOT is due on the 3rd of March" in page


def test_the_words_list_itself_never_leaves(worded):
    box = worded(True)
    runtime.call(box, "read", ASK, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    assert "inspection" not in page.lower()
    rows = runtime.call(box, "sent", door="pipe")["rows"]
    assert "inspection" not in json.dumps(rows)
