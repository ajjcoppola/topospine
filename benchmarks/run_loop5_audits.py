#!/usr/bin/env python3
"""n=5 collapse-branch failure rate, (H) filters, and c17 gate sharing.

Writes benchmarks/results/loop5_audit.json and loop5_audit_table.tex.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.cover.hypothesis_h import CANDIDATES, classify_predicate  # noqa: E402
from topospine.cover.minimize import minimize_cover  # noqa: E402
from topospine.cover.shotgun import enumerate_instances  # noqa: E402
from topospine.formats import read_blif, spec_to_states  # noqa: E402
from topospine.synth.aig import shared_factored_gates  # noqa: E402
from topospine.synth.logic_passes import DontCareSpinePass, LogicPassManager, find_abc, abc_optimize_blif_text  # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [centre - half, centre + half]


def failure_rate(n_vars: int, sample: int, seed: int) -> dict:
    inst = enumerate_instances(n_vars, sample, seed=seed)
    fired = bad = 0
    for cm in inst:
        _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
        _, got, st = minimize_cover(cm.copy(), use_collapse=True, require_admissible=True)
        fired += int(st.collapse_used > 0)
        bad += int(got != std)
    return {
        "n_vars": n_vars,
        "sample": len(inst),
        "seed": seed,
        "collapse_fired": fired,
        "disagreements": bad,
        "rate_all": bad / len(inst),
        "wilson95_all": wilson(bad, len(inst)),
        "rate_when_fired": (bad / fired) if fired else None,
        "wilson95_when_fired": wilson(bad, fired) if fired else None,
        "comparison": "plain branch-and-bound, not a fresh exhaustive oracle",
    }


def c17_sharing() -> dict:
    text = (ROOT / "examples" / "data" / "c17.blif").read_text()
    spec = read_blif(text)
    cube_lists = []
    separate_pipeline = 0
    for _name, st in spec_to_states(spec).items():
        out = LogicPassManager().run(st)
        separate_pipeline += out.gates()
        covered = DontCareSpinePass().try_apply(st)
        cube_lists.append(covered.state.cubes)
    shared = shared_factored_gates(spec.n, cube_lists)
    abc = abc_optimize_blif_text(text) if find_abc() else {"ands_final": None}
    return {
        "reference_nand2_gates": spec.gate_count_reference,
        "abc_on_original_netlist_ands": abc.get("ands_final"),
        "pipeline_gates_summed": separate_pipeline,
        **shared,
        "note": "shared count hashes the factored SOPs of each output into one AIG; it is not retimed against the NAND netlist",
    }


def write_tex(rate: dict, preds: dict, c17: dict, path: Path) -> None:
    lo, hi = rate["wilson95_all"]
    rows = ""
    for name, rec in preds.items():
        rows += f"{name.replace('_', ' ')} & {rec['status']} & {rec['fired']} & {rec['disagreements']} \\\\\n"
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Collapse-branch on "
        f"{rate['sample']} random $n={rate['n_vars']}$ ON-sets (seed {rate['seed']}). "
        f"Disagreements with plain B\\&B: {rate['disagreements']} "
        f"(rate {rate['rate_all']:.4f}, Wilson 95\\% interval [{lo:.4f}, {hi:.4f}]). "
        f"The branch fired on {rate['collapse_fired']} instances. "
        "Filters are decidable restrictions of that branch. "
        f"c17: summed pipeline {c17['pipeline_gates_summed']} gates, "
        f"shared factored AIG {c17['gates_shared']}, "
        f"ABC on the NAND netlist {c17['abc_on_original_netlist_ands']}.}}\n"
        "\\label{tab:audit5}\n\\begin{tabular}{lrrr}\n\\hline\n"
        "filter & status & times fired & disagreements \\\\\n\\hline\n"
        + rows
        + "\\hline\n\\end{tabular}\n\\end{table}\n"
    )


def main() -> None:
    rate = failure_rate(5, 40000, seed=21)
    # filters on a smaller slice: 4000 random n=5 plus the cost of re-solving
    inst = enumerate_instances(5, 4000, seed=21)
    preds = {name: classify_predicate(pred, inst) for name, pred in CANDIDATES.items()}
    sharing = c17_sharing()
    out = {"failure_rate": rate, "filters_on_4000": preds, "c17": sharing}
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "loop5_audit.json").write_text(json.dumps(out, indent=2))
    write_tex(rate, preds, sharing, res / "loop5_audit_table.tex")
    print(json.dumps({"rate": rate, "filters": {k: v["status"] for k, v in preds.items()}, "c17": sharing}, indent=2))


if __name__ == "__main__":
    main()
