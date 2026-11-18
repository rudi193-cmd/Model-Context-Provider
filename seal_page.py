"""seal_page.py: your seal, by a click, on this machine only. Python 3.9+.

    python seal_page.py --box DIR [--port N] [--no-open]

It prints a link and opens it in your browser. The page shows what waits on
your seal, each as what it is: a session's actions, a page a model would be
given (as it would leave, withheld), or a model's sentence. Under each:

- **Seal**: the kernel's own `seal`, proved with your key.
- **Decline**: the kernel's own `decline`, proved with your key, and final.
- **Not now**: nothing on your record and no key; it waits, and you aren't
  told again until you bring it back.

Ctrl-C stops it.

This is not a door. A door hands a model's request to the runtime; this
faces only you, and it is the one place in this project that carries out a
seal. It decides nothing: the decision is your click, and the seal is the
kernel's, run by its command line exactly as if you had typed it. The key is
read by the kernel and never by this file. No door imports it
(`tests/test_doors.py` fails one that does), so no model's door can reach it.

Who can reach it, and what stops each (Willow's browse keeps the same table):

- another computer: it listens on 127.0.0.1 only;
- another website in your browser: each start makes a new secret. The link
  hands it to your browser as an HttpOnly, SameSite=Strict cookie, and every
  form carries it too; without both, 403. A form whose Origin isn't this
  page (or is missing, or `null`) gets 403;
- a website renaming itself as this machine: a Host that isn't
  127.0.0.1:PORT or localhost:PORT gets 403;
- a website framing it under a button: frame-ancestors 'none' and
  X-Frame-Options: DENY;
- words in a passage or a model's sentence: every one is escaped, and the
  page allows no script at all, its own included;
- a program already running as you: nothing. It could run `kernel.py seal`
  itself, so the page gives it no reach it didn't have.
"""

from __future__ import annotations

import hmac
import html
import http.cookies
import http.server
import json
import re
import secrets
import sys
import urllib.parse
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime  # noqa: E402

SUBJECT = re.compile(r"proposal:[0-9a-f]{64}")
ACTS = ("seal", "decline", "later", "back")
MOST = 8192  # bytes of a form; ours are a few hundred

HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; style-src 'self'; form-action 'self'; "
        "frame-ancestors 'none'; base-uri 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    # same-origin, not no-referrer: under no-referrer Chromium sends
    # `Origin: null` on the page's own forms (found by Willow's browse)
    "Referrer-Policy": "same-origin",
    "Cache-Control": "no-store",
}

