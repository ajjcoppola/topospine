# TopoSpine Charter

**Opened:** 2026-11-17  
**Home:** `/Users/ajjc/proj/TopoSpine`

## Mission

Develop **certified, optimized representations** of finite complexes, filtrations,
and relative pairs, connecting logic minimization with scalable topological
computation and applications in biomedical imaging, synthetic biology,
molecular conformations, semantic embeddings, and quantum operators.

## Trust boundaries

1. **Archive** (`archive/`) is immutable provenance. Do not rewrite historical PDFs/HTML.
2. **Executable math** lives in `python/topospine/` with independent checkers in `checkers/`.
3. **Formal math** lives in `lean/TopoSpine/`. Released theorems have zero `sorry`.
4. **Claims** are only “established” when listed in `docs/claim-ledger.md` with
   hypothesis, Python check, counterexample test, Lean decl (if any), and paper section.
5. **Private correspondence** stays in `math-tda/outreach/` and is not public by default.
6. **Authorship** requires consent. Weiss: acknowledgment for 2006–2007. Bala: proposed
   co-author on Paper A TU/neutralization until acceptance.

## Novelty stance

Topology-preserving preprocessing (filtered Morse reductions, persistence-preserving
edge collapses) already exists. TopoSpine’s novelty is **integration and optimization**:
certificate-carrying rewrite passes, cover-optimality transport, and dual cubical /
simplicial / nerve data structures tied to exact and approximate minimization.

## Factory protocol

Each Sherlock Loop produces Theorems + Programs + Examples + Tutorials + Papers,
updates the claim ledger, then **stops for plan approval** before the next loop.
