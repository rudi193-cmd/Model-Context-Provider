"""Sharing with another person, by Willow's share: sentences the person
sealed, packed for someone they named, signed with an identity that is not
the seal key. The person sends; a model may only put a package together for
their seal, for someone they named; what arrives is read by a session they
let in, as another person's words."""

import json

import pytest
from test_answer import handed
from test_leave import seal

import runtime
import seal_page

SAID = "The first frost comes in late October"


def sentence(box):
    """A model's sentence the person sealed: its subject."""
    sid = handed(box)
    got = runtime.call(box, "answer", f"{SAID} [{sid}].", door="mcp")
    assert got["state"] == "waiting", got
    seal(box, got["seal"])
    return got["seal"]


def pipe(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="pipe")


def model(box, verb, arg=None, session="s1"):
    return runtime.call(box, verb, arg, door="mcp", where="/work/a", session=session)


@pytest.fixture
def walt(tmp_path):
    """Someone else's box, with an identity of its own: (the box, its key)."""
    pile = tmp_path / "walt-pile"
    pile.mkdir()
    (pile / "cases.md").write_text("The Kessler case is open.\n")
    b = tmp_path / "walt-box"
    run = runtime.willow("kernel.py", "init", "--box", str(b), "--pile", str(pile),
                         "--key", str(tmp_path / "walt.key"))  # fmt: skip
    assert run.returncode == 0, run.stderr
    return b, pipe(b, "share_id")["key"]


@pytest.fixture
def mine(box, walt):
    """This box with an identity, Walt named, and one sealed sentence."""
    key = pipe(box, "share_id")["key"]
    assert (
        pipe(box, "share_person", {"name": "Walt", "key": walt[1]})["state"] == "named"
    )
    return key, sentence(box)


def test_the_identity_is_made_once_and_is_not_the_seal_key(box, tmp_path):
    made = pipe(box, "share_id")
    assert made["state"] == "made" and runtime.SHARE_KEY.fullmatch(made["key"])
    assert pipe(box, "share_id") == {"state": "known", "key": made["key"]}
    idf = runtime.state(box) / "share.id"
    assert idf.stat().st_mode & 0o077 == 0  # the person's alone
    assert idf.read_text() != (tmp_path / "test.key").read_text()
    assert not list(box.rglob("share.id"))  # beside the box, never in it


def test_the_person_sends_a_sentence_they_sealed_to_someone_they_named(box, mine, walt):
    got = pipe(
        box, "share_send", {"answers": mine[1], "for": "Walt", "note": "As asked"}
    )
    assert got["state"] == "packed" and got["whom"] == "Walt", got
    pkg = json.loads(open(got["file"]).read())
    assert (
        pkg["for"] == walt[1] and pkg["from"] == mine[0] and pkg["note"] == "As asked"
    )
    assert [a["data"].strip() for a in pkg["answers"]] == [f"{SAID} [{a}]." for a in
                                                          [pkg["answers"][0]["data"].split("[")[1].split("]")[0]]]  # fmt: skip
    assert "dahlias" not in json.dumps(pkg)  # the sentence, never the file's line
    rows = [json.loads(r) for r in (box / "record.jsonl").read_text().splitlines()]
    assert rows[-1]["kind"] == "sent" and rows[-1]["package"] == got["package"]
    assert "packed for Walt" in pipe(box, "shared")["lines"][-1]
    assert not runtime.Path(got["file"]).resolve().is_relative_to(box.resolve())


def test_only_a_sealed_sentence_goes_and_only_to_someone_known(box, mine):
    let = model(box, "grant")  # sealed, but no sentence
    seal(box, let["seal"])
    for answers in (let["seal"], "proposal:" + "0" * 64, "", "x"):
        got = pipe(box, "share_send", {"answers": answers, "for": "Walt"})
        assert (got["state"], got["code"]) == ("refused", "share_refused"), answers
    got = pipe(box, "share_send", {"answers": mine[1], "for": "Aurelie"})
    assert got["code"] == "no_such_person"
    long = pipe(
        box, "share_send", {"answers": mine[1], "for": "Walt", "note": "x" * 501}
    )
    assert long["code"] == "share_refused"
    assert not (runtime.state(box) / "packages").exists()  # nothing was packed