CSS = """
:root { color-scheme: light dark; --ink: #1c1b18; --soft: #6b675e;
  --paper: #f7f4ec; --card: #fffdf7; --line: #d9d3c3; --go: #2f5d3a;
  --no: #8a2c22; }
@media (prefers-color-scheme: dark) { :root { --ink: #ece8dc; --soft: #a39d8e;
  --paper: #191815; --card: #22201c; --line: #3a372f; --go: #8fc79c;
  --no: #e39a8f; } }
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 46rem; padding: 2rem 1rem 4rem;
  background: var(--paper); color: var(--ink);
  font: 1rem/1.5 Georgia, 'Iowan Old Style', serif; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; }
h2 { font-size: 1.1rem; margin: 0 0 .25rem; }
p { margin: .4rem 0; }
.soft, .kind { color: var(--soft); font-size: .9rem; }
.kind { text-transform: uppercase; letter-spacing: .06em; font-size: .75rem; }
.card { background: var(--card); border: 1px solid var(--line);
  border-radius: .5rem; padding: 1rem 1.25rem; margin: 1rem 0; }
.note { border-left: .25rem solid var(--go); }
.note.refused { border-left-color: var(--no); }
pre, blockquote { background: var(--paper); border: 1px solid var(--line);
  border-radius: .35rem; padding: .75rem; margin: .6rem 0; overflow-x: auto;
  white-space: pre-wrap; overflow-wrap: anywhere;
  font: .85rem/1.45 ui-monospace, Menlo, Consolas, monospace; }
blockquote { font: inherit; }
details { margin: .5rem 0; }
summary { cursor: pointer; color: var(--soft); font-size: .9rem; }
.acts { display: flex; flex-wrap: wrap; gap: .75rem 1.25rem;
  align-items: center; margin-top: .9rem; padding-top: .9rem;
  border-top: 1px solid var(--line); }
form { margin: 0; display: flex; align-items: center; gap: .5rem; }
button { font: inherit; padding: .4rem 1rem; border-radius: .35rem;
  border: 1px solid var(--line); background: var(--card); color: var(--ink);
  cursor: pointer; }
button.seal { background: var(--go); border-color: var(--go);
  color: var(--paper); font-weight: bold; }
button.decline { color: var(--no); border-color: var(--no); }
label { font-size: .85rem; color: var(--soft); }
dl { margin: .6rem 0; }
dt { color: var(--soft); font-size: .8rem; margin-top: .5rem; }
dd { margin: 0; overflow-wrap: anywhere; }
code { font: .8rem/1.4 ui-monospace, Menlo, Consolas, monospace;
  overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: .6rem 0;
  font-size: .9rem; }
th { text-align: left; color: var(--soft); font-size: .8rem;
  font-weight: normal; }
th, td { padding: .25rem .6rem .25rem 0; vertical-align: top;
  border-bottom: 1px solid var(--line); }
td:first-child { text-align: right; padding-right: 1rem;
  font-variant-numeric: tabular-nums; }
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def whole(box: Path, subject: str) -> dict:
    """A waiting proposal's own file: what the key would sign. Read, shown,
    and nothing else."""
    try:
        doc = json.loads((box / "proposals" / f"{subject[9:]}.json").read_text())
    except (OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


def held(data: str) -> str:
    """What a proposal holds, laid out to be read: a session's rows as a
    table (which row, what it was, its hash), other JSON a key a line, and
    words as words."""
    try:
        doc = json.loads(data)
    except ValueError:
        doc = None
    if not isinstance(doc, (dict, list)):
        return f"<pre>{esc(data.strip()[:20000])}</pre>"
    rows = doc.get("rows") if isinstance(doc, dict) else None
    if not (
        isinstance(rows, list)
        and all(isinstance(r, list) and len(r) == 3 for r in rows)
    ):
        return (
            f"<pre>{esc(json.dumps(doc, indent=2, ensure_ascii=False)[:20000])}</pre>"
        )
    said = []
    if "from" in doc and "to" in doc:
        said.append(f"Rows {esc(doc['from'])} to {esc(doc['to'])} of your record.")
    if doc.get("tip"):
        said.append(f"The record ended, at the last of them, at <code>{esc(doc['tip'])}</code>.")  # fmt: skip
    body = "".join(
        f"<tr><td>{esc(n)}</td><td>{esc(kind)}</td><td><code>{esc(h)}</code></td></tr>"
        for n, kind, h in rows[:2000]
    )
    more = f"<p class=\"soft\">…and {len(rows) - 2000} more rows.</p>" if len(rows) > 2000 else ""  # fmt: skip
    return (
        "".join(f"<p>{x}</p>" for x in said)
        + "<table><thead><tr><th>Row</th><th>What it was</th><th>Its hash on your "
        f"record</th></tr></thead><tbody>{body}</tbody></table>{more}"
    )


def exactly(box: Path, subject: str, prop: dict) -> str:
    """What the key would sign, said so it can be read: where it would be
    written, what it claims, what it holds; then the file itself, as it is."""
    try:
        raw = (box / "proposals" / f"{subject[9:]}.json").read_text()
    except OSError:
        raw = ""
    cites = prop.get("cites") or []
    facts = [
        ("Its name on your record", f"<code>{esc(subject)}</code>"),
        ("It says", esc(prop.get("claim", ""))),
        ("Sealing writes it to", f"<code>written/{esc(prop.get('path', ''))}</code>"),
        (
            "It cites",
            esc(
                f"{len(cites)} passage{'s' * (len(cites) != 1)} of your folder"
                if cites
                else "no passage of your folder"
            ),
        ),  # fmt: skip
        (
            "The question it was made under",
            f"<code>{esc(prop.get('bite_key', ''))}</code> (the question’s key; your "
            "record never keeps its words)",
        ),  # fmt: skip
    ]
    return (
        "<details><summary>Exactly what you’d be sealing</summary><dl>"
        + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in facts)
        + '</dl><p class="soft">What it holds:</p>'
        + held(str(prop.get("data", "")))
        + "<details><summary>The file itself, as it is kept</summary>"
        f"<pre>{esc(raw[:40000])}</pre></details></details>"
    )


def decide(box: Path, act: str, subject: str) -> dict:
    """Carry out what the person clicked, on one thing that waits on them.
    Seal and decline are the kernel's own, by its command line, on the Willow
    this was built on; the kernel reads the key and proves the row. Not now
    and its undoing are the runtime's, beside the record. Nothing else can be
    asked for, and nothing that isn't waiting can be named."""
    if act not in ACTS or not SUBJECT.fullmatch(subject):
        return {"state": "refused", "why": "that isn't something this page does"}
    if act in ("later", "back"):
        return runtime.call(box, act, subject, door="page")
    got = runtime.call(box, "waiting", door="page")
    if got.get("state") == "refused":  # Willow off its pin, or a broken record
        return got
    if subject not in {w["seal"] for w in got.get("waiting", [])}:
        return {"state": "refused", "why": "that isn't waiting on your seal"}
    run = runtime.willow("kernel.py", act, "--box", str(box), subject)
    if run.returncode != 0:
        why = (run.stderr or run.stdout).strip().removeprefix("refused: ")
        return {"state": "refused", "why": why or "the kernel refused"}
    return {"state": "sealed" if act == "seal" else "declined",
            "seal": subject, "said": run.stdout.strip()}  # fmt: skip


