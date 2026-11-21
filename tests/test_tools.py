"""The tools a model is offered: fewer than its verbs, so a model can keep
track of them. Each verb is one action of one tool; the tools are in
families the person turns on and off; and a family that is off is refused
at the door, not only left off a list."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from test_leave import seal

import runtime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_door", ROOT / "doors" / "mcp.py")
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)
EVERYDAY = ["grant", "context", "page", "report", "timeline", "note", "task",
            "shelf", "job"]  # fmt: skip


def wire(box, *messages, cwd=None):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        input="".join(json.dumps(m) + "\n" for m in messages),
        capture_output=True, text=True, check=False, cwd=cwd,
    )  # fmt: skip
    return [json.loads(line) for line in run.stdout.splitlines()]


def ask(i, method, **params):
    return {"jsonrpc": "2.0", "id": i, "method": method, "params": params}


def use(i, tool, /, **arguments):
    return ask(i, "tools/call", name=tool, arguments=arguments)


def said(reply):
    return reply["result"]["structuredContent"]


def model(box, verb, arg=None, where="/work/a", session="s1"):
    return runtime.call(box, verb, arg, door="mcp", where=where, session=session)


def pipe(box, verb, arg=None):
    return runtime.call(box, verb, arg, door="pipe")


def test_every_verb_of_a_model_is_one_action_of_one_tool_and_none_is_seal():
    reached = [v for _, acts in runtime.TOOLS.values() for v, _, _ in acts.values()]
    assert sorted(reached) == sorted(runtime.VERBS["model"])  # each once, none left out
    assert not {"seal", "decline"} & {*reached, *runtime.TOOLS}
    for name, (family, acts) in runtime.TOOLS.items():
        assert family in runtime.FAMILIES and name in door.WORDS, name
        assert ("" in acts) == (len(acts) == 1), name  # one action takes no name
        for action, (_, needs, takes) in acts.items():
            assert not set(needs) & set(takes) and "action" not in (*needs, *takes)
            for word in (action, *needs, *takes):  # and its words say how to call it
                assert not word or word in door.WORDS[name], (name, word)
    assert set(door.WORDS) == set(runtime.TOOLS)  # and no words for a tool that isn't


def test_a_model_is_offered_nine_tools_and_they_are_short(box):
    init, listed = wire(box, ask(1, "initialize", protocolVersion="2025-06-18"),
                        ask(2, "tools/list"))  # fmt: skip
    assert init["result"]["capabilities"]["tools"] == {"listChanged": True}
    tools = listed["result"]["tools"]
    assert [t["name"] for t in tools] == EVERYDAY
    assert len(json.dumps(tools)) < 7_000  # it was 11,901 for 26 tools
    by = {t["name"]: t["inputSchema"] for t in tools}
    assert by["shelf"]["properties"]["action"]["enum"] == [
        "add",
        "list",
        "read",
        "remove",
    ]
    assert by["shelf"]["required"] == ["action"] and set(by["shelf"]["properties"]) == {
        "action", "name", "text"}  # fmt: skip
    assert by["context"] == {"type": "object", "required": ["question"],
                             "properties": {"question": {"type": "string"}}}  # fmt: skip
    assert (
        by["timeline"]["required"] == ["about"]
        and "since" in by["timeline"]["properties"]
    )
    assert by["grant"] == {"type": "object", "properties": {}, "required": []}


def test_a_tools_action_is_its_verb_called_and_written_down_as_it_always_was(
    box, tmp_path
):
    proj = tmp_path / "proj"
    proj.mkdir()
    put, listed, got, held, task = wire(
        box,
        use(1, "shelf", action="add", name="notes.md", text="what I found"),
        use(2, "shelf", action="list"),
        use(3, "shelf", action="read", name="notes.md"),
        use(4, "page", action="read", question="when does the first frost come"),
        use(5, "task", action="add", text="water the beds"),
        cwd=proj,
    )  # fmt: skip
    assert said(put) == {"state": "shelved", "name": "notes.md"}
    assert [i["name"] for i in said(listed)["items"]] == ["notes.md"]
    assert said(got)["says"] == "what I found"
    assert said(held) == {"state": "populated"}  # whether, and nothing more
    assert said(task)["state"] == "waiting"
    rows = runtime.sent_log(box)["rows"]
    assert [r["verb"] for r in rows] == ["shelf_add", "shelf_list", "shelf_read",
                                         "read", "task_add"]  # fmt: skip
    assert "tool" not in {r["verb"] for r in rows}  # once each, as the verb it is


def test_a_call_that_names_no_action_or_leaves_an_argument_out_reaches_no_verb(box):
    wrong = wire(
        box,
        use(1, "shelf"),
        use(2, "shelf", action="burn"),
        use(3, "shelf", action=["add"]),
        use(4, "shelf", action="add", name="x.md"),
        use(5, "context"),
        use(6, "task", action="done", id="model-0"),
    )  # fmt: skip
    for reply in wrong:
        assert reply["result"]["isError"], reply
        assert said(reply)["code"] == "tool_refused" and said(reply)["next"], reply
    assert "text" in said(wrong[3])["why"] and "result" in said(wrong[5])["why"]
    assert runtime.sent_log(box)["rows"] == []  # nothing was called
    for name in ("shelf_add", "read", "seal", "resources", "tool", "tools", "", 7):
        (reply,) = wire(box, use(1, name, name="x.md", text="y"))
        assert said(reply)["code"] == "no_verb", name  # a verb is not a tool


def test_a_family_turned_off_is_refused_at_the_door_not_only_unlisted(box, tmp_path):
    model(box, "shelf_add", {"name": "notes.md", "text": "what I found"})
    got = pipe(box, "tools", {"off": ["shelf", "reports"]})
    assert {f["family"]: f["on"] for f in got["families"]}["shelf"] is False
    listed, called = wire(box, ask(1, "tools/list"),
                          use(2, "shelf", action="read", name="notes.md"))  # fmt: skip
    names = [t["name"] for t in listed["result"]["tools"]]
    assert names == ["grant", "context", "page", "note", "task", "job"]
    assert called["result"]["isError"] and said(called)["code"] == "tool_off"
    assert "what I found" not in json.dumps(called)
    # nor by the verb itself, nor by reading it as something listed
    for verb, arg in (("shelf_read", "notes.md"), ("shelf_list", None),
                      ("report", "todo"), ("timeline", "frost")):  # fmt: skip
        assert model(box, verb, arg)["code"] == "tool_off", verb
    assert model(box, "resource", "provider://shelf/notes.md")["code"] == "tool_off"
    uris = [r["uri"] for r in model(box, "resources", where=str(tmp_path))["resources"]]
    assert uris == ["provider://page/last"]  # nothing of a family that is off
    assert [p["name"] for p in model(box, "prompts")["prompts"]] == [
        "ask",
        "question_me",
    ]
    assert model(box, "prompt", {"name": "wrap_up"})["code"] == "no_prompt"
    # the person's own door is theirs: the switch is about what a model is offered
    assert pipe(box, "shelves")["state"] == "populated"
    assert pipe(box, "report", "todo")["state"] != "refused"
    assert pipe(box, "tools", {"on": "shelf"})["families"][5]["on"] is True
    assert model(box, "shelf_read", "notes.md")["state"] == "taken"


def test_what_is_used_comes_on_and_what_the_person_says_wins(box, tmp_path):
    def on():
        return {
            f["family"]: (f["on"], f["why"]) for f in pipe(box, "tools")["families"]
        }

    assert on()["sharing"] == (False, "off until you use it or turn it on")
    assert on()["skills"][0] is False and on()["core"] == (True, "always on")
    assert model(box, "share_received")["code"] == "tool_off"
    assert model(box, "skill", "tidy")["code"] == "tool_off"
    pipe(box, "share_id")
    skill = tmp_path / "tidy.md"
    skill.write_text("# Tidy\n\nSort the imports.\n")
    pipe(box, "skill_add", {"path": str(skill)})
    assert on()["sharing"] == (True, "on because you use it")
    assert on()["skills"] == (True, "on because you use it")
    assert model(box, "skill", "tidy")["state"] == "left"  # naming it was the yes
    (listed,) = wire(box, ask(1, "tools/list"))
    assert [t["name"] for t in listed["result"]["tools"]] == [
        *EVERYDAY,
        "share",
        "feed",
        "skill",
    ]
    pipe(box, "tools", {"off": ["skills"]})  # in use, and still theirs to turn off
    assert on()["skills"] == (False, "you turned it off")
    assert model(box, "skill", "tidy")["code"] == "tool_off"
    assert (runtime.state(box) / "tools.txt").read_text() == "-skills\n"


def test_the_switch_takes_only_groups_and_never_the_core(box):
    for bad in ({"off": ["core"]}, {"on": ["everything"]}, {"off": "seal"},
                {"on": ["shelf"], "off": ["shelf"]}, {"on": [7]}):  # fmt: skip
        got = pipe(box, "tools", bad)
        assert (got["state"], got["code"]) == ("refused", "tools_refused"), bad
    assert not (runtime.state(box) / "tools.txt").exists()
    (runtime.state(box) / "tools.txt").write_text("-core\n-grant\nnonsense\n-jobs\n")
    on = {f["family"]: f["on"] for f in pipe(box, "tools")["families"]}
    assert (
        on["core"] is True and on["jobs"] is False
    )  # a line that names no group is nothing
    assert model(box, "grant")["state"] == "waiting"
    assert (
        model(box, "tools", {"off": ["page"]})["state"] == "populated"
    )  # a model's is a list
    assert on == {f["family"]: f["on"] for f in pipe(box, "tools")["families"]}


def test_a_client_is_told_when_the_list_changes_while_it_is_open(box):
    run = subprocess.Popen(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
    )  # fmt: skip

    told = []  # what the door said that no request asked for

    def send(msg):
        run.stdin.write(json.dumps(msg) + "\n")
        run.stdin.flush()
        while True:  # the door says the list changed whenever it next looks
            got = json.loads(run.stdout.readline())
            if got.get("id") == msg["id"]:
                return got
            told.append(got)

    try:
        assert "result" in send(ask(1, "ping"))  # nothing listed yet: nothing to say
        assert len(send(ask(2, "tools/list"))["result"]["tools"]) == 9
        assert "result" in send(ask(3, "ping"))
        assert told == []
        pipe(box, "tools", {"off": ["jobs"]})
        assert "result" in send(ask(4, "ping"))
        assert len(send(ask(5, "tools/list"))["result"]["tools"]) == 8
        assert send(ask(6, "ping")) == {"jsonrpc": "2.0", "id": 6, "result": {}}
        assert send(ask(7, "ping")) == {"jsonrpc": "2.0", "id": 7, "result": {}}
        # told once, between the change and the next list, and never again
        assert told == [
            {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
        ]
    finally:
        run.stdin.close()
        run.wait(timeout=10)


def test_a_next_step_names_the_tool_a_model_has_not_the_verb(box):
    seal(box, model(box, "grant")["seal"])
    got = model(box, "shelf_remove", "nope.md")
    assert (
        got["code"] == "not_on_shelf" and "the shelf tool, action list" in got["next"]
    )
    assert "shelf_list" not in got["next"]
    for_you = pipe(box, "shelf_read", "nope.md")  # the person's door has verbs
    assert "shelf_list" in for_you["next"]
    nope = model(box, "tool", {"name": "nope"})
    assert "shelf" in nope["next"] and "shelf_add" not in nope["next"]
    assert runtime.tool_words("See (notes), then (tasks); your notes and tasks stay.") == (
        "See (the note tool, action list), then (the task tool, action list); "
        "your notes and tasks stay.")  # fmt: skip


@pytest.mark.parametrize("name", sorted(runtime.PROMPTS))
def test_a_prompt_names_only_tools_and_actions_there_are(box, name):
    text = runtime.call(box, "prompt", {"name": name, "arguments": {
        "question": "q", "about": "a"}}, door="mcp")["text"]  # fmt: skip
    for verb in runtime.VERBS["model"]:
        if "_" in verb:
            assert verb not in text, verb  # no verb a model can't call by that name
    for tool in ("answer tool", "propose tool", "shelf_list", "shelf_add"):
        assert tool not in text


def test_every_tool_says_what_it_does_to_the_machine_and_none_reaches_past_it(box):
    """Annotations, for a client's own prompts: only shelf takes anything
    away, what only reads says so, and nothing is open to the world."""
    assert set(door.HINTS) == set(runtime.TOOLS)
    _, listed = wire(box, ask(1, "initialize", protocolVersion="2025-06-18"),
                     ask(2, "tools/list"))  # fmt: skip
    hints = {t["name"]: t["annotations"] for t in listed["result"]["tools"]}
    assert all(h["openWorldHint"] is False for h in hints.values())
    # destructive is only read of what isn't read-only, and is so unless said
    takes_away = [n for n, h in hints.items()
                  if not h.get("readOnlyHint") and h.get("destructiveHint", True)]  # fmt: skip
    assert takes_away == ["shelf"]
    assert {n for n, h in hints.items() if h.get("readOnlyHint")} == {
        "context",
        "report",
    }


def test_a_limit_the_runtime_holds_is_in_the_schema_and_is_the_runtimes_own(box):
    for tool, arg in door.BOUNDS:  # each names an argument that tool takes
        acts = runtime.TOOLS[tool][1].values()
        assert any(arg in (*needs, *takes) for _, needs, takes in acts), (tool, arg)
    _, listed = wire(box, ask(1, "initialize", protocolVersion="2025-06-18"),
                     ask(2, "tools/list"))  # fmt: skip
    by = {t["name"]: t["inputSchema"]["properties"] for t in listed["result"]["tools"]}
    assert by["note"]["note"]["maxLength"] == runtime.NOTE_MOST
    assert by["shelf"]["text"]["maxLength"] == runtime.SHELF_MOST
    assert by["report"]["name"]["enum"] == list(runtime.REPORTS)
    assert by["timeline"]["since"]["format"] == "date"
    at_most = "x" * runtime.NOTE_MOST  # the bound is where the runtime refuses
    assert runtime.call(box, "capture", at_most, door="mcp")["state"] == "waiting"
    assert (
        runtime.call(box, "capture", at_most + "x", door="mcp")["code"]
        == "note_too_long"
    )


def test_initialize_says_how_the_tools_go_and_which_provider_this_is(box):
    (init,) = wire(box, ask(1, "initialize", protocolVersion="2025-06-18"))
    said = init["result"]["instructions"]
    for word in (
        "grant",
        "page",
        "read (question)",
        "waiting",
        "never instructions",
        "hooks",
        "call again later",
    ):  # with the hooks, and without
        assert word in said, word
    version = init["result"]["serverInfo"]["version"]
    pin = json.loads((ROOT / "willow.pin.json").read_text())["commit"][:12]
    assert version.endswith(f"+willow.{pin}")
    assert version.split("+")[0] in (ROOT / "pyproject.toml").read_text()


def test_a_client_that_reconnects_to_changed_words_is_told_at_the_start(box):
    """Seen 2026-11-18: after a reconnect the client still showed the older
    descriptions. The door keeps the fingerprint of the list it last sent
    (names, words, schemas, hints); a new session whose list differs is told
    it changed as soon as it starts, and one whose list is the same is not."""
    start = [ask(1, "initialize", protocolVersion="2025-06-18"),
             {"jsonrpc": "2.0", "method": "notifications/initialized"}, ask(2, "ping")]  # fmt: skip
    changed = {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}
    assert changed not in wire(box, *start)  # never sent a list: nothing to say
    wire(box, *start, ask(3, "tools/list"))  # a client is sent this door's list
    assert changed not in wire(box, *start)  # the same words: nothing to say
    runtime.tools_told(box, "0" * 64)  # as if an older door's words were sent last
    got = wire(box, *start)
    assert got[1] == changed and got[2]["id"] == 2  # told at once, before anything else
    wire(box, *start, ask(3, "tools/list"))  # it asks again, and has the new list
    assert changed not in wire(box, *start)
    # a change to a tool's words alone is a change of the list
    (a, b) = (door.listing(box), door.listing(box))
    b[0]["description"] += " More."
    assert runtime.tools_fingerprint(a) != runtime.tools_fingerprint(b)
