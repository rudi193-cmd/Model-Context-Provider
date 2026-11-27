"""The assistants that take an MCP server: where their settings live, the
shape each wants, and (with write) putting the door there. Same table Willow
keeps in adapters/stdlib/hosts, pointed at this project's doors/mcp.py.
`show` and `list` change nothing; `write` merges into the home file and
refuses when an entry by our name already differs.

    python hosts.py list
    python hosts.py show NAME --box DIR
    python hosts.py write NAME --box DIR
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import runtime

HERE = Path(__file__).resolve().parent
SERVER = HERE / "doors" / "mcp.py"
NAME = "model-context-provider"


def toml_table(name: str, values: dict) -> str:
    """A TOML table of strings, string lists, and nested string maps."""
    rows = [f"[{name}]"]
    nested = []
    for k, v in values.items():
        if isinstance(v, dict):
            nested.append((k, v))
        else:
            rows.append(f"{k} = {json.dumps(v)}")
    text = "\n".join(rows) + "\n"
    for k, v in nested:
        text += toml_table(f"{name}.{k}", v)
    return text


def mcp_servers(py: str, args: list[str], env: dict) -> dict:
    """The shape most assistants read: {"mcpServers": {name: command, args, env}}."""
    return {"mcpServers": {NAME: {"command": py, "args": args, "env": env}}}


def context_servers(py: str, args: list[str], env: dict) -> dict:
    """Zed's shape."""
    return {"context_servers": {NAME: {"command": py, "args": args, "env": env}}}


def local_command(py: str, args: list[str], env: dict) -> dict:
    """OpenCode's shape: the command and its arguments in one list."""
    return {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {
            NAME: {
                "type": "local",
                "command": [py, *args],
                "enabled": True,
                "environment": env,
            }
        },
    }


def servers_stdio(py: str, args: list[str], env: dict) -> dict:
    """VS Code's shape, which Copilot reads there."""
    return {
        "servers": {NAME: {"type": "stdio", "command": py, "args": args, "env": env}}
    }


def local_tools(py: str, args: list[str], env: dict) -> dict:
    """Copilot CLI's shape."""
    return {
        "mcpServers": {
            NAME: {
                "type": "local",
                "command": py,
                "args": args,
                "tools": ["*"],
                "env": env,
            }
        }
    }


def typed(field: str, value: str):
    """The usual shape with one more field fixed: `type` or `transport`
    set to `stdio`, for the assistants that read one."""

    def shape(py: str, args: list[str], env: dict) -> dict:
        entry = {"command": py, "args": args, field: value, "env": env}
        return {"mcpServers": {NAME: entry}}

    shape.__doc__ = f'The usual shape, with "{field}": "{value}".'
    return shape


def codex_table(py: str, args: list[str], env: dict) -> str:
    """Codex's shape, the one TOML one: text, not a document."""
    return toml_table(f"mcp_servers.{NAME}", {"command": py, "args": args, "env": env})


#: name -> (title, [(where its settings live, home file under ~, shape)]).
HOSTS = {
    "codex-cli": (
        "Codex CLI",
        [
            (
                "~/.codex/config.toml (or .codex/config.toml in a trusted project)",
                ".codex/config.toml",
                codex_table,
            )
        ],
    ),
    "copilot": (
        "Copilot",
        [
            (
                "VS Code: .vscode/mcp.json in the project, or your user mcp.json",
                ".vscode/mcp.json",
                servers_stdio,
            ),
            (
                "Copilot CLI: ~/.copilot/mcp-config.json",
                ".copilot/mcp-config.json",
                local_tools,
            ),
        ],
    ),
    "cursor": (
        "Cursor",
        [
            (
                "~/.cursor/mcp.json (or .cursor/mcp.json in a project)",
                ".cursor/mcp.json",
                mcp_servers,
            )
        ],
    ),
    "gemini-cli": (
        "Gemini CLI",
        [
            (
                "~/.gemini/settings.json (or .gemini/settings.json in a project)",
                ".gemini/settings.json",
                mcp_servers,
            )
        ],
    ),
    "opencode": (
        "OpenCode",
        [
            (
                "opencode.json in the project, or ~/.config/opencode/opencode.json",
                ".config/opencode/opencode.json",
                local_command,
            )
        ],
    ),
    "windsurf": (
        "Windsurf",
        [
            (
                "~/.codeium/windsurf/mcp_config.json (%USERPROFILE%\\.codeium\\windsurf on Windows)",
                ".codeium/windsurf/mcp_config.json",
                mcp_servers,
            )
        ],
    ),
    "zed": (
        "Zed",
        [
            (
                "~/.config/zed/settings.json (zed: open settings file)",
                ".config/zed/settings.json",
                context_servers,
            )
        ],
    ),
}

