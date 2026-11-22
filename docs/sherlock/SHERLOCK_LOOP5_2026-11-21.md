# Sherlock Loop 5 — Post-Audit (2026-11-21)

Scope: GUDHI as a real baseline, MD17 ethanol, a MiniLM cloud, embedding spines, real Laplacians, collapse-branch filters, c17 sharing.

## Reflect
1. GUDHI was only an import flag; `betti_numbers()` without `persistence_dim_max` drops the top dimension, so a pure cycle looks acyclic.
2. The stock elementary pass deletes a top cell. That is not the pair collapse whose kernel is invariant.
3. Forcing an A-net can look like a win on radius and a loss on any task that wanted neighbours together.
4. "k ≥ 3 has no free face" might describe the geometry and not the k = 4 code.
5. The cofactor lemma might be about sets of minterms, while the matrix uses containment.
6. A 1 500-draw at n = 5 is a thin estimate of the failure rate.
7. Per-output c17 at 8 gates might share if the two covers sit in one AIG.

## Distill
- **A.** Items 3, 4, 5: claims that are true in one encoding and false in another.
- **B.** Items 1 and 2: the checker and the baseline have to compute the object they name.
- **C.** Items 6 and 7: measure them.

## Evidence
| # | Finding | Action |
|---|---------|--------|
| 1 | With `persistence_dim_max=True` and field 2, GUDHI matches `rips_betti_f2` on the 12-cycle at three radii, on both embedding clouds, and on 12 ethanol frames. | `gudhi_baseline.py`. `FlagEdgeCollapseAdapter` runs `collapse_edges` and still does not mutate. On one Rips graph the edge count fell 86→30 and the static flag Betti numbers changed. |
| 2 | Pair collapse of a Boolean square: 9 cells → 7, real Betti (1, 0) either way, L0 gap 2 → 0.586. Deleting one edge of the 6-cycle: Betti (1, 1) → (1, 0). RP2 is (1, 0, 0) over R and (1, 1, 1) over F2. | `core/laplacian.py`, `PairCollapsePass`, checker recomputes. The stock deletion pass is unchanged and is not certified for Betti. |
| 3 | Relative A-radius is smaller than k-center on the blobs (0 vs ~0.40), the 24 MiniLM sentences (0 vs ~1.22), and 12 ethanol frames (0.34/0.15/0 vs 0.68/0.53/0.34). NN co-membership recall goes the other way (0 vs 0.83 and 1.0; ethanol 0.29 vs 0.56 at the coarse scale). | Reported as a trade. Figures in `benchmarks/results/figures/`. |
| 4 | `suspension_sphere(3)` has no collapsible column. `suspension_sphere(4)` does. | Test, Paper A example, ledger C33. |
| 5 | Containment-row with weights 3, 1, 1 costs 3; the two cofactor rows cost 2. The minterm ON-set cost is 1 either way. | Ledger C34. The paper lemma is the set reading. |
| 6 | 40 000 n = 5 ON-sets, seed 21: 856 collapses, 42 disagreements with plain B&B. Rate 0.00105, Wilson 95% [0.00078, 0.00142]. Given that the branch fired, 0.049, interval [0.037, 0.066]. Not re-checked exhaustively. | `run_loop5_audits.py`. |
| 7 | Filters on 4 000 of those: same row support, vertex face, edge parent never fire. "At most one row" fires and disagrees. | C32. |
| 8 | c17: per-output sum 8, shared factored AIG 6, ABC on the NAND netlist 6. One circuit. | C19 updated. |

## Data and install
- `pip install gudhi` (3.13.0) into the `sr` conda env. That env already had sentence-transformers 5.1.0 and a cached MiniLM.
- `data/md17_ethanol.npz` is the sGDML file (219 MB, 555 092 × 9 × 3, atoms C,C,O,H×6). Gitignored. Twelve frames used. `A` is the four atoms farthest from the centroid of frame 0, a proxy, not a functional group.
- `data/embeddings_minilm_tiny.npz` (35 KB, 24 sentences) is committed.

## Gate
| Check | Result |
|-------|--------|
| pytest | 89 passed |
| Tutorials 01–06 | all exit 0 |
| Papers A and D | tectonic; Paper D after escaping underscores and a caption brace |
| Loop 6 | presented in Plan mode for approval only |
