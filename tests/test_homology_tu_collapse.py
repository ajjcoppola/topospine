"""Kernel repair tests: homology, TU, collapsibility, typed expansion."""

from topospine.core.homology import betti_numbers_f2, verify_d_squared_zero
from topospine.core.simplicial import SimplicialComplex, is_collapsible_flag
from topospine.cover.collapse import expand_collapse_once, list_collapsible_primes
from topospine.cover.tu import is_totally_unimodular, odd_hole_c5
from topospine.examples.zoo import (
    coppola_2007_graded,
    filled_triangle_simplices,
)


def test_filled_triangle_betti_zero_cycle():
    tri = filled_triangle_simplices()
    assert verify_d_squared_zero(tri)
    b = betti_numbers_f2(tri, max_dim=2)
    assert b[0] == 1
    assert b[1] == 0


def test_c5_not_tu():
    assert is_totally_unimodular(odd_hole_c5()) is False


def test_weak_collapse_on_k3():
    k3 = SimplicialComplex.from_maximal_faces([{0, 1}, {1, 2}, {0, 2}])
    assert is_collapsible_flag(k3) is True


def test_graded_table_typed_rows():
    cm = coppola_2007_graded()
    assert all(rc is not None for rc in cm.row_cubes)
    assert cm.n_cols() == 9
    assert len(list_collapsible_primes(cm)) >= 1


def test_expand_typed_face_not_parent_clone():
    cm = coppola_2007_graded()
    coll = list_collapsible_primes(cm)
    j, faces = coll[0]
    parent_cov = [cm.matrix[i][j] for i in range(cm.n_rows())]
    expanded, _, face_name = expand_collapse_once(cm, j, faces[0])
    face_j = expanded.cols.index(face_name)
    face_cov = [expanded.matrix[i][face_j] for i in range(expanded.n_rows())]
    expected = [
        rc.is_face_of(faces[0]) for rc in cm.row_cubes if rc is not None
    ]
    assert face_cov == expected
    assert sum(face_cov) <= sum(parent_cov)
