#!/usr/bin/env python3
"""Tutorial 05 runner: collapse modes, collapse-branch audit, shotgun counterexample, cup-length."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from topospine.checkers.pass_trace import verify_pass_trace  # noqa: E402
from topospine.core.cohomology import CohomologyF2, sphere2, torus7, vertex_stars  # noqa: E402
from topospine.core.cubes import parse_boolean_cube  # noqa: E402
from topospine.core.cubical import CubicalComplex  # noqa: E402
from topospine.cover.auditor import exhaustive_min_cost  # noqa: E402
from topospine.cover.grid2d import (  # noqa: E402
    FILLED,
    HOLLOW,
    ABSENT,
    apply_transform,
    build_grid,
    collapsible_pairs,
    to_core,
)
from topospine.cover.minimize import minimize_cover  # noqa: E402
from topospine.cover.out_complex import out_complex_step, path6_collar_lockin_instance  # noqa: E402
from topospine.cover.shotgun import _instance, shotgun_minimize  # noqa: E402
from topospine.synth.ir import SynthesisState  # noqa: E402
from topospine.synth.manager import PassManager  # noqa: E402
from topospine.synth.passes import ShotgunCoveringCollapsePass  # noqa: E402

C9_ROWS = ["0000", "0001", "0010", "0011", "0101", "0110", "0111", "1000", "1001", "1010",
           "1011", "1100", "1101", "1110"]
C2_N5_A = ["00000", "00001", "00010", "00100", "00101", "01000", "01011", "01100", "01101", "01110",
           "10000", "10010", "10011", "10101", "10111", "11000", "11001", "11010", "11011", "11101",
           "11110"]


def bits(rows):
    return [tuple(int(c) for c in r) for r in rows]


def main() -> None:
    print("=== Tutorial 05: modes, shotgun shelling, cup-length ===\n")

    # 1. modes on two disjoint squares
    cx = CubicalComplex([parse_boolean_cube("--0"), parse_boolean_cube("--1")], name="two squares")
    for mode in ("homotopy", "covering"):
        st = SynthesisState(complex=cx, mode=mode)
        out = PassManager.default(mode=mode).run(st) if mode == "homotopy" else PassManager.covering().run(st)
        print(f"{mode:9s}: size {st.size()} -> {out.size()}, total dimension {st.total_dimension()} -> {out.total_dimension()}")
        if mode == "covering":
            assert out.size() == st.size(), "covering mode must preserve the column count"

    # 2. experimental shotgun pass: certificate accepted, optimality claim rejected
    st = SynthesisState(complex=cx, mode="covering")
    res = ShotgunCoveringCollapsePass().try_apply(st)
    ok, _ = verify_pass_trace(res.certificate, res.state, st)
    bad_ok, why = verify_pass_trace(dict(res.certificate, optimality_claim=True), res.state, st)
    print(f"\nshotgun pass: pairs {len(res.certificate['pairs'])}, checker accepts {ok}; "
          f"optimality claim accepted? {bad_ok} ({why[:40]}...)")
    assert ok and not bad_ok

    # 3. C9 counterexample: batch collapse loses optimality
    cm = _instance(4, bits(C9_ROWS))
    exh, _ = exhaustive_min_cost(cm)
    _, shot, stats = shotgun_minimize(cm, "safe")
    print(f"\nC9 instance ({cm.n_cols()} columns): exact optimum {exh:g}, safe-shotgun cover {shot:g} (batches {stats.batches})")
    assert shot > exh

    # 4. C2 counterexample at n = 5
    cm5 = _instance(5, bits(C2_N5_A))
    exh5, _ = exhaustive_min_cost(cm5, max_cols=22)
    _, bb, _ = minimize_cover(cm5.copy(), use_collapse=False)
    _, br, s5 = minimize_cover(cm5.copy(), use_collapse=True, require_admissible=True)
    print(f"C2 n=5 instance: exact {exh5:g}, plain B&B {bb:g}, collapse-branch {br:g} (collapse used {s5.collapse_used}x)")
    assert exh5 == bb < br

    # 4b. Grid local transform: 2x3 strip counterexample (vertex rows)
    cfg = {
        (0, 0): HOLLOW, (1, 0): ABSENT,
        (0, 1): FILLED, (1, 1): ABSENT,
        (0, 2): HOLLOW, (1, 2): ABSENT,
    }
    g = build_grid(cfg, 2, 3)
    core = to_core(g)
    assert core is not None
    p, f = collapsible_pairs(core)[0]
    tres = apply_transform(core, p, f)
    print(f"grid 2x3 strip: opt {tres.opt:g}, opt(P') {tres.c_exp:g}, put-back {tres.decoded_putback:g}")
    assert tres.c_exp > tres.opt

    # 4c. Out_complex P6 collar lock-in — Boolean non-core witness
    p6, j_ff = path6_collar_lockin_instance()
    exh_p6, _ = exhaustive_min_cost(p6)
    bad_tie = lambda sub: [sub.cols.index(nm) for nm in ("00-0", "0-11", "01-1")]
    res_p6 = out_complex_step(p6, j_ff, variant="keep_intersection", use_reduced=True, out_solver=bad_tie)
    print(f"Out_complex P6 (non-core): exact {exh_p6:g}, Step {res_p6.step_taken} (irredundant) {res_p6.cost:g}")
    assert exh_p6 == 3.0 and res_p6.cost == 4.0

    # 5. cohomology
    T, S = CohomologyF2(torus7()), CohomologyF2(sphere2())
    print(f"\ntorus : betti {T.betti()}, cup-length {T.cup_length()}")
    print(f"sphere: betti {S.betti()}, cup-length {S.cup_length()}")
    stars = vertex_stars(torus7())
    assert all(T.restriction_is_zero_on_positive_cohomology(t) for t in stars.values())
    print(f"vertex stars of the torus are cohomologically trivial; LS bound: any such cover has >= {T.cup_length() + 1} pieces")
    assert T.cup_length() == 2 and S.cup_length() == 1
    print("\nTutorial 05 OK.")


if __name__ == "__main__":
    main()
