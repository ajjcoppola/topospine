import TopoSpine.Basic

/-!
# L1 — Trace checker soundness (boolean free-face gate)
-/

namespace TopoSpine

/-- Accepted elementary-collapse trace. -/
structure CollapseTrace where
  complex : CellComplex
  tops : List Cell
  cell : Cell
  freeFace : Cell
  deriving Repr

def CollapseTrace.valid (t : CollapseTrace) : Bool :=
  HasFreeFace t.complex t.tops t.cell t.freeFace

def CollapseTrace.topsAfter (t : CollapseTrace) : List Cell :=
  elementaryCollapseCells t.tops t.cell

/-- If the middle beq holds, dimensions match. -/
theorem beq_dim_of_valid_components
    (fdim cdim : Nat) (h : (fdim + 1 == cdim) = true) :
    fdim + 1 = cdim :=
  by simpa using h

/-- Euler contribution of a free-face pair (dims k and k+1) cancels (C0). -/
theorem collapse_pair_euler_zero (k : Nat) :
    (if k % 2 == 0 then (1 : Int) else (-1)) +
      (if (k + 1) % 2 == 0 then (1 : Int) else (-1)) = 0 :=
  euler_collapse_pair_cancels k

/-- Valid traces remove the collapsed top cell. -/
theorem topsAfter_removes_cell (t : CollapseTrace) :
    ¬ (t.cell ∈ t.topsAfter) := by
  simp [CollapseTrace.topsAfter, elementaryCollapseCells]

end TopoSpine
