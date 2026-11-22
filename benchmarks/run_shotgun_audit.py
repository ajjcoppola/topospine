#!/usr/bin/env python3
"""Loop 4 audit of claim C9 (shotgun shelling) and of the sequential collapse-branch (C2).

n=3: all 255 ON-sets.  n=4: all 65535 ON-sets.  n=5: seeded random sample.
Oracle: exhaustive search when <= 12 prime columns, otherwise standard B&B (validated
against exhaustive wherever both ran: 0 disagreements).
Writes benchmarks/results/shotgun_loop4.json and shotgun_audit_table.tex.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.cover.minimize import minimize_cover  # noqa: E402
from topospine.cover.shotgun import audit_shotgun, enumerate_instances  # noqa: E402


def sequential_audit(instances) -> dict:
    used = bad = 0
    for cm in instances:
        _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
        idx, col, st = minimize_cover(cm.copy(), use_collapse=True, require_admissible=True)
        used += st.collapse_used > 0
        if col != std or not cm.is_cover(idx):
            bad += 1
    return {"instances": len(instances), "collapse_used": used, "disagreements": bad}


def main() -> None:
    t0 = time.perf_counter()
    out: dict = {"sets": []}
    for label, n, sample, seed in (("n=3 (all)", 3, None, 0), ("n=4 (all)", 4, None, 0), ("n=5 (sample 1500)", 5, 1500, 7)):
        inst = enumerate_instances(n, sample, seed)
        entry = {"label": label, "n_vars": n, "sequential": sequential_audit(inst), "shotgun": {}}
        for rule in ("none", "rows", "safe"):
            r = audit_shotgun(inst, rule, exhaustive_cols=12)
            r.pop("examples")
            entry["shotgun"][rule] = r
        out["sets"].append(entry)
        print(label, json.dumps(entry["sequential"]), {k: (v["nontrivial_instances"], v["cost_mismatches"], v["infeasible_decodes"]) for k, v in entry["shotgun"].items()}, flush=True)
    out["wall_time_s"] = time.perf_counter() - t0
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "shotgun_loop4.json").write_text(json.dumps(out, indent=2))
    rows = ""
    for e in out["sets"]:
        s = e["sequential"]
        rows += f"{e['label']} & {s['collapse_used']} / {s['disagreements']}"
        for rule in ("none", "rows", "safe"):
            g = e["shotgun"][rule]
            rows += f" & {g['nontrivial_instances']} / {g['cost_mismatches']} / {g['reduced_table_infeasible']}"
        rows += " \\\\\n"
    (res / "shotgun_audit_table.tex").write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Audit of the collapse-branch and of shotgun (simultaneous) collapse against an exact oracle on "
        "Boolean covering instances. Sequential: instances where the collapse branch fired / disagreements with the exact "
        "optimum. Shotgun rules: nontrivial instances (a batch was applied) / cost mismatches / reduced tables left infeasible. "
        "``none'': all admissible pairs; ``rows'': pairwise row-disjoint faces; ``safe'': row-disjoint plus a coverability guard.}\n"
        "\\label{tab:shotgun}\n\\resizebox{\\linewidth}{!}{\\begin{tabular}{lrrrr}\n\\hline\n"
        "set & sequential & shotgun none & shotgun rows & shotgun safe \\\\\n\\hline\n"
        + rows + "\\hline\n\\end{tabular}}\n\\end{table}\n"
    )


if __name__ == "__main__":
    main()
