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
    """A record takes its words list only when it is made, and Willow's UI
    ticks the starter list only when the stack holds it."""
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
