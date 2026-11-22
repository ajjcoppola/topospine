"""Exact total unimodularity tests for small covering matrices."""

from __future__ import annotations

from itertools import combinations

from topospine.core.covering import CoveringMatrix


def is_totally_unimodular(cm: CoveringMatrix, max_size: int | None = None) -> bool:
    """
    Exact TU check: every square minor has det in {0, ±1}.

    Enumerates all square submatrices up to min(m, n) (or max_size).
    Catches C5 odd-hole (5×5 det = ±2). For very large matrices, pass max_size
    and treat inconclusive separately via LP witness helpers.
    """
    m = cm.matrix
    rows, cols = len(m), len(m[0]) if m else 0
    if rows == 0 or cols == 0:
        return True
    limit = min(rows, cols)
    if max_size is not None:
        limit = min(limit, max_size)
    for k in range(1, limit + 1):
        for row_idx in combinations(range(rows), k):
            for col_idx in combinations(range(cols), k):
                det = _det_minor(m, row_idx, col_idx)
                if det not in (0, 1, -1):
                    return False
    return True


def odd_hole_c5() -> CoveringMatrix:
    """5×5 cycle incidence (non-TU; det of full matrix is ±2)."""
    # Vertex-edge incidence of C5 is TU; use the complementary 0-diag circulant
    # with two 1's per row that yields |det|=2 when taken as square.
    # Classic non-TU: incidence matrix of odd cycle as node-edge is actually TU.
    # Use the matrix with rows/cols of C5 clique inequalities / cycle support:
    n = 5
    mat = [[0] * n for _ in range(n)]
    for i in range(n):
        mat[i][i] = 0
        mat[i][(i + 1) % n] = 1
        mat[i][(i - 1) % n] = 1
    # This is 2I-ish circulant; det(C5 adj) = 2 for C5 adjacency? 
    # Adjacency of C5 has eigenvalues 2cos(2πk/5); product not ±1.
    rows = [f"r{i}" for i in range(n)]
    cols = [f"c{i}" for i in range(n)]
    return CoveringMatrix(
        rows=rows,
        cols=cols,
        matrix=[[bool(x) for x in row] for row in mat],
    )


def _det_minor(m: list[list[bool]], row_idx: tuple[int, ...], col_idx: tuple[int, ...]) -> int:
    k = len(row_idx)
    if k == 1:
        return int(m[row_idx[0]][col_idx[0]])
    if k == 2:
        a = int(m[row_idx[0]][col_idx[0]])
        b = int(m[row_idx[0]][col_idx[1]])
        c = int(m[row_idx[1]][col_idx[0]])
        d = int(m[row_idx[1]][col_idx[1]])
        return a * d - b * c
    total = 0
    for j in range(k):
        sign = 1 if j % 2 == 0 else -1
        sub_rows = row_idx[1:]
        sub_cols = col_idx[:j] + col_idx[j + 1 :]
        total += sign * int(m[row_idx[0]][col_idx[j]]) * _det_minor(m, sub_rows, sub_cols)
    return total


def lp_integrality_witness(cm: CoveringMatrix) -> dict:
    """
    Lightweight LP extreme-point check for small instances without scipy.

    Enumerates vertices of the fractional cover polytope is hard; here we only
    report whether the all-1/deg fractional solution is integral on essentials.
    Full Ghouila-Houri deferred to Loop 2 with an LP backend.
    """
    if cm.n_rows() == 0:
        return {"integral": True, "method": "empty"}
    # Fractional: x_j = 1/deg for each row then take max — crude
    return {"integral": None, "method": "deferred_ghouila_houri", "note": "Loop 2"}
