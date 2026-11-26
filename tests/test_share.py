"""Sharing with another person, by Willow's share: sentences the person
sealed, packed for someone they named, signed with an identity that is not
the seal key. The person sends; a model may only put a package together for
their seal, for someone they named; what arrives is read by a session they
let in, as another person's words."""

import importlib.util
import json

import pytest
from test_answer import handed
from test_leave import seal

import runtime
import seal_page

SAID = "The first frost comes in late October"
HAS_KART = importlib.util.find_spec("kartikeya") is not None
needs_kart = pytest.mark.skipif(not HAS_KART, reason="needs Kartikeya and bwrap")


@pytest.fixture(autouse=True)
def no_fleet(monkeypatch):
    """A resource group this machine exports for a fleet is not these tests'."""
    monkeypatch.delenv("KART_CGROUP_PARENT", raising=False)


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
    assert idf.read_text() != (box.parent / "test.key").read_text()
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
                 "share_forward", "share_rotate", "share_witness", "shares",
                 "job_write", "job_take", "job_run", "job_gather"):  # fmt: skip
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
    # a key nobody named is said by its start; once named, by the name too
    assert f"from {mine[0][:12]}…" in got["said"] and "Ines" not in got["said"]
    assert f"to Walt ({walt[1][:12]}…)" in pipe(box, "shares")["log"][-1]
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
    assert f"Ines ({mine[0][:12]}…)" in pipe(theirs, "shares")["log"][-1]
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


# ── a new key, and the record held to what others kept ──────────────────────
def test_a_key_is_rotated_never_swapped_and_the_old_one_is_kept(box, mine, walt):
    assert pipe(box, "share_rotate")["code"] == "share_refused"  # nothing sent yet
    first = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    assert pipe(walt[0], "share_receive", first["file"])["verdict"] == "good"
    old_seed = (runtime.state(box) / "share.id").read_text()
    got = pipe(box, "share_rotate")
    assert got["state"] == "rotated" and got["was"] == mine[0] and got["key"] != mine[0]
    assert pipe(box, "share_id") == {"state": "known", "key": got["key"]}
    assert (runtime.state(box) / "share.id.was-1").read_text() == old_seed
    assert (runtime.state(box) / "share.id").read_text() != old_seed
    rows = [json.loads(r) for r in (box / "record.jsonl").read_text().splitlines()]
    assert rows[-1]["kind"] == "rotated" and rows[-1]["new"] == got["key"]
    # the next package carries the rotation: Walt sees the same person
    again = pipe(box, "share_send", {"answers": mine[1], "for": "Walt", "note": "2"})
    assert json.loads(open(again["file"]).read())["from"] == got["key"]
    told = pipe(walt[0], "share_receive", again["file"])
    assert told["verdict"] == "good" and "rotated since" in told["said"]
    assert pipe(box, "share_rotate")["state"] == "rotated"  # and again
    assert (runtime.state(box) / "share.id.was-2").exists()


def test_without_an_identity_there_is_nothing_to_rotate(box):
    assert pipe(box, "share_rotate")["code"] == "no_share_id"


def test_the_record_is_held_to_the_packages_signed_over_it(box, mine, walt, tmp_path):
    assert pipe(box, "share_witness") == {"state": "no_witness", "lines": []}
    sent = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    got = pipe(box, "share_witness")  # the copies beside the box
    assert got["state"] == "holds" and got["lines"][0].startswith("holds")
    kept = tmp_path / "walt-kept.json"  # a copy someone else kept
    kept.write_text(open(sent["file"]).read())
    assert pipe(box, "share_witness", {"packages": [str(kept)]})["state"] == "holds"
    # a package signed for another record is no witness of this one
    theirs = pipe(walt[0], "share_person", {"name": "Ines", "key": mine[0]})
    assert theirs["state"] == "named"
    assert (
        pipe(walt[0], "share_witness", {"packages": str(kept)})["state"] == "no_witness"
    )
    # the record cut back to before the send: the package says so
    record = box / "record.jsonl"
    lines = record.read_text().splitlines()
    record.write_text("\n".join(lines[:-1]) + "\n")
    cut = pipe(box, "share_witness", {"packages": [str(kept)]})
    assert cut["state"] == "does_not_hold" and "cut short" in cut["lines"][0]


