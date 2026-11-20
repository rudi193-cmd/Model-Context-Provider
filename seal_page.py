"""seal_page.py: your seal, by a click, on this machine only. Python 3.9+.

    python seal_page.py --box DIR [--port N] [--no-open] [--idle MINUTES]
    python seal_page.py launcher --box DIR [--write]

It prints a link and opens it in your browser. The page shows what waits on
your seal, each as what it is: a session's actions, a page a model would be
given (as it would leave, withheld), or a model's sentence. Under each:

- **Seal**: the kernel's own `seal`, proved with your key.
- **Decline**: the kernel's own `decline`, proved with your key, and final.
- **Not now**: nothing on your record and no key; it waits, and you aren't
  told again until you bring it back.

A second page, "What you've shared", lists every page you were asked to
share and where it stands, with **Stop** under each (never given to a model
again; no key, since refusing to send only makes things safer), and what
has left, to whom and when.

Ctrl-C stops it, and so does "Close this page"; with `--idle MINUTES` it
stops itself when nobody has asked it anything for that long.

`launcher` prints a file that starts this page with a double-click, for
macOS, Windows and Linux, and says where to save each. With `--write` it
saves the one for this machine, and never over a file that differs.

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
import platform
import re
import secrets
import shlex
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import runtime  # noqa: E402

SUBJECT = re.compile(r"proposal:[0-9a-f]{64}")
ACTS = ("seal", "decline", "later", "back", "stop", "turn_on", "turn_off")
PAGES = ("/", "/shared", "/status", "/promises", "/tools")
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
/* the page is as wide as its window, so a page or a report to seal is read
   whole; only running prose is kept to a line a person reads easily */
body { margin: 0; padding: 2rem clamp(1rem, 4vw, 4rem) 4rem;
  background: var(--paper); color: var(--ink);
  font: 1rem/1.5 Georgia, 'Iowan Old Style', serif; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; }
h2 { font-size: 1.1rem; margin: 0 0 .25rem; }
p { margin: .4rem 0; max-width: 46rem; }
.soft, .kind { color: var(--soft); font-size: .9rem; }
.kind { text-transform: uppercase; letter-spacing: .06em; font-size: .75rem; }
/* a seal's id or a long path in a card's prose breaks rather than widening
   the page: on a phone it scrolled sideways (seen 2026-11-20) */
.card { background: var(--card); border: 1px solid var(--line);
  border-radius: .5rem; padding: 1rem 1.25rem; margin: 1rem 0;
  overflow-wrap: anywhere; }
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
nav.top { border: 0; margin: 0 0 1.5rem; padding: 0;
  justify-content: space-between; font-size: .95rem; }
a { color: inherit; }
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
    if act in ("turn_on", "turn_off"):  # a group of tools: the runtime's switch
        if subject not in runtime.FAMILIES:
            return {"state": "refused", "why": "that isn't a group of tools"}
        asked = {"on" if act == "turn_on" else "off": [subject]}
        got = runtime.call(box, "tools", asked, door="page")
        if got.get("state") != "listed":
            return got
        return {"state": "switched", "family": subject, "on": act == "turn_on"}
    if act not in ACTS or not SUBJECT.fullmatch(subject):
        return {"state": "refused", "why": "that isn't something this page does"}
    if act in ("later", "back", "stop"):  # the runtime's, and no key
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
    if state == "stopped":
        return ("Stopped. It won't be given to a model again. To share it again, "
                "ask the question in other words, and seal that."), ""  # fmt: skip
    if state == "switched":
        if got.get("on"):
            return (f"Turned on. A model is offered the {got['family']} tools from "
                    "now on; a client that is open is told the list changed."), ""  # fmt: skip
        return (f"Turned off. A model that asks for the {got['family']} tools is "
                "refused from now on, by any door."), ""  # fmt: skip
    say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
    return "Nothing was done: " + (say or got.get("why") or "refused") + ".", "refused"


# What each of sentence-check's checks holds, said plainly and no larger than
# it is (it checks words and numbers, not what a sentence means).
CHECKED = {
    "every cite was served": "Every passage it cites is one on the page you sealed.",
    "every box cited": "Every passage on that page is cited.",
    "nothing the boxes lack": "No number or word in it is missing from that "
    "page (bar small joining words).",
    "your words quoted exactly": "Anything it puts in quotes is in your own "
    "words, exactly.",
}


def checked(kept) -> str:
    """The lines under a sentence: each check that was run, from what it said.
    A check that held is said by what it holds; one that said anything else is
    shown as it said it. No record of them says so, and never that it passed."""
    rows = kept.get("checks") if isinstance(kept, dict) else None
    head = "<p><b>What code checked before this reached you</b></p>"
    if not isinstance(rows, list) or not rows:
        return (
            head + '<p class="soft">The record of its checks isn’t kept for '
            "this sentence, so it can’t be shown here that any passed.</p>"
        )
    lines = []
    for r in rows:
        name, said = str(r.get("name", "")), str(r.get("said", ""))
        if said == "held" and name in CHECKED:
            lines.append(f"{CHECKED[name]} (held)")
        elif said == "nothing quoted" and name in CHECKED:
            lines.append("It quotes no one, so there was nothing to check there.")
        else:
            lines.append(f"{name}: {said}")
    return (
        head + "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in lines) + "</ul>"
        '<p class="soft">This checks words and numbers against the page. It '
        "doesn’t check that the sentence is true, or what it means.</p>"
        + left_out(kept)
    )


def left_out(kept: dict) -> str:
    """What was on the sealed page and isn't in the sentence. A sentence may
    cite only some of its page (the owner's ruling, 2026-11-19), so what it
    leaves out is shown beside it: by file and the passage's id, never its
    words, since the record of the checks keeps none. A sentence kept before
    that ruling has no list, and cited its whole page."""
    left = kept.get("left_out")
    if not isinstance(left, list):
        return ""
    if not left:
        return "<p>It cites every passage on the page you sealed.</p>"
    rows = "".join(
        f"<li>{esc(str(b.get('file') or 'a passage'))} "
        f'<span class="soft">({esc(str(b.get("id", "")))})</span></li>'
        for b in left
        if isinstance(b, dict)
    )
    of = kept.get("passages")
    total = f" of the {of} on the page" if isinstance(of, int) else ""
    return (
        f"<p><b>Left out: {len(left)}{total}</b></p><ul>{rows}</ul>"
        '<p class="soft">The sentence says nothing of these. A sentence can '
        "mislead by what it leaves out, so read them in your files before "
        "you keep it.</p>"
    )


def kind_of(w: dict) -> str:
    path = str(w.get("path", ""))
    if path.startswith("sessions/"):
        return "session"
    if "preview" in w:
        return "page"
    if path.startswith("answers/"):
        return "sentence"
    if path.startswith("reports/"):
        return "report"
    if path.startswith("tasks/"):
        return "task"
    if path.startswith("skills/"):
        return "skill"
    if path.startswith("grants/"):
        return "grant"
    if path.startswith("shares/"):
        return "share"
    return "suggestion"


def button(
    token: str, act: str, subject: str, words: str, sure: str = "", at: str = "/"
) -> str:
    check = (f'<label><input type="checkbox" name="sure" value="yes" required> '
             f"{esc(sure)}</label>" if sure else "")  # fmt: skip
    return (
        '<form method="post" action="/act">'
        f'<input type="hidden" name="k" value="{esc(token)}">'
        f'<input type="hidden" name="act" value="{esc(act)}">'
        f'<input type="hidden" name="subject" value="{esc(subject)}">'
        f'<input type="hidden" name="at" value="{esc(at)}">'
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
            bundle = json.loads(data)
            came = bundle.get("came_of", {})
            said = [str(t) for t in bundle.get("corrections", []) if isinstance(t, str)]
        except (ValueError, AttributeError):
            came, said = {}, []
        did = ", ".join(f"{n} × {k}" for k, n in sorted(came.items()))
        body = (
            '<p class="kind">A session</p>'
            f"<h2>{esc(w.get('claim') or 'A session’s actions')}</h2>"
            + (f"<p>What was done: {esc(did)}.</p>" if did else "")
            + (
                "<p><b>What you said to correct the assistant</b></p><ul>"
                + "".join(f"<li>{esc(t)}</li>" for t in said)
                + "</ul>"
                + '<p class="soft">Each was caught by its words. Sealing keeps '
                "them with the session; one that wasn’t a correction is kept "
                "as it was said, and goes nowhere else.</p>"
                if said
                else ""
            )
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
            + checked(w.get("checks"))
            + f'<p class="soft">{esc(w.get("claim", ""))}. Sealing keeps it in your '
            f"record, at {esc(w.get('path', ''))}.</p>"
        )
        sealing = "Seal: keep this sentence"
    elif kind == "report":
        body = (
            '<p class="kind">A report to share</p>'
            f"<h2>{esc(w.get('claim') or 'A report from your files')}</h2>"
            '<p class="soft">These are lines of your own files, as they would '
            "leave, with names, numbers and addresses withheld. This one was "
            "asked for before a report stopped waiting on a seal of its own: "
            "sealing it now gives it to no one. A session you let in is given "
            "a report as it reads; decline this to clear it.</p>"
            f"<pre>{esc(data.strip())}</pre>"
        )
        sealing = "Seal: share this report"
    elif kind == "task":
        folder, said = runtime.task_parse(data)
        by = "a model proposed" if "/model-" in str(w.get("path", "")) else "you wrote"
        body = (
            '<p class="kind">A task to do</p>'
            f"<h2>{esc(w.get('claim') or 'A task')}</h2>"
            f"<blockquote>{esc(said)}</blockquote>"
            f'<p class="soft">This task: {esc(by)}. For: '
            f"{esc('any project' if folder == 'any' else folder)}. Sealing says "
            "yes, do this: a session in that project may be given these words, "
            "withheld as a page is, and may claim the task. It grants no tool, "
            "no file and no leave: the guard still holds every tool call, and "
            "what is done is still closed over for one seal.</p>"
        )
        sealing = "Seal: yes, do this"
    elif kind == "skill":
        body = (
            '<p class="kind">A skill to give a model</p>'
            f"<h2>{esc(w.get('claim') or 'A skill')}</h2>"
            '<p class="soft">These are instructions. A model that asks for this '
            "skill by name will be given exactly these words and may follow "
            "them, so read them as you would anything you let run: what they "
            "tell it to do, and what they tell it to reach for. Sealing covers "
            "these words alone. If the file changes afterwards, the skill is "
            "given to no one until you name it again and seal what it then "
            "says.</p>"
            f"<pre>{esc(data.strip())}</pre>"
        )
        sealing = "Seal: give this skill"
    elif kind == "share":
        body = (
            '<p class="kind">A package to send someone</p>'
            f"<h2>{esc(w.get('claim') or 'A package')}</h2>"
            '<p class="soft">A model put this together from sentences you '
            "already sealed. If you say yes, exactly these sentences are packed "
            "for the person named, signed with your sharing identity (not your "
            "seal key), into a file beside your record, and a row is written on "
            "your record. Nothing is sent: the file is yours to pass on. Check "
            "the name and the key are who you mean.</p>"
            f"<pre>{esc(data.strip())}</pre>"
        )
        sealing = "Seal: pack this"
    elif kind == "grant":
        folder = next(
            (ln[5:] for ln in data.splitlines() if ln.startswith("for: ")), "?"
        )
        body = (
            '<p class="kind">A session asking to read your files</p>'
            f"<h2>{esc(folder)}</h2>"
            '<p class="soft">An assistant session working in this folder asks to '
            "read from your files. If you say yes, it is answered directly "
            "until that session ends: what your files hold on what it asks, "
            "and what a job it runs in the sandbox prints, with names and "
            "numbers withheld. You are not asked again for each one. "
            "Everything it is given is on your shared page, and you can stop "
            "it there at any time. It ends by itself when the session does."
            "</p>"
        )
        sealing = "Seal: yes, for this session"
    else:
        body = (
            '<p class="kind">A suggestion</p>'
            f"<h2>{esc(w.get('claim') or 'A suggestion')}</h2>"
            f"<blockquote>{esc(data.strip()[:2000])}</blockquote>"
            f'<p class="soft">Sealing writes it to {esc(w.get("path", ""))}.'
            + (
                " A model may then be given this note, withheld as a page is."
                if str(w.get("path", "")).startswith("captured/note-")
                else ""
            )
            + "</p>"
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
    return shell(box, token, "/", parts)


def shell(box: Path, token: str, at: str, parts: list[str]) -> str:
    """Any page, whole: its name, the way to the others, and a way to stop."""
    titles = {"/": "Waiting on your seal", "/shared": "What you’ve shared",
              "/status": "How things stand",
              "/promises": "What a model can never do",
              "/tools": "What a model is offered"}  # fmt: skip
    nav = " · ".join(
        f"<strong>{esc(t)}</strong>" if href == at else f'<a href="{href}">{esc(t)}</a>'
        for href, t in titles.items()
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{esc(titles[at])}</title>"
        '<link rel="stylesheet" href="/style.css">'
        f'</head><body><nav class="acts top"><span>{nav}</span>'
        + button(token, "quit", "", "Close this page")
        + f"</nav><h1>{esc(titles[at])}</h1>"
        f'<p class="soft">Your record: {esc(box)}. This page is on this machine '
        "only. A seal or a decline is proved with your key, which this page "
        "never reads, shows or sends.</p>" + "".join(parts) + "</body></html>"
    )


def shared_page(box: Path, token: str, note: tuple[str, str] = ("", "")) -> str:
    """Every page the person was asked to share and where it stands, each
    with a way to stop it; then what has left, to whom and when."""
    parts = []
    if note[0]:
        parts.append(f'<section class="card note {esc(note[1])}">{esc(note[0])}</section>')  # fmt: skip
    got = runtime.call(box, "scopes", door="page")
    if got.get("state") == "refused":
        say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
        parts.append(f'<section class="card note refused">{esc(say)}</section>')
    elif not got.get("scopes"):
        parts.append('<section class="card">You haven’t been asked to share a page yet.</section>')  # fmt: skip
    for sc in got.get("scopes", []):
        subject, stands = sc["seal"], str(sc.get("stands", ""))
        pv = runtime.call(box, "preview", subject, door="page")
        text = (pv.get("previews") or [{}])[0].get("page", "The page can’t be shown.")
        places = "; ".join(sc.get("places", []))
        stop = (
            ""
            if stands.startswith("stopped")
            else '<div class="acts">'
            + button(token, "stop", subject, "Stop sharing this", at="/shared")
            + '<span class="soft">it is never given to a model again</span></div>'
        )
        parts.append(
            '<section class="card"><p class="kind">A page to share</p>'
            f"<h2>{esc(places)}</h2><p>{esc(stands[:1].upper() + stands[1:])}.</p>"
            f"<details><summary>What this page holds</summary><pre>{esc(text)}</pre>"
            f'<p class="soft">Its name on your record: <code>{esc(subject)}</code></p>'
            f"</details>{stop}</section>"
        )
    log = runtime.call(box, "shared", door="page")
    lines = log.get("lines", [])
    if lines:
        last = "\n".join(reversed(lines[-300:]))
        parts.append(
            '<section class="card"><p class="kind">What has left</p>'
            f"<h2>{len(lines)} line{'s' * (len(lines) != 1)}, the newest first</h2>"
            '<p class="soft">Each time a model was told anything, or a page left: '
            "when, to whom, and what, by file and line.</p>"
            f"<pre>{esc(last)}</pre></section>"
        )
    return shell(box, token, "/shared", parts)


def status_page(box: Path, token: str, note: tuple[str, str] = ("", "")) -> str:
    """How things stand, in one look: the runtime's `status`, each part a
    card. It only shows; nothing on it seals, stops or changes anything."""
    parts = []
    if note[0]:
        parts.append(f'<section class="card note {esc(note[1])}">{esc(note[0])}</section>')  # fmt: skip
    got = runtime.call(box, "status", door="page")
    if got.get("state") == "refused":
        say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
        parts.append(f'<section class="card note refused">{esc(say)}</section>')
    else:
        said = str(got.get("said", ""))
        parts.append(f'<section class="card">{esc(said[:1].upper() + said[1:])}.</section>')  # fmt: skip
    for g in got.get("groups", []):
        rows = "".join(
            f"<tr><th>{esc(r['where'])}</th><td>{esc(r['what'])}</td></tr>"
            for r in g["rows"]
        )
        parts.append(
            f'<section class="card"><p class="kind">{esc(g["name"])}</p>'
            f"<table>{rows}</table></section>"
        )
    return shell(box, token, "/status", parts)


def tools_page(box: Path, token: str, note: tuple[str, str] = ("", "")) -> str:
    """Which groups of tools a model is offered: the runtime's `tools`, a
    card for each group with what it is for, the tools in it, whether it is
    on and why, and a button to switch it. The switch is the runtime's, kept
    beside the record; no key is needed, and the core has no button."""
    parts = []
    if note[0]:
        parts.append(f'<section class="card note {esc(note[1])}">{esc(note[0])}</section>')  # fmt: skip
    got = runtime.call(box, "tools", door="page")
    if got.get("state") == "refused":
        say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
        parts.append(f'<section class="card note refused">{esc(say)}</section>')
    groups = got.get("families", [])
    offered = sum(len(g["tools"]) for g in groups if g["on"])
    if groups:
        parts.append(
            f'<section class="card">A model is offered {offered} tool'
            f"{'s' * (offered != 1)} now. Fewer is easier for it to keep track "
            "of, and each tool’s description is sent to it at the start of "
            "every session. A group you turn off is refused, not only left "
            "off its list. Your own door is not affected.</section>"
        )
    for g in groups:
        held = []
        for name in g["tools"]:
            actions = [a for a in runtime.TOOLS[name][1] if a]
            held.append(f"<code>{esc(name)}</code>"
                        + (f" ({esc(', '.join(actions))})" if actions else ""))  # fmt: skip
        switch = ""
        if g["family"] != "core":
            switch = '<div class="acts">' + button(
                token, "turn_off" if g["on"] else "turn_on", g["family"],
                "Turn this off" if g["on"] else "Turn this on", at="/tools",
            ) + "</div>"  # fmt: skip
        parts.append(
            f'<section class="card"><p class="kind">{"On" if g["on"] else "Off"}'
            f": {esc(g['why'])}</p><h2>{esc(g['family'])}</h2>"
            f"<p>{esc(g['what'][:1].upper() + g['what'][1:])}.</p>"
            f'<p class="soft">Tools: {", ".join(held)}</p>{switch}</section>'
        )
    return shell(box, token, "/tools", parts)


def promises_page(box: Path, token: str, note: tuple[str, str] = ("", "")) -> str:
    """What a model can never do, from the code itself: the runtime's
    `promises`, each part a card. It only shows; nothing on it changes anything."""
    parts = []
    if note[0]:
        parts.append(f'<section class="card note {esc(note[1])}">{esc(note[0])}</section>')  # fmt: skip
    got = runtime.call(box, "promises", door="page")
    if got.get("state") == "refused":
        say = " ".join(x for x in (got.get("say"), got.get("next")) if x)
        parts.append(f'<section class="card note refused">{esc(say)}</section>')
    else:
        said = str(got.get("said", ""))
        parts.append(f'<section class="card">{esc(said[:1].upper() + said[1:])}.</section>')  # fmt: skip
    for g in got.get("groups", []):
        rows = "".join(
            f"<tr><th>{esc(r['where'])}</th><td>{esc(r['what'])}</td></tr>"
            for r in g["rows"]
        )
        parts.append(
            f'<section class="card"><p class="kind">{esc(g["name"])}</p>'
            f"<table>{rows}</table></section>"
        )
    return shell(box, token, "/promises", parts)


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
            if url.path not in PAGES:
                return self.say(404, "404\n", "text/plain")
            self.server.last = time.monotonic()
            note, Page.note = Page.note, ("", "")
            show = {"/": page, "/shared": shared_page, "/status": status_page,
                    "/promises": promises_page, "/tools": tools_page}  # fmt: skip
            self.say(200, show[url.path](box, secret, note))

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
            self.server.last = time.monotonic()
            if act == "quit":  # stops the page; touches nothing
                self.server.done = True
                return self.say(200, "Closed. Whatever you didn't seal still waits. "
                                "You can close this tab.\n", "text/plain")  # fmt: skip
            if act == "decline" and one.get("sure") != "yes":
                Page.note = ("Nothing was done: tick the box beside Decline to "
                             "say you mean it; a decline is final.", "refused")  # fmt: skip
            else:
                Page.note = note_of(decide(box, act, subject))
            at = one.get("at") if one.get("at") in PAGES else "/"
            self.say(303, "", extra=(("Location", at),))

    return Page


def serve(box: Path, port: int = 0):
    """The server, bound to this machine only, and the link that opens it."""
    secret = secrets.token_urlsafe(32)
    server = http.server.HTTPServer(("127.0.0.1", port), handler(box, secret))
    server.done, server.last = False, time.monotonic()
    return server, f"http://127.0.0.1:{server.server_address[1]}/?k={secret}"


def run(server, idle: float = 0) -> str:
    """Answer until the person closes the page, or (with idle, in seconds)
    nobody has asked it anything for that long. Says which."""
    server.timeout = 0.5
    while not server.done:
        server.handle_request()
        if idle and time.monotonic() - server.last > idle:
            return "idle"
    return "closed"


NAME = "Seal page"


def desktop_arg(a: str) -> str:
    """One argument of a .desktop file's Exec line: quoted, its reserved
    characters escaped, then the escapes a desktop file's strings take."""
    a = re.sub(r'(["`$\\])', r"\\\1", a)
    return '"' + a.replace("\\", "\\\\").replace("%", "%%") + '"'


def launchers(box: Path, home: Path) -> dict[str, tuple[Path, str]]:
    """For each system, the file that starts this page with a double-click
    and where it goes. Each names this Python, this file, this Willow and
    this record by their whole paths, and stops itself after half an hour
    with nobody asking."""
    argv = [sys.executable or "python3", str(HERE / "seal_page.py"),
            "--box", str(box.resolve()), "--idle", "30"]  # fmt: skip
    willow = f"WILLOW={Path(runtime.WILLOW).resolve()}"
    return {
        "Darwin": (
            home / "Desktop" / f"{NAME}.command",
            f"#!/bin/sh\n{shlex.quote(willow)} exec {shlex.join(argv)}\n",
        ),
        "Windows": (
            home / "Desktop" / f"{NAME}.bat",
            f'@echo off\r\nset "{willow}"\r\n{subprocess.list2cmdline(argv)}\r\n',
        ),
        "Linux": (
            home / ".local/share/applications/model-context-provider-seal.desktop",
            "[Desktop Entry]\nType=Application\n"
            f"Name={NAME}\nComment=Read and seal what waits on you, on this "
            "machine only\nTerminal=false\nCategories=Utility;\n"
            f"Exec=env {' '.join(desktop_arg(a) for a in [willow, *argv])}\n",
        ),
    }


def launcher(box: Path, write: bool, home: Path, system: str) -> tuple[int, str]:
    """Print each system's launcher and where to save it; or, with write,
    save this machine's: never over a file that differs."""
    all_ = launchers(box, home)
    if not write:
        names = {"Darwin": "macOS"}
        return 0, "\n".join(
            f"{names.get(sysname, sysname)}: save as {to}"
            + ("; then in Terminal once: chmod +x on it" if sysname == "Darwin" else "")
            + f"\n\n{text}"
            for sysname, (to, text) in all_.items()
        )
    if system not in all_:
        return 2, f"There's no launcher for {system}; start the page from a terminal."
    to, text = all_[system]
    if to.exists():
        if to.read_bytes() == text.encode():
            return 0, f"Already there: {to}"
        return 2, (f"{to} is there already and differs, and it's never written "
                   "over. Move it away first, if you mean this one to win.")  # fmt: skip
    to.parent.mkdir(parents=True, exist_ok=True)
    with open(to, "xb") as f:
        f.write(text.encode())
    if system != "Windows":
        to.chmod(0o755)
    where = ("your applications menu, as “Seal page”" if system == "Linux"
             else "your Desktop")  # fmt: skip
    return 0, f"Saved {to}\nLook for it in {where}."


USAGE = (
    "usage: seal_page.py --box DIR [--port N] [--no-open] [--idle MINUTES]\n"
    "       seal_page.py launcher --box DIR [--write]"
)


def main(argv: list[str]) -> int:
    launch = argv[:1] == ["launcher"]
    opts, it = {"--port": "0", "--idle": "0"}, iter(argv[1:] if launch else argv)
    for a in it:
        if a in ("--box", "--port", "--idle"):
            opts[a] = next(it, "")
        elif a in ("--no-open", "--write"):
            opts[a] = "yes"
        else:
            opts["bad"] = a
    if (
        "bad" in opts
        or not opts.get("--box")
        or not opts["--port"].isdigit()
        or not opts["--idle"].isdigit()
        or ("--write" in opts) > launch
    ):
        print(USAGE, file=sys.stderr)
        return 2
    box = Path(opts["--box"]).resolve()
    if not (box / "kernel.json").is_file():
        print(f"There's no record at {box}. Name your record with --box.", file=sys.stderr)  # fmt: skip
        return 2
    if launch:
        code, said = launcher(box, "--write" in opts, Path.home(), platform.system())
        print(said, file=sys.stderr if code else sys.stdout)
        return code
    try:
        server, link = serve(box, int(opts["--port"]))
    except OSError as why:
        print(f"The page couldn't start: {why}. Try another --port.", file=sys.stderr)
        return 2
    print(f"Your seal page, on this machine only:\n\n  {link}\n\nCtrl-C stops it.", flush=True)  # fmt: skip
    if "--no-open" not in opts:
        webbrowser.open(link)
    try:
        why = run(server, int(opts["--idle"]) * 60)
        print("Stopped: " + ("nobody asked for a while." if why == "idle"
                             else "you closed the page.")
              + " Whatever you didn't seal still waits.")  # fmt: skip
    except KeyboardInterrupt:
        print("\nStopped. Whatever you didn't seal still waits.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
