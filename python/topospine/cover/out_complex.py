"""The ``Out_complex`` 4-step formulation of collapsible-cube reduction.

Given a covering instance ``(R, P)`` with a collapsible prime ``FF_c`` (column
``col_j``) of unit weight:

1. Form ``Out_complex`` by removing ``FF_c`` while keeping intersection faces in
   ``Out_complex`` (see the three geometric variants below).
2. Find a minimum cover ``MinCov`` of ``Out_complex``.
3. If ``Intersection(MinCov, FF_c) == FF_c`` (every row of ``FF_c`` in ``R`` is
   already covered by ``MinCov``), return ``MinCov``.
4. Otherwise return ``MinCov + {FF_c}`` (or ``ReducedCov(MinCov + {FF_c})``).

What holds unconditionally and what requires transport ``(H_out)``:

* **Feasibility** holds unconditionally whenever ``R \\ rows(FF_c) <= R_out``.
* **Optimality** holds iff ``(H_out)`` holds for the chosen ``MinCov``:
    - in Step 3: ``cost(MinCov) <= cost(C_in)``;
    - in Step 4: ``cost(ReducedCov(MinCov + {FF_c})) <= min(cost(C_in), cost(C_out))``.
* **Why unconditional optimality fails** (three minimal geometric witnesses):
    1. *Bridge redundancy* (``path4_bridge_instance``, ``n=3``, 4 minterms, 3 edges):
       without ``ReducedCov`` Step 4 returns 3 vs optimum 2; with ``ReducedCov``
       all 198 collapsible ``n=3`` Boolean instances agree with the exact optimum.
    2. *Collar lock-in* (``path6_collar_lockin_instance``, ``n=4``, 6 minterms,
       5 edges forming path ``P_6``): **not a cyclic core** (it still has essential
       edges / free-face essentials under face rows).  Kept as a Boolean
       ``Out_complex`` witness only: keeping the shared vertex ``0000`` lets
       ``MinCov(Out_complex)`` pick ``{e2, e4, e5}`` (cost 3); adding
       ``FF_c = e1`` yields an *irredundant* cost-4 cover while ``{e1, e3, e5}``
       covers ``P_6`` with cost 3.
    3. *Cyclic-core shared boundary* (``cyclic_core_step3_trap_n4`` and
       ``cyclic_core_exclude_win_n5``): after essential removal every remaining
       minterm of ``FF_c`` lies in some other prime, so ``keep_intersection``
       leaves ``R_out = R`` and always takes Step 3 (``= C_out``, failing 192/1544
       times on ``n=4``).  Dropping all ``FF_c`` rows instead (``drop_all_ff_rows``,
       ``= C_in``) succeeds on **all 1,544 ``n=4`` cyclic cores (4,368 collapsible
       primes)** and first fails at ``n=5`` when the unique minimum cover excludes
       ``FF_c`` (cost 5 vs 4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Sequence

from topospine.core.covering import CoveringMatrix, CubeLike, reduce_to_cyclic_core
from topospine.core.cubes import BooleanCube, parse_boolean_cube
from topospine.cover.collapse import list_collapsible_primes
from topospine.cover.minimize import minimize_cover

OutVariant = Literal[
    "keep_intersection",
    "drop_free_face",
    "drop_all_ff_rows",
    "link_opposite",
]

OUT_VARIANTS: tuple[OutVariant, ...] = (
    "keep_intersection",
    "drop_free_face",
    "drop_all_ff_rows",
    "link_opposite",
)

@dataclass
class OutComplexResult:
    cover_indices: list[int]
    cover_names: list[str]
    cost: float
    step_taken: int  # 3 (MinCov already covers FF_c) or 4 (added FF_c)
    out_cover_names: list[str]
    out_cost: float
    ff_col_name: str
    variant: OutVariant
    use_reduced: bool
    is_feasible: bool


def irredundant_cover(cm: CoveringMatrix, col_indices: Sequence[int]) -> list[int]:
    """``ReducedCov``: greedily drop redundant columns while preserving coverage."""
    keep = list(dict.fromkeys(col_indices))
    for j in list(keep):
        trial = [k for k in keep if k != j]
        if cm.is_cover(trial):
            keep = trial
    return keep


def build_out_complex(
    cm: CoveringMatrix,
    col_j: int,
    variant: OutVariant = "keep_intersection",
    free_face: CubeLike | None = None,
) -> CoveringMatrix:
    """Construct ``Out_complex`` after removing column ``col_j`` (``FF_c``)."""
    if variant not in OUT_VARIANTS:
        raise ValueError(f"unknown Out_complex variant: {variant!r}")
    ff_cube = cm.col_cubes[col_j]
    free_faces: list[CubeLike] = []
    if variant == "drop_free_face":
        if free_face is not None:
            free_faces = [free_face]
        else:
            for j, fs in list_collapsible_primes(cm):
                if j == col_j:
                    free_faces = list(fs)
                    break

    out = cm.copy()
    out.remove_cols({col_j})
    drop_rows: set[int] = set()
    if variant == "keep_intersection":
        # Drop only rows that were covered exclusively by FF_c; every row shared
        # with at least one remaining column stays in Out_complex.
        drop_rows = {i for i in range(out.n_rows()) if not any(out.matrix[i])}
    elif variant == "drop_free_face":
        for i, rc in enumerate(out.row_cubes):
            if rc is not None and any(rc.is_face_of(ff) for ff in free_faces):  # type: ignore[attr-defined]
                drop_rows.add(i)
        drop_rows |= {i for i in range(out.n_rows()) if not any(out.matrix[i])}
    elif variant == "drop_all_ff_rows":
        if ff_cube is not None:
            drop_rows = {
                i
                for i, rc in enumerate(out.row_cubes)
                if rc is not None and rc.is_face_of(ff_cube)  # type: ignore[attr-defined]
            }
        else:
            drop_rows = {i for i in range(cm.n_rows()) if cm.matrix[i][col_j]}
        drop_rows |= {i for i in range(out.n_rows()) if not any(out.matrix[i])}
    elif variant == "link_opposite":
        # Boolean tables have no geometric opp/link; fall back to keep_intersection
        # (grid Link(opp) lives in cover.grid2d.link_out_complex).
        drop_rows = {i for i in range(out.n_rows()) if not any(out.matrix[i])}
    out.remove_rows(drop_rows)
    return out


def out_complex_step(
    cm: CoveringMatrix,
    col_j: int,
    *,
    variant: OutVariant = "keep_intersection",
    use_reduced: bool = True,
    free_face: CubeLike | None = None,
    out_solver: Callable[[CoveringMatrix], list[int]] | None = None,
) -> OutComplexResult:
    """Run the 4-step ``Out_complex`` reduction on column ``col_j`` (``FF_c``)."""
    ff_name = cm.cols[col_j]
    out = build_out_complex(cm, col_j, variant=variant, free_face=free_face)
    if out.n_rows() == 0:
        out_idx: list[int] = []
    elif out_solver is not None:
        out_idx = list(out_solver(out))
    else:
        out_idx, _, _ = minimize_cover(out.copy(), use_collapse=False)
    out_names = [out.cols[k] for k in out_idx]
    out_cost = out.cost(out_idx)

    mapped = [cm.cols.index(nm) for nm in out_names]
    # Step 2/3 check: Intersection(MinCov, FF_c) == FF_c on the rows of cm.
    ff_rows = [i for i in range(cm.n_rows()) if cm.matrix[i][col_j]]
    cov_vec = cm.covered(mapped)
    if all(cov_vec[i] for i in ff_rows) and all(cov_vec):
        final_idx = mapped
        step = 3
    else:
        final_idx = mapped + [col_j]
        if use_reduced:
            final_idx = irredundant_cover(cm, final_idx)
        step = 4

    return OutComplexResult(
        cover_indices=final_idx,
        cover_names=[cm.cols[k] for k in final_idx],
        cost=cm.cost(final_idx),
        step_taken=step,
        out_cover_names=out_names,
        out_cost=out_cost,
        ff_col_name=ff_name,
        variant=variant,
        use_reduced=use_reduced,
        is_feasible=cm.is_cover(final_idx),
    )


def check_h_out(
    cm: CoveringMatrix,
    col_j: int,
    *,
    variant: OutVariant = "keep_intersection",
    use_reduced: bool = True,
) -> tuple[bool, OutComplexResult, float]:
    """Return ``(holds, result, exact_opt_cost)`` comparing the 4-step output to plain B&B."""
    res = out_complex_step(cm, col_j, variant=variant, use_reduced=use_reduced)
    _, opt, _ = minimize_cover(cm.copy(), use_collapse=False)
    return (res.is_feasible and res.cost == opt), res, opt


# ----------------------------------------------------------------- canonical witnesses
def _table_from_strings(row_strs: Sequence[str], col_strs: Sequence[str]) -> CoveringMatrix:
    rows = [parse_boolean_cube(r) for r in row_strs]
    cols = [parse_boolean_cube(c) for c in col_strs]
    return CoveringMatrix(
        rows=list(row_strs),
        cols=list(col_strs),
        matrix=[[r.is_face_of(c) for c in cols] for r in rows],
        weights=[1.0] * len(cols),
        row_cubes=rows,
        col_cubes=cols,
    )


def path4_bridge_instance() -> tuple[CoveringMatrix, int]:
    """``n=3`` 4-vertex, 3-edge path: shows why Step 4 needs ``ReducedCov``."""
    cm = _table_from_strings(
        row_strs=["100", "000", "001", "011"],
        col_strs=["-00", "00-", "0-1"],
    )
    return cm, 0  # FF_c = -00 (free vertex 100, shared vertex 000)


def path6_collar_lockin_instance() -> tuple[CoveringMatrix, int]:
    """``n=4`` 6-vertex, 5-edge path ``P_6``: collar lock-in (**not** a cyclic core).

    The path retains essential edges, so it is a non-core witness for the
    ``Out_complex`` put-back gap, not evidence about cyclic-core free faces.

    Vertices along the path:
        v1=1000 --e1(-000)-- v2=0000 --e2(00-0)-- v3=0010
                --e3(001-)-- v4=0011 --e4(0-11)-- v5=0111 --e5(01-1)-- v6=0101

    * True minimum cover: ``{e1, e3, e5}`` of cost **3**.
    * ``Out_complex`` (removing ``e1`` while keeping intersection vertex ``v2=0000``)
      is the 5-vertex path ``P_5`` on ``v2..v6``; ``{e2, e4, e5}`` is a minimum
      cover of ``Out_complex`` of cost **3**.
    * Step 4 adds ``e1`` to get ``{e1, e2, e4, e5}`` of cost **4**, which is
      *irredundant* (``v1`` needs ``e1``, ``v3`` needs ``e2``, ``v4`` needs ``e4``,
      ``v6`` needs ``e5``).
    """
    cm = _table_from_strings(
        row_strs=["1000", "0000", "0010", "0011", "0111", "0101"],
        col_strs=["-000", "00-0", "001-", "0-11", "01-1"],
    )
    return cm, 0  # FF_c = -000


def cyclic_core_step3_trap_n4() -> tuple[CoveringMatrix, int]:
    """``9x9`` ``n=4`` cyclic core where ``keep_intersection`` takes Step 3 (cost 5 vs 4)."""
    cm = _table_from_strings(
        row_strs=["0000", "0001", "0011", "0100", "0110", "0111", "1000", "1010", "1011"],
        col_strs=["000-", "00-1", "--00", "0-11", "-011", "10-0", "01-0", "101-", "011-"],
    )
    return cm, 2  # FF_c = --00 (free face 0-00)


def cyclic_core_exclude_win_n5() -> tuple[CoveringMatrix, int]:
    """``9x9`` ``n=5`` partial-domain cube table where every variant adding ``FF_c`` gets 5 vs opt 4.

    Layer-0 note (``docs/definitions-cube-array.md``): this synthetic table lists only 9
    of the 17 minterms covered by its 9 cubes; on the full implicit ON-set of that cube
    array, 5 primes are essential and the Layer-0 cyclic core is ``0x0``.  For the genuine
    Layer-0 prime cyclic-core ``C_in`` counterexample (where ALL implicit minterms and ALL
    Blake primes are included), see ``cover.cube_array.layer0_include_cex_n6_bridged_12x13``.
    """
    cm = _table_from_strings(
        row_strs=["00010", "00100", "00110", "10000", "10010", "10011", "10100", "10101", "10111"],
        col_strs=["1--00", "001--", "1-0-0", "--10-", "10-11", "-0010", "-01-1", "00-10", "1001-"],
    )
    return cm, 0  # FF_c = 1--00 (free faces 10-00, 11-00)


def audit_out_complex_on_cyclic_cores(
    instances: Sequence[CoveringMatrix],
    variant: OutVariant = "keep_intersection",
    use_reduced: bool = True,
) -> dict[str, int]:
    """Audit one ``Out_complex`` step on the cyclic core of each instance."""
    tested = mismatches = step3 = step4 = 0
    for cm in instances:
        sub, _, _ = reduce_to_cyclic_core(cm.copy())
        if sub.n_rows() == 0:
            continue
        coll = list_collapsible_primes(sub)
        if not coll:
            continue
        col_j = coll[0][0]
        ok, res, _opt = check_h_out(sub, col_j, variant=variant, use_reduced=use_reduced)
        tested += 1
        mismatches += int(not ok)
        step3 += int(res.step_taken == 3)
        step4 += int(res.step_taken == 4)
    return {
        "tested_cyclic_cores": tested,
        "mismatches": mismatches,
        "step3_count": step3,
        "step4_count": step4,
    }
