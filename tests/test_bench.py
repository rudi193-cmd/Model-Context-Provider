"""bench.py: the runtime timed as pyperformance times (warm-ups left out,
several runs, mean and spread) and two timings compared by its two-tailed
t-test at 95%, its code kept as it is there."""

import json
import subprocess
import sys
from pathlib import Path

import bench

ROOT = Path(__file__).resolve().parents[1]


def test_the_t_test_is_pyperformances():
    assert bench.tdist95conf_level(1) == 12.706
    assert bench.tdist95conf_level(8) == 2.306
    assert (
        bench.tdist95conf_level(45) == 2.021 and bench.tdist95conf_level(500) == 1.960
    )
    real, t = bench.is_significant([1.0, 1.1, 0.9, 1.0], [2.0, 2.1, 1.9, 2.0])
    assert real and t < 0
    same, _ = bench.is_significant([1.0, 1.2, 0.8, 1.0], [1.05, 1.15, 0.85, 0.95])
    assert not same


def test_compare_says_how_much_and_whether_it_is_past_the_noise():
    said = bench.compare([2.0, 2.1, 1.9, 2.0], [1.0, 1.1, 0.9, 1.0])
    assert "2.00x faster" in said and "a real difference" in said
    said = bench.compare([1.0, 1.1, 0.9], [1.0, 1.1, 0.9])
    assert "within the noise" in said
    assert bench.compare([1.0], [1.0]).startswith("can't compare")


def test_run_times_the_runtimes_read_and_writes_each_run(box, tmp_path):
    to = tmp_path / "b.json"
    got = subprocess.run(
        [sys.executable, str(ROOT / "bench.py"), "run", "--box", str(box),
         "when does the first frost come", "--runs", "2", "--warmup", "0",
         "--to", str(to)],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert got.returncode == 0, got.stderr
    times = json.loads(to.read_text())["times"]
    assert len(times) == 2 and all(t > 0 for t in times)
    bad = subprocess.run([sys.executable, str(ROOT / "bench.py"), "run"],
                         capture_output=True, text=True, check=False)  # fmt: skip
    assert bad.returncode == 2
