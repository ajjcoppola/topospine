# Sherlock Loop 3 — Post-Audit (2026-11-17)

Scope: ABC factor diagrams, bio circuits, molecular spines.

## Reflect (7 candidate weaknesses)
1. Covering-mode collapse is vacuous on the flagship 2007 core (every free face inadmissible).
2. Loop 1–2 claim "`lake build` succeeds" may be hollow.
3. Don't-care savings are measured against a weak baseline (minterm SOP).
4. DCs could be unsound if sampled instead of exact.
5. The relative tower may "win" only because it uses more pieces.
6. ABC was never actually run (binary absent), so the factor-diagram claims are untested against the real baseline.
7. The default `PassManager` / Tutorial 03 still use deletion-style collapse (medical synthetic 33→1).

## Distill
- **A (hollow gate):** item 2 — checked first because it undermines every Lean claim.
- **B (baseline honesty):** items 3 and 5.
- **C (semantic contract):** items 1 and 7.

## Evidence / findings
| # | Finding | Action |
|---|---------|--------|
| 1 | **Confirmed hole.** Bare `lake build` printed "Build completed successfully" while `TraceChecker.lean` (import after a doc comment; `Nat.eq_of_beq_eq_true` mismatch; dead tactic) and `CollapseContraction.lean` (`deriving Repr` on a function field) did **not compile**. Root cause: `lean_lib` without `@[default_target]`. Demonstrated on a temp copy that the repaired lakefile now fails on a broken module. | Fixed both modules; added `@[default_target]`; added `tests/test_lean_build.py`; ledger C22 states Loops 1–2 were wrong. |
| 2 | Covering-mode collapse inserts nothing on the 2007 core (6 of 9 columns have free faces, 12 in all, none admissible); works on disjoint squares. | Recorded as negative result C21, regression test, Paper C §1. |
| 3 | Reported three columns: minterm / same pipeline without DC / with DC. Only the last-vs-middle difference is attributed to don't-cares. Gate savings per node never negative on any benchmark (empirical, not a theorem). | Table caption and ledger C19 wording. |
| 4 | DCs are exact SDCs (exhaustive over 2^6 PI assignments, brute-force re-derivation in a test) and the whole re-synthesized network is re-simulated (0 mismatches over 64 assignments). | Kept; test `test_cascade_sdc_is_exact_not_sampled`. |
| 5 | Relative tower uses 15/31/43 pieces vs 4/13/19 for coverage-only, A-radius 0.60/0.27/0.14 vs 2.33/1.17/0.60. Pure trade-off; no same-budget ablation yet. | Paper C says so; ledger C20 "benefit unproven"; ablation → Loop 4. |
| 6 | ABC not installed: adapter produces a no-op certificate; BLIF export and ABC-output parser are unit-tested only. | Disclosed in abstract, §2, tutorial. |
| 7 | Deletion-style `ElementaryCubicalCollapsePass` still the default in `PassManager`; 9→0 on the 2007 complex persists. Covering-mode is a separate pass/closure, not wired into the manager. | Loop 4 obligation. |
| 8 | MD17 not run: loader needs a local `.npz` (`TOPOSPINE_MD17_NPZ`); no download attempted (100MB+). Synthetic conformations are generated geometry, not MD. | Disclosed; synthetic labelled everywhere. |
| 9 | Lean L3 contraction laws are `True` placeholders (vacuous) — surfaced while fixing the build. | Ledger C16 now says so. |

| Check | Result |
|-------|--------|
| pytest | 44 passed (15 → 44) |
| `lake build` (bare, all modules) | success, no `sorry`; new theorems depend only on `propext` |
| Tutorials 02–04 | OK |
| Paper C | `papers/C-abc-bio-molecular/main.pdf` compiled (tectonic) |
| Bench artifacts | `benchmarks/results/bio_loop3.json`, `molecular_loop3.json` + `.tex` tables |
| Headline numbers (synthetic) | gene toy 83→14→5 gates; cascade-24 467→202→159; cascade-40 seeds 848→328→142 / 845→333→207 / 807→338→135; global mismatches 0 |

## Suggestions (Loop 4)
- Wire covering mode into `PassManager` with an explicit homotopy-vs-covering mode switch; default medical/AIG consumers to covering.
- Same-budget ablation for the relative tower; interleaving proof attempt or drop the claim.
- Real ABC baseline (install `abc`), larger/non-synthetic circuits (ISCAS/EPFL), literal-cost objective.
- Shotgun shelling (C9), Lean L6 cocycle/cup-length, replace L3 `True` placeholders with real statements.
- Paper A/B camera-ready gates; correct any text implying Lean was fully building in Loops 1–2.

## Cleanup
No temporary diagnostic probes left. Temp Lean copies removed.

## Gate
Stop for Loop 4 plan approval.
