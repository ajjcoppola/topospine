"""Counterexample & example zoo for Loop 1."""

from __future__ import annotations

from topospine.core.covering import CoveringMatrix, graded_table_from_cubical
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.core.cubical import CubicalComplex
from topospine.core.homology import betti_numbers_f2, verify_d_squared_zero
from topospine.core.simplicial import SimplicialComplex, is_collapsible_flag
from topospine.cover.tu import is_totally_unimodular, odd_hole_c5


def coppola_2007_boolean_complex() -> CubicalComplex[BooleanCube]:
    """
    Outer hexagon + inner cells from 2007 Fig. 1 as Boolean cubes.

    Outer p1..p6 are dim-2 with free faces; p7..p9 inner.
    """
    primes = [
        parse_boolean_cube("--00"),
        parse_boolean_cube("-0-0"),
        parse_boolean_cube("0--0"),
        parse_boolean_cube("0-0-"),
        parse_boolean_cube("00--"),
        parse_boolean_cube("-00-"),
        parse_boolean_cube("000-"),
        parse_boolean_cube("00-0"),
        parse_boolean_cube("0-00"),
    ]
    return CubicalComplex(top_cells=primes, name="coppola_2007")


def coppola_2007_graded() -> CoveringMatrix:
    """True derived graded T_C (typed row_cubes) — fixes C7."""
    return graded_table_from_cubical(coppola_2007_boolean_complex(), include_faces_down_to=0)


def tiled_2007(k: int = 2) -> CoveringMatrix:
    """Disjoint union of k copies via coordinate padding on Boolean cubes."""
    base = coppola_2007_boolean_complex()
    tops: list[BooleanCube] = []
    for t in range(k):
        prefix = (0,) * (2 * t)
        for c in base.top_cells:
            tops.append(BooleanCube(prefix + c.bits))
    return graded_table_from_cubical(CubicalComplex(top_cells=tops, name=f"tiled_{k}x"))


def suspension_sphere(k: int = 3) -> CoveringMatrix:
    """
    Antipodal removal on k-cube: top cells = edges of equatorial belt for k=3.

    Built as vertex×edge covering of the cycle (no free faces among edges).
    """
    # k=3: 6 edges of octahedral equator ~ C6
    edges = [
        parse_boolean_cube("01-"),
        parse_boolean_cube("0-1"),
        parse_boolean_cube("-01"),
        parse_boolean_cube("10-"),
        parse_boolean_cube("1-0"),
        parse_boolean_cube("-10"),
    ]
    # For k=4 quarantine historically; we still expose graded table
    if k == 4:
        # 2-faces of middle slice — simplified 6 squares on S^2 belt (no free faces)
        edges = [
            parse_boolean_cube("01--"),
            parse_boolean_cube("0-1-"),
            parse_boolean_cube("0--1"),
            parse_boolean_cube("10--"),
            parse_boolean_cube("1-0-"),
            parse_boolean_cube("1--0"),
        ]
    return graded_table_from_cubical(CubicalComplex(top_cells=edges, name=f"suspension_k{k}"))


def filled_triangle_simplices() -> list[frozenset[int]]:
    return [frozenset({0}), frozenset({1}), frozenset({2}),
            frozenset({0, 1}), frozenset({1, 2}), frozenset({0, 2}),
            frozenset({0, 1, 2})]


def bings_house() -> SimplicialComplex:
    return SimplicialComplex.from_maximal_faces(
        [
            {0, 1, 2},
            {0, 2, 3},
            {2, 3, 4},
            {2, 4, 5},
            {4, 5, 6},
            {1, 2, 5},
            {0, 1, 5},
        ]
    )


def dunce_cap() -> SimplicialComplex:
    return SimplicialComplex.from_maximal_faces(
        [
            {0, 1, 2}, {0, 2, 3}, {0, 3, 4}, {1, 2, 5}, {2, 5, 6},
            {3, 4, 6}, {4, 6, 7}, {5, 6, 7}, {1, 5, 7}, {0, 1, 7},
            {0, 4, 7}, {3, 6, 2},
        ]
    )


def demo() -> None:
    cm = coppola_2007_graded()
    print("coppola_2007 graded:", cm.n_rows(), "x", cm.n_cols(), "typed rows", all(r is not None for r in cm.row_cubes))
    tri = filled_triangle_simplices()
    print("β(Δ²)=", betti_numbers_f2(tri, max_dim=2), "d²=0?", verify_d_squared_zero(tri))
    print("C5 TU?", is_totally_unimodular(odd_hole_c5()))
    print("K3 collapsible (weak)?", is_collapsible_flag(SimplicialComplex.from_maximal_faces([{0, 1}, {1, 2}, {0, 2}])))


if __name__ == "__main__":
    demo()
