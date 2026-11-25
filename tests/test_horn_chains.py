"""Tests for constructive Layer-0 free-face variants and controlled collapsible horn chains."""

from __future__ import annotations

import random
from itertools import product

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.core.cubical import CubicalComplex
from topospine.cover.collapse import expand_collapse_once, list_collapsible_primes
from topospine.cover.cube_array import (
    covering_table_from_cube_array,
    expand_to_primes_blake,
    layer0_include_cex_n6_bridged_12x13,
    minimize_cube_array,
)
from topospine.cover.auditor import exhaustive_min_cost
from topospine.cover.horn_chains import (
    ambient_cone_prism_cubes,
    collapse_to_topological_spine,
    complement_cubes,
    controlled_horn_chain_cover,
    cubical_cohomology_betti_f2,
    cubical_persistent_cohomology_betti_f2,
    cylinder_product_cubes,
    decode_horn_cover,
    filtration_compatible_spine,
    free_faces_via_complement,
    horn_exact_iff_holds,
    horn_replace_once,
)


def test_h1_horn_strictly_beats_single_face_swap_on_5x4_3cube_core():
    """Concrete 5x4 Layer-0 3-cube cyclic core (certified in HornChains.lean):
    p = ---10, free face f = 1--10.
    * True opt = 2 ({---10, --01-}).
    * Single-face swap (CC \\ {p}) ∪ {f} has opt = 3.
    * Horn replacement (CC \\ {p}) ∪ (∂p \\ {f}) has opt = 2 via side face -1-10!
    """
    rows = [parse_boolean_cube(s) for s in ["01011", "01110", "10011", "10110", "11010"]]
    cols = [parse_boolean_cube(s) for s in ["---10", "--01-", "-0-1-", "0--1-"]]
    cm = CoveringMatrix(
        rows=[str(r) for r in rows],
        cols=[str(c) for c in cols],
        matrix=[[r.is_face_of(c) for c in cols] for r in rows],
        row_cubes=rows,
        col_cubes=cols,
    )
    opt_orig, _ = exhaustive_min_cost(cm)
    assert opt_orig == 2.0

    f = parse_boolean_cube("1--10")
    exp_single, _, _ = expand_collapse_once(cm, 0, f)
    opt_single, _ = exhaustive_min_cost(exp_single)
    assert opt_single == 3.0

    cm_horn, _, h_names = horn_replace_once(cm, 0, f)
    opt_horn, h_pick = exhaustive_min_cost(cm_horn)
    assert opt_horn == 2.0
    dec = decode_horn_cover(cm, cm_horn, h_pick, 0, h_names)
    assert len(dec) == 2 and cm.is_cover(dec)

    ok_iff, o_orig, o_horn, o_dec = horn_exact_iff_holds(cm, 0, f)
    assert ok_iff and o_orig == 2 and o_horn == 2 and o_dec == 2


def test_h1_horn_iff_and_feasibility_across_n5_layer0_cores():
    """Horn replacement preserves 100% residual ON-coverage and satisfies Exact Horn IFF."""
    rng = random.Random(20261123)
    all5 = list(product((0, 1), repeat=5))
    checked_pairs = 0

    for _ in range(500):
        dens = rng.uniform(0.20, 0.70)
        on = [m for m in all5 if rng.random() < dens]
        if len(on) < 3:
            continue
        primes = expand_to_primes_blake([BooleanCube(m) for m in on])
        cm = covering_table_from_cube_array(primes)
        core, _, _ = reduce_to_cyclic_core(cm)
        if core.n_rows() == 0 or core.n_cols() > 14:
            continue
        for j, faces in list_collapsible_primes(core):
            for f in faces:
                assert isinstance(f, BooleanCube)
                ok, _, opt_h, dec_c = horn_exact_iff_holds(core, j, f)
                assert ok
                assert opt_h < 10**8  # always feasible!
                assert dec_c <= opt_h
                checked_pairs += 1

    assert checked_pairs >= 200


def test_h2_cylinder_and_ambient_cone_prism_theorems():
    """Cylinder product preserves opt and cohomology; cone-prism is contractible with opt+1."""
    raw, core, _ = layer0_include_cex_n6_bridged_12x13()
    base_res = minimize_cube_array(raw)
    assert base_res.cost == 8.0

    # Global cylinder C × I^2
    cyl = cylinder_product_cubes(raw, m=2)
    cyl_res = minimize_cube_array(cyl)
    assert cyl_res.cost == base_res.cost == 8.0
    assert cubical_cohomology_betti_f2(cyl) == cubical_cohomology_betti_f2(raw)

    # Ambient cone-prism E(F) = (F × {0}) ∪ (Q_n × {1}) on n=4 hollow 6-cycle
    cycle6 = ["000-", "00-1", "0-11", "-111", "11-0", "1-00"]
    # Wait: verify Betti of boundary of 2-cube (4 edges = S^1 -> [1, 1])!
    sq_bdry = ["0-", "1-", "-0", "-1"]
    assert cubical_cohomology_betti_f2([parse_boolean_cube(s) for s in sq_bdry]) == [1, 1]

    # On non-tautology n=4 6-cycle (in x_0=0: S^1 -> Betti [1, 1], opt=3, F != Q_4):
    sub4 = ["000-", "00-1", "0-11", "011-", "01-0", "0-00"]
    assert cubical_cohomology_betti_f2([parse_boolean_cube(s) for s in sub4]) == [1, 1]
    r_sub4 = minimize_cube_array(sub4)
    assert r_sub4.cost == 3.0

    cone_primes = expand_to_primes_blake(ambient_cone_prism_cubes(sub4))
    # Contractible cone-prism prime complex has Betti [1] and opt = 1 + opt(F) = 4!
    assert cubical_cohomology_betti_f2(cone_primes) == [1]
    r_cone = minimize_cube_array(cone_primes)
    assert r_cone.cost == 1.0 + r_sub4.cost == 4.0


