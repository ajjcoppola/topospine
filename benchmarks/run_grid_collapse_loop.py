#!/usr/bin/env python3
"""Five-round sufficient-condition search for the free-face local transform.

Each round writes benchmarks/results/grid_collapse_round{k}.json.
Stop when a candidate fires on ≥5% of (core,p,f) cases with zero failures,
or after 5 rounds.
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
    candidate_far_dominated,
    candidate_far_empty,
    candidate_far1_face1,
    candidate_window,
)

RES = ROOT / "benchmarks" / "results"
RES.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ("far_empty", candidate_far_empty, "trivial: F_p empty"),
    ("far1_face1", candidate_far1_face1, "|F_p|=1 and |V(f)∩R|=1"),
    ("far_dominated", candidate_far_dominated, "every far row in a column covering all of F_p"),
    ("window_r1", lambda c, p, f: candidate_window(c, p, f, 1), "radius-1 window profile"),
    ("window_r2", lambda c, p, f: candidate_window(c, p, f, 2), "radius-2 window profile"),
]


def run_round(k: int, a: int = 3, b: int = 3) -> dict:
    name, pred, note = CANDIDATES[k - 1]
    t0 = time.perf_counter()
    print(f"ROUND {k}: {name} — {note}", flush=True)
    result = audit_sufficient_candidate(name, pred, a=a, b=b)
    result["round"] = k
    result["note"] = note
    result["grid"] = f"{a}x{b}"
    result["wall_time_s"] = time.perf_counter() - t0
    path = RES / f"grid_collapse_round{k}.json"
    path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2), flush=True)
    return result


def main() -> None:
    summary = []
    winner = None
    for k in range(1, 6):
        r = run_round(k)
        summary.append(r)
        # far_empty is reported separately as trivial even if it passes
        if r.get("pass") and r["name"] != "far_empty":
            winner = r
            break
        if r["name"] == "far_empty":
            r["reported_separately"] = True
    out = {
        "rounds": summary,
        "winner": winner,
        "stopped_early": winner is not None,
        "n_rounds": len(summary),
    }
    (RES / "grid_collapse_loop_summary.json").write_text(json.dumps(out, indent=2))
    print("SUMMARY winner:", winner["name"] if winner else None, flush=True)


if __name__ == "__main__":
    main()
