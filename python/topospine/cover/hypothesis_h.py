"""Candidate checks for hypothesis (H) of the collapse-branch.

(H) says a minimum cover of the expanded table costs no more than a minimum
cover of the original table that is forced to contain the collapsed prime.
CoverAdmissibleFreeFace does not imply (H).  The predicates below are
decidable filters on a proposed free face.  A filter is:

* refuted, if collapse-branch restricted to pairs that pass the filter still
  returns a cost above plain branch-and-bound on some instance;
* vacuous, if the filter never lets a collapse fire on the instances we tried;
* unrefuted, if it fires at least once and never disagreed with branch-and-bound
  on those instances.  Unrefuted is not a proof.
"""

from __future__ import annotations

from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import BooleanCube


def _parent(cm: CoveringMatrix, col_j: int):
    return cm.col_cubes[col_j]


def _row_count(cm: CoveringMatrix, cube) -> int:
    return sum(rc is not None and rc.is_face_of(cube) for rc in cm.row_cubes)  # type: ignore[attr-defined]


def same_row_support(cm: CoveringMatrix, col_j: int, face) -> bool:
    """The face column would cover exactly the same rows as its parent."""
    parent = _parent(cm, col_j)
    if parent is None:
        return False
    rows_f = _row_count(cm, face)
    return rows_f > 0 and rows_f == _row_count(cm, parent)


def face_is_vertex(cm: CoveringMatrix, col_j: int, face) -> bool:
    return isinstance(face, BooleanCube) and face.dimension == 0


def parent_is_edge(cm: CoveringMatrix, col_j: int, face) -> bool:
    parent = _parent(cm, col_j)
    return isinstance(parent, BooleanCube) and parent.dimension == 1


def face_covers_at_most_one_row(cm: CoveringMatrix, col_j: int, face) -> bool:
    return _row_count(cm, face) <= 1


# Exhaustive-confirmed n=5 instances where admissible collapse-branch is suboptimal.
C2_COUNTEREXAMPLES = {
    "n5_a": [
        "00000", "00001", "00010", "00100", "00101", "01000", "01011", "01100", "01101", "01110",
        "10000", "10010", "10011", "10101", "10111", "11000", "11001", "11010", "11011", "11101",
        "11110",
    ],
    "n5_b": [
        "00001", "00010", "00011", "00100", "00110", "01000", "01001", "01010", "01011", "01110",
        "10000", "10001", "10010", "10011", "10101", "10110", "10111", "11000", "11001", "11010",
        "11101", "11111",
    ],
}


CANDIDATES = {
    "same_row_support": same_row_support,
    "face_is_vertex": face_is_vertex,
    "parent_is_edge": parent_is_edge,
    "face_covers_at_most_one_row": face_covers_at_most_one_row,
}


def classify_predicate(predicate, instances: list[CoveringMatrix]) -> dict:
    """Compare collapse-branch restricted by ``predicate`` with plain branch-and-bound."""
    from topospine.cover.minimize import minimize_cover

    fired = disagreements = 0
    for cm in instances:
        _, std, _ = minimize_cover(cm.copy(), use_collapse=False)
        _, got, st = minimize_cover(
            cm.copy(), use_collapse=True, require_admissible=True, collapse_if=predicate
        )
        fired += int(st.collapse_used > 0)
        disagreements += int(got != std)
    if disagreements:
        status = "refuted"
    elif fired == 0:
        status = "vacuous"
    else:
        status = "unrefuted"
    return {"fired": fired, "disagreements": disagreements, "instances": len(instances), "status": status}
