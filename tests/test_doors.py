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


def test_mcp_lists_the_runtimes_verbs_and_no_seal(box):
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
    assert sorted(names) == sorted(runtime.VERBS)
    assert "seal" not in names


def test_both_doors_get_the_same_answer_from_the_one_runtime(box, tmp_path):
    q = "when does the first frost come"
    by_pipe = pipe(box, {"read": q})[0]
    by_mcp = mcp(box, tool(1, "read", question=q))[0]["result"]["structuredContent"]
    by_pipe.pop("verb")
    assert by_mcp == by_pipe


def test_mcp_cannot_leave_unsealed_any_more_than_the_pipe(box, tmp_path):
    out = tmp_path / "out.md"
    got = mcp(
        box,
        tool(1, "read", question="when does the first frost come"),
        tool(2, "propose"),
        tool(3, "leave", to=str(out)),
    )
    assert [g["result"]["isError"] for g in got] == [False, False, True]
    assert not out.exists()
