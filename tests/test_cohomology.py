"""Loop 4: F2 cohomology, cup products, cup-length and the LS-style cover bound."""

from __future__ import annotations

import random

from topospine.core.cohomology import CohomologyF2, sphere2, torus7, vertex_stars
from topospine.spines.spine_min import greedy_set_cover
from topospine.core.covering import CoveringMatrix


def test_betti_numbers_match_known_surfaces():
    assert CohomologyF2(torus7()).betti() == [1, 2, 1]
    assert CohomologyF2(sphere2()).betti() == [1, 0, 1]
    assert len(torus7()) == 14


def test_coboundary_squared_zero_and_leibniz_rule():
    X = CohomologyF2(torus7())
    rng = random.Random(0)
    n0, n1 = len(X.cells[0]), len(X.cells[1])
    for _ in range(25):
        f = rng.getrandbits(n0)
        assert X.delta(1, X.delta(0, f)) == 0
        a, b = rng.getrandbits(n1), rng.getrandbits(n1)
        # Leibniz over F2: delta(f ∪ a) = delta f ∪ a + f ∪ delta a   (f a 0-cochain, a a 1-cochain)
        assert X.delta(1, X.cup(0, f, 1, a)) == (
            X.cup(1, X.delta(0, f), 1, a) ^ X.cup(0, f, 2, X.delta(1, a))
        )
        # a ∪ b of 1-cochains lands in C^2 = top degree here, so delta of it is 0 (no 3-cells);
        # the 1-cochain Leibniz identity delta(a ∪ b) is proved in Lean on a 3-simplex (Cocycle.lean).
        assert X.delta(2, X.cup(1, a, 1, b)) == 0


def test_torus_cup_length_is_two_and_sphere_is_one():
    T, S = CohomologyF2(torus7()), CohomologyF2(sphere2())
    assert T.cup_length() == 2
    assert S.cup_length() == 1
    a, b = T.H[1]
    ab = T.cup(1, a, 1, b)
    aa = T.cup(1, a, 1, a)
    bb = T.cup(1, b, 1, b)
    assert not T.is_coboundary(2, ab)  # a ∪ b generates H^2 of the torus
    assert T.is_coboundary(2, aa) and T.is_coboundary(2, bb)  # squares vanish mod 2 on T^2


def test_vertex_stars_are_cohomologically_trivial_and_cover_needs_cuplength_plus_one_pieces():
    facets = torus7()
    X = CohomologyF2(facets)
    stars = vertex_stars(facets)
    for v, tris in stars.items():
        assert X.restriction_is_zero_on_positive_cohomology(tris)
    # greedy set cover of the 14 triangles by stars: a cover by trivial pieces
    verts = sorted(stars)
    cm = CoveringMatrix(
        rows=[str(t) for t in facets],
        cols=[f"star{v}" for v in verts],
        matrix=[[t in stars[v] for v in verts] for t in facets],
    )
    cover = greedy_set_cover(cm)
    assert cm.is_cover(cover)
    assert len(cover) >= X.cup_length() + 1 == 3


def test_noncontractible_piece_is_detected():
    facets = torus7()
    X = CohomologyF2(facets)
    stars = vertex_stars(facets)
    complement = [t for t in facets if t not in stars[0]]  # punctured torus
    assert not X.restriction_is_zero_on_positive_cohomology(complement)


def test_one_cochain_leibniz_on_a_3_simplex_exhaustively():
    """delta(a ∪ b) = delta a ∪ b + a ∪ delta b for ALL 1-cochains a, b on the 3-simplex (2^12 pairs)."""
    X = CohomologyF2([(0, 1, 2, 3)])
    n1 = len(X.cells[1])
    assert n1 == 6
    for a in range(1 << n1):
        for b in range(1 << n1):
            lhs = X.delta(2, X.cup(1, a, 1, b))
            rhs = X.cup(2, X.delta(1, a), 1, b) ^ X.cup(1, a, 2, X.delta(1, b))
            assert lhs == rhs
