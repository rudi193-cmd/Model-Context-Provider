"""Line 2 held as a test: a door imports the runtime and nothing that
decides, so no door can serve, seal or let anything leave by itself."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

import runtime

ROOT = Path(__file__).resolve().parents[1]
DOORS = sorted(p for p in (ROOT / "doors").glob("*.py") if p.name != "__init__.py")
ALLOWED = {"__future__", "json", "sys", "pathlib", "runtime"}


@pytest.mark.parametrize("door", DOORS, ids=lambda p: p.name)
def test_a_door_imports_only_the_runtime(door):
    tree = ast.parse(door.read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert names <= ALLOWED, names - ALLOWED


def test_what_carries_out_a_seal_is_no_door_and_the_runtime_imports_neither():
    for name in ("seal_page.py", "seal_prompt.py"):
        assert (ROOT / name).is_file() and not (ROOT / "doors" / name).exists()
    tree = ast.parse((ROOT / "runtime.py").read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
    assert not names & {"seal_page", "seal_prompt"}
    # the runtime runs the kernel's seal and decline nowhere
    text = (ROOT / "runtime.py").read_text()
    assert '"kernel.py", "seal"' not in text and '"kernel.py", "decline"' not in text


@pytest.mark.parametrize("door", DOORS, ids=lambda p: p.name)
def test_a_door_never_calls_willow_itself(door):
    assert "runtime.willow" not in door.read_text()


def pipe(box, *requests):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "pipe.py"), "--box", str(box)],
        input="".join(json.dumps(r) + "\n" for r in requests),
        capture_output=True,
        text=True,
        check=False,
    )
    return [json.loads(line) for line in run.stdout.splitlines()]


def test_the_pipe_reads_proposes_and_refuses_to_leave_unsealed(box, tmp_path):
    out = tmp_path / "out.md"
    got = pipe(
        box,
        {"read": "when does the first frost come"},
        {"propose": True},
        {"leave": str(out)},
    )
    assert [g["state"] for g in got] == ["populated", "waiting", "refused"]
    assert not out.exists()


def test_the_pipe_refuses_a_verb_it_has_not_got(box):
    got = pipe(box, {"seal": "proposal:x"})
    assert got[0]["state"] == "refused"


def mcp(box, *messages):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        input="".join(json.dumps(m) + "\n" for m in messages),
        capture_output=True,
        text=True,
        check=False,
    )
    return [json.loads(line) for line in run.stdout.splitlines()]


def tool(i, name, **arguments):
    return {
        "jsonrpc": "2.0",
        "id": i,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }


def test_mcp_lists_the_tools_the_runtime_offers_and_no_seal(box):
    (init, listed) = mcp(
        box,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18"},
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    assert init["result"]["protocolVersion"] == "2025-06-18"
    names = [t["name"] for t in listed["result"]["tools"]]
    offered = runtime.call(box, "tools", door="mcp")["tools"]
    assert names == [t["name"] for t in offered]  # the runtime's, in its order
    assert "seal" not in names


def test_a_model_learns_whether_the_files_hold_it_never_what_they_say(box):
    q = "when does the first frost come"
    assert pipe(box, {"read": q})[0]["served"]  # the person's door: passages
    got = mcp(box, tool(1, "page", action="read", question=q))[0]["result"][
        "structuredContent"
    ]
    assert got == {"state": "populated"}  # the model's: no text, place or count


def test_a_sealed_scope_is_the_one_page_the_model_gets(box):
    from test_leave import seal

    q = "when does the first frost come"
    mcp(box, tool(1, "page", action="read", question=q))
    seal(
        box,
        mcp(box, tool(2, "page", action="propose"))[0]["result"]["structuredContent"][
            "seal"
        ],
    )
    got = mcp(box, tool(3, "page", action="leave"))[0]["result"]
    assert not got["isError"]
    assert "first frost comes in late October" in got["structuredContent"]["page"]
    assert "MOT" not in got["structuredContent"]["page"]


def test_a_door_the_runtime_does_not_know_is_treated_as_facing_a_model(box):
    got = runtime.call(box, "read", "when does the first frost come", door="new")
    assert got == {"state": "populated"}


def test_mcp_cannot_leave_unsealed_any_more_than_the_pipe(box):
    got = mcp(
        box,
        tool(1, "page", action="read", question="when does the first frost come"),
        tool(2, "page", action="propose"),
        tool(3, "page", action="leave"),
    )
    assert [g["result"]["isError"] for g in got] == [False, False, True]
