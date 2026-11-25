# Tutorial 05 — Modes, shotgun shelling, cup-length

**Runner:** `python tutorials/run_tutorial_05.py` (a few seconds, no external data).

## 1. Homotopy mode vs covering mode

`PassManager.default(mode="homotopy")` deletes cells (simple-homotopy collapse);
`PassManager.covering()` inserts the free face in place of the cell, so column count and
weights are preserved, a `face -> parent` decode map is kept, and the IR can never be
emptied.  The verifier (`verify_pass_trace`) rejects a deletion-style pass or a silent
emptying while `mode == "covering"`.  Covering mode is **vacuous** on the 2007 core and on a
solid voxel blob (no admissible free face): that is a recorded negative result.

## 2. Free-face local transform + Link(opp) window (Paper A sandbox)

**Vocabulary:** Layer 0 vs Layer 1 in `docs/definitions-cube-array.md`. The items
below are **Layer 1** (grid surrogate) unless re-proved for minterm×cube arrays.

**Face rows.** Free face of square `p` ⇒ `p` essential and
`opt = 1 + opt(K/p)` (`star_collapse_face_rows`, Lean `StarLink.lean`, claim C42).

**Vertex rows (far-side).** Replace collapsible square `p` by free face `f`,
solve once, decode `f→p`, then **put-back**. Exact criterion
(`cover.grid2d`, Lean `LocalTransform.lean`):
`opt(P') = opt(P)` iff some optimum excludes `p` or covers the far side
`F_p = (V(p) ∩ R) \ V(f)` without `p`.  Sufficient condition
`|F_p| = |V(f) ∩ R| = 1` fires on 33% of 3×3 pairs with zero failures.

**Vertex rows (Link approx).** `Out_link = Link(opp(f))` with collar `V(opp)`:
`L = MinCov(Out_link)`, `U = cost(Reduced(M ∪ {p}))` satisfy `L ≤ opt ≤ U`
(claim C43). Stitch + window `(L,U)` is an approx-min certificate for downstream
cohomology checkers (C44) — not a free cohomology theorem.

`Out_complex` Boolean path `P_6` collar lock-in remains a **non-core** witness.
One-recursion absolute-min on Layer-0 cyclic cores is **deferred** (C45).

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
