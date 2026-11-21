"""The shelf: where a session puts what it makes for the project it is
working on. Beside the box, never in it; no seal, since nothing on it was
ever the person's files and nothing on it leaves."""

import json
import subprocess
import sys
from pathlib import Path

from test_guard import guard

import runtime

ROOT = Path(__file__).resolve().parents[1]
REPORT = "# Findings\n\nThe build breaks on Python 3.9.\n"


def put(box, where, name="report.md", text=REPORT, door="mcp"):
    return runtime.call(box, "shelf_add", {"name": name, "text": text},
                        door=door, where=str(where))  # fmt: skip


def test_what_a_session_shelves_it_can_list_and_read_back_with_no_seal(box, tmp_path):
    proj = tmp_path / "proj"
    assert put(box, proj) == {"state": "shelved", "name": "report.md"}
    listed = runtime.call(box, "shelf_list", door="mcp", where=str(proj))
    assert listed["project"] == str(proj)
    assert [(i["name"], i["chars"]) for i in listed["items"]] == [("report.md", len(REPORT))]  # fmt: skip
    got = runtime.call(box, "shelf_read", "report.md", door="mcp", where=str(proj))
    assert (got["state"], got["says"]) == ("taken", REPORT)
    assert runtime.waiting(box)["state"] == "empty"  # nothing waits on a seal


def test_it_lives_beside_the_box_never_in_it_or_in_the_folder_it_reads(box, tmp_path):
    put(box, tmp_path / "proj")
    (kept,) = (runtime.state(box) / "shelf").glob("proj-*/report.md")
    assert kept.read_text() == REPORT
    for inside in (box, box.parent / "pile", tmp_path / "proj"):
        assert not list(inside.rglob("report.md")) if inside.exists() else True
    # and a question never finds it as if the person had written it
    assert runtime.read(box, "what breaks the build on Python 3.9")["state"] == "empty"


def test_each_project_has_its_own_shelf(box, tmp_path):
    put(box, tmp_path / "a" / "site")
    put(box, tmp_path / "b" / "site", text="the other site\n")  # the same name
    here = runtime.call(box, "shelf_read", "report.md", door="mcp", where=str(tmp_path / "a" / "site"))  # fmt: skip
    assert here["says"] == REPORT
    assert runtime.call(box, "shelf_list", door="mcp", where=str(tmp_path / "c"))["items"] == []  # fmt: skip
    got = runtime.call(
        box, "shelf_read", "report.md", door="mcp", where=str(tmp_path / "c")
    )
    assert got["code"] == "not_on_shelf"


def test_nothing_on_a_shelf_is_written_over(box, tmp_path):
    proj = tmp_path / "proj"
    put(box, proj)
    assert put(box, proj) == {"state": "shelved", "name": "report.md", "same": True}
    assert put(box, proj, text="a second look\n")["name"] == "report.2.md"
    assert put(box, proj, text="a third\n")["name"] == "report.3.md"
    first = runtime.call(box, "shelf_read", "report.md", door="mcp", where=str(proj))
    assert first["says"] == REPORT


def test_a_name_is_one_plain_file_name_and_the_words_are_some(box, tmp_path):
    proj = tmp_path / "proj"
    for name in ("../x", "a/b", "/etc/passwd", ".hidden", "", "x" * 81, "mine.key", None):  # fmt: skip
        got = put(box, proj, name=name)
        assert (got["state"], got["code"]) == ("refused", "shelf_refused"), name
    for text in ("", "   ", None, "x" * (runtime.SHELF_MOST + 1)):
        assert put(box, proj, text=text)["code"] == "shelf_refused"
    assert put(box, "")["code"] == "shelf_refused"  # a door with no folder to name
    assert not (runtime.state(box) / "shelf").exists() or not list(
        (runtime.state(box) / "shelf").rglob("*.md")
    )


def test_take_never_reads_outside_the_shelf(box, tmp_path):
    proj = tmp_path / "proj"
    put(box, proj)
    for name in ("../../sent.jsonl", "../proj-x.json", str(box / "record.jsonl"), None):
        got = runtime.call(box, "shelf_read", name, door="mcp", where=str(proj))
        assert got["code"] == "not_on_shelf", name


def test_what_is_shelved_and_read_back_is_on_the_sent_log_by_hash(box, tmp_path):
    proj = tmp_path / "proj"
    put(box, proj)
    runtime.call(box, "shelf_read", "report.md", door="mcp", where=str(proj))
    log = (runtime.state(box) / "sent.jsonl").read_text()
    assert "Findings" not in log and "3.9" not in log
    lines = runtime.call(box, "shared", door="pipe")["lines"]
    assert "put on its project's shelf" in lines[0]
    assert "read back from its project's shelf" in lines[1]


def test_the_person_sees_every_shelf_and_reads_any_of_it(box, tmp_path):
    put(box, tmp_path / "a")
    put(box, tmp_path / "b", name="notes.txt")
    seen = runtime.call(box, "shelves", door="pipe")["shelves"]
    assert sorted(s["project"] for s in seen) == [str(tmp_path / "a"), str(tmp_path / "b")]  # fmt: skip
    got = runtime.call(box, "shelf_read", {"project": str(tmp_path / "b"), "name": "notes.txt"}, door="pipe")  # fmt: skip
    assert got["says"] == REPORT
    assert runtime.call(box, "shelves", door="mcp")["code"] == "no_verb"


