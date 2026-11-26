"""The seal page: the person's click carries out the kernel's own seal, and
nothing but the person's browser, on this machine, can make that click."""

import html
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
        self.server = server
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
    # in the person's words, not the kernel's: what was asked, what was
    # handed in, how many wait; the sentence by the files of its page
    assert " × " not in shown and "bite" not in shown.split("<details")[0]
    assert "asked of your files" in text and "handed in for your seal" in text
    assert "Said of the page you sealed from garden.md" in text
    assert "2 things wait on your seal." in text
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
    for act in ("seal", "decline", "later", "stop", "quit"):
        got, _ = browser.click(act, subject, sure="yes", **REFUSED[how])
        assert got.status == 403, (how, act)
    assert {"seal", "decline"}.isdisjoint(kinds(box))
    assert not (runtime.state(box) / "later.json").exists()
    assert not (runtime.state(box) / "stopped.json").exists()
    assert browser.server.done is False
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


def test_what_you_shared_is_listed_and_a_click_stops_it(box, browser):
    from test_leave import seal

    subject = a_scope(box)
    seal(box, subject)
    assert runtime.call(box, "leave", door="mcp")["state"] == "left"
    browser.open()
    got, text = browser.ask("GET", "/shared")
    assert got.status == 200
    assert "garden.md:1" in text and "Sealed." in text and "late October" in text
    assert "Stop sharing this" in text
    assert "the AI assistant (MCP): the page you sealed: garden.md:1" in text
    got, _ = browser.ask(
        "POST", "/act",
        urllib.parse.urlencode({"k": browser.secret(), "act": "stop",
                                "subject": subject, "at": "/shared"}),
        Content_Type="application/x-www-form-urlencoded",
        Origin=f"http://127.0.0.1:{browser.port}",
    )  # fmt: skip
    assert got.status == 303 and got.getheader("Location") == "/shared"
    again = runtime.call(box, "leave", door="mcp")
    assert (again["state"], again["code"]) == ("refused", "stopped")
    assert {"decline"}.isdisjoint(kinds(box))  # a stop is beside the record
    got, text = browser.ask("GET", "/shared")
    text = html.unescape(text)
    assert "Stopped. It won't be given to a model again." in text  # said once
    assert "Stopped: it won't be shared again." in text  # where it stands now
    assert "Stop sharing this" not in text


def test_the_shared_page_is_held_to_the_same_table(box, browser):
    a_scope(box)
    got, text = browser.ask("GET", "/shared")
    assert got.status == 403 and "garden" not in text
    browser.open()
    got, text = browser.ask("GET", "/shared")
    assert got.status == 200 and "<script" not in text
    assert "frame-ancestors 'none'" in got.getheader("Content-Security-Policy")
    got, _ = browser.click("seal", "x")  # where a click goes back to is one of two
    assert got.getheader("Location") == "/"


def test_close_this_page_stops_it_and_so_does_nobody_asking(box):
    server, link = seal_page.serve(box)
    said = []
    t = threading.Thread(target=lambda: said.append(seal_page.run(server)))
    t.start()
    b = Browser(server, link)
    b.open()
    assert "Close this page" in b.page()
    got, text = b.click("quit", "")
    assert got.status == 200 and "still waits" in text
    t.join(10)
    server.server_close()
    assert said == ["closed"]
    assert {"seal", "decline"}.isdisjoint(kinds(box))
    server, _ = seal_page.serve(box)
    assert seal_page.run(server, idle=0.01) == "idle"
    server.server_close()


def test_a_launcher_is_printed_for_each_system_and_writes_nothing(box, tmp_path):
    home = tmp_path / "home"
    code, said = seal_page.launcher(box, False, home, "Linux")
    assert code == 0 and not home.exists()
    for name in ("macOS", "Windows", "Linux"):
        assert f"{name}: save as" in said
    assert "seal_page.py" in said and str(box.resolve()) in said
    assert "--idle 30" in said and "WILLOW=" in said and "Terminal=false" in said
    assert "?k=" not in said  # a launcher holds no secret: each start makes one


def test_the_launcher_is_saved_once_and_never_over_one_that_differs(box, tmp_path):
    home = tmp_path / "home"
    code, said = seal_page.launcher(box, True, home, "Linux")
    (f,) = (home / ".local/share/applications").iterdir()
    assert code == 0 and str(f) in said and f.stat().st_mode & 0o100
    assert seal_page.launcher(box, True, home, "Linux") == (0, f"Already there: {f}")
    kept = f.read_text()
    f.write_text(kept + "# mine\n")
    code, said = seal_page.launcher(box, True, home, "Linux")
    assert code == 2 and "never written over" in said
    assert f.read_text() == kept + "# mine\n"
    assert seal_page.launcher(box, True, home, "Plan9")[0] == 2
    for system, name in (("Darwin", "Seal page.command"), ("Windows", "Seal page.bat")):
        assert seal_page.launcher(box, True, home, system)[0] == 0
        assert (home / "Desktop" / name).is_file()


