"""The checks run on a model's sentence are kept, handed on and shown."""

import json
import zipfile

from test_answer import handed

import runtime
import seal_page


def stood(box):
    sid = handed(box)
    return runtime.call(box, "answer", f"The first frost comes in late October [{sid}].",
                        door="mcp")  # fmt: skip


def kept(box):
    return json.loads((runtime.state(box) / "checks.json").read_text())


def test_checks_are_kept_when_a_sentence_stands_without_its_words(box):
    got = stood(box)
    row = kept(box)[got["seal"]]
    names = {c["name"]: c["said"] for c in row["checks"]}
    assert names["every cite was served"] == "held" and len(row["checks"]) == 4
    assert len(row["page"]) == 64
    assert "October" not in (runtime.state(box) / "checks.json").read_text()


def test_nothing_is_kept_for_a_struck_sentence(box):
    sid = handed(box)
    got = runtime.call(box, "answer", f"The first frost comes in early October [{sid}].",
                       door="mcp")  # fmt: skip
    assert got["state"] == "struck"
    assert not (runtime.state(box) / "checks.json").exists()


def test_waiting_carries_the_checks(box):
    got = stood(box)
    (w,) = runtime.call(box, "waiting", door="pipe")["waiting"]
    assert w["checks"] == kept(box)[got["seal"]]


def card_of(box):
    (w,) = runtime.call(box, "waiting", door="pipe")["waiting"]
    return seal_page.card(box, "tok", w)


def test_the_card_lists_each_check_escaped(box):
    got = stood(box)
    html = card_of(box)
    assert "What code checked before this reached you" in html
    assert html.count("(held)") == 3 and "nothing to check there" in html
    f = runtime.state(box) / "checks.json"
    data = kept(box)
    data[got["seal"]]["checks"].append({"name": "<script>a</script>",
                                        "said": "<script>b</script>"})  # fmt: skip
    f.write_text(json.dumps(data))
    html = card_of(box)
    assert "<script>" not in html and "&lt;script&gt;a&lt;/script&gt;" in html


def test_an_older_sentence_says_its_checks_are_not_kept(box):
    stood(box)
    (runtime.state(box) / "checks.json").unlink()
    html = card_of(box)
    assert "isn’t kept" in html and "(held)" not in html


def test_backup_and_restore_carry_the_checks(box, tmp_path_factory):
    stood(box)
    was = (runtime.state(box) / "checks.json").read_bytes()
    usb = tmp_path_factory.mktemp("usb")
    got = runtime.call(box, "backup", str(usb), door="pipe")
    assert got["state"] == "kept", got
    with zipfile.ZipFile(usb / got["runtime"]) as z:
        assert z.read("checks.json") == was
    (runtime.state(box) / "checks.json").unlink()
    back = runtime.call(box, "restore", str(usb / got["runtime"]), door="pipe")
    assert back["state"] == "restored", back
    assert (runtime.state(box) / "checks.json").read_bytes() == was
