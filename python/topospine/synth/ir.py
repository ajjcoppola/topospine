"""Intermediate representation for certificate-carrying rewrite passes."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from topospine.core.cubical import CubicalComplex
from topospine.core.cubes import BooleanCube, GridCube

Cell = BooleanCube | GridCube


@dataclass
class SynthesisState:
    """Complex + optional filtration grades + relative subcomplex + rewrite log."""

    complex: CubicalComplex
    grades: dict[str, float] = field(default_factory=dict)  # cell str -> grade
    relative: set[str] = field(default_factory=set)  # designated subcomplex A (cell names)
    log: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    # "homotopy": cells may be deleted by elementary collapse (simple-homotopy view).
    # "covering": columns of a covering IR; deletion-style passes are forbidden and
    #             collapse inserts the free face in place (CoveringAwareCollapse).
    mode: str = "homotopy"

    def snapshot(self) -> SynthesisState:
        return SynthesisState(
            complex=CubicalComplex(
                top_cells=list(self.complex.top_cells),
                name=self.complex.name,
            ),
            grades=dict(self.grades),
            relative=set(self.relative),
            log=list(self.log),
            meta=deepcopy(self.meta),
            mode=self.mode,
        )

    def size(self) -> int:
        return len(self.complex.top_cells)

    def total_dimension(self) -> int:
        return sum(int(c.dimension) for c in self.complex.top_cells)  # type: ignore[attr-defined]

    def cell_names(self) -> list[str]:
        return [str(c) for c in self.complex.top_cells]


@dataclass
class PassResult:
    accepted: bool
    state: SynthesisState
    certificate: dict[str, Any]
    reason: str = ""
