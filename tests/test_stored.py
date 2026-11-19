"""What is kept beside the record is the person's to see, delete or pack
away. The record keeps the hole: each file's name, size and fingerprint on
a row written before it goes (Willow's removed), never its words. A file
deleted from their own folder leaves its hole too (Willow's what-changed)."""

import hashlib
import json
import tarfile

from conftest import CHANGED_AT_START
from test_leave import seal

import runtime

WORDS = "A plan for the dahlia bed, bed by bed.\n"


def pipe(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="pipe")


def model(box, verb, arg=None, where="/work/a", session="s1"):
    return runtime.call(box, verb, arg, door="mcp", where=where, session=session)


def rows(box):
    return [json.loads(r) for r in (box / "record.jsonl").read_text().splitlines()]


def made(box, name, text=WORDS):
    d = runtime.state(box) / "made"
    d.mkdir(exist_ok=True)
    (d / name).write_text(text)
    return f"made/{name}"


def test_the_person_sees_what_is_kept_by_kind_and_by_file(box):
    assert pipe(box, "stored") == {"state": "empty", "kinds": []}
    made(box, "timeline-a.txt")
    made(box, "feed.xml", "<rss/>")
    model(box, "shelf_add", {"name": "notes.md", "text": "what I found"})
    got = {k["kind"]: k for k in pipe(box, "stored")["kinds"]}
    assert got["made"]["files"] == 2 and got["made"]["bytes"] == len(WORDS) + 6
    assert got["shelf"]["files"] == 1 and "index" not in got
    items = pipe(box, "stored", {"kind": "made"})["items"]
    assert [i["name"] for i in items] == ["made/feed.xml", "made/timeline-a.txt"]
    assert WORDS not in json.dumps(pipe(box, "stored", {"kind": "made"}))


def test_a_file_removed_is_gone_and_its_hole_is_on_the_record(box):
    name = made(box, "timeline-a.txt")
    made(box, "feed.xml", "<rss/>")
    got = pipe(box, "remove", {"kind": "made", "names": [name]})
    assert got == {"state": "removed", "kind": "made", "files": 1, "bytes": len(WORDS)}
    assert not (runtime.state(box) / name).exists()
    assert (runtime.state(box) / "made" / "feed.xml").exists()  # only what was named
    hole = rows(box)[-1]
    assert (hole["kind"], hole["how"], hole["what"]) == ("removed", "deleted", "made")
    assert hole["files"] == {name: {"size": len(WORDS),
                                    "sha256": hashlib.sha256(WORDS.encode()).hexdigest()}}  # fmt: skip
    assert "dahlia" not in (box / "record.jsonl").read_text()  # never its words
    assert runtime.willow("kernel.py", "verify", "--box", str(box)).returncode == 0


def test_by_age_or_all_of_a_kind_and_never_without_saying_which(box):
    import os

    old = made(box, "old.txt")
    made(box, "new.txt")
    os.utime(runtime.state(box) / old, (1_700_000_000, 1_700_000_000))  # 2023-11-14
    for asked in ({"kind": "made"}, {"kind": "made", "all": "yes"}, {"kind": "everything"},
                  {"kind": "made", "older": "last week"}, "made", None,
                  {"kind": "made", "names": ["sent.jsonl"]}, {"kind": "made", "names": ["../box/kernel.json"]},
                  {"kind": "made", "names": [old, "made/nope.txt"]}):  # fmt: skip
        got = pipe(box, "remove", asked)
        assert (got["state"], got["code"]) == ("refused", "remove_refused"), asked
    assert len(list((runtime.state(box) / "made").iterdir())) == 2  # nothing went
    assert pipe(box, "remove", {"kind": "made", "older": "2024-01-01"})["files"] == 1
    assert not (runtime.state(box) / old).exists()
    assert (
        pipe(box, "remove", {"kind": "made", "older": "2024-01-01"})["state"] == "empty"
    )
    assert pipe(box, "remove", {"kind": "made", "all": True})["files"] == 1
    assert pipe(box, "stored") == {"state": "empty", "kinds": []}


def test_the_runtimes_own_books_are_never_removed(box):
    model(box, "read", "when does the first frost come")
    kept = sorted(p.name for p in runtime.state(box).iterdir() if p.is_file())
    for kind in runtime.KEPT_KINDS:
        pipe(box, "remove", {"kind": kind, "all": True})
    assert sorted(p.name for p in runtime.state(box).iterdir() if p.is_file()) == kept
    assert "sent.jsonl" in kept


