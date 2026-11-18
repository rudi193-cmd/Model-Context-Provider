"""The seal page: the person's click carries out the kernel's own seal, and
nothing but the person's browser, on this machine, can make that click."""

import http.client
import json
import re
import threading
import urllib.parse
from pathlib import Path

import pytest

import runtime
import seal_page

FROST = "when does the first frost come"
ROOT = Path(__file__).resolve().parents[1]


class Browser:
    """A browser that opened the link: it holds the cookie, reads the form's
    secret off the page, and says where it is posting from."""

    def __init__(self, server, link):
        self.port = server.server_address[1]
        self.link = urllib.parse.urlsplit(link)
        self.cookie = ""

    def ask(self, method, path, body=None, **headers):
        con = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        if self.cookie and "Cookie" not in headers:
            headers["Cookie"] = self.cookie
        headers = {k.replace("_", "-"): v for k, v in headers.items() if v is not None}
        con.request(method, path, body=body, headers=headers)
        got = con.getresponse()
        text = got.read().decode()
        con.close()
        return got, text

    def open(self):
        got, _ = self.ask("GET", f"/?{self.link.query}")
        assert got.status == 303 and got.getheader("Location") == "/"
        self.cookie = got.getheader("Set-Cookie").split(";")[0]
        return got

    def page(self):
        got, text = self.ask("GET", "/")
        assert got.status == 200, text
        return text

    def click(self, act, subject, k=None, origin="", sure=None, **headers):
        form = {"k": self.secret() if k is None else k, "act": act, "subject": subject}
        if sure:
            form["sure"] = sure
        headers.setdefault("Origin", origin or f"http://127.0.0.1:{self.port}")
        return self.ask("POST", "/act", urllib.parse.urlencode(form),
                        Content_Type="application/x-www-form-urlencoded", **headers)  # fmt: skip

    def secret(self):
        return urllib.parse.parse_qs(self.link.query)["k"][0]


@pytest.fixture
def browser(box):
    server, link = seal_page.serve(box)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield Browser(server, link)
    server.shutdown()
    server.server_close()


def a_scope(box):
    runtime.call(box, "read", FROST, door="mcp")
    return runtime.call(box, "propose", door="mcp")["seal"]


def kinds(box):
    rows = (box / "record.jsonl").read_text().splitlines()
    return [json.loads(r)["kind"] for r in rows]


def test_it_listens_on_this_machine_only(browser, box):
    server, _ = seal_page.serve(box)
    assert server.server_address[0] == "127.0.0.1"
    server.server_close()


def test_the_link_opens_the_page_and_shows_the_page_that_would_leave(box, browser):
    subject = a_scope(box)
    got = browser.open()
    assert "HttpOnly" in got.getheader("Set-Cookie")
    assert "SameSite=Strict" in got.getheader("Set-Cookie")
    text = browser.page()
    assert "first frost comes in late October" in text and "garden.md:1" in text
    assert "MOT" not in text  # the scope's page, not the folder
    assert subject in text  # its name on the record, under "exactly what"
    assert "Seal: share this page" in text and "Not now" in text and "Decline" in text


def test_a_click_on_seal_is_the_kernels_own_seal(box, browser):
    subject = a_scope(box)
    browser.open()
    got, _ = browser.click("seal", subject)
    assert got.status == 303
    assert "seal" in kinds(box)
    assert runtime.willow("kernel.py", "verify", "--box", str(box)).returncode == 0
    assert runtime.call(box, "waiting", door="pipe")["state"] == "empty"
    assert "late October" in runtime.call(box, "leave", door="mcp")["page"]
    text = browser.page()
    assert "Sealed, with your key." in text and "Nothing waits on your seal." in text
    assert "Sealed, with your key." not in browser.page()  # said once


