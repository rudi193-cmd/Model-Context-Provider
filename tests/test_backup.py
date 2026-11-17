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
