"""The MCP door as 2026-07-28 has it, beside the older one: no handshake,
each request saying its version and its client's capabilities in its own
_meta, what the client is to be asked going out in the reply and coming back
on a retry (multi round-trip requests), and a stream for what changes. The
door only carries; what a retry may carry is the runtime's to decide."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

from test_draft import FROST, sealed_for
from test_leave import seal
from test_point import LINKS, page  # noqa: F401 - the fixture

import runtime

ROOT = Path(__file__).resolve().parents[1]
DOOR = ROOT / "doors" / "mcp.py"
spec = importlib.util.spec_from_file_location("mcp_door", DOOR)
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

V = "2026-07-28"
P = "io.modelcontextprotocol/"
SAMPLES = {"sampling": {}}


def req(method, params=None, caps=None, mid=1, version=V):
    meta = {P + "protocolVersion": version, P + "clientCapabilities": caps or {},
            P + "clientInfo": {"name": "test", "version": "0"}}  # fmt: skip
    return {"jsonrpc": "2.0", "id": mid, "method": method,
            "params": {**(params or {}), "_meta": meta}}  # fmt: skip


def draft_call(**more):
    return {"name": "page", "arguments": {"action": "draft", "question": FROST}, **more}


def reply_to(sampling, text):
    """A client's model's answer to a sampling request, citing the page."""
    user = sampling["params"]["messages"][0]["content"]["text"]
    sid = re.search(r"`([0-9a-f]{12})`", user).group(1)
    return {"role": "assistant", "model": "stand-in",
            "content": {"type": "text", "text": text.format(sid=sid)}}  # fmt: skip


# ── what every modern reply carries ────────────────────────────────────────


def test_discover_says_the_versions_and_what_the_door_can_do(box):
    got = door.answer(box, req("server/discover"))["result"]
    assert got["supportedVersions"][0] == V and "2025-11-25" in got["supportedVersions"]
    assert got["capabilities"]["tools"] and got["instructions"] == door.INSTRUCTIONS
    assert got["resultType"] == "complete"
    assert got["_meta"][P + "serverInfo"]["name"] == "model-context-provider"
    assert got["ttlMs"] == 0 and got["cacheScope"] == "private"


def test_discover_with_no_meta_is_still_answered_as_its_own_version(box):
    msg = {"jsonrpc": "2.0", "id": 1, "method": "server/discover"}
    assert door.answer(box, msg)["result"]["supportedVersions"][0] == V


def test_a_version_the_door_doesnt_speak_is_said_with_those_it_does(box):
    got = door.answer(box, req("tools/list", version="1900-01-01"))["error"]
    assert got["code"] == -32022 and got["data"]["requested"] == "1900-01-01"
    assert got["data"]["supported"][0] == V


def test_a_list_is_complete_named_and_never_kept_for_long(box):
    got = door.answer(box, req("tools/list"))["result"]
    assert [t["name"] for t in got["tools"]] == [t["name"] for t in door.listing(box)]
    assert got["resultType"] == "complete" and got["ttlMs"] == 0
    assert got["cacheScope"] == "private"


def test_a_tool_result_says_its_kind_and_isnt_cached(box):
    got = door.answer(box, req("tools/call", {"name": "grant", "arguments": {}}))
    assert got["result"]["resultType"] == "complete"
    assert "ttlMs" not in got["result"] and got["result"]["structuredContent"]["state"]


def test_ping_is_gone_and_initialize_still_opens_the_older_way(box):
    assert door.answer(box, req("ping"))["error"]["code"] == -32601
    old = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2025-11-25", "capabilities": {}}}  # fmt: skip
    got = door.answer(box, old)["result"]
    assert got["protocolVersion"] == "2025-11-25" and "resultType" not in got


def test_a_resource_not_found_is_invalid_params_now(box):
    got = door.answer(box, req("resources/read", {"uri": "provider://nothing"}))
    assert got["error"]["code"] == -32602
    old = {"jsonrpc": "2.0", "id": 1, "method": "resources/read",
           "params": {"uri": "provider://nothing"}}  # fmt: skip
    assert door.answer(box, old)["error"]["code"] == -32002


# ── a sentence from the client's model, over a retry ───────────────────────


def test_draft_asks_the_clients_model_in_the_reply(box):
    sealed_for(box)
    got = door.answer(box, req("tools/call", draft_call(), SAMPLES))["result"]
    assert got["resultType"] == "input_required" and "ttlMs" not in got
    (asked,) = got["inputRequests"].values()
    assert asked["method"] == "sampling/createMessage"
    assert (
        asked["params"]["temperature"] == 0 and "includeContext" not in asked["params"]
    )
    text = asked["params"]["messages"][0]["content"]["text"]
    assert "first frost comes in late October" in text and "MOT" not in text
    assert [r["verb"] for r in runtime.call(box, "sent", door="pipe")["rows"]] == [
        "sample"
    ]


def test_the_retry_with_its_answer_is_held_and_waits_on_the_seal(box):
    sealed_for(box)
    first = door.answer(box, req("tools/call", draft_call(), SAMPLES))["result"]
    ((key, asked),) = first["inputRequests"].items()
    retry = draft_call(requestState=first["requestState"], inputResponses={
        key: reply_to(asked, "The first frost comes in late October [{sid}].")})  # fmt: skip
    got = door.answer(box, req("tools/call", retry, SAMPLES, mid=2))["result"]
    assert got["resultType"] == "complete"
    assert got["structuredContent"]["state"] == "waiting", got
    verbs = [r["verb"] for r in runtime.call(box, "sent", door="pipe")["rows"]]
    assert verbs == ["sample", "draft"]  # the page went once, on the first


def test_a_struck_sentence_is_asked_once_more_in_the_reply_told_why(box):
    sealed_for(box)
    first = door.answer(box, req("tools/call", draft_call(), SAMPLES))["result"]
    ((key, asked),) = first["inputRequests"].items()
    retry = draft_call(requestState=first["requestState"], inputResponses={
        key: reply_to(asked, "The first frost comes in early October [{sid}].")})  # fmt: skip
    again = door.answer(box, req("tools/call", retry, SAMPLES, mid=2))["result"]
    assert again["resultType"] == "input_required"
    (asked2,) = again["inputRequests"].values()
    text = asked2["params"]["messages"][0]["content"]["text"]
    assert "struck" in text and "early" in text
    last = draft_call(requestState=again["requestState"], inputResponses={
        key: reply_to(asked2, "Frost comes in early October [{sid}].")})  # fmt: skip
    got = door.answer(box, req("tools/call", last, SAMPLES, mid=3))["result"]
    assert got["structuredContent"]["state"] == "struck"  # two tries, as before
    assert runtime.call(box, "waiting", door="pipe")["state"] == "empty"


def test_a_retry_with_no_answer_is_asked_again(box):
    sealed_for(box)
    first = door.answer(box, req("tools/call", draft_call(), SAMPLES))["result"]
    retry = draft_call(requestState=first["requestState"])
    got = door.answer(box, req("tools/call", retry, SAMPLES, mid=2))["result"]
    assert got["resultType"] == "input_required"


def test_a_client_that_doesnt_sample_is_never_asked_to(box):
    sealed_for(box)
    got = door.answer(box, req("tools/call", draft_call()))["result"]
    assert got["resultType"] == "complete" and got["isError"]


# ── what a retry carries is held to this process, this request, and once ───


def first_state(box):
    sealed_for(box)
    first = door.answer(box, req("tools/call", draft_call(), SAMPLES))["result"]
    ((key, asked),) = first["inputRequests"].items()
    return first["requestState"], {
        key: reply_to(asked, "The first frost comes in late October [{sid}].")
    }


def refused(box, call):
    got = door.answer(box, req("tools/call", call, SAMPLES, mid=9))
    return "error" in got and got["error"]["code"] == -32602


def test_a_changed_state_is_refused(box):
    state, answers = first_state(box)
    a, b = state.split(".")
    flipped = a[:-2] + ("A" if a[-2] != "A" else "B") + a[-1] + "." + b
    assert refused(box, draft_call(requestState=flipped, inputResponses=answers))
    assert refused(box, draft_call(requestState="not a state", inputResponses=answers))


def test_a_state_holds_once(box):
    state, answers = first_state(box)
    ok = door.answer(box, req("tools/call", draft_call(requestState=state,
                                                       inputResponses=answers), SAMPLES))  # fmt: skip
    assert ok["result"]["structuredContent"]["state"] == "waiting"
    assert refused(box, draft_call(requestState=state, inputResponses=answers))


def test_a_state_holds_only_for_the_request_it_was_made_for(box):
    state, answers = first_state(box)
    other = {"name": "page", "arguments": {"action": "draft", "question": "something else"},
             "requestState": state, "inputResponses": answers}  # fmt: skip
    assert refused(box, other)


def test_a_state_holds_only_until_its_end(box, monkeypatch):
    state, answers = first_state(box)
    later = runtime.time.time() + runtime.LATER_SECONDS + 1
    monkeypatch.setattr(runtime.time, "time", lambda: later)
    assert refused(box, draft_call(requestState=state, inputResponses=answers))


def test_a_state_holds_only_in_the_process_that_made_it(box, monkeypatch):
    state, answers = first_state(box)
    monkeypatch.setattr(runtime, "LATER_KEY", b"another process" * 2)
    assert refused(box, draft_call(requestState=state, inputResponses=answers))


# ── the seal page, offered in the reply ────────────────────────────────────


def grant_call(**more):
    return {"name": "grant", "arguments": {}, **more}


def test_a_waiting_reply_offers_the_seal_page_in_the_reply(box, page):  # noqa: F811
    got = door.answer(box, req("tools/call", grant_call(), LINKS))["result"]
    assert got["resultType"] == "input_required"
    (asked,) = got["inputRequests"].values()
    assert asked["method"] == "elicitation/create"
    assert asked["params"]["mode"] == "url" and asked["params"]["url"] == page
    assert "elicitationId" not in asked["params"]  # 2026-07-28 has none
    rows = runtime.sent_log(box)["rows"]
    assert [(r["verb"], r["state"]) for r in rows if r["verb"] == "point"] == [
        ("point", "offered")
    ]


def test_the_retry_says_what_they_answered_and_never_asks_again(box, page):  # noqa: F811
    first = door.answer(box, req("tools/call", grant_call(), LINKS))["result"]
    (key,) = first["inputRequests"]
    retry = grant_call(requestState=first["requestState"],
                       inputResponses={key: {"action": "accept"}})  # fmt: skip
    got = door.answer(box, req("tools/call", retry, LINKS, mid=2))["result"]
    reply = got["structuredContent"]
    assert reply["state"] == "waiting" and reply["pointed"] == "accept"
    assert "settled" not in reply and page not in json.dumps(got)
    grants = [r for r in runtime.sent_log(box)["rows"] if r["verb"] == "grant"]
    assert len(grants) == 1  # the verb ran once, on the first request


def test_once_they_have_sealed_the_retry_says_so(box, page):  # noqa: F811
    first = door.answer(box, req("tools/call", grant_call(), LINKS))["result"]
    (key,) = first["inputRequests"]
    seal(box, runtime.call(box, "grant", door="mcp", where=door.here())["seal"])
    retry = grant_call(requestState=first["requestState"],
                       inputResponses={key: {"action": "accept"}})  # fmt: skip
    got = door.answer(box, req("tools/call", retry, LINKS, mid=2))["result"]
    assert got["structuredContent"]["settled"] == "sealed"


def test_no_seal_page_running_offers_nothing(box):
    got = door.answer(box, req("tools/call", grant_call(), LINKS))["result"]
    assert got["resultType"] == "complete"
    assert got["structuredContent"]["state"] == "waiting"


# ── a stream for what changes, through the real door ───────────────────────


def test_a_stream_is_told_when_the_tools_change_and_ends_with_the_input(box):
    p = subprocess.Popen([sys.executable, str(DOOR), "--box", str(box)], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True)  # fmt: skip

    def send(m):
        p.stdin.write(json.dumps(m) + "\n")
        p.stdin.flush()

    send(req("subscriptions/listen", {"notifications": {"toolsListChanged": True,
                                                        "resourceSubscriptions": ["x"]}}, mid=7))  # fmt: skip
    ack = json.loads(p.stdout.readline())
    assert ack["method"] == "notifications/subscriptions/acknowledged"
    assert ack["params"]["_meta"][P + "subscriptionId"] == 7
    assert ack["params"]["notifications"] == {"toolsListChanged": True}
    off = next(f for f, on in runtime.families(box).items() if on and f != "core")
    runtime.call(box, "tools", {"off": [off]}, door="pipe")
    send(req("tools/list", mid=8))
    listed = json.loads(p.stdout.readline())
    assert listed["id"] == 8
    told = json.loads(p.stdout.readline())
    assert told["method"] == "notifications/tools/list_changed"
    assert told["params"]["_meta"][P + "subscriptionId"] == 7
    p.stdin.close()
    end = json.loads(p.stdout.readline())
    assert end == {"jsonrpc": "2.0", "id": 7, "result": {
        "resultType": "complete", "_meta": {P + "subscriptionId": 7}}}  # fmt: skip
    p.wait(timeout=30)


def test_a_cancelled_stream_hears_nothing_more(box):
    p = subprocess.Popen([sys.executable, str(DOOR), "--box", str(box)], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True)  # fmt: skip
    lines = [req("subscriptions/listen", {"notifications": {"toolsListChanged": True}}, mid=7),
             {"jsonrpc": "2.0", "method": "notifications/cancelled",
              "params": {"requestId": 7}}]  # fmt: skip
    out, _ = p.communicate("".join(json.dumps(m) + "\n" for m in lines), timeout=30)
    (ack,) = [json.loads(x) for x in out.splitlines()]
    assert ack["method"] == "notifications/subscriptions/acknowledged"
