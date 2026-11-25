"""Layer-0 cube-array absolute minimization: legal expansions, cyclic core, free-face push-down, and blobs.

Follows ``docs/definitions-cube-array.md`` (Layer 0, approved 2026-11-23):

1. Input is an **array of cubes** ``C`` implicitly defining ``F = union(minterms(c))``
   without enumerating ``2^n`` minterms.
2. **Legal expansions** operate directly in cube space:
   - ``expand_single_cubes_implicit`` (Espresso-style literal raising via Shannon
     cofactor containment ``candidate <= union(C)`` — zero minterm enumeration,
     avoids full prime blow-up);
   - ``expand_to_primes_blake`` (iterated consensus + absorption in cube space,
     producing all prime implicants ``P(F)`` without listing minterms).
3. **Legal reductions** extract cube-space essentials (via sharp / cofactor
   containment ``p <= union(others)``), build a subcube-row covering table on
   active coordinates only (factoring out globally free variables), iterate
   essentials / dominance, apply **zero-loss free-face push-down**
   (Theorem L0-A: ``(p ∩ R) \\ f = ∅``), and split into connected **blobs**
   (Theorem L0-C: ``opt(⊔ B_i) = ∑ opt(B_i)``).
4. **Iterative free-face push-down to blobs** (``iterative_free_face_blob_bound``)
   pushes remaining free faces down to break bridge cubes into blobs and obtain a
   tight certified window ``(L, U)`` that warm-starts and prunes exact B&B in
   ``minimize_layer0_exact`` / ``minimize_cube_array``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from itertools import combinations, product
from typing import Iterable, Literal, Sequence

from topospine.core.covering import CoveringMatrix, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.cover.collapse import expand_collapse_once, list_collapsible_primes

ExpandMode = Literal["blake_primes", "implicit_single", "none"]


# ----------------------------------------------------------------- cube-space algebra (no minterm enumeration)
def coerce_cubes(cubes: Iterable[BooleanCube | str]) -> list[BooleanCube]:
    out = [parse_boolean_cube(c) if isinstance(c, str) else c for c in cubes]
    if len({len(c.bits) for c in out}) > 1:
        raise ValueError("all cubes in an array must have the same number of variables")
    return out


def cube_intersection(a: BooleanCube, b: BooleanCube) -> BooleanCube | None:
    """Intersection of two Boolean cubes, or None if disjoint."""
    if len(a.bits) != len(b.bits):
        raise ValueError("dimension mismatch")
    bits: list[int | None] = []
    for x, y in zip(a.bits, b.bits):
        if x is None:
            bits.append(y)
        elif y is None or x == y:
            bits.append(x)
        else:
            return None
    return BooleanCube(tuple(bits))


def cube_consensus(a: BooleanCube, b: BooleanCube) -> BooleanCube | None:
    """Consensus cube ``a * b`` if ``a`` and ``b`` oppose in exactly one variable, else None."""
    if len(a.bits) != len(b.bits):
        raise ValueError("dimension mismatch")
    oppose = -1
    bits: list[int | None] = []
    for i, (x, y) in enumerate(zip(a.bits, b.bits)):
        if x is not None and y is not None and x != y:
            if oppose != -1:
                return None
            oppose = i
            bits.append(None)
        elif x is None:
            bits.append(y)
        else:
            bits.append(x)
    return BooleanCube(tuple(bits)) if oppose != -1 else None


def absorb_cubes(cubes: Iterable[BooleanCube]) -> list[BooleanCube]:
    """Remove duplicates and any cube contained in another cube of the family."""
    uniq = sorted(set(cubes), key=lambda c: (-c.dimension, str(c)))
    kept: list[BooleanCube] = []
    for c in uniq:
        if not any(c.is_face_of(big) for big in kept):
            kept.append(c)
    return sorted(kept, key=str)


def cube_contained_in_union(target: BooleanCube, cover: Sequence[BooleanCube]) -> bool:
    """Exact cube-space check ``minterms(target) ⊆ ⋃ minterms(cover)`` via Shannon cofactors.

    Never enumerates minterms; works at arbitrary ambient variable count ``n``.
    """
    restricted: list[BooleanCube] = []
    for c in cover:
        inter = cube_intersection(target, c)
        if inter is None:
            continue
        if inter == target:
            return True
        restricted.append(inter)
    if not restricted:
        return False

    # Pick a free variable of target appearing most often as a fixed literal in restricted cubes
    best_var = -1
    best_score = -1
    for i, b in enumerate(target.bits):
        if b is None:
            score = sum(1 for c in restricted if c.bits[i] is not None)
            if score > best_score:
                best_score = score
                best_var = i
    if best_var == -1 or best_score <= 0:
        return False
    t0 = target.cofactor(best_var, 0)
    t1 = target.cofactor(best_var, 1)
    return cube_contained_in_union(t0, restricted) and cube_contained_in_union(t1, restricted)


def cube_difference(target: BooleanCube, cover: Sequence[BooleanCube]) -> list[BooleanCube]:
    """Sharp operation ``target # cover``: absorbed subcubes covering ``target \\ ⋃ cover``."""
    restricted: list[BooleanCube] = []
    for c in cover:
        inter = cube_intersection(target, c)
        if inter is None:
            continue
        if inter == target:
            return []
        restricted.append(inter)
    if not restricted:
        return [target]

    best_var = -1
    best_score = -1
    for i, b in enumerate(target.bits):
        if b is None:
            score = sum(1 for c in restricted if c.bits[i] is not None)
            if score > best_score:
                best_score = score
                best_var = i
    if best_var == -1 or best_score <= 0:
        return [target]
    d0 = cube_difference(target.cofactor(best_var, 0), restricted)
    d1 = cube_difference(target.cofactor(best_var, 1), restricted)
    return expand_to_primes_blake(d0 + d1) if len(d0) + len(d1) <= 16 else absorb_cubes(d0 + d1)


