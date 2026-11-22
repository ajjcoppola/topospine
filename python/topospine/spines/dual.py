"""Dual views: nerve of a cover, Stanley–Reisner stub, voxel helpers."""

from __future__ import annotations

from itertools import combinations

from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import GridCube
from topospine.core.cubical import CubicalComplex


def nerve_of_cover(cm: CoveringMatrix, max_dim: int = 2) -> list[frozenset[int]]:
    """Nerve: simplex on column subset with nonempty common intersection."""
    n = cm.n_cols()
    simplices: set[frozenset[int]] = set()
    for r in range(1, min(n, max_dim + 1) + 1):
        for combo in combinations(range(n), r):
            if any(all(cm.matrix[i][j] for j in combo) for i in range(cm.n_rows())):
                simplices.add(frozenset(combo))
    return sorted(simplices, key=lambda s: (len(s), sorted(s)))


def stanley_reisner_generators(nerve: list[frozenset[int]], n_verts: int) -> list[frozenset[int]]:
    """
    Minimal non-faces (Stanley–Reisner generators) up to dim 2 stub.

    Returns subsets that are not faces of the nerve.
    """
    faces = set(nerve)
    gens: list[frozenset[int]] = []
    for r in range(1, 4):
        for combo in combinations(range(n_verts), r):
            s = frozenset(combo)
            if s not in faces and r >= 2:
                # minimal: no proper subset missing — stub keeps all nonfaces size 2–3
                gens.append(s)
    return gens[:50]  # cap for Loop 2


def voxel_grid_complex(shape: tuple[int, int, int], threshold_mask: list[list[list[bool]]]) -> CubicalComplex:
    """
    Build a 3D GridCube complex from a boolean voxel mask (top cells = occupied unit cubes).
    """
    sx, sy, sz = shape
    tops: list[GridCube] = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                if threshold_mask[x][y][z]:
                    tops.append(
                        GridCube(
                            (
                                (x, x + 1),
                                (y, y + 1),
                                (z, z + 1),
                            )
                        )
                    )
    return CubicalComplex(top_cells=tops, name=f"voxels_{sx}x{sy}x{sz}")