#: More assistants, each where codebase-memory-mcp's installer writes its
#: MCP entry (src/cli/cli.c and src/cli/agent_clients.c there, read
#: 2026-11-25), in the shape it writes, with WILLOW in `env` as every
#: mcpServers host above takes it. A path an environment variable moves is
#: named in the words; --write uses the default.
MORE = {
    "amazon-q": ("Amazon Q Developer", ".aws/amazonq/default.json", mcp_servers),
    "antigravity": ("Antigravity", ".gemini/config/mcp_config.json", mcp_servers),
    "augment": ("Augment (Auggie)", ".augment/settings.json", mcp_servers),
    "cline": ("Cline", ".cline/mcp.json", mcp_servers),
    "codebuddy": ("CodeBuddy Code", ".codebuddy/.mcp.json", mcp_servers),
    "devin": ("Devin CLI", ".config/devin/config.json", mcp_servers),
    "factory-droid": ("Factory Droid", ".factory/mcp.json", typed("type", "stdio")),
    "gitlab-duo": ("GitLab Duo CLI", ".gitlab/duo/mcp.json", typed("type", "stdio")),
    "ibm-bob": ("IBM Bob Shell", ".bob/mcp_settings.json", mcp_servers),
    "junie": ("Junie", ".junie/mcp/mcp.json", mcp_servers),
    "kimi": ("Kimi Code CLI", ".kimi-code/mcp.json", mcp_servers),
    "kiro": ("Kiro", ".kiro/settings/mcp.json", mcp_servers),
    "openhands": ("OpenHands", ".openhands/mcp.json", mcp_servers),
    "qoder": ("Qoder CLI", ".qoder/settings.json", mcp_servers),
    "qwen-code": ("Qwen Code", ".qwen/settings.json", mcp_servers),
    "rovo-dev": ("Rovo Dev CLI", ".rovodev/mcp.json", typed("transport", "stdio")),
    "tabnine": ("Tabnine", ".tabnine/mcp_servers.json", mcp_servers),
}
#: where a path moves with an environment variable, said beside it
MOVED = {
    "gitlab-duo": "$GLAB_CONFIG_DIR/duo/mcp.json, or $XDG_CONFIG_HOME/gitlab/duo/mcp.json",
    "kimi": "$KIMI_CODE_HOME/mcp.json",
    "kiro": "$KIRO_HOME/settings/mcp.json",
    "qwen-code": "$QWEN_HOME/settings.json",
    "rovo-dev": "the mcp.mcpConfigPath in ~/.rovodev/config.yml, if it names another",
}
#: Cline's extension reads a second file of its own
ALSO = {"cline": (".cline/data/settings/cline_mcp_settings.json", "Cline in an editor")}
for _name, (_title, _home, _shape) in MORE.items():
    _where = f"~/{_home}" + (f" (or {MOVED[_name]})" if _name in MOVED else "")
    _places = [(_where, _home, _shape)]
    if _name in ALSO:
        _places.append(
            (f"{ALSO[_name][1]}: ~/{ALSO[_name][0]}", ALSO[_name][0], _shape)
        )
    HOSTS[_name] = (_title, _places)

