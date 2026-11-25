# One-recursion absolute-min — reopened & resolved on Layer 0 (2026-11-23)

**Status:** Layer 0 (with legal expansions) and Layer 1 approved in
`docs/definitions-cube-array.md`. Reopened on genuine Layer-0 cube-array cyclic
cores (`python/topospine/cover/cube_array.py`, `lean/TopoSpine/Layer0CubeArray.lean`).

## Resolution summary

1. **No blind 1-recursion rule (even picking the *best* free face \(\exists (p,f)\)) works on all Layer-0 cyclic cores:**
   - **Swap-only fails at \(n=5\)** (`layer0_swap_cex_n5_9x9`): 17 implicit ON-minterms, 13 primes \(\to\) 4 essentials removed \(\to\) \(9\times 9\) core with unique collapsible prime `0-10-`; \(\mathrm{opt}=4\) via `C_in`, swap gives `5`.
   - **Include-only (`C_in`) fails at \(n=6\)** (`layer0_include_cex_n6_bridged_12x13`): two antipodal 6-cycles bridged by `--0000` with corners `000000, 110000` stripped by essentials `00000-, 11000-` \(\to\) \(12\times 13\) core with unique collapsible prime `--0000`; \(\mathrm{opt}=6\) via `C_out`, `C_in` gives `7`.
   - *(Correction to older C37 witness:* `cyclic_core_exclude_win_n5` omitted 8 of its cubes' 17 minterms; on its true cube-array ON-set, 5 primes are essential and the Layer-0 cyclic core is empty `0×0`.)

2. **What *does* hold with 0 branching / 1 subproblem (and powers a faster exact solver):**
   - **Zero-loss dead-opposite push-down (`F_p(f) = ∅`):** exact, zero branching, fires on ~89% of \(n=5,6\) collapsible cyclic cores.
   - **Layer-0 far-side iff:** exact criterion for 1-branch swap on minterm×prime cores (`0` mismatches; refutes grid `|F_p|=1 & |f∩R|=1` at \(n=5\)).
   - **Blob partitioning + iterative free-face push-down:** connected components solve additively (\(\mathrm{opt}=\sum\mathrm{opt}(B_i)\)), and iteratively pushing down free faces severs bridges (splitting the \(12\times 13\) witness into two \(6\times 6\) blobs) and yields a tight primal upper bound `U` that prunes exact B&B in `minimize_cube_array`.