def test_a_sentence_still_waiting_on_the_seal_is_never_packed(box):
    pipe(box, "share_id")
    sid = handed(box)
    owed = runtime.call(box, "answer", f"{SAID} [{sid}].", door="mcp")
    got = pipe(box, "share_send", {"answers": owed["seal"], "for": "a" * 64})
    assert (got["state"], got["code"]) == ("refused", "share_refused")
    run = runtime.willow("kernel.py", "decline", "--box", str(box), owed["seal"])
    assert run.returncode == 0, run.stderr
    got = pipe(box, "share_send", {"answers": owed["seal"], "for": "a" * 64})
    assert (got["state"], got["code"]) == ("refused", "share_refused")  # Willow's no
    assert not list((runtime.state(box) / "packages" / "out").glob("*"))


def test_without_an_identity_nothing_is_packed_or_received(box, tmp_path):
    subject = sentence(box)
    got = pipe(box, "share_send", {"answers": subject, "for": "a" * 64})
    assert got["code"] == "no_share_id"
    assert pipe(box, "share_receive", str(tmp_path / "p.json"))["code"] == "no_share_id"


def test_a_model_puts_a_package_together_and_it_waits_on_the_seal(box, mine):
    asked = {"answers": mine[1], "for": "Walt", "note": "For the file"}
    got = model(box, "share_propose", asked)
    assert got["state"] == "waiting" and got["seal"].startswith("proposal:")
    assert model(box, "share_propose", asked) == got  # asked again: the same one
    owed = [w for w in runtime.waiting(box)["waiting"] if w["seal"] == got["seal"]]
    assert runtime.what_waits(owed[0], {}) == "a package to send someone"
    assert seal_page.kind_of(owed[0]) == "share"
    words = json.loads(
        (box / "proposals" / f"{got['seal'][len('proposal:'):]}.json").read_text())["data"]  # fmt: skip
    assert f"for: Walt\nkey: {runtime.share_people(box)['Walt']}\n" in words
    assert "note: For the file" in words and SAID in words  # all of it, to read
    assert not (runtime.state(box) / "packages").exists()  # nothing packed yet
    seal(box, got["seal"])
    packed = model(box, "share_propose", asked)
    assert packed["state"] == "packed" and packed["whom"] == "Walt"
    assert model(box, "share_propose", asked)["package"] == packed["package"]  # once
    assert len(list((runtime.state(box) / "packages" / "out").iterdir())) == 1
    assert SAID not in json.dumps(packed)  # told its id, never what it holds
    assert "you sealed for Walt is packed" in pipe(box, "shared")["lines"][-1]


def test_a_model_never_gives_a_key_or_a_name_the_person_did_not(box, mine, walt):
    for whom in (walt[1], "b" * 64, "Aurelie", ""):
        got = model(box, "share_propose", {"answers": mine[1], "for": whom})
        assert (got["state"], got["code"]) == ("refused", "no_such_person"), whom
    assert runtime.waiting(box)["state"] == "empty"
    for verb in ("share_id", "share_person", "share_send", "share_receive",
                 "share_forward", "shares"):  # fmt: skip
        assert model(box, verb, {})["code"] == "no_verb", verb
    assert pipe(box, "share_propose", {})["code"] == "no_verb"


def test_a_package_declined_or_stopped_is_never_packed(box, mine):
    asked = {"answers": mine[1], "for": "Walt"}
    got = model(box, "share_propose", asked)
    run = runtime.willow("kernel.py", "decline", "--box", str(box), got["seal"])
    assert run.returncode == 0, run.stderr
    assert model(box, "share_propose", asked) == {"state": "unsealed", "whom": "Walt"}
    other = {**asked, "note": "again"}
    got = model(box, "share_propose", other)
    seal(box, got["seal"])
    assert pipe(box, "stop", got["seal"])["state"] == "stopped"
    assert model(box, "share_propose", other)["code"] == "stopped"
    assert not (runtime.state(box) / "packages").exists()


