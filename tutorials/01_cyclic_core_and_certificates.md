# Tutorial 01 — Cyclic cores, free faces, and certificates

**Audience:** researchers and students entering TopoSpine  
**Time:** ~20 minutes  
**Runner:** `python tutorials/run_tutorial_01.py`

**Vocabulary:** read [`docs/definitions-cube-array.md`](../docs/definitions-cube-array.md)
first. **Layer 0** = array of cubes covering (implicit) minterms → absolute min →
cyclic core after legal reductions. **Layer 1** = F/H/. grids (`cover.grid2d`) are a
geometric sandbox; their residuals are *grid-surrogate cores*, not Layer-0 cores.

## 1. The story in one breath

Two-level Boolean minimization starts from an **array of cubes** and an ON-set of
**minterms**, builds a **covering table**, and after essentials and dominance hits a
**cyclic core** (Layer 0). If a prime has a **free face** (simple-homotopy),
**collapse-branch** replaces the classical in/out pair of recursive calls by **one**
expanded call — *provided* a checkable admissibility hypothesis holds so that
`encode`/`decode` transport optimality (Lean `transport_optimum`). Grid pictures in
later tutorials are Layer 1 unless re-stated for minterm×cube tables.

## 2. Build a cubical complex and derive $T_C$

Never load a bare adjacency table with `row_cubes=None`. Derive the graded covering
table from the complex so every row is a typed cube:

```python
from topospine.examples.zoo import coppola_2007_graded
cm = coppola_2007_graded()
assert all(rc is not None for rc in cm.row_cubes)
```

## 3. Expand a free face (exact incidence)

```python
from topospine.cover.collapse import list_collapsible_primes, expand_collapse_once
j, faces = list_collapsible_primes(cm)[0]
expanded, p_name, face_name = expand_collapse_once(cm, j, faces[0])
```

Face-column coverage is `row.is_face_of(face)`, **not** a clone of the parent column.

## 4. Run the theorem auditor

```python
from topospine.cover.auditor import audit_collapse_branch
aud = audit_collapse_branch(cm, name="demo", depth_limit=16)
print(aud.as_dict())
```

Compare exhaustive (tiny), standard B&B, and collapse-branch on **cost**, **calls**,
**nodes**, and **wall time**.

## 5. Inspect a JSON certificate

```python
from topospine.checkers import verify_elementary_collapse_trace, verify_cover_optimality_witness
trace = {
  "type": "ElementaryCollapseTrace",
  "cell": p_name,
  "free_face": str(faces[0]),
  "other_top_cells": [c for i,c in enumerate(cm.cols) if i != j],
  "chi_before": 0,
  "chi_after": 0,
}
print(verify_elementary_collapse_trace(trace))
```

Schema: `certificates/schema_v1.json`.

## 6. Why naive free-face intuition needs transport

A codimension-1 face can be free among top cells while its **vertices** are jointly
covered by other primes. Then replacing $p$ by $F(p)$ may not admit a cost-nonincreasing
`encode` of every include-$p$ cover unless **CoverAdmissibleFreeFace** holds.
Lean L5 states the abstract obligations; Python checks the concrete hypothesis.

## 7. Homology sanity (β₁ of a filled triangle is 0)

```python
from topospine.core.homology import betti_numbers_f2
from topospine.examples.zoo import filled_triangle_simplices
assert betti_numbers_f2(filled_triangle_simplices())[1] == 0
```

## 8. Lean pointer

- `lean/TopoSpine/Basic.lean` (L0)
- `lean/TopoSpine/TraceChecker.lean` (L1)
- `lean/TopoSpine/OptimalityTransport.lean` (L5 `transport_optimum`)

## Next

Loop 2: ABC-style pass shell, filtered/relative collapses, medical volumes.