#: the folder in the home folder that says an assistant of MORE is here:
#: `--write all` writes one only where it is, so it never makes settings
#: for an assistant the person doesn't have (codebase-memory-mcp installs
#: only what it detects); `--write NAME` writes it when asked
FOUND_BY = {
    "amazon-q": ".aws/amazonq",
    "antigravity": ".gemini/antigravity-cli",
    "augment": ".augment",
    "cline": ".cline",
    "codebuddy": ".codebuddy",
    "devin": ".config/devin",
    "factory-droid": ".factory",
    "gitlab-duo": ".gitlab/duo",
    "ibm-bob": ".bob",
    "junie": ".junie",
    "kimi": ".kimi-code",
    "kiro": ".kiro",
    "openhands": ".openhands",
    "qoder": ".qoder",
    "qwen-code": ".qwen",
    "rovo-dev": ".rovodev",
    "tabnine": ".tabnine",
}


def here_now(name: str) -> bool:
    """Whether the assistant called name is on this machine, as far as its
    home settings can say: always, for the hosts this table began with."""
    return name not in FOUND_BY or (Path.home() / FOUND_BY[name]).is_dir()


#: Prompt hooks that can inject context (Willow's hook-elsewhere). Cursor cannot.
HOOK_HOSTS = {
    "codex-cli": (
        "Codex CLI",
        "~/.codex/hooks.json (or .codex/hooks.json in a trusted project)",
        "UserPromptSubmit",
    ),
    "gemini-cli": (
        "Gemini CLI",
        "~/.gemini/settings.json (or .gemini/settings.json in a project)",
        "BeforeAgent",
    ),
    "opencode": (
        "OpenCode",
        "~/.claude/settings.json for Claude-compatible hooks",
        "UserPromptSubmit",
    ),
}


def door_args(box: Path) -> list[str]:
    return [str(SERVER), "--box", str(box.resolve())]


def env() -> dict:
    return {"WILLOW": str(runtime.WILLOW_SOURCE)}


def places(name: str, box: Path, py: str) -> list[tuple[str, str, object]]:
    """Where each piece goes, its format, and what goes there."""
    args = door_args(box)
    out = []
    for where, _home, shape in HOSTS[name][1]:
        value = shape(py, args, env())
        out.append((where, "toml" if isinstance(value, str) else "json", value))
    return out


def render_places(found: list[tuple[str, str, object]]) -> str:
    """The text that says where to paste each piece, and the piece."""
    out = []
    for where, kind, value in found:
        text = value if kind == "toml" else json.dumps(value, indent=2) + "\n"
        out.append(f"Add this to {where}:\n\n{text}")
    return "\n".join(out)


def render(name: str, box: Path, py: str | None = None) -> str:
    """What to paste, and where, for the assistant called name."""
    return render_places(places(name, box, py or sys.executable or "python3"))


def hook_command(host: str, box: Path) -> str:
    """Shell command the host runs at each prompt (doors/hook.py --host)."""
    import shlex

    env_s = f"WILLOW={runtime.WILLOW_SOURCE}"
    parts = [
        sys.executable or "python3",
        str(HERE / "doors" / "hook.py"),
        "--host",
        host,
        "--box",
        str(box.resolve()),
    ]
    return " ".join([env_s, *map(shlex.quote, parts)])


def session_command(host: str, box: Path) -> str:
    """Shell command for session start/end (doors/session.py --host)."""
    import shlex

    env_s = f"WILLOW={runtime.WILLOW_SOURCE}"
    parts = [
        sys.executable or "python3",
        str(HERE / "doors" / "session.py"),
        "--host",
        host,
        "--box",
        str(box.resolve()),
    ]
    return " ".join([env_s, *map(shlex.quote, parts)])


def guard_command(box: Path) -> str:
    """Shell command for the guard door (doors/guard.py)."""
    import shlex

    parts = [sys.executable or "python3", str(HERE / "doors" / "guard.py"),
             "--box", str(box.resolve())]  # fmt: skip
    return " ".join([f"WILLOW={runtime.WILLOW_SOURCE}", *map(shlex.quote, parts)])


#: the tools Cursor's preToolUse is asked about: the ones that read a file by
#: name, change or delete one, or run a command (its hooks reference's names)
CURSOR_GUARDED = "Shell|Read|Write|Delete|Grep"


