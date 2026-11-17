"""MCP sampling the unnamed way: the runtime holds the model, over the page the
person sealed and nothing else, and what it says is held strictly."""

import json
import re
import subprocess
import sys
from pathlib import Path

from test_leave import seal

import runtime

FROST = "when does the first frost come"
DOOR = Path(__file__).resolve().parents[1] / "doors" / "mcp.py"


class Model:
    """A stand-in for the client's model: says what it's told to, and keeps
    what it was sent."""

    def __init__(self, *replies):
        self.replies, self.sent = list(replies), []

    def __call__(self, system, user):
        self.sent.append((system, user))
        sid = re.search(r"`([0-9a-f]{12})`", user).group(1)
        return self.replies.pop(0).format(sid=sid)


def sealed_for(box, q=FROST):
    runtime.call(box, "read", q, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])


def test_nothing_sealed_no_model_is_asked(box):
    model = Model("x")
    got = runtime.call(box, "draft", FROST, door="mcp", ask=model)
    assert got == {"state": "populated", "asked": False} and model.sent == []


def test_a_sealed_page_is_all_the_model_is_sent(box):
    sealed_for(box)
    model = Model("The first frost comes in late October [{sid}].")
    got = runtime.call(box, "draft", FROST, door="mcp", ask=model)
    assert got["state"] == "waiting" and got["asked"], got
    ((_system, user),) = model.sent
    assert "first frost comes in late October" in user and "MOT" not in user


def test_a_struck_sentence_gets_one_more_try_told_why(box):
    sealed_for(box)
    model = Model("The first frost comes in early October [{sid}].",
                  "The first frost comes in late October [{sid}].")  # fmt: skip
    got = runtime.call(box, "draft", FROST, door="mcp", ask=model)
    assert got["state"] == "waiting"
    assert "early" in model.sent[1][1] and "struck" in model.sent[1][1]


def test_struck_twice_nothing_is_proposed(box):
    sealed_for(box)
    model = Model("Frost in early October [{sid}].", "Frost, early October [{sid}].")
    got = runtime.call(box, "draft", FROST, door="mcp", ask=model)
    assert got["state"] == "struck" and len(model.sent) == 2
    assert runtime.call(box, "waiting", door="pipe")["state"] == "empty"


def test_what_the_model_was_sent_is_on_the_log_first(box):
    sealed_for(box)
    model = Model("The first frost comes in late October [{sid}].")
    runtime.call(box, "draft", FROST, door="mcp", ask=model)
    verbs = [r["verb"] for r in runtime.call(box, "sent", door="pipe")["rows"]]
    assert verbs == ["sample", "draft"]


def test_a_client_that_fails_asks_nothing_more(box):
    sealed_for(box)

    def broken(system, user):
        raise RuntimeError("no model here")

    assert (
        runtime.call(box, "draft", FROST, door="mcp", ask=broken)["state"] == "refused"
    )


def test_without_sampling_draft_is_refused(box):
    assert runtime.call(box, "draft", FROST, door="mcp")["state"] == "refused"


# ── through the real door, a client that speaks MCP sampling ──────────────


def client(box, caps, reply):
    """Initialize, call draft, answer the door's sampling request if one comes."""
    p = subprocess.Popen([sys.executable, str(DOOR), "--box", str(box)], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True)  # fmt: skip

    def send(m):
        p.stdin.write(json.dumps(m) + "\n")
        p.stdin.flush()

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
          "params": {"protocolVersion": "2025-06-18", "capabilities": caps}})  # fmt: skip
    json.loads(p.stdout.readline())
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "draft", "arguments": {"question": FROST}}})  # fmt: skip
    asked = []
    while True:
        msg = json.loads(p.stdout.readline())
        if msg.get("method") == "sampling/createMessage":
            asked.append(msg["params"])
            text = msg["params"]["messages"][0]["content"]["text"]
            sid = re.search(r"`([0-9a-f]{12})`", text).group(1)
            send({"jsonrpc": "2.0", "id": msg["id"], "result": {
                "role": "assistant", "model": "stand-in",
                "content": {"type": "text", "text": reply.format(sid=sid)}}})  # fmt: skip
            continue
        p.stdin.close()
        p.wait(timeout=30)
        return msg["result"], asked


def test_the_door_samples_the_client_and_the_answer_waits(box):
    sealed_for(box)
    result, asked = client(
        box, {"sampling": {}}, "The first frost comes in late October [{sid}]."
    )
    assert not result["isError"] and result["structuredContent"]["state"] == "waiting"
    (params,) = asked
    assert params["includeContext"] == "none" and params["temperature"] == 0
    assert "MOT" not in params["messages"][0]["content"]["text"]


def test_a_client_that_did_not_declare_sampling_is_never_sampled(box):
    sealed_for(box)
    result, asked = client(box, {}, "x")
    assert result["isError"] and asked == []