def test_a_click_on_decline_is_the_kernels_own_and_final(box, browser):
    subject = a_scope(box)
    browser.open()
    browser.click("decline", subject)  # the box beside it not ticked
    assert "decline" not in kinds(box)
    assert "tick the box" in browser.page()
    browser.click("decline", subject, sure="yes")
    assert "decline" in kinds(box) and "seal" not in kinds(box)
    assert runtime.call(box, "waiting", door="pipe")["state"] == "empty"
    run = runtime.willow("kernel.py", "seal", "--box", str(box), subject)
    assert run.returncode == 2 and "you declined" in run.stderr


def test_not_now_is_kept_beside_the_record_and_never_on_it(box, browser):
    subject = a_scope(box)
    browser.open()
    browser.click("later", subject)
    assert {"seal", "decline"}.isdisjoint(kinds(box))
    assert json.loads((runtime.state(box) / "later.json").read_text()) == [subject]
    (w,) = runtime.call(box, "waiting", door="pipe")["waiting"]
    assert w["seal"] == subject and w["later"]  # it still waits
    assert runtime.call(box, "owed", door="pipe") == {"state": "empty", "later": 1}
    assert not (runtime.state(box) / "needs-you.txt").exists()
    text = browser.page()
    assert "Set aside: 1, still waiting" in text and "Bring back" in text
    assert "Seal: share this page" not in text
    browser.click("back", subject)
    assert "Seal: share this page" in browser.page()
    assert runtime.call(box, "owed", door="pipe")["state"] == "waiting"


def test_a_session_and_a_sentence_are_each_said_as_what_they_are(box, browser):
    from test_leave import seal

    seal(box, a_scope(box))
    page = runtime.call(box, "leave", door="mcp")["page"]
    (sid,) = [b["id"] for b in runtime.boxes_of(page)]
    said = f"The first frost comes in late October [{sid}]."
    assert runtime.call(box, "answer", said, door="mcp")["state"] == "waiting"
    assert runtime.call(box, "close", door="session")["state"] == "waiting"
    browser.open()
    text = browser.page()
    assert "A model’s sentence" in text and "late October" in text
    assert "A session" in text and "these were my actions" in text
    assert "Seal: these were my actions" in text
    # what would be sealed is laid out to be read, not JSON inside JSON
    assert "<th>What it was</th>" in text and "<td>proposal</td>" in text
    assert "Sealing writes it to" in text and "written/sessions/" in text
    shown = text.split("The file itself")[0]
    assert "\\&quot;" not in shown and "came_of" not in shown
    for w in runtime.call(box, "waiting", door="pipe")["waiting"]:
        browser.click("seal", w["seal"])
    assert runtime.call(box, "waiting", door="pipe")["state"] == "empty"
    assert runtime.willow("kernel.py", "verify", "--box", str(box)).returncode == 0


REFUSED = {
    "no cookie": {"Cookie": "seal=wrong"},
    "another site": {"origin": "http://evil.example"},
    "a sandboxed frame": {"origin": "null"},
    "another port here": {"origin": "http://127.0.0.1:1"},
    "no origin": {"Origin": None},
    "the wrong secret in the form": {"k": "wrong"},
    "no secret in the form": {"k": ""},
    "renamed as this machine": {"Host": "evil.example:80"},
}


@pytest.mark.parametrize("how", sorted(REFUSED))
def test_a_click_that_is_not_the_persons_gets_403_and_seals_nothing(box, browser, how):
    subject = a_scope(box)
    browser.open()
    for act in ("seal", "decline", "later"):
        got, _ = browser.click(act, subject, sure="yes", **REFUSED[how])
        assert got.status == 403, (how, act)
    assert {"seal", "decline"}.isdisjoint(kinds(box))
    assert not (runtime.state(box) / "later.json").exists()
    assert runtime.call(box, "leave", door="mcp")["state"] == "refused"


