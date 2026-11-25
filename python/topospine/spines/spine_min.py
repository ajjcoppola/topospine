"""Approximate minimum covers (spines) with fail-closed collapsibility."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Sequence

from topospine.core.covering import CoveringMatrix
from topospine.core.simplicial import SimplicialComplex, is_collapsible_flag
from topospine.cover.minimize import minimize_cover


@dataclass
class SpineResult:
    cover_indices: list[int]
    cover_names: list[str]
    cost: float
    certificate: dict
    log: list[str] = field(default_factory=list)
    lower_bound: int = 0
    upper_bound: int = 0
    certified_optimal: bool = False


def _dist(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def candidate_cover_from_points(
    points: list[tuple[float, ...]],
    radius: float,
    *,
    landmark_indices: list[int] | None = None,
) -> CoveringMatrix:
    landmarks = landmark_indices if landmark_indices is not None else list(range(len(points)))
    rows = [f"p{i}" for i in range(len(points))]
    cols = [f"ball({j},r={radius:.3g})" for j in landmarks]
    matrix = [[_dist(points[i], points[j]) <= radius + 1e-12 for j in landmarks] for i in range(len(points))]
    return CoveringMatrix(rows=rows, cols=cols, matrix=matrix, weights=[1.0] * len(landmarks))


def greedy_set_cover(cm: CoveringMatrix) -> list[int]:
    uncovered = set(range(cm.n_rows()))
    chosen: list[int] = []
    while uncovered:
        best_j, best_gain = -1, -1
        for j in range(cm.n_cols()):
            gain = sum(1 for i in uncovered if cm.matrix[i][j])
            if gain > best_gain:
                best_gain, best_j = gain, j
        if best_j < 0 or best_gain == 0:
            break
        chosen.append(best_j)
        uncovered -= {i for i in uncovered if cm.matrix[i][best_j]}
    return chosen


def irredundant_prune(cm: CoveringMatrix, cover: list[int]) -> list[int]:
    cover = list(cover)
    changed = True
    while changed:
        changed = False
        for j in list(cover):
            others = [c for c in cover if c != j]
            if not others:
                continue
            if all(any(cm.matrix[i][c] for c in others) for i in range(cm.n_rows()) if cm.matrix[i][j]):
                cover.remove(j)
                changed = True
    return cover


def spine_min(
    cm: CoveringMatrix,
    *,
    method: Literal["greedy", "espresso_loop", "exact", "horn"] = "espresso_loop",
    horn_mode: Literal["exact", "approx", "probabilistic"] = "approx",
) -> SpineResult:
    log: list[str] = []
    if method == "horn":
        from topospine.cover.horn_chains import controlled_horn_chain_cover

        work = cm.copy()
        if any(abs(w - 1.0) > 1e-9 for w in work.weights):
            work.weights = [1.0] * work.n_cols()
        chain = controlled_horn_chain_cover(work, mode=horn_mode, num_chains=8, seed=0)
        # Optional LP tighten
        ceil_lp = 0
        try:
            import math
            import numpy as np
            from scipy.optimize import linprog

            if work.n_rows() and work.n_cols() <= 64:
                A = np.array(work.matrix, dtype=float)
                lp = linprog(
                    np.ones(work.n_cols()),
                    A_ub=-A,
                    b_ub=-np.ones(work.n_rows()),
                    bounds=(0, 1),
                    method="highs",
                )
                if lp.success:
                    ceil_lp = int(math.ceil(float(lp.fun) - 1e-9))
        except Exception:
            ceil_lp = 0
        L = max(chain.lower_bound, ceil_lp)
        U = int(chain.upper_bound)
        cert_opt = U == L or chain.certified_optimal
        return SpineResult(
            cover_indices=chain.cover_indices,
            cover_names=[cm.cols[i] for i in chain.cover_indices],
            cost=float(U),
            certificate={
                "method": "horn",
                "horn_mode": horn_mode,
                "contract": "CoverOptimality" if cert_opt else "Coverage",
                "L": L,
                "U": U,
                "L_MIS": chain.lower_bound,
                "ceil_LP": ceil_lp,
                "certified_optimal": cert_opt,
                "horn_steps": chain.total_horn_steps,
            },
            log=[f"horn_{horn_mode}=[{L},{U}]"],
            lower_bound=L,
            upper_bound=U,
            certified_optimal=cert_opt,
        )
    if method == "exact":
        idx, cost, stats = minimize_cover(cm.copy(), use_collapse=False)  # exact B&B (collapse-branch not trusted: C2)
        return SpineResult(
            cover_indices=idx,
            cover_names=[cm.cols[i] for i in idx],
            cost=cost,
            certificate={"method": "exact", "contract": "CoverOptimality", "bb_calls": stats.recursive_calls},
            log=stats.log,
            lower_bound=int(cost),
            upper_bound=int(cost),
            certified_optimal=True,
        )
    cover = greedy_set_cover(cm)
    log.append(f"greedy={len(cover)}")
    cover = irredundant_prune(cm, cover)
    if method == "espresso_loop":
        prev = -1
        while len(cover) != prev:
            prev = len(cover)
            cover = irredundant_prune(cm, cover)
        log.append(f"espresso_loop={len(cover)}")
    cost = cm.cost(cover)
    return SpineResult(
        cover_indices=cover,
        cover_names=[cm.cols[j] for j in cover],
        cost=cost,
        certificate={
            "method": method,
            "contract": "Coverage",  # not ProvenMinimum
            "cover_size": len(cover),
            "candidate_size": cm.n_cols(),
            "L": 0,
            "U": len(cover),
        },
        log=log,
        lower_bound=0,
        upper_bound=len(cover),
        certified_optimal=False,
    )


def filter_collapsible_columns(
    points: list[tuple[float, ...]],
    landmarks: list[int],
    radius: float,
    cm: CoveringMatrix,
    *,
    fail_closed: bool = True,
) -> list[int]:
    """
    Keep columns whose local flag complex is collapsible.

    fail_closed=True: if none feasible, raise (no silent fallback to all).
    """
    feasible: list[int] = []
    for j, name in enumerate(cm.cols):
        try:
            center = int(name.split("(")[1].split(",")[0])
        except (IndexError, ValueError):
            center = landmarks[j] if j < len(landmarks) else 0
        covered = [i for i, p in enumerate(points) if _dist(p, points[center]) <= radius + 1e-12]
        if len(covered) <= 1:
            feasible.append(j)
            continue
        edges = [frozenset({a, b}) for a in covered for b in covered if a < b]
        piece = SimplicialComplex.from_maximal_faces(edges if edges else [{covered[0]}])
        if is_collapsible_flag(piece):
            feasible.append(j)
    if not feasible:
        if fail_closed:
            raise ValueError("collapsibility oracle returned empty; refuse silent fallback")
        return []
    return feasible
