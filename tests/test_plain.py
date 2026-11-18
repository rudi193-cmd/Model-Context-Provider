"""Every refusal a person can meet, in plain words with one next step."""

import json
import re
from pathlib import Path

import pytest
from test_leave import seal

import runtime

FROST = "when does the first frost come"
JARGON = re.compile(
    r"(?<![.\w])(bite|kernel|proposal:|scope|stderr|exit|json|None)\b", re.IGNORECASE
)


def sealed(box):
    runtime.call(box, "read", FROST, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])


def away(tmp_path_factory):
    return tmp_path_factory.mktemp("usb")


def scenario(code, box, tmp_path_factory, monkeypatch):
    """Reach the refusal with this code, through a door, as a person would."""
    usb = away(tmp_path_factory)
    if code == "record_broken":
        (box / "record.jsonl").write_text("not a record\n")
        return runtime.call(box, "read", FROST, door="pipe")
    if code == "nothing_to_scope":
        return runtime.call(box, "propose", door="pipe")
    if code == "not_sealed":
        return runtime.call(box, "leave", str(usb / "out.md"), door="pipe")
    if code == "not_whole":
        sealed(box)
        (box.parent / "pile" / "garden.md").write_text("Nothing about frost now.\n")
        return runtime.call(box, "leave", door="mcp")
    if code == "scrub_failed":
        sealed(box)
        monkeypatch.setattr(runtime, "PRIVACY", "no/such/privacy.py")
        return runtime.call(box, "leave", door="mcp")
    if code == "inside":
        return runtime.call(box, "leave", str(box / "out.md"), door="pipe")
    if code == "no_page":
        return runtime.call(box, "answer", "Frost [x].", door="mcp")
    if code == "not_scope":
        sealed(box)
        page = runtime.call(box, "leave", door="mcp")["page"]
        (sid,) = [b["id"] for b in runtime.boxes_of(page)]
        f = runtime.state(box) / "last-page.md"
        f.write_text(f.read_text().replace("late October", "late May"))
        return runtime.call(box, "answer", f"The first frost comes in late May [{sid}].", door="mcp")  # fmt: skip
    if code == "check_failed":
        sealed(box)
        runtime.call(box, "leave", door="mcp")
        monkeypatch.setattr(runtime, "SENTENCE_CHECK", "no/such/check.py")
        return runtime.call(box, "answer", "x", door="mcp")
    if code == "answer_refused":
        sealed(box)
        page = runtime.call(box, "leave", door="mcp")["page"]
        (sid,) = [b["id"] for b in runtime.boxes_of(page)]
        real = runtime.willow
        monkeypatch.setattr(runtime, "willow", lambda *a: real(*a[:1], "--stray") if a[1:2] == ("propose",) else real(*a))  # fmt: skip
        return runtime.call(box, "answer", f"The first frost comes in late October [{sid}].", door="mcp")  # fmt: skip
    if code == "no_model":
        sealed(box)
        return runtime.call(box, "draft", FROST, door="pipe")
    if code == "model_json":
        (runtime.state(box) / "model.json").write_text(
            '{"url": "https://far.example/v1", "model": "m"}'
        )
        return runtime.call(box, "draft", FROST, door="pipe")
    if code == "model_failed":
        sealed(box)
        (runtime.state(box) / "model.json").write_text(
            '{"url": "http://127.0.0.1:9/v1", "model": "m"}'
        )
        return runtime.call(box, "draft", FROST, door="pipe")
    if code == "no_verb":
        return runtime.call(box, "seal", "x", door="mcp")
    if code == "backup_place":
        return runtime.call(box, "backup", str(box), door="pipe")
    if code == "exists":
        runtime.call(box, "read", FROST, door="mcp")
        runtime.call(box, "pin", str(usb / "pin.json"), door="pipe")
        return runtime.call(box, "pin", str(usb / "pin.json"), door="pipe")
    if code == "copy_bad":
        monkeypatch.setattr(runtime, "chain_holds", lambda lines: False)
        return runtime.call(box, "backup", str(usb), door="pipe")
    if code == "log_changed":
        runtime.call(box, "read", FROST, door="mcp")
        runtime.call(box, "read", FROST, door="mcp")
        f = runtime.state(box) / "sent.jsonl"
        first, second = f.read_text().splitlines()
        f.write_text(first.replace("populated", "empty") + "\n" + second + "\n")
        return runtime.call(box, "pin", str(usb / "pin.json"), door="pipe")
    if code == "pin_beside":
        return runtime.call(box, "pin", str(box.parent / "pin.json"), door="pipe")
    if code == "not_pin":
        (usb / "pin.json").write_text("hello")
        return runtime.call(box, "check", str(usb / "pin.json"), door="pipe")
    if code == "stopped":
        sealed(box)
        subject = runtime.call(box, "scopes", door="pipe")["scopes"][0]["seal"]
        runtime.call(box, "stop", subject, door="pipe")
        return runtime.call(box, "leave", door="mcp")
    if code == "not_a_scope":
        return runtime.call(box, "stop", "proposal:" + "0" * 64, door="pipe")
    if code == "not_waiting":
        return runtime.call(box, "later", "proposal:" + "0" * 64, door="pipe")
    if code == "session_failed":
        monkeypatch.setattr(runtime, "SESSION_SEAL", "no/such/session_seal.py")
        return runtime.call(box, "close", door="pipe")
    if code == "no_box":
        return runtime.call(usb / "gone", "restore", str(usb / "x.zip"), door="pipe")
    if code == "not_backup":
        (usb / "x.zip").write_text("hello")
        return runtime.call(box, "restore", str(usb / "x.zip"), door="pipe")
    if code == "restore_over":
        (runtime.state(box) / "names.txt").write_text("Aoife\n")
        made = runtime.call(box, "backup", str(usb), door="pipe")["runtime"]
        (runtime.state(box) / "names.txt").write_text("Brigid\n")
        return runtime.call(box, "restore", str(usb / made), door="pipe")
    if code == "capture_refused":
        return runtime.call(box, "capture", "  ", door="mcp")
    if code == "no_resource":
        return runtime.call(box, "resource", "provider://key/the-key", door="mcp")
    if code == "no_prompt":
        return runtime.call(box, "prompt", {"name": "horoscope"}, door="mcp")
    if code == "no_report":
        return runtime.call(box, "report", "horoscope", door="mcp")
    if code == "report_failed":
        monkeypatch.setitem(runtime.REPORTS, "todo", "no/such/todo.py")
        return runtime.call(box, "report", "todo", door="mcp")
    if code == "report_too_long":
        (box.parent / "pile" / "chores.md").write_text("TODO: order the tubers.\n")
        monkeypatch.setattr(runtime, "REPORT_MOST", 10)
        return runtime.call(box, "report", "todo", door="mcp")
    if code == "shelf_refused":
        return runtime.call(box, "shelf_add", {"name": "../x", "text": "t"},
                            door="mcp", where=str(usb))  # fmt: skip
    if code == "not_on_shelf":
        return runtime.call(box, "shelf_read", "nope.md", door="mcp", where=str(usb))
    if code == "event_unread":
        return runtime.call(box, "event", "not json", door="guard")
    if code == "guard_failed":
        monkeypatch.setattr(runtime, "HOOK_GUARD", "no/such/guard.py")
        call = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": "ls"}}  # fmt: skip
        return runtime.call(box, "event", call, door="guard")
    if code == "willow_unpinned":
        monkeypatch.setattr(runtime, "PIN", usb / "no-pin.json")
        return runtime.call(box, "read", FROST, door="pipe")
    raise AssertionError(f"no scenario for {code}")


@pytest.mark.parametrize("code", sorted(runtime.PLAIN))
def test_every_refusal_is_plain_with_a_next_step(
    code, box, tmp_path_factory, monkeypatch
):
    got = scenario(code, box, tmp_path_factory, monkeypatch)
    assert got["state"] == "refused" and got["code"] == code, got
    assert got["say"] and got["next"], got
    assert not JARGON.search(got["say"]), got["say"]


def test_every_code_in_the_runtime_has_plain_words_and_every_plain_word_a_code():
    src = (Path(runtime.__file__)).read_text()
    used = set(re.findall(r'"code": "([a-z_]+)"', src))
    assert used == set(runtime.PLAIN)


def test_a_models_door_is_told_what_to_tell_the_person(box):
    got = runtime.call(box, "leave", door="mcp")
    assert got["next"].startswith("Tell the person: ")
    assert not runtime.call(box, "leave", "/x", door="pipe")["next"].startswith("Tell")


def test_the_refusals_own_words_stay_for_whoever_needs_the_detail(box):
    got = runtime.call(box, "propose", door="pipe")
    assert got["why"] and got["say"] != got["why"]
    json.dumps(got)
