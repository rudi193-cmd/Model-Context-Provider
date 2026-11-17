"""Set the Model Context Provider up over your record, in one go. It changes nothing of your
client's: it checks what's there and prints what to paste. The one file it
writes is model.json beside your record, and only when you name a model.

    python set_up.py --stack STACK            the stack Willow's UI made
    python set_up.py --box BOX                or one record directly
    python set_up.py --box BOX --model URL NAME   and the model on this machine
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import runtime

HERE = Path(__file__).resolve().parent


def boxes(stack: Path) -> list[Path]:
    """The records Willow's UI made under a stack: STACK/mine/FOLDER/box."""
    return sorted(p.parent for p in (stack / "mine").glob("*/box/kernel.json"))


def check(box: Path) -> list[tuple[str, bool, str]]:
    """What setup looked at: (what, fine, said)."""
    out = []
    willow_ok = (runtime.WILLOW / "kernel.py").is_file()
    out.append(("Willow", willow_ok, str(runtime.WILLOW) if willow_ok
                else f"not at {runtime.WILLOW}; set WILLOW to your Willow folder"))  # fmt: skip
    if not willow_ok:
        return out
    run = runtime.willow("kernel.py", "verify", "--box", str(box))
    out.append(("your record", run.returncode == 0,
                run.stdout.strip() or run.stderr.strip()))  # fmt: skip
    cfg = json.loads((box / "kernel.json").read_text())
    out.append(("your words", True, f"in use: {cfg['words']}" if cfg.get("words")
                else "none: type them in the words step of Willow's UI, then Start"))  # fmt: skip
    model = runtime.state(box) / "model.json"
    out.append(("a model to draft with", True, f"named in {model}" if model.exists()
                else "none: drafting needs a client that samples, or --model URL NAME"))  # fmt: skip
    return out


def paste(box: Path) -> str:
    """What to paste: the MCP door for Claude Code, the prompt hook, and the
    same door for any other client's MCP settings."""
    env = f"WILLOW={runtime.WILLOW}"
    door = [sys.executable, str(HERE / "doors" / "mcp.py"), "--box", str(box)]
    hook = " ".join([env, *map(shlex.quote, [sys.executable, str(HERE / "doors" / "hook.py"), "--box", str(box)])])  # fmt: skip
    session = " ".join([env, *map(shlex.quote, [sys.executable, str(HERE / "doors" / "session.py"), "--box", str(box)])])  # fmt: skip
    settings = {"hooks": {
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": hook}]}],
        "SessionStart": [{"hooks": [{"type": "command", "command": session}]}],
        "SessionEnd": [{"hooks": [{"type": "command", "command": session, "timeout": 60}]}],
    }}  # fmt: skip
    other = {"mcpServers": {"model-context-provider": {"type": "stdio", "command": door[0], "args": door[1:],
                                        "env": {"WILLOW": str(runtime.WILLOW)}}}}  # fmt: skip
    return "\n".join([
        "1. The MCP door, for Claude Code in every folder (run it once):",
        "",
        "    claude mcp add --scope user model-context-provider -e " + shlex.quote(env) + " -- " + shlex.join(door),
        "",
        "2. The hooks, in ~/.claude/settings.json (merge them with what's there): the prompt",
        "   hook, and the session door, which closes each session for your one seal and",
        "   tells you at the next start what waits on it:",
        "",
        *("    " + ln for ln in json.dumps(settings, indent=2).splitlines()),
        "",
        "3. Any other client that takes MCP servers as JSON:",
        "",
        *("    " + ln for ln in json.dumps(other, indent=2).splitlines()),
        "",
        "Your door has more: python doors/pipe.py --box " + shlex.quote(str(box)),
        '  with {"waiting": true}, {"shared": true}, {"backup": "/media/usb"} a line.',
    ])  # fmt: skip


def name_model(box: Path, url: str, model: str) -> str:
    if not runtime.on_this_machine(url):
        return f"refused: {url} is not on this machine"
    f = runtime.state(box) / "model.json"
    f.write_text(json.dumps({"url": url, "model": model}) + "\n")
    return f"wrote {f}"


def main(argv: list[str]) -> int:
    opts, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in ("--stack", "--box") and i + 1 < len(argv):
            opts[a], i = argv[i + 1], i + 2
        elif a == "--model" and i + 2 < len(argv):
            opts[a], i = (argv[i + 1], argv[i + 2]), i + 3
        else:
            print(__doc__, file=sys.stderr)
            return 2
    if ("--stack" in opts) == ("--box" in opts):
        print("setup: one of --stack or --box", file=sys.stderr)
        return 2
    if "--stack" in opts:
        found = boxes(Path(opts["--stack"]))
        if not found:
            print(f"No record under {opts['--stack']}/mine yet: seal your pick in "
                  "Willow's UI and press Start it, then run this again.")  # fmt: skip
            return 42
        if len(found) > 1:
            print("Your stack has a record for each folder. Run again with one:")
            print(
                "\n".join(
                    f"    python set_up.py --box {shlex.quote(str(b))}" for b in found
                )
            )
            return 42
        box = found[0]
    else:
        box = Path(opts["--box"])
        if not (box / "kernel.json").is_file():
            print(
                f"{box} isn't a record: Willow's UI makes one when you press Start it."
            )
            return 2
    if "--model" in opts:
        said = name_model(box, *opts["--model"])
        print(said)
        if said.startswith("refused"):
            return 2
    print(f"Your record: {box}\n")
    looked = check(box)
    for what, fine, said in looked:
        print(f"  {'ok ' if fine else 'NO '} {what}: {said}")
    if not all(fine for _, fine, _ in looked):
        print("\nFix what says NO first; nothing below would work without it.")
        return 2
    print("\n" + paste(box))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
