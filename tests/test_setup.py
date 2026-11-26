"""Setup checks, prints what to paste, and with --write finishes a client."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import runtime  # noqa: E402
import set_up as setup  # noqa: E402


def run(*argv):
    p = subprocess.run([sys.executable, str(ROOT / "set_up.py"), *map(str, argv)],
                       capture_output=True, text=True, check=False)  # fmt: skip
    return p.returncode, p.stdout + p.stderr


def a_stack(tmp_path, box, n=1):
    """Willow's UI's layout: STACK/mine/FOLDER/box."""
    stack = tmp_path / "stack"
    for i in range(n):
        (stack / "mine" / f"folder{i}").mkdir(parents=True)
        (stack / "mine" / f"folder{i}" / "box").symlink_to(box)
    return stack


def test_one_record_under_a_stack_is_found_checked_and_printed(box, tmp_path):
    code, out = run("--stack", a_stack(tmp_path, box))
    assert code == 0, out
    assert (
        "ok  your record" in out
        and "claude mcp add --scope user model-context-provider -e WILLOW=" in out
    )


def test_several_records_are_listed_to_choose_from(box, tmp_path):
    code, out = run("--stack", a_stack(tmp_path, box, 2))
    assert code == 42 and out.count("python set_up.py --box") == 2


def test_no_record_yet_says_to_press_start(tmp_path):
    (tmp_path / "stack" / "mine").mkdir(parents=True)
    code, out = run("--stack", tmp_path / "stack")
    assert code == 42 and "Start it" in out


def test_a_broken_record_stops_setup_before_anything_is_printed(box):
    (box / "record.jsonl").write_text("not a record\n")
    code, out = run("--box", box)
    assert code == 2 and "NO  your record" in out and "claude mcp add" not in out


def test_naming_a_model_off_this_machine_is_refused_and_nothing_written(box):
    code, _ = run("--box", box, "--model", "https://far.example/v1", "m")
    assert code == 2 and not (runtime.state(box) / "model.json").exists()


def test_a_model_on_another_machine_of_theirs_is_told_to_tunnel_it(box):
    code, out = run("--box", box, "--model", "http://192.168.1.20:11434/v1", "m")
    assert code == 2 and not (runtime.state(box) / "model.json").exists()
    assert "tunnel it" in out and "ExitOnForwardFailure=yes" in out
    # the port it names is one nothing else uses, and naming it is allowed
    assert "-L 21434:localhost:11434" in out
    code, _ = run("--box", box, "--model", "http://127.0.0.1:21434/v1", "m")
    assert code == 0


def test_naming_a_model_on_this_machine_writes_model_json(box):
    code, out = run("--box", box, "--model", "http://127.0.0.1:11434/v1", "gemma3:4b")
    assert code == 0, out
    doc = json.loads((runtime.state(box) / "model.json").read_text())
    assert doc == {"url": "http://127.0.0.1:11434/v1", "model": "gemma3:4b"}


def test_what_it_says_to_paste_starts_a_door_that_answers(box):
    """Cursor's JSON, started exactly as Cursor would start it."""
    import hosts as hosts_mod

    entry = hosts_mod.places("cursor", box, sys.executable)[0][2]["mcpServers"][
        "model-context-provider"
    ]
    env = {**os.environ, **entry["env"]}
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]  # fmt: skip
    p = subprocess.run([entry["command"], *entry["args"]], env=env, check=False,
                       input="".join(json.dumps(m) + "\n" for m in msgs),
                       capture_output=True, text=True)  # fmt: skip
    listed = json.loads(p.stdout.splitlines()[1])["result"]["tools"]
    offered = runtime.call(box, "tools", door="mcp")["tools"]
    assert [t["name"] for t in listed] == [t["name"] for t in offered]


def test_paste_names_cursor_and_the_other_hosts(box):
    out = setup.paste(box)
    assert "### Cursor (`cursor`)" in out
    assert "~/.cursor/mcp.json" in out
    assert "--write cursor" in out
    for name in ("copilot", "codex-cli", "gemini-cli", "opencode", "windsurf", "zed"):
        assert f"`{name}`" in out