def expand_single_cubes_implicit(cubes: Sequence[BooleanCube | str]) -> list[BooleanCube]:
    """Implicit legal expansion (Espresso-style EXPAND): greedily raise literals in each cube
    while ``candidate ⊆ ⋃ C`` holds in cube space, then absorb contained cubes.

    Does not enumerate minterms and does not materialize exponentially many consensus primes.
    """
    orig = absorb_cubes(coerce_cubes(cubes))
    expanded: list[BooleanCube] = []
    for c in orig:
        cur = c
        for i, b in enumerate(cur.bits):
            if b is not None:
                bits = list(cur.bits)
                bits[i] = None
                cand = BooleanCube(tuple(bits))
                if cube_contained_in_union(cand, orig):
                    cur = cand
        expanded.append(cur)
    return absorb_cubes(expanded)


def expand_to_primes_blake(
    cubes: Sequence[BooleanCube | str],
    *,
    max_primes: int = 4096,
) -> list[BooleanCube]:
    """Explicit legal expansion to all prime implicants ``P(F)`` via iterated consensus
    (Blake canonical form) directly on cubes — zero minterm enumeration.
    """
    pool = absorb_cubes(coerce_cubes(cubes))
    if not pool:
        return []
    n = len(pool[0].bits)
    # Tison-style variable-by-variable consensus: exact all-primes in <= n passes!
    for var in range(n):
        zeros = [c for c in pool if c.bits[var] == 0]
        ones = [c for c in pool if c.bits[var] == 1]
        new_cons: list[BooleanCube] = []
        for a in zeros:
            for b in ones:
                # Check opposing only in `var`
                ok = True
                bits: list[int | None] = []
                for k in range(n):
                    if k == var:
                        bits.append(None)
                    else:
                        xk, yk = a.bits[k], b.bits[k]
                        if xk is not None and yk is not None and xk != yk:
                            ok = False
                            break
                        bits.append(yk if xk is None else xk)
                if ok:
                    new_cons.append(BooleanCube(tuple(bits)))
        if new_cons:
            pool = absorb_cubes(pool + new_cons)
            if len(pool) > max_primes:
                raise ValueError(f"prime expansion exceeded max_primes={max_primes}; use implicit_single")
    return pool


def extract_cube_space_essentials(
    candidates: Sequence[BooleanCube],
    already_covered: Sequence[BooleanCube] = (),
) -> tuple[list[BooleanCube], list[BooleanCube]]:
    """Return ``(essentials, remaining)`` directly in cube space without listing minterms.

    A candidate ``p`` is essential iff ``p`` is not contained in ``⋃(others ∪ already_covered)``
    AND at least one private point of ``p`` is uncovered.  Wait: for prime implicants ``P(F)`` of
    the full ON-set ``F = ⋃ P(F)``, a prime ``p ∈ P(F)`` has ``p \\ ⋃(P(F)\\{p}) ≠ ∅`` iff
    every point in ``p \\ ⋃(P(F)\\{p})`` is covered ONLY by ``p`` — hence ``p`` is essential!
    When ``candidates`` is a proper subset of primes, a non-contained cube is essential iff it is
    the unique candidate covering some uncovered point; for full Blake primes that condition is
    identical to ``not cube_contained_in_union(p, others + already_covered)``.
    """
    cands = list(candidates)
    essentials: list[BooleanCube] = []
    remaining: list[BooleanCube] = []
    for idx, p in enumerate(cands):
        others = [cands[k] for k in range(len(cands)) if k != idx] + list(already_covered)
        # Drop candidates completely covered by already_covered
        if already_covered and cube_contained_in_union(p, already_covered):
            continue
        if not cube_contained_in_union(p, others):
            essentials.append(p)
        else:
            remaining.append(p)
    return essentials, remaining


