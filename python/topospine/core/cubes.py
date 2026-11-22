"""Boolean hypercube cubes vs integer-grid cubical cells (distinct semantics)."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterator


@dataclass(frozen=True, order=True)
class BooleanCube:
    """Cube in {0,1,*}^n (None = free / *)."""

    bits: tuple[int | None, ...]

    @property
    def dimension(self) -> int:
        return sum(1 for b in self.bits if b is None)

    def faces(self) -> Iterator[BooleanCube]:
        """Codimension-1 faces."""
        for i, b in enumerate(self.bits):
            if b is None:
                for val in (0, 1):
                    new = list(self.bits)
                    new[i] = val
                    yield BooleanCube(tuple(new))

    def is_face_of(self, other: BooleanCube) -> bool:
        if len(self.bits) != len(other.bits):
            return False
        for a, b in zip(self.bits, other.bits):
            if b is not None and a != b:
                return False
            if b is None and a is not None:
                continue
            if b is None and a is None:
                continue
            if a is None and b is not None:
                return False
        return True

    def vertices(self) -> list[tuple[int, ...]]:
        free = [i for i, b in enumerate(self.bits) if b is None]
        if not free:
            return [tuple(int(b) for b in self.bits)]  # type: ignore[arg-type]
        out: list[tuple[int, ...]] = []
        for assign in product((0, 1), repeat=len(free)):
            bits = list(self.bits)
            for i, v in zip(free, assign):
                bits[i] = v
            out.append(tuple(int(x) for x in bits))  # type: ignore[misc]
        return out

    def first_free_var(self) -> int | None:
        for i, b in enumerate(self.bits):
            if b is None:
                return i
        return None

    def cofactor(self, var: int, val: int) -> BooleanCube:
        bits = list(self.bits)
        bits[var] = val
        return BooleanCube(tuple(bits))

    def __str__(self) -> str:
        return "".join("-" if b is None else str(b) for b in self.bits)


def parse_boolean_cube(s: str) -> BooleanCube:
    bits: list[int | None] = []
    for ch in s.strip():
        if ch in "-*xX":
            bits.append(None)
        elif ch in "01":
            bits.append(int(ch))
        else:
            raise ValueError(f"bad cube char {ch!r} in {s!r}")
    return BooleanCube(tuple(bits))


@dataclass(frozen=True, order=True)
class GridCube:
    """
    Axis-aligned cubical cell on the integer grid Z^d.

    For each coordinate: either a fixed integer (0-cell in that axis) or an
    open unit interval [k, k+1] represented as (k, k+1).
    """

    coords: tuple[tuple[int, int] | int, ...]

    @property
    def dimension(self) -> int:
        return sum(1 for c in self.coords if isinstance(c, tuple))

    def faces(self) -> Iterator[GridCube]:
        for i, c in enumerate(self.coords):
            if isinstance(c, tuple):
                lo, hi = c
                for endpoint in (lo, hi):
                    new = list(self.coords)
                    new[i] = endpoint
                    yield GridCube(tuple(new))

    def is_face_of(self, other: GridCube) -> bool:
        if len(self.coords) != len(other.coords):
            return False
        for a, b in zip(self.coords, other.coords):
            if isinstance(b, int):
                if a != b:
                    return False
            else:
                lo, hi = b
                if isinstance(a, int):
                    if a not in (lo, hi) and not (lo <= a <= hi):
                        # endpoint or interior point of interval
                        if not (lo <= a <= hi):
                            return False
                else:
                    alo, ahi = a
                    if not (lo <= alo and ahi <= hi):
                        return False
        return True

    def __str__(self) -> str:
        parts = []
        for c in self.coords:
            if isinstance(c, int):
                parts.append(str(c))
            else:
                parts.append(f"[{c[0]},{c[1]}]")
        return "(" + ",".join(parts) + ")"
