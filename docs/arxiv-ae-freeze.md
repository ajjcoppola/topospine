# ArXiv Wave 1 freeze — Papers A + E

**Freeze date:** 2026-11-24  
**Tag:** `v0.1.0-arxiv-ae`  
**Primary categories (proposed):** `cs.LO` (A), `cs.CG` / `cs.LO` (E)  
**Secondary:** `math.CO`, `cs.SC` as fit  

## Submission package

| Artifact | Path | Role |
|----------|------|------|
| Paper A PDF | `papers/A-cyclic-core/main.pdf` | Primary |
| Ancillary intuition | `papers/A-cyclic-core/intuition_examples.pdf` | Ancillary with A |
| Optional A talk | `papers/A-cyclic-core/talk/main.pdf` | Optional |
| Paper E PDF | `papers/E-tda-horn-programs/main.pdf` | Companion (same week) |
| Optional E talk | `papers/E-tda-horn-programs/talk/main.pdf` | Optional |

Rebuild (tectonic or latexmk) from `main.tex` before upload. Cross-cite footnotes
say “ID pending”; replace with arXiv IDs after acceptance, then Wave 2.

## Claim-ledger freeze (labels as in PDFs)

| ID | Label in A/E | Status |
|----|--------------|--------|
| C45–C52 | Layer-0 / Roth / Lean companions | as in ledger |
| C53 | Espresso variants + window | established |
| C54 | `sccc` escape (E1 paper-A) | established |
| C55 | Non-vacuous `HornRetractionCollapsePass` | established |
| C56 | Horn medical / 2007 non-vacuous | established (E) |
| C57 | Filtration Horn + spine `(L,U)` | established (E) |
| C58 | Classic Espresso + AbcHornSopRefine | established (E) |
| Conjecture E1 | AIG Forman pairing | **not claimed** |
| Thm TU (A) | Informal TU residue | **PROPOSED** only |
| C21 | Single-face covering vacuity | historical negative; superseded by C56 |

## Frozen benches (committed)

- `benchmarks/results/espresso_horn_bench{,_table.tex}.json`
- `benchmarks/results/horn_chain_audit_table.tex`
- `benchmarks/results/layer0_blob_audit_table.tex`
- `benchmarks/results/medical_benchmark_table.tex`
- `benchmarks/results/spine_horn_bench_table.tex`
- `benchmarks/results/classic_espresso_bench{,_table.tex}.json`

## Gate

```bash
bash scripts/release_gate.sh
```

Grep guard: Paper B must not assert current covering vacuity without
“superseded” / Paper E / C56 language.

## Human arXiv steps (Wave 1)

1. Run release gate green on tagged commit `v0.1.0-arxiv-ae`
   (`https://github.com/ajjcoppola/topospine/releases/tag/v0.1.0-arxiv-ae`).
2. Upload A: `main.pdf` + ancillary `intuition_examples.pdf`.
3. Upload E same week; E cites A; A cites E as program companion.
4. Record IDs in `CITATION.cff`, README Papers section, and this file.
5. Proceed to Wave 2 (`docs/arxiv-wave2.md`).