def test_a_backup_never_holds_the_identity(box, mine, tmp_path):
    usb = tmp_path / "usb"
    usb.mkdir()
    kept = pipe(box, "backup", str(usb))
    assert kept["state"] == "kept", kept
    assert "share.key" in kept["files"] and "share-people.json" in kept["files"]
    assert not [f for f in kept["files"] if f.startswith("share.id")]


# ── a correction follows the first package's path ───────────────────────────
def test_a_correction_says_where_the_first_one_went_and_follows_it(box, mine, walt):
    theirs = walt[0]
    pipe(theirs, "share_person", {"name": "Aurelie", "key": "e" * 64})
    first = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    got = pipe(theirs, "share_receive", first["file"])
    on = pipe(theirs, "share_forward", {"package": got["package"], "for": "Aurelie"})
    fixed = pipe(box, "share_send", {"answers": mine[1], "for": "Walt",
                                     "note": "the date was wrong",
                                     "replaces": first["package"]})  # fmt: skip
    assert fixed["state"] == "packed", fixed
    told = pipe(theirs, "share_receive", fixed["file"])
    assert told["verdict"] == "good" and "it replaces" in told["said"]
    (nxt,) = told["forward_with"]
    assert nxt["replaces"] == on["package"]  # what to name when passing it on
    again = pipe(theirs, "share_forward", {"package": told["package"], "for": "Aurelie",
                                           "replaces": nxt["replaces"]})  # fmt: skip
    assert again["state"] == "packed"
    assert json.loads(open(again["file"]).read())["replaces"] == on["package"]
    bad = pipe(box, "share_send", {"answers": mine[1], "for": "Walt",
                                   "replaces": "package:" + "0" * 64})  # fmt: skip
    assert bad["code"] == "share_refused"  # not one this record sent


def test_a_model_may_propose_a_correction_and_it_says_so(box, mine):
    first = pipe(box, "share_send", {"answers": mine[1], "for": "Walt"})
    asked = {"answers": mine[1], "for": "Walt", "replaces": first["package"]}
    got = model(box, "share_propose", asked)
    words = json.loads(
        (box / "proposals" / f"{got['seal'][len('proposal:'):]}.json").read_text())["data"]  # fmt: skip
    assert f"replaces: {first['package']}" in words
    seal(box, got["seal"])
    packed = model(box, "share_propose", asked)
    assert json.loads(open(packed["file"]).read())["replaces"] == first["package"]
    assert model(box, "share_propose", {**asked, "replaces": "that one"})["code"] == (
        "share_refused")  # fmt: skip


# ── a job that travels in a package ─────────────────────────────────────────
COUNT = "grep -rhic frost {pile} | paste -sd+ | bc"


def test_a_job_is_written_sealed_and_sent_and_never_runs_because_it_arrived(
    box, mine, walt
):
    assert (
        pipe(box, "job_write", "# allow_net\ncurl example.com")["code"] == "job_refused"
    )
    assert pipe(box, "job_write", " ")["code"] == "job_refused"
    job = pipe(box, "job_write", {"text": COUNT, "words": "count frost"})
    assert job["state"] == "waiting", job
    (owed,) = [w for w in runtime.waiting(box)["waiting"] if w["seal"] == job["seal"]]
    assert runtime.what_waits(owed, {}) == "a job to run over your folder"
    asked = {"answers": job["seal"], "for": "Walt"}
    assert pipe(box, "share_send", asked)["code"] == "share_refused"  # not sealed yet
    seal(box, job["seal"])
    assert (
        model(box, "share_propose", asked)["code"] == "share_refused"
    )  # never a model's
    sent = pipe(box, "share_send", asked)
    assert sent["state"] == "packed", sent
    theirs = walt[0]
    got = pipe(theirs, "share_receive", sent["file"])
    assert pipe(theirs, "job_run", job["seal"])["code"] == "job_refused"  # not theirs
    taken = pipe(theirs, "job_take", got["package"])
    assert taken["state"] == "waiting" and taken["seal"].startswith("proposal:")
    rows = (theirs / "record.jsonl").read_text()
    assert '"kind": "ran"' not in rows and '"kind":"ran"' not in rows  # nothing ran
    assert pipe(theirs, "job_run", taken["seal"])["code"] == "job_refused"  # unsealed
    assert pipe(theirs, "job_take", "package:" + "0" * 64)["code"] == "job_refused"


