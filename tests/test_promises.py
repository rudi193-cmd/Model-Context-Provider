"""promises: what a model can never do, from the code itself, with the test
that holds each promise. It reads nothing of the person's and decides nothing."""

import ast
from pathlib import Path

import runtime
import seal_page

HERE = Path(__file__).parent


def rows(got, name):
    for g in got["groups"]:
        if g["name"] == name:
            return {r["where"]: r["what"] for r in g["rows"]}
    return {}


def test_every_test_it_names_exists():
    named = [where for where, _ in runtime.HELD]
    assert 10 <= len(named) <= 15 and len(set(named)) == len(named)
    for ref in named:
        path, _, name = ref.partition("::")
        assert path.startswith("tests/") and name.startswith("test_"), ref
        file = HERE.parent / path
        assert file.is_file(), f"no such file: {ref}"
        tree = ast.parse(file.read_text())
        found = {n.name for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}  # fmt: skip
        assert name in found, f"no such test: {ref}"
    got = runtime.promises()
    assert list(rows(got, "Held by a test")) == named


def test_the_door_groups_are_what_verbs_and_listed_hold_now():
    got = runtime.promises()
    for name, face in (("A model's door", "model"), ("The assistant's host", "host"),
                       ("Your door", "person")):  # fmt: skip
        said = rows(got, name)
        assert said["verbs"] == ", ".join(sorted(runtime.VERBS[face]))
        assert said["doors"] == ", ".join(
            sorted(d for d, f in runtime.FACES.items() if f == face)
        )
        listed = runtime.LISTED.get(face)
        assert (said.get("also listed and read") == ", ".join(sorted(listed))) if listed \
            else "also listed and read" not in said  # fmt: skip


def test_what_no_model_can_do_is_worked_out_not_written():
    got = runtime.promises()
    no = rows(got, "What no model's door can do")
    assert no["seal or decline"] == "no verb of that name on any door"
    person, model = set(runtime.VERBS["person"]), set(runtime.VERBS["model"])
    assert no["only you have"] == ", ".join(
        sorted(person - model - set(runtime.LISTED["model"]))
    )
    assert "seal" not in no["only you have"].split(", ")
    assert no["only the host has"] == "event"
    assert no["an unknown door"] == "is treated as facing a model"
    assert runtime.FACES.get("no such door", "model") == "model"


def test_a_verb_added_shows_in_the_report_without_anyone_editing_it(monkeypatch):
    monkeypatch.setitem(runtime.VERBS["model"], "seal", lambda *a, **k: {})
    got = runtime.promises()
    assert "seal" in rows(got, "A model's door")["verbs"].split(", ")
    assert rows(got, "What no model's door can do")["seal or decline"].startswith(
        "A VERB OF THAT NAME EXISTS"
    )


def test_it_is_the_persons_alone_and_writes_nothing_down_as_sent(box):
    for door in ("mcp", "hook", "guard", "no such door"):
        got = runtime.call(box, "promises", door=door)
        assert got["code"] == "no_verb" and got["say"]
    got = runtime.call(box, "promises", door="pipe")
    assert got["state"] == "populated" and got["said"]
    assert got["text"].startswith("promises: ") and "## Held by a test" in got["text"]
    assert not (runtime.state(box) / "sent.jsonl").exists()


def test_the_seal_page_shows_it_escaped_and_with_nothing_to_click_but_close(
    box, monkeypatch
):
    monkeypatch.setattr(
        runtime, "HELD", [("tests/x.py::test_<script>", "<b>words</b>")]
    )
    html = seal_page.promises_page(box, "tok")
    assert "<h1>What a model can never do</h1>" in html
    assert "<script>" not in html and "test_&lt;script&gt;" in html
    assert "<b>" not in html and "&lt;b&gt;words&lt;/b&gt;" in html
    assert html.count("<form") == 1 and 'value="quit"' in html
    for href in ('href="/"', 'href="/shared"', 'href="/status"'):
        assert href in html
    assert "/promises" in seal_page.PAGES
    assert 'href="/promises"' in seal_page.status_page(box, "tok")
