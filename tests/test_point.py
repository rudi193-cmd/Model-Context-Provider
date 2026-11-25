"""The person pointed at their seal page through their own assistant, by
MCP's URL elicitation (2025-11-25): when a model's reply waits on their seal,
a client that shows links is asked to offer them the page's address. The
runtime decides when and what; the door only carries. The address holds no
secret, nothing is sealed by it, and it is written down on the sent log."""

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

import runtime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_door", ROOT / "doors" / "mcp.py")
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)

LINKS = {"elicitation": {"url": {}}}


@pytest.fixture
def page(box):
    """Something listening where the seal page says it is, for as long as a
    test runs: the page itself isn't needed to know its address answers."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen()
    runtime.page_here(box, s.getsockname()[1])
    yield f"http://127.0.0.1:{s.getsockname()[1]}/"
    runtime.page_gone(box)
    s.close()


def pointed(box, *, page_open=True, point=True, door_name="mcp", verb="grant"):
    """A call, with a pointer that records what it was asked and accepts."""
    seen = []

    def to_person(message, url, asked):
        seen.append({"message": message, "url": url, "asked": asked})
        return "accept"

    got = runtime.call(box, verb, door=door_name, where="/work/a", session="s1",
                       point=to_person if point else None)  # fmt: skip
    return got, seen


def sent_points(box):
    return [r for r in runtime.sent_log(box)["rows"] if r["verb"] == "point"]


def test_no_page_running_means_no_address(box):
    assert runtime.page_url(box) is None
    runtime.page_here(box, 9)  # left behind by a page that was killed
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens there now
    runtime.page_here(box, port)
    assert runtime.page_url(box) is None
    (runtime.state(box) / runtime.PAGE_AT).write_text("not json")
    assert runtime.page_url(box) is None


def test_the_address_is_the_pages_with_no_secret(box, page):
    assert runtime.page_url(box) == page
    assert "?" not in page and "k=" not in page


def test_a_waiting_reply_points_the_person_at_their_page(box, page):
    got, seen = pointed(box)
    assert got["state"] == "waiting" and got["pointed"] == "accept"
    (one,) = seen
    assert one["url"] == page
    assert "a session asking to read your files" in one["message"]
    assert "Nothing is sealed from here" in one["message"]
    assert len(one["asked"]) == 32
    assert [r["state"] for r in sent_points(box)] == ["accept"]
    assert page not in json.dumps(got)  # the model is never given the address


def test_nothing_is_sealed_or_declined_by_the_persons_answer(box, page):
    got, _ = pointed(box)
    again = runtime.call(box, "grant", door="mcp", where="/work/a", session="s1")
    assert again["state"] == "waiting" and again["seal"] == got["seal"]


def test_no_page_no_door_to_show_it_or_another_reply_points_no_one(box, page):
    assert pointed(box, point=False)[1] == []
    assert pointed(box, verb="tools")[1] == []  # not waiting on a seal
    runtime.page_gone(box)
    got, seen = pointed(box)
    assert seen == [] and "pointed" not in got and got["state"] == "waiting"


def test_the_persons_own_door_is_never_pointed(box, page):
    assert pointed(box, door_name="pipe", verb="waiting")[1] == []


def test_a_client_that_cant_answer_leaves_the_reply_as_it_was(box, page):
    def fails(message, url, asked):
        raise RuntimeError("the client closed before answering")

    got = runtime.call(box, "grant", door="mcp", where="/work/a", session="s1",
                       point=fails)  # fmt: skip
    assert got["state"] == "waiting" and got["pointed"] == "unanswered"


def test_only_a_client_that_shows_links_is_asked():
    assert door.can_point(LINKS)
    assert not door.can_point({"elicitation": {}})  # form only
    assert not door.can_point({"elicitation": {"form": {}}})
    assert not door.can_point({"sampling": {}})


def test_the_door_carries_the_request_and_the_answer():
    out = []

    class Out:
        def write(self, s):
            out.append(s)

        def flush(self):
            pass

    lines = iter([
        json.dumps({"jsonrpc": "2.0", "method": "notifications/progress"}) + "\n",
        json.dumps({"jsonrpc": "2.0", "id": "provider-point-1",
                    "result": {"action": "decline"}}) + "\n",
    ])  # fmt: skip
    p = door.Pointer(lines, Out())
    assert p("words", "http://127.0.0.1:1/", "a" * 32) == "decline"
    req = json.loads("".join(out))
    assert req["method"] == "elicitation/create"
    assert req["params"] == {"mode": "url", "message": "words",
                             "url": "http://127.0.0.1:1/", "elicitationId": "a" * 32}  # fmt: skip
    odd = iter([json.dumps({"jsonrpc": "2.0", "id": "provider-point-1",
                            "result": {"action": "sure"}}) + "\n"])  # fmt: skip
    assert door.Pointer(odd, Out())("w", "u", "a") == "unanswered"


def test_over_the_wire_a_grant_is_offered_to_the_person(box, page):
    run = subprocess.run(
        [sys.executable, str(ROOT / "doors" / "mcp.py"), "--box", str(box)],
        input="".join(json.dumps(m) + "\n" for m in [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-11-25", "capabilities": LINKS}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "grant", "arguments": {}}},
            {"jsonrpc": "2.0", "id": "provider-point-1", "result": {"action": "accept"}},
        ]),
        capture_output=True, text=True, check=False, cwd=str(box.parent),
    )  # fmt: skip
    msgs = [json.loads(line) for line in run.stdout.splitlines()]
    init, ask, reply = msgs[0], msgs[1], msgs[2]
    assert init["result"]["protocolVersion"] == "2025-11-25", run.stderr
    assert ask["method"] == "elicitation/create" and ask["params"]["url"] == page
    said = reply["result"]["structuredContent"]
    assert said["state"] == "waiting" and said["pointed"] == "accept"


def test_the_seal_page_says_where_it_is_while_it_runs(box):
    env = dict(os.environ)
    run = subprocess.Popen(
        [sys.executable, str(ROOT / "seal_page.py"), "--box", str(box), "--no-open"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
    )  # fmt: skip
    try:
        first = run.stdout.readline()
        while "http://" not in first:
            first = run.stdout.readline()
        deadline = time.monotonic() + 10
        while runtime.page_url(box) is None and time.monotonic() < deadline:
            time.sleep(0.05)
        url = runtime.page_url(box)
        assert url is not None and url in first and "k=" not in url
        secret = first.split("k=")[1].strip()
        assert secret not in (runtime.state(box) / runtime.PAGE_AT).read_text()
    finally:
        run.send_signal(signal.SIGINT)
        run.wait(timeout=10)
    assert runtime.page_url(box) is None
    assert not (runtime.state(box) / runtime.PAGE_AT).exists()
