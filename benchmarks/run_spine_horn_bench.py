#!/usr/bin/env python3
"""SpineTower Horn-window bench for Paper E (C57)."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "python"))

from topospine.spines.tower import build_cover_tower, tower_certificate


def _circle(n: int = 24, seed: int = 0) -> list[tuple[float, ...]]:
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n + 0.01 * rng.random()
        pts.append((math.cos(ang), math.sin(ang)))
    return pts


def main() -> None:
    points = _circle(24)
    base = build_cover_tower(points, base_scale=1.2, n_levels=3, spine_method="espresso_loop")
    horn = build_cover_tower(points, base_scale=1.2, n_levels=3, spine_method="horn", horn_mode="approx")
    cert_b = tower_certificate(base)
    cert_h = tower_certificate(horn)
    out = {
        "baseline": cert_b,
        "horn": cert_h,
        "horn_certified_fraction": cert_h["certified_optimal_fraction"],
        "cover_sizes_baseline": cert_b["cover_sizes"],
        "cover_sizes_horn": cert_h["cover_sizes"],
        "windows_horn": cert_h["windows"],
    }
    results = ROOT / "benchmarks" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "spine_horn_bench.json").write_text(json.dumps(out, indent=2))
    tex = results / "spine_horn_bench_table.tex"
    tex.write_text(
        "\\begin{table}[h]\\centering\\small\n"
        "\\caption{SpineTower levels with Horn $(L,U)$ windows (Paper~E).}\n"
        "\\label{tab:spine-horn}\n"
        "\\begin{tabular}{lrrr}\\hline\n"
        "mode & cover sizes & certified levels & certified fraction \\\\\\hline\n"
        f"espresso\\_loop & {cert_b['cover_sizes']} & 0 & 0.00 \\\\\n"
        f"horn approx & {cert_h['cover_sizes']} & {cert_h['certified_optimal_levels']} & "
        f"{cert_h['certified_optimal_fraction']:.2f} \\\\\n"
        "\\hline\\end{tabular}\\end{table}\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
