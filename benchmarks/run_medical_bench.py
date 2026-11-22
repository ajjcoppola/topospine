#!/usr/bin/env python3
"""Run medical/synthetic volume bench; write results under benchmarks/results/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "applications" / "medical"))

from pipeline import run_benchmark  # noqa: E402


def main() -> None:
    out = run_benchmark()
    results = ROOT / "benchmarks" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "medical_loop2.json").write_text(json.dumps(out, indent=2, default=str))
    syn = out["synthetic"]
    cov = out["synthetic_covering"]
    tex = results / "medical_benchmark_table.tex"
    tex.write_text(
        "\\begin{table}[h]\n\\centering\n"
        "\\caption{Loop~2 medical/synthetic volume reduction (TopoSpine pass manager).}\n"
        "\\label{tab:medical}\n"
        "\\resizebox{\\linewidth}{!}{\\begin{tabular}{lrrrrl}\n\\hline\n"
        "Volume & cells before & cells after & time (s) & peak B & note \\\\\n\\hline\n"
        f"synthetic $8^3$ blob & {syn['cells_before']} & {syn['cells_after']} & "
        f"{syn['wall_time_s']:.4f} & {syn['peak_rss_bytes']} & homotopy mode (cells deleted) \\\\\n"
        f"synthetic $8^3$ blob & {cov['cells_before']} & {cov['cells_after']} & "
        f"{cov['wall_time_s']:.4f} & {cov['peak_rss_bytes']} & covering mode (face insertion; "
        f"dim sum {cov['dim_sum_before']}$\\to${cov['dim_sum_after']}) \\\\\n"
        "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )
    print(json.dumps({"homotopy_cells": [syn["cells_before"], syn["cells_after"]],
                      "covering_cells": [cov["cells_before"], cov["cells_after"]],
                      "covering_dim_sum": [cov["dim_sum_before"], cov["dim_sum_after"]],
                      "medmnist": out.get("medmnist")}, indent=2))


if __name__ == "__main__":
    main()
