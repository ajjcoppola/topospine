"""Suspension sphere, cofactor-split lemma, (H) filters, multi-output AIG sharing."""

from __future__ import annotations

from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import parse_boolean_cube
from topospine.cover.collapse import list_collapsible_primes
from topospine.cover.hypothesis_h import C2_COUNTEREXAMPLES, CANDIDATES, classify_predicate
from topospine.cover.minimize import minimize_cover
from topospine.cover.shotgun import _instance, enumerate_instances
from topospine.examples.zoo import suspension_sphere
from topospine.synth.aig import shared_factored_gates


def test_suspension_sphere_free_faces():
    # k=3 is the 6-cycle with no free face.  The k=4 "belt" in zoo.py is a
    # simplified list of squares that does have free faces; Paper A's sentence
    # "for k>=3, no free face" does not hold for that construction.
    assert list_collapsible_primes(suspension_sphere(3)) == []
    assert list_collapsible_primes(suspension_sphere(4)) != []


def test_cofactor_split_of_a_containment_row_can_change_the_cost():
    """Paper A's lemma is about covering the minterms of a cube.

    Encoding the cube as one containment-row is a different matrix: a heavy
    column that contains the whole cube can lose to two cheap columns that
    each contain one cofactor.  The minterm-row formulation is unchanged by
    'splitting', because the ON-set is the same set of points.
    """
    on = [(0, 0), (0, 1)]
    cm = _instance(2, on)
    _, semantic, _ = minimize_cover(cm.copy(), use_collapse=False)
    assert semantic == 1.0

    parent = parse_boolean_cube("0-")
    left, right = parse_boolean_cube("00"), parse_boolean_cube("01")
    cube_row = CoveringMatrix(
        rows=["0-"],
        cols=["P", "Q", "R"],
        matrix=[[True, False, False]],
        weights=[3.0, 1.0, 1.0],
        row_cubes=[parent],
        col_cubes=[parent, left, right],
    )
    split = CoveringMatrix(
        rows=["00", "01"],
        cols=["P", "Q", "R"],
        matrix=[[True, True, False], [True, False, True]],
        weights=[3.0, 1.0, 1.0],
        row_cubes=[left, right],
        col_cubes=[parent, left, right],
    )
    _, cost_cube, _ = minimize_cover(cube_row, use_collapse=False)
    _, cost_split, _ = minimize_cover(split, use_collapse=False)
    assert cost_cube == 3.0
    assert cost_split == 2.0


def test_hypothesis_filters_on_the_known_counterexamples_and_a_small_n4_sample():
    bad = [
        _instance(5, [tuple(int(ch) for ch in r) for r in rows]) for rows in C2_COUNTEREXAMPLES.values()
    ]
    sample = bad + enumerate_instances(4, 400, seed=4)
    # unrestricted admissible collapse is already refuted by these two instances
    unrestricted = classify_predicate(lambda cm, j, face: True, bad)
    assert unrestricted["status"] == "refuted"
    report = {name: classify_predicate(pred, sample) for name, pred in CANDIDATES.items()}
    # same row-support is sufficient and, on minterm tables, vacuous: a proper face
    # covers fewer rows than its parent.  Vertex faces and edge parents do not
    # occur in this sample (the bad collapses are higher-dimensional).
    for name in ("same_row_support", "face_is_vertex", "parent_is_edge"):
        assert report[name]["status"] == "vacuous"
        assert report[name]["disagreements"] == 0
    # "the face covers at most one row" still allows both n=5 counterexamples
    assert report["face_covers_at_most_one_row"]["status"] == "refuted"


def test_shared_aig_reuses_identical_outputs_and_does_not_grow():
    cubes = [parse_boolean_cube("1-0"), parse_boolean_cube("-01")]
    shared = shared_factored_gates(3, [cubes, cubes, cubes])
    assert shared["gates_shared"] < shared["gates_separate"]
    assert shared["gates_shared"] * 3 == shared["gates_separate"]
