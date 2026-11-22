# Mathematical Contracts

Every transformation must declare a **preservation contract**. “Preserves topology”
is too ambiguous for software, proofs, or papers.

## Preservation contracts

| Contract | Required evidence | Does *not* establish |
|----------|-------------------|----------------------|
| **Coverage** | All required elements remain covered | Homology preservation |
| **CoverOptimality** | Valid reconstruction + lower-bound/transport argument | Simple-homotopy equivalence |
| **ElementaryCollapse** | Valid free-face pair and resulting subcomplex | Minimum representation |
| **ChainEquivalence** | Chain maps + chain-homotopy identities ($pi=\mathrm{id}$, $\mathrm{id}-ip=dh+hd$) | Geometric simple-homotopy |
| **PersistentEquivalence** | Filtration-compatible maps and homotopies | Merely matching Betti at sampled scales |
| **RelativeEquivalence** | Maps/homotopies compatible with designated subcomplex | Arbitrary region preservation |
| **ApproximatePersistence** | Explicit interleaving or justified error certificate | Approximation of optimization objective |

Filtration compatibility is essential: independently simplifying two complexes can
destroy their inclusion relationship even when each preserves homology individually.

## Optimality qualifiers

| Label | Meaning |
|-------|---------|
| **Irredundant** | No permitted item can simply be removed |
| **LocallyMinimal** | No allowed local rewrite improves the objective |
| **ProvenMinimum** | Optimal over a precisely specified admissible search space |
| **ObjectiveApproximation** | Proven bound relative to that optimum |
| **TopologicalApproximation** | Proven bound on invariant distortion |

Do **not** advertise a general approximation ratio merely because a heuristic is small.
Optimal Morse matching is NP-hard.

## Cover-optimality transport (Loop 1 focus)

Abstract obligation (Lean `transport_optimum`):

- `encode : Original → Reduced`, `decode : Reduced → Original`
- Feasibility both ways
- `costR(encode o) ≤ costO(o)` and `costO(decode r) ≤ costR(r)`

Concrete specialization for collapse-branch requires a checkable free-face
**admissibility** hypothesis (`CoverAdmissibleFreeFace` / `StronglyFreeRow`) so that
`encode(C_in)` has cost ≤ `cost(C_in)`. See `docs/claim-ledger.md`.
