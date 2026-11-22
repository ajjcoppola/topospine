/-!
# L0 — Finite graded cells and free faces
-/

namespace TopoSpine

structure Cell where
  id : Nat
  dim : Nat
  deriving DecidableEq, Repr

structure CellComplex where
  cells : List Cell
  faces : List (Cell × Cell)
  deriving Repr

def CellComplex.hasFace (K : CellComplex) (f c : Cell) : Bool :=
  K.faces.any (fun p => decide (p.1 == f) && decide (p.2 == c))

def HasFreeFace (K : CellComplex) (tops : List Cell) (c f : Cell) : Bool :=
  K.hasFace f c &&
  (f.dim + 1 == c.dim) &&
  tops.all (fun q => decide (q == c) || !(K.hasFace f q))

def euler (cells : List Cell) : Int :=
  cells.foldl (fun acc c => acc + (if c.dim % 2 == 0 then (1 : Int) else (-1))) 0

def elementaryCollapseCells (tops : List Cell) (c : Cell) : List Cell :=
  tops.filter (fun q => !(q == c))

theorem euler_collapse_pair_cancels (k : Nat) :
    (if k % 2 == 0 then (1 : Int) else (-1)) +
      (if (k + 1) % 2 == 0 then (1 : Int) else (-1)) = 0 := by
  -- k even => contrib +1 + (-1); k odd => -1 + 1
  have h : (k + 1) % 2 = 1 - k % 2 ∨ (k % 2 = 0 ∧ (k + 1) % 2 = 1) ∨ (k % 2 = 1 ∧ (k + 1) % 2 = 0) := by
    omega
  match Nat.mod_two_eq_zero_or_one k with
  | Or.inl hk =>
    have : (k + 1) % 2 = 1 := by omega
    simp [hk, this]
  | Or.inr hk =>
    have : (k + 1) % 2 = 0 := by omega
    simp [hk, this]

end TopoSpine
