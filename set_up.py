"""Set the Model Context Provider up over your record, in one go.

By default it changes nothing of your client's: it checks what's there and
prints what to paste (Claude Code, and Cursor and the other assistants from
Willow's hosts table). With --write it merges the MCP door (and Cursor's
session hooks) into the home settings file, and refuses when an entry by our
name already differs. The one other file it writes is model.json beside your
record, and only when you name a model.

    python set_up.py --stack STACK
    python set_up.py --box BOX
    python set_up.py --box BOX --model URL NAME
    python set_up.py --box BOX --write cursor
    python set_up.py --box BOX --write all
    python set_up.py --box BOX --write command    your own door, as `provider`
    python set_up.py --box BOX --write managed    Claude Code's hooks, for its
                                                  managed settings, and the line
                                                  that installs them
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

import hosts
import runtime
import willow_pin

HERE = Path(__file__).resolve().parent


def boxes(stack: Path) -> list[Path]:
    """The records Willow's UI made under a stack: STACK/mine/FOLDER/box."""
    return sorted(p.parent for p in (stack / "mine").glob("*/box/kernel.json"))


#: Willow's base list of what a person's words mean in their files
STARTER = "starter-words"
#: its copy of the starter list, made readable by its owner alone, as the kernel asks
STARTER_COPY = "adapters/stdlib/starter-words/starter.py"


