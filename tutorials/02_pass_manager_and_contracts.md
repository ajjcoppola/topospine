# Tutorial 02 — Pass manager and preservation contracts

**Runner:** `python tutorials/run_tutorial_02.py`

## Idea

TopoSpine is a **rewrite engine**: each pass proposes a reduction, emits a JSON
certificate, and an independent checker accepts or rejects before commit.

Pipeline: `read → validate → simplify → inspect residual → rewrite → check → export`.

## Contracts

See `docs/mathematical-contracts.md`. Loop 2 passes declare:

| Pass | Contract |
|------|----------|
| ElementaryCubicalCollapse | ElementaryCollapse |
| FiltrationCompatibleCollapse | PersistentEquivalence |
| RelativeCollapse | RelativeEquivalence |
| BoundedExactCore | CoverOptimality |
| FlagEdgeCollapseAdapter | PersistentEquivalence (GUDHI baseline, no mutation) |

## Try it

```python
from topospine.examples.zoo import coppola_2007_boolean_complex
from topospine.synth import PassManager, SynthesisState

cx = coppola_2007_boolean_complex()
state = SynthesisState(complex=cx, grades={str(c): float(c.dimension) for c in cx.top_cells})
out = PassManager.default().run(state)
print(out.size(), len(out.log))
```