def covering_table_from_cube_array(
    remaining_cubes: Sequence[BooleanCube],
    already_covered: Sequence[BooleanCube] = (),
    *,
    max_active_vars: int = 16,
) -> CoveringMatrix:
    """Build an exact typed subcube-row CoveringMatrix for ``remaining_cubes`` outside
    ``already_covered``, factoring out all globally free variables so ambient ``n`` can be large.
    """
    if not remaining_cubes:
        return CoveringMatrix(rows=[], cols=[], matrix=[])
    n = len(remaining_cubes[0].bits)
    all_cubes = list(remaining_cubes) + list(already_covered)
    active_vars = [
        i for i in range(n) if any(c.bits[i] is not None for c in all_cubes)
    ]
    if len(active_vars) > max_active_vars:
        raise ValueError(
            f"active variable count {len(active_vars)} > max_active_vars={max_active_vars}"
        )

    rows_cubes: list[BooleanCube] = []
    for assign in product((0, 1), repeat=len(active_vars)):
        bits: list[int | None] = [None] * n
        for v, val in zip(active_vars, assign):
            bits[v] = val
        atom = BooleanCube(tuple(bits))
        if any(atom.is_face_of(e) for e in already_covered):
            continue
        if any(atom.is_face_of(p) for p in remaining_cubes):
            rows_cubes.append(atom)

    cols = [str(p) for p in remaining_cubes]
    rows = [str(r) for r in rows_cubes]
    matrix = [[r.is_face_of(p) for p in remaining_cubes] for r in rows_cubes]
    return CoveringMatrix(
        rows=rows,
        cols=cols,
        matrix=matrix,
        weights=[1.0] * len(remaining_cubes),
        row_cubes=rows_cubes,
        col_cubes=list(remaining_cubes),
    )


# ----------------------------------------------------------------- blobs & zero-loss free-face push-down
def partition_into_blobs(cm: CoveringMatrix) -> list[CoveringMatrix]:
    """Partition ``cm`` into connected row/column components ("blobs").

    Theorem L0-C: ``opt(cm) = sum(opt(B) for B in partition_into_blobs(cm))``.
    """
    R, C = cm.n_rows(), cm.n_cols()
    if R == 0:
        return []
    seen_r = [False] * R
    seen_c = [False] * C
    blobs: list[CoveringMatrix] = []
    for r0 in range(R):
        if seen_r[r0]:
            continue
        qr = [r0]
        seen_r[r0] = True
        comp_r: list[int] = []
        comp_c: list[int] = []
        while qr:
            r = qr.pop()
            comp_r.append(r)
            for c in range(C):
                if cm.matrix[r][c] and not seen_c[c]:
                    seen_c[c] = True
                    comp_c.append(c)
                    for r2 in range(R):
                        if cm.matrix[r2][c] and not seen_r[r2]:
                            seen_r[r2] = True
                            qr.append(r2)
        comp_r.sort()
        comp_c.sort()
        blobs.append(
            CoveringMatrix(
                rows=[cm.rows[r] for r in comp_r],
                cols=[cm.cols[c] for c in comp_c],
                matrix=[[cm.matrix[r][c] for c in comp_c] for r in comp_r],
                weights=[cm.weights[c] for c in comp_c],
                row_cubes=[cm.row_cubes[r] for r in comp_r],
                col_cubes=[cm.col_cubes[c] for c in comp_c],
            )
        )
    return blobs


def residual_far_rows(cm: CoveringMatrix, col_j: int, face: BooleanCube) -> list[int]:
    """Indices of residual rows in ``cm`` covered by ``col_j`` but NOT contained in ``face``:
    ``F_p(face) = (p ∩ R) \\ face``.
    """
    out: list[int] = []
    for i in range(cm.n_rows()):
        if not cm.matrix[i][col_j]:
            continue
        rc = cm.row_cubes[i]
        if rc is None or not rc.is_face_of(face):  # type: ignore[attr-defined]
            out.append(i)
    return out


