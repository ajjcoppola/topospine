#!/usr/bin/env python3
"""Real Betti numbers, pair-collapse resource counts, random-deletion baseline.

Classical linear algebra only.  No device and no speedup is claimed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.core.cohomology import CohomologyF2, sphere2, torus7  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402
from topospine.core.laplacian import (  # noqa: E402
    cubical_spectrum,
    delete_one_top,
    pair_collapse_cubical,
    resource_counts,
    rp2,
    simplicial_betti_real,
)


def _pad(a, b):
    n = max(len(a), len(b))
    return a + [0] * (n - len(a)), b + [0] * (n - len(b))


def main() -> None:
    surfaces = []
    for name, facets in (("torus7", torus7()), ("sphere2", sphere2()), ("RP2", rp2())):
        surfaces.append({
            "complex": name,
            "betti_f2": CohomologyF2(facets).betti(),
            "betti_real": simplicial_betti_real(facets),
        })
    square = CubicalComplex([parse_boolean_cube("--")], name="square")
    before = cubical_spectrum(square)
    after = cubical_spectrum(pair_collapse_cubical(square))
    cycle = CubicalComplex(
        [parse_boolean_cube(s) for s in ("01-", "0-1", "-01", "10-", "1-0", "-10")],
        name="C6",
    )
    cyc_before = cubical_spectrum(cycle)
    cyc_del = cubical_spectrum(delete_one_top(cycle))
    out = {
        "surfaces": surfaces,
        "square_pair_collapse": {
            "cells_before": before["n_cells"],
            "cells_after": after["n_cells"],
            "betti_before": before["betti_real"],
            "betti_after": after["betti_real"],
            "betti_preserved": _pad(before["betti_real"], after["betti_real"])[0]
            == _pad(before["betti_real"], after["betti_real"])[1],
            "gap_before": before["spectral_gaps"],
            "gap_after": after["spectral_gaps"],
            "resources_before": resource_counts(before["n_cells"]),
            "resources_after": resource_counts(after["n_cells"]),
        },
        "cycle_delete_one_edge": {
            "betti_before": cyc_before["betti_real"],
            "betti_after": cyc_del["betti_real"],
            "cells_before": cyc_before["n_cells"],
            "cells_after": cyc_del["n_cells"],
        },
    }
    res = ROOT / "benchmarks" / "results"
    res.mkdir(parents=True, exist_ok=True)
    (res / "quantum_loop5.json").write_text(json.dumps(out, indent=2))
    rows = ""
    for s in surfaces:
        rows += f"{s['complex']} & {' '.join(map(str, s['betti_f2']))} & {' '.join(map(str, s['betti_real']))} \\\\\n"
    sq = out["square_pair_collapse"]
    path = res / "quantum_bench_table.tex"
    path.write_text(
        "\\begin{table}[h]\n\\centering\\small\n"
        "\\caption{Real versus $\\mathbb F_2$ Betti numbers, and one elementary pair collapse. "
        "The square's positive spectral gap changes "
        f"({sq['gap_before'][0]:.3f} $\\to$ {sq['gap_after'][0]:.3f}) while the kernel dimension does not. "
        f"One-qubit-per-cell encoding: {sq['resources_before']['qubits_one_per_cell']} $\\to$ "
        f"{sq['resources_after']['qubits_one_per_cell']}. "
        "Deleting one edge of a 6-cycle (not a collapse) changes the Betti numbers.}\n"
        "\\label{tab:quantum}\n\\begin{tabular}{lcc}\n\\hline\n"
        "complex & $\\beta(\\mathbb F_2)$ & $\\beta(\\mathbb R)$ \\\\\n\\hline\n"
        + rows
        + "\\hline\n\\end{tabular}\n\\end{table}\n"
    )
    print(json.dumps({"surfaces": surfaces, "square_cells": [sq["cells_before"], sq["cells_after"]],
                      "cycle_betti": [out["cycle_delete_one_edge"]["betti_before"], out["cycle_delete_one_edge"]["betti_after"]]}, indent=2))


if __name__ == "__main__":
    main()