def test_setup_without_write_writes_nothing_of_the_clients(box, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    run("--box", box)
    assert list((tmp_path / "home").iterdir()) == []


def test_write_cursor_finishes_setup(box, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    code, out = run("--box", box, "--write", "cursor")
    assert code == 0, out
    assert (home / ".cursor" / "mcp.json").is_file()
    assert (home / ".cursor" / "hooks.json").is_file()
    assert "wrote" in out


def test_the_hooks_it_says_to_paste_include_the_session_door(box):
    text = setup.paste(box).split("2. The hooks")[1].split("\n\n3. Cursor")[0]
    hooks = json.loads(text[text.index("{") :])["hooks"]
    (start,) = hooks["SessionStart"][0]["hooks"]
    (end,) = hooks["SessionEnd"][0]["hooks"]
    assert "doors/session.py" in start["command"] and start["command"] == end["command"]
    assert end["timeout"] == 60
    assert "doors/hook.py" in hooks["UserPromptSubmit"][0]["hooks"][0]["command"]


def test_setup_says_so_when_willow_is_not_the_pinned_one(box, tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "PIN", tmp_path / "no-pin.json")
    rows = setup.check(box)
    assert rows[-1][0] == "Willow is the pinned one" and rows[-1][1] is False
    assert "your record" not in [r[0] for r in rows]
    monkeypatch.undo()
    assert ("Willow is the pinned one", True) in [r[:2] for r in setup.check(box)]


def test_write_command_saves_the_persons_door_and_never_writes_over_another(
    box, tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    code, out = run("--box", box, "--write", "command")
    assert code == 0, out
    saved = home / ".local" / "bin" / "provider"
    text = saved.read_text()
    assert text.startswith("#!/bin/sh\n") and saved.stat().st_mode & 0o111
    assert f"--box {box.resolve()}" in text and "doors/pipe.py" in text
    assert text.rstrip().endswith('"$@"')
    assert "isn't on your PATH yet" in out
    assert run("--box", box, "--write", "command")[0] == 0  # the same again is fine
    saved.write_text("#!/bin/sh\necho something else\n")
    code, out = run("--box", box, "--write", "command")
    assert code == 2 and "refused" in out
    assert saved.read_text() == "#!/bin/sh\necho something else\n"


def test_a_stack_without_the_starter_words_is_told_before_its_record_is_made(tmp_path):
    """Willow's UI ticks the starter list only when the stack holds it; a
    record made without one can be given one later, and is told how."""
    stack = tmp_path / "stack"
    (stack / "mine").mkdir(parents=True)
    (stack / "STACK.json").write_text(json.dumps({"addons": ["approved-only"]}))
    code, out = run("--stack", stack)
    assert code == 42 and "Start it" in out
    assert "Your stack has no starter-words" in out
    assert f"ui/assemble.py add starter-words --to {stack}" in out
    (stack / "STACK.json").write_text(json.dumps({"addons": ["starter-words"]}))
    assert "no starter-words" not in run("--stack", stack)[1]
    (stack / "STACK.json").unlink()  # no list to read: nothing guessed
    assert "no starter-words" not in run("--stack", stack)[1]


def test_a_record_with_no_words_is_said_so_and_setup_still_finishes(box):
    code, out = run("--box", box)
    assert code == 0, out
    assert "--  your words: none: this record was made with no words list" in out
    assert "ok  your words" not in out
    # and the two lines that give it one, the record's own path in each
    mine = box.parent / "my-words.txt"
    assert f"starter-words/starter.py copy --to {mine}" in out
    assert f"kernel.py words --box {box} --words {mine}" in out


def test_a_record_with_words_is_told_it_can_add_its_own(tmp_path):
    pile, words = tmp_path / "pile", tmp_path / "my-words.txt"
    pile.mkdir()
    (pile / "car.md").write_text("The MOT is due in March.\n")
    words.write_text("mot = inspection, test\n")
    words.chmod(0o600)
    b = tmp_path / "box"
    made = runtime.willow("kernel.py", "init", "--box", str(b), "--pile", str(pile),
                          "--key", str(tmp_path / "k.key"), "--words", str(words))  # fmt: skip
    assert made.returncode == 0, made.stderr
    code, out = run("--box", b)
    assert code == 0 and f"ok  your words: in use: {words}" in out
    assert "add a line of your own to it any time" in out


def test_the_hooks_are_written_for_managed_settings_with_the_line_that_installs_them(
    box, tmp_path, monkeypatch
):
    """In ~/.claude/settings.json an assistant allowed to edit ~/.claude can
    switch the guard door off. Claude Code's managed settings are an
    administrator's: setup writes the same hooks as a file of their own and
    prints the line that installs them, and never writes there itself."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    managed = tmp_path / "etc-claude-code"
    monkeypatch.setattr(setup, "managed_dir", lambda: managed)
    lines = setup.write(box, "managed")
    made = home / ".claude" / "model-context-provider-managed.json"
    assert json.loads(made.read_text()) == setup.managed(box)
    to = managed / "managed-settings.d" / setup.MANAGED_NAME
    assert any(
        str(to) in ln and ln.strip().startswith(("sudo", "copy")) for ln in lines
    )
    assert not managed.exists()  # the administrator's to write, not setup's


def test_setup_says_where_the_guard_door_is_and_whether_it_can_be_switched_off(
    box, tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    managed = tmp_path / "etc-claude-code"
    monkeypatch.setattr(setup, "managed_dir", lambda: managed)

    def row():
        return next(r for r in setup.check(box) if r[0] == "the guard door")

    assert row()[1] is None and "not in Claude Code's settings" in row()[2]
    setup.write(box, "claude-code")  # the person's own settings
    assert (
        row()[1] is None
        and "could switch it off" in row()[2]
        and "--write managed" in row()[2]
    )
    (managed / "managed-settings.d").mkdir(parents=True)
    made = home / ".claude" / "model-context-provider-managed.json"
    setup.write(box, "managed")
    (managed / "managed-settings.d" / setup.MANAGED_NAME).write_text(made.read_text())
    assert row()[1] is True and "can't switch it off" in row()[2]
    # another record's guard door there is not this one's
    other = tmp_path / "other-box"
    assert setup.guard_where(other) == ""


def test_setup_says_who_can_read_the_key_without_opening_it(box, tmp_path, monkeypatch):
    """The account setup runs as is the one any assistant runs as. A key it
    can read is one a script the assistant writes can read, whatever a guard
    says; only a key in an account of its own is out of reach. Told from the
    file's owner and mode, never its bytes."""
    key = Path(json.loads((box / "kernel.json").read_text())["key"])

    def row():
        return next(r for r in setup.check(box) if r[0] == "who can read your key")

    assert setup.key_reader(key) == "this account"
    assert row()[1] is None and "any assistant you run" in row()[2]
    opened = []
    real_open = Path.open
    monkeypatch.setattr(Path, "open", lambda self, *a, **k: (opened.append(self), real_open(self, *a, **k))[1])  # fmt: skip
    setup.key_reader(key)
    assert key not in opened  # its owner and mode only
    if hasattr(os, "getuid"):  # another account's: as the system would say it
        monkeypatch.setattr(os, "getuid", lambda: key.stat().st_uid + 1)
        monkeypatch.setattr(os, "access", lambda *a, **k: False)
        assert setup.key_reader(key) == "another account"
        assert row()[1] is True and "can't read it" in row()[2]
    assert setup.key_reader(tmp_path / "no-key-here") == ""


def test_setup_says_who_can_change_the_code_the_doors_run(box, tmp_path, monkeypatch):
    """An assistant running as the account that owns this code could change
    the guard door itself, by a command the guard reads as no edit. Told
    from each file's owner and mode, never its bytes; only code no file or
    folder of which this account can write is out of its reach."""

    def row():
        return next(r for r in setup.check(box) if r[0] == "who can change this code")

    assert setup.code_writer() == "this account"
    assert row()[1] is None and "the guard door too" in row()[2]
    code = tmp_path / "code"
    (code / "doors").mkdir(parents=True)
    for f in ("runtime.py", "doors/guard.py", "willow.pin.json"):
        (code / f).write_text("")
    if hasattr(os, "getuid"):  # another account's: as the system would say it
        mine = code.stat().st_uid
        writable = set()
        monkeypatch.setattr(os, "getuid", lambda: mine + 1)
        monkeypatch.setattr(os, "access", lambda p, mode, **k: Path(p) in writable)
        assert setup.code_writer(code) == "another account"
        for f in (
            code / "doors" / "guard.py",
            code / "doors",
            code / "willow.pin.json",
        ):
            writable.add(f)  # any one of them is enough
            assert setup.code_writer(code) == "this account", f
            writable.clear()
        monkeypatch.setattr(setup, "HERE", code)
        assert row()[1] is True and "can't change the doors" in row()[2]


def test_the_guard_refuses_a_call_when_it_cant_answer(box, tmp_path, monkeypatch):
    """Claude Code takes a hook that crashed, timed out or printed nonsense as
    leave to go on, so one bad edit to the guard switched it off. Before a
    tool runs, the guard is written to refuse then; the prompt hook isn't,
    or a crash would stop every prompt; and setup says which it is."""
    hooks = setup.claude_hooks(box.resolve())["hooks"]
    (pre,) = [h for e in hooks["PreToolUse"] for h in e["hooks"]]
    assert "doors/guard.py" in pre["command"] and pre["onFailure"] == "block"
    for event in ("UserPromptSubmit", "SessionStart", "Stop", "PostToolUse"):
        assert all("onFailure" not in h for e in hooks[event] for h in e["hooks"])
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(setup, "managed_dir", lambda: tmp_path / "etc-claude-code")

    def row():
        return next(
            (r for r in setup.check(box) if r[0] == "a guard that can't answer"), None
        )

    assert row() is None  # no guard door wired: nothing to say of it
    setup.write(box, "claude-code")
    assert setup.guard_closed(box) and row()[1] is True
    f = home / ".claude" / "settings.json"
    doc = json.loads(f.read_text())
    for e in doc["hooks"]["PreToolUse"]:
        for h in e["hooks"]:
            h.pop("onFailure", None)  # a settings file written before this
    f.write_text(json.dumps(doc))
    assert not setup.guard_closed(box)
    assert row()[1] is None and "lets the call through" in row()[2]
    assert "--write claude-code" in row()[2]


def test_managed_settings_hold_the_key_and_code_by_the_system_not_by_words(
    box, tmp_path
):
    """What no guard of words could do: the sandbox refuses every shell
    command a read of the key and a write to the record, the runtime's
    files and the code, whatever its words, and no command may leave it;
    the file tools, outside the sandbox, are held by deny rules, absolute
    paths written as Claude Code reads them (a double slash)."""
    doc = setup.managed(box)
    key = Path(json.loads((box / "kernel.json").read_text())["key"]).resolve()
    kept = [box.resolve(), setup.runtime.state(box).resolve(), setup.HERE,
            setup.runtime.WILLOW.resolve()]  # fmt: skip
    assert doc["hooks"] == setup.claude_hooks(box.resolve())["hooks"]
    deny = doc["permissions"]["deny"]
    assert f"Read(/{key})" in deny and deny[0].startswith("Read(//")
    assert all(f"Edit(/{d}/**)" in deny for d in kept)
    if sys.platform.startswith("win"):
        assert "sandbox" not in doc  # Claude Code has none on Windows itself
        return
    sb = doc["sandbox"]
    assert sb["enabled"] and sb["failIfUnavailable"]
    assert sb["allowUnsandboxedCommands"] is False
    assert sb["filesystem"]["denyRead"] == [str(key)]
    assert set(sb["filesystem"]["denyWrite"]) == {str(key), *map(str, kept)}
    assert not any(p.startswith("//") for p in sb["filesystem"]["denyWrite"])


def test_on_wsl_managed_settings_are_refused_since_they_hold_nothing(
    box, tmp_path, monkeypatch
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(setup, "on_wsl", lambda: True)
    (line,) = setup.write(box, "managed")
    assert line.startswith("refused:") and "wslInheritsWindowsSettings" in line
    assert not (home / ".claude" / "model-context-provider-managed.json").exists()


def test_cursors_managed_hooks_are_written_for_its_administrators_file(
    box, tmp_path, monkeypatch
):
    import set_up

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(set_up.sys, "platform", "linux")
    monkeypatch.setattr(
        set_up, "CURSOR_MANAGED", tmp_path / "etc" / "cursor" / "hooks.json"
    )
    lines = set_up.write_cursor_managed(box)
    made = home / ".cursor" / "model-context-provider-managed-hooks.json"
    hooks = json.loads(made.read_text())["hooks"]
    assert hooks["preToolUse"][0]["failClosed"] is True
    assert any("sudo install -D -m 644" in ln for ln in lines)
    assert not set_up.CURSOR_MANAGED.exists()  # never written there by this
    set_up.CURSOR_MANAGED.parent.mkdir(parents=True)
    set_up.CURSOR_MANAGED.write_text("{}")
    again = set_up.write_cursor_managed(box)
    assert any(
        ln.startswith("refused") and "by hand" in " ".join(again) for ln in again
    )
    assert set_up.CURSOR_MANAGED.read_text() == "{}"
    monkeypatch.setattr(set_up.sys, "platform", "darwin")
    assert set_up.write_cursor_managed(box)[0].startswith("refused")
