#!/usr/bin/env python3
"""Sufficient-condition search rounds for the free-face local transform.

Writes benchmarks/results/grid_collapse_round{k}.json for k=1..5.
Stop condition: fire_rate >= 0.05 and failures == 0 (non-trivial candidates).
Candidate order (plan):
  1. F_p empty (trivial; reported separately)
  2. |F_p|=1 and |V(f)∩R|=1
  3. every far row lies in a column that dominates p on the far side
  4. window profile radius-1
  5. window profile radius-2
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.cover.grid2d import (  # noqa: E402
    audit_sufficient_candidate,
    candidate_far1_face1,
    candidate_far_dominated,
    candidate_far_empty,
    candidate_window,
)

ROUNDS = [
    ("far_empty", lambda c, p, f: candidate_far_empty(c, p, f), True),
    ("far1_face1", lambda c, p, f: candidate_far1_face1(c, p, f), False),
    ("far_dominated", lambda c, p, f: candidate_far_dominated(c, p, f), False),
    ("window_r1", lambda c, p, f: candidate_window(c, p, f, 1), False),
    ("window_r2", lambda c, p, f: candidate_window(c, p, f, 2), False),
]


def main() -> None:
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    log_lines = []
    winner = None
    for k, (name, pred, trivial) in enumerate(ROUNDS, start=1):
        t0 = time.perf_counter()
        print(f"round {k}: {name} …", flush=True)
        # 3x3 exhaustive
        out3 = audit_sufficient_candidate(name, pred, a=3, b=3)
        out3["grid"] = "3x3"
        out3["trivial"] = trivial
        out3["wall_s"] = time.perf_counter() - t0
        # 3x4 may be heavy for window; sample if needed
        t1 = time.perf_counter()
        if name.startswith("window"):
            out34 = audit_sufficient_candidate(name, pred, a=3, b=4, sample=5000)
        else:
            out34 = audit_sufficient_candidate(name, pred, a=3, b=4, sample=20000)
        out34["grid"] = "3x4_sample"
        out34["trivial"] = trivial
        out34["wall_s"] = time.perf_counter() - t1
        payload = {
            "round": k,
            "candidate": name,
            "results": {"3x3": out3, "3x4": out34},
            "stop_pass": (not trivial) and out3.get("pass", False),
        }
        path = res / f"grid_collapse_round{k}.json"
        path.write_text(json.dumps(payload, indent=2))
        line = (
            f"round {k} {name}: 3x3 fires={out3['fires']}/{out3['total']} "
            f"fail={out3['failures']} rate={out3['fire_rate']:.3f}; "
            f"3x4 fires={out34['fires']}/{out34['total']} fail={out34['failures']}"
        )
        print(line, flush=True)
        log_lines.append(line)
        if payload["stop_pass"] and winner is None:
            winner = payload
            print(f"STOP: passing condition {name} on 3x3", flush=True)
            break
    summary = {"winner": winner, "log": log_lines}
    (res / "grid_collapse_rounds_summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote summary", flush=True)


if __name__ == "__main__":
    main()