def test_a_desktop_files_exec_line_survives_a_space_and_a_percent():
    assert seal_page.desktop_arg("/my files/50%/box") == '"/my files/50%%/box"'
    assert seal_page.desktop_arg('a"b$c\\d') == '"a\\\\"b\\\\$c\\\\\\\\d"'


def test_the_launcher_starts_the_page(box, tmp_path):
    import shlex
    import subprocess
    import sys

    _, text = seal_page.launchers(box, tmp_path)["Darwin"]
    line = text.splitlines()[1].replace(" exec ", " ", 1).replace("--idle 30", "--bad")
    env, *argv = shlex.split(line)
    assert env.startswith("WILLOW=") and argv[0] == sys.executable
    run = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert run.returncode == 2 and "usage: seal_page.py" in run.stderr


def switch(browser, act, family):
    return browser.ask(
        "POST", "/act",
        urllib.parse.urlencode({"k": browser.secret(), "act": act,
                                "subject": family, "at": "/tools"}),
        Content_Type="application/x-www-form-urlencoded",
        Origin=f"http://127.0.0.1:{browser.port}",
    )  # fmt: skip


def test_the_tools_page_lists_each_group_and_a_click_switches_it(box, browser):
    browser.open()
    got, text = browser.ask("GET", "/tools")
    text = html.unescape(text)
    assert got.status == 200 and "A model is offered 9 tools now." in text
    for word in ("<h2>shelf</h2>", "<code>shelf</code> (add, list, read, remove)",
                 "On: on unless you turn it off", "Off: off until you use it or turn it on",
                 "On: always on", "<code>grant</code>"):  # fmt: skip
        assert word in text, word
    assert text.count("Turn this off") == 6 and text.count("Turn this on") == 2
    got, _ = switch(browser, "turn_off", "jobs")
    assert got.status == 303 and got.getheader("Location") == "/tools"
    assert (runtime.state(box) / "tools.txt").read_text() == "-jobs\n"
    told = runtime.call(box, "job", "ls", door="mcp", where="/w", session="s")
    assert (told["state"], told["code"]) == ("refused", "tool_off")
    got, text = browser.ask("GET", "/tools")
    text = html.unescape(text)
    assert "Turned off. A model that asks for the jobs tools is refused" in text  # once
    assert (
        "A model is offered 8 tools now." in text and "Off: you turned it off" in text
    )
    switch(browser, "turn_on", "jobs")
    switch(browser, "turn_on", "sharing")
    got, text = browser.ask("GET", "/tools")
    assert "A model is offered 11 tools now." in html.unescape(text)
    assert kinds(box).count("seal") == 0  # a switch is beside the record, and no key


def test_the_core_and_anything_that_is_no_group_cannot_be_switched(box, browser):
    browser.open()
    for act, family in (("turn_off", "core"), ("turn_off", "seal"), ("turn_on", "../x"),
                        ("turn_off", "proposal:" + "0" * 64), ("switch", "jobs")):  # fmt: skip
        got, _ = switch(browser, act, family)
        assert got.status == 303, (act, family)
        _, text = browser.ask("GET", "/tools")
        assert "Nothing was done:" in html.unescape(text), (act, family)
    assert not (runtime.state(box) / "tools.txt").exists()
    got, text = browser.ask("GET", "/tools")
    assert "<script" not in text and text.count('value="core"') == 0  # no button for it


def test_the_tools_page_is_held_to_the_same_table(box, browser):
    got, text = browser.ask("GET", "/tools")  # no link opened yet
    assert got.status == 403 and "shelf" not in text
    got, _ = browser.click("turn_off", "jobs", k="wrong")
    assert got.status == 403
    got, _ = browser.click("turn_off", "jobs", origin="http://evil.example")
    assert got.status == 403
    assert not (runtime.state(box) / "tools.txt").exists()


def test_a_long_word_in_a_card_breaks_rather_than_widening_the_page():
    """A model's sentence quotes its page's seal, a 70-character id with no
    break, in a card's prose: at a phone's 390 pixels the page ran 137 too
    wide and scrolled sideways (seen in headless Chromium, 2026-11-20)."""
    import re

    (card,) = re.findall(r"\.card \{[^}]*\}", seal_page.CSS)
    assert "overflow-wrap: anywhere" in card


def test_the_kernels_counts_are_said_in_the_persons_words():
    said = seal_page.done_said({"bite: served": 4, "bite: empty": 2, "boot": 1,
                                "out": 4, "proposal: pass": 5, "seal": 1})  # fmt: skip
    assert said == ("6 questions asked of your files, 4 of them finding something; "
                    "5 things handed in for your seal; 1 sealed")  # fmt: skip
    assert seal_page.done_said({"bite: empty": 1}) == (
        "1 question asked of your files, 0 of them finding something"
    )
    assert seal_page.done_said({"odd": 2}) == "2 × odd"  # a kind it doesn't know
    assert seal_page.done_said({}) == ""


def test_a_note_is_headed_as_a_note_to_keep(box, browser):
    got = runtime.call(box, "capture", "Ring the plumber about the boiler.", door="mcp")
    assert got["state"] == "waiting", got
    browser.open()
    text = browser.page()
    assert "A note to keep" in text and "A suggestion" not in text
    assert "1 thing waits on your seal." in text
