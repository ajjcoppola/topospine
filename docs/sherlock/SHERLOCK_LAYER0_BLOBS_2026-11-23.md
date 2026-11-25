# Sherlock — Layer-0 Legal Expansions, Free-Face Push-Down & Blobs (2026-11-23)

Scope: reopen Layer-0 absolute cube-array minimization after approving Layer 0
(enhanced with legal cube expansions) and Layer 1 in `docs/definitions-cube-array.md`.

## Step 1 — Reflect
1. Input array of cubes has implicit minterms; absolute minimization requires legal
   expansions toward primes `P(F)` (explicit Blake consensus or implicit EXPAND),
   not subset selection on raw input cubes.
2. Older `cyclic_core_exclude_win_n5` might omit minterms of its own cubes.
3. Maybe existential choice (`∃(p,f)`) rescues blind 1-recursion (`Swap` or `C_in`).
4. Why did `same_row_support` look vacuous in Loop 5 (`run_loop5_audits.py`)?
5. Does grid sufficient condition `|F_p|=1 & |f∩R|=1` survive on `n=5` hypercubes?
6. Iterative free-face push-down could sever bridge cubes into independent **blobs**.
7. Active-variable projection + cube-space `#`/cofactor containment avoids `2^n`
   minterm enumeration completely.

## Step 2 — Distill
- **A.** Audit existential `Swap` and `C_in` on true Blake-prime Layer-0 cyclic cores.
- **B.** Fix `free_faces[0]` blind spot to expose exact zero-loss push-down `F_p(f)=∅`.
- **C.** Build `cube_array.py` + `Layer0CubeArray.lean` combining cube-space legal
  expansions, zero-loss push-down, blob partitioning, and iterative FF blob pruning.

## Step 3–4 — Findings

| # | Finding | Evidence |
|---|---------|----------|
| 1 | `cyclic_core_exclude_win_n5` listed only 9 of its cubes' 17 minterms; on the true ON-set, 5 primes are essential and the Layer-0 core is `0×0` | `test_old_n5_exclude_witness_is_empty_on_full_layer0_onset` |
| 2 | Existential swap-only fails on a genuine `n=5`, `9×9` Blake-prime core (`0-10-` unique collapsible; `opt=4`, all 4 swaps `=5`) | `layer0_swap_cex_n5_9x9`, Lean `layer0_n5_9x9_swap_counterexample` |
| 3 | Existential `C_in`-only holds on all `n≤4` (1544/1544) and 1168 random `n=5` cores, **but fails at `n=6`** on a `12×13` Bridged Double-6-Cycle (`--0000` unique collapsible; `opt=6`, `C_in=7`) | `layer0_include_cex_n6_bridged_12x13`, Lean `layer0_n6_12x13_include_counterexample` |
| 4 | Zero-loss push-down `F_p(f)=∅` (Theorem L0-A) was hidden because `minimize.py` only checked `free_faces[0]` behind `cover_admissible_free_face`; checking all free faces fires on **193/220 (87.7%)** `n=5` collapsible cores with **0 failures** | `zero_loss_free_face_pushdown`, Lean `zero_loss_pushdown_exact` |
| 5 | Layer-0 Far-Side IFF (Theorem L0-B) has **0/2821** mismatches on `n=5` cores; grid `|F_p|=1 & |f∩R|=1` fails on `n=5` hypercube cores (48/412) | `layer0_far_side_holds` |
| 6 | Iterative FF push-down + blob partitioning (Theorem L0-C) splits the `12×13` bridged core into two `6×6` blobs (`0` B&B nodes), empties 30% of `n=5` cores with 0 B&B, and cuts nodes `817→385` (`n=5`), `53→9` (`27×27` 3-blob), while solving `n=32` implicit-minterm arrays in ~22 ms | `minimize_cube_array`, `run_layer0_blob_audit.py` |

## Step 5–6 — Gate & Cleanup
- Ephemeral stdin probes were not written to repo; clean benchmark saved at `benchmarks/run_layer0_blob_audit.py`.
- Full gates (`pytest`, `lake build`, tutorials 01–06, `tectonic` Paper A + talk) verified below.
