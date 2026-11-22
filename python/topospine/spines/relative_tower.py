"""Relative cover towers: a designated subset A of the data is resolved exactly.

Setting (molecular conformations): ``points`` are atom positions pooled over a
conformational ensemble, ``A`` indexes a functional group / binding region.  The
relative tower keeps a *forced* piece centred at every A-point at every level and
covers the rest with a greedy-pruned spine over collapsible columns.

Certificates:
  * ``RelativeEquivalence`` – every A-point lies in a selected piece centred at
    an A-point (an epsilon-net of A is forced at each scale, so A is resolved at
    the level's own scale), and the A-nerve ``N_A`` (faces with a common
    *A-witness*) is a subcomplex of the full nerve ``N``; we report β(N), β(N_A) and the relative
    Betti numbers β(N, N_A) over F2 (exact).
  * ``ApproximatePersistence`` – the usual tower contract (selected refinement
    maps); no interleaving *proof* is claimed (qualifier TopologicalApproximation).

Fail-closed: if any non-A point cannot be covered, the level is flagged and the
uncovered count is reported (never silently dropped).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from itertools import combinations
from typing import Sequence

from topospine.core.covering import CoveringMatrix
from topospine.core.homology import _skeleton, betti_numbers_f2
from topospine.spines.spine_min import (
    _dist,
    candidate_cover_from_points,
    filter_collapsible_columns,
    greedy_set_cover,
    irredundant_prune,
)
from topospine.spines.tower import _refinement_map_selected, epsilon_net

Point = tuple[float, ...]


# ----------------------------------------------------------------- homology
def _rank_f2_bitmask(columns: list[int]) -> int:
    """Rank over F2 of vectors given as Python int bitmasks."""
    pivots: dict[int, int] = {}
    rank = 0
    for v in columns:
        while v:
            h = v.bit_length() - 1
            if h in pivots:
                v ^= pivots[h]
            else:
                pivots[h] = v
                rank += 1
                break
    return rank


def relative_betti_f2(
    simplices: list[frozenset[int]],
    sub: list[frozenset[int]],
    max_dim: int = 1,
) -> list[int]:
    """β_k(N, N_A; F2) for k ≤ max_dim.  ``sub`` must be a subcomplex of ``simplices``."""
    skel = _skeleton(simplices)
    sub_skel = _skeleton(sub) if sub else {}
    sub_sets = {d: set(v) for d, v in sub_skel.items()}
    for d, cells in sub_skel.items():
        missing = [c for c in cells if c not in set(skel.get(d, []))]
        if missing:
            raise ValueError("sub is not a subcomplex of simplices")
    rel: dict[int, list[frozenset[int]]] = {
        d: [c for c in cells if c not in sub_sets.get(d, set())] for d, cells in skel.items()
    }

    def rank_boundary(d: int) -> int:
        if d <= 0 or not rel.get(d) or not rel.get(d - 1):
            return 0
        idx = {c: i for i, c in enumerate(rel[d - 1])}
        cols = []
        for sigma in rel[d]:
            verts = sorted(sigma)
            mask = 0
            for k in range(len(verts)):
                f = frozenset(verts[:k] + verts[k + 1 :])
                i = idx.get(f)
                if i is not None:
                    mask ^= 1 << i
            cols.append(mask)
        return _rank_f2_bitmask(cols)

    out = []
    for d in range(max_dim + 1):
        n_d = len(rel.get(d, []))
        out.append(max(0, n_d - rank_boundary(d) - rank_boundary(d + 1)))
    return out


# ----------------------------------------------------------------- nerve
def _pieces(points: Sequence[Point], centers: list[int], radius: float) -> list[set[int]]:
    return [
        {i for i, p in enumerate(points) if _dist(p, points[c]) <= radius + 1e-12} for c in centers
    ]


def nerve_from_pieces(
    pieces: list[set[int]], witnesses: set[int] | None = None, max_dim: int = 2
) -> list[frozenset[int]]:
    """Nerve on piece indices; a face needs a common point in ``witnesses`` (default: all)."""
    simplices: set[frozenset[int]] = set()
    n = len(pieces)
    wit = witnesses
    eff = [p if wit is None else (p & wit) for p in pieces]
    for r in range(1, min(n, max_dim + 1) + 1):
        for combo in combinations(range(n), r):
            common = eff[combo[0]]
            for j in combo[1:]:
                common = common & eff[j]
                if not common:
                    break
            if common:
                simplices.add(frozenset(combo))
    return sorted(simplices, key=lambda s: (len(s), sorted(s)))


# ----------------------------------------------------------------- tower
@dataclass
class RelLevel:
    scale: float
    selected: list[int]  # point indices of selected centres
    n_forced: int
    uncovered_points: int
    oracle_rejected: int
    betti_N: list[int]
    betti_NA: list[int]
    betti_rel: list[int]
    A_cover_radius: float  # max over A of distance to nearest selected centre (any centre)
    A_covered_by_A_pieces: bool = False  # every A point lies in a selected piece centred in A
    r_all: float = 0.0  # max over all points of distance to nearest selected centre
    parent_map: dict[int, int] = field(default_factory=dict)
    wall_time_s: float = 0.0


@dataclass
class RelTower:
    levels: list[RelLevel]
    A: list[int]
    mode: str  # "relative" | "coverage_only"


def _A_pieces(pieces: list[set[int]], A: set[int]) -> list[int]:
    return [k for k, p in enumerate(pieces) if p & A]


def _level_homology(
    points: Sequence[Point], selected: list[int], scale: float, A: set[int]
) -> tuple[list[int], list[int], list[int], float]:
    pieces = _pieces(points, selected, scale)
    N = nerve_from_pieces(pieces)
    a_idx = _A_pieces(pieces, A)
    # N_A: faces whose common intersection meets A (a subcomplex of N)
    NA = nerve_from_pieces(pieces, witnesses=A)
    b_N = betti_numbers_f2(N, max_dim=1) if N else [0, 0]
    b_NA = betti_numbers_f2(NA, max_dim=1) if NA else [0, 0]
    b_rel = relative_betti_f2(N, NA, max_dim=1) if N else [0, 0]
    a_rad = max(
        (min(_dist(points[a], points[c]) for c in selected) for a in A), default=0.0
    )
    _ = a_idx
    return b_N, b_NA, b_rel, a_rad


def _make_level(
    points: Sequence[Point],
    selected: list[int],
    scale: float,
    A_set: set[int],
    prev_sel: list[int] | None,
    prev_scale: float,
    t0: float,
    *,
    n_forced: int,
    rejected: int = 0,
) -> RelLevel:
    cov_now = [False] * len(points)
    for c in selected:
        for i, p in enumerate(points):
            if _dist(p, points[c]) <= scale + 1e-12:
                cov_now[i] = True
    uncovered = sum(1 for v in cov_now if not v)
    b_N, b_NA, b_rel, a_rad = _level_homology(points, selected, scale, A_set)
    a_centres = [c for c in selected if c in A_set]
    a_by_a = all(
        any(_dist(points[a], points[c]) <= scale + 1e-12 for c in a_centres) for a in A_set
    )
    r_all = max(min(_dist(p, points[c]) for c in selected) for p in points)
    parent = (
        _refinement_map_selected(selected, prev_sel, points, prev_scale)
        if prev_sel is not None
        else {}
    )
    return RelLevel(
        scale=scale,
        selected=selected,
        n_forced=n_forced,
        uncovered_points=uncovered,
        oracle_rejected=rejected,
        betti_N=b_N,
        betti_NA=b_NA,
        betti_rel=b_rel,
        A_cover_radius=a_rad,
        A_covered_by_A_pieces=a_by_a,
        r_all=r_all,
        parent_map=parent,
        wall_time_s=time.perf_counter() - t0,
    )


def build_relative_tower(
    points: list[Point],
    A: Sequence[int],
    base_scale: float,
    n_levels: int = 3,
    *,
    relative: bool = True,
) -> RelTower:
    """``relative=True``: forced A-centred pieces + spine over the rest.
    ``relative=False``: coverage-only spine over the eps-net (baseline)."""
    A_set = set(A)
    levels: list[RelLevel] = []
    prev_sel: list[int] | None = None
    prev_scale = base_scale
    for lev in range(n_levels):
        t0 = time.perf_counter()
        scale = base_scale / (2**lev)
        net, _ = epsilon_net(points, scale / 2.0)
        if relative:
            A_sorted = sorted(A_set)
            net_A, _ = epsilon_net([points[a] for a in A_sorted], scale / 2.0)
            forced = sorted(A_sorted[i] for i in net_A)
            landmarks = sorted(set(net) | set(forced))
        else:
            forced = []
            landmarks = list(net)
        cm = candidate_cover_from_points(points, radius=scale, landmark_indices=landmarks)

        # fail-closed oracle but non-raising: report rejections instead of crashing
        try:
            feasible = filter_collapsible_columns(points, landmarks, scale, cm, fail_closed=True)
        except ValueError:
            feasible = []
        rejected = cm.n_cols() - len(feasible)
        forced_cols = [j for j, c in enumerate(landmarks) if c in set(forced)]
        usable = sorted(set(feasible) | set(forced_cols))

        covered = [False] * len(points)
        chosen_cols: list[int] = list(forced_cols)
        for j in chosen_cols:
            for i in range(len(points)):
                if cm.matrix[i][j]:
                    covered[i] = True
        rest_rows = [i for i, c in enumerate(covered) if not c]
        if rest_rows:
            sub = CoveringMatrix(
                rows=[cm.rows[i] for i in rest_rows],
                cols=[cm.cols[j] for j in usable if j not in set(forced_cols)],
                matrix=[
                    [cm.matrix[i][j] for j in usable if j not in set(forced_cols)] for i in rest_rows
                ],
            )
            if sub.n_cols():
                pick = greedy_set_cover(sub)
                pick = irredundant_prune(sub, pick)
                free_cols = [j for j in usable if j not in set(forced_cols)]
                for p in pick:
                    chosen_cols.append(free_cols[p])
        selected = sorted({landmarks[j] for j in chosen_cols})
        levels.append(
            _make_level(
                points, selected, scale, A_set, prev_sel, prev_scale, t0,
                n_forced=len(forced), rejected=rejected,
            )
        )
        prev_sel, prev_scale = selected, scale
    return RelTower(levels=levels, A=list(A), mode="relative" if relative else "coverage_only")


def relative_tower_certificate(tower: RelTower) -> dict:
    A = set(tower.A)
    rel_ok = tower.mode == "relative" and all(
        lv.A_covered_by_A_pieces and lv.n_forced > 0 for lv in tower.levels
    )
    return {
        "contracts": ["RelativeEquivalence", "ApproximatePersistence"],
        "mode": tower.mode,
        "qualifier": "TopologicalApproximation",
        "relative_equivalence_checked": rel_ok,
        "n_A": len(A),
        "scales": [lv.scale for lv in tower.levels],
        "cover_sizes": [len(lv.selected) for lv in tower.levels],
        "betti_N": [lv.betti_N for lv in tower.levels],
        "betti_NA": [lv.betti_NA for lv in tower.levels],
        "betti_relative": [lv.betti_rel for lv in tower.levels],
        "A_cover_radius": [lv.A_cover_radius for lv in tower.levels],
        "A_covered_by_A_pieces": [lv.A_covered_by_A_pieces for lv in tower.levels],
        "r_all": [lv.r_all for lv in tower.levels],
        "n_forced_A_pieces": [lv.n_forced for lv in tower.levels],
        "uncovered_points": [lv.uncovered_points for lv in tower.levels],
        "oracle_rejected": [lv.oracle_rejected for lv in tower.levels],
        "refinement_maps_selected": [lv.parent_map for lv in tower.levels],
        "wall_time_s": [lv.wall_time_s for lv in tower.levels],
    }


# ----------------------------------------------------------------- ablations
def kcenter_centers(points: Sequence[Point], k: int, start: int = 0) -> list[int]:
    """Farthest-point traversal (Gonzalez 2-approximation to k-center)."""
    k = min(k, len(points))
    centers = [start]
    md = [_dist(p, points[start]) for p in points]
    while len(centers) < k:
        far = max(range(len(points)), key=lambda i: md[i])
        centers.append(far)
        for i, p in enumerate(points):
            d = _dist(p, points[far])
            if d < md[i]:
                md[i] = d
    return sorted(centers)


def build_budget_matched_baseline(points: list[Point], A: Sequence[int], reference: RelTower) -> RelTower:
    """Coverage-only baseline given exactly the relative tower's per-level budget (k-center)."""
    A_set = set(A)
    levels: list[RelLevel] = []
    prev_sel: list[int] | None = None
    prev_scale = reference.levels[0].scale
    for lv in reference.levels:
        t0 = time.perf_counter()
        sel = kcenter_centers(points, len(lv.selected))
        levels.append(_make_level(points, sel, lv.scale, A_set, prev_sel, prev_scale, t0, n_forced=0))
        prev_sel, prev_scale = sel, lv.scale
    return RelTower(levels=levels, A=list(A), mode="kcenter_same_budget")


