"""Exact F2 homology via Gaussian elimination on boundary matrices."""

from __future__ import annotations

from itertools import combinations


def _rank_f2(matrix: list[list[int]]) -> int:
    """Row-reduce binary matrix over F2; return rank. Mutates a copy."""
    if not matrix:
        return 0
    m = [row[:] for row in matrix]
    rows, cols = len(m), len(m[0])
    rank = 0
    row = 0
    for col in range(cols):
        pivot = None
        for r in range(row, rows):
            if m[r][col] % 2 == 1:
                pivot = r
                break
        if pivot is None:
            continue
        m[row], m[pivot] = m[pivot], m[row]
        for r in range(rows):
            if r != row and m[r][col] % 2 == 1:
                for c in range(cols):
                    m[r][c] = (m[r][c] + m[row][c]) % 2
        rank += 1
        row += 1
        if row >= rows:
            break
    return rank


def boundary_matrix_f2(
    simplices_by_dim: dict[int, list[frozenset[int]]],
    d: int,
) -> list[list[int]]:
    """
    Boundary ∂_d : C_d → C_{d-1} over F2.

    Columns = d-simplices, rows = (d-1)-simplices.
    """
    if d <= 0:
        return []
    upper = simplices_by_dim.get(d, [])
    lower = simplices_by_dim.get(d - 1, [])
    if not upper or not lower:
        return [[0] * len(upper) for _ in lower] if lower else []
    lower_index = {s: i for i, s in enumerate(lower)}
    mat = [[0] * len(upper) for _ in lower]
    for j, sigma in enumerate(upper):
        verts = sorted(sigma)
        for k in range(len(verts)):
            face = frozenset(verts[:k] + verts[k + 1 :])
            i = lower_index.get(face)
            if i is not None:
                mat[i][j] ^= 1
    return mat


def _skeleton(simplices: list[frozenset[int]]) -> dict[int, list[frozenset[int]]]:
    skel: dict[int, set[frozenset[int]]] = {}
    for s in simplices:
        # add all faces
        verts = sorted(s)
        n = len(verts)
        for r in range(1, n + 1):
            for combo in combinations(verts, r):
                face = frozenset(combo)
                d = r - 1
                skel.setdefault(d, set()).add(face)
    return {d: sorted(faces, key=lambda f: sorted(f)) for d, faces in skel.items()}


def betti_numbers_f2(simplices: list[frozenset[int]], max_dim: int = 2) -> list[int]:
    """
    Exact Betti numbers β_0..β_max_dim over F2.

    β_d = dim ker ∂_d - dim im ∂_{d+1} = (# d-simplices - rank ∂_d) - rank ∂_{d+1}.
    """
    skel = _skeleton(simplices)
    betti: list[int] = []
    for d in range(max_dim + 1):
        n_d = len(skel.get(d, []))
        if n_d == 0:
            betti.append(0)
            continue
        bd = boundary_matrix_f2(skel, d)
        rank_d = _rank_f2(bd) if bd else 0
        bd1 = boundary_matrix_f2(skel, d + 1)
        rank_d1 = _rank_f2(bd1) if bd1 else 0
        # dim ker ∂_d = n_d - rank_d; dim im ∂_{d+1} = rank_d1
        betti.append(max(0, n_d - rank_d - rank_d1))
    return betti


def verify_d_squared_zero(simplices: list[frozenset[int]], max_dim: int = 3) -> bool:
    """Check ∂_{d-1} ∘ ∂_d = 0 over F2 for d = 1..max_dim."""
    skel = _skeleton(simplices)
    for d in range(1, max_dim + 1):
        bd = boundary_matrix_f2(skel, d)
        bd_prev = boundary_matrix_f2(skel, d - 1)
        if not bd or not bd_prev:
            continue
        # multiply bd_prev @ bd over F2
        rows, mid = len(bd_prev), len(bd_prev[0]) if bd_prev else 0
        cols = len(bd[0]) if bd else 0
        if mid != len(bd):
            return False
        for i in range(rows):
            for j in range(cols):
                s = 0
                for k in range(mid):
                    s ^= bd_prev[i][k] & bd[k][j]
                if s:
                    return False
    return True
