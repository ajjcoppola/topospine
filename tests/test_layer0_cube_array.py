"""Tests for Layer-0 cube-array legal expansions, free-face push-down, blobs, and counterexamples."""

from __future__ import annotations

import random
from itertools import product

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.cover.auditor import _primes_from_minterms, exhaustive_min_cost
from topospine.cover.collapse import expand_collapse_once, list_collapsible_primes
from topospine.cover.cube_array import (
    covering_table_from_cube_array,
    cube_contained_in_union,
    expand_single_cubes_implicit,
    expand_to_primes_blake,
    iterative_free_face_blob_bound,
    layer0_far_side_holds,
    layer0_include_cex_n6_bridged_12x13,
    layer0_swap_cex_n5_9x9,
    minimize_cube_array,
    minimize_layer0_exact,
    partition_into_blobs,
    zero_loss_free_face_pushdown,
)
from topospine.cover.minimize import MinimizeStats, minimize_cover
from topospine.cover.out_complex import cyclic_core_exclude_win_n5


def test_blake_prime_expansion_matches_qm_all_n3_without_minterm_table():
    """Blake consensus expansion on raw cubes yields the exact prime implicants P(F)."""
    all3 = list(product((0, 1), repeat=3))
    for mask in range(1, 1 << 8):
        on = [all3[i] for i in range(8) if mask & (1 << i)]
        qm_primes = sorted(_primes_from_minterms(on), key=str)
        raw_cubes = [BooleanCube(m) for m in on]
        blake_primes = expand_to_primes_blake(raw_cubes)
        assert blake_primes == qm_primes


def test_legal_expansion_strictly_beats_subset_cover_via_consensus():
    """Absolute minimization expands raw cubes into primes rather than taking a subset.

    Raw array C = {00-, 11-, 0-0, 1-1} on n=3 covers 6 minterms; any subset cover of C
    needs >= 3 cubes, wait: {00-, 11-} already covers {000,001,110,111} (only 4 minterms).
    Consider instead C = {'000', '001', '011', '111'} (4 minterms):
      * Subset of raw minterm cubes needs all 4 cubes (cost 4).
      * Legal expansion to primes {'00-', '0-1', '-11'} has absolute min cover {'00-', '-11'} of cost 2!
      * Even starting from non-prime edges {'000', '00-', '011', '111'}, expansion finds '-11' and cost 2.
    """
    raw = ["000", "00-", "011", "111"]
    res_subset = minimize_cube_array(raw, expand_mode="none")
    res_implicit = minimize_cube_array(raw, expand_mode="implicit_single")
    res_abs = minimize_cube_array(raw, expand_mode="blake_primes")

    assert res_subset.cost == 3.0
    assert res_implicit.cost == 2.0
    assert res_abs.cost == 2.0
    assert [str(c) for c in res_abs.cubes] == ["-11", "00-"]


def test_high_dimensional_implicit_minterms_no_enumeration():
    """32-variable cube array (billions of implicit minterms) solves in cube space."""
    _, core_primes, _ = layer0_include_cex_n6_bridged_12x13()
    raw6, _, _ = layer0_include_cex_n6_bridged_12x13()
    # Pad every 6-var cube with 26 free '-' coordinates -> n = 32 (2^26 * 16 > 10^9 minterms)
    padded32 = [str(c) + ("-" * 26) for c in raw6]
    res = minimize_cube_array(padded32, expand_mode="blake_primes")
    assert res.cost == 8.0
    assert res.bb_nodes == 0
    for c in padded32:
        assert cube_contained_in_union(parse_boolean_cube(c), res.cubes)


def test_old_n5_exclude_witness_is_empty_on_full_layer0_onset():
    """Verify the wire-crossing discovery: cyclic_core_exclude_win_n5 omitted 8 of its
    cubes' 17 minterms; on the full cube-array ON-set, 5 primes are essential and the
    true Layer-0 cyclic core is 0x0.
    """
    cm_partial, _ = cyclic_core_exclude_win_n5()
    raw_cubes = [c for c in cm_partial.col_cubes if c is not None]
    primes = expand_to_primes_blake(raw_cubes)
    full_table = covering_table_from_cube_array(primes)
    assert full_table.n_rows() == 17
    core, _, ess = reduce_to_cyclic_core(full_table)
    assert len(ess) == 5
    assert core.n_rows() == 0 and core.n_cols() == 0


