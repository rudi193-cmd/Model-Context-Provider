"""One yes for one session in one folder. The person seals it once; while it
stands, a model's tools answer directly, and it ends with the session.
Nothing beside the box is trusted for the yes: the kernel says it is sealed."""

import importlib.util
import json

import pytest
from test_leave import seal

import runtime
import seal_page

FROST = "when does the first frost come"
HAS_KART = importlib.util.find_spec("kartikeya") is not None


@pytest.fixture(autouse=True)
def no_fleet(monkeypatch):
    """A resource group this machine exports for a fleet is not these tests'."""
    monkeypatch.delenv("KART_CGROUP_PARENT", raising=False)


def call(box, verb, arg=None, where="/work/a", session="s1", door="mcp"):
    return runtime.call(box, verb, arg, door=door, where=where, session=session)


def let_in(box, where="/work/a", session="s1"):
    got = call(box, "grant", where=where, session=session)
    assert got["state"] == "waiting", got
    seal(box, got["seal"])
    return got


def test_without_a_grant_a_model_is_told_only_that_there_is_something(box):
    assert call(box, "context", FROST) == {"state": "populated"}
    got = call(box, "job", "ls {pile}")
    assert (got["state"], got["code"]) == ("refused", "no_grant")
    assert "frost" not in json.dumps(got) and "garden" not in json.dumps(got)


def test_a_grant_is_asked_once_and_waits_on_the_persons_seal(box):
    got = call(box, "grant")
    assert got["state"] == "waiting" and got["seal"].startswith("proposal:")
    assert call(box, "grant") == got  # asked again: the same one, nothing new
    (owed,) = runtime.waiting(box)["waiting"]
    assert owed["path"].startswith("grants/") and "for: /work/a" in owed["words"]
    assert runtime.what_waits(owed, {}) == "a session asking to read your files"
    assert call(box, "context", FROST) == {"state": "populated"}  # not yet


def test_once_granted_context_answers_directly_and_nothing_waits(box):
    let_in(box)
    assert call(box, "grant")["state"] == "granted"
    got = call(box, "context", FROST)
    assert got["state"] == "left" and "late October" in got["page"]
    assert "[garden.md" in got["page"]  # where it is from
    assert runtime.waiting(box)["state"] == "empty"
    assert call(box, "context", "a word no file holds zzqx")["state"] != "left"
    log = (runtime.state(box) / "sent.jsonl").read_text()
    assert "late October" not in log and '"verb": "context"' in log


def test_a_grant_is_for_its_own_session_and_its_own_folder(box):
    let_in(box)
    for where, session in (("/work/b", "s1"), ("/work/a", "s2"), ("", "s1")):
        got = call(box, "context", FROST, where=where, session=session)
        assert got == {"state": "populated"}, (where, session)
        assert (
            call(box, "job", "ls", where=where, session=session)["code"] == "no_grant"
        )
    assert (
        call(box, "context", FROST, where="/work/a/", session="s1")["state"] == "left"
    )


def test_it_ends_with_the_session_and_is_never_open_again(box):
    let_in(box)
    end = {"hook_event_name": "SessionEnd", "session_id": "s1", "cwd": "/work/a"}
    assert runtime.call(box, "event", end, door="guard") == {"state": "empty"}
    assert call(box, "context", FROST) == {"state": "populated"}
    (g,) = runtime.call(box, "grants", door="pipe")["grants"]
    assert g["stands"] == "ended"
    # the same session id again is a new asking, with a seal of its own to wait on
    again = call(box, "grant")
    assert again["state"] == "waiting" and again["seal"] != g["seal"]
    assert call(box, "context", FROST) == {"state": "populated"}
    seal(box, again["seal"])
    assert call(box, "context", FROST)["state"] == "left"
    other = {"hook_event_name": "SessionEnd", "session_id": "nobody", "cwd": "/work/a"}
    assert runtime.call(box, "event", other, door="guard") == {"state": "empty"}