def zero_loss_free_face_pushdown(
    cm: CoveringMatrix,
) -> tuple[CoveringMatrix, dict[str, str], int]:
    """Iteratively apply Theorem L0-A: whenever a collapsible cube ``p`` has a free face
    ``f`` with ``F_p(f) = (p ∩ R) \\ f == ∅``, push ``p -> f`` in place.

    Because every row of ``cm`` covered by ``p`` is already contained in ``f``, the
    binary incidence matrix on ``R`` is unchanged, so ``opt`` is preserved identically
    with zero branching while strictly lowering cube dimension.

    Returns ``(pushed_cm, root_name_of_col, n_pushes)``.
    """
    cur = cm.copy()
    root_of = {c: c for c in cur.cols}
    pushes = 0
    if any(rc is None for rc in cur.row_cubes):
        return cur, root_of, 0

    changed = True
    while changed:
        changed = False
        for j, faces in list_collapsible_primes(cur):
            for f in faces:
                if not isinstance(f, BooleanCube):
                    continue
                if len(residual_far_rows(cur, j, f)) == 0:
                    old_name = cur.cols[j]
                    root = root_of[old_name]
                    # If another column already has cube == f, column dominance will merge them;
                    # rename uniquely while tracking root prime for decode.
                    new_name = f"{root}@{f}"
                    idx = 1
                    while new_name in root_of and new_name != old_name:
                        idx += 1
                        new_name = f"{root}@{f}#{idx}"
                    root_of[new_name] = root
                    cur.cols[j] = new_name
                    cur.col_cubes[j] = f
                    pushes += 1
                    changed = True
                    break
            if changed:
                break
    return cur, root_of, pushes


# ----------------------------------------------------------------- bitmask exact kernel + MIS lower bound
def _masks_from_cm(cm: CoveringMatrix) -> tuple[list[int], int]:
    R, C = cm.n_rows(), cm.n_cols()
    univ = (1 << R) - 1
    masks = [sum((1 << i) for i in range(R) if cm.matrix[i][j]) for j in range(C)]
    return masks, univ


def _mis_lower_bound(row_col_masks: list[int], uncovered: int) -> int:
    """Greedy maximal independent set of uncovered rows (no two rows share a column).

    Valid admissible lower bound for unit-weight covering: any cover needs >= |MIS| columns.
    """
    if uncovered == 0:
        return 0
    # Order uncovered rows by fewest covering columns first for a tighter packing LB
    candidates: list[tuple[int, int]] = []
    u = uncovered
    while u:
        lsb = u & -u
        r = lsb.bit_length() - 1
        u ^= lsb
        rm = row_col_masks[r]
        candidates.append((rm.bit_count(), rm))
    candidates.sort(key=lambda x: x[0])
    used_cols = 0
    lb = 0
    for deg, rm in candidates:
        if deg == 0:
            return 10**9  # infeasible!
        if (rm & used_cols) == 0:
            used_cols |= rm
            lb += 1
    return lb


def _min_subcover_indices(masks: list[int], chosen: Sequence[int], univ: int) -> list[int]:
    """Exact minimum sub-cover of ``chosen`` (for <= 16 chosen cols, else greedy)."""
    uniq = sorted(set(chosen))
    if len(uniq) <= 16:
        for k in range(0, len(uniq) + 1):
            for comb in combinations(uniq, k):
                cov = 0
                for j in comb:
                    cov |= masks[j]
                if (cov & univ) == univ:
                    return list(comb)
        return uniq
    keep = list(uniq)
    for item in list(keep):
        trial = [x for x in keep if x != item]
        cov = 0
        for j in trial:
            cov |= masks[j]
        if (cov & univ) == univ:
            keep = trial
    return keep


