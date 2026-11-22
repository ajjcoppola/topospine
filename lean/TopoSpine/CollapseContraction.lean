/-!
# L3 — Elementary collapse: concrete chain contraction over F2 (Loop 4)

Replaces the Loop 2 placeholder (`pi_id := True`, which was vacuous).  Chains of the filled
triangle are bitmasks (`Nat`, xor = F2 addition); cells are

  bit 0,1,2 = v0,v1,v2   bit 3,4,5 = e01,e12,e02   bit 6 = t.

The elementary collapse removes the pair (t, e02): `e02` is a free face of `t`.  We define the
boundary `d`, the projection `p : C → D`, the inclusion `i : D → C` (D = chains on cells 0..4,
the 2-simplex with the free pair removed) and the homotopy `h`, and prove by exhaustive
evaluation over all 128 chains (`decide`):

* `d ∘ d = 0`;
* `p ∘ i = id_D`;
* `id + i ∘ p = d ∘ h + h ∘ d`  (F2, so `+ = -`);
* `p` and `i` are chain maps, and `h ∘ i = 0`, `p ∘ h = 0`, `h ∘ h = 0` (side conditions).

This is a *finite concrete instance*, not the general theorem for arbitrary complexes (that
needs Mathlib-style chain complexes and remains open in the ledger, claim C16).
-/

namespace TopoSpine
namespace TriangleCollapse

/-- Boundary of a chain (bitmask over the 7 cells). -/
def d (x : Nat) : Nat :=
  (if x.testBit 3 then 3 else 0) ^^^ (if x.testBit 4 then 6 else 0) ^^^
  (if x.testBit 5 then 5 else 0) ^^^ (if x.testBit 6 then 56 else 0)

/-- Projection onto D (cells 0..4): cancel the `e02` coordinate with `∂t`, drop `t`. -/
def p (x : Nat) : Nat := (x ^^^ (if x.testBit 5 then 56 else 0)) &&& 31

/-- Inclusion D → C.  No correction term is needed: no cell of D has `e02` in its boundary. -/
def i (y : Nat) : Nat := y

/-- Chain homotopy: `e02 ↦ t`. -/
def h (x : Nat) : Nat := if x.testBit 5 then 64 else 0

set_option maxRecDepth 8192

theorem dd_zero : ∀ x, x < 128 → d (d x) = 0 := by decide

theorem p_i : ∀ y, y < 32 → p (i y) = y := by decide

theorem homotopy_identity :
    ∀ x, x < 128 → x ^^^ i (p x) = d (h x) ^^^ h (d x) := by decide

theorem p_chain_map : ∀ x, x < 128 → p (d x) = d (p x) := by decide

theorem i_chain_map : ∀ y, y < 32 → d (i y) = i (d y) := by decide

theorem side_conditions :
    (∀ y, y < 32 → h (i y) = 0) ∧ (∀ x, x < 128 → p (h x) = 0) ∧ (∀ x, x < 128 → h (h x) = 0) := by
  decide

/-- The bundled contraction laws (no `True` fields). -/
structure ContractionLaws where
  dd_zero : ∀ x, x < 128 → d (d x) = 0
  p_i : ∀ y, y < 32 → p (i y) = y
  homotopy : ∀ x, x < 128 → x ^^^ i (p x) = d (h x) ^^^ h (d x)
  p_chain : ∀ x, x < 128 → p (d x) = d (p x)

def triangleLaws : ContractionLaws :=
  ⟨dd_zero, p_i, homotopy_identity, p_chain_map⟩

/-- Sanity: the laws are not vacuous — the free pair really is a pair. -/
theorem free_pair_witness : d 64 = 56 ∧ (d 64).testBit 5 = true ∧ d 32 = 5 := by decide

#print axioms homotopy_identity

end TriangleCollapse
end TopoSpine
