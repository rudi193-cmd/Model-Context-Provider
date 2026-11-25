"""The index: a bite answered from an index of the folder, kept current
beside the box, the same as the kernel's own; and the kernel's bite when
there is no index to ask."""

import json

import runtime

FROST = "when does the first frost come"


def kernel_bite(box, question):
    return json.loads(
        runtime.willow("kernel.py", "bite", "--box", str(box), question).stdout
    )


def test_a_read_keeps_an_index_beside_the_box_and_answers_as_the_kernel(box):
    got = runtime.read(box, FROST)
    at = runtime.state(box) / "index"
    assert (at / "index.json").is_file()
    assert not (box / "index").exists()  # beside the box, never in it
    want = kernel_bite(box, FROST)
    want.pop("look", None)  # hints for a person; an index gives none
    assert got == want and got["state"] == "populated"


def test_the_index_follows_the_folder(box):
    runtime.read(box, FROST)
    (box.parent / "pile" / "garden.md").write_text("Snowdrops come up in February.\n")
    assert runtime.read(box, FROST)["state"] != "populated"
    assert runtime.read(box, "when do the snowdrops come up")["state"] == "populated"


def test_without_willows_indexed_bite_the_kernel_reads_the_folder(box, monkeypatch):
    monkeypatch.setattr(runtime, "INDEXED", "no/such/hook.py")
    monkeypatch.setattr(runtime, "INDEX_CACHE", "no/such/index_cache.py")
    assert runtime.read(box, FROST)["state"] == "populated"
    assert runtime.read(box, "what colour is the boat")["state"] == "empty"


def test_a_broken_record_is_the_kernels_refusal_with_or_without_an_index(box):
    runtime.read(box, FROST)
    (box / "record.jsonl").write_text("not a record\n")
    got = runtime.call(box, "read", FROST, door="pipe")
    assert got["code"] == "record_broken" and "kernel.py verify" in got["next"]


def test_the_index_never_goes_in_a_backup(box, tmp_path_factory):
    runtime.read(box, FROST)
    got = runtime.call(box, "backup", str(tmp_path_factory.mktemp("usb")), door="pipe")
    assert got["state"] == "kept" and not any("index" in f for f in got["files"])


def test_a_session_closes_with_the_index_and_without_it(box, monkeypatch):
    runtime.read(box, FROST)
    assert runtime.close(box)["state"] == "waiting"
    runtime.read(box, FROST)
    monkeypatch.setattr(runtime, "INDEX_CACHE", "no/such/index_cache.py")
    assert runtime.close(box)["state"] == "waiting"


def test_a_box_laid_from_several_places_is_answered_from_its_index(tmp_path):
    """A box that reads its files where they are kept (init --from, a folder
    and a list) keeps an index of all of them, answers as the kernel does
    from it, and follows a change to a listed file."""
    notes, code = tmp_path / "notes", tmp_path / "code"
    notes.mkdir(), code.mkdir()
    (notes / "garden.md").write_text("The first frost comes in late October.\n")
    (code / "frost.md").write_text("Frost comes first to the low field.\n")
    lst = tmp_path / "code.list"
    lst.write_text(f"{code / 'frost.md'}\n")
    b = tmp_path / "box"
    run = runtime.willow(
        "kernel.py", "init", "--box", str(b), "--from", f"notes={notes}",
        "--from", f"code=@{lst}", "--key", str(tmp_path / "test.key"),
    )  # fmt: skip
    assert run.returncode == 0, run.stderr
    got = runtime.read(b, FROST)
    at = runtime.state(b) / "index"
    assert (at / "index.json").is_file() and not (b / "index").exists()
    want = kernel_bite(b, FROST)
    want.pop("look", None)
    assert got == want and got["state"] == "populated"
    assert {s["where"] for s in got["served"]} == {
        "notes/garden.md:1",
        "code/frost.md:1",
    }
    (code / "frost.md").write_text("Snowdrops come up in the low field.\n")
    asked = runtime.read(b, "when do the snowdrops come up")
    assert asked["state"] == "populated"
    assert [s["where"] for s in asked["served"]] == ["code/frost.md:1"]