def _solve_unit_bitmask_bb(
    masks: list[int],
    univ: int,
    *,
    initial_best: Sequence[int] | None = None,
) -> tuple[list[int], int]:
    """Fast exact unit-weight bitmask B&B with MIS lower-bound pruning.

    Returns ``(best_col_indices, recursive_nodes)``.
    """
    if univ == 0:
        return [], 0
    C = len(masks)
    R = univ.bit_length()
    row_cols = [
        sum((1 << j) for j in range(C) if (masks[j] >> r) & 1)
        for r in range(R)
    ]

    if initial_best is not None:
        cov0 = 0
        for j in initial_best:
            cov0 |= masks[j]
        best_sol = list(initial_best) if (cov0 & univ) == univ else list(range(C))
    else:
        # Quick greedy primal bound
        rem = univ
        greedy: list[int] = []
        while rem:
            best_j = max(range(C), key=lambda j: (masks[j] & rem).bit_count())
            if (masks[best_j] & rem) == 0:
                return [], 1  # infeasible
            greedy.append(best_j)
            rem &= ~masks[best_j]
        best_sol = _min_subcover_indices(masks, greedy, univ)

    best_len = len(best_sol)
    nodes = 0

    def _reduce_bitmask(uncov: int, avail: int, cur_len: int) -> tuple[int, int, list[int], bool]:
        """Bitmask essentials + row dominance + column dominance to fixed point."""
        u_w = uncov
        a_w = avail
        forced: list[int] = []
        changed = True
        while changed and u_w != 0:
            changed = False
            # 1. Essentials / dead rows
            ut = u_w
            while ut:
                lsb = ut & -ut
                r = lsb.bit_length() - 1
                ut ^= lsb
                if not ((u_w >> r) & 1):
                    continue
                rc = row_cols[r] & a_w
                if rc == 0:
                    return u_w, a_w, forced, False
                if (rc & (rc - 1)) == 0:
                    j = rc.bit_length() - 1
                    forced.append(j)
                    u_w &= ~masks[j]
                    a_w &= ~rc
                    changed = True
                    if cur_len + len(forced) >= best_len and u_w != 0:
                        return u_w, a_w, forced, False
            if u_w == 0:
                break

            # 2. Drop empty columns & dominated columns
            act_cols: list[tuple[int, int]] = []
            at = a_w
            while at:
                lsb = at & -at
                j = lsb.bit_length() - 1
                at ^= lsb
                mj = masks[j] & u_w
                if mj == 0:
                    a_w ^= lsb
                    changed = True
                else:
                    act_cols.append((j, mj))
            for idx_a, (j, mj) in enumerate(act_cols):
                if not ((a_w >> j) & 1):
                    continue
                for idx_b, (l, ml) in enumerate(act_cols):
                    if idx_a == idx_b or not ((a_w >> l) & 1):
                        continue
                    if (mj & ~ml) == 0 and (ml != mj or l < j):
                        a_w &= ~(1 << j)
                        changed = True
                        break

            # 3. Row dominance: if cov(r1) ⊂ cov(r2) (or == with r1 < r2), drop r2!
            act_rows: list[tuple[int, int]] = []
            ut = u_w
            while ut:
                lsb = ut & -ut
                r = lsb.bit_length() - 1
                ut ^= lsb
                if not ((u_w >> r) & 1):
                    continue
                rc = row_cols[r] & a_w
                if rc == 0:
                    return u_w, a_w, forced, False
                act_rows.append((r, rc))
            for idx_a, (r1, rc1) in enumerate(act_rows):
                if not ((u_w >> r1) & 1):
                    continue
                for idx_b, (r2, rc2) in enumerate(act_rows):
                    if idx_a == idx_b or not ((u_w >> r2) & 1):
                        continue
                    if (rc1 & ~rc2) == 0 and (rc1 != rc2 or r1 < r2):
                        u_w &= ~(1 << r2)
                        changed = True
        return u_w, a_w, forced, True

    def dfs(uncov: int, avail_cols: int, picked: list[int]) -> None:
        nonlocal best_len, best_sol, nodes
        nodes += 1
        if uncov == 0:
            if len(picked) < best_len:
                best_len = len(picked)
                best_sol = list(picked)
            return
        if len(picked) >= best_len:
            return

        u_work, a_work, forced_local, ok = _reduce_bitmask(uncov, avail_cols, len(picked))
        if not ok:
            return
        base_picked = picked + forced_local
        if u_work == 0:
            if len(base_picked) < best_len:
                best_len = len(base_picked)
                best_sol = base_picked
            return
        if len(base_picked) >= best_len:
            return

        cur_row_cols = [row_cols[r] & a_work for r in range(R)]
        lb = _mis_lower_bound(cur_row_cols, u_work)
        if len(base_picked) + lb >= best_len:
            return

        # 2-way branch (in / out) on active column maximizing coverage of u_work
        best_j = -1
        best_cov = 0
        at = a_work
        while at:
            lsb = at & -at
            j = lsb.bit_length() - 1
            at ^= lsb
            c = (masks[j] & u_work).bit_count()
            if c > best_cov:
                best_cov = c
                best_j = j
        if best_j == -1:
            return

        rest_avail = a_work & ~(1 << best_j)
        dfs(u_work & ~masks[best_j], rest_avail, base_picked + [best_j])
        dfs(u_work, rest_avail, base_picked)

    dfs(univ, (1 << C) - 1, [])
    return best_sol, nodes


# ----------------------------------------------------------------- iterative free-face push-down to blobs
@dataclass
class BlobPushResult:
    cover_indices: list[int]
    lower_bound: int
    upper_bound: int
    n_blobs: int
    emptied_by_push: bool
    exact_zero_loss_pushes: int
    lossy_face_pushes: int


