"""Covering matrices with typed row/col cubes (no None-clone expansion)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from topospine.core.cubes import BooleanCube, GridCube
from topospine.core.cubical import CubicalComplex

CubeLike = BooleanCube | GridCube


@dataclass
class CoveringMatrix:
    rows: list[str]
    cols: list[str]
    matrix: list[list[bool]]
    weights: list[float] = field(default_factory=list)
    row_cubes: list[CubeLike | None] = field(default_factory=list)
    col_cubes: list[CubeLike | None] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.weights:
            self.weights = [1.0] * len(self.cols)
        if not self.row_cubes:
            self.row_cubes = [None] * len(self.rows)
        if not self.col_cubes:
            self.col_cubes = [None] * len(self.cols)

    def copy(self) -> CoveringMatrix:
        return CoveringMatrix(
            rows=list(self.rows),
            cols=list(self.cols),
            matrix=[r[:] for r in self.matrix],
            weights=list(self.weights),
            row_cubes=list(self.row_cubes),
            col_cubes=list(self.col_cubes),
        )

    def n_rows(self) -> int:
        return len(self.rows)

    def n_cols(self) -> int:
        return len(self.cols)

    def cost(self, col_indices: Sequence[int]) -> float:
        return sum(self.weights[j] for j in col_indices)

    def covered(self, col_indices: Sequence[int]) -> list[bool]:
        cov = [False] * self.n_rows()
        for j in col_indices:
            for i in range(self.n_rows()):
                if self.matrix[i][j]:
                    cov[i] = True
        return cov

    def is_cover(self, col_indices: Sequence[int]) -> bool:
        return all(self.covered(col_indices))

    def remove_rows(self, indices: set[int]) -> None:
        keep = [i for i in range(self.n_rows()) if i not in indices]
        self.rows = [self.rows[i] for i in keep]
        self.matrix = [self.matrix[i] for i in keep]
        self.row_cubes = [self.row_cubes[i] for i in keep]

    def remove_cols(self, indices: set[int]) -> None:
        keep = [j for j in range(self.n_cols()) if j not in indices]
        self.cols = [self.cols[j] for j in keep]
        self.matrix = [[row[j] for j in keep] for row in self.matrix]
        self.weights = [self.weights[j] for j in keep]
        self.col_cubes = [self.col_cubes[j] for j in keep]

    def add_col(
        self,
        name: str,
        coverage: list[bool],
        weight: float = 1.0,
        cube: CubeLike | None = None,
    ) -> int:
        if any(c is None for c in self.row_cubes) and cube is not None:
            # Safety: require typed rows when adding geometric face columns
            missing = [i for i, rc in enumerate(self.row_cubes) if rc is None]
            if missing and not all(isinstance(x, bool) for x in coverage):
                raise ValueError("row_cubes required for geometric face expansion")
        self.cols.append(name)
        for i, v in enumerate(coverage):
            self.matrix[i].append(v)
        self.weights.append(weight)
        self.col_cubes.append(cube)
        return len(self.cols) - 1


def _contains(row: CubeLike, col: CubeLike) -> bool:
    return row.is_face_of(col)  # type: ignore[attr-defined]


def graded_table_from_cubical(
    complex: CubicalComplex,
    *,
    include_faces_down_to: int = 0,
) -> CoveringMatrix:
    """
    Derive graded covering table T_C from a cubical complex.

    Columns = top cells (primes). Rows = all faces of dimension ≥ include_faces_down_to
    appearing in the face closure of top cells. Incidence = face relation.
    """
    # Collect face-closed set
    face_set: dict[str, CubeLike] = {}

    def add_closure(cell: CubeLike) -> None:
        key = str(cell)
        if key in face_set:
            return
        if cell.dimension >= include_faces_down_to:  # type: ignore[attr-defined]
            face_set[key] = cell
        for f in cell.faces():  # type: ignore[attr-defined]
            add_closure(f)

    for c in complex.top_cells:
        add_closure(c)

    # Prefer higher-dim rows first for graded view
    rows_cells = sorted(face_set.values(), key=lambda c: (-c.dimension, str(c)))  # type: ignore[attr-defined]
    cols_cells = list(complex.top_cells)
    rows = [str(c) for c in rows_cells]
    cols = [str(c) for c in cols_cells]
    matrix = [[_contains(r, p) for p in cols_cells] for r in rows_cells]
    return CoveringMatrix(
        rows=rows,
        cols=cols,
        matrix=matrix,
        weights=[1.0] * len(cols),
        row_cubes=list(rows_cells),
        col_cubes=list(cols_cells),
    )


def reduce_to_cyclic_core(cm: CoveringMatrix) -> tuple[CoveringMatrix, list[str], list[str]]:
    log: list[str] = []
    essentials: list[str] = []
    changed = True
    while changed:
        changed = False
        if _essentials(cm, log, essentials):
            changed = True
        if _row_dom(cm, log):
            changed = True
        if _col_dom(cm, log):
            changed = True
    if cm.n_rows() == 0:
        log.append("fully covered")
    else:
        log.append(f"cyclic core: {cm.n_rows()}x{cm.n_cols()}")
    return cm, log, essentials


def _essentials(cm: CoveringMatrix, log: list[str], picked: list[str]) -> bool:
    essential: set[int] = set()
    for i in range(cm.n_rows()):
        cols = [j for j in range(cm.n_cols()) if cm.matrix[i][j]]
        if len(cols) == 1:
            essential.add(cols[0])
    if not essential:
        return False
    names = [cm.cols[j] for j in sorted(essential)]
    log.append(f"essentials: {names}")
    picked.extend(n for n in names if n not in picked)
    drop_rows = {i for j in essential for i in range(cm.n_rows()) if cm.matrix[i][j]}
    cm.remove_rows(drop_rows)
    empty = {
        j
        for j in range(cm.n_cols())
        if j not in essential and not any(cm.matrix[i][j] for i in range(cm.n_rows()))
    }
    cm.remove_cols(empty | essential)
    return True


def _row_dom(cm: CoveringMatrix, log: list[str]) -> bool:
    drop: set[int] = set()
    for i in range(cm.n_rows()):
        cov_i = {j for j in range(cm.n_cols()) if cm.matrix[i][j]}
        for k in range(cm.n_rows()):
            if i == k:
                continue
            cov_k = {j for j in range(cm.n_cols()) if cm.matrix[k][j]}
            if cov_i < cov_k:
                drop.add(k)
    if drop:
        log.append(f"row dominance removed {len(drop)}")
        cm.remove_rows(drop)
        return True
    return False


def _col_dom(cm: CoveringMatrix, log: list[str]) -> bool:
    drop: set[int] = set()
    for j in range(cm.n_cols()):
        if j in drop:
            continue
        cov_j = {i for i in range(cm.n_rows()) if cm.matrix[i][j]}
        w_j = cm.weights[j]
        for l in range(cm.n_cols()):
            if j == l or l in drop:
                continue
            cov_l = {i for i in range(cm.n_rows()) if cm.matrix[i][l]}
            w_l = cm.weights[l]
            if cov_l > cov_j and w_l <= w_j:
                drop.add(j)
                break
            if cov_l == cov_j and (w_l < w_j or (w_l == w_j and l < j)):
                drop.add(j)
                break
    if drop:
        log.append(f"col dominance removed {len(drop)}")
        cm.remove_cols(drop)
        return True
    return False
