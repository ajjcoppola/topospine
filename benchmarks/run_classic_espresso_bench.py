#!/usr/bin/env python3
"""Classic Espresso CLI + ABC-Horn SOP refine bench (Paper E / C58)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.core.cubes import parse_boolean_cube as P
from topospine.cover.espresso_variants import (
    abc_isop_minimize,
    classic_espresso_minimize,
    espresso_horn_minimize,
    find_classic_espresso,
)
from topospine.synth.aig import minterm_sop
from topospine.synth.logic_passes import AbcHornSopRefinePass, LogicState


def main() -> None:
    examples_dir = ROOT / "third_party" / "espresso" / "examples"
    rows = []
    # Built-in cyclic-ish ON
    on = [P(s) for s in ["--00", "-0-0", "0--0", "0-0-", "00--", "-00-"]]
    for name, cubes in [
        ("hex_ring", on),
        ("antipodal", [P("00--"), P("11--")]),
    ]:
        row = {"name": name, "n_on": len(cubes)}
        for label, fn in [
            ("classic", classic_espresso_minimize),
            ("abc_isop", abc_isop_minimize),
            ("horn", espresso_horn_minimize),
        ]:
            r = fn(cubes)
            row[label] = {"cost": r.cost, "time_s": r.wall_time_s, "meta": r.meta}
        rows.append(row)

    # A few Berkeley example PLAs if present
    if examples_dir.is_dir():
        for pla in sorted(examples_dir.glob("*"))[:6]:
            if pla.is_dir():
                continue
            text = pla.read_text(errors="ignore")
            if ".i" not in text:
                continue
            from topospine.cover.espresso_variants import pla_cubes_from_text

            cubes = pla_cubes_from_text(text)
            if not cubes or len(cubes[0].bits) > 12:
                continue
            row = {"name": pla.name, "n_on": len(cubes)}
            r = classic_espresso_minimize(cubes, timeout_s=20)
            row["classic"] = {"cost": r.cost, "time_s": r.wall_time_s}
            r2 = espresso_horn_minimize(cubes)
            row["horn"] = {"cost": r2.cost, "time_s": r2.wall_time_s}
            rows.append(row)

    # AbcHornSopRefine witness
    st = LogicState.from_minterms(4, {0, 1, 2, 3, 12, 13, 14, 15})
    before = len(st.cubes)
    res = AbcHornSopRefinePass().try_apply(st)
    witness = {
        "accepted": res.accepted,
        "cubes_before": before,
        "cubes_after": res.certificate.get("cubes_after"),
        "abc_isop_cubes": res.certificate.get("abc_isop_cubes"),
        "horn_cubes": res.certificate.get("horn_cubes"),
        "action": res.certificate.get("action"),
    }

    out = {
        "espresso_binary": find_classic_espresso(),
        "rows": rows,
        "abc_horn_witness": witness,
    }
    results = ROOT / "benchmarks" / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "classic_espresso_bench.json").write_text(json.dumps(out, indent=2))
    tex = results / "classic_espresso_bench_table.tex"
    lines = [
        r"\begin{table}[h]\centering\small",
        r"\caption{Classic Espresso CLI vs ABC ISOP vs Espresso-Horn (Paper~E).}",
        r"\label{tab:classic-espresso}",
        r"\begin{tabular}{lrrr}\hline",
        r"instance & classic & ABC ISOP & Horn \\\hline",
    ]
    for row in rows:
        c = (row.get("classic") or {}).get("cost", "---")
        a = (row.get("abc_isop") or {}).get("cost", "---")
        h = (row.get("horn") or {}).get("cost", "---")
        tex_name = row["name"].replace("_", r"\_")
        lines.append(f"{tex_name} & {c} & {a} & {h} \\\\")
    lines += [r"\hline\end{tabular}\end{table}", ""]
    tex.write_text("\n".join(lines))
    print(json.dumps(out, indent=2)[:2000])


if __name__ == "__main__":
    main()