def test_an_archive_holds_the_files_and_the_record_holds_its_fingerprint(box, tmp_path):
    a, b = made(box, "a.txt"), made(box, "b.txt", "second\n")
    tar = tmp_path / "away.tar.gz"
    got = pipe(box, "archive", {"kind": "made", "all": True, "to": str(tar)})
    assert got["state"] == "removed" and got["to"] == str(tar) and got["files"] == 2
    with tarfile.open(tar) as t:
        assert sorted(t.getnames()) == [a, b]
        assert t.extractfile(a).read().decode() == WORDS
    hole = rows(box)[-1]
    assert hole["how"] == "archived" and hole["to"]["name"] == "away.tar.gz"
    assert hole["to"]["sha256"] == hashlib.sha256(tar.read_bytes()).hexdigest()
    assert not list((runtime.state(box) / "made").iterdir())
    made(box, "c.txt")
    for to in (tar, box / "x.tar.gz", box.parent / "pile" / "x.tar.gz",
               runtime.state(box) / "x.tar.gz", tmp_path / "no" / "x.tar.gz", ""):  # fmt: skip
        got = pipe(box, "archive", {"kind": "made", "all": True, "to": str(to)})
        assert (got["state"], got["code"]) == ("refused", "remove_refused"), to
    assert (runtime.state(box) / "made" / "c.txt").exists()  # refused: nothing went


def test_if_the_hole_cannot_be_written_nothing_is_removed(box, tmp_path, monkeypatch):
    name = made(box, "a.txt")
    monkeypatch.setattr(runtime, "REMOVED", "no/such/removed.py")
    tar = tmp_path / "away.tar.gz"
    for verb, more in (("remove", {}), ("archive", {"to": str(tar)})):
        got = pipe(box, verb, {"kind": "made", "all": True, **more})
        assert (got["state"], got["code"]) == ("refused", "remove_refused")
    assert (runtime.state(box) / name).read_text() == WORDS and not tar.exists()


def test_a_session_let_in_takes_a_thing_off_its_own_shelf_and_no_other(box):
    model(box, "shelf_add", {"name": "notes.md", "text": "what I found"})
    model(
        box,
        "shelf_add",
        {"name": "theirs.md", "text": "another project"},
        where="/work/b",
    )
    told = model(box, "shelf_remove", "notes.md")
    assert (told["state"], told["code"]) == ("refused", "no_grant")
    seal(box, model(box, "grant")["seal"])
    for name in ("theirs.md", "../x", "nope.md", "", 7):
        got = model(box, "shelf_remove", name)
        assert (got["state"], got["code"]) == ("refused", "not_on_shelf"), name
    assert model(box, "shelf_remove", "notes.md") == {
        "state": "removed",
        "name": "notes.md",
    }
    assert model(box, "shelf_list")["items"] == []
    assert [i["name"] for i in model(box, "shelf_list", where="/work/b")["items"]] == [
        "theirs.md"
    ]
    hole = rows(box)[-1]
    assert hole["kind"] == "removed" and hole["what"] == "shelf"
    assert "what I found" not in (box / "record.jsonl").read_text()
    assert any(
        "taken off its project's shelf" in ln for ln in pipe(box, "shared")["lines"]
    )
    for verb in ("stored", "remove", "archive", "changed"):
        assert model(box, verb, {})["code"] == "no_verb", verb  # the person's alone


def test_the_index_goes_without_a_hole_and_is_built_again(box):
    model(box, "read", "when does the first frost come")
    assert (runtime.state(box) / "index").is_dir()
    n = len(rows(box))
    got = pipe(box, "remove", {"kind": "index", "all": True})
    assert got["state"] == "removed" and not (runtime.state(box) / "index").exists()
    assert len(rows(box)) == n  # it held nothing the folder doesn't
    assert model(box, "read", "when does the first frost come")["state"] == "populated"
    assert (runtime.state(box) / "index").is_dir()


def test_a_file_deleted_from_the_folder_leaves_its_hole(box):
    assert pipe(box, "changed")["state"] == "first"
    assert pipe(box, "changed") == {"state": "unchanged"}
    (box.parent / "pile" / "car.md").unlink()
    (box.parent / "pile" / "new.md").write_text("A new note.\n")
    got = pipe(box, "changed")
    assert got == {"state": "changed", "new": 1, "edited": 0, "deleted": ["car.md"]}
    assert rows(box)[-1]["deleted"] == ["car.md"]
    assert "MOT" not in (box / "record.jsonl").read_text().splitlines()[-1]


def test_a_session_start_checks_the_folder_once_an_hour_and_never_waits(
    box, monkeypatch
):
    started = []
    monkeypatch.setattr(runtime, "changed_at_start", CHANGED_AT_START)
    monkeypatch.setattr(
        runtime, "launch", lambda argv, cwd=None, said=None: started.append(argv)
    )
    sent = {"hook_event_name": "SessionStart", "cwd": "/work/a", "session_id": "s1"}
    runtime.call(box, "event", sent, door="guard")
    runtime.call(box, "event", {**sent, "session_id": "s2"}, door="guard")
    checks = [a for a in started if runtime.WHAT_CHANGED in a]
    assert len(checks) == 1 and checks[0][-2:] == ["--box", str(box)]
    import os

    stamp = runtime.state(box) / "changed.stamp"
    os.utime(stamp, (1_700_000_000, 1_700_000_000))  # long ago
    runtime.call(box, "event", {**sent, "session_id": "s3"}, door="guard")
    assert len([a for a in started if runtime.WHAT_CHANGED in a]) == 2
