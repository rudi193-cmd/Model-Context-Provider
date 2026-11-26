"""A page given to a model also comes as data: each passage's id, the file
it is from and its text, exactly as the page holds them, so a model cites by
id without taking the page's markup apart. Nothing leaves that the page
didn't hold, and the tools that can give a page say so in their schema."""

import importlib.util
from pathlib import Path

from test_grant import FROST, call, let_in

import runtime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_door", ROOT / "doors" / "mcp.py")
door = importlib.util.module_from_spec(spec)
spec.loader.exec_module(door)


def test_a_page_given_comes_with_its_passages_as_data(box):
    let_in(box)
    got = call(box, "context", FROST)
    assert got["state"] == "left", got
    page, passages = got["page"], got["passages"]
    assert passages and all(f"[{p['id']}]" in page for p in passages)
    # never the kernel's id: the hash of a passage's text before withholding
    kernel = {s["id"] for s in runtime.read(box, FROST)["served"]}
    assert not kernel & {p["id"] for p in passages}
    assert not any(k in str(got) for k in kernel)
    for p in passages:
        assert p["file"] == "garden.md" and p["text"] in page and "frost" in p["text"]
        assert set(p) == {"id", "file", "text"}


def test_a_reply_with_no_page_has_no_passages(box):
    assert "passages" not in call(box, "context", FROST)  # not let in: populated
    assert "passages" not in runtime.with_passages(
        {"state": "left", "page": "# a report\n"}
    )


def test_the_tools_that_give_a_page_say_what_their_reply_holds(box):
    tools = {t["name"]: t for t in door.listing(box)}
    for name in door.PAGES:
        out = tools[name]["outputSchema"]
        assert out["required"] == ["state"] and "passages" in out["properties"]
    assert all("outputSchema" not in t for n, t in tools.items() if n not in door.PAGES)


def test_a_sealed_page_comes_with_its_passages_by_its_own_ids():
    page = ("## garden.md\n\n- `a1b2c3` human-sealed\n  ```\n"
            "  The first frost comes in late October.\n  ```\n")  # fmt: skip
    got = runtime.with_passages({"state": "left", "page": page})
    assert got["passages"] == [{"id": "a1b2c3", "file": "garden.md",
                                "text": "The first frost comes in late October."}]  # fmt: skip
