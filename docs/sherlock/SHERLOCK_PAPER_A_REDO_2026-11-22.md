# Sherlock — Paper A collapse redo (2026-11-22)

Scope: free-face collapse as a local transform on vertex-row 2D grid complexes.

## Reflect
1. Face-row free faces are essentials; vertex-row free faces survive into cores.
2. `restore()` swapped `f→p` without put-back (`Reduced`).
3. Failures concentrate on the far side of `p`.
4. Path / `P_6` pictures still have essentials — not cyclic cores.
5. A checkable sufficient condition may exist short of the full iff.
6. Window profiles are sufficient by construction but may be rare.
7. Boolean n=5 failures may persist after put-back (geometric, not bookkeeping).

## Distill
- **A.** Row-model dichotomy + far-side iff (C38, C39).
- **B.** Put-back is necessary but not sufficient (C40).
- **C.** Loop finds `|F_p|=|V(f)∩R|=1` at 33% / 0 failures (C41).

## Evidence
| # | Finding | Action |
|---|---------|--------|
| 1 | Face rows: 0/4149 cores keep a collapsible square; vertex rows: 6126/9770 | `dichotomy_counts`, Prop dichotomy |
| 2 | Put-back rescues a minority of raw decode failures; n=5 sample still 2/1500 disagreements | `minimize.restore`, Boolean re-audit |
| 3 | `opt(P')=opt(P)` ↔ far-side condition: 0/32288 (3×3); 0/1 013 750 (3×4) | `verify_characterization`, `grid_collapse_char_3x4.json` |
| 4 | Smallest strip cex: 7 cols, opt 3 vs opt(P') 4; Lean `native_decide` | `LocalTransform.lean` |
| 5 | Loop round 1 trivial `F_p=∅` 17.7%/0; round 2 `|F_p|=|V(f)∩R|=1` 33.3%/0 — stop | `grid_collapse_round{1,2}.json` |
| 6 | `P_6` reduces to essentials — labelled non-core in OutComplex / ledger C36 | docs + tests |

## Gate
| Check | Result |
|-------|--------|
| pytest | 102 passed (incl. `test_grid_collapse`, Lean build) |
| `lake build` | LocalTransform + library, no `sorry` |
| Tutorials 01–06 | all exit 0 |
| Paper A + talk | tectonic → `main.pdf` both |

## Round log
- Round 1: `far_empty` — fire 5700/32288 (17.7%), failures 0 (trivial, reported separately).
- Round 2: `far1_face1` — fire 10760/32288 (33.3%), failures 0 → **winner**, stop.