def build_a_weighted_greedy(
    points: list[Point], A: Sequence[int], base_scale: float, n_levels: int = 3, a_weight: float = 10.0
) -> RelTower:
    """Greedy set cover where covering an A point is worth ``a_weight`` times a non-A point."""
    A_set = set(A)
    levels: list[RelLevel] = []
    prev_sel: list[int] | None = None
    prev_scale = base_scale
    n = len(points)
    for lev in range(n_levels):
        t0 = time.perf_counter()
        scale = base_scale / (2**lev)
        balls = [
            {i for i in range(n) if _dist(points[i], points[c]) <= scale + 1e-12} for c in range(n)
        ]
        uncovered = set(range(n))
        sel: list[int] = []
        while uncovered:
            best = max(
                range(n),
                key=lambda c: sum(a_weight if i in A_set else 1.0 for i in balls[c] & uncovered),
            )
            sel.append(best)
            uncovered -= balls[best]
        sel = sorted(set(sel))
        levels.append(_make_level(points, sel, scale, A_set, prev_sel, prev_scale, t0, n_forced=0))
        prev_sel, prev_scale = sel, scale
    return RelTower(levels=levels, A=list(A), mode="a_weighted_greedy")


def rips_betti_f2(points: Sequence[Point], idx: Sequence[int], radius: float) -> list[int]:
    """beta_0, beta_1 of the Vietoris-Rips complex (2-skeleton) on points[idx] at ``radius``."""
    idx = list(idx)
    n = len(idx)
    adj = [[False] * n for _ in range(n)]
    edges: list[tuple[int, int]] = []
    for a in range(n):
        for b in range(a + 1, n):
            if _dist(points[idx[a]], points[idx[b]]) <= radius + 1e-12:
                adj[a][b] = adj[b][a] = True
                edges.append((a, b))
    eidx = {e: k for k, e in enumerate(edges)}
    # boundary of edges onto vertices
    d1 = [(1 << a) | (1 << b) for a, b in edges]
    r1 = _rank_f2_bitmask(d1)
    d2 = []
    for a, b in edges:
        for c in range(b + 1, n):
            if adj[a][c] and adj[b][c]:
                d2.append((1 << eidx[(a, b)]) | (1 << eidx[(a, c)]) | (1 << eidx[(b, c)]))
    r2 = _rank_f2_bitmask(d2)
    return [n - r1, len(edges) - r1 - r2]


