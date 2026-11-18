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
    if code == "no_skill":
        return runtime.call(box, "skill", "nope", door="mcp")
    if code == "skill_refused":
        return runtime.call(
            box, "skill_add", {"path": str(box / "record.jsonl")}, door="pipe"
        )
    if code == "skill_too_long":
        (usb / "long.md").write_text("Do a thing. " * 20)
        monkeypatch.setattr(runtime, "SKILL_MOST", 10)
        return runtime.call(
            box, "skill_add", {"path": str(usb / "long.md")}, door="pipe"
        )
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
    if code in BRING:
        return BRING[code](box, tmp_path_factory)
    if code == "willow_unpinned":
        monkeypatch.setattr(runtime, "PIN", usb / "no-pin.json")
        return runtime.call(box, "read", FROST, door="pipe")
    if code in ("task_refused", "no_such_task", "task_taken", "task_not_held"):
        here = str(usb)
        words = {"text": "Order the tubers.", "project": ""}
        if code == "task_refused":
            return runtime.call(box, "task_add", {"text": " ", "project": ""},
                                door="mcp", where=here)  # fmt: skip
        if code == "no_such_task":
            return runtime.call(box, "task_claim", "model-" + "a1" * 6, door="mcp", where=here)  # fmt: skip
        added = runtime.call(box, "task_add", words, door="mcp", where=here)
        seal(box, added["seal"])
        runtime.note_session(box, {"cwd": here, "session_id": "first"})
        if code == "task_not_held":
            return runtime.call(box, "task_done", {"id": added["task"], "result": "x"},
                                door="mcp", where=here)  # fmt: skip
        runtime.call(box, "task_claim", added["task"], door="mcp", where=here)
        runtime.note_session(box, {"cwd": here, "session_id": "second"})
        return runtime.call(box, "task_claim", added["task"], door="mcp", where=here)
    if code == "notes_too_long":
        seal(box, runtime.call(box, "capture", "A note to keep.", door="mcp")["seal"])
        monkeypatch.setattr(runtime, "NOTES_MOST", 5)
        return runtime.call(box, "notes", door="mcp")
    raise AssertionError(f"no scenario for {code}")


def _bring(box, src, kind="notes", name="mine"):
    arg = {"kind": kind, "from": str(src), "as": name}
    return runtime.call(box, "bring_in", arg, door="pipe")


def _vault(tmp_path_factory):
    v = tmp_path_factory.mktemp("vault")
    (v / "a.md").write_text("Rosemary is potted in April.\n")
    return v


def _bring_exists(box, tmp_path_factory):
    _bring(box, _vault(tmp_path_factory))
    return _bring(box, _vault(tmp_path_factory))


def _bring_record(box, tmp_path_factory):
    (runtime.state(box) / "brought-in.json").write_text("not json")
    return runtime.call(box, "brought_in", door="pipe")


def _bring_no_folder(box, tmp_path_factory):
    (box / "kernel.json").write_text(json.dumps({"pile": str(box.parent / "gone")}))
    return _bring(box, _vault(tmp_path_factory))


#: how each refusal of bring_in is reached (used by scenario above)
BRING = {
    "bring_what": lambda box, t: _bring(box, _vault(t), kind="photos"),
    "bring_name": lambda box, t: _bring(box, _vault(t), name="../x"),
    "bring_no_folder": _bring_no_folder,
    "bring_inside": lambda box, t: _bring(box, box.parent / "pile"),
    "bring_exists": _bring_exists,
    "bring_nothing": lambda box, t: _bring(box, t.mktemp("empty")),
    "bring_failed": lambda box, t: _bring(box, box.parent / "no-such-folder"),
    "bring_record": _bring_record,
}


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
