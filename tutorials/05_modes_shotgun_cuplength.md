# Tutorial 05 — Modes, shotgun shelling, cup-length

**Runner:** `python tutorials/run_tutorial_05.py` (a few seconds, no external data).

## 1. Homotopy mode vs covering mode

`PassManager.default(mode="homotopy")` deletes cells (simple-homotopy collapse);
`PassManager.covering()` inserts the free face in place of the cell, so column count and
weights are preserved, a `face -> parent` decode map is kept, and the IR can never be
emptied.  The verifier (`verify_pass_trace`) rejects a deletion-style pass or a silent
emptying while `mode == "covering"`.  Covering mode is **vacuous** on the 2007 core and on a
solid voxel blob (no admissible free face): that is a recorded negative result.

## 2. Collapse-branch is audited, not trusted

The checkable predicate `CoverAdmissibleFreeFace` does *not* imply the transport hypothesis
(H) of Paper A.  Exhaustively: no disagreement with the exact optimum for all n ≤ 4; two
disagreements in 1500 sampled n = 5 instances (costs 9 vs 8 and 8 vs 7).  Hence certified
covers use plain B&B, and the checker compares them against the exhaustive oracle.

The `Out_complex` 4-step formulation (`topospine.cover.out_complex`, Lean `TopoSpine/OutComplex.lean`)
makes the transport barrier concrete without free-face columns:
* with `ReducedCov`, all 198 collapsible `n = 3` Boolean functions agree with the exact optimum;
* on the 6-vertex, 5-edge path `P_6` (`n = 4`), keeping the shared vertex `0000` in `Out_complex`
  causes **collar lock-in** (`{e1, e2, e4, e5}` irredundant of cost 4 vs optimum `{e1, e3, e5}` of cost 3,
  proved by `decide` in `OutComplex.lean`);
* on cyclic cores, dropping all rows of `FF_c` (`= C_in`) succeeds on **all 1,544 `n = 4` cyclic cores**
  (4,368 collapsible columns) and first fails at `n = 5` (cost 5 vs 4).

## 3. Shotgun (simultaneous) shelling is not optimality-preserving (claim C9, disproved)

`topospine.cover.shotgun` applies a *batch* of admissible collapses.  Rules: `none`,
`rows` (row-disjoint) and `safe` (row-disjoint + coverability guard).  A 7-column,
14-row instance has optimum 4 but the `safe` batch rule returns 5.
`ShotgunCoveringCollapsePass` exists as an *experimental* pass whose certificate is
rejected if it claims optimality.  Audit table: `benchmarks/results/shotgun_audit_table.tex`
(`python benchmarks/run_shotgun_audit.py`).

## 4. Cohomology, cup-length and the Lusternik–Schnirelmann bound

`topospine.core.cohomology.CohomologyF2` computes F₂ Betti numbers, the cup product on
simplicial cochains and the cup-length.  For the 7-vertex torus: Betti `[1, 2, 1]`, cup-length 2;
every vertex star is cohomologically trivial and any cover of the torus by such pieces
needs at least `cup_length + 1 = 3` of them.  Status: *tested in Python*; the Leibniz rule on a
3-simplex and the contraction on a triangle are proved in Lean by `decide`
(`TopoSpine/Cocycle.lean`, `TopoSpine/CollapseContraction.lean`); the general LS bound is not formalized.
