"""The hide door: one command of an assistant's, run with the box gone.

    python3 doors/hide.py --box DIR --command TEXT

No one types this. Where the person turned hide-shell on, the guard door
hands the assistant's host this command line in place of each shell command
the guards allowed, and the host runs it as it would have run the command:
in the same folder, with the same environment, the network and the person's
home as they are. One thing differs. The box, its key, the runtime's folder
beside it and each path in hide.txt aren't there: an empty folder stands
where each folder was, and nothing readable where each file was. This
checkout and the Willow that runs the guards can be read and not changed.

It becomes bubblewrap, which becomes the command: what the command prints
comes as it is printed, and this ends as the command ends. 126 when nothing
ran. It decides nothing and puts nothing on the record.

It hides by where a file is. A command that asks a program outside for the
file (a service of the person's, another machine's shell back to this one)
isn't stopped by it: that takes a key the assistant's account can't read.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


def main(argv: list[str]) -> int:
    if len(argv) != 4 or tuple(argv[::2]) != runtime.HIDE_WORDS:
        print("usage: hide.py --box DIR --command TEXT", file=sys.stderr)
        return 126
    box, command = argv[1::2]
    return runtime.hide_run(Path(box), command)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
