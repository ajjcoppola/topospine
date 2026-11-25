"""Grid free-face local transform: dichotomy, counterexample, characterization, put-back."""

from __future__ import annotations

import pytest

from topospine.core.covering import CoveringMatrix
from topospine.cover.grid2d import (
    FILLED,
    HOLLOW,
    apply_transform,
    build_grid,
    characterization_holds,
    collapsible_pairs,
    dichotomy_counts,
    far_rows,
    min_subcover_masks,
    smallest_vertex_counterexample,
    to_core,
    verify_characterization,
)
from topospine.cover.minimize import _min_subcover_names, minimize_cover


def test_row_model_dichotomy_3x3():
    d = dichotomy_counts(3, 3)
    # Face rows: free face forces its square essential → no collapsible square survives.
    assert d["face_with_collapsible_square"] == 0
    assert d["face_cores"] > 0
    # Vertex rows: collapsible squares survive into many cores.
    assert d["vertex_with_collapsible_square"] > 0
    assert d["vertex_cores"] > d["vertex_with_collapsible_square"]


def test_smallest_2x3_vertex_counterexample():
    res = smallest_vertex_counterexample()
    assert res is not None
    assert res.c_exp > res.opt
    assert not res.far_empty
    # Put-back alone need not recover: raw decode can remain suboptimal.
    assert res.decoded_putback >= res.opt
    lines = res.grid_draw.strip().split("\n")
    assert len(lines) in (2, 3)  # 2x2 or 2x3


def test_characterization_iff_on_2x3_and_3x3():
    r23 = verify_characterization(2, 3)
    assert r23["checked"] > 0 and r23["mismatches"] == 0
    r33 = verify_characterization(3, 3)
    assert r33["checked"] > 1000 and r33["mismatches"] == 0


def test_characterization_matches_helper_on_cex():
    cfg = {
        (0, 0): HOLLOW,
        (1, 0): HOLLOW,
        (0, 1): FILLED,
        (1, 1): HOLLOW,
        (0, 2): HOLLOW,
        (1, 2): HOLLOW,
    }
    g = build_grid(cfg, 2, 3)
    core = to_core(g)
    assert core is not None
    pairs = collapsible_pairs(core)
    assert pairs
    for p, f in pairs:
        res = apply_transform(core, p, f)
        assert characterization_holds(core, p, f, res)
        if res.c_exp != res.opt:
            assert not res.far_coverable_without_p or res.far_empty is False
            F = far_rows(p, f, core.core_rows)
            assert len(F) > 0


def test_putback_min_subcover_masks():
    # Single dominating column wins; without it the two halves are needed.
    chosen = [("a", 0b0011), ("b", 0b1100), ("c", 0b1111)]
    sub = min_subcover_masks(0b1111, chosen)
    assert sub == [("c", 0b1111)]
    sub2 = min_subcover_masks(0b1111, [("a", 0b0011), ("b", 0b1100)])
    assert len(sub2) == 2
    assert {n for n, _ in sub2} == {"a", "b"}


def test_minimize_restore_putback_drops_redundant():
    """Synthetic table: collapse decode then put-back must drop a cube p covers."""
    # rows 0,1,2; cols p covers all, q covers {0}, r covers {1,2}
    cm = CoveringMatrix(
        rows=["r0", "r1", "r2"],
        cols=["p", "q", "r"],
        matrix=[
            [True, True, False],
            [True, False, True],
            [True, False, True],
        ],
        weights=[1.0, 1.0, 1.0],
    )
    # Without geometry, collapse-branch won't fire; exercise put-back helper directly.
    cov = {
        "p": frozenset({0, 1, 2}),
        "q": frozenset({0}),
        "r": frozenset({1, 2}),
    }
    reduced, mode = _min_subcover_names({"p", "q", "r"}, cov, frozenset({0, 1, 2}))
    assert mode == "exact"
    assert reduced == {"p"}


def test_minimize_putback_stats_field_exists():
    cm = CoveringMatrix(
        rows=["a", "b"],
        cols=["c0", "c1"],
        matrix=[[True, False], [False, True]],
        weights=[1.0, 1.0],
    )
    _, cost, st = minimize_cover(cm, use_collapse=False)
    assert cost == 2.0
    assert hasattr(st, "putback_exact")
    assert hasattr(st, "putback_greedy")
