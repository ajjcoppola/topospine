# Sherlock — Cube-array definitions reset (2026-11-22)

Scope: wire-crossing between Alan’s absolute cube-array minimization language and
geometric F/H/. grid / vertex-row surrogates used in recent Paper A audits.

## Reflect
1. “Cyclic core” was applied to unreduced grids and to vertex-row residuals whose
   essentials are vertex-essentials, not minterm-essentials.
2. “Array of cubes” (home problem) was conflated with filled/hollow/absent grids.
3. Absolute min = smallest subarray covering the ON-set; code often minimized a
   different row universe (vertices or faces).
4. Face-row Theorem A is a different covering problem, not cube-array absolute min.
5. Hollow-padding kills geometric vertex-essentials; it is not “reduce a cube array.”
6. One-recursion cex debates fired before Layer-0 definitions were locked.
7. Algorithm boxes (`reduce_to_cyclic_core`) match; row semantics do not.

## Distill
- **A.** Lock Layer 0 glossary: cubes → minterms → legal ops → cyclic core.
- **B.** Demote `grid2d` to Layer 1 sandbox; never call a grid residual a cyclic
  core in Alan’s sense without the *grid-surrogate* label.
- **C.** Defer one-recursion proof/cex until the glossary is signed; then scan
  Boolean/unate cores only.

## Evidence
| # | Finding | Action |
|---|---------|--------|
| 1 | Paper A §defs already define cyclic core via essentials/dominance, but main theorems jumped to vertex-row grids | Lead §defs with Layer 0; sandbox subsection for grids |
| 2 | `grid2d` docstring called vertex-row “the logic-minimization problem” | Retitle as geometric surrogate |
| 3 | FFH/FFF/FFH unreduced had prime essentials; after reduction it is a *grid-surrogate* core, not a Boolean ON-set core | Do not cite as Layer-0 cex |
| 4 | Canonical note needed for shared vocabulary | `docs/definitions-cube-array.md` |

## Gate
| Check | Result |
|-------|--------|
| Glossary + Sherlock log | this session |
| `grid2d` / Paper A / Tutorial 01 hygiene | this session |
| One-recursion reopen | deferred (see glossary “Next question”) |

## Round log
- Trigger: Alan — cyclic core = legal ops on an array of cubes with implicit minterms;
  recent cex debate crossed wires.
- Outcome: definitions reset plan implemented; math reopen only in Layer-0 words.
