"""SpineMin / SpineTower repairs."""

import math

import pytest

from topospine.spines import build_cover_tower, spine_min, candidate_cover_from_points, tower_certificate
from topospine.spines.spine_min import filter_collapsible_columns


def sample_circle(n: int = 16) -> list[tuple[float, float]]:
    return [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]


def test_spine_min_covers():
    pts = sample_circle(12)
    cm = candidate_cover_from_points(pts, radius=0.8)
    res = spine_min(cm)
    assert cm.is_cover(res.cover_indices)
    assert res.certificate["contract"] == "Coverage"


def test_tower_selected_refinement_maps():
    pts = sample_circle(20)
    tower = build_cover_tower([(x, y) for x, y in pts], base_scale=1.2, n_levels=2, fail_closed=True)
    assert len(tower.levels) == 2
    cert = tower_certificate(tower)
    assert cert["contract"] == "ApproximatePersistence"
    # level 1 map keys index selected children
    if tower.levels[1].parent_map:
        assert max(tower.levels[1].parent_map) < len(tower.levels[1].selected_landmarks)


def test_fail_closed_empty_oracle():
    pts = [(0.0, 0.0), (10.0, 10.0)]
    cm = candidate_cover_from_points(pts, radius=0.01, landmark_indices=[0, 1])
    # Very small radius: each ball is a single point — collapsible; should not raise
    feas = filter_collapsible_columns(pts, [0, 1], 0.01, cm, fail_closed=True)
    assert feas  # single-point pieces are feasible