def test_the_person_stops_it_with_no_key(box):
    got = let_in(box)
    assert runtime.call(box, "stop", got["seal"], door="pipe")["state"] == "stopped"
    assert call(box, "context", FROST) == {"state": "populated"}
    assert call(box, "job", "ls")["code"] == "no_grant"
    (g,) = runtime.call(box, "grants", door="pipe")["grants"]
    assert g["stands"] == "stopped"


def test_a_grant_declined_or_edited_beside_the_box_lets_no_one_in(box):
    got = call(box, "grant")
    run = runtime.willow("kernel.py", "decline", "--box", str(box), got["seal"])
    assert run.returncode == 0, run.stderr
    assert call(box, "context", FROST) == {"state": "populated"}
    # a grants.json that claims a yes the kernel never gave
    f = runtime.state(box) / "grants.json"
    doc = json.loads(f.read_text())
    gid, _, _ = runtime.grant_of("/work/z", "s9")
    doc[gid] = {"seal": "proposal:" + "0" * 64, "for": "/work/z", "session": "s9"}
    f.write_text(json.dumps(doc))
    assert call(box, "context", FROST, where="/work/z", session="s9") == {
        "state": "populated"
    }
    f.write_text("not json")
    assert call(box, "context", FROST) == {"state": "populated"}


def test_only_a_models_door_asks_and_only_the_persons_lists(box):
    for door in ("pipe", "hook", "guard"):
        assert call(box, "grant", door=door)["code"] == "no_verb"
        assert call(box, "job", "ls", door=door)["code"] == "no_verb"
    for door in ("mcp", "hook", "guard", "nobody"):
        assert call(box, "grants", door=door)["code"] == "no_verb"
    assert runtime.call(box, "grants", door="pipe") == {"state": "empty", "grants": []}


def test_a_session_start_asks_and_says_so_and_a_prompt_hook_is_not_let_in(box):
    start = {"hook_event_name": "SessionStart", "session_id": "s1", "cwd": "/work/a"}
    got = runtime.call(box, "event", start, door="guard")
    assert got["state"] == "handed" and "has asked to read" in got["says"]
    assert "frost" not in got["says"]
    (owed,) = runtime.waiting(box)["waiting"]
    seal(box, owed["seal"])
    got = runtime.call(box, "event", start, door="guard")
    assert "has let this session read" in got["says"]
    # the prompt hook asks at every prompt: it is never handed a grant's passages
    assert call(box, "context", FROST, door="hook") == {"state": "populated"}
    assert call(box, "context", FROST)["state"] == "left"  # the model's own asking is


def test_what_is_given_under_a_grant_is_withheld(box):
    (box.parent / "pile" / "call.md").write_text(
        "Ring Aoife on 07700 900123 about the frost.\n"
    )
    (runtime.state(box) / "names.txt").write_text("Aoife\n")
    let_in(box)
    page = call(box, "context", "who do I ring about the frost")["page"]
    assert "Aoife" not in page and "900123" not in page and "[withheld: name]" in page


def test_the_seal_page_shows_a_grant_as_what_it_is(box):
    call(box, "grant")
    (w,) = runtime.waiting(box)["waiting"]
    html = seal_page.card(box, "tok", w)
    assert "A session asking to read your files" in html
    assert "Seal: yes, for this session" in html and "/work/a" in html
    assert "You are not asked again for each one" in html
    groups = runtime.call(box, "status", door="pipe")["groups"]
    assert "Sessions let in" in [g["name"] for g in groups]


# ── a job, in the sandbox ───────────────────────────────────────────────────
def test_a_job_runs_over_the_folder_and_what_it_printed_comes_back(box):
    let_in(box)
    got = call(
        box, "job", "grep -rhic frost {pile} | sort | tail -1; ls {pile} | wc -l"
    )
    if not HAS_KART:  # this Python has no Kartikeya: kart says so, and nothing ran
        assert (got["state"], got["code"]) == ("refused", "job_refused")
        assert "Kartikeya isn't installed" in got["why"]
        return
    assert got["state"] == "left", got
    assert got["page"].split() == ["1", "2"] and got["ended"] == "well"
    assert runtime.waiting(box)["state"] == "empty"  # nothing is proposed
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    (ran,) = [r for r in rows if r["kind"] == "ran"]
    assert ran["sealed"] is False and ran["status"] == "completed"
    assert "frost" not in json.dumps(ran)
    log = (runtime.state(box) / "sent.jsonl").read_text()
    assert '"verb": "job"' in log