def test_h3_complement_boundary_free_face_duality_all_n3_and_sampled_n5():
    """Free faces in C(F) match external normal complement checks without enumerating P(F)."""
    all3 = list(product((0, 1), repeat=3))
    for mask in range(1, (1 << 8) - 1):
        on = [all3[i] for i in range(8) if mask & (1 << i)]
        raw = [BooleanCube(m) for m in on]
        primes = expand_to_primes_blake(raw)
        off = complement_cubes(raw)
        cx = CubicalComplex(top_cells=primes)
        for p in primes:
            want = sorted(cx.free_faces_of(p), key=str)
            got_on = sorted(free_faces_via_complement(p, on_cubes=raw), key=str)
            got_off = sorted(free_faces_via_complement(p, off_cubes=off), key=str)
            assert got_on == want
            assert got_off == want

    rng = random.Random(7)
    all5 = list(product((0, 1), repeat=5))
    for _ in range(80):
        on = [m for m in all5 if rng.random() < 0.45]
        if not on or len(on) == 32:
            continue
        raw = [BooleanCube(m) for m in on]
        primes = expand_to_primes_blake(raw)
        off = complement_cubes(raw)
        cx = CubicalComplex(top_cells=primes)
        for p in primes:
            want = sorted(cx.free_faces_of(p), key=str)
            assert sorted(free_faces_via_complement(p, on_cubes=raw), key=str) == want
            assert sorted(free_faces_via_complement(p, off_cubes=off), key=str) == want


def test_h4_collapsible_chains_preserve_cohomology_persistence_and_solve():
    """Collapsible chains preserve H* and persistent H*, and controlled modes satisfy bounds."""
    # Boundary of 3-cube (6 squares = S^2 -> Betti [1, 0, 1], non-collapsible)
    s2 = [parse_boolean_cube(s) for s in ["0--", "1--", "-0-", "-1-", "--0", "--1"]]
    assert cubical_cohomology_betti_f2(s2) == [1, 0, 1]
    # Punctured S^2 (5 squares = disk -> Betti [1], collapses down to 1 vertex!)
    disk2 = s2[:-1]
    assert cubical_cohomology_betti_f2(disk2) == [1]
    tr = collapse_to_topological_spine(disk2)
    assert cubical_cohomology_betti_f2(tr.spine_generators) == [1]
    assert tr.spine_cell_count == 1

    rng = random.Random(20261123)
    all5 = list(product((0, 1), repeat=5))
    tested = 0
    k1_hits = 0
    k8_hits = 0

    for _ in range(700):
        dens = rng.uniform(0.22, 0.68)
        on = [m for m in all5 if rng.random() < dens]
        if len(on) < 3:
            continue
        primes = expand_to_primes_blake([BooleanCube(m) for m in on])
        cm = covering_table_from_cube_array(primes)
        core, _, _ = reduce_to_cyclic_core(cm)
        if core.n_rows() == 0 or core.n_cols() > 15:
            continue
        if not list_collapsible_primes(core):
            continue
        tested += 1

        # 1. Unfiltered spine cohomology invariance
        tops = [c for c in core.col_cubes if isinstance(c, BooleanCube)]
        b_orig = cubical_cohomology_betti_f2(tops)
        trace = collapse_to_topological_spine(tops)
        b_spine = cubical_cohomology_betti_f2(trace.spine_generators)
        assert b_orig == b_spine

        # 2. Filtered persistent cohomology invariance
        vw = {m: float(rng.choice([1, 2, 3])) for m in all5}
        births: dict[BooleanCube, float] = {}

        def add_b(c: BooleanCube) -> None:
            if c in births:
                return
            births[c] = max(vw[v] for v in c.vertices())
            for f in c.faces():
                add_b(f)

        for c in tops:
            add_b(c)

        rem_births, fsteps = filtration_compatible_spine(births)
        assert len(rem_births) <= len(births)
        grades = [1.0, 2.0, 3.0]
        assert cubical_persistent_cohomology_betti_f2(births, grades) == cubical_persistent_cohomology_betti_f2(
            rem_births, grades
        )

        # 3. Controlled exact / approx / probabilistic covering guarantees
        r_ex = controlled_horn_chain_cover(core, mode="exact")
        r_ap = controlled_horn_chain_cover(core, mode="approx")
        r_pr = controlled_horn_chain_cover(core, mode="probabilistic", num_chains=8, seed=tested)

        exh_cost, _ = exhaustive_min_cost(core)
        assert r_ex.cost == exh_cost and core.is_cover(r_ex.cover_indices)
        assert r_ap.lower_bound <= exh_cost <= r_ap.upper_bound
        assert core.is_cover(r_ap.cover_indices)
        if r_ap.certified_optimal:
            assert r_ap.cost == exh_cost
        assert r_pr.lower_bound <= exh_cost <= r_pr.upper_bound
        assert r_pr.upper_bound <= r_ap.upper_bound
        assert core.is_cover(r_pr.cover_indices)
        if r_pr.certified_optimal:
            assert r_pr.cost == exh_cost

        k1_hits += int(r_ap.cost == exh_cost)
        k8_hits += int(r_pr.cost == exh_cost)

    assert tested >= 25
    assert k8_hits >= k1_hits
    assert k8_hits >= int(0.90 * tested)
