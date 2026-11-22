#!/usr/bin/env python3
"""Tutorial 04 runner: covering-mode collapse, AIG/don't-care spine, bio cascade, molecular tower."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "applications" / "molecular"))

from mol_pipeline import run_one, synthetic_conformations  # noqa: E402
from topospine.checkers.logic_trace import verify_logic_trace  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402
from topospine.examples.bio_circuits import run_cascade, run_gene_toy  # noqa: E402
from topospine.synth.ir import SynthesisState  # noqa: E402
from topospine.synth.logic_passes import DontCareSpinePass, LogicPassManager, LogicState  # noqa: E402
from topospine.synth.passes import (  # noqa: E402
    ElementaryCubicalCollapsePass,
    covering_collapse_closure,
)


def main() -> None:
    print("=== Tutorial 04: ABC factor diagrams, bio circuits, molecular spines ===\n")

    # 1. covering-mode collapse never empties the IR
    sq = SynthesisState(complex=CubicalComplex([parse_boolean_cube("--")], name="square"))
    print("deletion-style collapse   :", ElementaryCubicalCollapsePass().try_apply(sq).state.size(), "columns left")
    closed = covering_collapse_closure(sq)
    print("covering-mode collapse    :", closed.size(), "column(s); decode map", closed.meta["decode"])
    assert closed.size() == 1

    # 2. don't-care spine on the classic K-map example
    on, dc = {4, 8, 10, 11, 12, 15}, {9, 14}
    plain = LogicPassManager().run(LogicState.from_minterms(4, on))
    withdc = LogicPassManager().run(LogicState.from_minterms(4, on, dc))
    print("\nK-map f: gates minterm/no-DC/with-DC =",
          LogicState.from_minterms(4, on).gates(), plain.gates(), withdc.gates())
    spine = DontCareSpinePass().try_apply(LogicState.from_minterms(4, on, dc))
    ok, why = verify_logic_trace(spine.certificate, spine.state)
    print("independent check:", ok, why, "| optimality:", spine.certificate["optimality"])
    assert ok and withdc.gates() <= plain.gates()
    abc = next(e for e in withdc.log if e.get("pass") == "AbcBaselineAdapter")
    print("ABC on PATH:", abc["abc_available"], "->", abc["action"])

    # 3. bio circuits
    toy = run_gene_toy()["totals"]
    cas = run_cascade(24, 6, 2026)
    print("\ngene toy gates   :", toy)
    print("cascade-24 gates :", cas["totals"], "| global mismatches:", cas["global_mismatches"],
          "| witnesses ok:", cas["all_witnesses_ok"])
    assert cas["global_mismatches"] == 0 and cas["all_witnesses_ok"]

    # 4. molecular relative tower
    pts, A, meta = synthetic_conformations()
    out = run_one(pts, A, base_scale=2.4)
    for mode in ("coverage_only", "relative"):
        d = out[mode]
        print(f"\n[{mode}] cover sizes {d['cover_sizes']}  A-radius {[round(r, 2) for r in d['A_cover_radius']]}")
    assert out["relative"]["relative_equivalence_checked"]
    print("\nsource:", meta["source"], "(synthetic geometry; set TOPOSPINE_MD17_NPZ for MD17)")
    print("\nTutorial 04 OK.")


if __name__ == "__main__":
    main()
