"""GUDHI as an external Rips and edge-collapse baseline.

Own code (``rips_betti_f2``) stays the reference used by certificates.  When
GUDHI imports, these helpers recompute the same 2-skeleton over F2 and run
``SimplexTree.collapse_edges`` on a graph.  Callers must not treat a missing
install as a result: :func:`gudhi_available` is the gate.  Nothing here mutates
a :class:`SynthesisState`.
"""

from __future__ import annotations

from typing import Sequence


def gudhi_available() -> bool:
    try:
        import gudhi  # noqa: F401
    except ImportError:
        return False
    return True


def gudhi_rips_betti(
    points: Sequence[Sequence[float]],
    idx: Sequence[int],
    radius: float,
    max_dim: int = 2,
) -> list[int]:
    """Absolute Betti numbers over F2 of the Rips complex at ``radius`` (Euclidean).

    ``max_dim`` must be at least 2 to match ``rips_betti_f2``, which uses filled
    triangles when computing beta_1.  Returns a list of length ``max_dim + 1``.
    """
    import gudhi
    import numpy as np

    idx = list(idx)
    if not idx:
        return [0] * (max_dim + 1)
    pts = np.asarray([points[i] for i in idx], dtype=float)
    st = gudhi.RipsComplex(points=pts, max_edge_length=float(radius)).create_simplex_tree(
        max_dimension=max_dim
    )
    # persistence_dim_max: otherwise GUDHI skips the top dimension, so a pure
    # graph (no triangles) reports beta_1 = 0 even when a cycle is present.
    st.compute_persistence(homology_coeff_field=2, persistence_dim_max=True)
    beta = list(st.betti_numbers())
    if len(beta) < max_dim + 1:
        beta = beta + [0] * (max_dim + 1 - len(beta))
    return beta[: max_dim + 1]


def collapse_graph_edges(
    n_vertices: int,
    edges: Sequence[tuple[int, int]],
    iterations: int = 8,
) -> dict:
    """Edge-collapse a graph with GUDHI.  Returns counts and F2 Betti of the flag expansion.

    The input graph is copied into a fresh simplex tree.  Betti numbers are those of
    the 2-skeleton before collapse and after ``collapse_edges`` + ``expansion(2)``.
    GUDHI's theorem is about persistent homology of the filtration, not equality of
    the static Betti numbers after a partial collapse, so a mismatch is recorded
    rather than asserted.
    """
    import gudhi

    st = gudhi.SimplexTree()
    for v in range(n_vertices):
        st.insert([v])
    n_edges = 0
    for a, b in edges:
        if a == b:
            continue
        st.insert([min(a, b), max(a, b)])
        n_edges += 1

    def flag_betti(tree) -> list[int]:
        exp = gudhi.SimplexTree()
        for simplex, _filt in tree.get_skeleton(1):
            exp.insert(simplex)
        exp.expansion(2)
        exp.compute_persistence(homology_coeff_field=2, persistence_dim_max=True)
        beta = list(exp.betti_numbers())
        return (beta + [0, 0, 0])[:3]

    before = flag_betti(st)
    st.collapse_edges(nb_iterations=iterations)
    after_edges = sum(1 for s, _ in st.get_skeleton(1) if len(s) == 2)
    after = flag_betti(st)
    return {
        "vertices": n_vertices,
        "edges_before": n_edges,
        "edges_after": after_edges,
        "iterations": iterations,
        "betti_before": before,
        "betti_after": after,
        "betti_preserved": before == after,
    }


def rips_edge_collapse(
    points: Sequence[Sequence[float]],
    radius: float,
    iterations: int = 8,
) -> dict:
    """1-skeleton of a Euclidean Rips graph, then GUDHI edge collapse."""
    import math

    pts = [tuple(p) for p in points]

    def dist(a, b) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    edges = [
        (i, j)
        for i in range(len(pts))
        for j in range(i + 1, len(pts))
        if dist(pts[i], pts[j]) <= radius + 1e-12
    ]
    out = collapse_graph_edges(len(pts), edges, iterations=iterations)
    out["radius"] = radius
    return out
