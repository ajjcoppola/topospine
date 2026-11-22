# Sherlock Loop 2 — Post-Audit (2026-11-17)

## Reflect
1. Pass manager over-collapsing (9→0) on 2007 complex — elementary pass removes tops without inserting faces as covering cells (size reduction OK for simple-homotopy; covering semantics need Loop 3 care for ABC/factor graphs).
2. MedMNIST not installed — synthetic voxel CI fallback used (planned).
3. GUDHI/cripser optional — adapter pass correctly no-ops.
4. Lean L2/L3 are schema-level (matching Python gates) rather than full Mathlib chain complexes.
5. Underscore in TeX bench table broke Paper B compile — fixed.

## Distill
1. Pass manager + checkers work; over-collapse is a **semantic contract** issue for covering vs homotopy — document as Loop 3 obligation when wiring ABC don't-care spines.
2. Medical gate met via synthetic 8³ blob (81→49 cells) with verification/size advantage.
3. Spines/towers fail-closed + selected refinement maps verified by tests.

## Evidence
| Check | Result |
|-------|--------|
| pytest | 15 passed |
| lake build L2–L4 | success |
| Tutorial 02/03 | OK |
| medical bench | `benchmarks/results/medical_loop2.json` |
| Paper B PDF | `papers/B-certified-synthesis/main.pdf` |

## Suggestions (Loop 3)
- Mishchenko ABC / AIG factor-diagram passes with don't-care spines
- Bio circuit + MD17/22 molecular relative spines
- Tighten elementary collapse to optional face-insertion mode for covering IR
- Expand Lean L2/L3 toward Mathlib HomologicalComplex when ready

## Cleanup
No temporary diagnostic probes.

## Gate
Stop for Loop 3 plan approval.
