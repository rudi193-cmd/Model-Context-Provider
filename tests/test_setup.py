"""Setup checks, prints what to paste, and changes nothing of the client's."""

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
    """The JSON a client is given, started exactly as a client would start it."""
    entry = json.loads(setup.paste(box).split("3. Any other client")[1]
                       .split("\n", 2)[2].rsplit("\n\nYour door", 1)[0])["mcpServers"]["model-context-provider"]  # fmt: skip
    env = {**os.environ, **entry["env"]}
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]  # fmt: skip
    p = subprocess.run([entry["command"], *entry["args"]], env=env, check=False,
                       input="".join(json.dumps(m) + "\n" for m in msgs),
                       capture_output=True, text=True)  # fmt: skip
    listed = json.loads(p.stdout.splitlines()[1])["result"]["tools"]
    assert {t["name"] for t in listed} == set(runtime.VERBS["model"])


def test_setup_writes_nothing_of_the_clients(box, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    run("--box", box)
    assert list((tmp_path / "home").iterdir()) == []