def test_layer0_existential_counterexamples_swap_and_include():
    """Both blind 1-recursion rules fail even existentially on genuine Layer-0 cyclic cores."""
    # 1. Swap-only fails on 9x9 n=5 core (unique collapsible prime 0-10-)
    _, core1, j1 = layer0_swap_cex_n5_9x9()
    opt1, _ = exhaustive_min_cost(core1)
    assert opt1 == 4.0
    coll1 = list_collapsible_primes(core1)
    assert len(coll1) == 1 and coll1[0][0] == j1
    for face in coll1[0][1]:
        exp1, _, _ = expand_collapse_once(core1, j1, face)
        exp_opt1, _ = exhaustive_min_cost(exp1)
        assert exp_opt1 == 5.0 > opt1

    # 2. Include-only (C_in) fails on 12x13 n=6 bridged double-6-cycle (unique collapsible --0000)
    _, core2, j2 = layer0_include_cex_n6_bridged_12x13()
    opt2, _ = exhaustive_min_cost(core2)
    assert opt2 == 6.0
    coll2 = list_collapsible_primes(core2)
    assert len(coll2) == 1 and coll2[0][0] == j2

    sub_in = core2.copy()
    sub_in.remove_rows({i for i in range(sub_in.n_rows()) if sub_in.matrix[i][j2]})
    sub_in.remove_cols({j2})
    cin_rest, _ = exhaustive_min_cost(sub_in)
    assert 1.0 + cin_rest == 7.0 > opt2

    # Iterative free-face push-down severs bridge --0000 into 2 blobs and hits exact opt=6!
    bp2 = iterative_free_face_blob_bound(core2)
    assert bp2.n_blobs == 2
    assert bp2.lower_bound == 6 and bp2.upper_bound == 6


def test_theorems_l0_a_b_c_and_solver_beats_plain_bb():
    """Zero-loss push-down (L0-A), Far-Side IFF (L0-B), blob additivity (L0-C), and exact solver."""
    rng = random.Random(20261123)
    all5 = list(product((0, 1), repeat=5))
    checked_cores = 0
    zpush_fires = 0
    plain_nodes_total = 0
    layer0_nodes_total = 0

    for _ in range(900):
        dens = rng.uniform(0.20, 0.70)
        on = [m for m in all5 if rng.random() < dens]
        if len(on) < 3:
            continue
        primes = expand_to_primes_blake([BooleanCube(m) for m in on])
        cm = covering_table_from_cube_array(primes)
        core, _, _ = reduce_to_cyclic_core(cm.copy())
        if core.n_rows() == 0 or core.n_cols() > 15:
            continue
        coll = list_collapsible_primes(core)
        if not coll:
            continue
        checked_cores += 1

        # L0-A: zero-loss push-down preserves exact opt identically
        opt_before, _ = exhaustive_min_cost(core)
        pushed, _, nz = zero_loss_free_face_pushdown(core)
        if nz > 0:
            zpush_fires += 1
            opt_after, _ = exhaustive_min_cost(pushed)
            assert opt_after == opt_before

        # L0-B: Layer-0 Far-Side IFF holds with 0 mismatches
        for j, faces in coll:
            for f in faces:
                assert isinstance(f, BooleanCube)
                ok, _, _ = layer0_far_side_holds(core, j, f)
                assert ok

        # Exactness & node comparison on full unreduced table
        s_plain = MinimizeStats()
        _, c_plain, s_plain = minimize_cover(cm.copy(), use_collapse=False, stats=s_plain)
        _, c_l0, res_l0 = minimize_layer0_exact(cm.copy())
        assert c_l0 == c_plain
        plain_nodes_total += s_plain.recursive_calls
        layer0_nodes_total += res_l0.bb_nodes

    assert checked_cores >= 35
    assert zpush_fires >= int(0.75 * checked_cores)
    assert layer0_nodes_total < plain_nodes_total

    # L0-C: explicit multi-blob disjoint union solves with 0 cross-blob explosion
    _, core1, _ = layer0_swap_cex_n5_9x9()
    # Embed two disjoint copies on 6 vars (prefix 0 vs prefix 1)
    c_blob = [parse_boolean_cube("0" + c) for c in core1.cols] + [
        parse_boolean_cube("1" + c) for c in core1.cols
    ]
    r_blob = [parse_boolean_cube("0" + r) for r in core1.rows] + [
        parse_boolean_cube("1" + r) for r in core1.rows
    ]
    two_blobs = CoveringMatrix(
        rows=[str(r) for r in r_blob],
        cols=[str(c) for c in c_blob],
        matrix=[[r.is_face_of(c) for c in c_blob] for r in r_blob],
        row_cubes=r_blob,
        col_cubes=c_blob,
    )
    blobs = partition_into_blobs(two_blobs)
    assert len(blobs) == 2
    _, cost2, res2 = minimize_layer0_exact(two_blobs)
    assert cost2 == 8.0 and res2.n_blobs == 2
