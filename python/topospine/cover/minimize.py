"""Branch-and-bound with optional certified collapse-branch."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from itertools import combinations

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.cover.collapse import (
    cover_admissible_free_face,
    expand_collapse_once,
    list_collapsible_primes,
)


@dataclass
class MinimizeStats:
    standard_nodes: int = 0
    collapse_nodes: int = 0
    collapse_used: int = 0
    recursive_calls: int = 0
    two_way_branches: int = 0
    dominance_passes: int = 0
    max_table_width: int = 0
    wall_time_s: float = 0.0
    best_cost: float = float("inf")
    admissibility_failures: int = 0
    putback_exact: int = 0
    putback_greedy: int = 0
    log: list[str] = field(default_factory=list)


def _min_subcover_names(
    names: set[str],
    cov: dict[str, frozenset[int]],
    universe: frozenset[int],
    *,
    greedy_threshold: int = 16,
) -> tuple[set[str], str]:
    """Drop redundant columns after decode. Exact for ≤ greedy_threshold cols; else greedy."""
    chosen = [(n, cov[n]) for n in names if n in cov]
    if not chosen:
        return set(names), "noop"
    if len(chosen) > greedy_threshold:
        keep = list(chosen)
        for item in list(keep):
            trial = [x for x in keep if x is not item]
            covered: set[int] = set()
            for _, s in trial:
                covered |= s
            if universe <= covered:
                keep = trial
        return {n for n, _ in keep}, "greedy"
    for k in range(0, len(chosen) + 1):
        for combo in combinations(chosen, k):
            covered: set[int] = set()
            for _, s in combo:
                covered |= s
            if universe <= covered:
                return {n for n, _ in combo}, "exact"
    return {n for n, _ in chosen}, "exact"


def minimize_cover(
    cm: CoveringMatrix,
    use_collapse: bool = True,
    stats: MinimizeStats | None = None,
    depth_limit: int = 64,
    require_admissible: bool = True,
    collapse_if=None,
) -> tuple[list[int], float, MinimizeStats]:
    """``collapse_if(sub, col_j, face)`` may reject a pair.  Rejected pairs are skipped.

    If every admissible pair is rejected, the search falls through to ordinary
    two-way branching.  The default ``None`` keeps the historical policy: the
    first admissible pair is collapsed.

    After decoding free-face columns back to their parents, ``restore`` runs a
    put-back minimum sub-cover (exact ≤ 16 columns, greedy beyond) so cubes now
    covered by ``p`` are dropped — the paper's ``Reduced`` step.
    """
    if stats is None:
        stats = MinimizeStats()
    t0 = time.perf_counter()
    weight_map = {cm.cols[j]: cm.weights[j] for j in range(cm.n_cols())}
    orig_cov = {
        cm.cols[j]: frozenset(i for i in range(cm.n_rows()) if cm.matrix[i][j])
        for j in range(cm.n_cols())
    }
    orig_universe = frozenset(range(cm.n_rows()))
    cm_work = cm.copy()
    cm_work, red_log, essentials = reduce_to_cyclic_core(cm_work)
    stats.log.extend(red_log)
    stats.dominance_passes += 1
    stats.max_table_width = max(stats.max_table_width, cm_work.n_cols())

    if cm_work.n_rows() == 0:
        cost = sum(weight_map[n] for n in essentials)
        indices = [i for i, c in enumerate(cm.cols) if c in essentials]
        stats.best_cost = cost
        stats.wall_time_s = time.perf_counter() - t0
        return indices, cost, stats

    best_names: set[str] = set()
    best_cost = float("inf")
    collapse_stack: list[tuple[str, tuple[str, ...]]] = []

    def cost(names: set[str]) -> float:
        return sum(weight_map.get(n, 1.0) for n in names)

    def restore(names: set[str]) -> set[str]:
        out = set(names)
        for p_name, face_names in reversed(collapse_stack):
            faces = set(face_names)
            if out & faces:
                out -= faces
                out.add(p_name)
                weight_map.setdefault(p_name, 1.0)
        reduced, mode = _min_subcover_names(out, orig_cov, orig_universe)
        if mode == "greedy":
            stats.putback_greedy += 1
        elif mode == "exact":
            stats.putback_exact += 1
        return reduced

    def pick_col(sub: CoveringMatrix) -> int:
        for j, name in enumerate(sub.cols):
            if not name.startswith("face("):
                return j
        return 0

    def bb(sub: CoveringMatrix, forced_names: set[str], depth: int) -> None:
        nonlocal best_cost, best_names
        stats.recursive_calls += 1
        if depth > depth_limit:
            return
        sub, _, ess = reduce_to_cyclic_core(sub)
        stats.dominance_passes += 1
        stats.max_table_width = max(stats.max_table_width, sub.n_cols())
        forced = forced_names | set(ess)
        if sub.n_rows() == 0:
            names = restore(forced)
            c = cost(names)
            if c < best_cost:
                best_cost = c
                best_names = set(names)
            return

        if use_collapse:
            stats.collapse_nodes += 1
            collapsible = list_collapsible_primes(sub)
            for j, free_faces in collapsible:
                face = free_faces[0]
                if require_admissible and not cover_admissible_free_face(sub, j, face):
                    stats.admissibility_failures += 1
                    continue
                if collapse_if is not None and not collapse_if(sub, j, face):
                    continue
                stats.collapse_used += 1
                expanded, p_name, face_name = expand_collapse_once(sub, j, face)
                weight_map.setdefault(face_name, weight_map.get(p_name, 1.0))
                collapse_stack.append((p_name, (face_name,)))
                bb(expanded, forced, depth + 1)
                collapse_stack.pop()
                return

        stats.standard_nodes += 1
        if sub.n_cols() == 0:
            return
        j = pick_col(sub)
        col_name = sub.cols[j]
        stats.two_way_branches += 1

        sub_in = sub.copy()
        rows_drop = {i for i in range(sub_in.n_rows()) if sub_in.matrix[i][j]}
        sub_in.remove_rows(rows_drop)
        sub_in.remove_cols({j})
        bb(sub_in, forced | {col_name}, depth + 1)

        sub_out = sub.copy()
        sub_out.remove_cols({j})
        bb(sub_out, forced, depth + 1)

    bb(cm_work, set(essentials), 0)
    stats.best_cost = best_cost
    stats.wall_time_s = time.perf_counter() - t0
    cover_indices = [i for i, n in enumerate(cm.cols) if n in best_names]
    return cover_indices, best_cost, stats
