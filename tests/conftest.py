import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime


#: the check of the folder a session's start sets going on its own: kept
#: here so the one test of it can put it back
CHANGED_AT_START = runtime.changed_at_start


def facts(got: dict) -> dict:
    """A reply without the words the runtime adds for its reader (`say`, what
    happened, and `next`, what to do): the facts a test holds it to. Those
    words are held on their own, in tests/test_ahead.py, never to carry a
    word of the files."""
    return {k: v for k, v in got.items() if k not in ("say", "next")}


@pytest.fixture(autouse=True)
def no_check_let_go(monkeypatch):
    """A session's start sets a program going on its own to fingerprint the
    folder. No test leaves one running behind it."""
    monkeypatch.setattr(runtime, "changed_at_start", lambda box: False)


def made_box(at: Path) -> Path:
    """A box over a small pile in `at`, made by the kernel's own init, its key
    a test key beside it: never a real one."""
    pile = at / "pile"
    pile.mkdir()
    (pile / "garden.md").write_text(
        "The first frost comes in late October, so the dahlias come up then.\n"
    )
    (pile / "car.md").write_text("The car's MOT is due on the 3rd of March.\n")
    b = at / "box"
    run = runtime.willow("kernel.py", "init", "--box", str(b), "--pile", str(pile),
                         "--key", str(at / "test.key"))  # fmt: skip
    assert run.returncode == 0, run.stderr
    return b


@pytest.fixture(scope="session")
def made(tmp_path_factory):
    """The box, made once a test run at the path every test gets it at, and
    a copy of it as it was made. A box's record names its folder by its
    path, so it is only ever put back where it was made, never moved."""
    slot = tmp_path_factory.mktemp("box-slot")
    b = made_box(slot)
    kept = tmp_path_factory.mktemp("box-as-made") / "copy"
    shutil.copytree(slot, kept, symlinks=True)
    return slot, kept, b


@pytest.fixture
def box(made):
    """The box as the kernel's init made it, put back before each test: its
    pile, its record and its key at the paths it was made with, and nothing
    a test before left beside it. One init a run instead of one a test."""
    slot, kept, b = made
    shutil.rmtree(slot)
    shutil.copytree(kept, slot, symlinks=True)
    # what the runtime keeps in memory for a box, by its path: a test before
    # was another program's run, as a box in a folder of its own was
    runtime.OWED.clear()
    runtime.ASKED.clear()
    runtime.REMEMBERED.clear()
    return b