@pytest.mark.skipif(not HAS_KART, reason="needs Kartikeya, Python 3.11+")
def test_a_job_cannot_reach_the_box_the_key_or_the_network(box, tmp_path):
    let_in(box)
    probe = (f"echo \"key: $(cat {tmp_path / 'test.key'} 2>/dev/null | wc -c)\"; "
             f"echo \"box: $(ls {box} 2>/dev/null | wc -l)\"; "
             "(echo x > {pile}/new) 2>/dev/null && echo wrote || echo held; "
             "echo \"home: ${HOME##*/}\"; env | grep -c -i -E \"claude|willow|kart\"")  # fmt: skip
    got = call(box, "job", probe)
    assert got["state"] == "left", got
    assert got["page"].splitlines() == ["key: 0", "box: 0", "held", "home: home", "0"]
    assert not (box.parent / "pile" / "new").exists()
    got = call(box, "job", "# allow_net\ncurl example.com")
    assert got["code"] == "job_refused" and "asks for the network" in got["why"]


@pytest.mark.skipif(not HAS_KART, reason="needs Kartikeya, Python 3.11+")
def test_what_a_job_prints_is_withheld_and_a_flood_is_not_given(box, monkeypatch):
    (box.parent / "pile" / "call.md").write_text("Ring Aoife on 07700 900123.\n")
    (runtime.state(box) / "names.txt").write_text("Aoife\n")
    let_in(box)
    page = call(box, "job", "cat {pile}/call.md")["page"]
    assert "Aoife" not in page and "900123" not in page
    bad = call(box, "job", "echo partial; exit 3")
    assert (
        bad["state"] == "left" and bad["ended"] == "badly" and "partial" in bad["page"]
    )
    assert bad["how"] == "exited 3"  # how it failed, and not again what it printed
    monkeypatch.setattr(runtime, "JOB_MOST", 40)
    got = call(box, "job", "cat {pile}/*")
    assert (got["state"], got["code"]) == ("refused", "job_too_long")
    assert "frost" not in json.dumps(got)


@pytest.mark.skipif(not HAS_KART, reason="needs Kartikeya, Python 3.11+")
def test_a_job_says_when_it_was_clipped_and_when_it_ran_out_of_time(box, monkeypatch):
    let_in(box)
    plain = call(box, "job", "echo hi")
    assert "how" not in plain and "clipped" not in plain
    got = call(box, "job", "seq 1 30000 | sed 's/^/line /'")
    assert got["state"] == "left" and got["clipped"] is True and got["ended"] == "well"
    assert "line 1\n" in got["page"] and got["page"].rstrip().endswith("line 30000")
    # a failed job's last line is on the page, and nowhere else it is told
    got = call(box, "job", "cat {pile}/garden.md; exit 5")
    assert got["how"] == "exited 5" and "frost" in got["page"]
    monkeypatch.setattr(runtime, "JOB_SECONDS", 2)
    got = call(box, "job", "echo started; sleep 30; echo never")
    assert got["ended"] == "badly" and "never" not in got["page"]
    assert "time" in got["how"].lower(), got
    rows = [json.loads(x) for x in (box / "record.jsonl").read_text().splitlines()]
    ran = [r for r in rows if r["kind"] == "ran"]
    assert len(ran) == 4 and "frost" not in json.dumps(ran)


def test_a_job_that_is_no_job_is_refused(box, monkeypatch):
    let_in(box)
    for bad in ("", "   ", None, 7, {"text": ""}, "x" * (runtime.JOB_MOST + 1)):
        got = call(box, "job", bad)
        assert (got["state"], got["code"]) == ("refused", "job_refused"), bad
    monkeypatch.setattr(runtime, "kart_python", lambda box: "/nonexistent/python")
    with pytest.raises(OSError):
        call(box, "job", "ls")
