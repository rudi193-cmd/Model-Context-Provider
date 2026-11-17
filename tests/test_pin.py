"""The sent log's end, pinned where the runtime can't reach."""

import json

import pytest

import runtime

FROST = "when does the first frost come"


@pytest.fixture
def away(tmp_path_factory):
    """Somewhere the box's folder isn't: a stick, another machine."""
    return tmp_path_factory.mktemp("usb") / "pin.json"


def told(box, n):
    for _ in range(n):
        runtime.call(box, "read", FROST, door="mcp")


def pin(box, to):
    return runtime.call(box, "pin", str(to), door="pipe")


def check(box, at):
    return runtime.call(box, "check", str(at), door="pipe")


def lines(box):
    return (runtime.state(box) / "sent.jsonl").read_text().splitlines()


def test_a_log_that_only_grew_holds(box, away):
    told(box, 2)
    assert pin(box, away)["rows"] == 2
    told(box, 3)
    assert check(box, away) == {"state": "holds", "pinned": 2, "since": 3}


def test_a_cut_the_chain_cannot_see_the_pin_does(box, away):
    told(box, 3)
    pin(box, away)
    f = runtime.state(box) / "sent.jsonl"
    f.write_text("\n".join(lines(box)[:2]) + "\n")
    assert (
        runtime.call(box, "sent", door="pipe")["breaks"] == []
    )  # the chain can't see it
    assert check(box, away)["state"] == "cut short"


def test_an_edit_to_the_last_line_the_pin_sees(box, away):
    told(box, 2)
    pin(box, away)
    ls = lines(box)
    last = json.loads(ls[-1])
    last["state"] = "empty"
    (runtime.state(box) / "sent.jsonl").write_text(
        "\n".join([*ls[:-1], json.dumps(last, sort_keys=True)]) + "\n"
    )
    assert runtime.call(box, "sent", door="pipe")["breaks"] == []
    assert check(box, away) == {"state": "rewritten", "at": 1}


def test_a_pin_is_never_written_over_or_kept_beside_the_box(box, away):
    told(box, 1)
    assert pin(box, away)["state"] == "pinned"
    assert pin(box, away)["state"] == "refused"
    assert pin(box, box.parent / "pin.json")["state"] == "refused"


def test_a_model_can_neither_pin_nor_check(box, away):
    for verb in ("pin", "check"):
        assert runtime.call(box, verb, str(away), door="mcp")["state"] == "refused"


def test_what_is_not_a_pin_is_refused(box, tmp_path_factory):
    bad = tmp_path_factory.mktemp("usb") / "pin.json"
    bad.write_text("not a pin")
    assert check(box, bad)["state"] == "refused"