def note_of(got: dict) -> tuple[str, str]:
    """What to say back after a click, and whether it was a refusal."""
    state = got.get("state")
    if state == "sealed":
        said = got.get("said", "")
        where = said.split("; ", 1)[1] if "; " in said else ""
        return f"Sealed, with your key. {where}".strip(), ""
    if state == "declined":
        return "Declined, with your key. It won't be offered again.", ""
    if state == "later":
        return ("Set aside. Nothing was written on your record; it still waits, "
                "under “Set aside” below."), ""  # fmt: skip
    if state == "waiting":
        return "Brought back.", ""
    say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
    return "Nothing was done: " + (say or got.get("why") or "refused") + ".", "refused"


def kind_of(w: dict) -> str:
    path = str(w.get("path", ""))
    if path.startswith("sessions/"):
        return "session"
    if "preview" in w:
        return "page"
    if path.startswith("answers/"):
        return "sentence"
    return "suggestion"


def button(token: str, act: str, subject: str, words: str, sure: str = "") -> str:
    check = (f'<label><input type="checkbox" name="sure" value="yes" required> '
             f"{esc(sure)}</label>" if sure else "")  # fmt: skip
    return (
        '<form method="post" action="/act">'
        f'<input type="hidden" name="k" value="{esc(token)}">'
        f'<input type="hidden" name="act" value="{esc(act)}">'
        f'<input type="hidden" name="subject" value="{esc(subject)}">'
        f'<button class="{esc(act)}" type="submit">{esc(words)}</button>{check}</form>'
    )


