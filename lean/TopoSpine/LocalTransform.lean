/-!
# Local free-face transform on vertex-row covers

Abstract Lemmas A/B and the far-side characterization of when replacing a
collapsible square `p` by a free face `f` preserves optimum.  Concrete
`decide` check of the smallest 2×3 vertex-row counterexample (hollow ring with
one filled square): `opt = 5` but `opt(P') = 6`.
-/

namespace TopoSpine
namespace LocalTransform

/-- Lemma A: `opt(P') ≤ C_out` via an exclude-`p` encode into the expanded table. -/
theorem lemmaA_opt_exp_le_Cout
    {P Pexp : Type}
    (feasibleP : P → Prop) (feasibleExp : Pexp → Prop)
    (costP : P → Nat) (costExp : Pexp → Nat)
    (encodeOut : P → Pexp)
    (encode_feas : ∀ o, feasibleP o → feasibleExp (encodeOut o))
    (encode_cost : ∀ o, feasibleP o → costExp (encodeOut o) ≤ costP o)
    (bestExp : Pexp)
    (hopt : ∀ r, feasibleExp r → costExp bestExp ≤ costExp r)
    (cOut : P) (hout : feasibleP cOut) :
    costExp bestExp ≤ costP cOut :=
  Nat.le_trans (hopt (encodeOut cOut) (encode_feas cOut hout))
    (encode_cost cOut hout)

/-- Lemma B: decode + put-back is feasible and never raises cost. -/
theorem lemmaB_decode_putback
    {P Pexp : Type}
    (feasibleP : P → Prop) (feasibleExp : Pexp → Prop)
    (costP : P → Nat) (costExp : Pexp → Nat)
    (decode : Pexp → P)
    (decode_feas : ∀ r, feasibleExp r → feasibleP (decode r))
    (decode_cost : ∀ r, feasibleExp r → costP (decode r) ≤ costExp r)
    (bestExp : Pexp) (hfeas : feasibleExp bestExp) :
    feasibleP (decode bestExp) ∧ costP (decode bestExp) ≤ costExp bestExp :=
  ⟨decode_feas bestExp hfeas, decode_cost bestExp hfeas⟩

/-- Sufficiency half of the interface characterization (far-side encode preserves cost). -/
theorem characterization_sufficient
    {P Pexp : Type}
    (feasibleP : P → Prop) (feasibleExp : Pexp → Prop)
    (costP : P → Nat) (costExp : Pexp → Nat)
    (encode : P → Pexp) (decode : Pexp → P)
    (encode_feas : ∀ o, feasibleP o → feasibleExp (encode o))
    (decode_feas : ∀ r, feasibleExp r → feasibleP (decode r))
    (decode_cost : ∀ r, feasibleExp r → costP (decode r) ≤ costExp r)
    (bestExp : Pexp) (hfeas : feasibleExp bestExp)
    (hoptExp : ∀ r, feasibleExp r → costExp bestExp ≤ costExp r)
    (bestP : P) (hfeasP : feasibleP bestP)
    (hoptP : ∀ o, feasibleP o → costP bestP ≤ costP o)
    (h_far : costExp (encode bestP) = costP bestP) :
    costP (decode bestExp) = costP bestP := by
  have h1 : costP (decode bestExp) ≤ costExp bestExp := decode_cost bestExp hfeas
  have h2 : costExp bestExp ≤ costExp (encode bestP) :=
    hoptExp (encode bestP) (encode_feas bestP hfeasP)
  have h4 : costP bestP ≤ costP (decode bestExp) :=
    hoptP (decode bestExp) (decode_feas bestExp hfeas)
  have : costP (decode bestExp) ≤ costP bestP :=
    Nat.le_trans h1 (Nat.le_trans h2 (Nat.le_of_eq h_far))
  exact Nat.le_antisymm this h4

/-! ## Concrete 2×3 counterexample (vertex rows)

Hollow 2×3 ring with one filled square.  Fourteen columns; twelve residual
vertices (`allRows = 4095`).  Column 0 is the filled square `p`; free face
`f` has mask `34`.  Expanded table drops column 0 and appends `f` as bit 13.
-/

def m0 : Nat := 102
def m1 : Nat := 17
def m2 : Nat := 136
def m3 : Nat := 272
def m4 : Nat := 544
def m5 : Nat := 1088
def m6 : Nat := 2176
def m7 : Nat := 3
def m8 : Nat := 12
def m9 : Nat := 48
def m10 : Nat := 192
def m11 : Nat := 768
def m12 : Nat := 1536
def m13 : Nat := 3072
def fMask : Nat := 34
def allRows : Nat := 4095

