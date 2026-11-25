"""bench.py: how long the runtime takes, measured the way pyperformance
measures (warm-up runs left out, several timed runs, the mean and its
spread), and two measurements compared by its test of a real difference: a
two-tailed Student's t-test at 95%. Python 3.9+, standard library only.

    WILLOW=... python bench.py run --box BOX "question" [--runs N] [--warmup N] [--to FILE]
    python bench.py compare BEFORE.json AFTER.json

`run` asks the box the question through `runtime.read`, as every door does:
the index brought current, then the bite from it. It writes the seconds of
each timed run to FILE (bench-NAME.json by default), and prints the mean.
`compare` says whether AFTER is faster or slower than BEFORE, by how much,
and whether the difference is past the noise; it exits 0 either way.

The t-test and its table are pyperformance's (pyperformance/compare.py,
MIT, Copyright (c) the pyperformance authors), kept as they are there.
Reading the box needs no seal: nothing here leaves the machine.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

#: pyperformance's table: the 95% two-tailed critical value of Student's t,
#: by degrees of freedom 0 to 29
_T_DIST_95_CONF_LEVELS = [0, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365,
                          2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
                          2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069,
                          2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]  # fmt: skip


def tdist95conf_level(df: float) -> float:
    """pyperformance's: the critical value for df degrees of freedom."""
    df = int(round(df))
    highest_table_df = len(_T_DIST_95_CONF_LEVELS)
    if df >= 200:
        return 1.960
    if df >= 100:
        return 1.984
    if df >= 80:
        return 1.990
    if df >= 60:
        return 2.000
    if df >= 50:
        return 2.009
    if df >= 40:
        return 2.021
    if df >= highest_table_df:
        return _T_DIST_95_CONF_LEVELS[highest_table_df - 1]
    return _T_DIST_95_CONF_LEVELS[df]


def pooled_sample_variance(sample1: list, sample2: list) -> float:
    """pyperformance's."""
    deg_freedom = len(sample1) + len(sample2) - 2
    mean1 = statistics.mean(sample1)
    squares1 = ((x - mean1) ** 2 for x in sample1)
    mean2 = statistics.mean(sample2)
    squares2 = ((x - mean2) ** 2 for x in sample2)
    return (math.fsum(squares1) + math.fsum(squares2)) / float(deg_freedom)


def tscore(sample1: list, sample2: list) -> float:
    """pyperformance's: the t score of two samples of one size."""
    if len(sample1) != len(sample2):
        raise ValueError("different number of values")
    error = pooled_sample_variance(sample1, sample2) / len(sample1)
    diff = statistics.mean(sample1) - statistics.mean(sample2)
    return diff / math.sqrt(error * 2) if error else math.copysign(math.inf, diff or 1)


def is_significant(sample1: list, sample2: list) -> tuple[bool, float]:
    """pyperformance's: whether two samples differ, at 95%, and the t score."""
    deg_freedom = len(sample1) + len(sample2) - 2
    critical_value = tdist95conf_level(deg_freedom)
    t_score = tscore(sample1, sample2)
    return (abs(t_score) >= critical_value, t_score)


def measure(box: Path, question: str, runs: int, warmup: int) -> list[float]:
    """Seconds for each timed run of the question through runtime.read."""
    import runtime

    times = []
    for n in range(warmup + runs):
        t = time.perf_counter()
        runtime.read(box, question)
        if n >= warmup:
            times.append(time.perf_counter() - t)
    return times


def said(times: list[float]) -> str:
    spread = statistics.stdev(times) if len(times) > 1 else 0.0
    return f"{statistics.mean(times):.3f} s ± {spread:.3f} over {len(times)} runs"


def compare(before: list[float], after: list[float]) -> str:
    """AFTER against BEFORE, in a sentence."""
    if len(before) < 2 or len(after) < 2 or len(before) != len(after):
        return "can't compare: each needs the same number of runs, two or more"
    b, a = statistics.mean(before), statistics.mean(after)
    real, t = is_significant(before, after)
    how = f"{b / a:.2f}x faster" if a < b else f"{a / b:.2f}x slower"
    verdict = "a real difference" if real else "within the noise"
    return f"{said(before)} -> {said(after)}: {how}, {verdict} (t = {t:.2f})"


def main(argv: list[str]) -> int:
    if argv[:1] == ["compare"] and len(argv) == 3:
        one, two = (json.loads(Path(p).read_text())["times"] for p in argv[1:])
        print(compare(one, two))
        return 0
    if argv[:1] != ["run"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    opts, words, it = {"--runs": "5", "--warmup": "1"}, [], iter(argv[1:])
    for a in it:
        if a in ("--box", "--runs", "--warmup", "--to"):
            opts[a] = next(it, "")
        else:
            words.append(a)
    if "--box" not in opts or len(words) != 1 or not opts["--runs"].isdigit():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    box = Path(opts["--box"])
    times = measure(box, words[0], int(opts["--runs"]), int(opts["--warmup"] or 0))
    to = Path(opts.get("--to") or f"bench-{box.name}.json")
    to.write_text(
        json.dumps({"box": str(box), "question": words[0], "times": times}) + "\n"
    )
    print(f"{box.name}: {said(times)}; written to {to}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
