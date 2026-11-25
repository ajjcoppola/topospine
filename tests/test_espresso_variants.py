"""Tests for Espresso-family variants, Espresso-Horn, and HornRetractionCollapsePass."""

from __future__ import annotations

import pytest

from topospine.core.cubes import BooleanCube, parse_boolean_cube as P
from topospine.core.covering import graded_table_from_cubical
from topospine.core.cubical import CubicalComplex
from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes
from topospine.cover.espresso_variants import (
    _sccc_reduce,
    abc_isop_minimize,
    boom_cd_minimize,
    cover_contains_on,
    espresso_horn_minimize,
    espresso_ii_minimize,
    espresso_signature_minimize,
    find_abc_binary,
    highs_lp_ilp_bound,
)
from topospine.cover.out_complex import irredundant_cover
from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.synth.ir import SynthesisState
from topospine.synth.passes import (
    CoveringAwareCollapsePass,
    HornRetractionCollapsePass,
    covering_collapse_closure,
    horn_retraction_closure,
)
from topospine.checkers.pass_trace import verify_pass_trace


def _on_equal_bits() -> list[BooleanCube]:
    """ON-set x0==x1 on n=4 (union of 00-- and 11--)."""
    on: list[BooleanCube] = []
    for a in range(16):
        bits = tuple((a >> i) & 1 for i in range(3, -1, -1))
        if bits[0] == bits[1]:
            on.append(BooleanCube(bits))
    return on


def test_espresso_ii_covers_and_may_stall_on_expanded_primes():
    on = _on_equal_bits()
    res = espresso_ii_minimize(on)
    assert res.cost >= 2
    assert cover_contains_on(res.cover, on)
    # Maximally expanded antipodal cover is a classical sccc local fixed point
    stuck = [P("00--"), P("11--")]
    _, stalled = _sccc_reduce(stuck, on)
    assert stalled


def test_signature_boom_cover_on():
    on = _on_equal_bits()
    for fn in (espresso_signature_minimize, boom_cd_minimize):
        res = fn(on)
        assert res.cost >= 1
        assert cover_contains_on(res.cover, on)


@pytest.mark.skipif(find_abc_binary() is None, reason="abc / yosys-abc not installed")
def test_abc_isop_parity_with_care_set():
    on = _on_equal_bits()
    res = abc_isop_minimize(on)
    assert res.meta.get("available")
    assert res.cost >= 1
    assert cover_contains_on(res.cover, on)
    # ISOP size should match the two-cube optimum on this function
    assert res.cost == 2


def test_highs_lp_mis_window_sound():
    on = _on_equal_bits()
    res = highs_lp_ilp_bound(on, solve_milp=True)
    assert res.meta.get("lp_success")
    assert res.lower_bound <= res.cost
    assert res.cost == 2
    assert res.meta.get("ceil_lp") <= res.cost
    if res.meta.get("zero_integrality_gap"):
        assert res.certified_optimal


def test_espresso_horn_window_and_coverage():
    on = _on_equal_bits()
    res = espresso_horn_minimize(on, mode="exact")
    assert cover_contains_on(res.cover, on)
    assert res.lower_bound <= res.cost <= res.upper_bound
    assert res.cost == 2


def test_sccc_stall_escaped_by_horn_on_covering_table():
    """Layer-0 5×4 residual: stuck irredundant cost 3 → horn faces → opt 2.

    Matches Lean ``sccc_stall_escaped_by_horn`` / HornChains ``5×4`` masks.
    """
    from topospine.cover.cube_array import _solve_unit_bitmask_bb
    from topospine.core.covering import CoveringMatrix

    # Bitmasks 26,21,12,3 on univ=31 (5 rows)
    masks = [26, 21, 12, 3]
    univ = 31
    matrix = [[bool((masks[j] >> i) & 1) for j in range(4)] for i in range(5)]
    cols = [P(s) for s in ["---10", "--01-", "-0-1-", "0--1-"]]
    cm = CoveringMatrix(
        rows=[f"r{i}" for i in range(5)],
        cols=[str(c) for c in cols],
        matrix=matrix,
        weights=[1.0] * 4,
        col_cubes=cols,
    )
    stuck = [1, 2, 3]
    assert cm.is_cover(stuck)
    assert irredundant_cover(cm, stuck) == stuck
    # Each stuck column has nonempty private residual (sccc cannot drop it)
    for j in stuck:
        others = 0
        for k in stuck:
            if k != j:
                others |= masks[k]
        assert masks[j] & ~others
    opt_sol, _ = _solve_unit_bitmask_bb(masks, univ)
    assert len(opt_sol) == 2
    assert len(opt_sol) < len(stuck)
    # Horn-augmented table (cols 1..3 + horn faces of col0): cost 2
    hmasks = [21, 12, 3, 2, 8, 18, 16, 10]
    hsol, _ = _solve_unit_bitmask_bb(hmasks, univ)
    assert len(hsol) == 2


def test_horn_retraction_pass_nonvacuous_on_2007():
    cx = coppola_2007_boolean_complex()
    st = SynthesisState(complex=cx, mode="covering")
    assert CoveringAwareCollapsePass().try_apply(st).accepted is False
    cm = graded_table_from_cubical(cx)
    free = list_collapsible_primes(cm)
    assert free
    assert all(not cover_admissible_free_face(cm, j, f) for j, fs in free for f in fs)
    assert covering_collapse_closure(st).log == []

    res = HornRetractionCollapsePass().try_apply(st)
    assert res.accepted
    ok, why = verify_pass_trace(res.certificate, res.state, st)
    assert ok, why
    assert res.certificate["cohomology_preserved"]
    assert res.certificate["dim_after"] < res.certificate["dim_before"]
    closed = horn_retraction_closure(st)
    assert len(closed.log) >= 1
    assert max(c.dimension for c in closed.complex.top_cells) < max(
        c.dimension for c in st.complex.top_cells
    )


def test_horn_retraction_on_3cube_voxel():
    st = SynthesisState(
        complex=CubicalComplex([BooleanCube((None, None, None))], name="voxel"),
        mode="covering",
    )
    res = HornRetractionCollapsePass().try_apply(st)
    assert res.accepted
    ok, why = verify_pass_trace(res.certificate, res.state, st)
    assert ok, why
    closed = horn_retraction_closure(st)
    assert len(closed.log) >= 1
