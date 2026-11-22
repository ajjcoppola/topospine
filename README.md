# TopoSpine

Certified, optimized representations of finite cubical and simplicial complexes,
filtrations, relative pairs, and logic/circuit networks — connecting exact Boolean
covering and ABC-style synthesis with scalable homological data structures.

**Status (2026-11-21, Loop 5):** Loop 1 — kernel repairs, collapse-branch auditor,
Paper A. Loop 2 — certificate pass manager, spines/towers, medical synthetic bench,
Paper B. Loop 3 — covering-aware collapse, AIG/factor-diagram IR with don't-care spine
and ABC adapter, synthetic bio circuits, relative molecular towers, Tutorial 04,
Paper C. Loop 4 — hardening: mode-aware pass manager (homotopy vs covering), collapse-branch
shown suboptimal on n = 5 (C2 disproved as implemented), shotgun shelling disproved (C9), real ABC
baseline, same-budget relative-tower ablation, finite Lean instances of the collapse contraction (L3)
and the cup-product Leibniz rule (L6), cohomology/cup-length module, camera-ready checklist
(`docs/camera-ready-checklist.md`). Loop 5 — GUDHI Rips and edge-collapse baselines,
MD17 ethanol (12 frames of `data/md17_ethanol.npz`), a 24-sentence MiniLM cloud,
embedding spines with a nearest-neighbour recall, real Hodge Laplacians
(Paper D). See `docs/claim-ledger.md`. Large trajectories under `data/*.npz`
are not committed; `data/embeddings_minilm_tiny.npz` is.

## Layout

```
TopoSpine/
  archive/           # Immutable 2006/2007/2022 provenance
  docs/              # Charter, contracts, claim ledger, Sherlock logs
  python/topospine/  # Certificate-first Python package
  lean/TopoSpine/    # Lean 4 formalization
  certificates/      # JSON schemas + golden traces
  examples/          # Zoo + biomedical seed
  tutorials/         # Progressive runnable tutorials
  papers/            # A (cyclic core), B (synthesis), C (ABC/bio/molecular)
  applications/      # Domain pipelines (logic, medical, abc, molecular, …)
```

## Quick start

```bash
cd python && pip install -e ".[dev]"
pytest ../tests -q
python ../tutorials/run_tutorial_01.py   # ... through run_tutorial_06.py
cd ../lean && lake build                  # whole library
```

## Tracks

| Track | Question | Output |
|-------|----------|--------|
| TopoSpine-Min | When does geometry reduce covering search while preserving optimality? | Cover solver + certificates |
| TopoSpine-TDA | How can complexes be rewritten without losing specified topology? | Cubical/flag synthesis tools |
| TopoSpine-Lean | Which transformations can be independently verified? | Formal defs + soundness theorems |

Private outreach remains in `math-tda/outreach/` (not migrated).
