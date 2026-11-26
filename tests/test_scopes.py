"""Every question the person was asked to share, where each stands, and a
stop that keeps one from ever leaving again."""

from test_leave import seal

from conftest import facts
import runtime

FROST = "when does the first frost come"


def stands(box):
    return [
        (s["places"], s["stands"])
        for s in runtime.call(box, "scopes", door="pipe")["scopes"]
    ]


def proposed(box, q=FROST):
    runtime.call(box, "read", q, door="mcp")
    return runtime.call(box, "propose", door="mcp")["seal"]


def test_another_sessions_question_between_a_read_and_its_propose_changes_nothing(box):
    """One record hears every session (seen 2026-11-17: a propose refused
    with nothing to share, straight after a read that found something)."""
    runtime.call(box, "read", FROST, door="mcp")
    for theirs in ("what colour is the boat", "when is the car's MOT due"):
        assert runtime.willow("kernel.py", "bite", "--box", str(box), theirs).returncode != 2  # fmt: skip
    got = runtime.call(box, "propose", door="mcp")
    assert got["state"] == "waiting"
    seal(box, got["seal"])
    page = runtime.call(box, "context", FROST, door="hook")["page"]
    assert "late October" in page and "MOT" not in page


def test_a_scope_reads_as_its_places_and_where_it_stands(box):
    subject = proposed(box)
    assert stands(box) == [(["garden.md:1"], "waiting on your seal")]
    seal(box, subject)
    assert stands(box) == [(["garden.md:1"], "sealed")]


def test_a_sealed_scope_whose_file_changed_says_so_out_loud(box):
    seal(box, proposed(box))
    (box.parent / "pile" / "garden.md").write_text("The frost was early.\n")
    ((places, said),) = stands(box)
    assert places == ["garden.md:1"] and said.startswith("changed in your files")


def test_a_stopped_scope_never_leaves_by_any_door(box, tmp_path):
    subject = proposed(box)
    seal(box, subject)
    assert runtime.call(box, "stop", subject, door="pipe") == {
        "state": "stopped",
        "seal": subject,
    }
    assert runtime.call(box, "leave", door="mcp")["code"] == "stopped"
    assert (
        runtime.call(box, "leave", str(tmp_path / "out.md"), door="pipe")["code"]
        == "stopped"
    )
    assert facts(runtime.call(box, "context", FROST, door="hook")) == {
        "state": "populated"
    }
    asked = []
    got = runtime.call(
        box, "draft", FROST, door="mcp", ask=lambda s, u: asked.append(u)
    )
    assert got["asked"] is False and asked == []
    assert stands(box)[0][1].startswith("stopped")


def test_stopping_one_leaves_the_other_free(box):
    frost = proposed(box)
    seal(box, frost)
    mot = proposed(box, "when is the car's MOT due")
    seal(box, mot)
    runtime.call(box, "stop", frost, door="pipe")
    assert (
        "MOT"
        in runtime.call(box, "context", "when is the car's MOT due", door="hook")[
            "page"
        ]
    )


def test_a_model_can_neither_list_nor_stop(box):
    subject = proposed(box)
    assert runtime.call(box, "scopes", door="mcp")["state"] == "refused"
    assert runtime.call(box, "stop", subject, door="mcp")["state"] == "refused"
