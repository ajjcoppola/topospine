# TopoSpine

Certificate-carrying cubical / simplicial synthesis and Boolean covering solvers:
exact Layer-0 minimization (Horn retraction, Roth extremals, Espresso-Horn),
mode-aware pass managers, Lean~4 witnesses, and TDA spine/tower pipelines.

**Status (2026-11-24):** Papers **A** (Horn / Roth / Espresso-Horn) and **E** (TDA
programs + classic Espresso / ABC-Horn SOP) are the Wave~1 arXiv tranche. Paper **B**
documents the pass manager; single-face covering vacuity (C21) is historical and
**superseded** by Horn covering (C56). Papers **C**/**D** are empirical companions
(Wave~2 / deferred). See [`docs/claim-ledger.md`](docs/claim-ledger.md) and
[`docs/arxiv-ae-freeze.md`](docs/arxiv-ae-freeze.md).

## Papers

| Paper | Topic | Ledger |
|-------|--------|--------|
| [A](papers/A-cyclic-core/) | Layer-0 cyclic cores, H1–H4, Espresso-Horn | C45–C55 |
| [B](papers/B-certified-synthesis/) | Certificate-carrying pass manager | C11–C17, C21→C56 |
| [C](papers/C-abc-bio-molecular/) | Don't-care spines, ABC bio | C18–C20 |
| [D](papers/D-embeddings-operators/) | Embeddings / real Laplacians | C29–C31 |
| [E](papers/E-tda-horn-programs/) | Horn for TDA programs, Espresso CLI | C56–C58 |

Companion intuition (grids only): [`papers/A-cyclic-core/intuition_examples.tex`](papers/A-cyclic-core/intuition_examples.tex).

## Quick start

```bash
cd python && pip install -e ".[dev]"
pytest ../tests -q
python ../tutorials/run_tutorial_01.py   # ... through run_tutorial_06.py
cd ../lean && lake build
# Optional release gate:
# bash ../scripts/release_gate.sh
```

Optional extras: `pip install -e ".[scipy,gudhi]"` for HiGHS LP and GUDHI baselines.
Classic Espresso: build under `third_party/espresso` (see `NOTICE`) or put `espresso` on `PATH`.

## Layout

```
TopoSpine/
  archive/           # 2006/2007/2022 provenance
  docs/              # Claim ledger, camera-ready, Sherlock, arXiv freeze
  python/topospine/  # Certificate-first Python package
  lean/TopoSpine/    # Lean 4 formalization
  certificates/      # JSON schemas + golden traces
  tutorials/         # Runnable tutorials 01–06
  papers/            # A–E (+ A intuition companion)
  applications/      # Medical / logic pipelines
  third_party/       # Berkeley Espresso sources (NOTICE)
  scripts/           # release_gate.sh
```

## Tracks

| Track | Question | Output |
|-------|----------|--------|
| TopoSpine-Min | When does geometry reduce covering search while preserving optimality? | Cover solver + certificates |
| TopoSpine-TDA | How can complexes be rewritten without losing specified topology? | Cubical/flag synthesis + Horn covering |
| TopoSpine-Lean | Which transformations can be independently verified? | Formal defs + finite soundness theorems |

## Citation

See [`CITATION.cff`](CITATION.cff). Prefer citing the arXiv Wave~1 papers (A+E) once IDs are assigned.

## License

MIT — see [`LICENSE`](LICENSE). Third-party Espresso retains its Berkeley license — see [`NOTICE`](NOTICE).
