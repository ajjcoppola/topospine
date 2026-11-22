#!/usr/bin/env python3
"""Bio-circuit / logic bench (Loop 3, extended in Loop 4).

Writes benchmarks/results/bio_loop3.json (kept name) and bio_benchmark_table.tex.
Columns: minterm SOP; same pipeline without don't-cares; DC spine; and, when
``abc``/``yosys-abc`` is on PATH, ABC (strash + resyn2) on (a) the minterm AIG with DC
forced to 0 (what a standard flow sees) and (b) our DC-spine AIG.
Also: ISCAS-85 c17 (public benchmark) and a literal-objective ablation on random 5-var ISFs.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.examples.bio_circuits import run_cascade, run_gene_toy  # noqa: E402
from topospine.formats import read_blif, spec_to_states  # noqa: E402
from topospine.synth.logic_passes import (  # noqa: E402
    DontCareSpinePass,
    LogicPassManager,
    LogicState,
    abc_optimize,
    abc_optimize_blif_text,
    find_abc,
)


def run_c17() -> dict:
    text = (ROOT / "examples" / "data" / "c17.blif").read_text()
    spec = read_blif(text)
    rows, tot_ours, tot_abc_ours = [], 0, 0
    for name, st in spec_to_states(spec).items():
        out = LogicPassManager().run(st)
        a = abc_optimize(out.aig, out.out) if find_abc() else {"ands_final": None}
        rows.append({"output": name, "gates_minterm": st.gates(), "gates_ours": out.gates(), "abc_on_ours": a["ands_final"]})
        tot_ours += out.gates()
        tot_abc_ours += a["ands_final"] or 0
    abc_whole = abc_optimize_blif_text(text) if find_abc() else {"ands_final": None}
    return {
        "reference_nand2_gates": spec.gate_count_reference,
        "abc_on_original_netlist_ands": abc_whole["ands_final"],
        "ours_sum_per_output": tot_ours,
        "note": "per-output synthesis has no cross-output sharing, so it cannot match the shared 6-gate netlist",
        "rows": rows,
    }


def objective_ablation(n_funcs: int = 120, n: int = 5, seed: int = 3) -> dict:
    rng = random.Random(seed)
    tot = {o: {"cubes": 0, "literals": 0, "gates": 0} for o in DontCareSpinePass.OBJECTIVES}
    used = 0
    for _ in range(n_funcs):
        on = {m for m in range(1 << n) if rng.random() < 0.4}
        dc = {m for m in range(1 << n) if m not in on and rng.random() < 0.15}
        if not on:
            continue
        used += 1
        for obj in DontCareSpinePass.OBJECTIVES:
            r = DontCareSpinePass(objective=obj).try_apply(LogicState.from_minterms(n, on, dc)).state
            tot[obj]["cubes"] += len(r.cubes)
            tot[obj]["literals"] += r.literals()
            tot[obj]["gates"] += r.gates()
    return {"n_vars": n, "functions": used, "seed": seed, "totals": tot}


def build() -> dict:
    have_abc = find_abc() is not None
    toy = run_gene_toy()
    cas = run_cascade(n_nodes=24, n_pi=6, seed=2026, with_abc=have_abc)
    cas_wide = [run_cascade(n_nodes=40, n_pi=6, seed=s, with_abc=have_abc) for s in (1, 2, 3)]
    return {
        "abc_on_path": have_abc,
        "abc_binary": Path(find_abc()).name if have_abc else None,
        "gene_toy": toy,
        "cascade24": cas,
        "cascade40_seeds": [
            {
                "seed": c["seed"],
                "totals": c["totals"],
                "global_mismatches": c["global_mismatches"],
                "all_witnesses_ok": c["all_witnesses_ok"],
            }
            for c in cas_wide
        ],
        "c17": run_c17(),
        "objective_ablation": objective_ablation(),
    }


def write_tex(out: dict, path: Path) -> None:
    rows = [
        ("5-gene regulation toy (4 nodes)", out["gene_toy"]["totals"]),
        ("pathway cascade, 24 nodes", out["cascade24"]["totals"]),
    ]
    for s in out["cascade40_seeds"]:
        rows.append((f"pathway cascade, 40 nodes (seed {s['seed']})", s["totals"]))
    have_abc = out["abc_on_path"]

    def pct(a: int, b: int) -> str:
        return f"{100 * (a - b) / a:.0f}\\%" if a else "--"

    body = ""
    for name, t in rows:
        cells = f"{name} & {t['minterm']} & {t['nodc']} & {t['dc']} & {pct(t['nodc'], t['dc'])}"
        if have_abc:
            if "abc_on_minterm" in t:
                cells += f" & {t['abc_on_minterm']} & {t['abc_on_ours']}"
            else:
                cells += " & -- & --"
        body += cells + " \\\\\n"
    ncol = "lrrrr" + ("rr" if have_abc else "")
    head = "Circuit & minterm & min-cube & DC spine & vs min-cube"
    if have_abc:
        head += " & ABC (no DC) & ABC on DC spine"
    abc_text = (
        " ABC columns: \\texttt{strash} plus an expanded \\texttt{resyn2} script run through "
        f"\\texttt{{{out['abc_binary']}}}; ``ABC (no DC)'' is applied to the minterm AIG with "
        "don't-cares forced to 0 (a standard flow), ``ABC on DC spine'' to our output."
        if have_abc
        else " ABC was not available."
    )
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Synthetic bio-circuit AIG gate counts (sum over nodes, no cross-node sharing). "
        "``minterm'': unoptimized ON-set SOP; ``min-cube'': the same pipeline (exact min-cube SOP, "
        "then factoring) \\emph{without} don't-cares; ``DC spine'': the same pipeline with exact "
        "satisfiability don't-cares; ``vs min-cube'': reduction from the don't-care spine alone."
        + abc_text
        + "}\n\\label{tab:bio}\n"
        f"\\resizebox{{\\linewidth}}{{!}}{{\\begin{{tabular}}{{{ncol}}}\n\\hline\n{head} \\\\\n\\hline\n"
        + body
        + "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )


def main() -> None:
    out = build()
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "bio_loop3.json").write_text(json.dumps(out, indent=2, default=str))
    write_tex(out, res / "bio_benchmark_table.tex")
    print(
        json.dumps(
            {
                "abc": out["abc_binary"],
                "gene_toy": out["gene_toy"]["totals"],
                "cascade24": out["cascade24"]["totals"],
                "cascade24_mismatches": out["cascade24"]["global_mismatches"],
                "cascade40": [s["totals"] for s in out["cascade40_seeds"]],
                "c17": {k: v for k, v in out["c17"].items() if k != "rows"},
                "objective_ablation": out["objective_ablation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
