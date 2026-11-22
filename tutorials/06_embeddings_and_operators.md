# Tutorial 06 — Embedding spines and real Laplacians

**Runner:** `python tutorials/run_tutorial_06.py` (a few seconds, no download).

Pictures from a prelim pass over the local MiniLM sentences, the synthetic
conformation cloud, and 12 frames of MD17 ethanol live in
`benchmarks/results/figures/`.  Regenerate them with
`python benchmarks/run_prelim_viz.py` (the ethanol file is `data/md17_ethanol.npz`;
it is not downloaded by the tutorial).

## 1. Embedding clouds

`synthetic_embedding_cloud` builds labelled Gaussian blobs with bridge points.
`load_embedding_npz` reads `embeddings` and `labels`.  `TOPOSPINE_EMB_NPZ` is
the only switch for an external file.  The checked-in
`data/embeddings_minilm_tiny.npz` is 24 sentences from all-MiniLM-L6-v2.

The relative tower is the same one as the molecular pipeline.  Baselines at the
same budget: k-center, uniform random landmarks, and a coverage-only spine.
`nn_recall_A` is the fraction of designated points whose nearest neighbour in
the designated set falls in the same piece.  A single piece that covers the
whole set scores 1, so recall is not by itself a win.

When GUDHI is installed, its Rips Betti numbers over F2 are compared with
`rips_betti_f2`.  `FlagEdgeCollapseAdapterPass` runs `collapse_edges` on the
cubical 1-skeleton and does not change the complex.

## 2. Real Hodge Laplacians

`simplicial_betti_real` is the nullity of the combinatorial Hodge Laplacian.
On the 7-vertex torus and the tetrahedron boundary it matches the F2 Betti
numbers.  On the 6-vertex RP2 it is `[1, 0, 0]` while F2 is `[1, 1, 1]`
(torsion).  `pair_collapse_cubical` removes a free face and its coface and
keeps the other faces; the real Betti numbers stay put and the chain-space
dimension (the one-qubit-per-cell count, and the Dirac operator's dimension)
drops.  The spectral gap is allowed to change.  Deleting an arbitrary edge of
a 6-cycle changes the Betti numbers: that is the baseline the collapse has to
beat.  Nothing here is a quantum-hardware result.

## 3. What this loop did not rescue

Admissible collapse-branch is still suboptimal on some n=5 covering instances.
`same_row_support` would imply the expanded column is a copy of the parent, but
a proper face never has that support on a minterm table, so the filter never
fires.  `face_covers_at_most_one_row` still accepts the known counterexamples.
Sharing factored AIGs across the two outputs of c17 reduces the summed gate
count and still does not reproduce the 6-NAND netlist.
