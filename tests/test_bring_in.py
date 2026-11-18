"""A notes vault or a calendar brought into the folder the box reads, by the
person, through Willow's notes and calendar add-ons."""

import hashlib
import json
import zipfile

import pytest

import runtime

ROSEMARY = "when should the rosemary cuttings be potted"
DENTIST = "when is the dentist appointment"

ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:one@example
DTSTART:20261028T140000
SUMMARY:Dentist appointment with Dr Okafor
LOCATION:Studio 2
END:VEVENT
END:VCALENDAR
"""


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / ".obsidian").mkdir(parents=True)
    (v / ".obsidian" / "app.json").write_text("{}")
    (v / "garden").mkdir()
    (v / "garden" / "Herbs.md").write_text(
        "#garden\nRosemary cuttings should be potted in April, see [[Soil|the soil mix]].\n"
    )
    (v / "Soil.md").write_text("The soil mix is two parts loam to one of grit.\n")
    return v


@pytest.fixture
def cal(tmp_path):
    c = tmp_path / "calendars"
    c.mkdir()
    (c / "home.ics").write_text(ICS)
    return c


def snapshot(folder):
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def bring(box, kind, src, name="mine", door="pipe"):
    return runtime.call(box, "bring_in", {"kind": kind, "from": str(src), "as": name}, door=door)  # fmt: skip


def found(box, question):
    got = runtime.call(box, "read", question, door="pipe")
    return [s["where"] for s in got.get("served", [])]


def test_a_vault_is_mirrored_and_a_question_then_finds_a_line_of_it(box, vault):
    assert found(box, ROSEMARY) == []
    got = bring(box, "notes", vault)
    assert got["state"] == "brought", got
    assert got["wrote"] == 2 and got["skipped"] == 0
    assert got["to"].endswith("pile/brought-in/notes-mine")
    where = found(box, ROSEMARY)
    assert where and where[0].startswith("brought-in/notes-mine/garden/Herbs.md.txt")


def test_a_calendar_is_mirrored_and_its_event_is_found(box, cal):
    got = bring(box, "calendar", cal, "family")
    assert got["state"] == "brought", got
    assert got["wrote"] == 1
    where = found(box, DENTIST)
    assert where and where[0].startswith("brought-in/calendar-family/home.ics.txt")
    mirror = box.parent / "pile" / "brought-in" / "calendar-family" / "home.ics.txt"
    assert "2026-10-28 14:00  Dentist appointment" in mirror.read_text()


def test_the_original_is_never_changed(box, vault, cal):
    for kind, src in (("notes", vault), ("calendar", cal)):
        before = snapshot(src)
        assert bring(box, kind, src, kind)["state"] == "brought"
        assert bring(box, kind, src, kind)["state"] == "brought"
        assert snapshot(src) == before


def test_a_from_inside_the_box_or_the_pile_is_refused(box, tmp_path):
    pile = box.parent / "pile"
    (box / "stuff").mkdir()
    (pile / "more").mkdir()
    for inside in (box, box / "stuff", pile, pile / "more"):
        got = bring(box, "notes", inside)
        assert got["state"] == "refused" and got["code"] == "bring_inside", got
    assert not (pile / "brought-in").exists()


def test_a_from_that_is_the_mirror_itself_is_refused(box, vault):
    assert bring(box, "notes", vault)["state"] == "brought"
    mirror = box.parent / "pile" / "brought-in" / "notes-mine"
    assert bring(box, "notes", mirror)["code"] == "bring_inside"


def test_a_from_that_holds_the_pile_is_refused(box, tmp_path):
    assert bring(box, "notes", tmp_path)["code"] == "bring_inside"


@pytest.mark.parametrize("name", ["", "a/b", "..", "../x", ".hidden", "a b", "x" * 65])
def test_a_name_that_is_not_one_plain_folder_name_is_refused(box, vault, name):
    assert bring(box, "notes", vault, name)["code"] == "bring_name"
    assert not (box.parent / "pile" / "brought-in").exists()


def test_a_kind_that_is_not_notes_or_calendar_is_refused(box, vault):
    assert bring(box, "photos", vault)["code"] == "bring_what"
    got = runtime.call(box, "bring_in", "nonsense", door="pipe")
    assert got["code"] == "bring_what"


def test_a_folder_that_is_not_there_or_has_nothing_to_read_is_refused(box, tmp_path):
    assert bring(box, "notes", tmp_path / "nope")["code"] == "bring_failed"
    empty = tmp_path / "empty"
    empty.mkdir()
    assert bring(box, "calendar", empty)["code"] == "bring_nothing"
    assert brought_rows(box) == []


def brought_rows(box):
    return runtime.call(box, "brought_in", door="pipe")["brought_in"]


def test_a_mirror_that_is_not_this_ones_own_is_never_written_over(box, vault, tmp_path):
    other = tmp_path / "other-vault"
    other.mkdir()
    (other / "x.md").write_text("Something else entirely.\n")
    assert bring(box, "notes", vault)["state"] == "brought"
    before = snapshot(box.parent / "pile" / "brought-in")
    got = bring(box, "notes", other)
    assert got["code"] == "bring_exists", got
    assert snapshot(box.parent / "pile" / "brought-in") == before
    # a folder the person made by that name, with no record, is theirs
    (box.parent / "pile" / "brought-in" / "notes-hand").mkdir()
    assert bring(box, "notes", vault, "hand")["code"] == "bring_exists"


def test_a_second_run_over_the_same_vault_mirrors_again_and_keeps_what_was_deleted(
    box, vault
):
    first = bring(box, "notes", vault)
    assert first["again"] is False and first["times"] == 1
    (vault / "Soil.md").unlink()
    (vault / "Water.md").write_text("Water the ferns on Sundays.\n")
    (vault / "garden" / "Herbs.md").write_text("Rosemary is potted in May now.\n")
    second = bring(box, "notes", vault)
    assert second["state"] == "brought" and second["again"] is True
    assert second["times"] == 2 and second["first"] == first["at"]
    mirror = box.parent / "pile" / "brought-in" / "notes-mine"
    assert (mirror / "Water.md.txt").is_file()  # new: added
    assert "May now" in (mirror / "garden" / "Herbs.md.txt").read_text()  # changed
    assert (mirror / "Soil.md.txt").is_file()  # deleted from the vault: stays
    assert [r["times"] for r in brought_rows(box)] == [2]  # one row, not two
    assert found(box, "when are the ferns watered")


def test_a_second_run_over_a_calendar_behaves_the_same(box, cal):
    assert bring(box, "calendar", cal)["again"] is False
    (cal / "home.ics").write_text(ICS.replace("Dr Okafor", "Dr Haddad"))
    got = bring(box, "calendar", cal)
    assert got["again"] is True
    mirror = box.parent / "pile" / "brought-in" / "calendar-mine" / "home.ics.txt"
    assert "Dr Haddad" in mirror.read_text()


def test_what_was_brought_in_is_listed_with_where_from_and_when(box, vault, cal):
    assert runtime.call(box, "brought_in", door="pipe")["state"] == "empty"
    bring(box, "notes", vault, "vault")
    bring(box, "calendar", cal, "family")
    rows = brought_rows(box)
    assert [(r["kind"], r["name"]) for r in rows] == [
        ("notes", "vault"),
        ("calendar", "family"),
    ]
    assert rows[0]["from"] == str(vault.resolve())
    assert rows[0]["at"].endswith("Z") and rows[0]["wrote"] == 2
    assert rows[0]["mirror"] == "brought-in/notes-vault"


def test_status_says_what_was_brought_in(box, vault):
    bring(box, "notes", vault, "vault")
    group = [g for g in runtime.call(box, "status", door="pipe")["groups"]
             if g["name"] == "Brought in"]  # fmt: skip
    assert group and group[0]["rows"][0]["where"] == "notes vault"
    assert str(vault.resolve()) in group[0]["rows"][0]["what"]


@pytest.mark.parametrize("door", ["mcp", "hook", "guard", "unknown-door"])
def test_a_models_door_and_a_hosts_door_are_refused_the_verb(box, vault, door):
    for verb, arg in (("bring_in", {"kind": "notes", "from": str(vault), "as": "x"}),
                      ("brought_in", None)):  # fmt: skip
        got = runtime.call(box, verb, arg, door=door)
        assert got["state"] == "refused" and got["code"] == "no_verb", got
    assert not (box.parent / "pile" / "brought-in").exists()
    assert not (runtime.state(box) / "brought-in.json").exists()


def test_no_door_but_the_persons_has_the_verbs():
    for face in ("model", "host"):
        assert not {"bring_in", "brought_in"} & set(runtime.VERBS[face])
        assert not {"bring_in", "brought_in"} & set(runtime.LISTED.get(face, {}))


def test_the_record_is_a_flat_file_beside_the_box_and_a_backup_carries_it(
    box, vault, tmp_path_factory
):
    bring(box, "notes", vault, "vault")
    record = runtime.state(box) / "brought-in.json"
    assert json.loads(record.read_text())[0]["name"] == "vault"
    assert runtime.kept_name("brought-in.json")
    usb = tmp_path_factory.mktemp("usb")
    got = runtime.call(box, "backup", str(usb), door="pipe")
    assert got["state"] == "kept" and "brought-in.json" in got["files"], got
    with zipfile.ZipFile(usb / got["runtime"]) as z:
        assert z.read("brought-in.json") == record.read_bytes()
    was = record.read_bytes()
    record.unlink()
    back = runtime.call(box, "restore", str(usb / got["runtime"]), door="pipe")
    assert back["state"] == "restored" and "brought-in.json" in back["files"], back
    assert record.read_bytes() == was


def test_a_record_that_cannot_be_read_stops_the_next_bring_in(box, vault):
    (runtime.state(box) / "brought-in.json").write_text("not json")
    assert bring(box, "notes", vault)["code"] == "bring_record"
    assert runtime.call(box, "brought_in", door="pipe")["code"] == "bring_record"


def test_a_mirror_folder_that_leads_somewhere_else_is_not_written_through(
    box, vault, tmp_path
):
    away = tmp_path / "away"
    away.mkdir()
    (box.parent / "pile" / "brought-in").symlink_to(away)
    assert bring(box, "notes", vault)["code"] == "bring_exists"
    assert list(away.iterdir()) == []


def test_a_box_with_no_folder_to_read_refuses(box, vault):
    cfg = json.loads((box / "kernel.json").read_text())
    cfg["pile"] = str(box.parent / "gone")
    (box / "kernel.json").write_text(json.dumps(cfg))
    assert bring(box, "notes", vault)["code"] == "bring_no_folder"
