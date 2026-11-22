# Tutorial 04 — ABC factor diagrams, bio circuits, molecular spines

**Runner:** `python tutorials/run_tutorial_04.py` (about 1 s, no external data).

Loop 3 extends the certificate-carrying pass manager from complexes to **logic
circuits** (Mishchenko-style AIG/factor diagrams) and to **relative spines** on
molecular point clouds.

## 1. Covering-mode collapse

`ElementaryCubicalCollapsePass` *deletes* a collapsible top cell; on a covering IR
this can silently empty the IR (a single square collapses to nothing).
`CoveringAwareCollapsePass` instead **inserts the free face in place**:

* guarded by `cover_admissible_free_face` on the typed graded table and by the
  relative subcomplex;
* column count is preserved, the face has lower dimension, weights are preserved;
* a `decode` map `face -> parent` is stored, so a cover of the reduced IR
  transports back (Lean: `TopoSpine/CoveringCollapse.lean`, `replaceCol_ne_nil`,
  `decode_replace`, alias of `transport_optimum`).

It is **fail-closed**: on the 2007 core every free face is inadmissible, so nothing is
inserted (`test_covering_collapse_fail_closed_on_2007_complex`).

## 2. AIG, factor diagram, don't-care spine

`topospine.synth.aig` is a small And-Inverter Graph with structural hashing and
`quick_factor` (algebraic factoring).  `DontCareSpinePass` builds the covering table
with rows = ON minterms and columns = primes of ON ∪ DC (don't-cares can be *used* but
never *must be covered*), solves it with the collapse-branch B&B, and attaches an
exhaustive audit whenever ≤16 columns remain (`ProvenMinimum` for the chosen objective: `cubes`, `literals` or `cubes_then_literals`).
`FactorDiagramRewritePass` factors the SOP and refuses to grow the AIG.
`AbcBaselineAdapterPass` runs Berkeley ABC (`strash` + expanded `resyn2`) as a *baseline only* if
`abc` or `yosys-abc` is on PATH; otherwise it records a no-op certificate.

Every accepted pass is re-checked by `verify_logic_trace`, which evaluates the AIG on
every minterm directly (no minimizer code involved).

## 3. Bio circuits (synthetic)

* `gene_regulation_toy`: 5-gene toy network with satisfiability don't-cares from two
  stated invariants (not a published model).
* `pathway_cascade`: seeded feed-forward cascade; local don't-cares are the **exact**
  unreachable fan-in patterns over all 2^6 primary inputs, so re-synthesis preserves
  every node value (checked exhaustively).

Results: `benchmarks/results/bio_loop3.json`, `bio_benchmark_table.tex`.
Each node also yields a `CoverOptimalityWitness` checked by
`verify_cover_optimality_witness`.

## 4. Molecular relative SpineTower

`build_relative_tower(points, A, ...)` forces an ε-net of the designated subset `A`
(functional group / binding region) at every scale, then covers the rest with a
pruned greedy spine.  Reported per level: cover sizes, A-covering radius, F₂ Betti
numbers of the nerve `N`, the A-nerve `N_A`, and the relative pair `(N, N_A)`.
Data: synthetic 13-atom × 12-conformation cloud by default; MD17/MD22 when
`TOPOSPINE_MD17_NPZ=/path/to/file.npz` is set (no download is attempted).

**Honest limits.** The tower contract is `ApproximatePersistence` /
`TopologicalApproximation` — no interleaving proof.  Don't-care savings are
measured against the same pipeline without don't-cares and against ABC run on the
minterm AIG with don't-cares forced to 0 (ABC cannot use our don't-cares in this flow).
The molecular tower has a same-budget ablation (Tutorial 05 / Paper C): better
A-resolution than k-center at equal size, but no demonstrated topological benefit.