def iterative_free_face_blob_bound(cm: CoveringMatrix) -> BlobPushResult:
    """Iteratively push down free faces (zero-loss first, then active ``F(p)``) interleaved
    with legal reductions until no collapsible cubes remain; solve resulting **blobs**
    independently, decode back to root columns of ``cm``, and apply put-back.

    Produces a certified feasible cover of ``cm`` of cost ``U`` and MIS lower bound ``L``.
    """
    if cm.n_rows() == 0:
        return BlobPushResult([], 0, 0, 0, True, 0, 0)

    orig_masks, orig_univ = _masks_from_cm(cm)
    C = cm.n_cols()
    R = cm.n_rows()
    row_cols = [sum((1 << j) for j in range(C) if (orig_masks[j] >> r) & 1) for r in range(R)]
    lb = _mis_lower_bound(row_cols, orig_univ)
    col_index_by_name = {cm.cols[j]: j for j in range(C)}

    cur = cm.copy()
    root_of = {c: c for c in cur.cols}
    forced_roots: set[str] = set()
    exact_pushes = 0
    lossy_pushes = 0

    for step in range(64):
        cur, _, ess = reduce_to_cyclic_core(cur)
        for e in ess:
            forced_roots.add(root_of[e])
        if cur.n_rows() == 0:
            break
        cur, zmap, nz = zero_loss_free_face_pushdown(cur)
        for k, v in zmap.items():
            root_of[k] = root_of.get(v, v)
        exact_pushes += nz
        if nz > 0:
            continue
        coll = list_collapsible_primes(cur)
        if not coll:
            break
        j, faces = coll[0]
        old_name = cur.cols[j]
        root = root_of[old_name]
        added = 0
        for f_idx, f in enumerate(faces):
            cov = [rc is not None and rc.is_face_of(f) for rc in cur.row_cubes]  # type: ignore[attr-defined]
            if any(cov):
                fn = f"ff({step},{f_idx},{f})"
                root_of[fn] = root
                cur.add_col(fn, cov, weight=1.0, cube=f)
                added += 1
        if added == 0:
            break
        cur.remove_cols({j})
        lossy_pushes += 1

    emptied = cur.n_rows() == 0
    blobs = partition_into_blobs(cur)
    for blob in blobs:
        bmasks, buniv = _masks_from_cm(blob)
        bpick, _ = _solve_unit_bitmask_bb(bmasks, buniv)
        for k in bpick:
            forced_roots.add(root_of[blob.cols[k]])

    chosen_idx = [col_index_by_name[nm] for nm in sorted(forced_roots) if nm in col_index_by_name]
    reduced_idx = _min_subcover_indices(orig_masks, chosen_idx, orig_univ)
    return BlobPushResult(
        cover_indices=reduced_idx,
        lower_bound=lb,
        upper_bound=len(reduced_idx),
        n_blobs=len(blobs),
        emptied_by_push=emptied,
        exact_zero_loss_pushes=exact_pushes,
        lossy_face_pushes=lossy_pushes,
    )


# ----------------------------------------------------------------- Layer-0 exact solver
@dataclass
class Layer0SolveResult:
    cubes: list[BooleanCube]
    cost: float
    cube_space_essentials: list[BooleanCube]
    table_essentials: list[str]
    n_candidates_after_expand: int
    n_blobs: int
    zero_loss_pushes: int
    blob_upper_bound_closed: int
    bb_nodes: int
    wall_time_s: float
    log: list[str] = field(default_factory=list)


def minimize_layer0_exact(cm: CoveringMatrix) -> tuple[list[int], float, Layer0SolveResult]:
    """Exact unit-weight Layer-0 solver on a typed CoveringMatrix:
    legal reductions -> zero-loss FF push-down -> blob partitioning ->
    iterative FF blob upper-bound warm-start + MIS-pruned exact B&B.
    """
    t0 = time.perf_counter()
    if any(abs(w - 1.0) > 1e-9 for w in cm.weights):
        raise ValueError("minimize_layer0_exact expects unit-weight columns")

    orig_masks, orig_univ = _masks_from_cm(cm)
    idx_by_name = {cm.cols[j]: j for j in range(cm.n_cols())}
    work = cm.copy()
    root_of = {c: c for c in work.cols}
    picked_roots: set[str] = set()
    total_zpush = 0
    log: list[str] = []

    while True:
        work, rlog, ess = reduce_to_cyclic_core(work)
        log.extend(rlog)
        for e in ess:
            picked_roots.add(root_of[e])
        if work.n_rows() == 0:
            break
        work, zmap, nz = zero_loss_free_face_pushdown(work)
        for k, v in zmap.items():
            root_of[k] = root_of.get(v, v)
        total_zpush += nz
        if nz == 0:
            break
        log.append(f"zero-loss free-face push-down: {nz}")

    blobs = partition_into_blobs(work)
    ub_closed = 0
    bb_nodes = 0

    for blob in blobs:
        bp = iterative_free_face_blob_bound(blob)
        if bp.lower_bound == bp.upper_bound:
            ub_closed += 1
            for k in bp.cover_indices:
                picked_roots.add(root_of[blob.cols[k]])
            continue
        bmasks, buniv = _masks_from_cm(blob)
        bsol, nodes = _solve_unit_bitmask_bb(bmasks, buniv, initial_best=bp.cover_indices)
        bb_nodes += nodes
        for k in bsol:
            picked_roots.add(root_of[blob.cols[k]])

    chosen = [idx_by_name[nm] for nm in sorted(picked_roots)]
    chosen = _min_subcover_indices(orig_masks, chosen, orig_univ)
    chosen_cubes = [cm.col_cubes[j] for j in chosen if isinstance(cm.col_cubes[j], BooleanCube)]
    dt = time.perf_counter() - t0
    res = Layer0SolveResult(
        cubes=chosen_cubes,
        cost=float(len(chosen)),
        cube_space_essentials=[],
        table_essentials=[cm.cols[j] for j in chosen if cm.cols[j] in picked_roots],
        n_candidates_after_expand=cm.n_cols(),
        n_blobs=len(blobs),
        zero_loss_pushes=total_zpush,
        blob_upper_bound_closed=ub_closed,
        bb_nodes=bb_nodes,
        wall_time_s=dt,
        log=log,
    )
    return chosen, float(len(chosen)), res


