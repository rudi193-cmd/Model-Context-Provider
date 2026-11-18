"""What a model's door lists besides its tools: the Model Context Protocol's
resources and prompts. Listing gives nothing a verb doesn't, and reading one
is that verb, decided, refused and written down as it always is."""

import json
import subprocess
import sys
from pathlib import Path

from test_leave import seal

import runtime

ROOT = Path(__file__).resolve().parents[1]
FROST = "when does the first frost come"
REPORT = "# Findings\n\nThe build breaks on Python 3.9.\n"


def mcp(box, cwd, *messages):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        input="".join(json.dumps(m) + "\n" for m in messages),
        capture_output=True, text=True, check=False, cwd=cwd,
    )  # fmt: skip
    return [json.loads(line) for line in run.stdout.splitlines()]


def ask(i, method, **params):
    return {"jsonrpc": "2.0", "id": i, "method": method, "params": params}


def uris(box, where):
    got = runtime.call(box, "resources", door="mcp", where=str(where))
    return [r["uri"] for r in got["resources"]]


def test_the_door_says_it_lists_resources_and_prompts(box, tmp_path):
    (init,) = mcp(box, tmp_path, ask(1, "initialize", protocolVersion="2025-06-18"))
    assert sorted(init["result"]["capabilities"]) == ["prompts", "resources", "tools"]


def test_the_list_names_reports_the_last_page_and_this_projects_shelf(box, tmp_path):
    assert uris(box, tmp_path) == [
        "provider://report/todo", "provider://report/on-this-day",
        "provider://report/coming-up", "provider://report/people",
        "provider://page/last",
    ]  # fmt: skip
    runtime.call(box, "shelf_add", {"name": "report.md", "text": REPORT},
                 door="mcp", where=str(tmp_path))  # fmt: skip
    assert uris(box, tmp_path)[-1] == "provider://shelf/report.md"
    assert "provider://shelf/report.md" not in uris(box, tmp_path / "other")


def test_listing_says_nothing_of_the_persons_files(box, tmp_path):
    (box.parent / "pile" / "chores.md").write_text("TODO: order the dahlia tubers.\n")
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    listed = json.dumps(runtime.call(box, "resources", door="mcp", where=str(tmp_path)))
    for word in ("dahlia", "frost", "October", "garden", "chores", "proposal:"):
        assert word not in listed


def test_reading_a_report_is_the_report_verb(box, tmp_path):
    (box.parent / "pile" / "chores.md").write_text("TODO: order the dahlia tubers.\n")
    got = runtime.call(box, "resource", "provider://report/todo", door="mcp")
    assert got["state"] == "waiting" and "dahlia" not in json.dumps(got)
    seal(box, got["seal"])
    got = runtime.call(box, "resource", "provider://report/todo", door="mcp")
    assert got["state"] == "left" and "dahlia" in got["page"]
    # written down once each time, as the report it was
    rows = [json.loads(ln) for ln in (runtime.state(box) / "sent.jsonl").read_text().splitlines()]  # fmt: skip
    assert [(r["verb"], r["state"]) for r in rows] == [("report", "waiting"), ("report", "left")]  # fmt: skip


def test_reading_the_last_page_is_leave_and_needs_a_seal(box):
    got = runtime.call(box, "resource", "provider://page/last", door="mcp")
    assert (got["state"], got["code"]) == ("refused", "not_sealed")
    runtime.read(box, FROST)
    seal(box, runtime.propose(box)["seal"])
    got = runtime.call(box, "resource", "provider://page/last", door="mcp")
    assert got["state"] == "left" and "late October" in got["page"]


def test_reading_from_the_shelf_is_take(box, tmp_path):
    runtime.call(box, "shelf_add", {"name": "report.md", "text": REPORT},
                 door="mcp", where=str(tmp_path))  # fmt: skip
    got = runtime.call(box, "resource", "provider://shelf/report.md",
                       door="mcp", where=str(tmp_path))  # fmt: skip
    assert got["says"] == REPORT
    got = runtime.call(box, "resource", "provider://shelf/../../sent.jsonl",
                       door="mcp", where=str(tmp_path))  # fmt: skip
    assert got["code"] == "not_on_shelf"


def test_nothing_else_can_be_read_this_way(box):
    for uri in ("provider://key/key", "provider://page/first", "file:///etc/passwd",
                "provider://waiting/all", "provider://", "", None, 7):  # fmt: skip
        got = runtime.call(box, "resource", uri, door="mcp")
        assert (got["state"], got["code"]) == ("refused", "no_resource"), uri


def test_only_a_models_door_lists_and_the_hosts_and_persons_do_not(box):
    for door in ("hook", "guard", "pipe"):
        for verb in ("resources", "resource", "prompts", "prompt"):
            assert runtime.call(box, verb, door=door)["code"] == "no_verb"


