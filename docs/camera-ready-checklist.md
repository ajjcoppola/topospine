# Camera-ready checklist (Loop 4, 2026-11-18)

Labels: **PROVED-LEAN** (machine-checked, no unfinished proofs, bare `lake build`), **PROVED-PAPER** (proof on paper, not formalized),
**AUDITED** (checked by exhaustive computation over a stated finite set), **TESTED** (pytest / benchmark evidence, not exhaustive),
**EMPIRICAL-SYNTHETIC** (synthetic data only), **PROPOSED** (not done), **DISPROVED**, **EXTERNAL** (cited, not ours).
Every statement below that is not PROVED-* must stay labelled in the paper text. Ledger IDs refer to `docs/claim-ledger.md`.

## Paper A — Certified Cyclic-Core Transformations

| Statement | Label | Evidence | Ledger |
|-----------|-------|----------|--------|
| Elementary free-face collapse preserves Euler characteristic | PROVED-PAPER + TESTED | `checkers.collapse_trace`, L1 schema | C0 |
| Layer-0 glossary + legal expansions (array of cubes → primes → cyclic core; grids = sandbox) | PROVED-LEAN (monotone lift) + PROVED-PAPER | `docs/definitions-cube-array.md`, `Layer0CubeArray.lean` | C45 |
| Layer-0 existential 1-recursion counterexamples (`9×9` swap-fail, `12×13` include-fail) | PROVED-LEAN (`native_decide`) + TESTED | `cover.cube_array`, `Layer0CubeArray.lean` | C46 |
| Layer-0 zero-loss FF push-down (`F_p(f)=∅`) + Layer-0 Far-Side IFF | PROVED-LEAN + AUDITED (`n=5` sample, 0 fails) | `zero_loss_free_face_pushdown`, `Layer0CubeArray.lean` | C47 |
| Layer-0 blob additivity + cube-space implicit-minterm solver (`minimize_cube_array`) | PROVED-LEAN (blob additivity) + TESTED | `cover.cube_array`, `run_layer0_blob_audit.py` | C48 |
| Horn retraction `(CC\{f_top}) ∪ (∂f_top\{f})` dominance + Exact Horn IFF | PROVED-LEAN (transport + `5×4` 3-cube `native_decide`) + AUDITED (`n=5` sample, 0/2519 IFF mismatches) | `cover.horn_chains`, `HornChains.lean` | C49 |
| Cylinder `× I^m` invariance & cone-prism `1 + opt(F)` offset | PROVED-LEAN + TESTED | `cover.horn_chains`, `HornChains.lean` | C50 |
| Complement boundary free-face duality (`f^(j) ∩ F^c ≠ ∅`) | PROVED-LEAN (mask duality) + AUDITED (`n=3` exhaustive, `n=5` 14682 faces, 0 mismatches) | `is_free_face_via_complement`, `HornChains.lean` | C51 |
| Controlled collapsible horn chains (`exact`/`approx`/`probabilistic`) + persistent cohomology invariance | PROVED-LEAN (chain induction + window cert) + TESTED (`n=5` 195 cores, 0 cohom/persistence mismatches) | `controlled_horn_chain_cover`, `HornChains.lean` | C52 |
| Espresso-family + Espresso-Horn (`L=max(L_MIS,⌈z_LP⌉)`) head-to-head | PROVED-LEAN (LP/MIS window) + TESTED | `espresso_variants.py`, `run_espresso_horn_bench.py`, `RothEspressoHorn.lean` | C53 |
| `sccc`-stall escape by Horn split (E1) | PROVED-LEAN (`native_decide` 5×4) + TESTED | `RothEspressoHorn.sccc_stall_escaped_by_horn` | C54 |
| Non-vacuous `HornRetractionCollapsePass` on 2007 core | PROVED-IR + TESTED (C21 vacuity of single-face pass) | `HornRetractionCollapsePass`, `pass_trace` | C55 |
| Paper A grid intuition separated to companion | DRAFT | `intuition_examples.tex`, rewritten `main.tex` / `talk/main.tex` | — |
| Paper E: Horn covering closes B vacuity on $8^3$/2007 | TESTED | `medical/pipeline`, `test_paper_e_tda_horn.py` | C56 |
| Paper E: SpineTower Horn $(L,U)$ windows | TESTED | `spine_min`/`tower`, `run_spine_horn_bench.py` | C57 |
| Paper E: classic Espresso + AbcHornSopRefine; AIG Morse conjectural | TESTED / CONJECTURED | `classic_espresso_minimize`, `AbcHornSopRefinePass` | C58 |
| Paper E draft + talk | DRAFT | `papers/E-tda-horn-programs/` | — |
| Face-row Theorem A: free face ⇒ essential, `opt=1+opt(K/p)` | PROVED-PAPER + AUDITED + PROVED-LEAN (abstract); **Layer-1 sandbox** | `star_collapse_face_rows`, `StarLink.lean` | C42 |
| Link(opp) bounds `L≤opt≤U` | PROVED-PAPER + AUDITED (3×3) + PROVED-LEAN (abstract window); **Layer-1 sandbox** | `link_out_complex`, `StarLink.lean` | C43 |
| Approx-min certificate interface `(L,U)` | PROVED-PAPER (certificate claim only); sandbox unless re-proved on Layer 0 | Tutorial 05 / paper | C44 |
| Far-side theorem: `opt(P')=opt(P)` iff far side coverable without `p` in some optimum | PROVED-PAPER + AUDITED (3×3: 0/32288; 3×4: 0/1 013 750) + PROVED-LEAN (abstract + 2×3 strip) | `grid2d`, `grid_collapse_char_3x4.json`, `LocalTransform.lean` | C38 |
| Row-model dichotomy (face vs vertex rows) | AUDITED (3×3); sandbox row models | `dichotomy_counts` | C39 |
| Put-back after decode | TESTED + code | `minimize.restore` | C40 |
| Sufficient condition `|F_p|=|V(f)∩R|=1` (≥5% fire, 0 fail) | AUDITED | `grid_collapse_round2.json` | C41 |
| "CoverAdmissibleFreeFace ⇒ far-side / (H)" | **DISPROVED** (n = 5) | `tests/test_shotgun.py::test_c2_*` | C2 |
| Collapse-branch = exact optimum for all n ≤ 4 Boolean instances | AUDITED (255 + 65 535 functions; fired on 330) | `benchmarks/run_shotgun_audit.py` | C2 |
| Collapse-branch fails on 2 of 1500 sampled n = 5 instances | AUDITED (sample; exhaustive oracle) | same | C2 |
| Shotgun shelling preserves optimality | **DISPROVED** (7-column counterexample 4 vs 5; 33/864 mismatches at n = 4 with the guarded rule) | `test_c9_counterexample_*` | C9 |
| Lazy row refinement lemma | PROVED-PAPER for the minterm ON-set (splitting does not change the set). **DISPROVED** as a containment-matrix operation (cost 3 becomes 2) | `tests/test_loop5_open.py` | C34 |
| Suspension sphere has no free face | k = 3 code: TESTED, no collapsible column. k = 4 code is a stand-in that **does** have free faces. The geometric sentence is not the k = 4 complex | `tests/test_loop5_open.py` | C33 |
| Hochster summary | EXTERNAL | Björner / Francisco et al. | — |
| TU residue theorem ("informal") | PROPOSED (with B. Krishnamoorthy); no result claimed | — | C10 |
| 71→57, 431→219 recursive-call wins | TESTED on tiled 2007 cores; not an average-case claim | regression tests | — |
| Lean: LocalTransform lemmas + 2×3 counterexample; abstract transport; L3/L6; OutComplex (P₆ non-core example) | PROVED-LEAN | `lean/TopoSpine/*.lean`, `tests/test_lean_build.py` | C16, C22, C35, C36, C38 |
| `Out_complex` 4-step rule: unconditionally feasible; exact on all 198 collapsible `n = 3` with `ReducedCov`; `P_6` collar lock-in is a **non-core** Boolean witness | PROVED-LEAN + AUDITED | `OutComplex.lean`, `tests/test_out_complex.py` | C35, C36 |
| Cyclic-core collapsible inclusion (`C_in = opt`): holds on all 1,544 `n = 4` cyclic cores (4,368 collapsible columns), **DISPROVED** at `n = 5` (5 vs 4) | AUDITED (`n ≤ 4` exhaustive, `n = 5` witness) | `tests/test_out_complex.py` | C37 |
| Lean: general collapse theorem, (H) from admissibility, TU | not formalized | — | C16 |

