#!/usr/bin/env python3
"""Audit the free-face local transform on 2D grid complexes.

Writes:
  benchmarks/results/grid_collapse_audit.json
  benchmarks/results/grid_collapse_audit_table.tex
  benchmarks/results/figures/grid_*.tikz  (and .pdf if tectonic/pdflatex available)
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
    ABSENT,
    apply_transform,
    build_grid,
    collapsible_pairs,
    dichotomy_counts,
    smallest_vertex_counterexample,
    to_core,
    verify_characterization,
    all_configs,
)


def tikz_grid(config: dict, a: int, b: int, p=None, f=None, far=None, label: str = "") -> str:
    """TikZ picture: filled squares shaded, hollow as edge frames; highlight p/f/far."""
    lines = [
        r"\begin{tikzpicture}[x=0.55cm,y=0.55cm,every node/.style={font=\scriptsize}]",
    ]
    if label:
        lines.append(rf"\node[anchor=south] at ({a/2:.1f},{b+0.35:.1f}) {{{label}}};")
    for i in range(a):
        for j in range(b):
            st = config.get((i, j), ABSENT)
            if st == ABSENT:
                continue
            fill = "black!18" if st == FILLED else "white"
            if p is not None and p.cell == ("sq", i, j):
                fill = "orange!45"
            lines.append(
                rf"\draw[fill={fill}] ({i},{j}) rectangle ++(1,1);"
            )
            if st == HOLLOW:
                lines.append(rf"\draw[thick] ({i},{j}) rectangle ++(1,1);")
    if f is not None and f[0] == "ed":
        _, kind, x, y = f
        if kind == "h":
            lines.append(rf"\draw[blue,very thick] ({x},{y}) -- ({x+1},{y});")
        else:
            lines.append(rf"\draw[blue,very thick] ({x},{y}) -- ({x},{y+1});")
    if far:
        for vx, vy in far:
            lines.append(rf"\fill[red!70] ({vx},{vy}) circle (2pt);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def audit_transform_stats(a: int, b: int) -> dict:
    stats = {
        "configs": 0,
        "cores": 0,
        "pairs": 0,
        "c_exp_eq_opt": 0,
        "putback_eq_opt": 0,
        "putback_rescues": 0,
        "far_empty": 0,
        "char_mismatches": 0,
    }
    for cfg in all_configs(a, b):
        stats["configs"] += 1
        g = build_grid(cfg, a, b)
        core = to_core(g)
        if core is None:
            continue
        stats["cores"] += 1
        for p, f in collapsible_pairs(core):
            stats["pairs"] += 1
            res = apply_transform(core, p, f)
            if res.c_exp == res.opt:
                stats["c_exp_eq_opt"] += 1
            if res.decoded_putback == res.opt:
                stats["putback_eq_opt"] += 1
            if res.decoded_raw != res.opt and res.decoded_putback == res.opt:
                stats["putback_rescues"] += 1
            if res.far_empty:
                stats["far_empty"] += 1
            from topospine.cover.grid2d import characterization_holds

            if not characterization_holds(core, p, f, res):
                stats["char_mismatches"] += 1
    return stats


def main() -> None:
    t0 = time.perf_counter()
    out: dict = {"dichotomy": {}, "stats": {}, "characterization": {}, "counterexample": None}
    print("dichotomy 3x3 …", flush=True)
    out["dichotomy"]["3x3"] = dichotomy_counts(3, 3)
    print(out["dichotomy"]["3x3"], flush=True)

    for a, b in ((2, 2), (2, 3), (3, 3)):
        print(f"audit {a}x{b} …", flush=True)
        out["stats"][f"{a}x{b}"] = audit_transform_stats(a, b)
        print(out["stats"][f"{a}x{b}"], flush=True)

    print("characterization 3x3 …", flush=True)
    out["characterization"]["3x3"] = verify_characterization(3, 3)
    print(out["characterization"]["3x3"], flush=True)

    cex = smallest_vertex_counterexample()
    if cex is not None:
        out["counterexample"] = {
            "grid": cex.grid_draw,
            "p": cex.p_name,
            "free_face": str(cex.free_face),
            "opt": cex.opt,
            "c_exp": cex.c_exp,
            "decoded_putback": cex.decoded_putback,
        }
        print("smallest cex:", out["counterexample"], flush=True)

    out["wall_time_s"] = time.perf_counter() - t0
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    fig = res / "figures"
    fig.mkdir(parents=True, exist_ok=True)
    (res / "grid_collapse_audit.json").write_text(json.dumps(out, indent=2))

    # TikZ for smallest counterexample (2x3 hollow ring with one fill)
    cfg = {
        (0, 0): HOLLOW, (1, 0): HOLLOW,
        (0, 1): FILLED, (1, 1): HOLLOW,
        (0, 2): HOLLOW, (1, 2): HOLLOW,
    }
    g = build_grid(cfg, 2, 3)
    core = to_core(g)
    assert core is not None
    p, f = next(iter(collapsible_pairs(core)))
    from topospine.cover.grid2d import far_rows

    far = far_rows(p, f, core.core_rows)
    tikz = tikz_grid(cfg, 2, 3, p=p, f=f, far=far, label="smallest vertex-row counterexample")
    (fig / "grid_cex_2x3.tikz").write_text(tikz)

    # filled vs hollow demo
    demo = {(0, 0): FILLED, (1, 0): HOLLOW, (0, 1): HOLLOW, (1, 1): FILLED}
    (fig / "grid_demo_2x2.tikz").write_text(
        tikz_grid(demo, 2, 2, label="filled / hollow demo")
    )

    rows = ""
    for key, s in out["stats"].items():
        rows += (
            f"{key} & {s['cores']} & {s['pairs']} & {s['c_exp_eq_opt']} & "
            f"{s['putback_eq_opt']} & {s['putback_rescues']} & {s['char_mismatches']} \\\\\n"
        )
    d = out["dichotomy"]["3x3"]
    (res / "grid_collapse_audit_table.tex").write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Vertex-row free-face transform on filled/hollow/absent grids. "
        f"Dichotomy on $3\\times 3$: face-row cores with a collapsible square "
        f"{d['face_with_collapsible_square']}/{d['face_cores']}; "
        f"vertex-row {d['vertex_with_collapsible_square']}/{d['vertex_cores']}. "
        "Columns: cyclic cores; $(p,f)$ pairs; $\\mathrm{opt}(P')=\\mathrm{opt}(P)$; "
        "put-back equals opt; put-back rescues; characterization mismatches.}\n"
        "\\label{tab:grid-collapse}\n"
        "\\begin{tabular}{lrrrrrr}\n\\hline\n"
        "grid & cores & pairs & $C'=\\mathrm{opt}$ & putback & rescues & char miss \\\\\n\\hline\n"
        + rows
        + "\\hline\n\\end{tabular}\n\\end{table}\n"
    )
    print("wrote", res / "grid_collapse_audit.json", flush=True)


if __name__ == "__main__":
    main()
