"""Finite cubical complexes (Boolean or grid cells)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from topospine.core.cubes import BooleanCube, GridCube

Cell = TypeVar("Cell", BooleanCube, GridCube)


@dataclass
class CubicalComplex(Generic[Cell]):
    """Face-closed collection of top cells (closure computed on demand)."""

    top_cells: list[Cell] = field(default_factory=list)
    name: str = ""

    def free_faces_of(self, cell: Cell) -> list[Cell]:
        others = [c for c in self.top_cells if c != cell]
        free: list[Cell] = []
        for face in cell.faces():  # type: ignore[attr-defined]
            if all(not face.is_face_of(o) for o in others):  # type: ignore[attr-defined]
                free.append(face)
        return free

    def collapsible_cells(self) -> list[tuple[Cell, list[Cell]]]:
        out: list[tuple[Cell, list[Cell]]] = []
        for c in self.top_cells:
            if getattr(c, "dimension", 0) < 1:
                continue
            ff = self.free_faces_of(c)
            if ff:
                out.append((c, ff))
        return out

    def euler_characteristic(self) -> int:
        """χ from face-closed set of all faces of top cells (naive)."""
        faces: set[str] = set()
        dims: dict[str, int] = {}

        def add_all(cell: Cell) -> None:
            key = str(cell)
            if key in faces:
                return
            faces.add(key)
            dims[key] = cell.dimension  # type: ignore[attr-defined]
            for f in cell.faces():  # type: ignore[attr-defined]
                add_all(f)

        for c in self.top_cells:
            add_all(c)
        chi = 0
        for key, d in dims.items():
            chi += 1 if d % 2 == 0 else -1
        return chi
