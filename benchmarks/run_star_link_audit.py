#!/usr/bin/env python3
"""Audit face-row Theorem A and vertex-row Link(opp) (L,U) bounds.

Writes benchmarks/results/star_link_audit.json and star_link_audit_table.tex.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.cover.grid2d import (  # noqa: E402
    FILLED,
    HOLLOW,
    audit_face_row_theorem_a,
    audit_link_bounds,
    build_grid,
    collapsible_pairs,
    link_out_complex,
    to_core,
)


def main() -> None:
    t0 = time.perf_counter()
    out: dict = {}
    print("Theorem A 2x2 …", flush=True)
    out["theorem_a"] = {
        "2x2": audit_face_row_theorem_a(2, 2),
        "2x3": audit_face_row_theorem_a(2, 3),
    }
    print(out["theorem_a"], flush=True)
    # 3x3 face-row is slower; still exhaustive for the claim
    print("Theorem A 3x3 …", flush=True)
    out["theorem_a"]["3x3"] = audit_face_row_theorem_a(3, 3)
    print(out["theorem_a"]["3x3"], flush=True)

    print("Link bounds 2x3 / 3x3 …", flush=True)
    out["link_bounds"] = {
        "2x3": audit_link_bounds(2, 3),
        "3x3": audit_link_bounds(3, 3),
    }
    print(out["link_bounds"], flush=True)

    cfg = {
        (0, 0): HOLLOW,
        (1, 0): HOLLOW,
        (0, 1): FILLED,
        (1, 1): HOLLOW,
        (0, 2): HOLLOW,
        (1, 2): HOLLOW,
    }
    core = to_core(build_grid(cfg, 2, 3))
    assert core is not None
    ring = []
    for p, f in collapsible_pairs(core):
        inst = link_out_complex(core, p, f)
        ring.append(
            {
                "p": inst.p_name,
                "f": str(inst.free_face),
                "opp": str(inst.opp),
                "L": inst.L,
                "opt": inst.opt,
                "U": inst.U,
                "exact": inst.exact_stitch,
            }
        )
    out["ring_2x3"] = ring
    out["wall_s"] = time.perf_counter() - t0

    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "star_link_audit.json").write_text(json.dumps(out, indent=2))

    a = out["theorem_a"]
    b = out["link_bounds"]["3x3"]
    tex = (
        "\\begin{table}[h]\\centering\\small\n"
        "\\caption{Face-row Theorem~A (free face $\\Rightarrow$ essential, "
        "$\\mathrm{opt}=1+\\mathrm{opt}(K/p)$) and vertex-row Link($\\mathrm{opp}(f)$) "
        f"bounds $L\\le\\mathrm{{opt}}\\le U$. Exact stitch rate on $3\\times 3$: "
        f"{b['exact_rate']:.3f}; gap histogram {b['gap_histogram']}."
        "}\n"
        "\\label{tab:star-link}\n"
        "\\begin{tabular}{lrrr}\\hline\n"
        "audit & checked & mismatches/violations & notes \\\\\\hline\n"
        f"Thm A $2\\times 2$ & {a['2x2']['checked']} & {a['2x2']['mismatches']} & essential {a['2x2']['essential_pairs']} \\\\\n"
        f"Thm A $2\\times 3$ & {a['2x3']['checked']} & {a['2x3']['mismatches']} & essential {a['2x3']['essential_pairs']} \\\\\n"
        f"Thm A $3\\times 3$ & {a['3x3']['checked']} & {a['3x3']['mismatches']} & essential {a['3x3']['essential_pairs']} \\\\\n"
        f"Link bounds $3\\times 3$ & {b['checked']} & {b['violations']} & exact {b['exact_stitch']} \\\\\n"
        "\\hline\\end{tabular}\\end{table}\n"
    )
    (res / "star_link_audit_table.tex").write_text(tex)
    print("wrote", res / "star_link_audit.json", flush=True)


if __name__ == "__main__":
    main()