def test_a_name_is_never_moved_to_another_key_quietly(box, mine):
    got = pipe(box, "share_person", {"name": "Walt", "key": "c" * 64})
    assert got["code"] == "share_refused"
    assert pipe(box, "share_person", {"name": "Walt", "key": "c" * 64,
                                      "replace": True})["state"] == "named"  # fmt: skip
    assert pipe(box, "share_person", {"name": "Walt", "key": ""})["people"] == []
    for bad in ({"name": "../x", "key": "c" * 64}, {"name": "W", "key": "short"}, "W"):
        assert pipe(box, "share_person", bad)["code"] == "share_refused"


def test_what_arrives_is_received_by_the_person_and_read_by_a_session_let_in(
    box, mine, walt
):
    sent = pipe(
        box, "share_send", {"answers": mine[1], "for": "Walt", "note": "As asked"}
    )
    theirs = walt[0]
    got = pipe(theirs, "share_receive", sent["file"])
    assert (got["state"], got["verdict"]) == ("received", "good"), got
    assert "received, not sealed by you" in got["said"]
    told = model(theirs, "share_received")
    assert (told["state"], told["code"]) == ("refused", "no_grant")
    seal(theirs, model(theirs, "grant")["seal"])
    pipe(theirs, "share_person", {"name": "Ines", "key": mine[0]})
    (row,) = model(theirs, "share_received")["packages"]
    assert row["layers"][0]["from"] == "Ines" and row["layers"][0]["note"] == "As asked"
    assert len(row["sentences"]) == 1 and SAID in row["sentences"][0]
    assert (
        pipe(theirs, "share_receive", sent["file"])["verdict"] == "good"
    )  # twice: once
    assert runtime.waiting(theirs)["state"] == "empty"  # receiving is never sealing


def test_a_package_changed_on_the_way_or_beside_the_box_is_given_to_no_one(
    box, mine, walt, tmp_path
):
    sent = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    theirs = walt[0]
    seal(theirs, model(theirs, "grant")["seal"])
    forged = tmp_path / "forged.json"
    forged.write_text(open(sent["file"]).read().replace("late October", "early June"))
    got = pipe(theirs, "share_receive", str(forged))
    assert got["verdict"] == "broken"
    assert model(theirs, "share_received") == {"state": "empty"}
    assert pipe(theirs, "share_receive", sent["file"])["verdict"] == "good"
    (kept,) = (runtime.state(theirs) / "packages" / "in").iterdir()
    kept.write_text(kept.read_text().replace("late October", "early June"))
    assert model(theirs, "share_received") == {"state": "empty"}  # not on trust


def test_a_package_for_someone_else_is_not_kept(box, mine, walt, tmp_path):
    sent = pipe(box, "share_send", {"answers": mine[1], "for": "d" * 64})
    got = pipe(walt[0], "share_receive", sent["file"])
    assert got["verdict"] == "not-for-you"
    assert not (runtime.state(walt[0]) / "packages" / "in").exists()


def test_a_received_package_is_passed_on_in_a_layer_of_the_persons_own(box, mine, walt):
    sent = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    theirs = walt[0]
    got = pipe(theirs, "share_receive", sent["file"])
    pipe(theirs, "share_person", {"name": "Aurelie", "key": "e" * 64})
    on = pipe(theirs, "share_forward", {"package": got["package"], "for": "Aurelie",
                                        "note": "Reviewed"})  # fmt: skip
    assert on["state"] == "packed" and on["whom"] == "Aurelie", on
    pkg = json.loads(open(on["file"]).read())
    assert pkg["note"] == "Reviewed" and pkg["wraps"]["from"] == mine[0]
    nope = pipe(
        theirs, "share_forward", {"package": "package:" + "0" * 64, "for": "Aurelie"}
    )
    assert nope["code"] == "share_refused"
    listed = pipe(theirs, "shares")
    assert listed["people"] == {"Aurelie": "e" * 64} and len(listed["log"]) == 2
