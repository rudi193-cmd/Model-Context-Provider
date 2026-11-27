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
    assert entry["env"] == {"WILLOW": str(runtime.WILLOW_SOURCE)}


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
    # the guard door before a tool, a shell command and a read, failing closed
    for event in ("preToolUse", "beforeShellExecution", "beforeReadFile"):
        (gate,) = hooks["hooks"][event]
        assert "doors/guard.py" in gate["command"] and gate["failClosed"] is True
    assert hooks["hooks"]["preToolUse"][0]["matcher"] == "Shell|Read|Write|Delete|Grep"
    code2, out2 = run("write", "cursor", "--box", box)
    assert code2 == 0 and "already set" in out2
    again = json.loads((home / ".cursor" / "hooks.json").read_text())
    assert all(len(again["hooks"][e]) == 1 for e in ("preToolUse", "beforeReadFile"))


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


def test_the_assistants_codebase_memory_mcp_writes_to_are_here_in_its_shapes(box):
    """Each assistant added from codebase-memory-mcp's installer: its home
    file, the servers under mcpServers, and the one field some read."""
    assert set(hosts.MORE) == set(hosts.FOUND_BY)
    fixed = {"factory-droid": ("type", "stdio"), "gitlab-duo": ("type", "stdio"),
             "rovo-dev": ("transport", "stdio")}  # fmt: skip
    for name in hosts.MORE:
        found = hosts.places(name, box, sys.executable)
        for where, kind, value in found:
            assert kind == "json" and where.startswith(("~/", "Cline in an editor"))
            entry = value["mcpServers"]["model-context-provider"]
            assert entry["command"] == sys.executable
            assert entry["env"] == {"WILLOW": str(runtime.WILLOW_SOURCE)}
            if name in fixed:
                assert entry[fixed[name][0]] == fixed[name][1]
            else:
                assert set(entry) == {"command", "args", "env"}
        # found by the folder its settings sit in; Antigravity by its CLI's,
        # as codebase-memory-mcp finds it (cli.c:1497)
        mark = hosts.FOUND_BY[name]
        assert mark in hosts.MORE[name][1] or (name, mark) == (
            "antigravity",
            ".gemini/antigravity-cli",
        )
    assert len(hosts.places("cline", box, sys.executable)) == 2


def test_write_all_makes_nothing_for_an_assistant_that_isnt_here(
    box, tmp_path, monkeypatch
):
    import set_up

    home = tmp_path / "home"
    (home / ".qoder").mkdir(parents=True)  # Qoder is here; Kiro is not
    monkeypatch.setenv("HOME", str(home))
    set_up.write(box, "all")
    qoder = json.loads((home / ".qoder" / "settings.json").read_text())
    assert "model-context-provider" in qoder["mcpServers"]
    assert not (home / ".kiro").exists() and not (home / ".tabnine").exists()
    assert not (home / ".aws").exists()  # not even the folder above Amazon Q's
    assert hosts.here_now("cursor")  # the hosts this began with, as before
    code, out = run("write", "kiro", "--box", box)  # asked by name, it writes
    assert code == 0 and "wrote" in out


def test_a_shared_settings_file_keeps_what_it_had(box, tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".qwen").mkdir(parents=True)
    (home / ".qwen" / "settings.json").write_text(
        json.dumps({"theme": "dark", "mcpServers": {"other": {"command": "x"}}})
    )
    monkeypatch.setenv("HOME", str(home))
    code, out = run("write", "qwen-code", "--box", box)
    assert code == 0, out
    got = json.loads((home / ".qwen" / "settings.json").read_text())
    assert got["theme"] == "dark" and set(got["mcpServers"]) == {
        "other",
        "model-context-provider",
    }
    (home / ".qwen" / "settings.json").write_text('{ // a comment\n "theme": 1 }')
    code, out = run("write", "qwen-code", "--box", box)
    assert "refused" in out  # JSON with comments isn't parsed, so never written
