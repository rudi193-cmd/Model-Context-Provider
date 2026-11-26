"""The record is a chain, so a row is never taken back: the runtime writes
one only when something happened. A yes the kernel gave is remembered, in
memory and only while the proposal it was for reads the same (Willow's
forge: put to the person once and remembered); what waits on the seal is
asked of the kernel once while a call is answered."""

import json

from test_leave import seal

from conftest import facts

import runtime


def model(box, verb, arg=None, where="/work/a", session="s1"):
    return runtime.call(box, verb, arg, door="mcp", where=where, session=session)


def pipe(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="pipe")


def kinds(box):
    rows = (box / "record.jsonl").read_text().splitlines()
    return [json.loads(r)["kind"] for r in rows]


def test_a_yes_is_asked_of_the_kernel_once_and_then_remembered(box):
    got = model(box, "grant")
    seal(box, got["seal"])
    assert model(box, "notes") == {"state": "empty"}  # the kernel is asked: a row
    before = kinds(box)
    for _ in range(5):
        assert model(box, "notes") == {"state": "empty"}
        assert model(box, "grant")["state"] == "granted"
        assert model(box, "tasks") == {"state": "empty"}
    after = kinds(box)
    assert after.count("bite") == before.count("bite")  # not asked again
    assert after.count("out") - before.count("out") <= 15  # once a call, at most


def test_it_is_kept_in_memory_and_nowhere_else(box):
    seal(box, model(box, "grant")["seal"])
    model(box, "notes")
    beside = sorted(p.name for p in runtime.state(box).iterdir())
    model(box, "notes")
    assert sorted(p.name for p in runtime.state(box).iterdir()) == beside
    assert (str(box), f"grant {model(box, 'grant')['grant']}") in runtime.REMEMBERED
    runtime.REMEMBERED.clear()  # a door that starts again knows nothing
    before = kinds(box).count("bite")
    assert model(box, "grant")["state"] == "granted"
    assert kinds(box).count("bite") == before + 1  # and asks the kernel


def test_a_no_is_never_remembered_so_a_seal_is_seen_at_once(box):
    got = model(box, "grant")
    for _ in range(3):
        assert facts(model(box, "context", "when does the first frost come")) == {
            "state": "populated"}  # fmt: skip
    assert not [k for k in runtime.REMEMBERED if k[0] == str(box)]
    seal(box, got["seal"])
    assert model(box, "context", "when does the first frost come")["state"] == "left"


def test_what_the_person_stopped_or_a_session_that_ended_bites_at_the_next_call(box):
    got = model(box, "grant")
    seal(box, got["seal"])
    assert model(box, "notes") == {"state": "empty"}
    assert pipe(box, "stop", got["seal"])["state"] == "stopped"
    assert model(box, "job", "ls")["code"] == "no_grant"  # remembered, and still no
    again = model(box, "grant", session="s2")
    seal(box, again["seal"])
    assert model(box, "grant", session="s2")["state"] == "granted"
    runtime.grant_end(box, "s2")
    assert model(box, "job", "ls", session="s2")["code"] == "no_grant"


def test_a_yes_stands_only_while_its_proposal_reads_the_same(box):
    got = model(box, "grant")
    seal(box, got["seal"])
    assert model(box, "grant")["state"] == "granted"
    f = box / "proposals" / f"{got['seal'][len('proposal:') :]}.json"
    whole = f.read_text()
    f.write_text(whole.replace("/work/a", "/work/b"))  # stale: asked again
    before = kinds(box).count("bite")
    assert model(box, "job", "ls")["code"] == "no_grant"  # and the kernel says no
    assert kinds(box).count("bite") > before
    assert not [k for k in runtime.REMEMBERED if k[0] == str(box)]
    f.unlink()
    assert model(box, "job", "ls")["code"] == "no_grant"
    f.write_text(whole)  # as it was sealed: the kernel serves it again
    assert model(box, "grant")["state"] == "granted"


def test_a_sealed_task_and_a_kept_note_are_remembered_the_same_way(box):
    task = model(box, "task_add", "water the beds")
    note = model(box, "capture", "the gate sticks in the wet")
    seal(box, task["seal"])
    seal(box, note["seal"])
    first = (model(box, "tasks"), model(box, "notes"))
    before = kinds(box).count("bite")
    assert (model(box, "tasks"), model(box, "notes")) == first
    assert kinds(box).count("bite") == before
    assert first[0]["tasks"][0]["text"] == "water the beds"
    assert first[1]["notes"] == [{"text": "the gate sticks in the wet"}]


def test_what_was_remembered_is_never_handed_out_to_be_changed(box):
    seal(box, model(box, "grant")["seal"])
    question = f"grant {model(box, 'grant')['grant']}"
    got = runtime.asked_of_kernel(box, question)
    got["answer"] = "something else"
    assert runtime.asked_of_kernel(box, question)["answer"] != "something else"


def test_what_waits_is_asked_once_a_call_and_again_after_anything_changes_it(box):
    before = kinds(box).count("out")
    model(box, "tasks")
    assert kinds(box).count("out") - before <= 1
    # a call that proposes sees what it proposed: nothing stale within it
    got = model(box, "grant")
    assert got["state"] == "waiting" and got["seal"] in runtime.waiting_seals(box)
    seal(box, got["seal"])  # the person's, in another program: seen by the next call
    assert model(box, "grant")["state"] == "granted"
    assert not runtime.OWED and runtime.OWED_FOR == 0  # nothing kept between calls
