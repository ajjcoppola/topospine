"""Shotgun shelling: apply several free-face collapses to a covering table *at once* (claim C9).

A *batch* is a set of (prime, free-face) pairs, one per prime, each admissible
(``CoverAdmissibleFreeFace``) in the **current** table.  Two independence rules:

``rows``   the sets of rows incident to the chosen faces are pairwise disjoint.
           Then admissibility of each pair is unaffected by applying the others, so
           the batch equals any sequential order of single collapses (see
           ``docs/mathematical-contracts.md``, "Shotgun reduces to iterated C2").
``none``   apply every admissible pair simultaneously (naive shotgun); negative control.
``safe``   ``rows`` plus a coverability guard: after removing all chosen parents (and adding
           their faces) every remaining row must still have a covering column.  Needed
           because the batch removes parents *simultaneously*, whereas the sequential
           algorithm re-reduces (forcing essentials) between collapses.

Reduction is *transport-only*: the decoded cover (face column -> parent column) is
always feasible for the original table with the same cost, but the reduced optimum
may exceed the original optimum.  :func:`audit_shotgun` measures exactly that.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from itertools import product
from typing import Any

from topospine.core.covering import CoveringMatrix, CubeLike, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube
from topospine.cover.auditor import _primes_from_minterms, exhaustive_min_cost
from topospine.cover.collapse import cover_admissible_free_face, list_collapsible_primes
from topospine.cover.minimize import minimize_cover


def _rows_of(cm: CoveringMatrix, face: CubeLike) -> frozenset[int]:
    return frozenset(i for i, rc in enumerate(cm.row_cubes) if rc is not None and rc.is_face_of(face))  # type: ignore[attr-defined]


def select_batch(cm: CoveringMatrix, independence: str = "rows") -> list[tuple[int, CubeLike]]:
    """Choose one admissible (col, face) per collapsible prime under the independence rule."""
    if independence not in ("rows", "none", "safe"):
        raise ValueError("independence must be 'rows', 'none' or 'safe'")
    cands: list[tuple[int, CubeLike, frozenset[int]]] = []
    for j, faces in list_collapsible_primes(cm):
        for face in faces:
            if cover_admissible_free_face(cm, j, face):
                cands.append((j, face, _rows_of(cm, face)))
                break
    if independence == "none":
        return [(j, f) for j, f, _ in cands]
    chosen: list[tuple[int, CubeLike]] = []
    used: set[int] = set()
    removed: set[int] = set()
    for j, f, rows in cands:
        if rows & used:
            continue
        if independence == "safe":
            trial_removed = removed | {j}
            face_rows = used | rows
            ok = all(
                i in face_rows
                or any(cm.matrix[i][c] for c in range(cm.n_cols()) if c not in trial_removed)
                for i in range(cm.n_rows())
            )
            if not ok:
                continue
            removed = trial_removed
        used |= rows
        chosen.append((j, f))
    return chosen


def apply_batch(
    cm: CoveringMatrix, batch: list[tuple[int, CubeLike]]
) -> tuple[CoveringMatrix, dict[str, str]]:
    """Replace each chosen prime by its face column (same weight).  Returns (table, face_name -> parent_name)."""
    sub = cm.copy()
    parents = [(sub.cols[j], f) for j, f in batch]
    decode: dict[str, str] = {}
    for p_name, face in parents:
        cov = [rc.is_face_of(face) for rc in sub.row_cubes]  # type: ignore[union-attr,attr-defined]
        j = sub.cols.index(p_name)
        face_name = f"face({p_name},{face})"
        sub.add_col(face_name, cov, weight=sub.weights[j], cube=face)
        decode[face_name] = p_name
    sub.remove_cols({sub.cols.index(p) for p, _ in parents})
    return sub, decode


@dataclass
class ShotgunStats:
    batches: int = 0
    pairs_applied: int = 0
    max_batch: int = 0
    reduced_infeasible: bool = False  # some row of the reduced table has no covering column
    log: list[str] = field(default_factory=list)


def shotgun_minimize(
    cm: CoveringMatrix, independence: str = "rows", max_rounds: int = 64
) -> tuple[list[int], float, ShotgunStats]:
    """Core reduction + shotgun batches to a fixpoint, then plain B&B on the residue, then decode."""
    stats = ShotgunStats()
    work = cm.copy()
    picked: list[str] = []
    decode: dict[str, str] = {}
    for _ in range(max_rounds):
        work, _log, ess = reduce_to_cyclic_core(work)
        picked.extend(ess)
        if work.n_rows() == 0:
            break
        batch = select_batch(work, independence)
        if not batch:
            break
        work, dec = apply_batch(work, batch)
        decode.update(dec)
        stats.batches += 1
        stats.pairs_applied += len(batch)
        stats.max_batch = max(stats.max_batch, len(batch))
    if work.n_rows():
        idx, _c, _st = minimize_cover(work.copy(), use_collapse=False)
        picked.extend(work.cols[i] for i in idx)
    def root(n: str) -> str:  # faces can be collapsed again: decode transitively
        while n in decode:
            n = decode[n]
        return n

    names = {root(n) for n in picked}
    indices = [i for i, n in enumerate(cm.cols) if n in names]
    stats.reduced_infeasible = bool(work.n_rows()) and any(
        not any(r) for r in work.matrix
    )
    return indices, cm.cost(indices), stats


# --------------------------------------------------------------------- audit
def _instance(n: int, on: list[tuple[int, ...]]) -> CoveringMatrix | None:
    primes = _primes_from_minterms(on)
    if not primes:
        return None
    rows = [BooleanCube(m) for m in on]
    return CoveringMatrix(
        rows=[str(r) for r in rows],
        cols=[str(p) for p in primes],
        matrix=[[r.is_face_of(p) for p in primes] for r in rows],
        weights=[1.0] * len(primes),
        row_cubes=list(rows),
        col_cubes=list(primes),
    )


def enumerate_instances(n_vars: int, sample: int | None, seed: int = 0) -> list[CoveringMatrix]:
    """All nonempty ON-sets for n=3; a seeded random sample for n>=4."""
    minterms = list(product((0, 1), repeat=n_vars))
    total = 1 << len(minterms)
    if sample is None or sample >= total - 1:
        masks: list[int] = list(range(1, total))
    else:
        rng = random.Random(seed)
        masks = [rng.randrange(1, total) for _ in range(sample)]
    out = []
    for mask in masks:
        on = [minterms[i] for i in range(len(minterms)) if mask & (1 << i)]
        cm = _instance(n_vars, on)
        if cm is not None:
            out.append(cm)
    return out


def audit_shotgun(
    instances: list[CoveringMatrix], independence: str, exhaustive_cols: int = 12
) -> dict[str, Any]:
    """Compare shotgun cost to the standard-B&B optimum (and to exhaustive where cheap)."""
    n = nontrivial = mismatch = infeasible = exh_checked = std_vs_exh_bad = reduced_infeasible = 0
    examples: list[dict[str, Any]] = []
    for cm in instances:
        n += 1
        std_idx, std_cost, _ = minimize_cover(cm.copy(), use_collapse=False)
        if cm.n_cols() <= exhaustive_cols:
            exh_checked += 1
            ec, _ = exhaustive_min_cost(cm)
            if ec != std_cost:
                std_vs_exh_bad += 1
        sg_idx, sg_cost, st = shotgun_minimize(cm, independence)
        if st.batches:
            nontrivial += 1
        if st.reduced_infeasible:
            reduced_infeasible += 1
        if not cm.is_cover(sg_idx):
            infeasible += 1
        if sg_cost != std_cost:
            mismatch += 1
            if len(examples) < 3:
                examples.append(
                    {"cols": cm.cols, "rows": cm.rows, "std_cost": std_cost, "shotgun_cost": sg_cost,
                     "batches": st.batches, "max_batch": st.max_batch}
                )
    return {
        "independence": independence,
        "instances": n,
        "nontrivial_instances": nontrivial,
        "cost_mismatches": mismatch,
        "infeasible_decodes": infeasible,
        "reduced_table_infeasible": reduced_infeasible,
        "exhaustive_checked": exh_checked,
        "std_vs_exhaustive_disagreements": std_vs_exh_bad,
        "examples": examples,
    }
