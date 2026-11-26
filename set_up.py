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
    reader = key_reader(Path(cfg.get("key", "")))
    out.append(("who can read your key", None if reader != "another account" else True,
                "an account of its own: an assistant running as you can't read it"
                if reader == "another account" else
                "this account, the one any assistant you run works as, so a script it "
                "writes can read it, whatever a guard says. Keeping it in an account of "
                "its own, with sealing across, is designed in docs/OPEN.md, not built. "
                "For Claude Code, --write managed has its sandbox refuse the read to "
                "every command"
                if reader == "this account" else
                "can't be told here"))  # fmt: skip
    writer = code_writer()
    out.append(("who can change this code", None if writer != "another account" else True,
                "an account of its own: an assistant running as you can't change the doors"
                if writer == "another account" else
                f"this account, so an assistant running as you could change the doors in "
                f"{HERE} by a command, the guard door too. Installed where only an "
                "administrator can write is designed in docs/OPEN.md, not built. For "
                "Claude Code, --write managed has its sandbox and deny rules refuse the edit"
                if writer == "this account" else
                "can't be told here"))  # fmt: skip
    where = guard_where(box)
    out.append(("the guard door", True if where == "managed" else None,
                "in Claude Code's managed settings: an assistant can't switch it off"
                if where == "managed" else
                "in ~/.claude/settings.json, where an assistant let edit ~/.claude could "
                "switch it off; to make it the administrator's: python set_up.py --box "
                f"{shlex.quote(str(box))} --write managed" if where == "user" else
                "not in Claude Code's settings (another assistant's hooks are its own)"))  # fmt: skip
    if where:
        out.append(("a guard that can't answer", True if guard_closed(box) else None,
                    "refuses the call (onFailure: block)" if guard_closed(box) else
                    "lets the call through: Claude Code takes a guard that crashed or timed "
                    "out as leave to go on. Write the hooks again: python set_up.py --box "
                    f"{shlex.quote(str(box))} --write " + ("managed" if where == "managed"
                                                          else "claude-code")))  # fmt: skip
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
    env = f"WILLOW={runtime.WILLOW_SOURCE}"

    def line(door: str) -> str:
        argv = [sys.executable, str(HERE / "doors" / door), "--box", str(box)]
        return " ".join([env, *map(shlex.quote, argv)])

    def run(door: str, **more) -> dict:
        return {"type": "command", "command": line(door), **more}

    guard = run("guard.py")
    # before a tool runs, a guard that can't answer is a No: Claude Code
    # otherwise takes a crash, a timeout or bad output as leave to go on
    # (Claude Code 2.1.295 and later). Not on the prompt hook, whose failure
    # would block every prompt, nor where the call has already run.
    gate = {**guard, "onFailure": "block"}
    return {"hooks": {
        "UserPromptSubmit": [{"hooks": [run("hook.py")]}],
        "SessionStart": [{"hooks": [run("session.py")]}, {"hooks": [guard]}],
        "SessionEnd": [{"hooks": [run("session.py", timeout=60)]}, {"hooks": [guard]}],
        "PreToolUse": [{"matcher": GUARDED, "hooks": [gate]}],
        "PostToolUse": [{"matcher": "Bash", "hooks": [guard]}],
        "PostToolUseFailure": [{"matcher": "Bash", "hooks": [guard]}],
        "Stop": [{"hooks": [guard]}],
        "PreCompact": [{"hooks": [guard]}],
    }}  # fmt: skip


def paste(box: Path) -> str:
    """What to paste: Claude Code's MCP + hooks, then every other assistant
    from Willow's hosts table, each in its own settings shape. --write does
    the merge instead."""
    env = f"WILLOW={runtime.WILLOW_SOURCE}"
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


