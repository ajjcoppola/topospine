"""Exact F2 simplicial cohomology, cup products and cup-length (small complexes).

Simplices are sorted tuples of vertex labels; the vertex order is the label order, which
fixes the cup-product convention ``(a ∪ b)(v0..vp+q) = a(v0..vp) · b(vp..vp+q)``.
Linear algebra is over F2 with Python-int bitmasks.

Lusternik–Schnirelmann bound used by the tests (a standard fact, not proved in Lean here):
if X is covered by k subcomplexes U_i whose inclusions induce the zero map on
H^{>=1}(-; F2), then ``cup_length(X) < k``.  Hence any cover by cohomologically trivial
pieces (e.g. contractible stars) has at least ``cup_length(X) + 1`` pieces.
"""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, Sequence

Simplex = tuple[int, ...]


def skeleton(facets: Iterable[Sequence[int]]) -> dict[int, list[Simplex]]:
    cells: dict[int, set[Simplex]] = {}
    for f in facets:
        verts = tuple(sorted(f))
        for r in range(1, len(verts) + 1):
            for c in combinations(verts, r):
                cells.setdefault(r - 1, set()).add(c)
    return {d: sorted(v) for d, v in cells.items()}


def _reduce(vec: int, pivots: dict[int, int]) -> int:
    while vec:
        h = vec.bit_length() - 1
        p = pivots.get(h)
        if p is None:
            return vec
        vec ^= p
    return 0


class CohomologyF2:
    """Cochain complex of a simplicial complex with cohomology bases and a cup product."""

    def __init__(self, facets: Iterable[Sequence[int]]) -> None:
        self.cells = skeleton(facets)
        self.dim = max(self.cells)
        self.index = {d: {s: i for i, s in enumerate(cs)} for d, cs in self.cells.items()}
        # delta^k : C^k -> C^{k+1} as list over k-cells of the bitmask of (k+1)-cells it hits
        self._delta_cols: dict[int, list[int]] = {}
        for k in range(self.dim):
            cols = [0] * len(self.cells[k])
            for j, sigma in enumerate(self.cells[k + 1]):
                for r in range(len(sigma)):
                    face = sigma[:r] + sigma[r + 1 :]
                    cols[self.index[k][face]] ^= 1 << j
            self._delta_cols[k] = cols
        self._build_bases()

    # ---- linear algebra helpers
    def delta(self, k: int, f: int) -> int:
        """Apply delta^k to a k-cochain (bitmask over k-cells)."""
        if k >= self.dim:
            return 0
        out = 0
        for i, col in enumerate(self._delta_cols[k]):
            if (f >> i) & 1:
                out ^= col
        return out

    def _kernel(self, k: int) -> list[int]:
        """Basis of Z^k = ker delta^k (bitmasks of k-cochains)."""
        n = len(self.cells[k])
        if k >= self.dim:
            return [1 << i for i in range(n)]
        pivots: dict[int, tuple[int, int]] = {}  # leading bit of image -> (image, combo)
        kernel: list[int] = []
        for i in range(n):
            img, combo = self._delta_cols[k][i], 1 << i
            while img:
                h = img.bit_length() - 1
                if h in pivots:
                    pimg, pcombo = pivots[h]
                    img ^= pimg
                    combo ^= pcombo
                else:
                    pivots[h] = (img, combo)
                    break
            if img == 0:
                kernel.append(combo)
        return kernel

    def _build_bases(self) -> None:
        self.cocycles: dict[int, list[int]] = {}
        self.coboundary_pivots: dict[int, dict[int, int]] = {}
        self.H: dict[int, list[int]] = {}
        for k in range(self.dim + 1):
            piv: dict[int, int] = {}
            if k > 0:
                for i in range(len(self.cells[k - 1])):
                    img = _reduce(self._delta_cols[k - 1][i], piv)
                    if img:
                        piv[img.bit_length() - 1] = img
            self.coboundary_pivots[k] = piv
            reps: list[int] = []
            piv2 = dict(piv)
            for z in self._kernel(k):
                r = _reduce(z, piv2)
                if r:
                    piv2[r.bit_length() - 1] = r
                    reps.append(z)
            self.H[k] = reps

    # ---- public API
    def betti(self) -> list[int]:
        return [len(self.H[k]) for k in range(self.dim + 1)]

    def is_coboundary(self, k: int, f: int) -> bool:
        return _reduce(f, self.coboundary_pivots[k]) == 0

    def is_cocycle(self, k: int, f: int) -> bool:
        return self.delta(k, f) == 0

    def cup(self, p: int, a: int, q: int, b: int) -> int:
        """Cup product of a p-cochain and a q-cochain, a (p+q)-cochain; zero above dim."""
        n = p + q
        if n > self.dim:
            return 0
        out = 0
        for j, sigma in enumerate(self.cells[n]):
            front, back = sigma[: p + 1], sigma[p:]
            if (a >> self.index[p][front]) & 1 and (b >> self.index[q][back]) & 1:
                out ^= 1 << j
        return out

    def class_is_zero(self, k: int, f: int) -> bool:
        return self.is_coboundary(k, f)

    def cup_length(self) -> int:
        """Longest nonzero product of basis classes of H^{>=1} (multilinearity makes this exact)."""
        gens = [(k, z) for k in range(1, self.dim + 1) for z in self.H[k]]
        best = 0

        def dfs(deg: int, cochain: int, count: int, start: int) -> None:
            nonlocal best
            best = max(best, count)
            for gi in range(start, len(gens)):
                k, z = gens[gi]
                if deg + k > self.dim:
                    continue
                prod = self.cup(deg, cochain, k, z)
                if not self.is_coboundary(deg + k, prod):
                    dfs(deg + k, prod, count + 1, gi)  # same generator may repeat (e.g. x^2)

        for gi, (k, z) in enumerate(gens):
            dfs(k, z, 1, gi)
        return best

    def restriction_is_zero_on_positive_cohomology(self, sub_facets: Iterable[Sequence[int]]) -> bool:
        """Does H^k(X) -> H^k(U) vanish for all k >= 1?  U must be a subcomplex of X."""
        sub = CohomologyF2(sub_facets)
        for k in range(1, sub.dim + 1):
            if k > self.dim:
                break
            for z in self.H[k]:
                r = 0
                for j, sigma in enumerate(sub.cells[k]):
                    if (z >> self.index[k][sigma]) & 1:  # KeyError => not a subcomplex
                        r ^= 1 << j
                if not sub.is_coboundary(k, r):
                    return False
        return True


# ----------------------------------------------------------------- examples
def torus7() -> list[tuple[int, int, int]]:
    """Moebius-Kantor / Csaszar 7-vertex triangulation of the torus (14 triangles)."""
    tri = set()
    for i in range(7):
        tri.add(tuple(sorted((i, (i + 1) % 7, (i + 3) % 7))))
        tri.add(tuple(sorted((i, (i + 2) % 7, (i + 3) % 7))))
    return sorted(tri)  # type: ignore[arg-type]


def sphere2() -> list[tuple[int, ...]]:
    return [c for c in combinations(range(4), 3)]


def vertex_stars(facets: Sequence[Sequence[int]]) -> dict[int, list[tuple[int, ...]]]:
    out: dict[int, list[tuple[int, ...]]] = {}
    for f in facets:
        for v in f:
            out.setdefault(v, []).append(tuple(sorted(f)))
    return out
