"""Collapsible primes with typed free-face expansion (no parent-clone)."""

from __future__ import annotations

from topospine.core.covering import CoveringMatrix, CubeLike


def list_collapsible_primes(cm: CoveringMatrix) -> list[tuple[int, list[CubeLike]]]:
    results: list[tuple[int, list[CubeLike]]] = []
    active = [(j, cm.col_cubes[j]) for j in range(cm.n_cols()) if cm.col_cubes[j] is not None]
    for j, pcube in active:
        assert pcube is not None
        if pcube.dimension < 1:  # type: ignore[attr-defined]
            continue
        others = [c for idx, c in active if idx != j and c is not None]
        free: list[CubeLike] = []
        for face in pcube.faces():  # type: ignore[attr-defined]
            if all(not face.is_face_of(o) for o in others):  # type: ignore[attr-defined]
                free.append(face)
        if free:
            results.append((j, free))
    return results


def expand_collapse_once(
    cm: CoveringMatrix,
    col_j: int,
    face: CubeLike,
) -> tuple[CoveringMatrix, str, str]:
    """
    Remove prime col_j; add free-face column with *exact* face incidence.

    Requires typed row_cubes. Raises if any row_cube is None.
    """
    sub = cm.copy()
    p_name = sub.cols[col_j]
    if any(rc is None for rc in sub.row_cubes):
        raise ValueError(
            "expand_collapse_once requires typed row_cubes; "
            "derive T_C via graded_table_from_cubical (C7)"
        )
    coverage = []
    for rc in sub.row_cubes:
        assert rc is not None
        coverage.append(rc.is_face_of(face))  # type: ignore[attr-defined]
    face_name = f"face({p_name},{face})"
    # Reuse existing column if same cube present
    for j, c in enumerate(sub.col_cubes):
        if c == face:
            face_name = sub.cols[j]
            break
    else:
        sub.add_col(face_name, coverage, weight=sub.weights[col_j], cube=face)
    parent_idx = sub.cols.index(p_name)
    sub.remove_cols({parent_idx})
    return sub, p_name, face_name


def cover_admissible_free_face(
    cm: CoveringMatrix,
    col_j: int,
    face: CubeLike,
) -> bool:
    """
    CoverAdmissibleFreeFace (narrowed C2 hypothesis):

    Every row covered by `face` is covered *only* by columns that contain `face`
    as a face of the chosen prime — equivalently, no cover of those rows exists
    that avoids both the parent prime and all columns containing the face's
    geometry without using the parent.

    Practical check used in Loop 1: every row i with incidence to `face` has
    the property that the only original columns covering i are those for which
    face ⊆ col (is_face_of). In particular the parent covers them; if some other
    prime covers i without containing the face, encoding C_in by replacing p
    with F(p) may fail cost transport.
    """
    parent = cm.col_cubes[col_j]
    if parent is None:
        return False
    for i, rc in enumerate(cm.row_cubes):
        if rc is None:
            return False
        if not rc.is_face_of(face):  # type: ignore[attr-defined]
            continue
        for j, pc in enumerate(cm.col_cubes):
            if j == col_j or pc is None:
                continue
            if cm.matrix[i][j] and not face.is_face_of(pc):  # type: ignore[attr-defined]
                # Another prime covers this free-face row without containing the face
                return False
    return True