/-- Coverage of a 14-bit column subset of the original table. -/
def covOf (s : Nat) : Nat :=
  (if s.testBit 0 then m0 else 0) |||
  (if s.testBit 1 then m1 else 0) |||
  (if s.testBit 2 then m2 else 0) |||
  (if s.testBit 3 then m3 else 0) |||
  (if s.testBit 4 then m4 else 0) |||
  (if s.testBit 5 then m5 else 0) |||
  (if s.testBit 6 then m6 else 0) |||
  (if s.testBit 7 then m7 else 0) |||
  (if s.testBit 8 then m8 else 0) |||
  (if s.testBit 9 then m9 else 0) |||
  (if s.testBit 10 then m10 else 0) |||
  (if s.testBit 11 then m11 else 0) |||
  (if s.testBit 12 then m12 else 0) |||
  (if s.testBit 13 then m13 else 0)

/-- Coverage after replacing `p` (bit 0) by the free face (bit 13 of `s`).
Bits 0..12 of `s` select among original columns 1..13. -/
def covExp (s : Nat) : Nat :=
  (if s.testBit 0 then m1 else 0) |||
  (if s.testBit 1 then m2 else 0) |||
  (if s.testBit 2 then m3 else 0) |||
  (if s.testBit 3 then m4 else 0) |||
  (if s.testBit 4 then m5 else 0) |||
  (if s.testBit 5 then m6 else 0) |||
  (if s.testBit 6 then m7 else 0) |||
  (if s.testBit 7 then m8 else 0) |||
  (if s.testBit 8 then m9 else 0) |||
  (if s.testBit 9 then m10 else 0) |||
  (if s.testBit 10 then m11 else 0) |||
  (if s.testBit 11 then m12 else 0) |||
  (if s.testBit 12 then m13 else 0) |||
  (if s.testBit 13 then fMask else 0)

def pop14 (s : Nat) : Nat :=
  (if s.testBit 0 then 1 else 0) +
  (if s.testBit 1 then 1 else 0) +
  (if s.testBit 2 then 1 else 0) +
  (if s.testBit 3 then 1 else 0) +
  (if s.testBit 4 then 1 else 0) +
  (if s.testBit 5 then 1 else 0) +
  (if s.testBit 6 then 1 else 0) +
  (if s.testBit 7 then 1 else 0) +
  (if s.testBit 8 then 1 else 0) +
  (if s.testBit 9 then 1 else 0) +
  (if s.testBit 10 then 1 else 0) +
  (if s.testBit 11 then 1 else 0) +
  (if s.testBit 12 then 1 else 0) +
  (if s.testBit 13 then 1 else 0)

/-- Witness: original optimum uses columns `{0,1,2,11,13}`. -/
def optWitness : Nat := 10247

/-- Witness: expanded cover of cost 6 (bits `{0,4,5,7,10,13}` on the expanded table). -/
def expWitness : Nat := 9393

theorem grid2x3_opt_witness :
    covOf optWitness = allRows ∧ pop14 optWitness = 5 := by
  decide

theorem grid2x3_exp_witness :
    covExp expWitness = allRows ∧ pop14 expWitness = 6 := by
  decide

/-- Exhaustive check: no cover of the original table has cost &lt; 5. -/
theorem grid2x3_opt_minimal :
    ∀ s : Nat, s < 2 ^ 14 → covOf s = allRows → 5 ≤ pop14 s := by
  native_decide

/-- Exhaustive check: no cover of the expanded table has cost &lt; 6. -/
theorem grid2x3_exp_minimal :
    ∀ s : Nat, s < 2 ^ 14 → covExp s = allRows → 6 ≤ pop14 s := by
  native_decide

theorem grid2x3_vertex_counterexample :
    (covOf optWitness = allRows) ∧ (pop14 optWitness = 5) ∧
    (covExp expWitness = allRows) ∧ (pop14 expWitness = 6) ∧
    (∀ s : Nat, s < 2 ^ 14 → covOf s = allRows → 5 ≤ pop14 s) ∧
    (∀ s : Nat, s < 2 ^ 14 → covExp s = allRows → 6 ≤ pop14 s) :=
  ⟨grid2x3_opt_witness.1, grid2x3_opt_witness.2,
   grid2x3_exp_witness.1, grid2x3_exp_witness.2,
   grid2x3_opt_minimal, grid2x3_exp_minimal⟩

#print axioms lemmaA_opt_exp_le_Cout
#print axioms lemmaB_decode_putback
#print axioms characterization_sufficient
#print axioms grid2x3_vertex_counterexample

end LocalTransform
end TopoSpine
