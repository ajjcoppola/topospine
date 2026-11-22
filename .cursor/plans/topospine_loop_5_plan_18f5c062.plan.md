---
name: TopoSpine Loop 5 Plan
overview: "Loop 5 takes TopoSpine to LLM-embedding point clouds and quantum-style operators (Hodge/Dirac Laplacians, qubit-count reduction), reusing the Loop 4 discipline: same-budget baselines first, honest negative results, every claim labelled. Presented for approval only; nothing has been started."
todos:
  - id: loop5-embedding-spines
    content: Embeddings loader (npz + synthetic), relative-tower ablation with k-center/greedy/random baselines and retrieval-recall metric, bench table, Tutorial 06
    status: in_progress
  - id: loop5-laplacian-quantum
    content: core/laplacian.py (real Hodge Laplacians, real Betti), collapse-preserves-kernel tests incl. RP2 torsion case, qubit-count resource module, real-Betti check in verify_pass_trace
    status: pending
  - id: loop5-open-items
    content: Sufficient-condition search for (H), larger n=5 audit with CI, multi-output cover sharing vs ABC, pytest for suspension sphere and lazy refinement
    status: pending
  - id: loop5-papers-ledger-sherlock
    content: Ledger C29+, Paper D draft and checklist, Sherlock Loop 5 log + session log mirror + plan copies, full tests/tutorials, Plan mode Loop 6 proposal
    status: pending
isProject: false
---

# TopoSpine Factory Loop 5: Embedding Spines and Quantum Operators

Status of Loop 4 (done): 74 pytest pass, bare `lake build` green, Tutorials 01-05 run, Papers A/B/C compile, Sherlock Loop 4 logged. This plan is for approval only.

## Lessons carried in (design rules for Loop 5)
- Every new benefit claim is measured against a same-budget baseline from day one (C20 was downgraded for lacking one).
- Certified optimality uses plain B&B; collapse-branch stays a comparator (C2 disproved at n=5).
- Data is synthetic or precomputed unless a real file is supplied; nothing is downloaded silently. GUDHI is absent, so own exact F2 code is the reference.
- No quantum-hardware or quantum-advantage claims. Only classical simulation and resource counts.

## Workstream 1: Embedding spines (LLM point clouds)
- New `python/topospine/embeddings/`: loader for a local `.npz` of embeddings plus labels (env var `TOPOSPINE_EMB_NPZ`, same pattern as `TOPOSPINE_MD17_NPZ`); a seeded synthetic cluster-and-bridge generator as the default; optional `sentence-transformers` path only if already installed.
- Reuse [python/topospine/spines/relative_tower.py](python/topospine/spines/relative_tower.py): A = a labelled subset (one topic/class); metrics are A-radius, F2 Betti of N, N_A and (N, N_A), against k-center (same budget), A-weighted greedy, and a random-landmark baseline.
- Add a downstream metric that does not depend on topology: nearest-neighbour retrieval recall on A after replacing points by their selected centres.
- Deliverable: `benchmarks/run_embedding_bench.py`, table `embedding_ablation_table.tex`, Tutorial 06.

## Workstream 2: Quantum-style operators on spines
- New `python/topospine/core/laplacian.py`: boundary matrices over R, combinatorial Hodge Laplacians, spectrum via numpy; `betti_real` = nullity of each Laplacian.
- Claim to test, not assume: an elementary collapse is a simple-homotopy equivalence, so real Betti numbers and the Laplacian kernel dimension are preserved while the number of cells (hence qubits in a one-qubit-per-cell encoding) drops. Check on torus7, sphere2, voxel blobs and relative pairs; also report spectral gap change (expected to change, so no claim of gap preservation).
- Resource-count module: qubits (cells, and ceil(log2 cells)) and Dirac-operator dimension before and after collapse; compare homotopy-mode reduction against a random-deletion baseline that breaks Betti numbers.
- Extend `verify_pass_trace` with a real-Betti check using the new module. Python only; no new Lean claim.

## Workstream 3: Close Loop 4 open items
- Search for a sufficient checkable condition implying hypothesis (H) of Paper A, using exhaustive n=4 data and the two n=5 counterexamples to refute candidate conditions; record candidates as conjectures with their refutations.
- Larger n=5 audit (e.g. 20k-50k seeded samples, optionally symmetry-reduced) to estimate the C2 failure rate with a confidence interval.
- Cross-output sharing for multi-output logic (c17: 8 vs 6) via shared-prime covering, measured against ABC on the same netlist.
- Add the missing pytest for the suspension-sphere no-free-face statement and the lazy row refinement lemma (checklist flagged both).
- Run MD17 only if the user provides a local `.npz`; otherwise leave labelled as not run.

## Workstream 4: Papers, ledger, Sherlock
- Ledger rows C29 onward: embedding-spine ablation, Laplacian kernel preservation under collapse, qubit-count reduction, (H) conjectures, n=5 failure rate, multi-output sharing.
- Paper D draft (embeddings + operators), tectonic-compiled; update checklist; Papers A-C touched only if a ledger status changes.
- `docs/sherlock/SHERLOCK_LOOP5_<date>.md`, append to `~/proj/modes/sherlock-mode/SESSION_LOG.md`, mirror to `~/proj/history/topospine/sherlock-sessions/`, plan copies in `~/.cursor/plans/` and the workspace `.cursor/plans/`.
- End by switching to Plan mode with a Loop 6 proposal for approval only.

## Completion criteria
- pytest green, including Laplacian-vs-F2 Betti agreement, collapse-preserves-kernel, and embedding-ablation tests; bare `lake build` still green.
- Tutorials 01-06 run; Papers A-D compile; every checklist row labelled.
- Embedding and qubit results reported against same-budget baselines, including negative outcomes.
- Sherlock Loop 5 log written; Loop 6 presented for approval only.

## Risks and assumptions
- Real LLM embeddings need a local file or an installed model; default is synthetic, which limits external claims.
- Dense Laplacians cap complex size (about a few thousand cells); larger cases use scipy sparse eigensolvers or are skipped and disclosed.
- Assumes F2 and real Betti numbers agree on the test complexes (no torsion); test explicitly on RP2 to show where they differ.
- Plan-panel copies of this plan (`~/.cursor/plans/` and workspace `.cursor/plans/`) are written on approval, since Plan mode forbids edits now.