def card(box: Path, token: str, w: dict) -> str:
    """One thing that waits, said as what it is, with what the key would sign
    folded under it. Every word from the box or a model is escaped."""
    subject, kind = w["seal"], kind_of(w)
    prop = whole(box, subject)
    data = str(prop.get("data", w.get("words", "")))
    if kind == "session":
        try:
            came = json.loads(data).get("came_of", {})
        except (ValueError, AttributeError):
            came = {}
        did = ", ".join(f"{n} × {k}" for k, n in sorted(came.items()))
        body = (
            '<p class="kind">A session</p>'
            f"<h2>{esc(w.get('claim') or 'A session’s actions')}</h2>"
            + (f"<p>What was done: {esc(did)}.</p>" if did else "")
            + '<p class="soft">Sealing says these actions were yours. It lets no '
            "page leave: a page leaves only on its own seal.</p>"
        )
        sealing = "Seal: these were my actions"
    elif kind == "page":
        got = runtime.call(box, "preview", subject, door="page")
        pv = (got.get("previews") or [{}])[0]
        n = pv.get("passages", 0)
        body = (
            '<p class="kind">A page to share</p>'
            f"<h2>{esc(n)} passage{'s' * (n != 1)} of your folder, for one "
            "question</h2>"
            '<p class="soft">This is the page as it would leave, with names, '
            "numbers and addresses withheld. Sealing lets it be given to a "
            "model for this question, whole, until it changes in your files or "
            "you stop it.</p>"
            f"<pre>{esc(pv.get('page', 'The page can’t be shown.'))}</pre>"
        )
        sealing = "Seal: share this page"
    elif kind == "sentence":
        body = (
            '<p class="kind">A model’s sentence</p>'
            f"<blockquote>{esc(data.strip())}</blockquote>"
            f'<p class="soft">{esc(w.get("claim", ""))}. Sealing keeps it in your '
            f"record, at {esc(w.get('path', ''))}.</p>"
        )
        sealing = "Seal: keep this sentence"
    else:
        body = (
            '<p class="kind">A suggestion</p>'
            f"<h2>{esc(w.get('claim') or 'A suggestion')}</h2>"
            f"<blockquote>{esc(data.strip()[:2000])}</blockquote>"
            f'<p class="soft">Sealing writes it to {esc(w.get("path", ""))}.</p>'
        )
        sealing = "Seal"
    exact = exactly(box, subject, prop)
    acts = (
        '<div class="acts">'
        + button(token, "seal", subject, sealing)
        + button(token, "later", subject, "Not now")
        + button(token, "decline", subject, "Decline", "final: never offered again")
        + "</div>"
    )
    return f'<section class="card">{body}{exact}{acts}</section>'


def page(box: Path, token: str, note: tuple[str, str] = ("", "")) -> str:
    """The whole page: what waits, then what was set aside. No script."""
    got = runtime.call(box, "waiting", door="page")
    parts = []
    if note[0]:
        parts.append(f'<section class="card note {esc(note[1])}">{esc(note[0])}</section>')  # fmt: skip
    if got.get("state") == "refused":
        say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
        parts.append(f'<section class="card note refused">{esc(say)}</section>')
    items = got.get("waiting", [])
    now = [w for w in items if not w.get("later")]
    aside = [w for w in items if w.get("later")]
    if not now and got.get("state") != "refused":
        parts.append(
            f'<section class="card">Nothing {"else " * bool(aside)}waits on your '
            "seal.</section>"
        )
    parts += [card(box, token, w) for w in now]
    if aside:
        rows = "".join(
            f'<div class="acts"><span>{esc(w.get("claim") or kind_of(w))}</span>'
            + button(token, "back", w["seal"], "Bring back")
            + "</div>"
            for w in aside
        )
        parts.append(
            f'<section class="card"><details><summary>Set aside: {len(aside)}, '
            f"still waiting</summary>{rows}</details></section>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Waiting on your seal</title><link rel="stylesheet" href="/style.css">'
        "</head><body><h1>Waiting on your seal</h1>"
        f'<p class="soft">Your record: {esc(box)}. This page is on this machine '
        "only. A seal or a decline is proved with your key, which this page "
        "never reads, shows or sends.</p>" + "".join(parts) + "</body></html>"
    )