## Paper B — Certificate-Carrying Synthesis

| Statement | Label | Evidence | Ledger |
|-----------|-------|----------|--------|
| PassManager commits only checker-accepted transforms | TESTED (+ fail-closed unit tests) | `tests/test_pass_manager.py` | C11 |
| Filtration / relative collapse refusals | TESTED | same | C12, C13 |
| Covering mode never empties the IR; checker rejects deletion-style passes there | TESTED | `tests/test_pass_manager.py` mode tests | C17 |
| Single-face covering vacuous on 2007 / 8³ blob | TESTED (historical negative); **superseded for Horn** by C56 / Paper E | `test_covering_collapse_fail_closed_*`; Horn medical bench | C21 → C56 |
| Homotopy mode 81 → 49 cells on the synthetic blob | EMPIRICAL-SYNTHETIC | `benchmarks/run_medical_bench.py` | — |
| Shotgun pass never claims optimality; checker rejects a claim | TESTED | `tests/test_shotgun.py` | C9 |
| Lean library builds (bare `lake build`) and has no unfinished proofs | PROVED-LEAN gate (test) | `tests/test_lean_build.py` | C22 |
| L3: d² = 0, p∘i = id, id + ip = dh + hd on the filled triangle (128 chains) | PROVED-LEAN (finite instance) | `CollapseContraction.lean` | C16 |
| L6: δ(α∪β) = δα∪β + α∪δβ for F₂ 1-cochains on a 3-simplex | PROVED-LEAN (finite instance) + exhaustive 2¹² Python check | `Cocycle.lean`, `tests/test_cohomology.py` | C23 |
| Cup-length / LS bound on torus (3 pieces) and sphere | TESTED (not formalized) | `tests/test_cohomology.py` | C23 |
| ApproximatePersistence certificate is not ProvenMinimum | PROVED-PAPER (by definition) | `spines.tower` | C15 |

