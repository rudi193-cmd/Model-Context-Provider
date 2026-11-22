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


def sealed_check(box):
    return runtime.call(box, "check", door="pipe")


def test_each_session_seals_where_the_log_ended_and_check_holds_it_to_that(box):
    """No pin to keep by hand: a session's close puts where the sent log
    ended in the one proposal, so the person's seal pins its last line, and
    check with no pin holds the log to the last session they sealed."""
    from test_leave import seal

    told(box, 2)
    assert sealed_check(box)["state"] == "not sealed yet"
    got = runtime.call(box, "close", door="pipe")
    assert got["state"] == "waiting" and "log" not in got
    (w,) = [w for w in runtime.waiting(box)["waiting"] if w["seal"] == got["seal"]]
    assert w["claim"].endswith(", and your log's 2 lines")
    assert sealed_check(box)["state"] == "not sealed yet"  # waiting is no one's word
    seal(box, got["seal"])
    assert sealed_check(box)["state"] == "holds"
    told(box, 1)
    assert sealed_check(box)["said"] == "holds: 1 lines since"
    f = runtime.state(box) / "sent.jsonl"
    f.write_text("\n".join(lines(box)[:1]) + "\n")
    assert (
        runtime.call(box, "sent", door="pipe")["breaks"] == []
    )  # the chain can't see it
    assert sealed_check(box)["state"] == "cut short"


def test_a_log_that_doesnt_hold_is_left_out_of_the_seal_and_said(box):
    told(box, 2)
    ls = lines(box)
    (runtime.state(box) / "sent.jsonl").write_text("\n".join([ls[1], ls[0]]) + "\n")
    got = runtime.call(box, "close", door="pipe")
    assert got["state"] == "waiting"
    assert got["log"] == "not in the seal: the log doesn't hold at line 0"
    (w,) = [w for w in runtime.waiting(box)["waiting"] if w["seal"] == got["seal"]]
    assert "your log" not in w["claim"]
    assert sealed_check(box)["code"] == "log_changed"