def build_random_landmark_baseline(
    points: list[Point], A: Sequence[int], reference: RelTower, seed: int = 0
) -> RelTower:
    """Same per-level budget as ``reference``, centres drawn uniformly without replacement."""
    rng = random.Random(seed)
    A_set = set(A)
    levels: list[RelLevel] = []
    prev_sel: list[int] | None = None
    prev_scale = reference.levels[0].scale
    n = len(points)
    for lv in reference.levels:
        t0 = time.perf_counter()
        sel = sorted(rng.sample(range(n), min(len(lv.selected), n)))
        levels.append(_make_level(points, sel, lv.scale, A_set, prev_sel, prev_scale, t0, n_forced=0))
        prev_sel, prev_scale = sel, lv.scale
    return RelTower(levels=levels, A=list(A), mode="random_same_budget")


def nn_recall_A(points: Sequence[Point], A: Sequence[int], selected: Sequence[int]) -> float:
    """Fraction of A-points whose nearest other A-point falls in the same selected piece.

    Each point is replaced by its nearest selected centre.  A hit means the true
    nearest neighbour in A receives the same centre.  This is a retrieval score,
    not a topological invariant; a one-centre cover scores 1.
    """
    A = list(A)
    selected = list(selected)
    if len(A) < 2 or not selected:
        return 0.0
    assign = {
        a: min(selected, key=lambda c: _dist(points[a], points[c])) for a in A
    }
    hits = 0
    for a in A:
        nn = min((b for b in A if b != a), key=lambda b: _dist(points[a], points[b]))
        hits += assign[a] == assign[nn]
    return hits / len(A)


