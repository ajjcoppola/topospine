# Sherlock Log: Roth Extremals, Espresso-Horn, Paper A Separation

**Date:** 2026-11-23  
**Plan:** Horn Retraction, Roth Extremals, and Espresso Variants for Paper A and TopoSpine  
**Claims:** C53–C55

## Verdict

Free faces / Horn retraction are ArXiv- and TopoSpine-worthy as the main
exact / bounded-approx / probabilistic extension of Quine–McCluskey and Roth
(1958). Classical Espresso `REDUCE` (`sccc`) stalls on antipodal private points;
Horn splits escape those local minima. Single-face covering collapse remains
vacuous on the 2007 core (C21); `HornRetractionCollapsePass` is not.

## Delivered

| Item | Path / status |
|------|----------------|
| Espresso variants | `python/topospine/cover/espresso_variants.py` (II, Signature, BOOM, ABC ISOP, HiGHS, Horn) |
| Covering pass | `HornRetractionCollapsePass` + `pass_trace` checker + covering manager |
| Lean | `lean/TopoSpine/RothEspressoHorn.lean` (0 sorry; `roth_extremal_hierarchy`, `sccc_stall_escaped_by_horn`, `tightened_lp_mis_window`) |
| Paper A | Rewritten around H1–H4 / E1; grids → `intuition_examples.tex` |
| Talk | Rebuilt Layer-0 Roth → Espresso → Horn story; grid slide = appendix |
| Bench / tests | `benchmarks/run_espresso_horn_bench.py`, `tests/test_espresso_variants.py` |
| Ledger | C53 (variants + window), C54 (`sccc` escape), C55 (non-vacuous horn pass) |

## Gates

- [x] `pytest tests/test_espresso_variants.py` (8 passed)
- [x] `lake build` (incl. `RothEspressoHorn`, 0 sorry)
- [x] tutorials `01`–`06` OK
- [x] `tectonic` on `main.tex`, `intuition_examples.tex`, `talk/main.tex`
- [x] full `pytest` (exit 0)

## Notes

- ABC via `yosys-abc` `read_pla; collapse; sop; write_pla`.
- HiGHS via `scipy.optimize.linprog` / `milp`.
- Intuition companion is Layer-1 only; no Layer-0 absolute claim.