def minimize_cube_array(
    cubes: Sequence[BooleanCube | str],
    *,
    expand_mode: ExpandMode = "blake_primes",
    max_primes: int = 4096,
    max_active_vars: int = 16,
) -> Layer0SolveResult:
    """End-to-end Layer-0 cube-array minimizer (no explicit minterm input required).

    - ``expand_mode="blake_primes"`` computes the **absolute minimum** cover over all
      prime implicants ``P(F)`` of ``F = ⋃ minterms(cubes)`` via cube-space consensus.
    - ``expand_mode="implicit_single"`` performs implicit single-cube literal raising
      without full prime enumeration when ``|P(F)|`` is huge.
    """
    t0 = time.perf_counter()
    raw = coerce_cubes(cubes)
    if not raw:
        return Layer0SolveResult([], 0.0, [], [], 0, 0, 0, 0, 0, 0.0)

    if expand_mode == "blake_primes":
        cands = expand_to_primes_blake(raw, max_primes=max_primes)
    elif expand_mode == "implicit_single":
        cands = expand_single_cubes_implicit(raw)
    elif expand_mode == "none":
        cands = absorb_cubes(raw)
    else:
        raise ValueError(f"unknown expand_mode: {expand_mode!r}")

    # Cube-space essential extraction (works at arbitrary ambient n without listing minterms!)
    ess_cubes: list[BooleanCube] = []
    rem = list(cands)
    if expand_mode == "blake_primes":
        while rem:
            new_ess, next_rem = extract_cube_space_essentials(rem, ess_cubes)
            if not new_ess:
                break
            ess_cubes.extend(new_ess)
            rem = [c for c in next_rem if not cube_contained_in_union(c, ess_cubes)]
    else:
        rem = [c for c in rem if not (ess_cubes and cube_contained_in_union(c, ess_cubes))]

    if not rem:
        dt = time.perf_counter() - t0
        return Layer0SolveResult(
            cubes=sorted(ess_cubes, key=str),
            cost=float(len(ess_cubes)),
            cube_space_essentials=sorted(ess_cubes, key=str),
            table_essentials=[],
            n_candidates_after_expand=len(cands),
            n_blobs=0,
            zero_loss_pushes=0,
            blob_upper_bound_closed=0,
            bb_nodes=0,
            wall_time_s=dt,
            log=[f"emptied in cube space via {len(ess_cubes)} essentials"],
        )

    cm = covering_table_from_cube_array(rem, ess_cubes, max_active_vars=max_active_vars)
    if cm.n_rows() == 0:
        dt = time.perf_counter() - t0
        return Layer0SolveResult(
            cubes=sorted(ess_cubes, key=str),
            cost=float(len(ess_cubes)),
            cube_space_essentials=sorted(ess_cubes, key=str),
            table_essentials=[],
            n_candidates_after_expand=len(cands),
            n_blobs=0,
            zero_loss_pushes=0,
            blob_upper_bound_closed=0,
            bb_nodes=0,
            wall_time_s=dt,
            log=["residual uncovered domain empty"],
        )

    chosen_idx, sub_cost, sub_res = minimize_layer0_exact(cm)
    core_cubes = [rem[j] for j in chosen_idx]
    all_chosen = sorted(ess_cubes + core_cubes, key=str)
    sub_res.cubes = all_chosen
    sub_res.cost = float(len(all_chosen))
    sub_res.cube_space_essentials = sorted(ess_cubes, key=str)
    sub_res.n_candidates_after_expand = len(cands)
    sub_res.wall_time_s = time.perf_counter() - t0
    return sub_res


