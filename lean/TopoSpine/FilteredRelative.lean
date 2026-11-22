/-!
# L4 — Filtration-grade and relative-pair compatibility
-/

namespace TopoSpine

/-- Grade assignment on cell ids. -/
def Grade := Nat → Nat

/-- Filtration-compatible: face grade ≤ cell grade. -/
def filtrationCompatible (g : Grade) (face cell : Nat) : Prop :=
  g face ≤ g cell

theorem filtration_compatible_trans (g : Grade) (a b c : Nat)
    (h1 : filtrationCompatible g a b) (h2 : filtrationCompatible g b c) :
    filtrationCompatible g a c :=
  Nat.le_trans h1 h2

/-- Relative pair (K, A): collapses must not remove cells of A. -/
def relativeSafe (A : List Nat) (removed : Nat) : Prop :=
  removed ∉ A

theorem relative_safe_of_not_mem (A : List Nat) (removed : Nat)
    (h : removed ∉ A) : relativeSafe A removed := h

#print axioms filtration_compatible_trans

end TopoSpine