def test_the_page_is_shown_to_nobody_without_the_link(box, browser):
    a_scope(box)
    for headers in ({}, {"Cookie": "seal=wrong"}):
        got, text = browser.ask("GET", "/", **headers)
        assert got.status == 403 and "October" not in text
    got, text = browser.ask("GET", "/?k=wrong")
    assert got.status == 403 and got.getheader("Set-Cookie") is None
    browser.open()
    got, text = browser.ask("GET", "/", Host="evil.example")
    assert got.status == 403 and "October" not in text


def test_only_what_waits_can_be_sealed_and_only_these_acts(box, browser):
    subject = a_scope(box)
    browser.open()
    for act, subj in (
        ("seal", "proposal:" + "0" * 64),
        ("seal", "--box"),
        ("verify", subject),
        ("init", subject),
    ):
        got, _ = browser.click(act, subj)
        assert got.status == 303
        assert "Nothing was done" in browser.page()
    assert {"seal", "decline"}.isdisjoint(kinds(box))
    got, _ = browser.ask("POST", "/seal", "k=x", Origin=f"http://127.0.0.1:{browser.port}")  # fmt: skip
    assert got.status == 403


def test_it_cannot_be_framed_and_runs_no_script(box, browser):
    a_scope(box)
    browser.open()
    got, text = browser.ask("GET", "/")
    csp = got.getheader("Content-Security-Policy")
    assert "frame-ancestors 'none'" in csp and "default-src 'none'" in csp
    assert "script-src" not in csp and "unsafe" not in csp
    assert got.getheader("X-Frame-Options") == "DENY"
    assert got.getheader("Referrer-Policy") == "same-origin"
    assert got.getheader("Cache-Control") == "no-store"
    assert "<script" not in text and not re.search(r"\son\w+=", text)
    assert " style=" not in text  # the one stylesheet is the page's own file
    got, css = browser.ask("GET", "/style.css")
    assert got.status == 200 and got.getheader("Content-Type").startswith("text/css")


def test_words_from_the_folder_cannot_write_markup(box, browser):
    (box.parent / "pile" / "garden.md").write_text(
        'The first frost <script>alert(1)</script> comes in "late" October.\n'
    )
    a_scope(box)
    browser.open()
    text = browser.page()
    assert "<script>" not in text and "&lt;script&gt;alert" in text


def test_a_refusal_of_the_kernels_is_said_and_nothing_is_sealed(box, browser):
    subject = a_scope(box)
    (box.parent / "test.key").chmod(0o644)  # a key others can read is refused
    browser.open()
    browser.click("seal", subject)
    text = browser.page()
    assert "Nothing was done" in text and "chmod 600" in text
    assert "seal" not in kinds(box)


def test_the_key_is_never_read_here_and_the_runtime_still_cannot_seal():
    src = (ROOT / "seal_page.py").read_text()
    assert ".key" not in src.replace("kernel.py", "") and '["key"]' not in src
    assert {"seal", "decline"}.isdisjoint(runtime.VERBS["person"])
    assert {"seal", "decline", "later", "back"}.isdisjoint(runtime.VERBS["model"])
    kernel_seal = re.compile(r"willow\(\s*\"kernel\.py\",\s*\"(seal|decline)\"")
    for f in [ROOT / "runtime.py", *(ROOT / "doors").glob("*.py")]:
        assert not kernel_seal.search(f.read_text()), f.name
        assert "seal_page" not in f.read_text().replace("seal_page.py", ""), f.name


def test_the_needs_you_card_names_the_page_and_never_its_secret(box, browser):
    a_scope(box)
    got = runtime.call(box, "owed", door="session")
    assert "seal_page.py" in got["card"] and "seal_page.py" in got["say"]
    for text in (got["card"], got["say"]):
        assert browser.secret() not in text and "?k=" not in text


def test_a_model_can_neither_set_aside_nor_bring_back(box):
    subject = a_scope(box)
    for verb in ("later", "back"):
        assert runtime.call(box, verb, subject, door="mcp")["state"] == "refused"
    assert not (runtime.state(box) / "later.json").exists()
