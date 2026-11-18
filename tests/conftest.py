import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


#: the check of the folder a session's start sets going on its own: kept
#: here so the one test of it can put it back
CHANGED_AT_START = runtime.changed_at_start


@pytest.fixture(autouse=True)
def no_check_let_go(monkeypatch):
    """A session's start sets a program going on its own to fingerprint the
    folder. No test leaves one running behind it."""
    monkeypatch.setattr(runtime, "changed_at_start", lambda box: False)


@pytest.fixture
def box(tmp_path):
    """A box over a small pile, its key a test key in tmp_path: never a real one."""
    pile = tmp_path / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "The first frost comes in late October, so the dahlias come up then.\n"
    )
    (pile / "car.md").write_text("The car's MOT is due on the 3rd of March.\n")
    b = tmp_path / "box"
    run = runtime.willow(
        "kernel.py",
        "init",
        "--box",
        str(b),
        "--pile",
        str(pile),
        "--key",
        str(tmp_path / "test.key"),
    )
    assert run.returncode == 0, run.stderr
    return b
