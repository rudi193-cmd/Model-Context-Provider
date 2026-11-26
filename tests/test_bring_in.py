"""A notes vault, a calendar, or a Joplin, Evernote or Google Keep export
brought into the folder the box reads, by the person, through Willow's
add-ons for each."""

import hashlib
from pathlib import Path
import sqlite3
import io
import json
import tarfile
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


FROST = "when should the tomatoes be planted out after the last frost"
BEANS = "which plot gets the beans"
MILK = "what is on the shopping list"

ENEX = (
    "<en-export><note><title>Allotment plan</title><content><![CDATA["
    "<en-note><div>Plot 14 gets the beans.</div></en-note>]]></content>"
    "<created>20240303T101500Z</created><tag>garden</tag></note></en-export>"
)
KEEP = (
    '{"isTrashed":false,"title":"Shopping","userEditedTimestampUsec":1710000000000000,'
    '"createdTimestampUsec":1709380000000000,"labels":[{"name":"home"}],'
    '"listContent":[{"text":"milk","isChecked":false}]}'
)


def jex(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


JEX = jex(
    {
        "a.md": "Garden\n\nid: a\nparent_id: \ntype_: 2",
        "n1.md": "Tomato notes\n\nPlant out after the last frost.\n\nid: n1\nparent_id: a\n"
        "created_time: 2024-03-02T08:00:00.000Z\ndeleted_time: 0\ntype_: 1",
    }
)


EML = (
    "From: Ada Example <ada@example.org>\nTo: Ben Example <ben@example.org>\n"
    "Date: Wed, 14 Oct 2026 09:15:00 +0000\nSubject: Roof estimate\n\n"
    "The estimate for the roof is in. The total is 4,200.\n"
)
ROOF = "what is the estimate for the roof"
SENT = 1733213400  # 2024-12-03 08:10 UTC, in seconds; a backup keeps milliseconds
WHO = "+1" + "555" + "0100"  # a made-up number, put together here


def texts():
    """A phone backup of two texts, as SMS Backup & Restore writes one."""
    line = '<sms address="{who}" date="{at}" type="{kind}" body="{body}" contact_name="Dev Raman" />\n'
    return (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>\n"
        '<smses count="2">\n'
        + line.format(who=WHO, at=SENT * 1000, kind=1,
                      body="I can bring the ladder on Saturday")
        + line.format(who=WHO, at=(SENT + 120) * 1000, kind=2, body="Saturday works")
        + "</smses>\n"
    )  # fmt: skip


LADDER = "who can bring the ladder on Saturday"


@pytest.fixture
def mailbox(tmp_path):
    m = tmp_path / "mail-export"
    (m / "inbox").mkdir(parents=True)
    (m / "inbox" / "roof.eml").write_text(EML)
    return m


@pytest.fixture
def phone(tmp_path):
    p = tmp_path / "phone-backup"
    p.mkdir()
    (p / "texts.xml").write_text(texts())
    return p


@pytest.fixture
def joplin(tmp_path):
    j = tmp_path / "joplin-export"
    j.mkdir()
    (j / "export.jex").write_bytes(JEX)
    return j


@pytest.fixture
def evernote(tmp_path):
    e = tmp_path / "evernote-export"
    e.mkdir()
    (e / "Garden.enex").write_text(ENEX)
    return e


@pytest.fixture
def keep(tmp_path):
    k = tmp_path / "keep-export"
    k.mkdir()
    (k / "shopping.json").write_text(KEEP)
    return k


#: Zotero's own tables, those its importer reads, as Willow's zotero test
#: makes them (adapters/stdlib/zotero/test_zotero.py, SCHEMA)
ZOTERO = """
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT, templateItemTypeID INT, display INT DEFAULT 1);
CREATE TABLE itemTypesCombined (itemTypeID INT NOT NULL, typeName TEXT NOT NULL, display INT DEFAULT 1 NOT NULL,
    custom INT NOT NULL, PRIMARY KEY (itemTypeID));
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT, fieldFormatID INT);
CREATE TABLE fieldsCombined (fieldID INT NOT NULL, fieldName TEXT NOT NULL, label TEXT, fieldFormatID INT,
    custom INT NOT NULL, PRIMARY KEY (fieldID));
CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INT NOT NULL,
    dateAdded TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, dateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, libraryID INT NOT NULL, key TEXT NOT NULL,
    version INT NOT NULL DEFAULT 0, clientVersion INT NOT NULL DEFAULT 0, synced INT NOT NULL DEFAULT 0,
    UNIQUE (libraryID, key));
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value UNIQUE, valueNormalized TEXT);
CREATE TABLE itemData (itemID INT, fieldID INT, valueID, PRIMARY KEY (itemID, fieldID));
CREATE TABLE itemNotes (itemID INTEGER PRIMARY KEY, parentItemID INT, note TEXT, title TEXT);
CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT, linkMode INT, contentType TEXT,
    charsetID INT, path TEXT, syncState INT DEFAULT 0, storageModTime INT, storageHash TEXT,
    lastProcessedModificationTime INT, lastRead INT);
CREATE TABLE itemAnnotations (itemID INTEGER PRIMARY KEY, parentItemID INT NOT NULL, type INTEGER NOT NULL,
    authorName TEXT, text TEXT, textNormalized TEXT, comment TEXT, commentNormalized TEXT, color TEXT,
    pageLabel TEXT, sortIndex TEXT NOT NULL, position TEXT NOT NULL, isExternal INT NOT NULL);
CREATE TABLE tags (tagID INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, nameNormalized TEXT);
CREATE TABLE itemTags (itemID INT NOT NULL, tagID INT NOT NULL, type INT NOT NULL, PRIMARY KEY (itemID, tagID));
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT, fieldMode INT,
    firstNameNormalized TEXT, lastNameNormalized TEXT, UNIQUE (lastName, firstName, fieldMode));
CREATE TABLE itemCreators (itemID INT NOT NULL, creatorID INT NOT NULL, creatorTypeID INT NOT NULL DEFAULT 1,
    orderIndex INT NOT NULL DEFAULT 0, PRIMARY KEY (itemID, creatorID, creatorTypeID, orderIndex),
    UNIQUE (itemID, orderIndex));
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT NOT NULL,
    parentCollectionID INT DEFAULT NULL, clientDateModified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    libraryID INT NOT NULL, key TEXT NOT NULL, version INT NOT NULL DEFAULT 0, clientVersion INT NOT NULL DEFAULT 0,
    synced INT NOT NULL DEFAULT 0, UNIQUE (libraryID, key));
CREATE TABLE collectionItems (collectionID INT NOT NULL, itemID INT NOT NULL, orderIndex INT NOT NULL DEFAULT 0,
    PRIMARY KEY (collectionID, itemID));
CREATE TABLE deletedCollections (collectionID INTEGER PRIMARY KEY, dateDeleted DEFAULT CURRENT_TIMESTAMP NOT NULL);
CREATE TABLE deletedItems (itemID INTEGER PRIMARY KEY, dateDeleted DEFAULT CURRENT_TIMESTAMP NOT NULL);
CREATE TABLE feedItems (itemID INTEGER PRIMARY KEY, guid TEXT NOT NULL UNIQUE, readTime TIMESTAMP, translatedTime TIMESTAMP);
"""


def one_file(tmp: Path, folder: str, name: str, data: str) -> Path:
    """A folder holding one export file: what each importer is pointed at."""
    f = tmp / folder / name
    f.parent.mkdir(parents=True)
    f.write_text(data)
    return tmp / folder


@pytest.fixture
def mastodon(tmp_path):
    return one_file(tmp_path, "mastodon-archive", "outbox.json", json.dumps({
        "type": "OrderedCollection", "orderedItems": [{
            "type": "Create", "published": "2026-03-02T08:15:00Z",
            "object": {"type": "Note",
                       "content": "<p>Planted out the tomatoes by the greenhouse today.</p>"}}]}))  # fmt: skip


@pytest.fixture
def goodreads(tmp_path):
    return one_file(tmp_path, "goodreads-export", "goodreads_library_export.csv",
                    "Book Id,Title,Author,My Rating,Date Read,Date Added,Bookshelves,"
                    "Exclusive Shelf,My Review,Private Notes\n1,The Hobbit,J.R.R. Tolkien,4,"
                    "2026/03/02,2023/01/05,fantasy,read,A comfort read about dragons.,\n")  # fmt: skip


@pytest.fixture
def karakeep(tmp_path):
    return one_file(tmp_path, "karakeep-export", "karakeep.json", json.dumps({"bookmarks": [{
        "createdAt": 1710000000, "title": "Tomato staking guide", "tags": ["garden"],
        "note": "Read the staking section before May.",
        "content": {"type": "link", "url": "https://example.org/t"}}]}))  # fmt: skip


@pytest.fixture
def opml(tmp_path):
    return one_file(tmp_path, "feeds", "feeds.opml",
                    '<?xml version="1.0"?><opml version="2.0"><head><title>Feeds</title></head>'
                    '<body><outline text="Gardening"><outline text="Allotment Weekly podcast" '
                    'type="rss" xmlUrl="https://example.org/a.xml"/></outline></body></opml>')  # fmt: skip


@pytest.fixture
def takeout(tmp_path):
    t = tmp_path / "takeout" / "Takeout" / "My Activity" / "Search"
    t.mkdir(parents=True)
    (t / "MyActivity.json").write_text(json.dumps([{
        "header": "Search", "title": "Searched for when to prune apple trees",
        "time": "2026-02-10T09:00:00.000Z", "products": ["Search"]}]))  # fmt: skip
    return tmp_path / "takeout"


@pytest.fixture
def bookmarks(tmp_path):
    return one_file(tmp_path, "browser", "bookmarks.html",
                    "<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p><DT><H3>Garden</H3><DL><p>"
                    '<DT><A HREF="https://example.org/compost" ADD_DATE="1710000000">'
                    "Compost bin building plans</A></DL><p></DL>")  # fmt: skip


@pytest.fixture
def zotero(tmp_path):
    z = tmp_path / "zotero-copy"
    z.mkdir()
    con = sqlite3.connect(z / "zotero.sqlite")
    con.executescript(ZOTERO)
    con.execute("INSERT INTO itemTypes VALUES (7, 'book', NULL, 1)")
    con.execute("INSERT INTO itemTypesCombined VALUES (7, 'book', 1, 0)")
    for i, f in ((1, "title"), (6, "date"), (8, "publisher")):
        con.execute("INSERT INTO fields VALUES (?, ?, NULL)", (i, f))
        con.execute("INSERT INTO fieldsCombined VALUES (?, ?, NULL, NULL, 0)", (i, f))
    con.execute("INSERT INTO items (itemID, itemTypeID, dateAdded, libraryID, key) "
                "VALUES (1, 7, '2026-01-04 10:00:00', 1, 'K0000001')")  # fmt: skip
    for f, v in ((1, "The Well-Tempered Garden"), (6, "1970"), (8, "Collins")):
        con.execute("INSERT INTO itemDataValues (value) VALUES (?)", (v,))
        (vid,) = con.execute(
            "SELECT valueID FROM itemDataValues WHERE value = ?", (v,)
        ).fetchone()
        con.execute("INSERT INTO itemData VALUES (1, ?, ?)", (f, vid))
    con.commit()
    con.close()
    return z


@pytest.fixture
def code_graph(tmp_path):
    """codebase-memory-mcp's graph as it writes it now: nodes and edges."""
    g = tmp_path / "graph-copy"
    g.mkdir()
    con = sqlite3.connect(g / "graph.db")
    con.executescript("""
        CREATE TABLE nodes (id INTEGER PRIMARY KEY, project TEXT, label TEXT, name TEXT,
            qualified_name TEXT, file_path TEXT, start_line INTEGER, end_line INTEGER, properties TEXT);
        CREATE TABLE edges (id INTEGER PRIMARY KEY, project TEXT, source_id INTEGER,
            target_id INTEGER, type TEXT, properties TEXT);
        INSERT INTO nodes VALUES
            (1, 'p', 'Function', 'water_beds', 'garden.water_beds', 'garden.py', 3, 9, '{}'),
            (2, 'p', 'Function', 'open_valve', 'garden.open_valve', 'garden.py', 12, 20, '{}');
        INSERT INTO edges VALUES (1, 'p', 1, 2, 'CALLS', '{}');
    """)
    con.commit()
    con.close()
    return g


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


@pytest.mark.parametrize(
    "kind, fixture, question, mirror_file, words",
    [
        ("joplin", "joplin", FROST, "export.jex.txt", "notebook: Garden"),
        ("evernote", "evernote", BEANS, "Garden.enex.txt", "tags: garden"),
        ("google-keep", "keep", MILK, "shopping.json.txt", "[ ] milk"),
        (
            "mastodon",
            "mastodon",
            "when were the tomatoes planted out by the greenhouse",
            "outbox.json.txt",
            "Planted out the tomatoes",
        ),
        (
            "goodreads",
            "goodreads",
            "what did I think of the hobbit",
            "goodreads_library_export.csv.txt",
            "read The Hobbit by J.R.R. Tolkien",
        ),
        (
            "karakeep",
            "karakeep",
            "the tomato staking guide",
            "karakeep.json.txt",
            "note: Read the staking section",
        ),
        (
            "opml",
            "opml",
            "the allotment weekly podcast",
            "feeds.opml.txt",
            "Allotment Weekly podcast",
        ),
        (
            "takeout",
            "takeout",
            "when to prune apple trees",
            "Takeout/My Activity/Search/MyActivity.json.txt",
            "Searched for when to prune",
        ),
        (
            "bookmarks",
            "bookmarks",
            "compost bin building plans",
            "bookmarks.html.txt",
            "in Garden",
        ),
        (
            "zotero",
            "zotero",
            "the well-tempered garden by collins",
            "zotero.sqlite.txt",
            "The Well-Tempered Garden. Collins.",
        ),
        (
            "code-graph",
            "code_graph",
            "what calls open_valve",
            "graph.db.txt",
            "edges: call garden.open_valve",
        ),
    ],
)
def test_an_export_is_mirrored_and_a_question_then_finds_it(
    box, request, kind, fixture, question, mirror_file, words
):
    src = request.getfixturevalue(fixture)
    assert found(box, question) == []
    got = bring(box, kind, src, "mine")
    assert got["state"] == "brought", got
    assert got["wrote"] == 1 and got["skipped"] == 0
    assert got["to"].endswith(f"pile/brought-in/{kind}-mine")
    mirror = box.parent / "pile" / "brought-in" / f"{kind}-mine" / mirror_file
    assert words in mirror.read_text()
    where = found(box, question)
    assert where and where[0].startswith(f"brought-in/{kind}-mine/{mirror_file}")


def test_the_original_is_never_changed(box, vault, cal, joplin, evernote, keep):
    for kind, src in (
        ("notes", vault),
        ("calendar", cal),
        ("joplin", joplin),
        ("evernote", evernote),
        ("google-keep", keep),
    ):
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


def test_a_from_that_holds_the_pile_is_refused(box):
    assert bring(box, "notes", box.parent)["code"] == "bring_inside"


@pytest.mark.parametrize("name", ["", "a/b", "..", "../x", ".hidden", "a b", "x" * 65])
def test_a_name_that_is_not_one_plain_folder_name_is_refused(box, vault, name):
    assert bring(box, "notes", vault, name)["code"] == "bring_name"
    assert not (box.parent / "pile" / "brought-in").exists()


def test_a_kind_it_does_not_bring_in_is_refused(box, vault):
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


def test_a_second_run_over_an_export_behaves_the_same(box, joplin, evernote, keep):
    for kind, src, file in (
        ("joplin", joplin, "export.jex"),
        ("evernote", evernote, "Garden.enex"),
        ("google-keep", keep, "shopping.json"),
    ):
        assert bring(box, kind, src)["again"] is False
        got = bring(box, kind, src)
        assert got["state"] == "brought" and got["again"] is True and got["times"] == 2
        mirror = box.parent / "pile" / "brought-in" / f"{kind}-mine" / f"{file}.txt"
        assert mirror.is_file()
    assert [r["times"] for r in brought_rows(box)] == [2, 2, 2]


def test_a_folder_with_nothing_an_export_reader_can_read_is_refused(box, vault):
    for kind in ("joplin", "evernote", "google-keep"):
        got = bring(box, kind, vault, kind)  # only .md files: not this kind's
        assert got["state"] == "refused" and got["code"] == "bring_nothing", got
    assert brought_rows(box) == []


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
    kinds = ("notes", "calendar", "joplin", "evernote", "google-keep")
    asks = [("bring_in", {"kind": k, "from": str(vault), "as": "x"}) for k in kinds]
    for verb, arg in [*asks, ("brought_in", None)]:
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


# ── email, and a phone's texts ──────────────────────────────────────────────
def test_email_is_mirrored_with_its_map_hidden_from_every_question(box, mailbox):
    from test_leave import seal

    before = snapshot(mailbox)
    got = bring(box, "mail", mailbox, "home")
    assert got["state"] == "brought" and got["wrote"] == 1, got
    mirror = box.parent / "pile" / "brought-in" / "mail-home"
    text = (mirror / "inbox" / "roof.eml.txt").read_text()
    assert "Subject: Roof estimate" in text and "The total is 4,200." in text
    assert snapshot(mailbox) == before  # the original is never changed
    where = found(box, ROOF)
    assert where and where[0].startswith("brought-in/mail-home/inbox/roof.eml.txt")
    # Willow's mail keeps a map of where each passage came from, in a hidden
    # folder of the mirror: the kernel never reads it, so no question finds it
    assert (mirror / ".places").is_dir()
    assert not [w for w in found(box, "message places json") if ".places" in w]
    # what a model is given of it is withheld: an address never leaves
    asked = runtime.call(box, "grant", door="mcp", where="/w", session="s")
    seal(box, asked["seal"])
    page = runtime.call(box, "context", ROOF, door="mcp", where="/w", session="s")[
        "page"
    ]
    assert "roof" in page and "ada@example.org" not in page
    assert bring(box, "mail", mailbox, "home")["again"] is True  # a second run is safe


def test_a_phones_texts_are_mirrored_and_say_who_you_are_and_when(box, phone):
    got = bring(box, "sms", phone, "phone")
    assert got["state"] == "brought" and got["wrote"] == 1, got
    folder = box.parent / "pile" / "brought-in" / "sms-phone"
    mirror = folder.joinpath("texts.xml.txt")
    text = mirror.read_text()
    assert "# Dev Raman" in text and "me: Saturday works" in text
    where = found(box, LADDER)
    assert where and where[0].startswith("brought-in/sms-phone/")
    asked = {"kind": "sms", "from": str(phone), "as": "phone",
             "me": "Robin", "tz": "America/Denver"}  # fmt: skip
    named = runtime.call(box, "bring_in", asked, door="pipe")
    assert named["state"] == "brought" and named["again"] is True, named
    text = mirror.read_text()
    assert "Robin: Saturday works" in text and "me: Saturday" not in text
    assert "01:10" in text and "08:10" not in text  # as it was sent, in Denver


def test_what_else_an_importer_is_told_is_one_plain_line_and_only_what_it_takes(
    box, phone, vault
):
    base = {"kind": "sms", "from": str(phone), "as": "phone"}
    for also in ({"tz": "--to"}, {"me": "-x"}, {"me": "a\nb"}, {"me": ""}, {"tz": 7},
                 {"me": "x" * 81}):  # fmt: skip
        got = runtime.call(box, "bring_in", {**base, **also}, door="pipe")
        assert (got["state"], got["code"]) == ("refused", "bring_what"), also
    wrong = runtime.call(box, "bring_in", {**base, "tz": "Mars/Olympus"}, door="pipe")
    assert (wrong["state"], wrong["code"]) == (
        "refused",
        "bring_failed",
    )  # the add-on's no
    assert not (box.parent / "pile" / "brought-in").exists()
    # a kind that takes nothing more is told nothing more
    more = {
        "kind": "notes",
        "from": str(vault),
        "as": "v",
        "me": "Robin",
        "tz": "nowhere",
    }
    assert runtime.call(box, "bring_in", more, door="pipe")["state"] == "brought"


@pytest.mark.parametrize(
    "kind, fixture",
    [("mastodon", "mastodon"), ("goodreads", "goodreads"), ("karakeep", "karakeep"),
     ("opml", "opml"), ("takeout", "takeout"), ("bookmarks", "bookmarks"),
     ("zotero", "zotero"), ("code-graph", "code_graph")],
)  # fmt: skip
def test_each_newer_kinds_original_is_never_changed(box, request, kind, fixture):
    src = request.getfixturevalue(fixture)
    before = snapshot(src)
    assert bring(box, kind, src)["state"] == "brought"
    assert snapshot(src) == before
