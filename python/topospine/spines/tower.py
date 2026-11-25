"""Multiscale collapsible cover towers with selected-spine refinement maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from topospine.core.covering import CoveringMatrix
from topospine.core.homology import betti_numbers_f2
from topospine.spines.spine_min import (
    _dist,
    candidate_cover_from_points,
    filter_collapsible_columns,
    spine_min,
)
from topospine.spines.dual import nerve_of_cover


@dataclass
class CoverLevel:
    scale: float
    epsilon: float
    landmark_indices: list[int]
    cover_indices: list[int]  # indices into landmark list / candidate cols
    selected_landmarks: list[int]
    cm: CoveringMatrix
    nerve: list[frozenset[int]]
    betti: list[int]
    parent_map: dict[int, int] = field(default_factory=dict)  # child selected idx -> parent selected idx
    lower_bound: int = 0
    upper_bound: int = 0
    certified_optimal: bool = False


@dataclass
class CoverTower:
    points: list[tuple[float, ...]]
    levels: list[CoverLevel] = field(default_factory=list)


def epsilon_net(points: list[tuple[float, ...]], target_spacing: float) -> tuple[list[int], float]:
    n = len(points)
    if n == 0:
        return [], 0.0
    landmarks = [0]
    min_dist = [float("inf")] * n
    for _ in range(n - 1):
        last = landmarks[-1]
        for i in range(n):
            d = _dist(points[i], points[last])
            if d < min_dist[i]:
                min_dist[i] = d
        farthest = max(range(n), key=lambda i: min_dist[i])
        if min_dist[farthest] < target_spacing * 0.5:
            break
        landmarks.append(farthest)
    achieved = 0.0
    if landmarks:
        achieved = max(
            (min((_dist(points[i], points[j]) for j in landmarks if j != i), default=0.0) for i in range(n)),
            default=0.0,
        )
    return landmarks, achieved


def _refinement_map_selected(
    child_selected: list[int],
    parent_selected: list[int],
    points: list[tuple[float, ...]],
    parent_radius: float,
) -> dict[int, int]:
    """Map each *selected* child landmark to a *selected* parent landmark."""
    mapping: dict[int, int] = {}
    for ci, c_idx in enumerate(child_selected):
        best_pj = 0
        best_d = float("inf")
        for pj, p_idx in enumerate(parent_selected):
            d = _dist(points[c_idx], points[p_idx])
            if d <= parent_radius + 1e-12 and d < best_d:
                best_d = d
                best_pj = pj
        mapping[ci] = best_pj
    return mapping


def build_cover_tower(
    points: list[tuple[float, ...]],
    base_scale: float,
    n_levels: int = 3,
    *,
    fail_closed: bool = True,
    spine_method: str = "espresso_loop",
    horn_mode: str = "approx",
) -> CoverTower:
    tower = CoverTower(points=points)
    prev_selected: list[int] | None = None
    prev_scale = base_scale

    for i in range(n_levels):
        scale = base_scale / (2**i)
        landmarks, achieved_eps = epsilon_net(points, scale / 2.0)
        cm = candidate_cover_from_points(points, radius=scale, landmark_indices=landmarks)
        feasible = filter_collapsible_columns(
            points, landmarks, scale, cm, fail_closed=fail_closed
        )
        sub = cm.copy()
        drop = set(range(sub.n_cols())) - set(feasible)
        sub.remove_cols(drop)
        # Map feasible old -> new
        if spine_method == "horn":
            result = spine_min(sub, method="horn", horn_mode=horn_mode)  # type: ignore[arg-type]
        else:
            result = spine_min(sub, method=spine_method)  # type: ignore[arg-type]
        # selected columns in `sub` indices → original landmark indices
        selected_landmarks = []
        for new_j in result.cover_indices:
            # sub.cols[new_j] is ball(landmark,...)
            name = sub.cols[new_j]
            lid = int(name.split("(")[1].split(",")[0])
            selected_landmarks.append(lid)

        # Build nerve on selected cover only
        keep_cm = candidate_cover_from_points(
            points, radius=scale, landmark_indices=selected_landmarks
        )
        # For nerve, columns = selected pieces covering landmarks as rows of selected set
        nerve_cm = CoveringMatrix(
            rows=[f"L{k}" for k in selected_landmarks],
            cols=[f"U{k}" for k in selected_landmarks],
            matrix=[
                [_dist(points[a], points[b]) <= scale + 1e-12 for b in selected_landmarks]
                for a in selected_landmarks
            ],
        )
        nerve = nerve_of_cover(nerve_cm)
        betti = betti_numbers_f2(nerve, max_dim=1) if nerve else []

        parent_map: dict[int, int] = {}
        if prev_selected is not None:
            parent_map = _refinement_map_selected(
                selected_landmarks, prev_selected, points, prev_scale
            )

        tower.levels.append(
            CoverLevel(
                scale=scale,
                epsilon=achieved_eps,
                landmark_indices=landmarks,
                cover_indices=result.cover_indices,
                selected_landmarks=selected_landmarks,
                cm=keep_cm,
                nerve=nerve,
                betti=betti,
                parent_map=parent_map,
                lower_bound=result.lower_bound,
                upper_bound=result.upper_bound,
                certified_optimal=result.certified_optimal,
            )
        )
        prev_selected = selected_landmarks
        prev_scale = scale
    return tower


def tower_certificate(tower: CoverTower) -> dict:
    """ApproximatePersistence contract certificate (not ProvenMinimum)."""
    n_cert = sum(1 for lv in tower.levels if lv.certified_optimal)
    return {
        "contract": "ApproximatePersistence",
        "n_levels": len(tower.levels),
        "interleaving_constant": 2.5,
        "qualifier": "TopologicalApproximation",
        "scales": [lv.scale for lv in tower.levels],
        "cover_sizes": [len(lv.selected_landmarks) for lv in tower.levels],
        "betti_per_level": [lv.betti for lv in tower.levels],
        "refinement_maps_selected": [lv.parent_map for lv in tower.levels],
        "windows": [(lv.lower_bound, lv.upper_bound) for lv in tower.levels],
        "certified_optimal_levels": n_cert,
        "certified_optimal_fraction": n_cert / max(1, len(tower.levels)),
    }