def test_what_is_listed_is_not_a_tool(box, tmp_path):
    tools, called = mcp(
        box, tmp_path,
        ask(1, "tools/list"),
        ask(2, "tools/call", name="resources", arguments={}),
    )  # fmt: skip
    names = [t["name"] for t in tools["result"]["tools"]]
    assert names == [t["name"] for t in runtime.call(box, "tools", door="mcp")["tools"]]
    assert not set(names) & set(runtime.LISTED["model"])
    assert called["result"]["isError"]
    assert called["result"]["structuredContent"]["code"] == "no_verb"


def test_the_prompts_tell_a_model_which_verbs_to_use_and_hold_nothing_else(box):
    listed = runtime.call(box, "prompts", door="mcp")["prompts"]
    assert [p["name"] for p in listed] == ["plate", "ask", "wrap_up", "question_me"]
    assert listed[1]["arguments"][0]["name"] == "question"
    plate = runtime.call(box, "prompt", {"name": "plate"}, door="mcp")
    assert plate["state"] == "prompt"
    assert '"todo"' in plate["text"] and '"coming-up"' in plate["text"]
    assert "Do not guess" in plate["text"]
    # every tool a prompt names is one the door has
    for name in runtime.PROMPTS:
        text = runtime.PROMPTS[name]["text"]
        for tool in (
            "report",
            "context",
            "answer",
            "propose",
            "shelf_list",
            "shelf_add",
        ):
            if f"the {tool} tool" in text:
                assert tool in runtime.VERBS["model"]
        assert "seal tool" not in text


def test_the_ask_prompt_carries_the_persons_question_or_asks_them_for_it(box):
    got = runtime.call(box, "prompt", {"name": "ask", "arguments": {"question": FROST}},
                       door="mcp")  # fmt: skip
    assert got["text"].startswith(f"The person asks their own files: {FROST}\n\n")
    assert "Use the context tool" in got["text"] and "{question}" not in got["text"]
    # run with nothing after it (seen confusing, 2026-11-17): it asks, then goes on
    for bare in ({"name": "ask"}, {"name": "ask", "arguments": {"question": "  "}},
                 {"name": "ask", "arguments": None}):  # fmt: skip
        got = runtime.call(box, "prompt", bare, door="mcp")
        assert got["state"] == "prompt"
        assert "Ask them what the question is" in got["text"]
        assert "wait for their answer" in got["text"]
        assert "Use the context tool" in got["text"] and "{question}" not in got["text"]
    for bad in ({"name": "nope"}, None):
        assert runtime.call(box, "prompt", bad, door="mcp")["code"] == "no_prompt"


def test_each_prompt_says_in_its_menu_line_what_to_type_and_what_comes_back(box):
    said = {p["name"]: p["description"]
            for p in runtime.call(box, "prompts", door="mcp")["prompts"]}  # fmt: skip
    for name in ("plate", "wrap_up"):
        assert "nothing to type after it" in said[name]
    assert "type your question when asked" in said["ask"]
    for line in said.values():
        assert "You get" in line or "tells you" in line  # what comes back
    (arg,) = runtime.PROMPTS["ask"]["arguments"]
    assert arg["required"] is False


def test_over_the_wire_lists_reads_and_prompts(box, tmp_path):
    runtime.call(box, "shelf_add", {"name": "report.md", "text": REPORT},
                 door="mcp", where=str(tmp_path))  # fmt: skip
    listed, read, bad, prompts, got, none, templates = mcp(
        box, tmp_path,
        ask(1, "resources/list"),
        ask(2, "resources/read", uri="provider://shelf/report.md"),
        ask(3, "resources/read", uri="provider://key/key"),
        ask(4, "prompts/list"),
        ask(5, "prompts/get", name="ask", arguments={"question": FROST}),
        ask(6, "prompts/get", name="nope"),
        ask(7, "resources/templates/list"),
    )  # fmt: skip
    assert listed["result"]["resources"][-1]["uri"] == "provider://shelf/report.md"
    assert read["result"]["contents"] == [
        {"uri": "provider://shelf/report.md", "mimeType": "text/plain", "text": REPORT}
    ]
    assert (
        bad["error"]["code"] == -32002 and "isn't something" in bad["error"]["message"]
    )
    assert [p["name"] for p in prompts["result"]["prompts"]] == [
        "plate",
        "ask",
        "wrap_up",
        "question_me",
    ]
    (said,) = got["result"]["messages"]
    assert said["role"] == "user" and FROST in said["content"]["text"]
    assert none["error"]["code"] == -32602
    assert templates["result"] == {"resourceTemplates": []}


def test_a_resource_told_only_a_state_is_read_as_that_state(box, tmp_path):
    (box.parent / "pile" / "chores.md").write_text("TODO: order the dahlia tubers.\n")
    (read,) = mcp(box, tmp_path, ask(1, "resources/read", uri="provider://report/todo"))
    (content,) = read["result"]["contents"]
    told = json.loads(content["text"])
    assert content["mimeType"] == "application/json"
    assert told["state"] == "waiting" and "dahlia" not in content["text"]