def ablation_report(
    points: list[Point], A: list[int], base_scale: float, n_levels: int = 3
) -> dict:
    """Relative tower vs coverage-only, same-budget k-center, A-weighted greedy, random landmarks."""
    rel = build_relative_tower(points, A, base_scale, n_levels, relative=True)
    towers = {
        "relative": rel,
        "coverage_only": build_relative_tower(points, A, base_scale, n_levels, relative=False),
        "kcenter_same_budget": build_budget_matched_baseline(points, A, rel),
        "a_weighted_greedy": build_a_weighted_greedy(points, A, base_scale, n_levels),
        "random_same_budget": build_random_landmark_baseline(points, A, rel),
    }
    from topospine.spines.gudhi_baseline import gudhi_available, gudhi_rips_betti

    gudhi_ok = gudhi_available()
    # Reference: Rips complex on A at 2*scale (nerve of radius-scale balls ~ Cech/Rips at 2*scale)
    ref = [rips_betti_f2(points, sorted(set(A)), 2 * lv.scale) for lv in rel.levels]
    gudhi_ref = None
    gudhi_match = None
    if gudhi_ok:
        gudhi_ref = [
            gudhi_rips_betti(points, sorted(set(A)), 2 * lv.scale, max_dim=2)[:2] for lv in rel.levels
        ]
        gudhi_match = [ref[k][:2] == gudhi_ref[k][:2] for k in range(len(ref))]
    out: dict = {
        "gudhi_available": gudhi_ok,
        "A_rips_reference_betti": ref,
        "gudhi_rips_betti": gudhi_ref,
        "own_rips_matches_gudhi": gudhi_match,
        "methods": {},
    }
    for name, t in towers.items():
        out["methods"][name] = {
            "cover_sizes": [len(lv.selected) for lv in t.levels],
            "A_cover_radius": [lv.A_cover_radius for lv in t.levels],
            "r_all": [lv.r_all for lv in t.levels],
            "uncovered_points": [lv.uncovered_points for lv in t.levels],
            "betti_NA": [lv.betti_NA for lv in t.levels],
            "betti_NA_matches_rips_A": [
                lv.betti_NA[:2] == ref[k][:2] for k, lv in enumerate(t.levels)
            ],
            "nn_recall_A": [nn_recall_A(points, A, lv.selected) for lv in t.levels],
            "wall_time_s": [lv.wall_time_s for lv in t.levels],
        }
    return out
