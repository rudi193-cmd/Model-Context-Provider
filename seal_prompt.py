"""seal_prompt.py: one question, in a dialog on your own desktop. Python 3.9+.

    python seal_prompt.py --box DIR --seal proposal:<sha256> [--pinentry PROGRAM]

When a session asks to read from your files, this asks you there and then,
in the system's own pinentry dialog (the one that asks for a passphrase,
here asking only yes or no), with three answers:

- **Seal: yes, for this session**: the kernel's own `seal`, proved with your key.
- **Decline**: the kernel's own `decline`, proved with your key, and final.
- **Not now** (or closing it, or leaving it): nothing happens. It waits on
  your seal page as before.

It asks about a session's grant and nothing else: anything else that waits
on you is read on the seal page, where there is room to read it.

This is not a door. Like seal_page.py, it faces only you and decides
nothing: the decision is your click in a dialog that no session's process
drew or can answer, and the seal is the kernel's, run by its command line
exactly as if you had typed it. The key is read by the kernel and never by
this file. No door imports it (`tests/test_doors.py` fails one that does).
The runtime starts it, as a program of its own, only where you turned it
on: a file named `ask-here` beside your record.

What it can't promise: a plain yes-or-no dialog proves that someone at this
desktop clicked, not who. A program that can click on your screen could
click it. A passphrase would hold against that; this was chosen for being
one click.

Exit codes: 0 sealed or declined; 42 not now (it still waits); 2 refused
(not a grant that waits, or no pinentry to ask with).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import runtime
import seal_page

PROGRAMS = ("pinentry", "pinentry-gnome3", "pinentry-qt", "pinentry-gtk-2",
            "pinentry-x11", "pinentry-mac")  # fmt: skip
NOT_CONFIRMED = 114  # the dialog's second button, as pinentry reports it
WAIT = 300  # seconds a dialog nobody answers is left up


def esc(text: str) -> str:
    """Text as pinentry's protocol carries it on one line."""
    return text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")


def ask(program: str, title: str, words: str) -> str:
    """ "seal", "decline" or "hold": what the person clicked. Anything that
    isn't a clear yes or a clear no is hold."""
    said = "\n".join([
        f"SETTITLE {esc(title)}", f"SETDESC {esc(words)}",
        "SETOK Seal: yes, for this session", "SETNOTOK Decline",
        "SETCANCEL Not now", f"SETTIMEOUT {WAIT}", "CONFIRM", "BYE", "",
    ])  # fmt: skip
    try:
        run = subprocess.run([program], input=said, capture_output=True, text=True,
                             timeout=WAIT + 30, check=False)  # fmt: skip
    except (OSError, subprocess.TimeoutExpired):
        return "hold"
    # every line it said, in order: a greeting, six settings, then the answer
    # to CONFIRM. Anything out of place is not a yes: a line that is neither
    # OK nor ERR must never let a later OK stand in for the answer.
    got = [ln.strip() for ln in run.stdout.splitlines()]  # blank lines too
    if len(got) < 8 or any(not ln.startswith("OK") for ln in got[:7]):
        return "hold"
    answer = got[7].split()
    if not answer:
        return "hold"
    if answer[0] == "OK":
        return "seal"
    if (answer[0] == "ERR" and len(answer) > 1 and answer[1].isdigit()
            and int(answer[1]) & 0xFFFF == NOT_CONFIRMED):  # fmt: skip
        return "decline"
    return "hold"


def grant_waiting(box: Path, subject: str) -> dict | None:
    """The session's grant that waits under this subject, or None: this
    program asks about nothing else."""
    got = runtime.call(box, "waiting", door="page")
    for w in got.get("waiting", []):
        if w.get("seal") == subject and str(w.get("path", "")).startswith("grants/"):
            return w
    return None


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[::2], argv[1::2]))
    if (len(argv) % 2 or not {"--box", "--seal"} <= opts.keys()
            or not opts.keys() <= {"--box", "--seal", "--pinentry"}):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box, subject = Path(opts["--box"]), opts["--seal"]
    w = grant_waiting(box, subject)
    if w is None:
        print(
            "refused: that isn't a session's grant waiting on your seal",
            file=sys.stderr,
        )
        return 2
    program = opts.get("--pinentry") or next(filter(shutil.which, PROGRAMS), None)
    if not program or not shutil.which(program):
        print("refused: no pinentry program to ask with; it waits on your seal page",
              file=sys.stderr)  # fmt: skip
        return 2
    words = str(w.get("words", ""))
    folder = next((ln[5:] for ln in words.splitlines() if ln.startswith("for: ")), "?")
    act = ask(
        program,
        "Model Context Provider",
        f"An assistant session working in\n{folder}\nasks to read from your files.\n\n"
        "If you say yes, it is answered directly until that session ends: what "
        "your files hold on what it asks, and what a job it runs in the sandbox "
        "prints, with names and numbers withheld. You can stop it at any time "
        "on your shared page.",
    )
    if act == "hold":
        print("not now: it waits on your seal page")
        return 42
    got = seal_page.decide(box, act, subject)
    if got.get("state") == "refused":
        print(f"refused: {got.get('why', '')}", file=sys.stderr)
        return 2
    print(f"{got['state']} {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