def hook_settings(host: str, box: Path) -> dict:
    """The hooks object to paste for a host that can inject context."""
    event = HOOK_HOSTS[host][2]
    cmd = {
        "type": "command",
        "command": hook_command(host, box),
        "timeout": 60 if host == "gemini-cli" else 10,
    }
    if host == "gemini-cli":
        cmd["name"] = "model-context-provider"
        return {"hooks": {event: [{"matcher": "*", "hooks": [cmd]}]}}
    return {"hooks": {event: [{"hooks": [cmd]}]}}


def cursor_hooks(box: Path) -> dict:
    """Cursor's hooks.json: session start/end for the person, a nudge after
    this server's MCP tools when something waits on their seal, and the guard
    door before a tool, a shell command or a read of a file. The guard fails
    closed (failClosed): Cursor otherwise lets a call through when its hook
    crashes, times out or says nothing."""
    cmd = session_command("cursor", box)
    entry = {"command": cmd, "timeout": 60}
    gate = {"command": guard_command(box), "timeout": 60, "failClosed": True}
    return {
        "version": 1,
        "hooks": {
            "sessionStart": [entry],
            "sessionEnd": [entry],
            "afterMCPExecution": [{**entry, "matcher": "model-context-provider"}],
            "preToolUse": [{**gate, "matcher": CURSOR_GUARDED}],
            "beforeShellExecution": [gate],
            "beforeReadFile": [gate],
        },
    }


def render_hook(host: str, box: Path) -> str:
    title, where, _ = HOOK_HOSTS[host]
    return (
        f"The prompt hook for {title}, in {where}:\n\n"
        + json.dumps(hook_settings(host, box), indent=2)
        + "\n"
    )


def paste_all(box: Path, py: str | None = None) -> str:
    """Every MCP host's paste, then the prompt hooks that can inject."""
    py = py or sys.executable or "python3"
    parts = ["MCP for assistants besides Claude Code (Willow's hosts table):", ""]
    for name, (title, _) in HOSTS.items():
        parts.append(f"### {title} (`{name}`)")
        parts.append("")
        parts.append(render(name, box, py).rstrip())
        parts.append("")
    parts.append(
        "Prompt hooks that can inject the sealed page (Cursor cannot; use MCP):"
    )
    parts.append("")
    for name, (title, _, _) in HOOK_HOSTS.items():
        parts.append(f"### {title} hook (`{name}`)")
        parts.append("")
        parts.append(render_hook(name, box).rstrip())
        parts.append("")
    parts.append("### Cursor hooks (`cursor`) — needs-you at session start/end")
    parts.append("")
    parts.append(
        "Add this to ~/.cursor/hooks.json:\n\n"
        + json.dumps(cursor_hooks(box), indent=2)
    )
    parts.append("")
    return "\n".join(parts)


def _merged(base: dict, patch: dict) -> dict:
    out = dict(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merged(out[k], v)
        else:
            out[k] = v
    return out


def _contains(have: dict, want: dict) -> bool:
    for k, v in want.items():
        if k not in have:
            return False
        if isinstance(v, dict) and isinstance(have[k], dict):
            if not _contains(have[k], v):
                return False
        elif have[k] != v:
            return False
    return True


def _conflicts(have: dict, want: dict) -> bool:
    """True when a key we set is already present with a different value."""
    for k, v in want.items():
        if k not in have:
            continue
        if isinstance(v, dict) and isinstance(have[k], dict):
            if _conflicts(have[k], v):
                return True
        elif have[k] != v:
            return True
    return False


def merge_json(path: Path, patch: dict) -> tuple[str, Path | None]:
    """Merge patch into path. Same keys we set that already differ refuse.
    Returns (state, path): wrote | same | refused."""
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text() or "{}")
        except ValueError:
            return "refused", path
        if not isinstance(existing, dict):
            return "refused", path
    if _conflicts(existing, patch):
        return "refused", path
    if _contains(existing, patch):
        return "same", path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_merged(existing, patch), indent=2) + "\n")
    return "wrote", path


