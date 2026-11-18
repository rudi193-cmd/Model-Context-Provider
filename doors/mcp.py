"""The MCP door: the Model Context Protocol's stdio transport, one JSON-RPC 2.0
message a line, written by hand with the standard library (the shape of
Willow's adapters/stdlib/mcp-lite/server.py).

    python doors/mcp.py --box DIR

Its tools are the runtime's verbs. There is no tool to seal: sealing is the
person's, with their key, outside any door.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime

VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")


def schema(arg: str | None) -> dict:
    if arg is None:
        return {"type": "object", "properties": {}}
    return {
        "type": "object",
        "properties": {arg: {"type": "string"}},
        "required": [arg],
    }


TOOLS = [
    {"name": "read", "arg": "question",
     "description": "Ask the person's files a question. You get whether they hold it, "
                    "never the passages: those reach you only through a sealed leave."},
    {"name": "propose", "arg": None,
     "description": "Propose what the last read served as one scope; it waits for the "
                    "person's seal. You cannot seal."},
    {"name": "leave", "arg": None,
     "description": "The scope the person sealed, as the one page you may read. "
                    "Without a seal, nothing."},
    {"name": "draft", "arg": "question",
     "description": "Ask willow to draft the answer itself: if the person sealed a page "
                    "for this question, your model is asked for one sentence over it "
                    "(MCP sampling), the sentence is checked, and it waits for their "
                    "seal. If nothing is sealed, no model is asked."},
    {"name": "context", "arg": "question",
     "description": "Ask a question and get the page the person sealed for it, if "
                    "they sealed one; else only whether their files hold it."},
    {"name": "answer", "arg": "sentence",
     "description": "One sentence about the page you were given, citing each passage "
                    "by its id in brackets, like [a1b2c3d4e5f6]. Code checks it; if it "
                    "stands it waits for the person's seal. Add nothing the page lacks."},
    {"name": "capture", "arg": "note",
     "description": "Hand in one thing worth keeping: a note, a decision, a finding. "
                    "It waits for the person's seal; sealed, it is kept in their "
                    "record. You cannot seal it, and you cannot read it back."},
]  # fmt: skip


def answer(box: Path, msg: dict, ask=None) -> dict | None:
    if not isinstance(msg, dict) or "id" not in msg:
        return None
    mid, method, params = msg["id"], msg.get("method"), msg.get("params") or {}

    def ok(result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    if method == "initialize":
        asked = params.get("protocolVersion")
        return ok({"protocolVersion": asked if asked in VERSIONS else VERSIONS[0],
                   "capabilities": {"tools": {}},
                   "serverInfo": {"name": "model-context-provider", "version": "0"}})  # fmt: skip
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": [{"name": t["name"], "description": t["description"],
                              "inputSchema": schema(t["arg"])} for t in TOOLS]})  # fmt: skip
    if method == "tools/call":
        name = str(params.get("name"))
        args = params.get("arguments") or {}
        spec = next((t for t in TOOLS if t["name"] == name), None)
        arg = args.get(spec["arg"]) if spec and spec["arg"] else None
        result = runtime.call(box, name, arg, door="mcp", ask=ask)
        refused = result.get("state") == "refused"
        return ok({"content": [{"type": "text", "text": json.dumps(result)}],
                   "structuredContent": result, "isError": refused})  # fmt: skip
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}  # fmt: skip


class Asker:
    """The way to the client's model, MCP sampling on the same pipe: a
    sampling/createMessage request out, the reply with its id back. Only
    carries; the runtime says what is asked."""

    def __init__(self, lines, out):
        self.lines, self.out, self.n, self.can = lines, out, 0, False

    def __call__(self, system: str, user: str) -> str:
        self.n += 1
        mid = f"provider-sample-{self.n}"
        req = {"jsonrpc": "2.0", "id": mid, "method": "sampling/createMessage",
               "params": {"messages": [{"role": "user",
                                        "content": {"type": "text", "text": user}}],
                          "systemPrompt": system, "maxTokens": 400,
                          "temperature": 0, "includeContext": "none"}}  # fmt: skip
        print(json.dumps(req), file=self.out, flush=True)
        for raw in self.lines:
            if not raw.strip():
                continue
            msg = json.loads(raw)
            if not isinstance(msg, dict) or msg.get("id") != mid:
                raise RuntimeError("the client answered something else while sampling")
            if "error" in msg:
                raise RuntimeError(str(msg["error"].get("message", msg["error"])))
            content = (msg.get("result") or {}).get("content")
            parts = content if isinstance(content, list) else [content or {}]
            return "".join(str(c.get("text", "")) for c in parts if isinstance(c, dict))
        raise RuntimeError("the client closed before answering")


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "--box":
        print("usage: mcp.py --box DIR", file=sys.stderr)
        return 2
    box = Path(argv[1])
    lines = iter(sys.stdin)
    asker = Asker(lines, sys.stdout)
    for raw in lines:
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except ValueError:
            reply = {"jsonrpc": "2.0", "id": None,
                     "error": {"code": -32700, "message": "parse error"}}  # fmt: skip
        else:
            if isinstance(msg, dict) and msg.get("method") == "initialize":
                caps = (msg.get("params") or {}).get("capabilities") or {}
                asker.can = "sampling" in caps
            reply = answer(box, msg, asker if asker.can else None)
        if reply is not None:
            print(json.dumps(reply), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
