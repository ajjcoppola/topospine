"""Tests for the 4-step ``Out_complex`` collapsible-cube reduction and its limits."""

from __future__ import annotations

from itertools import product

import pytest

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube
from topospine.core.cubical import CubicalComplex
from topospine.cover.auditor import _primes_from_minterms, exhaustive_min_cost
from topospine.cover.collapse import list_collapsible_primes
from topospine.cover.out_complex import (
    OUT_VARIANTS,
    audit_out_complex_on_cyclic_cores,
    build_out_complex,
    check_h_out,
    cyclic_core_exclude_win_n5,
    cyclic_core_step3_trap_n4,
    irredundant_cover,
    out_complex_step,
    path4_bridge_instance,
    path6_collar_lockin_instance,
)
from topospine.cover.shotgun import enumerate_instances


def test_path4_bridge_shows_why_step4_needs_reduced_cov():
    cm, col_j = path4_bridge_instance()
    exh, _ = exhaustive_min_cost(cm)
    assert exh == 2.0

    raw = out_complex_step(cm, col_j, variant="keep_intersection", use_reduced=False)
    assert raw.is_feasible and raw.step_taken == 4
    assert raw.cost == 3.0 > exh  # bridge edge 00- stays redundant without ReducedCov

    red = out_complex_step(cm, col_j, variant="keep_intersection", use_reduced=True)
    assert red.is_feasible and red.step_taken == 4
    assert red.cost == exh == 2.0


def test_all_n3_collapsible_boolean_functions_succeed_with_reduced_cov():
    minterms = list(product((0, 1), repeat=3))
    checked = 0
    for mask in range(1, 1 << 8):
        on = [minterms[i] for i in range(8) if mask & (1 << i)]
        primes = _primes_from_minterms(on)
        if len(primes) < 2:
            continue
        cx = CubicalComplex(top_cells=primes)
        coll = cx.collapsible_cells()
        if not coll:
            continue
        p = coll[0][0]
        rows = [BooleanCube(m) for m in on]
        cm = CoveringMatrix(
            rows=[str(r) for r in rows],
            cols=[str(q) for q in primes],
            matrix=[[r.is_face_of(q) for q in primes] for r in rows],
            row_cubes=rows,
            col_cubes=primes,
        )
        ok, res, opt = check_h_out(cm, primes.index(p), variant="keep_intersection", use_reduced=True)
        assert res.is_feasible and ok and res.cost == opt
        checked += 1
    assert checked == 198


def test_path6_collar_lockin_fails_even_with_reduced_cov():
    """P6 is a Boolean Out_complex witness, not a cyclic-core collapse witness."""
    cm, col_j = path6_collar_lockin_instance()
    exh, exh_idx = exhaustive_min_cost(cm)
    assert exh == 3.0
    assert [cm.cols[k] for k in exh_idx] == ["-000", "001-", "01-1"]
    # Still has essentials before reduction — not a cyclic core.
    sub, _, ess = reduce_to_cyclic_core(cm.copy())
    assert ess or sub.n_rows() < cm.n_rows()

    out = build_out_complex(cm, col_j, variant="keep_intersection")
    assert out.rows == ["0000", "0010", "0011", "0111", "0101"]  # shared vertex 0000 stays!
    out_opt, _ = exhaustive_min_cost(out)
    assert out_opt == 3.0

    # Valid minimum cover of Out_complex that triggers collar lock-in: {00-0, 0-11, 01-1}
    bad_tie = lambda sub: [sub.cols.index(nm) for nm in ("00-0", "0-11", "01-1")]
    assert out.is_cover(bad_tie(out)) and out.cost(bad_tie(out)) == out_opt

    res = out_complex_step(
        cm, col_j, variant="keep_intersection", use_reduced=True, out_solver=bad_tie
    )
    assert res.is_feasible and res.step_taken == 4
    assert res.cost == 4.0 > exh
    # Confirm irredundancy: dropping ANY one of the 4 chosen edges breaks coverage
    assert irredundant_cover(cm, res.cover_indices) == res.cover_indices


def test_cyclic_core_step3_trap_n4_and_drop_all_ff_rows_rescue_on_n4():
    cm, col_j = cyclic_core_step3_trap_n4()
    sub, _, ess = reduce_to_cyclic_core(cm.copy())
    assert ess == [] and sub.n_rows() == 9 and sub.n_cols() == 9
    exh, _ = exhaustive_min_cost(cm)
    assert exh == 4.0

    # Keeping intersection faces leaves all 9 rows in Out_complex -> Step 3 returns C_out (cost 5)
    ok_keep, res_keep, _ = check_h_out(cm, col_j, variant="keep_intersection", use_reduced=True)
    assert not ok_keep and res_keep.step_taken == 3 and res_keep.cost == 5.0

    # Dropping all FF_c rows recovers C_in (cost 4) — and succeeds across sampled n=4 cyclic cores
    ok_drop, res_drop, _ = check_h_out(cm, col_j, variant="drop_all_ff_rows", use_reduced=True)
    assert ok_drop and res_drop.step_taken == 4 and res_drop.cost == 4.0

    sample4 = enumerate_instances(4, 2500, seed=9)
    stats = audit_out_complex_on_cyclic_cores(sample4, variant="drop_all_ff_rows")
    assert stats["tested_cyclic_cores"] > 40 and stats["mismatches"] == 0


def test_cyclic_core_exclude_win_n5_breaks_even_drop_all_ff_rows():
    cm, col_j = cyclic_core_exclude_win_n5()
    sub, _, ess = reduce_to_cyclic_core(cm.copy())
    assert ess == [] and sub.n_rows() == 9 and sub.n_cols() == 9
    assert list_collapsible_primes(cm)[0][0] == col_j
    exh, _ = exhaustive_min_cost(cm)
    assert exh == 4.0

    for variant in ("drop_free_face", "drop_all_ff_rows"):
        ok, res, _ = check_h_out(cm, col_j, variant=variant, use_reduced=True)
        assert res.is_feasible
        assert not ok and res.step_taken == 4 and res.cost == 5.0 > exh


def test_feasibility_holds_unconditionally_across_variants():
    sample = enumerate_instances(4, 300, seed=12)
    for cm in sample:
        sub, _, _ = reduce_to_cyclic_core(cm.copy())
        coll = list_collapsible_primes(sub)
        if not coll:
            continue
        col_j = coll[0][0]
        for variant in OUT_VARIANTS:
            res = out_complex_step(sub, col_j, variant=variant, use_reduced=True)
            assert res.is_feasible

    with pytest.raises(ValueError):
        build_out_complex(path4_bridge_instance()[0], 0, variant="invalid")  # type: ignore[arg-type]
