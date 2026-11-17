"""What left, written down by the runtime as it leaves."""

import hashlib
import json

from test_leave import seal

import runtime

FROST = "when does the first frost come"


def log(box):
    return runtime.call(box, "sent", door="pipe")


def test_nothing_reached_a_model_nothing_is_written(box, tmp_path):
    runtime.call(box, "read", FROST, door="pipe")  # the person's own read
    runtime.call(box, "leave", str(tmp_path / "out.md"), door="pipe")  # refused
    assert log(box)["state"] == "empty"


def test_the_one_bit_a_model_is_told_is_on_the_log(box):
    runtime.call(box, "read", FROST, door="mcp")
    (row,) = log(box)["rows"]
    assert (row["door"], row["verb"], row["state"]) == ("mcp", "read", "populated")


def test_a_page_is_logged_by_hashes_never_its_text(box):
    runtime.call(box, "read", FROST, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    page = runtime.call(box, "leave", door="mcp")["page"]
    row = log(box)["rows"][-1]
    assert row["page"] == hashlib.sha256(page.encode()).hexdigest()
    (text,) = [b["text"] for b in runtime.boxes_of(page)]
    assert row["passages"] == [hashlib.sha256(text.encode()).hexdigest()]
    raw = (runtime.state(box) / "sent.jsonl").read_text()
    assert "October" not in raw


def test_a_file_the_person_lets_leave_is_logged_with_where_it_went(box, tmp_path):
    runtime.call(box, "read", FROST, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])
    out = tmp_path / "out.md"
    runtime.call(box, "leave", str(out), door="pipe")
    row = log(box)["rows"][-1]
    assert (row["door"], row["verb"], row["to"]) == ("pipe", "leave", str(out))


def test_an_edited_or_cut_log_shows(box):
    for _ in range(3):
        runtime.call(box, "read", FROST, door="mcp")
    f = runtime.state(box) / "sent.jsonl"
    lines = f.read_text().splitlines()
    assert log(box)["breaks"] == []
    edited = json.loads(lines[1])
    edited["state"] = "empty"
    f.write_text(
        "\n".join([lines[0], json.dumps(edited, sort_keys=True), lines[2]]) + "\n"
    )
    assert log(box)["breaks"] == [2]
    f.write_text("\n".join([lines[0], lines[2]]) + "\n")
    assert log(box)["breaks"] == [1]


def test_a_model_cannot_read_the_log(box):
    assert runtime.call(box, "sent", door="mcp")["state"] == "refused"
