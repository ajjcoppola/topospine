# Sherlock Loop 4 — Post-Audit (2026-11-18)

Scope: hardening, shotgun shelling, Lean L3/L6, camera-ready papers.

## Reflect (7 candidate weaknesses)
1. The collapse-branch (C2) "narrowed" claim was only tested on n ≤ 4; the paper called it "rigorously proved".
2. The default PassManager and Tutorial 03 still used deletion-style collapse (9→0 on the 2007 core).
3. Shotgun shelling (C9) was an open claim with no evidence either way.
4. Lean L3 laws were `True` placeholders (vacuous); L6 did not exist.
5. The relative tower's apparent benefit might be only extra pieces; ABC had never been run.
6. The Lean gate test grepped for the string `sorry`, which also fires on prose and misses `sorryAx` from `decide`-style failures.
7. Paper claims drifted from the ledger (Lean status, ABC "not available", Table 1 hand-written).

## Distill
- **A (mathematical honesty):** items 1, 3, 7.
- **B (checker/contract):** items 2, 4, 6.
- **C (baselines):** item 5.

## Evidence / findings
| # | Finding | Action |
|---|---------|--------|
| 1 | **C2 is false as implemented.** n ≤ 3 and all 65 535 n = 4 functions agree with the exact oracle (collapse branch fired on 330); but on 1500 sampled n = 5 instances it fired on 36 and lost on 2 (9 vs 8; 8 vs 7), exhaustive-confirmed. | DontCareSpinePass, BoundedExactCorePass and `spine_min` now certify plain B&B; collapse-branch kept as audited comparator; checker compares against the exhaustive oracle; Paper A theorem restated as a conditional reduction (hypothesis H) and its old proof gap (the include-p case) closed. |
| 2 | Original Theorem 1 proof used "admissibility supplies encode" for a hypothesis the checkable predicate does not imply. Reduction is valid; the predicate-to-(H) step is exactly what fails. | Paper A now separates predicate and (H); remark records this. |
| 3 | **C9 disproved.** 7-column instance: optimum 4, `safe` batch 5. n = 4 over all 864 nontrivial instances: guarded rule 33 mismatches; naive rules 672 mismatches and leave the table infeasible. Naive batching also needed a transitive decode (face may be collapsed again) and a coverability guard. | `cover.shotgun`, audit table, experimental pass with `optimality_claim = False`, checker rejects claims. |
| 4 | L3 replaced by a finite concrete instance (`decide` over 128 chains); L6 Leibniz rule on the 3-simplex by `decide`. First `decide` attempt on L6 failed because unused binders made `Decidable` synthesis fail: fixed by quantifying only occurring edge variables. | `CollapseContraction.lean`, `Cocycle.lean`. Cup-length / LS bound is **not** formalized. |
| 5 | Same-budget ablation: k-center with equal pieces has r_A 1.11/0.38/0.27 vs 0.60/0.27/0.14 (relative) but better global radius; A-nerve Betti agree with own-code Rips at 2/3 levels (same as k-center). ABC (yosys-abc, expanded resyn2): DC spine beats ABC(no DC) on every cascade; ABC on our output is better still. | C20 downgraded: no topological benefit claimed. |
| 6 | The old gate would fail on a comment containing the word; after adding a prose mention it did (caught on first run). | Gate now checks build output for `sorryAx` / "declaration uses 'sorry'" and scans code with comments stripped. |
| 7 | Paper C said ABC unavailable and that the molecular ablation was future work; Paper B said "L0--L5 builds"; Paper A's Loop-1 table had `--` cells with no generator. | Papers A/B/C rewritten; Loop-1 table input removed from Paper A and replaced by the generated shotgun/C2 audit table; all tables now `resizebox` to page width. |

## Known limitations (unchanged or new)
- All applied results are synthetic; MD17 loader exists but was not run; GUDHI not installed.
- n = 5 audit is a 1500-function sample, not exhaustive.
- Per-output synthesis has no cross-output sharing (c17: 8 vs 6); ABC cannot use our DCs.
- `brew install yosys` was executed (side effect: upgraded `readline`).
- Lazy row refinement lemma in Paper A and the suspension-sphere example have no pytest coverage this loop (checklist labels them).

## Gate
| Check | Result |
|-------|--------|
| pytest | 74 passed (66 → 74 over the loop incl. shotgun, cohomology, mode tests) |
| `lake build` (bare) | success; `cup_leibniz` depends on no axioms, `homotopy_identity` only on `propext` |
| Tutorials 01–05 | all exit 0 |
| Papers A/B/C | compile with tectonic, no overfull table boxes |
| Loop 5 | presented in Plan mode for approval only |
