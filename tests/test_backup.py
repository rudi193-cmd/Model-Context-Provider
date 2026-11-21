"""The box and what the runtime keeps beside it, copied and checked."""

import zipfile

from test_leave import seal

import runtime

FROST = "when does the first frost come"


def used(box):
    (runtime.state(box) / "names.txt").write_text("Aoife\n")
    runtime.call(box, "read", FROST, door="mcp")
    seal(box, runtime.call(box, "propose", door="mcp")["seal"])
    runtime.call(box, "leave", door="mcp")


def test_both_copies_are_kept_and_hold_what_a_box_backup_misses(box, tmp_path_factory):
    used(box)
    usb = tmp_path_factory.mktemp("usb")
    got = runtime.call(box, "backup", str(usb), door="pipe")
    assert got["state"] == "kept", got
    assert (usb / got["box"]).is_file()
    with zipfile.ZipFile(usb / got["runtime"]) as z:
        names = set(z.namelist())
        assert {"sent.jsonl", "scopes.json", "names.txt"} <= names
        assert z.read("sent.jsonl") == (runtime.state(box) / "sent.jsonl").read_bytes()


def test_no_copy_holds_the_key(box, tmp_path_factory):
    used(box)
    usb = tmp_path_factory.mktemp("usb")
    got = runtime.call(box, "backup", str(usb), door="pipe")
    key = (box.parent / "test.key").read_bytes()
    for name in (got["box"], got["runtime"]):
        with zipfile.ZipFile(usb / name) as z:
            assert all(key not in z.read(n) for n in z.namelist())


def test_a_backup_inside_the_box_is_refused(box):
    used(box)
    assert runtime.call(box, "backup", str(box), door="pipe")["state"] == "refused"


def test_a_model_cannot_take_a_backup(box, tmp_path_factory):
    usb = tmp_path_factory.mktemp("usb")
    assert runtime.call(box, "backup", str(usb), door="mcp")["state"] == "refused"
    assert list(usb.iterdir()) == []


def lost(box, tmp_path_factory):
    """A backup taken, then everything beside the box gone."""
    used(box)
    usb = tmp_path_factory.mktemp("usb")
    got = runtime.call(box, "backup", str(usb), door="pipe")
    was = {f.name: f.read_bytes() for f in runtime.state(box).iterdir() if f.is_file()}
    for f in runtime.state(box).iterdir():
        if f.is_file():
            f.unlink()
    return usb / got["runtime"], was


def test_a_backup_puts_back_what_was_lost_byte_for_byte(box, tmp_path_factory):
    zip_from, was = lost(box, tmp_path_factory)
    got = runtime.call(box, "restore", str(zip_from), door="pipe")
    assert got["state"] == "restored", got
    assert got["files"] == sorted(was)
    now = {f.name: f.read_bytes() for f in runtime.state(box).iterdir() if f.is_file()}
    assert now == was
    assert runtime.call(box, "shared", door="pipe")["state"] != "refused"


def test_restoring_twice_changes_nothing(box, tmp_path_factory):
    zip_from, was = lost(box, tmp_path_factory)
    runtime.call(box, "restore", str(zip_from), door="pipe")
    got = runtime.call(box, "restore", str(zip_from), door="pipe")
    assert got["state"] == "restored" and got["files"] == [], got
    assert got["same"] == sorted(was)


def test_a_file_that_differs_is_never_written_over(box, tmp_path_factory):
    zip_from, was = lost(box, tmp_path_factory)
    names = runtime.state(box) / "names.txt"
    names.write_text("Brigid\n")
    got = runtime.call(box, "restore", str(zip_from), door="pipe")
    assert got["state"] == "refused" and got["code"] == "restore_over", got
    assert "names.txt" in got["why"]
    assert names.read_text() == "Brigid\n"
    assert [f.name for f in runtime.state(box).iterdir() if f.is_file()] == [
        "names.txt"
    ]


def broken(tmp_path, members):
    z_to = tmp_path / "model-context-provider-bad.zip"
    with zipfile.ZipFile(z_to, "w") as z:
        for n, b in members.items():
            z.writestr(n, b)
    return z_to


def test_a_zip_that_isnt_the_runtimes_is_refused_and_nothing_is_written(box, tmp_path):
    before = sorted(runtime.state(box).iterdir())
    for members in (
        {"../escape.txt": "x"},
        {"sub/names.txt": "x"},
        {"test.key": "x"},
        {"kernel.json": "{}", "record.jsonl": ""},
        {"sent.jsonl": '{"n": 0, "prev": "not the start"}\n'},
        {},
    ):
        got = runtime.call(box, "restore", str(broken(tmp_path, members)), door="pipe")
        assert got["code"] == "not_backup", (members, got)
    (tmp_path / "plain.txt").write_text("hello")
    assert (
        runtime.call(box, "restore", str(tmp_path / "plain.txt"), door="pipe")["code"]
        == "not_backup"
    )
    assert sorted(runtime.state(box).iterdir()) == before


def test_a_model_cannot_restore(box, tmp_path_factory):
    zip_from, _ = lost(box, tmp_path_factory)
    got = runtime.call(box, "restore", str(zip_from), door="mcp")
    assert got["state"] == "refused" and got["code"] == "no_verb"


def test_a_sessions_corrections_go_in_the_backup_and_come_back(box, tmp_path_factory):
    """A session's corrections wait beside the record until it ends; a backup
    taken before then carries them, and a restore puts them back."""
    runtime.correction_kept(box, "s1", "no, the other bed")
    kept = runtime.corrections_of(box, "s1")
    usb = tmp_path_factory.mktemp("usb")
    made = runtime.call(box, "backup", str(usb), door="pipe")
    assert f"corrections/{kept.name}" in made["files"], made
    was = kept.read_bytes()
    kept.unlink()
    got = runtime.call(box, "restore", str(usb / made["runtime"]), door="pipe")
    assert f"corrections/{kept.name}" in got["files"] and kept.read_bytes() == was
    assert runtime.kept_name(f"corrections/{kept.name}")
    for bad in ("corrections/a/b.json", "corrections/../x", "corrections/"):
        assert not runtime.kept_name(bad), bad
