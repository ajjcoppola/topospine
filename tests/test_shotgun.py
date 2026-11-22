"""Loop 4: shotgun shelling (claim C9) -- audit evidence and the experimental pass."""

from __future__ import annotations

from topospine.checkers.pass_trace import verify_pass_trace
from topospine.core.cubes import parse_boolean_cube
from topospine.core.cubical import CubicalComplex
from topospine.cover.auditor import exhaustive_min_cost
from topospine.cover.minimize import minimize_cover
from topospine.cover.shotgun import (
    _instance,
    audit_shotgun,
    enumerate_instances,
    select_batch,
    shotgun_minimize,
)
from topospine.synth.ir import SynthesisState
from topospine.synth.passes import ShotgunCoveringCollapsePass


def two_squares() -> SynthesisState:
    cx = CubicalComplex([parse_boolean_cube("--0"), parse_boolean_cube("--1")], name="two squares")
    return SynthesisState(complex=cx, mode="covering")


def test_shotgun_pass_applies_independent_batch_without_optimality_claim():
    st = two_squares()
    res = ShotgunCoveringCollapsePass().try_apply(st)
    assert res.accepted and len(res.certificate["pairs"]) == 2
    assert res.certificate["optimality_claim"] is False
    ok, why = verify_pass_trace(res.certificate, res.state, st)
    assert ok, why
    assert res.state.size() == 2


def test_checker_rejects_shotgun_optimality_claim():
    st = two_squares()
    res = ShotgunCoveringCollapsePass().try_apply(st)
    bad = dict(res.certificate, optimality_claim=True)
    ok, why = verify_pass_trace(bad, res.state, st)
    assert not ok and "C9" in why


def test_sequential_collapse_branch_matches_exhaustive_on_all_n3_and_sampled_n4():
    insts = enumerate_instances(3, None) + enumerate_instances(4, 3000, seed=5)
    used = 0
    for cm in insts:
        _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
        idx, col, st = minimize_cover(cm.copy(), use_collapse=True, require_admissible=True)
        used += st.collapse_used > 0
        assert col == std and cm.is_cover(idx)
    assert used > 0


def _counterexample():
    rows = ['0000', '0001', '0010', '0011', '0101', '0110', '0111', '1000', '1001', '1010',
            '1011', '1100', '1101', '1110']
    return _instance(4, [tuple(int(ch) for ch in r) for r in rows])


def test_c9_counterexample_batch_loses_optimality_even_with_safe_independence():
    cm = _counterexample()
    assert cm.n_cols() == 7
    exh, _ = exhaustive_min_cost(cm)
    _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
    _, seq, _ = minimize_cover(cm.copy(), use_collapse=True, require_admissible=True)
    assert exh == std == seq == 4.0
    idx, sg, st = shotgun_minimize(cm, "safe")
    assert st.batches == 1 and st.max_batch == 2
    assert cm.is_cover(idx) and sg == 5.0 > exh  # feasible but suboptimal: C9 fails


def test_naive_batches_can_make_the_reduced_table_infeasible():
    inst = enumerate_instances(4, 2000, seed=1)
    a_rows = audit_shotgun(inst, "rows")
    a_safe = audit_shotgun(inst, "safe")
    assert a_rows["reduced_table_infeasible"] > 0
    assert a_safe["reduced_table_infeasible"] == 0 and a_safe["infeasible_decodes"] == 0
    assert a_rows["std_vs_exhaustive_disagreements"] == 0


def test_select_batch_validates_rule():
    import pytest

    with pytest.raises(ValueError):
        select_batch(_counterexample(), "bogus")


# ---------------------------------------------------------------- C2 counterexamples (n = 5)
C2_ROWS = {
    "n5_a": ['00000', '00001', '00010', '00100', '00101', '01000', '01011', '01100', '01101', '01110',
             '10000', '10010', '10011', '10101', '10111', '11000', '11001', '11010', '11011', '11101',
             '11110'],
    "n5_b": ['00001', '00010', '00011', '00100', '00110', '01000', '01001', '01010', '01011', '01110',
             '10000', '10001', '10010', '10011', '10101', '10110', '10111', '11000', '11001', '11010',
             '11101', '11111'],
}


def test_c2_collapse_branch_is_suboptimal_on_two_n5_instances_but_feasible():
    """The 'narrowed' CoverAdmissibleFreeFace collapse-branch loses 1 on these (exhaustive-confirmed)."""
    expected = {"n5_a": (8.0, 9.0), "n5_b": (7.0, 8.0)}
    for name, rows in C2_ROWS.items():
        cm = _instance(5, [tuple(int(ch) for ch in r) for r in rows])
        opt, col = expected[name]
        exh, _ = exhaustive_min_cost(cm, max_cols=22)
        _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
        idx, seq, st = minimize_cover(cm.copy(), use_collapse=True, require_admissible=True)
        assert exh == std == opt
        assert seq == col > exh and cm.is_cover(idx) and st.collapse_used > 0


def test_dont_care_spine_is_unaffected_by_c2_counterexample():
    from topospine.checkers.logic_trace import verify_logic_trace
    from topospine.synth.logic_passes import DontCareSpinePass, LogicState

    on = {int(r, 2) for r in C2_ROWS["n5_a"]}
    res = DontCareSpinePass().try_apply(LogicState.from_minterms(5, on))
    assert res.certificate["cost"] == 8.0
    assert res.certificate["optimality"] == "ProvenMinimum"
    assert res.certificate["collapse_branch_agrees"] is False
    ok, why = verify_logic_trace(res.certificate, res.state)
    assert ok, why
