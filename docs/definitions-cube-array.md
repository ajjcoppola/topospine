# Cube-array definitions (Layer 0 vs Layer 1)

**Status:** Layer 0 (with legal expansions) and Layer 1 **approved** (2026-11-23).  
Canonical vocabulary for absolute minimization. Paper A, tutorials, and
counterexample claims must use these senses unless explicitly labeled otherwise.

## Scope note — one problem among several

Absolute minimization of an array of cubes (defined below) is **one** problem in
a broader family that also includes subset-of-given-cubes unate covering,
literal-weighted covering, don't-care / multi-output synthesis, approximate
minimization, and **TopoSpine** compact representations of large point/cube
complexes for TDA. Layer 0 below locks the **absolute cube-array minimization**
problem first so theorems and counterexamples never cross wires.

## Layer 0 — home problem (absolute cube-array minimization)

1. **Input array of cubes** \(C=\{c_1,\ldots,c_k\}\subseteq\{0,1,-\}^n\).  
   The object one starts with: an array of cubes, not an explicit truth table and
   not a pixel drawing.

2. **Implicit ON-set / minterms** \(F = \bigcup_{i=1}^k \mathrm{minterms}(c_i)\).  
   The cover domain. Minterms are **implicit** inside the cubes (far too many to
   list at scale). Incidence is containment: \(t\le p\).

3. **Prime space and covering relation**.  
   To achieve the *absolute* minimum cover of \(F\), candidates are **not**
   restricted to a subset of the raw input array \(C\): cubes in \(C\) may be
   expanded into **prime implicants** \(P(F)\) (explicitly, or **implicitly** in
   cube space when \(|P(F)|\) is too large to materialize). On any active residual
   domain \(R\subseteq F\), columns cover subsets of \(R\) by cube containment.

4. **Absolute minimum**.  
   \[
   \mathrm{opt}(F)=\min\bigl\{|S|:S\subseteq P(F),\ F\subseteq \textstyle\bigcup_{p\in S}\mathrm{minterms}(p)\bigr\}.
   \]
   Absolute minimization = find a smallest possible array of cubes covering the
   implicit minterms \(F\).

5. **Legal expansions and reductions**.  
   - **Legal expansions (cube space, explicit or implicit):** single-cube literal
     dropping (`EXPAND` checked by cube-containment \(c'\subseteq \bigcup C\)
     without listing minterms), absorption (\(a\le b \Rightarrow\) drop \(a\)), and
     consensus (\(a * b\) along a single opposing variable). Iterated consensus +
     absorption yields all primes \(P(F)\) (Blake canonical form); local/implicit
     expansion avoids full prime blow-up at scale.
   - **Legal reductions:** essential-prime extraction (in cube space via cube
     difference \(p \setminus \bigcup_{q\ne p} q \neq \emptyset\), or unique-row
     essentials on an active table), row dominance, column dominance, **zero-loss
     free-face push-down** (\((p\cap R)\setminus f = \emptyset\)), and
     **connected-component partitioning ("blobs")**, iterated to a fixed point.

6. **Cyclic core**.  
   The residual covering problem after legal expansions and legal reductions reach
   a fixed point. By definition it has **no essential primes**, no dominated
   rows/columns, and is partitioned into connected **blobs**. A cyclic core is
   what one *obtains* from an array of cubes via Step 5 — never a partial-minterm
   table that omits minterms of its own cubes, and never an unreduced sketch.

7. **Collapsible prime / free face**.  
   Evaluated **on a cyclic core** (with essentials already forced and charged to
   the cover). A cube \(p\) in the residual complex is collapsible if it has a
   codimension-1 face \(f<p\) not contained in any other surviving cube of the
   core. The **residual far set** of \((p,f)\) is \(F_p(f)=(p\cap R)\setminus f\).

## Layer 1 — geometric sandbox (not Layer 0 unless re-proved)

8. **Grid surrogate** (`python/topospine/cover/grid2d.py`).  
   Filled / hollow / absent unit squares; **vertex-row** or **face-row** covering
   tables. Useful for visual intuition and local-transform probes. Residuals after
   `reduce_to_cyclic_core` on a **vertex** (or face) table are
   **grid-surrogate cores**, not Layer-0 cyclic cores, unless restated and proved
   for Layer-0 cube arrays. (For example, `|F_p|=1 and |f∩R|=1` has 0 failures on
   \(3\times 3\) 2D grids but fails on \(n=5\) Layer-0 hypercube cyclic cores.)

| Do not say | Say instead |
|------------|-------------|
| “minimize over a subset of the raw input cubes” (for absolute min) | “apply legal expansions toward primes \(P(F)\), then minimize” |
| “this table on 9 hand-picked minterms of 5-var cubes is a Layer-0 core” | “partial-domain table (not a Layer-0 cube-array ON-set core)” |
| “this F/H/. drawing is a cyclic core” | “grid-surrogate residual after reduction on the vertex table” |
| “face-row Theorem A proves absolute cube-array min” | “face-row theorem for the face covering table (different row universe)” |

## Layer-0 free-face & blob status (reopened after approval)

1. **Blind 1-recursion (\(\forall\) or \(\exists\) free face) is NOT unconditionally exact on all Layer-0 cyclic cores:**
   - *Swap-only existential counterexample (\(n=5\), \(9\times 9\) Layer-0 prime cyclic core):* unique collapsible prime `0-10-`; \(\mathrm{opt}=4\) (`C_in`), every free-face swap yields `5`.
   - *Include-only (`C_in`) existential counterexample (\(n=6\), \(12\times 13\) Bridged Double-6-Cycle Layer-0 prime cyclic core):* unique collapsible prime `--0000`; \(\mathrm{opt}=6\) (`C_out`), forcing `--0000` in yields `7`.
2. **Exact 1-subproblem / 0-branching Layer-0 reductions (Lean-certified):**
   - **Theorem L0-A (Zero-loss free-face push-down):** when \(F_p(f)=(p\cap R)\setminus f=\emptyset\), pushing \(p\mapsto f\) preserves \(\mathrm{opt}\) identically with zero branching (fires on ~89% of \(n=5,6\) collapsible cyclic cores).
   - **Theorem L0-B (Layer-0 far-side iff):** 1-branch swap \(p\mapsto f\) + put-back preserves \(\mathrm{opt}\) iff some minimum cover excludes \(p\) or covers \(F_p(f)\) without \(p\).
   - **Theorem L0-C (Blob partitioning):** connected components \(B_1\sqcup\cdots\sqcup B_k\) satisfy \(\mathrm{opt}=\sum_i \mathrm{opt}(B_i)\), and iterative free-face push-down breaks bridged cores into smaller blobs while supplying a tight certified upper bound \(U\).

## Pointers

- Layer-0 cube-array ops & solver: `python/topospine/cover/cube_array.py`
- Table reductions: `python/topospine/core/covering.py` (`reduce_to_cyclic_core`)
- Lean Layer-0 certificates: `lean/TopoSpine/Layer0CubeArray.lean`
- Sandbox: `python/topospine/cover/grid2d.py`
- Sherlock logs: `docs/sherlock/SHERLOCK_DEFS_RESET_2026-11-22.md`, `docs/sherlock/SHERLOCK_LAYER0_BLOBS_2026-11-23.md`
- Paper A: §Definitions & §Layer-0 cube-array theorems
- Ledger: C45–C48
