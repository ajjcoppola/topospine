"""Exhaustive oracle, B&B comparison, and collapse-branch counterexample hunt."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Any

from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes
from topospine.cover.minimize import MinimizeStats, minimize_cover


def exhaustive_min_cost(cm: CoveringMatrix, max_cols: int = 20) -> tuple[float, list[int]]:
    """Brute-force minimum-cost cover for tiny instances."""
    n = cm.n_cols()
    if n > max_cols:
        raise ValueError(f"too many columns for exhaustive search: {n}")
    best = float("inf")
    best_set: list[int] = []
    for k in range(0, n + 1):
        for combo in combinations(range(n), k):
            if cm.is_cover(combo):
                c = cm.cost(combo)
                if c < best:
                    best = c
                    best_set = list(combo)
    return best, best_set


@dataclass
class AuditResult:
    name: str
    exhaustive_cost: float
    std_cost: float
    col_cost: float
    std_stats: MinimizeStats
    col_stats: MinimizeStats
    costs_agree: bool
    collapse_used: int
    admissibility_ok_on_first: bool | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "exhaustive_cost": self.exhaustive_cost,
            "std_cost": self.std_cost,
            "col_cost": self.col_cost,
            "costs_agree": self.costs_agree,
            "std_calls": self.std_stats.recursive_calls,
            "col_calls": self.col_stats.recursive_calls,
            "std_nodes": self.std_stats.standard_nodes + self.std_stats.collapse_nodes,
            "col_nodes": self.col_stats.standard_nodes + self.col_stats.collapse_nodes,
            "std_time": self.std_stats.wall_time_s,
            "col_time": self.col_stats.wall_time_s,
            "collapse_used": self.collapse_used,
            "admissibility_ok_on_first": self.admissibility_ok_on_first,
            "notes": self.notes,
        }


def audit_collapse_branch(
    cm: CoveringMatrix,
    name: str = "instance",
    depth_limit: int = 64,
    require_admissible: bool = True,
) -> AuditResult:
    """Compare exhaustive oracle, standard B&B, and collapse-branch."""
    notes: list[str] = []
    if cm.n_cols() <= 16:
        exh, _ = exhaustive_min_cost(cm)
    else:
        exh = float("nan")
        notes.append("skipped exhaustive (ncols>16)")

    s_std, s_col = MinimizeStats(), MinimizeStats()
    _, c_std, st = minimize_cover(
        cm.copy(), use_collapse=False, stats=s_std, depth_limit=depth_limit
    )
    _, c_col, ct = minimize_cover(
        cm.copy(),
        use_collapse=True,
        stats=s_col,
        depth_limit=depth_limit,
        require_admissible=require_admissible,
    )

    adm: bool | None = None
    coll = list_collapsible_primes(cm)
    if coll:
        j, faces = coll[0]
        adm = cover_admissible_free_face(cm, j, faces[0])

    agree = (c_std == c_col) and (exh != exh or c_std == exh)  # NaN-safe
    if exh == exh and c_std != exh:
        notes.append(f"std differs from exhaustive: {c_std} vs {exh}")
    if c_std != c_col:
        notes.append(f"collapse differs from std: {c_col} vs {c_std}")

    return AuditResult(
        name=name,
        exhaustive_cost=exh,
        std_cost=c_std,
        col_cost=c_col,
        std_stats=st,
        col_stats=ct,
        costs_agree=agree and c_std == c_col,
        collapse_used=ct.collapse_used,
        admissibility_ok_on_first=adm,
        notes=notes,
    )


def enumerate_boolean_cover_instances(
    n_vars: int = 3,
    max_primes: int = 8,
) -> list[CoveringMatrix]:
    """
    Small Boolean ON-set covers: all primes of random-ish small ON-sets.

    For Loop 1 we enumerate all nonempty ON-sets on n_vars≤3 and build
    Quine–McCluskey-style minterm×prime tables with typed BooleanCube rows.
    """
    instances: list[CoveringMatrix] = []
    if n_vars > 4:
        raise ValueError("n_vars too large for enumeration")
    all_minterms = list(product((0, 1), repeat=n_vars))
    # Sample a structured subset of ON-sets for n=3 (all 2^8 nonempty is fine)
    limit = 2 ** len(all_minterms)
    step = 1 if n_vars <= 3 else max(1, limit // 64)
    for mask in range(1, limit, step):
        on = [all_minterms[i] for i in range(len(all_minterms)) if mask & (1 << i)]
        if not on:
            continue
        primes = _primes_from_minterms(on)
        if not primes or len(primes) > max_primes:
            continue
        rows = [BooleanCube(m) for m in on]
        cm = CoveringMatrix(
            rows=[str(r) for r in rows],
            cols=[str(p) for p in primes],
            matrix=[[r.is_face_of(p) for p in primes] for r in rows],
            weights=[1.0] * len(primes),
            row_cubes=list(rows),
            col_cubes=list(primes),
        )
        instances.append(cm)
        if len(instances) >= 200:
            break
    return instances


def _primes_from_minterms(minterms: list[tuple[int, ...]]) -> list[BooleanCube]:
    """Simple Quine–McCluskey prime generation."""
    cubes: set[BooleanCube] = {BooleanCube(m) for m in minterms}
    changed = True
    while changed:
        changed = False
        lst = list(cubes)
        merged: set[BooleanCube] = set()
        used: set[BooleanCube] = set()
        for i, a in enumerate(lst):
            for b in lst[i + 1 :]:
                m = _merge(a, b)
                if m is not None:
                    merged.add(m)
                    used.add(a)
                    used.add(b)
                    changed = True
        cubes = (cubes - used) | merged
    # primes = cubes not contained in a larger cube in the set
    primes = []
    for c in cubes:
        if not any(c != o and c.is_face_of(o) for o in cubes):
            primes.append(c)
    return primes


def _merge(a: BooleanCube, b: BooleanCube) -> BooleanCube | None:
    if len(a.bits) != len(b.bits):
        return None
    diff = 0
    out: list[int | None] = []
    for x, y in zip(a.bits, b.bits):
        if x == y:
            out.append(x)
        elif x is not None and y is not None and x != y:
            out.append(None)
            diff += 1
        else:
            return None
    if diff == 1:
        return BooleanCube(tuple(out))
    return None


def hunt_admissibility_counterexamples(
    instances: list[CoveringMatrix] | None = None,
) -> list[dict[str, Any]]:
    """
    Find instances where collapse without admissibility check disagrees with
    exhaustive/std, locking C2/C3 boundary.
    """
    if instances is None:
        instances = enumerate_boolean_cover_instances(3)
    hits: list[dict[str, Any]] = []
    for i, cm in enumerate(instances):
        if cm.n_cols() == 0 or cm.n_rows() == 0:
            continue
        coll = list_collapsible_primes(cm)
        if not coll:
            continue
        # Force collapse without admissibility
        bad = audit_collapse_branch(
            cm, name=f"bool3_{i}", require_admissible=False, depth_limit=24
        )
        good = audit_collapse_branch(
            cm, name=f"bool3_{i}_adm", require_admissible=True, depth_limit=24
        )
        if not bad.costs_agree or (bad.exhaustive_cost == bad.exhaustive_cost and bad.col_cost != bad.exhaustive_cost):
            hits.append(
                {
                    "index": i,
                    "bad": bad.as_dict(),
                    "good": good.as_dict(),
                    "first_admissible": good.admissibility_ok_on_first,
                }
            )
    return hits