def guard_closed(box: Path) -> bool:
    """Whether the settings that run this record's guard door (managed first,
    then the person's own) have it refuse a tool call when it can't answer:
    onFailure "block" on its PreToolUse entry."""
    d = managed_dir()
    files = [d / "managed-settings.json",
             *sorted((d / "managed-settings.d").glob("*.json")),
             Path.home() / ".claude" / "settings.json"]  # fmt: skip
    mine = str(box.resolve())
    for f in files:
        try:
            doc = json.loads(f.read_text())
            entries = doc["hooks"]["PreToolUse"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        hooks = [h for e in entries if isinstance(e, dict)
                 for h in e.get("hooks") or [] if isinstance(h, dict)
                 and "doors/guard.py" in str(h.get("command", ""))
                 and mine in str(h.get("command", ""))]  # fmt: skip
        if hooks:
            return all(h.get("onFailure") == "block" for h in hooks)
    return False


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


def key_reader(key: Path) -> str:
    """Who can read the key, from what the system says of the file, never
    its bytes: "this account" when the account setup runs as can (the one an
    assistant runs as, whatever it is told), "another account" when it can't,
    "" when it can't be told (no file there, or no owner to ask, as on
    Windows)."""
    try:
        st = key.stat()
    except OSError:
        return ""
    if not hasattr(os, "getuid"):
        return ""
    if st.st_uid == os.getuid() or os.access(key, os.R_OK):
        return "this account"
    return "another account"


#: what runs when a door does: the runtime, the doors, and the pin that holds
#: Willow to the bytes it was built on (so Willow's own files need no more)
CODE = ("*.py", "doors/*.py", "willow.pin.json")


def code_writer(root: Path | None = None) -> str:
    """Who can change the code that runs when a door does, from what the
    system says of each file and folder, never their bytes: "this account"
    when the account setup runs as can change any of them (the one an
    assistant runs as, so it could change the guard itself, by a command the
    guard can't read as an edit), "another account" when it can change none,
    "" when it can't be told (as on Windows)."""
    if not hasattr(os, "getuid"):
        return ""
    root = HERE if root is None else root
    paths = [root, root / "doors", *(f for g in CODE for f in sorted(root.glob(g)))]
    for f in paths:
        try:
            st = f.stat()
        except OSError:
            continue
        if st.st_uid == os.getuid() or os.access(f, os.W_OK):
            return "this account"
    return "another account"


def on_wsl() -> bool:
    """Linux under Windows, where /etc/claude-code is the person's to write."""
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def managed(box: Path) -> dict:
    """What goes in Claude Code's managed settings: the hooks, then what an
    assistant's own code can't get past, since the system holds it, not a
    guard of words. The sandbox (not on Windows itself, where Claude Code
    has none) refuses every shell command it runs, and what that starts, a
    read of the key and a write to the record, the runtime's files or the
    code the doors run; no command may leave it, and Claude Code doesn't
    start without it. The file tools run outside the sandbox, so deny rules
    hold the same paths for them. Hooks and MCP servers run outside both:
    that is how sealing still reads the key."""
    box = box.resolve()
    key = Path(json.loads((box / "kernel.json").read_text())["key"]).resolve()
    kept = [box, runtime.state(box).resolve(), HERE, runtime.WILLOW.resolve()]
    doc = claude_hooks(box)
    doc["permissions"] = {"deny": [f"Read(/{key})", f"Edit(/{key})",
                                   *(f"Edit(/{d}/**)" for d in kept)]}  # fmt: skip
    if not sys.platform.startswith("win"):
        doc["sandbox"] = {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {"denyRead": [str(key)],
                           "denyWrite": [str(key), *map(str, kept)]},
        }  # fmt: skip
    return doc


def write_managed(box: Path) -> list[str]:
    """Claude Code's managed settings for this record (managed() says what),
    as a file of their own, and the line that installs it. That folder is an
    administrator's, so this never writes there: the person runs the line,
    with sudo. Once it is there, an assistant that can edit ~/.claude can't
    switch the guard door off, and disableAllHooks or a project's sandbox
    settings don't reach it. Refused on WSL, where that folder is the
    person's to write and so no barrier."""
    if on_wsl():
        return ["refused: on WSL, /etc/claude-code is yours to write, so managed "
                "settings there hold nothing against an assistant running as you. "
                "Use Windows' own, C:\\Program Files\\ClaudeCode, with Claude Code's "
                "wslInheritsWindowsSettings"]  # fmt: skip
    text = json.dumps(managed(box), indent=2) + "\n"
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
        f"wrote {made}: the hooks, the sandbox and the deny rules, for Claude Code's",
        "managed settings. Read it before you install it. Install it in a terminal of",
        "your own (it needs your administrator password), readable by everyone (644):",
        "a managed file Claude Code can't read is skipped without a word.",
        "",
        f"    {install}",
        "",
        "Then an assistant can't switch the guard door off by editing your settings,",
        "and no command it runs can read your key or change your record, this",
        f"runtime's files, or the code in {HERE} and {runtime.WILLOW}, whatever its words.",
        "What else it changes, for every project in Claude Code:",
        *(
            [
                "  - every shell command runs in Claude Code's sandbox: it writes only in the",
                "    project's folder, and network to a new host asks you first;",
                "  - Claude Code won't start where the sandbox can't run"
                + (
                    " (Linux needs bubblewrap and socat: sudo apt install bubblewrap socat);"
                    if sys.platform.startswith("linux")
                    else ";"
                ),
            ]
            if not sys.platform.startswith("win")
            else [
                "  - Windows itself has no sandbox: only the deny rules hold, for the file tools;"
            ]
        ),
        f"  - an assistant can't edit the Provider in {HERE}, nor the Willow it runs",
        f"    in {runtime.WILLOW}: work on the Provider in another checkout, not the",
        "    one the hooks run from (docs/OPEN.md).",
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
            if not hosts.here_now(name):
                continue  # not on this machine: no settings made for it
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