@needs_kart
def test_a_job_runs_once_sealed_and_only_numbers_go_back(box, mine, walt, tmp_path):
    theirs = walt[0]
    (tmp_path / "walt-pile" / "frost.md").write_text("frost\nFrost again\nno\n")
    job = pipe(box, "job_write", COUNT)
    seal(box, job["seal"])
    sent = pipe(box, "share_send", {"answers": job["seal"], "for": "Walt"})
    got = pipe(theirs, "share_receive", sent["file"])
    taken = pipe(theirs, "job_take", got["package"])
    seal(theirs, taken["seal"])
    ran = pipe(theirs, "job_run", taken["seal"])
    assert ran["state"] == "ran" and ran["seal"].startswith("proposal:"), ran
    assert open(ran["file"]).read().split() == ["2"]  # theirs to read, on their machine
    back = {"answers": ran["seal"], "for": "Ines"}
    pipe(theirs, "share_person", {"name": "Ines", "key": mine[0]})
    assert pipe(theirs, "share_send", back)["code"] == "share_refused"  # not sealed
    seal(theirs, ran["seal"])
    answer = pipe(theirs, "share_send", back)
    assert answer["state"] == "packed", answer
    home = pipe(box, "share_receive", answer["file"])
    assert home["verdict"] == "good"
    total = pipe(box, "job_gather", {"packages": [home["package"]]})
    assert total["state"] == "waiting" and "total" in total["said"], total
    assert "Kessler" not in open(answer["file"]).read()  # no word of their files


@needs_kart
def test_a_job_that_prints_words_proposes_nothing_and_its_words_never_go(
    box, mine, walt, tmp_path
):
    job = pipe(box, "job_write", "cat {pile}/*")
    seal(box, job["seal"])
    ran = pipe(box, "job_run", job["seal"])
    assert ran["state"] == "ran" and "seal" not in ran, ran
    assert "nothing is proposed" in ran["said"]
    assert "frost" in open(ran["file"]).read()  # it stays on this machine
    # a result run by hand without the shape, sealed: still never packed
    out = tmp_path / "by-hand.txt"
    run = runtime.kart(box, "run", "--box", str(box), "--job", job["seal"],
                       "--to", str(out))  # fmt: skip
    words = runtime.re.search(
        r"^result (proposal:[0-9a-f]{64})", run.stdout, runtime.re.M
    )
    seal(box, words.group(1))
    got = pipe(box, "share_send", {"answers": words.group(1), "for": "Walt"})
    assert (got["state"], got["code"]) == ("refused", "share_refused")


def test_the_sentence_sealed_last_is_sent_by_that_word_and_each_is_listed(box, mine):
    """No long id to copy: `last` is the newest sentence the kernel wrote
    down, and `shares` lists each by its first words."""
    _, subject = mine
    (one,) = pipe(box, "shares")["sentences"]
    assert one["seal"] == subject and one["says"].startswith(SAID[:20])
    got = pipe(box, "share_send", {"answers": "last", "for": "Walt"})
    assert (got["state"], got["sentences"]) == ("packed", 1), got
    # one still waiting, or declined, is never the last: nothing wrote it down
    sid = handed(box)
    waits = runtime.call(
        box, "answer", f"The dahlias come up then [{sid}].", door="mcp"
    )
    assert waits["state"] == "waiting" and waits["seal"] != subject, waits
    assert [s["seal"] for s in pipe(box, "shares")["sentences"]] == [subject]
    seal(box, waits["seal"])  # sealed, it is the last
    assert pipe(box, "shares")["sentences"][0]["seal"] == waits["seal"]


def test_last_with_no_sentence_sealed_is_refused_in_plain_words(box, walt):
    pipe(box, "share_id")
    pipe(box, "share_person", {"name": "Walt", "key": walt[1]})
    got = pipe(box, "share_send", {"answers": "last", "for": "Walt"})
    assert got["state"] == "refused" and "sealed no sentence" in got["why"]
    assert pipe(box, "shares")["sentences"] == []
    # and a model's door has no such word: it names what it means
    assert (
        model(box, "share_propose", {"answers": "last", "for": "Walt"})["state"]
        == "refused"
    )