# ----------------------------------------------------------------- Layer-0 Far-Side check & canonical counterexamples
def layer0_far_side_holds(cm: CoveringMatrix, col_j: int, face: BooleanCube) -> tuple[bool, int, int]:
    """Check Theorem L0-B (Layer-0 Far-Side IFF) on a unit-weight typed residual ``cm``:

    ``opt(P') == opt(P)`` iff some minimum cover of ``cm`` excludes ``p`` OR covers
    ``F_p(face) = (p ∩ R) \\ face`` without ``p``.

    Returns ``(iff_matches, opt_P, opt_P_prime)``.
    """
    masks, univ = _masks_from_cm(cm)
    C = len(masks)
    opt_sol, _ = _solve_unit_bitmask_bb(masks, univ)
    opt = len(opt_sol)
    others = [masks[k] for k in range(C) if k != col_j]
    fmask = sum((1 << i) for i, rc in enumerate(cm.row_cubes) if rc is not None and rc.is_face_of(face))
    far_mask = masks[col_j] & ~fmask

    exp_sol, _ = _solve_unit_bitmask_bb(others + [fmask], univ)
    opt_exp = len(exp_sol) if exp_sol or univ == 0 else 10**9

    # Check if excluding p is feasible and hits opt
    if all(((univ >> r) & 1) == 0 or any((m >> r) & 1 for m in others) for r in range(cm.n_rows())):
        cout_sol, _ = _solve_unit_bitmask_bb(others, univ)
        cout = len(cout_sol)
    else:
        cout = 10**9

    if cout == opt or far_mask == 0:
        predicted = True
    else:
        need = (univ & ~masks[col_j]) | far_mask
        if all(((need >> r) & 1) == 0 or any((m >> r) & 1 for m in others) for r in range(cm.n_rows())):
            crest_sol, _ = _solve_unit_bitmask_bb(others, need)
            predicted = len(crest_sol) <= opt - 1
        else:
            predicted = False

    return (predicted == (opt_exp == opt)), opt, opt_exp


def layer0_swap_cex_n5_9x9() -> tuple[list[BooleanCube], CoveringMatrix, int]:
    """Genuine Layer-0 existential **swap-only** counterexample (``n=5``, 17 implicit minterms).

    Starting from an input cube array, Blake prime expansion gives 13 primes; legal
    reductions strip 4 essentials ``['1000-', '110-1', '-1010', '01-00']`` and leave a
    ``9×9`` Layer-0 prime cyclic core with **unique** collapsible prime ``0-10-``.

    * ``opt(core) = 4`` (achieved by ``C_in(0-10-)``).
    * Swapping ``0-10-`` to ANY of its 4 free faces (or all 4 simultaneously) yields ``5 > 4``.
    """
    input_cubes = coerce_cubes(
        [
            "1000-",
            "110-1",
            "-1010",
            "01-00",
            "-0101",
            "-0110",
            "-1111",
            "0-10-",
            "001-0",
            "011-1",
            "1-111",
            "101-1",
            "1011-",
        ]
    )
    primes = expand_to_primes_blake(input_cubes)
    full = covering_table_from_cube_array(primes)
    core, _, _ = reduce_to_cyclic_core(full)
    coll = list_collapsible_primes(core)
    assert len(coll) == 1 and core.cols[coll[0][0]] == "0-10-"
    return input_cubes, core, coll[0][0]


def layer0_include_cex_n6_bridged_12x13() -> tuple[list[BooleanCube], CoveringMatrix, int]:
    """Genuine Layer-0 existential **include-only (``C_in``)** counterexample (``n=6``).

    Two antipodal 6-cycles on ``01...0`` and ``10...0`` bridged by the 2-cube ``--0000``,
    whose remaining two corners ``000000, 110000`` are covered by essential primes
    ``00000-, 11000-``.  Blake prime expansion yields 15 primes; legal reductions strip
    ``00000-`` and ``11000-``, leaving a ``12×13`` Layer-0 prime cyclic core with
    **unique** collapsible prime ``--0000``.

    * ``opt(core) = 6`` (3 edges on each 6-cycle, **excluding** ``--0000``).
    * Forcing ``--0000`` in (``C_in``) yields ``1 + 3 + 3 = 7 > 6``.
    * Pushing ``--0000`` down to its free faces + column dominance **splits the core into
      two independent ``6×6`` blobs** and recovers ``opt = 6``.
    """
    cyc3 = ["000", "001", "011", "111", "110", "100"]
    on_minterm_cubes = coerce_cubes(
        ["01" + c + "0" for c in cyc3]
        + ["10" + c + "0" for c in cyc3]
        + ["000000", "000001", "110000", "110001"]
    )
    primes = expand_to_primes_blake(on_minterm_cubes)
    full = covering_table_from_cube_array(primes)
    core, _, _ = reduce_to_cyclic_core(full)
    coll = list_collapsible_primes(core)
    assert len(coll) == 1 and core.cols[coll[0][0]] == "--0000"
    return primes, core, coll[0][0]
