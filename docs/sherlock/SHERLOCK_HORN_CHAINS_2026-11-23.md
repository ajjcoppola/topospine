# Sherlock — Horn Retraction, Cylinder/Complement Duality & Collapsible Chains (2026-11-23)

Scope: on genuine Layer-0 cyclic cores from exact logic minimization (grids kept
strictly as intuition/examples, never proofs), investigate and prove constructive
theorems for (1) simple-homotopy horn removal `R_f = {f, f_top}` replacing `f_top`
by `∂f_top \ {f}`, cylinder `× I^m` / cone-prism expansions, and complement
boundary duality; and (2) controlled exact/approx/probabilistic collapsible chains
preserving cohomology and persistent cohomology.

## Step 1 — Reflect (7 candidate mechanisms)
1. **Horn replacement vs old single-face swap:** Whitehead collapse of `R_f = {f, f_top}`
   replaces `f_top` by the **horn** `Λ_f(f_top) = ∂f_top \ {f}`, NOT by `{f}`! For
   `dim(f_top) ≥ 2`, `Λ_f` contains `opp(f)` plus `2(d-1)` side faces whose union covers
   100% of `f_top`; for `dim = 1` on a cyclic core, non-essentiality forces `f ∩ R = ∅`.
2. **Exact Horn IFF:** Because decode maps any nonempty subset of `Λ_f` back to `f_top`,
   `opt(CC_horn) = opt(CC)` should hold whenever `C_out = opt` OR **any** horn face
   `h ∈ Λ_f` has `(f_top ∩ R) \ h` covered without `f_top` — strictly wider than single swap.
3. **Global cross-product `CC × I^m`:** Crossing all cubes with `I^m` lifts primes and
   free faces covariantly; does it change `opt` or leave `opt` invariant?
4. **Ambient cone-prism `E(F) = (F × {0}) ∪ (Q_n × {1})`:** Expands primes `p ↦ p × -`
   into a contractible `(n+1)`-complex whose complement is `F^c × {0}` with roof `Q_n × {1}`
   essential (`opt(E(F)) = 1 + opt(F)`).
5. **Complement boundary duality:** Free faces of `p ∈ P(F)` are boundary faces against
   `F^c = Q_n \ F` — specifically, `f < p` is free iff every external normal reflection
   `f|_{x_j := 1 - p_j}` meets `F^c`! If true, free faces are decidable without generating `P(F)`.
6. **Collapsible chains & persistent cohomology:** Iterated horn collapses `K_0 ↘ … ↘ K_spine`
   should preserve `H*(K; F2)` unconditionally and persistent cohomology Betti curves
   whenever `birth(f) = birth(f_top)`.
7. **Controlled exact / approx / probabilistic chain covering:** Sampling `K` soft-weighted
   collapsible chains with MIS lower bound `L_MIS` should give exponential tail decay toward
   `opt` and certify exact optimality in 0 B&B whenever `U_best = L_MIS`.

## Step 2 — Distill (4 constructive theorems)
- **H1:** Horn Retraction Coverage, Cohomology Invariance, Strict Dominance & Exact Horn IFF.
- **H2:** Cylinder `× I^m` Invariance & Contractible Cone-Prism `1 + opt(F)` Offset.
- **H3:** Complement Boundary Free-Face Duality (`≤ n - dim(p)` queries, zero prime enumeration).
- **H4:** Controlled Collapsible Horn Chains (`exact` / `approx` / `probabilistic`) + Cohomology & Persistent Cohomology Preservation.

## Step 3–4 — Investigation & Evidence

| Theorem / Variant | Result on General Layer-0 Cubical Complexes | Code & Lean Reference |
|-------------------|---------------------------------------------|-----------------------|
| **H1** Horn Retraction `(CC\{f_top}) ∪ (∂f_top\{f})` | **0/2,519** infeasible; **0/2,519** Exact Horn IFF mismatches; **94.3% vs 92.6%** single-step exactness over single-face swap; `5×4` 3-cube witness (`opt=2`, single swap `=3`, horn `=2` via side face `-1-10`) | `cover/horn_chains.py:130`, `HornChains.lean:95` (`horn_beats_single_swap_5x4`) |
| **H2** Cylinder `CC × I^m` & Cone-Prism `E(F)` | `opt(CC × I^m) = opt(CC)` and `H*` preserved; `E(F)` contractible (`β = [1]`) with `opt(E(F)) = 1 + opt(F)` | `cover/horn_chains.py:249`, `HornChains.lean:133` (`cylinder_product_opt_eq`) |
| **H3** Complement Boundary Free-Face Duality | **0/14,682** mismatches on `n=5` + **0** mismatches across all `n=3` Boolean functions (both via `on_cubes` and explicit `off_cubes = complement_cubes(C)`) | `cover/horn_chains.py:290`, `HornChains.lean:162` (`extension_blocked_iff_meets_complement`) |
| **H4** Collapsible Horn Chains (Topology + Solver) | **0/195** `H*(K; F2)` mismatches; **0/195** persistent `H*` mismatches (filtered cells compressed to **52.1%**); `approx` (`K=1`): **82.6%** exact; `probabilistic` (`K=8`): **92.8%** exact & **60.5%** certified optimal in `0` B&B (`U_best = L_MIS`); `exact` mode: **100.0%** exact | `cover/horn_chains.py:345`, `HornChains.lean:180` (`chain_preserves_invariant`, `controlled_chain_window_and_cert`) |

## Step 5–6 — Verification Gates & Cleanup
- `lean/TopoSpine/HornChains.lean`: built in `lake build` (`16/16` targets, zero `sorry`).
- `tests/test_horn_chains.py` + full `pytest` + tutorials `01`–`06` + `tectonic` Paper A/talk: all pass.
- Temporary stdin probes cleaned; reproducible benchmark saved at `benchmarks/run_horn_chain_audit.py`.
