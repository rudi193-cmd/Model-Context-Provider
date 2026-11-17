import runtime


def seal(box, subject):
    """The person's act, done here with the fixture's test key."""
    run = runtime.willow("kernel.py", "seal", "--box", str(box), subject)
    assert run.returncode == 0, run.stderr


def test_nothing_leaves_without_a_seal(box, tmp_path):
    runtime.read(box, "when does the first frost come")
    assert runtime.propose(box)["state"] == "waiting"
    out = tmp_path / "out.md"
    assert runtime.leave(box, out)["state"] == "refused"
    assert not out.exists()


def test_a_sealed_scope_leaves_and_only_what_it_holds(box, tmp_path):
    runtime.read(box, "when does the first frost come")
    seal(box, runtime.propose(box)["seal"])
    out = tmp_path / "out.md"
    assert runtime.leave(box, out)["state"] == "left"
    page = out.read_text()
    assert "first frost comes in late October" in page
    assert "MOT" not in page  # read is open; what leaves is only the sealed scope


def test_a_new_read_after_the_seal_does_not_widen_what_leaves(box, tmp_path):
    runtime.read(box, "when does the first frost come")
    seal(box, runtime.propose(box)["seal"])
    runtime.read(box, "when is the car's MOT due")
    out = tmp_path / "out.md"
    assert runtime.leave(box, out)["state"] == "left"
    assert "MOT" not in out.read_text()


def test_proposing_with_nothing_read_is_refused_not_a_blank_grant(box):
    assert runtime.propose(box)["state"] == "refused"


def test_proposing_what_is_already_sealed_says_sealed_not_waiting(box):
    runtime.read(box, "when does the first frost come")
    subject = runtime.propose(box)["seal"]
    seal(box, subject)
    assert runtime.propose(box) == {"state": "sealed", "seal": subject}