def merge_toml_table(path: Path, table: str) -> tuple[str, Path | None]:
    """Append a TOML table when missing; refuse when a different one is there."""
    text = path.read_text() if path.is_file() else ""
    header = table.split("\n", 1)[0]  # [mcp_servers.model-context-provider]
    if header in text:
        # find existing block
        start = text.index(header)
        rest = text[start:]
        nxt = rest.find("\n[")
        block = rest if nxt < 0 else rest[:nxt]
        if block.strip() == table.strip():
            return "same", path
        return "refused", path
    path.parent.mkdir(parents=True, exist_ok=True)
    sep = "" if not text or text.endswith("\n") else "\n"
    path.write_text(text + sep + ("\n" if text and not text.endswith("\n\n") else "")
                    + table)  # fmt: skip
    return "wrote", path


def write_host(name: str, box: Path, py: str | None = None) -> list[str]:
    """Put this host's MCP door into its home settings. Never overwrites a
    different entry under our name. Returns lines saying what happened."""
    py = py or sys.executable or "python3"
    said = []
    for (where, kind, value), (_path_label, home, _) in zip(
        places(name, box, py), HOSTS[name][1]
    ):
        path = Path.home() / home
        if kind == "toml":
            state, _ = merge_toml_table(path, value if isinstance(value, str) else "")
        else:
            state, _ = merge_json(path, value if isinstance(value, dict) else {})
        if state == "wrote":
            said.append(f"wrote {path} ({where})")
        elif state == "same":
            said.append(f"already set in {path}")
        else:
            said.append(
                f"refused: {path} already has a different {NAME}; "
                "move it aside first, or paste by hand"
            )
    return said


def write_cursor_hooks(box: Path) -> list[str]:
    """Merge Cursor session + afterMCP hooks into ~/.cursor/hooks.json."""
    path = Path.home() / ".cursor" / "hooks.json"
    patch = cursor_hooks(box)
    # Merge hook lists by replacing our command entries, keep others
    existing: dict = {}
    if path.is_file():
        try:
            existing = json.loads(path.read_text() or "{}")
        except ValueError:
            return [f"refused: {path} is not JSON"]
    if not isinstance(existing, dict):
        return [f"refused: {path} is not an object"]
    out = dict(existing)
    out["version"] = max(int(existing.get("version") or 1), 1)
    hooks = dict(existing.get("hooks") or {})
    for event, entries in patch["hooks"].items():
        have = list(hooks.get(event) or [])
        kept = [
            e
            for e in have
            if not (
                isinstance(e, dict)
                and any(
                    d in str(e.get("command", ""))
                    for d in ("doors/session.py", "doors/guard.py")
                )
            )
        ]
        hooks[event] = kept + entries
    out["hooks"] = hooks
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n")
    return [
        f"wrote {path} (sessionStart, sessionEnd, afterMCPExecution, and the guard: "
        "preToolUse, beforeShellExecution, beforeReadFile)"
    ]


def main(argv: list[str]) -> int:
    if argv == ["list"]:
        for name, (title, found) in HOSTS.items():
            print(f"{name}\t{title}\t{'; '.join(where for where, _, _ in found)}")
        return 0
    if len(argv) == 4 and argv[0] in ("show", "write") and argv[2] == "--box":
        if argv[1] not in HOSTS:
            way = (
                "; Claude Code's way in is set_up.py (mcp add + prompt hook)"
                if argv[1] == "claude-code"
                else ""
            )
            print(f"refused: no host called {argv[1]}{way}; try list", file=sys.stderr)
            return 2
        box = Path(argv[3])
        if not (box / "kernel.json").is_file():
            print(
                "refused: not a record; set_up.py --box after Start it", file=sys.stderr
            )
            return 2
        if argv[0] == "show":
            print(render(argv[1], box), end="")
            return 0
        lines = write_host(argv[1], box)
        if argv[1] == "cursor":
            lines.extend(write_cursor_hooks(box))
        print("\n".join(lines))
        return 2 if any(ln.startswith("refused") for ln in lines) else 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