def stack_has_starter(stack: Path) -> bool | None:
    """Whether a stack's add-ons hold the starter words list; None when the
    stack's own list can't be read."""
    try:
        got = json.loads((stack / "STACK.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    names = got.get("addons") if isinstance(got, dict) else None
    return STARTER in names if isinstance(names, (list, dict)) else None


def no_words_yet(stack: Path) -> str:
    """What to do before the record is made, when the stack holds no words
    list: the one time a record can take one."""
    add = shlex.join([sys.executable, str(runtime.WILLOW / "ui" / "assemble.py"),
                      "add", STARTER, "--to", str(stack)])  # fmt: skip
    return (
        "Your stack has no starter-words, so the words step starts with no "
        "words list ticked, and a question in your own words finds less "
        "without one. Add it first, then keep it ticked in the words step "
        "(a record made without one can be given one later, with "
        f"kernel.py words):\n\n    {add}\n"
    )


def check(box: Path) -> list[tuple[str, bool | None, str]]:
    """What setup looked at: (what, fine, said). Fine is None for what is
    worth knowing and stops nothing."""
    out = []
    willow_ok = (runtime.WILLOW / "kernel.py").is_file()
    out.append(("Willow", willow_ok, str(runtime.WILLOW) if willow_ok
                else f"not at {runtime.WILLOW}; set WILLOW to your Willow folder"))  # fmt: skip
    if not willow_ok:
        return out
    off = willow_pin.problems(runtime.WILLOW, runtime.PIN)
    out.append(("Willow is the pinned one", not off, "; ".join(off[:5]) if off
                else f"commit {willow_pin.load(runtime.PIN)['commit'][:12]}"))  # fmt: skip
    if off:
        return out
    run = runtime.willow("kernel.py", "verify", "--box", str(box))
    out.append(("your record", run.returncode == 0,
                run.stdout.strip() or run.stderr.strip()))  # fmt: skip
    cfg = json.loads((box / "kernel.json").read_text())
    if cfg.get("words"):
        out.append(("your words", True, f"in use: {cfg['words']}; add a line of your own "
                    "to it any time (your word = what your files call it, another)"))  # fmt: skip
    else:
        mine = box.parent / "my-words.txt"
        copy = shlex.join([sys.executable, str(runtime.WILLOW / STARTER_COPY), "copy",
                           "--to", str(mine)])  # fmt: skip
        give = shlex.join([sys.executable, str(runtime.WILLOW / "kernel.py"), "words",
                           "--box", str(box), "--words", str(mine)])  # fmt: skip
        out.append(("your words", None, "none: this record was made with no words list, "
                    "so a question in your own words finds less. Give it the starter "
                    f"list, then add lines of your own to it:\n\n    {copy}\n    {give}\n"))  # fmt: skip
    where = guard_where(box)
    out.append(("the guard door", True if where == "managed" else None,
                "in Claude Code's managed settings: an assistant can't switch it off"
                if where == "managed" else
                "in ~/.claude/settings.json, where an assistant let edit ~/.claude could "
                "switch it off; to make it the administrator's: python set_up.py --box "
                f"{shlex.quote(str(box))} --write managed" if where == "user" else
                "not in Claude Code's settings (another assistant's hooks are its own)"))  # fmt: skip
    model = runtime.state(box) / "model.json"
    out.append(("a model to draft with", True, f"named in {model}" if model.exists()
                else "none: drafting needs a client that samples, or --model URL NAME"))  # fmt: skip
    return out


#: the tools the guard is asked about before they run: the ones that read a
#: file by name, change one, or run a command
GUARDED = "Write|Edit|MultiEdit|NotebookEdit|Read|NotebookRead|Grep|Glob|Bash"


def claude_hooks(box: Path) -> dict:
    """Claude Code's hooks, as its settings file holds them: the prompt hook,
    the session door, and the guard door at each moment it answers."""
    env = f"WILLOW={runtime.WILLOW}"

    def line(door: str) -> str:
        argv = [sys.executable, str(HERE / "doors" / door), "--box", str(box)]
        return " ".join([env, *map(shlex.quote, argv)])

    def run(door: str, **more) -> dict:
        return {"type": "command", "command": line(door), **more}

    guard = run("guard.py")
    return {"hooks": {
        "UserPromptSubmit": [{"hooks": [run("hook.py")]}],
        "SessionStart": [{"hooks": [run("session.py")]}, {"hooks": [guard]}],
        "SessionEnd": [{"hooks": [run("session.py", timeout=60)]}, {"hooks": [guard]}],
        "PreToolUse": [{"matcher": GUARDED, "hooks": [guard]}],
        "PostToolUse": [{"matcher": "Bash", "hooks": [guard]}],
        "PostToolUseFailure": [{"matcher": "Bash", "hooks": [guard]}],
        "Stop": [{"hooks": [guard]}],
        "PreCompact": [{"hooks": [guard]}],
    }}  # fmt: skip


def paste(box: Path) -> str:
    """What to paste: Claude Code's MCP + hooks, then every other assistant
    from Willow's hosts table, each in its own settings shape. --write does
    the merge instead."""
    env = f"WILLOW={runtime.WILLOW}"
    door = [sys.executable, str(HERE / "doors" / "mcp.py"), "--box", str(box)]
    settings = claude_hooks(box)
    others = hosts.paste_all(box)
    return "\n".join([
        "1. The MCP door, for Claude Code in every folder (run it once):",
        "",
        "    claude mcp add --scope user model-context-provider -e " + shlex.quote(env) + " -- " + shlex.join(door),
        "",
        "2. The hooks, in ~/.claude/settings.json (merge them with what's there): the prompt",
        "   hook; the session door, which closes each session for your one seal and",
        "   tells you at the next start what waits on it; and the guard door, which",
        "   stops a tool call that names your key, writes into your record, holds a",
        "   secret, edits a file it hasn't read, or repeats a command that failed twice:",
        "",
        *("    " + ln for ln in json.dumps(settings, indent=2).splitlines()),
        "",
        "3. Cursor and the other assistants (Willow's hosts table).",
        "   Finish one: python set_up.py --box " + shlex.quote(str(box)) + " --write cursor",
        "   Or paste:  python hosts.py show cursor --box " + shlex.quote(str(box)),
        "",
        others.rstrip(),
        "",
        "To seal what waits on you with a click, in a terminal of your own:",
        "  python seal_page.py --box " + shlex.quote(str(box)),
        "Or save a launcher to start it with a double-click:",
        "  python seal_page.py launcher --box " + shlex.quote(str(box)) + " --write",
        "",
        "Your door has more: python doors/pipe.py --box " + shlex.quote(str(box)),
        '  with {"waiting": true}, {"preview": true}, {"shared": true}, {"backup": "/media/usb"} a line.',
        "Or save it as a command, and say: provider waiting",
        "  python set_up.py --box " + shlex.quote(str(box)) + " --write command",
    ])  # fmt: skip


def write_claude_hooks(box: Path) -> list[str]:
    """Merge Claude Code's prompt, session and guard hooks into
    ~/.claude/settings.json."""
    patch = claude_hooks(box.resolve())
    path = Path.home() / ".claude" / "settings.json"
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text() or "{}")
        except ValueError:
            return [f"refused: {path} is not JSON"]
    if not isinstance(existing, dict):
        return [f"refused: {path} is not an object"]
    hooks = dict(existing.get("hooks") or {})
    for event, entries in patch["hooks"].items():
        have = list(hooks.get(event) or [])
        kept = [
            e
            for e in have
            if not (
                isinstance(e, dict)
                and any(
                    "model-context-provider" in str(h.get("command", ""))
                    or "doors/hook.py" in str(h.get("command", ""))
                    or "doors/session.py" in str(h.get("command", ""))
                    or "doors/guard.py" in str(h.get("command", ""))
                    for h in (e.get("hooks") or [e])
                    if isinstance(h, dict)
                )
            )
        ]
        hooks[event] = kept + entries
    out = {**existing, "hooks": hooks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    return [
        f"wrote {path} ({', '.join(patch['hooks'])})",
        "MCP for Claude Code still needs: claude mcp add --scope user … "
        "(printed above when you run without --write)",
    ]


#: the Provider's own file among Claude Code's managed settings: a drop-in,
#: so it never touches managed-settings.json or anyone else's file there
MANAGED_NAME = "50-model-context-provider.json"


def managed_dir() -> Path:
    """Where Claude Code reads its managed settings on this system (its docs,
    managed-settings): only an administrator writes there, so a hook in it is
    one an assistant running as the person can't edit or switch off."""
    if sys.platform == "darwin":
        return Path("/Library/Application Support/ClaudeCode")
    if sys.platform.startswith("win"):
        return Path(r"C:\Program Files\ClaudeCode")
    return Path("/etc/claude-code")


def guard_where(box: Path) -> str:
    """Where Claude Code is told to run this record's guard door: "managed"
    when a managed settings file holds it, "user" when only the person's own
    settings do, "" when neither."""

    def holds(f: Path) -> bool:
        try:
            text = f.read_text()
        except (OSError, UnicodeDecodeError):
            return False
        return "doors/guard.py" in text and str(box.resolve()) in text

    d = managed_dir()
    managed = [
        d / "managed-settings.json",
        *sorted((d / "managed-settings.d").glob("*.json")),
    ]
    if any(holds(f) for f in managed):
        return "managed"
    return "user" if holds(Path.home() / ".claude" / "settings.json") else ""


def write_managed(box: Path) -> list[str]:
    """Claude Code's hooks, the same as --write claude-code, as a file of
    their own for its managed settings, and the line that installs it. That
    folder is an administrator's, so this never writes there: the person
    runs the line, with sudo. Once it is there, an assistant that can edit
    ~/.claude can't switch the guard door off, and disableAllHooks in user or
    project settings doesn't reach it."""
    text = json.dumps(claude_hooks(box.resolve()), indent=2) + "\n"
    made = Path.home() / ".claude" / "model-context-provider-managed.json"
    made.parent.mkdir(parents=True, exist_ok=True)
    made.write_text(text)
    to = managed_dir() / "managed-settings.d" / MANAGED_NAME
    if sys.platform.startswith("win"):
        install = f'copy "{made}" "{to}"   (in a terminal run as administrator)'
    elif sys.platform == "darwin":
        install = (f"sudo mkdir -p {shlex.quote(str(to.parent))} && "
                   f"sudo install -m 644 {shlex.quote(str(made))} {shlex.quote(str(to))}")  # fmt: skip
    else:
        install = (
            f"sudo install -D -m 644 {shlex.quote(str(made))} {shlex.quote(str(to))}"
        )
    return [
        f"wrote {made}: the hooks, for Claude Code's managed settings",
        "Install it, in a terminal of your own (it needs your administrator password):",
        "",
        f"    {install}",
        "",
        "Then an assistant can't switch the guard door off by editing your settings.",
        "The same hooks in ~/.claude/settings.json can stay: a hook named twice runs once.",
        'To block every hook but managed ones too, add "allowManagedHooksOnly": true to the',
        "file before you install it; that blocks your own other hooks as well.",
    ]


COMMAND = "provider"


def write_command(box: Path) -> list[str]:
    """Save the person's own door as a command, `provider`, with their
    record and this Python filled in: ~/.local/bin/provider. One that is
    there and differs is never written over."""
    pipe = Path(__file__).resolve().parent / "doors" / "pipe.py"
    willow = os.environ.get("WILLOW")
    text = "#!/bin/sh\n# Model Context Provider: your own door, by words.\n" + (
        f"export WILLOW={shlex.quote(willow)}\n" if willow else ""
    ) + (
        f"exec {shlex.quote(sys.executable)} {shlex.quote(str(pipe))} "
        f'--box {shlex.quote(str(box.resolve()))} "$@"\n'
    )  # fmt: skip
    path = Path.home() / ".local" / "bin" / COMMAND
    if path.exists() and path.read_text() != text:
        return [f"refused: {path} is there already and differs; move it, then run this again"]  # fmt: skip
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o755)
    on_path = str(path.parent) in os.environ.get("PATH", "").split(os.pathsep)
    return [
        f"wrote {path}",
        f"Try it: {COMMAND} waiting",
        *(
            []
            if on_path
            else [f"{path.parent} isn't on your PATH yet: add it, or run {path}"]
        ),  # fmt: skip
    ]


def write(box: Path, which: str) -> list[str]:
    """Finish setup for one host, or all MCP hosts plus Claude's hooks; or
    save the person's own door as a command."""
    if which == "command":
        return write_command(box)
    if which == "managed":
        return write_managed(box)
    if which == "claude-code":
        return write_claude_hooks(box)
    if which == "all":
        lines = write_claude_hooks(box)
        for name in hosts.HOSTS:
            lines.extend(hosts.write_host(name, box))
            if name == "cursor":
                lines.extend(hosts.write_cursor_hooks(box))
        return lines
    if which not in hosts.HOSTS:
        return [
            f"refused: no host called {which}; try hosts.py list, or claude-code, or all"
        ]
    lines = hosts.write_host(which, box)
    if which == "cursor":
        lines.extend(hosts.write_cursor_hooks(box))
    return lines


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
        if a in ("--stack", "--box", "--write") and i + 1 < len(argv):
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
            if stack_has_starter(Path(opts["--stack"])) is False:
                print(no_words_yet(Path(opts["--stack"])))
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
        print(f"  {'ok ' if fine else '-- ' if fine is None else 'NO '} {what}: {said}")
    if any(fine is False for _, fine, _ in looked):
        print("\nFix what says NO first; nothing below would work without it.")
        return 2
    if "--write" in opts:
        lines = write(box, opts["--write"])
        print("\n" + "\n".join(lines))
        return 2 if any(ln.startswith("refused") for ln in lines) else 0
    print("\n" + paste(box))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
