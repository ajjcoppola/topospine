# Sherlock Log: Paper E — Horn for TDA Programs + Espresso/ABC

**Date:** 2026-11-24  
**Plan:** Paper E TDA Horn  
**Claims:** C56–C58

## Verdict

H1–H4 / Espresso-Horn are good for TDA **here and now**: Horn covering is
non-vacuous on the $8^3$ blob (Paper B had 0 steps) and on the 2007 core with
$H^*$ preserved. Spine towers carry certified $(L,U)$ windows. Classic Espresso
CLI + ABC-Horn SOP refine connect the same theorems to large two-level practice;
AIG simple-homotopy remains Conjecture E1.

## Delivered

| Item | Status |
|------|--------|
| `PassManager.covering_horn` + GridCube-fast Horn | done |
| Medical bench non-vacuous + 2007 $H^*$ | done |
| `FiltrationCompatibleHornPass` | done |
| SpineTower/SpineMin horn windows | done |
| Classic espresso binary (`third_party/espresso/build`) | done |
| `AbcHornSopRefinePass` + Conjecture E1 text | done |
| `papers/E-tda-horn-programs/` + talk | done |
| C56–C58 ledger | done |

## Gates

- [x] `pytest tests/test_paper_e_tda_horn.py` (+ espresso variants): 14 passed
- [x] medical / spine / classic espresso benches
- [x] `tectonic` Paper E + talk
- [x] `lake build` (reuse RothEspressoHorn; 0 sorry)
