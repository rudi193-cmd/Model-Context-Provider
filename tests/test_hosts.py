"""hosts.py: Willow's hosts table, pointed at doors/mcp.py, with optional write."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hosts  # noqa: E402
import runtime  # noqa: E402


def run(*argv):
    p = subprocess.run(
        [sys.executable, str(ROOT / "hosts.py"), *map(str, argv)],
        capture_output=True,
        text=True,
        check=False,
    )
    return p.returncode, p.stdout + p.stderr


def test_list_names_every_host():
    code, out = run("list")
    assert code == 0
    for name in hosts.HOSTS:
        assert name in out


def test_show_cursor_is_mcp_json_with_willow_env(box):
    code, out = run("show", "cursor", "--box", box)
    assert code == 0, out
    doc = json.loads(out.split("Add this to", 1)[1].split(":\n\n", 1)[1])
    entry = doc["mcpServers"]["model-context-provider"]
    assert entry["command"] == sys.executable
    assert entry["args"] == [
        str(ROOT / "doors" / "mcp.py"),
        "--box",
        str(box.resolve()),
    ]
    assert entry["env"] == {"WILLOW": str(runtime.WILLOW)}


def test_every_host_shape_parses(box):
    for name in hosts.HOSTS:
        for where, kind, value in hosts.places(name, box, sys.executable):
            assert where
            if kind == "json":
                json.dumps(value)
            else:
                assert "mcp_servers.model-context-provider" in value
                assert "WILLOW" in value


def test_show_refuses_claude_code_and_unknown(box):
    code, out = run("show", "claude-code", "--box", box)
    assert code == 2 and "set_up.py" in out
    code, out = run("show", "nope", "--box", box)
    assert code == 2 and "no host called nope" in out


def test_show_writes_nothing(box, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    run("show", "cursor", "--box", box)
    assert list((tmp_path / "home").iterdir()) == []


def test_write_cursor_merges_mcp_and_hooks(box, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    code, out = run("write", "cursor", "--box", box)
    assert code == 0, out
    mcp = json.loads((home / ".cursor" / "mcp.json").read_text())
    assert "model-context-provider" in mcp["mcpServers"]
    hooks = json.loads((home / ".cursor" / "hooks.json").read_text())
    assert "sessionStart" in hooks["hooks"] and "sessionEnd" in hooks["hooks"]
    assert "afterMCPExecution" in hooks["hooks"]
    code2, out2 = run("write", "cursor", "--box", box)
    assert code2 == 0 and "already set" in out2


def test_write_refuses_a_different_entry(box, tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".cursor").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    (home / ".cursor" / "mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "model-context-provider": {
                        "command": "other",
                        "args": [],
                        "env": {},
                    }
                }
            }
        )
    )
    code, out = run("write", "cursor", "--box", box)
    assert code == 2 and "refused" in out
