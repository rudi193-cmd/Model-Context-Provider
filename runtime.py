"""The one local runtime. Every door calls this; nothing else decides.

Line 1: a grant guards what leaves, never what is read. Reading goes through
Willow's kernel and needs no grant.

Willow is used by its command line only (kernel.py and its add-ons), so the
kernel is never changed or imported here. WILLOW names the checkout; the
default is a sibling folder named Willow.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WILLOW = Path(os.environ.get("WILLOW", HERE.parent / "Willow"))


def willow(*args: str) -> subprocess.CompletedProcess:
    """Run one of Willow's commands, its output caught."""
    return subprocess.run(
        [sys.executable, *args], cwd=WILLOW, capture_output=True, text=True
    )


def read(box: Path, question: str) -> dict:
    """Ask the box. Reading never needs a grant: this is the kernel's bite,
    as the kernel answers it."""
    run = willow("kernel.py", "bite", "--box", str(box), question)
    if run.returncode == 2:
        return {"state": "refused", "why": run.stderr.strip()}
    return json.loads(run.stdout)
