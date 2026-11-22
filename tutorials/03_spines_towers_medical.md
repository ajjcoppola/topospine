# Tutorial 03 — Spines, towers, and medical voxels

**Runner:** `python tutorials/run_tutorial_03.py`

## Spines

`spine_min` builds an approximate cover (contract **Coverage**, not ProvenMinimum).
Collapsible column filtering is **fail-closed** — empty oracle raises.

## Towers

`build_cover_tower` uses **selected-spine** refinement maps $U_{i+1}\to U_i$
(not all landmarks). Certificate: `ApproximatePersistence` with declared
interleaving constant.

## Medical voxels

Synthetic $8^3$ blob → `voxel_grid_complex` → `PassManager` reduction.
MedMNIST attempted if installed; CI uses synthetic fallback.
See `benchmarks/results/medical_loop2.json`.
