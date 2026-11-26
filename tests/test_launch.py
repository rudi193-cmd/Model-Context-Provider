"""A Willow command is run as `python SCRIPT ARGS` would run it, but with its
compiled code kept between runs: the same name, file, arguments, path and
exit code, a missing script refused with 2, and a __pycache__ written."""

import subprocess
import sys

import runtime

SCRIPT = """import sys, os
print(__name__, __file__, sys.argv, sys.path[0] == os.path.dirname(os.path.abspath(__file__)))
print("to stderr", file=sys.stderr)
if __name__ == "__main__":
    raise SystemExit(int(sys.argv[1]))
"""


def both(tmp_path, *args):
    plain = subprocess.run([sys.executable, *args], cwd=tmp_path,
                           capture_output=True, text=True, check=False)  # fmt: skip
    launched = subprocess.run([sys.executable, "-c", runtime.LAUNCH, *args], cwd=tmp_path,
                              capture_output=True, text=True, check=False)  # fmt: skip
    return plain, launched


def test_a_script_sees_what_a_plain_run_gives_it(tmp_path):
    (tmp_path / "tool.py").write_text(SCRIPT)
    for code in ("0", "42", "2"):
        plain, launched = both(tmp_path, "tool.py", code, "two words")
        assert (launched.stdout, launched.stderr, launched.returncode) == (
            plain.stdout, plain.stderr, plain.returncode)  # fmt: skip
        assert launched.stdout.startswith(
            "__main__ "
        )  # its file, absolute, as Python's
        assert "/tool.py ['tool.py', " in launched.stdout.replace("\\", "/")
        assert launched.returncode == int(code)


def test_its_compiled_code_is_kept(tmp_path):
    (tmp_path / "tool.py").write_text(SCRIPT)
    both(tmp_path, "tool.py", "0")
    assert list((tmp_path / "__pycache__").glob("tool.*.pyc"))


def test_a_missing_script_is_refused_as_python_refuses_it(tmp_path):
    plain, launched = both(tmp_path, "no-such.py")
    assert launched.returncode == plain.returncode == 2
    assert "can't open file" in launched.stderr


def test_a_willow_command_answers_as_it_did(box):
    run = runtime.willow("kernel.py", "verify", "--box", str(box))
    assert run.returncode == 0, run.stderr
