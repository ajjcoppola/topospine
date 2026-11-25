# Sherlock — Star absolute + Link(opp) approx (2026-11-22)

Scope: implement Option 3 from the star/link plan — face-row star absolute
(Theorem A) and vertex-row Link(`opp(f)`) Out cost window (Theorem C / C43–C44).

## Reflect
1. Vertex-row one-branch star + always add `p` fails (~10% on 3×3).
2. `min(Outside_⋆∪{p}, C_out)` is exact but identical to classical B&B.
3. Face-row free face ⇒ essential (absolute home for star collapse).
4. Closed-link Out alone is a weaker exact stitch but usable for bounds.
5. Downstream cohomology only needs an admissible approx-min certificate `(L,U)`.
6. Far-side theorem remains the vertex-row absolute characterization.
7. 2×3 ring killed the old free-face swap; Link stitch should give `U=opt`.

## Distill
- **A.** Face-row Theorem A: `opt = 1 + opt(K/p)` (C42).
- **B.** Link Out bounds `L ≤ opt ≤ U` with stitch `Reduced(M∪{p})` (C43).
- **C.** Approx-min certificate interface `(L,U,stitch)` — not a free cohomology theorem (C44).

## Evidence
| # | Finding | Action |
|---|---------|--------|
| 1 | Theorem A: 0 mismatches on free squares of 2×2 / 2×3 / 3×3 | `audit_face_row_theorem_a`, `StarLink.theoremA_essential_offset` |
| 2 | Link bounds: 0 violations on 32288 3×3 pairs; exact stitch ≈96% | `audit_link_bounds`, `StarLink.theoremC_window` |
| 3 | 2×3 ring: `U=opt` for every free face of the fill | `test_2x3_ring_link_stitch_exact` |
| 4 | Paper A §3 dual arc + talk slides (star/link + `(L,U)`) | `main.tex`, `talk/main.tex` |
| 5 | Ledger C42–C44; checklist; Tutorial 05 | docs + tutorials |

## Gate
| Check | Result |
|-------|--------|
| `tests/test_star_link.py` | passed (in full suite) |
| `benchmarks/run_star_link_audit.py` | Thm A 183708/0 on 3×3; Link 32288/0 viol, exact 96.1%, gaps `{0:31016,1:1272}` |
| `lake build` (incl. `StarLink`) | OK, no `sorry` |
| pytest | 106 passed |
| tutorials 01–06 | all exit 0 |
| tectonic Paper A + talk | both wrote `main.pdf` |

## Round log
- Prior probe: `SHERLOCK_STAR_TRANSFORM_2026-11-22.md` (vertex one-branch refuted).
- This round: code geometry (`link_out_complex`, `star_collapse_face_rows`), Lean, paper, ledger.
