#!/usr/bin/env python3
"""Head-to-head Espresso-family + Espresso-Horn benchmark for Paper A."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from topospine.core.cubes import BooleanCube
from topospine.cover.cube_array import minimize_cube_array
from topospine.cover.espresso_variants import (
    abc_isop_minimize,
    boom_cd_minimize,
    cover_contains_on,
    espresso_horn_minimize,
    espresso_ii_minimize,
    espresso_signature_minimize,
    highs_lp_ilp_bound,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "benchmarks" / "results" / "espresso_horn_bench.json"
OUT_TEX = ROOT / "benchmarks" / "results" / "espresso_horn_bench_table.tex"


def _random_on(n: int, k: int, rng: random.Random) -> list[BooleanCube]:
    mins = rng.sample(range(2**n), k)
    out: list[BooleanCube] = []
    for m in mins:
        bits = tuple((m >> i) & 1 for i in range(n - 1, -1, -1))
        out.append(BooleanCube(bits))
    return out


def _run_family(on: list[BooleanCube]) -> dict:
    row: dict = {"n_on": len(on), "n": len(on[0].bits)}
    try:
        opt = int(minimize_cube_array(on).cost)
    except Exception as exc:
        opt = -1
        row["opt_error"] = repr(exc)
    row["opt"] = opt

    variants = {
        "espresso_ii": lambda: espresso_ii_minimize(on),
        "espresso_signature": lambda: espresso_signature_minimize(on),
        "boom_cd": lambda: boom_cd_minimize(on),
        "abc_isop": lambda: abc_isop_minimize(on),
        "highs_lp_ilp": lambda: highs_lp_ilp_bound(on, solve_milp=True),
        "espresso_horn": lambda: espresso_horn_minimize(on, mode="exact"),
    }
    for name, fn in variants.items():
        t0 = time.perf_counter()
        try:
            res = fn()
            ok = res.cost >= 0 and cover_contains_on(res.cover, on) if res.cover else res.cost == 0
            row[name] = {
                "cost": res.cost,
                "L": res.lower_bound,
                "U": res.upper_bound,
                "certified": res.certified_optimal,
                "sccc_stalled": res.sccc_stalled,
                "horn_splits": res.horn_splits,
                "covers": ok,
                "time_s": time.perf_counter() - t0,
                "meta": {k: v for k, v in (res.meta or {}).items() if k in (
                    "available", "z_lp", "ceil_lp", "zero_integrality_gap", "L_MIS", "ceil_LP", "mode"
                )},
            }
        except Exception as exc:
            row[name] = {"cost": -1, "error": repr(exc), "time_s": time.perf_counter() - t0}
    return row


def main() -> None:
    rng = random.Random(23)
    rows: list[dict] = []

    # Random n=5,6 ON-sets
    for n, k, trials in ((5, 10, 8), (6, 12, 6)):
        for t in range(trials):
            on = _random_on(n, k, rng)
            row = _run_family(on)
            row["family"] = f"random_n{n}"
            row["trial"] = t
            rows.append(row)

    # sccc-prone antipodal pair (already expanded primes)
    on_anti = [
        BooleanCube((0, 0, b0, b1))
        for b0 in (0, 1)
        for b1 in (0, 1)
    ] + [
        BooleanCube((1, 1, b0, b1))
        for b0 in (0, 1)
        for b1 in (0, 1)
    ]
    row = _run_family(on_anti)
    row["family"] = "antipodal_00_11"
    rows.append(row)

    # Sparse high-n: few cubes in n=12
    sparse = [
        BooleanCube((0, 0, 0) + (None,) * 9),
        BooleanCube((1, 1, 1) + (None,) * 9),
        BooleanCube((0, 1, None) + (0,) * 9),
    ]
    row = _run_family(sparse)
    row["family"] = "sparse_n12"
    rows.append(row)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_instances": len(rows),
        "rows": rows,
    }
    # Aggregate mean costs where covers
    agg: dict[str, list[float]] = {}
    for r in rows:
        for name in (
            "espresso_ii",
            "espresso_signature",
            "boom_cd",
            "abc_isop",
            "highs_lp_ilp",
            "espresso_horn",
        ):
            cell = r.get(name) or {}
            if cell.get("covers") and isinstance(cell.get("cost"), int) and cell["cost"] >= 0:
                agg.setdefault(name, []).append(float(cell["cost"]))
    summary["mean_cost"] = {k: sum(v) / len(v) for k, v in agg.items() if v}
    summary["horn_certified_rate"] = sum(
        1 for r in rows if (r.get("espresso_horn") or {}).get("certified")
    ) / max(1, len(rows))

    OUT_JSON.write_text(json.dumps(summary, indent=2))

    means = summary["mean_cost"]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Espresso-family head-to-head mean cover sizes "
        rf"(${summary['n_instances']}$ instances; "
        rf"Espresso-Horn certified rate "
        + f"${summary['horn_certified_rate']:.2f}$" + r").}",
        r"\label{tab:espresso-horn}",
        r"\begin{tabular}{lrr}",
        r"\hline",
        r"Variant & mean cost & notes \\",
        r"\hline",
    ]
    notes = {
        "espresso_ii": "Brayton 1984",
        "espresso_signature": "McGeer 1993",
        "boom_cd": "Fiser--Hlavicka",
        "abc_isop": "yosys-abc ISOP",
        "highs_lp_ilp": "HiGHS LP/MILP",
        "espresso_horn": "H1--H4 + E1",
    }
    for name in (
        "espresso_ii",
        "espresso_signature",
        "boom_cd",
        "abc_isop",
        "highs_lp_ilp",
        "espresso_horn",
    ):
        mc = means.get(name)
        mc_s = f"{mc:.2f}" if mc is not None else "---"
        tex_name = name.replace("_", r"\_")
        lines.append(f"{tex_name} & {mc_s} & {notes[name]} \\\\")
    lines += [
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    OUT_TEX.write_text("\n".join(lines))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_TEX}")
    print("mean_cost", means)
    print("horn_certified_rate", summary["horn_certified_rate"])


if __name__ == "__main__":
    main()
