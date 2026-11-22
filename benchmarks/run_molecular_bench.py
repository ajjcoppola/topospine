#!/usr/bin/env python3
"""Loop 3 molecular bench: relative SpineTower vs coverage-only spine.

Writes benchmarks/results/molecular_loop3.json and molecular_benchmark_table.tex.
Uses MD17/MD22 only if TOPOSPINE_MD17_NPZ points to a local .npz; otherwise the
synthetic 13-atom x 12-conformation cloud (reported as such).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "applications" / "molecular"))

from mol_pipeline import run_benchmark  # noqa: E402


def write_tex(out: dict, path: Path) -> None:
    block = out["md17"] if not out["md17"].get("skipped") else out["synthetic"]
    src = block["meta"]["source"]
    rel, cov = block["relative"], block["coverage_only"]
    rows = ""
    for k, scale in enumerate(rel["scales"]):
        rows += (
            f"{scale:.2f} & {cov['cover_sizes'][k]} & {rel['cover_sizes'][k]} & "
            f"{cov['A_cover_radius'][k]:.2f} & {rel['A_cover_radius'][k]:.2f} & "
            f"{cov['betti_N'][k][0]}/{cov['betti_N'][k][1]} & "
            f"{rel['betti_N'][k][0]}/{rel['betti_N'][k][1]} & "
            f"{rel['betti_NA'][k][0]}/{rel['betti_NA'][k][1]} & "
            f"{rel['betti_relative'][k][0]}/{rel['betti_relative'][k][1]} \\\\\n"
        )
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        f"\\caption{{Relative SpineTower on a {src} conformation cloud "
        f"({block['n_points']} points, $|A|={block['n_A']}$). "
        "Cover sizes, A-covering radius (max distance from an A-point to a selected centre), "
        "and F$_2$ Betti numbers $\\beta_0/\\beta_1$ of the nerve $N$, the A-nerve $N_A$ and the "
        "relative pair $(N,N_A)$. Wall time: coverage-only "
        f"{cov['total_wall_time_s']:.3f}\\,s, relative {rel['total_wall_time_s']:.3f}\\,s.}}\n"
        "\\label{tab:molecular}\n"
        "\\resizebox{\\linewidth}{!}{\\begin{tabular}{rrrrrrrrr}\n\\hline\n"
        "scale & $|$cov$|$ & $|$rel$|$ & $r_A$ cov & $r_A$ rel & $\\beta(N)$ cov & "
        "$\\beta(N)$ rel & $\\beta(N_A)$ rel & $\\beta(N,N_A)$ rel \\\\\n\\hline\n"
        + rows
        + "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )


def write_ablation_tex(out: dict, path: Path) -> None:
    block = out["md17"] if not out["md17"].get("skipped") else out["synthetic"]
    ab = block["ablation"]
    names = {
        "relative": "relative (forced A-net)",
        "coverage_only": "coverage-only spine",
        "kcenter_same_budget": "k-center, same budget",
        "a_weighted_greedy": "A-weighted greedy (x10)",
    }
    rows = ""
    for key, label in names.items():
        m = ab["methods"][key]
        rows += (
            f"{label} & " + " / ".join(str(x) for x in m["cover_sizes"]) + " & "
            + " / ".join(f"{x:.2f}" for x in m["A_cover_radius"]) + " & "
            + " / ".join(f"{x:.2f}" for x in m["r_all"]) + " & "
            + " / ".join("yes" if x else "no" for x in m["betti_NA_matches_rips_A"]) + " \\\\\n"
        )
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Ablation on the " + block["meta"]["source"] + " cloud, levels listed coarse to fine. "
        "$r_A$: max distance from an A-point to a selected centre; $r_{\\mathrm{all}}$: same over all points. "
        "``$\\beta(N_A)$ = Rips'': whether $\\beta_0,\\beta_1$ of the A-nerve equal those of the Vietoris--Rips "
        "complex of A at twice the scale (own exact F$_2$ code; GUDHI "
        + ("available" if ab["gudhi_available"] else "not installed") + ").}\n"
        "\\label{tab:ablation}\n\\resizebox{\\linewidth}{!}{\\begin{tabular}{lllll}\n\\hline\n"
        "method & cover sizes & $r_A$ & $r_{\\mathrm{all}}$ & $\\beta(N_A)$ = Rips \\\\\n\\hline\n"
        + rows + "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )


def main() -> None:
    out = run_benchmark()
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "molecular_loop3.json").write_text(json.dumps(out, indent=2, default=str))
    write_tex(out, res / "molecular_benchmark_table.tex")
    write_ablation_tex(out, res / "molecular_ablation_table.tex")
    s = out["synthetic"]
    print(
        json.dumps(
            {
                "md17": out["md17"] if out["md17"].get("skipped") else "ran",
                "synthetic_n_points": s["n_points"],
                "cover_sizes": {"coverage_only": s["coverage_only"]["cover_sizes"], "relative": s["relative"]["cover_sizes"]},
                "A_cover_radius": {"coverage_only": s["coverage_only"]["A_cover_radius"], "relative": s["relative"]["A_cover_radius"]},
                "relative_equivalence_checked": s["relative"]["relative_equivalence_checked"],
                "wall_s": {"coverage_only": s["coverage_only"]["total_wall_time_s"], "relative": s["relative"]["total_wall_time_s"]},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
