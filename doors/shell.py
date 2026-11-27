"""The shell door: one command of an assistant's, run in Kart's sandbox.

    python3 doors/shell.py --box DIR --project DIR --cwd DIR --timeout SECONDS --command TEXT

No one types this. Where the person turned kart-shell on, the guard door
hands the assistant's host this command line in place of each shell command
the guards allowed, and the host runs it as it would have run the command.
It asks the runtime to run the command through Willow's kart: the project
writable, the person's home read-only, no network, and never the box, its
key, the runtime's folder beside the box or this checkout. What the command
printed goes to standard output and standard error as it would have, and
this exits as the command did; 126 when nothing ran, 124 when it was ended.
It decides nothing and puts nothing on the record.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


def main(argv: list[str]) -> int:
    if (
        len(argv) != 10
        or tuple(argv[::2]) != runtime.SHELL_WORDS
        or not argv[7].isdigit()
    ):
        print("usage: shell.py --box DIR --project DIR --cwd DIR --timeout SECONDS "
              "--command TEXT", file=sys.stderr)  # fmt: skip
        return 126
    box, project, cwd, seconds, command = argv[1::2]
    code, out, err = runtime.kart_shell(Path(box), project, cwd, command, int(seconds))
    for stream, text in ((sys.stdout, out), (sys.stderr, err)):
        if text:
            stream.write(text if text.endswith("\n") else text + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
