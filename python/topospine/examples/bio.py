"""
Minimal Boolean gene-regulatory cover example (biomarker / regulator panel).

Toy 3-gene network truth table: ON-set of a regulatory phenotype covered by
prime implicants (regulator cubes). Demonstrates certified collapse-branch
on a typed graded covering table.
"""

from __future__ import annotations

from topospine.core.covering import CoveringMatrix
from topospine.core.cubes import BooleanCube
from topospine.cover.auditor import audit_collapse_branch
from topospine.cover.minimize import minimize_cover


def cell_cycle_toy() -> CoveringMatrix:
    """
    Genes (x,y,z). Phenotype ON on minterms {001,011,101,111} (z=1).
    Primes include z (--- wait: * * 1) and smaller.
    """
    on = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
    # Primes: z, and redundant xy-ish — keep z and a few overlapping
    primes = [
        BooleanCube((None, None, 1)),  # z
        BooleanCube((0, None, 1)),  # ~x z
        BooleanCube((1, None, 1)),  # x z
        BooleanCube((None, 0, 1)),
        BooleanCube((None, 1, 1)),
    ]
    rows = [BooleanCube(m) for m in on]
    return CoveringMatrix(
        rows=[str(r) for r in rows],
        cols=[str(p) for p in primes],
        matrix=[[r.is_face_of(p) for p in primes] for r in rows],
        weights=[1.0] * len(primes),
        row_cubes=list(rows),
        col_cubes=list(primes),
    )


def main() -> None:
    cm = cell_cycle_toy()
    cover, cost, stats = minimize_cover(cm.copy(), use_collapse=True)
    print("biomarker panel cost", cost, "cols", [cm.cols[i] for i in cover])
    print("collapse_used", stats.collapse_used, "calls", stats.recursive_calls)
    aud = audit_collapse_branch(cm, name="bio_toy")
    print("audit", aud.as_dict())


if __name__ == "__main__":
    main()