def handler(box: Path, secret: str):
    """The page's requests, each held to the table at the top of this file
    before anything is read or done."""

    class Page(http.server.BaseHTTPRequestHandler):
        server_version = "seal-page"
        note = ("", "")  # what the last click did, shown once

        def log_message(self, *a):  # the link holds the secret: log nothing
            pass

        def say(self, code: int, body: str, kind: str = "text/html", extra=()):
            raw = body.encode()
            self.send_response(code)
            for k, v in (*HEADERS.items(), *extra):
                self.send_header(k, v)
            self.send_header("Content-Type", f"{kind}; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def no(self, why: str):
            self.say(403, f"403: {why}\n", "text/plain")

        def here(self) -> bool:
            port = self.server.server_address[1]
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")  # fmt: skip

        def knows(self) -> bool:
            jar = http.cookies.SimpleCookie()
            try:
                jar.load(self.headers.get("Cookie", ""))
            except http.cookies.CookieError:
                return False
            got = jar["seal"].value if "seal" in jar else ""
            return hmac.compare_digest(got.encode(), secret.encode())

        def do_GET(self):
            if not self.here():
                return self.no("this page answers only as this machine")
            url = urllib.parse.urlsplit(self.path)
            given = urllib.parse.parse_qs(url.query).get("k", [""])[0]
            if url.path == "/" and given:
                if not hmac.compare_digest(given.encode(), secret.encode()):
                    return self.no("that link is from another start of this page")
                cookie = f"seal={secret}; HttpOnly; SameSite=Strict; Path=/"
                return self.say(303, "", extra=(("Set-Cookie", cookie), ("Location", "/")))  # fmt: skip
            if not self.knows():
                return self.no("open the link this page printed when it started")
            if url.path == "/style.css":
                return self.say(200, CSS, "text/css")
            if url.path != "/":
                return self.say(404, "404\n", "text/plain")
            note, Page.note = Page.note, ("", "")
            self.say(200, page(box, secret, note))

        def do_POST(self):
            port = self.server.server_address[1]
            if not self.here():
                return self.no("this page answers only as this machine")
            if self.headers.get("Origin") not in (
                f"http://127.0.0.1:{port}", f"http://localhost:{port}"
            ):  # fmt: skip
                return self.no("that form isn't this page's")
            if not self.knows():
                return self.no("open the link this page printed when it started")
            try:
                size = int(self.headers.get("Content-Length", ""))
            except ValueError:
                size = -1
            if self.path != "/act" or not 0 <= size <= MOST:
                return self.no("that isn't one of this page's forms")
            form = urllib.parse.parse_qs(
                self.rfile.read(size).decode("utf-8", "replace")
            )
            one = {k: v[0] for k, v in form.items() if len(v) == 1}
            if not hmac.compare_digest(one.get("k", "").encode(), secret.encode()):
                return self.no("that form isn't this page's")
            act, subject = one.get("act", ""), one.get("subject", "")
            if act == "decline" and one.get("sure") != "yes":
                Page.note = ("Nothing was done: tick the box beside Decline to "
                             "say you mean it; a decline is final.", "refused")  # fmt: skip
            else:
                Page.note = note_of(decide(box, act, subject))
            self.say(303, "", extra=(("Location", "/"),))

    return Page


def serve(box: Path, port: int = 0):
    """The server, bound to this machine only, and the link that opens it."""
    secret = secrets.token_urlsafe(32)
    server = http.server.HTTPServer(("127.0.0.1", port), handler(box, secret))
    return server, f"http://127.0.0.1:{server.server_address[1]}/?k={secret}"


def main(argv: list[str]) -> int:
    opts, it = {"--port": "0"}, iter(argv)
    for a in it:
        if a in ("--box", "--port"):
            opts[a] = next(it, "")
        elif a == "--no-open":
            opts[a] = "yes"
        else:
            opts["bad"] = a
    if "bad" in opts or not opts.get("--box") or not opts["--port"].isdigit():
        print("usage: seal_page.py --box DIR [--port N] [--no-open]", file=sys.stderr)
        return 2
    box = Path(opts["--box"]).resolve()
    if not (box / "kernel.json").is_file():
        print(f"There's no record at {box}. Name your record with --box.", file=sys.stderr)  # fmt: skip
        return 2
    try:
        server, link = serve(box, int(opts["--port"]))
    except OSError as why:
        print(f"The page couldn't start: {why}. Try another --port.", file=sys.stderr)
        return 2
    print(f"Your seal page, on this machine only:\n\n  {link}\n\nCtrl-C stops it.", flush=True)  # fmt: skip
    if "--no-open" not in opts:
        webbrowser.open(link)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Whatever you didn't seal still waits.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