## Paper C — Covering-Aware Collapse, Don't-Care Spines, Relative Towers

| Statement | Label | Evidence | Ledger |
|-----------|-------|----------|--------|
| Prop. 1 list-level invariants of `replace` | PROVED-LEAN | `CoveringCollapse.lean` | C17 |
| DC spine = min #cubes over primes of ON∪DC (≤ 16 columns) | AUDITED (exhaustive oracle per node) | `DontCareSpinePass` certificates | C18 |
| Literal objectives, `.pla`/`.blif` readers | TESTED | `tests/test_logic_io_objectives.py` | C18 |
| Every logic pass is re-checked by direct minterm evaluation | TESTED | `checkers.logic_trace` | C18 |
| Cascade re-synthesis preserves all node values (0 mismatches) | AUDITED (all 2⁶ inputs, generated cascades) | `run_bio_bench.py` | C19 |
| DC spine ≤ no-DC pipeline on gate count; beats ABC-without-DC | EMPIRICAL-SYNTHETIC (not a theorem) | bio table | C19 |
| ABC baseline numbers | EXTERNAL tool, EMPIRICAL-SYNTHETIC; not re-verified | `yosys-abc` | C18 |
| ABC cannot use our DCs; per-output c17 sums to 8. One shared factored AIG has 6, matching ABC and the NAND reference | TESTED, one netlist, hash reuse only | `run_loop5_audits.py` | C19 |
| Literal vs cube objective differs on ≈5 % of random 5-var ISFs | EMPIRICAL | objective ablation | C18 |
| Relative tower: better A-radius than same-budget k-center | EMPIRICAL-SYNTHETIC | ablation table | C20 |
| Relative tower has a topological benefit | **not shown** (downgraded) | ablation table | C20 |
| MD17 ethanol, 12 of 555092 frames | EMPIRICAL (peripheral-atom proxy for A). Full trajectory not towered | `run_prelim_viz.py` | C20, C29 |
| Rips reference via GUDHI 3.13 | TESTED match with own F₂ on circle, embedding clouds, 12 ethanol frames | `gudhi_baseline` | C31 |

## Paper D — Embedding spines and real Laplacians

| Statement | Label | Evidence | Ledger |
|-----------|-------|----------|--------|
| Relative spine has smaller A-radius than same-budget k-center on the three clouds | EMPIRICAL | embedding table, prelim JSON | C29 |
| That improvement preserves nearest-neighbour co-membership | **not shown**; recall drops, often to 0 | same | C29 |
| Real Betti equals F2 Betti on torus7 and sphere2 | TESTED | `tests/test_laplacian.py` | C30 |
| RP2 real [1,0,0] vs F2 [1,1,1] | TESTED | same | C30 |
| Pair collapse preserves real nullity; gap may change; one-edge deletion does not preserve nullity | TESTED | quantum table | C30 |
| One-qubit-per-cell count 9→7 on a square; log encoding 4→3 | TESTED (dimensions only, no device) | `resource_counts` | C30 |
| GUDHI edge collapse preserves static flag Betti | **not always** (86→30 edges, Betti changed) | Tutorial 06 | C31 |
| A usable sufficient filter for (H) | **not found** | audit table | C32 |
| c17 shared AIG has 6 gates | TESTED, one circuit | `loop5_audit.json` | C19 |
| Quantum advantage or hardware execution | not claimed | — | — |

## Gate before submission

- [ ] pytest green and Tutorials 01–06 run.
- [ ] Papers A–D compile (`tectonic main.tex`).
- [ ] No statement labelled PROVED-* lacks a Lean module or an in-text proof.
- [ ] B. Krishnamoorthy co-authorship, R. Weiss acknowledgment and the TU section remain labelled PROPOSED / historical.
- [ ] Disclose that ABC and Yosys were installed during this study (`brew install yosys`, which also upgraded `readline`).
