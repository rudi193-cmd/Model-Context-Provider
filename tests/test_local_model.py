"""A model on this machine, named by the person, for when the client can't
sample: the same sealed page, the same strict check."""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from test_leave import seal

import runtime

FROST = "when does the first frost come"


@pytest.fixture
def server():
    """A stand-in for llama.cpp's or Ollama's chat endpoint on 127.0.0.1."""
    heard = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            heard.append((self.path, body))
            sid = re.search(r"`([0-9a-f]{12})`", body["messages"][1]["content"]).group(
                1
            )
            text = f"The first frost comes in late October [{sid}]."
            out = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/v1", heard
    srv.shutdown()


def named(box, url, model="stand-in"):
    (runtime.state(box) / "model.json").write_text(
        json.dumps({"url": url, "model": model})
    )


def sealed(box):
    runtime.call(box, "read", FROST, door="pipe")
    seal(box, runtime.call(box, "propose", door="pipe")["seal"])


def test_the_person_drafts_with_their_own_model_and_it_waits_for_them(box, server):
    url, heard = server
    named(box, url)
    sealed(box)
    got = runtime.call(box, "draft", FROST, door="pipe")
    assert got["state"] == "waiting" and got["asked"], got
    ((path, body),) = heard
    assert path == "/v1/chat/completions" and body["temperature"] == 0
    assert "MOT" not in body["messages"][1]["content"]


def test_the_log_says_where_the_page_went(box, server):
    url, _ = server
    named(box, url)
    sealed(box)
    runtime.call(box, "draft", FROST, door="pipe")
    row = next(
        r
        for r in runtime.call(box, "sent", door="pipe")["rows"]
        if r["verb"] == "sample"
    )
    assert row["to"] == f"stand-in at {url} (this machine)" and row["page"]


def test_a_model_door_whose_client_cannot_sample_uses_the_named_model(box, server):
    url, heard = server
    named(box, url)
    sealed(box)
    assert runtime.call(box, "draft", FROST, door="mcp")["state"] == "waiting"
    assert len(heard) == 1


def test_nothing_sealed_the_named_model_hears_nothing(box, server):
    url, heard = server
    named(box, url)
    assert runtime.call(box, "draft", FROST, door="pipe")["asked"] is False
    assert heard == []


def test_a_model_off_this_machine_is_refused_before_anything_is_sent(box):
    named(box, "https://api.example.com/v1")
    sealed(box)
    got = runtime.call(box, "draft", FROST, door="pipe")
    assert got["state"] == "refused" and "not on this machine" in got["why"]
    assert all(
        r["verb"] != "sample" for r in runtime.call(box, "sent", door="pipe")["rows"]
    )


def test_a_model_that_is_not_running_is_said_so(box):
    named(box, "http://127.0.0.1:9/v1")  # nothing listens on the discard port
    sealed(box)
    assert runtime.call(box, "draft", FROST, door="pipe")["state"] == "refused"


def test_the_person_can_see_what_model_servers_this_machine_runs(box):
    got = runtime.call(box, "models", door="pipe")
    assert "servers" in got
    assert runtime.call(box, "models", door="mcp")["state"] == "refused"
