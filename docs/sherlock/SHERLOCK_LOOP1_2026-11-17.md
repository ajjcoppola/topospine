# Sherlock Loop 1 — Post-Audit (2026-11-17)

## Step 1 — Reflect (sources that drove Loop 1)
1. `row_cubes=None` parent-column clone on free-face expansion
2. Missing encode/decode optimality transport for FreeSize=0 include-$p$ case
3. Truncated Betti / ignored $n_2$ in old `_beta_d`
4. Strict strong-collapse rejecting flag cliques + silent tower fallback
5. Capped TU minors (missed $C_5$ det±2)
6. Lean `True := by trivial` stubs
7. No claim ledger / contract boundary

## Step 2 — Distill (addressed)
1. Typed graded $T_C$ + `CoverAdmissibleFreeFace` (C2 narrowed, C7 established)
2. Exact F₂ homology + weak collapse + full-minor TU (C4–C6)
3. Lean L0/L1/L5 + independent checkers + auditor

## Step 3–4 — Evidence
| Check | Result |
|-------|--------|
| `pytest tests` | 8 passed |
| Tutorial 01 | OK; graded 33×9 typed; β(Δ²)=[1,0,0] |
| C5 TU | `False`, full det = 2 |
| Lean `lake build` | success |
| `#print axioms transport_optimum` | does not depend on any axioms |
| Paper A PDF | `papers/A-cyclic-core/main.pdf` compiled |
| Admissibility hunt (40 of 200 n=3 instances) | 0 cost disagreements in sample |

## Step 5 — Suggestions for Loop 2
- Wire ABC-style pass manager with typed contracts
- Filtration-compatible / relative collapses; Lean L2–L4
- Repair SpineTower refinement maps; MedMNIST/CubicalRipser benches
- Expand counterexample hunt (n=4–5, abstract grid complexes)
- Optional LP Ghouila–Houri backend for larger TU

## Step 6 — Cleanup
No temporary diagnostic probes left in production paths.

## Gate
**Stop for approval of Loop 2 plan.**