def test_a_thing_on_the_shelf_says_which_session_put_it_there(box, tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    start = {"hook_event_name": "SessionStart", "session_id": "s7", "cwd": str(proj)}
    assert guard(box, start).returncode == 0
    put(box, proj)
    (item,) = runtime.call(box, "shelf_list", door="mcp", where=str(proj))["items"]
    assert item["session"] == "s7" and item["when"]


def test_a_moment_the_person_names_goes_on_the_shelf_as_the_host_sent_it(box, tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    failed = {"hook_event_name": "PostToolUseFailure", "session_id": "s1",
              "cwd": str(proj), "tool_name": "Bash",
              "tool_input": {"command": "make test"}, "error": "Exit code 2"}  # fmt: skip
    assert guard(box, failed).returncode == 0
    assert runtime.call(box, "shelf_list", door="mcp", where=str(proj))["items"] == []
    (runtime.state(box) / "capture.txt").write_text("PostToolUseFailure\n")
    run = guard(box, failed)
    assert (run.returncode, run.stdout) == (0, "")  # the model is told nothing
    (item,) = runtime.call(box, "shelf_list", door="mcp", where=str(proj))["items"]
    assert item["name"].startswith("event-PostToolUseFailure-")
    got = runtime.call(box, "shelf_read", item["name"], door="mcp", where=str(proj))
    assert json.loads(got["says"]) == failed
    assert runtime.waiting(box)["state"] == "empty"  # and nothing waits on a seal


def test_the_shelves_go_in_the_backup_and_come_back(box, tmp_path):
    proj, usb = tmp_path / "proj", tmp_path / "usb"
    usb.mkdir()
    put(box, proj)
    made = runtime.call(box, "backup", str(usb), door="pipe")
    assert any(f.startswith("shelf/proj-") and f.endswith("/report.md") for f in made["files"])  # fmt: skip
    (kept,) = (runtime.state(box) / "shelf").glob("proj-*/report.md")
    kept.unlink()
    got = runtime.call(box, "restore", str(usb / made["runtime"]), door="pipe")
    assert got["state"] == "restored" and kept.read_text() == REPORT


def test_a_backup_cannot_put_a_file_anywhere_but_beside_the_box(box, tmp_path):
    import zipfile

    for name in ("shelf/../../x", "shelf/a/b/c", "other/x", "shelf/a/../../x"):
        z = tmp_path / "bad.zip"
        with zipfile.ZipFile(z, "w") as f:
            f.writestr(name, "x")
        got = runtime.call(box, "restore", str(z), door="pipe")
        assert got["code"] == "not_backup", name


def mcp(box, cwd, *messages):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        input="".join(json.dumps(m) + "\n" for m in messages),
        capture_output=True, text=True, check=False, cwd=cwd,
    )  # fmt: skip
    return [json.loads(line)["result"]["structuredContent"] for line in run.stdout.splitlines()]  # fmt: skip


def tool(i, verb, arguments=None):
    return {"jsonrpc": "2.0", "id": i, "method": "tools/call",
            "params": {"name": verb, "arguments": arguments or {}}}  # fmt: skip


def test_the_mcp_door_shelves_under_the_folder_the_client_started_it_in(box, tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    put_, listed, got = mcp(
        box, proj,
        tool(1, "shelf", {"action": "add", "name": "report.md", "text": REPORT}),
        tool(2, "shelf", {"action": "list"}),
        tool(3, "shelf", {"action": "read", "name": "report.md"}),
    )  # fmt: skip
    assert put_["state"] == "shelved" and listed["project"] == str(proj)
    assert got["says"] == REPORT
    other = tmp_path / "other"
    other.mkdir()
    assert mcp(box, other, tool(1, "shelf", {"action": "list"}))[0]["items"] == []


def test_a_shelf_holds_so_many_things_or_so_much_and_no_more(
    box, tmp_path, monkeypatch
):
    """A model never let in could fill the disk a megabyte at a time."""
    where = str(tmp_path / "project")
    add = lambda name, text: runtime.call(  # noqa: E731
        box, "shelf_add", {"name": name, "text": text}, door="mcp", where=where
    )
    monkeypatch.setattr(runtime, "SHELF_ITEMS_MOST", 2)
    assert add("a.md", "one")["state"] == add("b.md", "two")["state"] == "shelved"
    assert add("c.md", "three")["code"] == "shelf_full"
    assert add("a.md", "one") == {"state": "shelved", "name": "a.md", "same": True}
    monkeypatch.setattr(runtime, "SHELF_ITEMS_MOST", 200)
    monkeypatch.setattr(runtime, "SHELF_BYTES_MOST", 10)
    assert add("d.md", "more than ten bytes")["code"] == "shelf_full"
    folder, _ = runtime.shelf_at(box, where)
    assert sorted(p.name for p in folder.iterdir()) == ["a.md", "b.md"]
