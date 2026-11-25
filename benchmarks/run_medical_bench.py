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
    c07 = out["coppola_2007_horn"]
    tex = results / "medical_benchmark_table.tex"
    tex.write_text(
        "\\begin{table}[h]\n\\centering\n"
        "\\caption{Medical/synthetic volume reduction (TopoSpine). "
        "Covering mode uses Horn retraction (Paper~E); non-vacuous on the "
        "$8^3$ blob and the 2007 core.}\n"
        "\\label{tab:medical}\n"
        "\\resizebox{\\linewidth}{!}{\\begin{tabular}{lrrrl}\n\\hline\n"
        "Volume & cells & horn steps & time (s) & note \\\\\n\\hline\n"
        f"synthetic $8^3$ (homotopy) & {syn['cells_before']}$\\to${syn['cells_after']} & "
        f"--- & {syn['wall_time_s']:.4f} & cells deleted \\\\\n"
        f"synthetic $8^3$ (Horn covering) & {cov['cells_before']}$\\to${cov['cells_after']} & "
        f"{cov['horn_steps']} & {cov['wall_time_s']:.4f} & "
        f"non-vacuous (dim-sum {cov['dim_sum_before']}$\\to${cov['dim_sum_after']}) \\\\\n"
        f"2007 core (Horn) & {c07['cells_before']}$\\to${c07['cells_after']} & "
        f"{c07['horn_steps']} & {c07['wall_time_s']:.4f} & "
        f"max-dim {c07['max_dim_before']}$\\to${c07['max_dim_after']}; "
        f"$H^*$ {'preserved' if c07['cohomology_preserved'] else 'CHANGED'} \\\\\n"
        "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )
    print(
        json.dumps(
            {
                "homotopy_cells": [syn["cells_before"], syn["cells_after"]],
                "covering_cells": [cov["cells_before"], cov["cells_after"]],
                "covering_max_dim": [cov["max_dim_before"], cov["max_dim_after"]],
                "covering_horn_steps": cov["horn_steps"],
                "2007": {
                    "cells": [c07["cells_before"], c07["cells_after"]],
                    "max_dim": [c07["max_dim_before"], c07["max_dim_after"]],
                    "horn_steps": c07["horn_steps"],
                    "H_star": c07["cohomology_preserved"],
                },
                "medmnist": out.get("medmnist"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
