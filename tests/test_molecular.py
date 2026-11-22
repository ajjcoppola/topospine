"""Loop 3: relative SpineTower on molecular conformation clouds."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "applications" / "molecular"))

from mol_pipeline import run_benchmark, run_one, synthetic_conformations, try_md17  # noqa: E402
from topospine.spines.relative_tower import (  # noqa: E402
    build_relative_tower,
    relative_betti_f2,
    relative_tower_certificate,
)


def fs(*v):
    return frozenset(v)


def test_relative_betti_known_cases():
    hollow = [fs(0, 1), fs(1, 2), fs(0, 2)]
    # circle rel a vertex: H0 = 0, H1 = 1
    assert relative_betti_f2(hollow, [fs(0)], max_dim=1) == [0, 1]
    # filled triangle rel its boundary: H2 = 1 (the 2-sphere quotient)
    tri = [fs(0, 1, 2)]
    boundary = [fs(0, 1), fs(1, 2), fs(0, 2)]
    assert relative_betti_f2(tri, boundary, max_dim=2) == [0, 0, 1]
    # sub = empty reduces to absolute Betti numbers of the circle
    assert relative_betti_f2(hollow, [], max_dim=1) == [1, 1]


def test_relative_betti_rejects_non_subcomplex():
    with pytest.raises(ValueError):
        relative_betti_f2([fs(0, 1)], [fs(2)], max_dim=1)


def test_synthetic_conformations_deterministic():
    p1, A1, m1 = synthetic_conformations()
    p2, A2, _ = synthetic_conformations()
    assert p1 == p2 and A1 == A2
    assert len(p1) == 13 * 12 and len(A1) == 4 * 12 and m1["source"] == "synthetic"


def test_relative_tower_resolves_A_finer_than_coverage_only():
    pts, A, _ = synthetic_conformations()
    out = run_one(pts, A, base_scale=2.4)
    rel, cov = out["relative"], out["coverage_only"]
    assert rel["relative_equivalence_checked"] is True
    assert cov["relative_equivalence_checked"] is False
    assert rel["uncovered_points"] == [0, 0, 0] == cov["uncovered_points"]
    for r, c in zip(rel["A_cover_radius"], cov["A_cover_radius"]):
        assert r < c
    for scale, r in zip(rel["scales"], rel["A_cover_radius"]):
        assert r <= scale / 2  # eps-net of A forced at spacing scale/2
    # it pays for fidelity with more pieces
    assert all(r >= c for r, c in zip(rel["cover_sizes"], cov["cover_sizes"]))


def test_relative_betti_satisfies_euler_identity_on_real_nerves():
    """sum (-1)^k beta_k(N, N_A) == sum (-1)^k (#cells of N not in N_A), with N truncated at dim 2."""
    from topospine.core.homology import _skeleton
    from topospine.spines.relative_tower import _pieces, nerve_from_pieces

    pts, A, _ = synthetic_conformations()
    tower = build_relative_tower(pts, A, 2.4, 3)
    for lv in tower.levels:
        pieces = _pieces(pts, lv.selected, lv.scale)
        N = nerve_from_pieces(pieces)
        NA = nerve_from_pieces(pieces, witnesses=set(A))
        assert set(NA) <= set(N)
        sk_N, sk_A = _skeleton(N), _skeleton(NA)
        chi_cells = sum(
            (-1) ** d * (len(sk_N.get(d, [])) - len(sk_A.get(d, []))) for d in range(3)
        )
        b = relative_betti_f2(N, NA, max_dim=2)
        assert sum((-1) ** d * x for d, x in enumerate(b)) == chi_cells


def test_refinement_maps_are_total_on_selected():
    pts, A, _ = synthetic_conformations()
    tower = build_relative_tower(pts, A, 2.4, 3)
    for k in (1, 2):
        lv = tower.levels[k]
        assert set(lv.parent_map) == set(range(len(lv.selected)))
        assert all(0 <= v < len(tower.levels[k - 1].selected) for v in lv.parent_map.values())


def test_md17_skipped_without_env_and_loads_with_npz(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    monkeypatch.delenv("TOPOSPINE_MD17_NPZ", raising=False)
    assert try_md17() is None
    assert run_benchmark.__name__ == "run_benchmark"
    rng = np.random.default_rng(0)
    R = rng.normal(size=(50, 9, 3))
    f = tmp_path / "fake_md17.npz"
    np.savez(f, R=R)
    monkeypatch.setenv("TOPOSPINE_MD17_NPZ", str(f))
    md = try_md17(n_frames=6, n_A=3)
    assert md is not None and len(md["points"]) == 6 * 9 and len(md["A"]) == 6 * 3
    assert md["meta"]["source"] == "md17"


def test_rips_betti_circle_and_budget_matched_baseline():
    import math

    from topospine.spines.relative_tower import ablation_report, rips_betti_f2

    circ = [(math.cos(2 * math.pi * k / 12), math.sin(2 * math.pi * k / 12)) for k in range(12)]
    assert rips_betti_f2(circ, range(12), 0.55) == [1, 1]  # nearest neighbours only: a 12-cycle
    assert rips_betti_f2(circ, range(12), 0.1) == [12, 0]
    assert rips_betti_f2(circ, range(12), 2.5) == [1, 0]

    pts, A, _ = synthetic_conformations()
    rep = ablation_report(pts, A, 2.4)
    m = rep["methods"]
    assert m["kcenter_same_budget"]["cover_sizes"] == m["relative"]["cover_sizes"]
    # at equal budget the forced A-net resolves A strictly better ...
    assert all(r < k for r, k in zip(m["relative"]["A_cover_radius"], m["kcenter_same_budget"]["A_cover_radius"]))
    # ... and pays in global covering radius (honest trade-off, documented in Paper C)
    assert all(r >= k for r, k in zip(m["relative"]["r_all"], m["kcenter_same_budget"]["r_all"]))
