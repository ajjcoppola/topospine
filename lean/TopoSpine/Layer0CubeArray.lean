/-!
# Layer-0 Cube-Array Theorems, Blob Partitioning, and Existential Counterexamples

Formalizes the Layer-0 theorems from `docs/definitions-cube-array.md`:

1. **Legal Expansion Monotonicity (`legal_expansion_opt_le`)**: expanding raw input
   cubes into prime implicants covering the same ON-set never increases minimum
   cover cost (`opt(P(F)) ≤ opt(C)`).
2. **Theorem L0-A (`zero_loss_pushdown_exact`)**: when a collapsible prime `p` and
   free face `f < p` have empty residual far set (`(pMask &&& ~~~fMask) = 0`, with
   `fMask` a submask of `pMask`), `fMask = pMask`, so pushing `p ↦ f` leaves every
   subset's coverage **identically unchanged** (0 branching, exact optimum).
3. **Theorem L0-C (`blob_partition_opt_additive`)**: for row- and column-disjoint
   connected components ("blobs") `(B₁, B₂)`, minimum cover cost is strictly
   additive (`opt(B₁ ⊔ B₂) = opt(B₁) + opt(B₂)`).
4. **Existential Layer-0 Counterexamples (`native_decide`)**:
   - `layer0_n5_9x9_swap_counterexample`: `9×9` Layer-0 prime cyclic core with
     unique collapsible prime `0-10-`; `opt = 4` (`C_in`), while swapping `0-10-`
     to **any** of its 4 free faces forces cost `≥ 5`.
   - `layer0_n6_12x13_include_counterexample`: `12×13` Bridged Double-6-Cycle
     Layer-0 prime cyclic core with unique collapsible prime `--0000`; `opt = 6`
     (`C_out`, splitting into two `6×6` blobs of opt `3 + 3`), while forcing
     `--0000` in (`C_in`) forces cost `≥ 7`.
-/

namespace TopoSpine
namespace Layer0CubeArray

/-! ## 1. Legal expansion monotonicity -/

/-- Expanding covers from raw input cubes `CoverRaw` into prime covers `CoverPrime`
via a cost-nonincreasing feasibility-preserving lift witnesses `opt(P(F)) ≤ opt(C)`. -/
theorem legal_expansion_opt_le
    {CoverRaw CoverPrime : Type}
    (feasRaw : CoverRaw → Prop) (feasPrime : CoverPrime → Prop)
    (costRaw : CoverRaw → Nat) (costPrime : CoverPrime → Nat)
    (liftToPrimes : CoverRaw → CoverPrime)
    (lift_feas : ∀ s, feasRaw s → feasPrime (liftToPrimes s))
    (lift_cost : ∀ s, feasRaw s → costPrime (liftToPrimes s) ≤ costRaw s)
    (bestPrime : CoverPrime)
    (hoptPrime : ∀ p, feasPrime p → costPrime bestPrime ≤ costPrime p)
    (bestRaw : CoverRaw) (hfeasRaw : feasRaw bestRaw) :
    costPrime bestPrime ≤ costRaw bestRaw :=
  Nat.le_trans (hoptPrime (liftToPrimes bestRaw) (lift_feas bestRaw hfeasRaw))
    (lift_cost bestRaw hfeasRaw)

/-! ## 2. Theorem L0-A: Zero-loss free-face push-down (`F_p(f) = ∅`) -/

/-- Abstract zero-loss push-down: if `fMask = pMask` (which holds whenever `f ≤ p`
so `fMask ⊆ pMask`, and residual far rows `(p ∩ R) \ f = ∅` so `pMask ⊆ fMask`),
replacing column `p` by `f` leaves coverage and cost of every selection identical. -/
theorem zero_loss_pushdown_cov_eq
    (restCov : Nat → Nat) (pBit : Nat) (pMask fMask : Nat)
    (h_same_support : fMask = pMask) (s : Nat) :
    (restCov s ||| (if s.testBit pBit then fMask else 0)) =
    (restCov s ||| (if s.testBit pBit then pMask else 0)) := by
  rw [h_same_support]

theorem zero_loss_pushdown_exact
    {Sel : Type}
    (covBefore covAfter : Sel → Nat)
    (cost : Sel → Nat)
    (univ : Nat)
    (h_ident : ∀ s, covAfter s = covBefore s)
    (bestAfter : Sel)
    (hfeasAfter : covAfter bestAfter = univ)
    (hoptAfter : ∀ s, covAfter s = univ → cost bestAfter ≤ cost s)
    (bestBefore : Sel)
    (hfeasBefore : covBefore bestBefore = univ)
    (hoptBefore : ∀ s, covBefore s = univ → cost bestBefore ≤ cost s) :
    covBefore bestAfter = univ ∧ cost bestAfter = cost bestBefore := by
  have hfB : covBefore bestAfter = univ := by rw [← h_ident]; exact hfeasAfter
  have hfA : covAfter bestBefore = univ := by rw [h_ident]; exact hfeasBefore
  have hle1 : cost bestAfter ≤ cost bestBefore := hoptAfter bestBefore hfA
  have hle2 : cost bestBefore ≤ cost bestAfter := hoptBefore bestAfter hfB
  exact ⟨hfB, Nat.le_antisymm hle1 hle2⟩

/-! ## 3. Theorem L0-C: Exact blob-partition additivity -/

/-- Abstract additive optimality for two independent covering blobs `(B₁, B₂)`:
when any joint cover projects to feasible covers on `B₁` and `B₂` with superadditive
cost, and any pair of blob covers combines feasibly with additive cost, minimum
cover cost equals `opt(B₁) + opt(B₂)`. -/
theorem blob_partition_opt_additive
    {Joint Blob1 Blob2 : Type}
    (feasJ : Joint → Prop) (feas1 : Blob1 → Prop) (feas2 : Blob2 → Prop)
    (costJ : Joint → Nat) (cost1 : Blob1 → Nat) (cost2 : Blob2 → Nat)
    (proj1 : Joint → Blob1) (proj2 : Joint → Blob2)
    (stitch : Blob1 → Blob2 → Joint)
    (proj_feas : ∀ s, feasJ s → feas1 (proj1 s) ∧ feas2 (proj2 s))
    (proj_cost : ∀ s, feasJ s → cost1 (proj1 s) + cost2 (proj2 s) ≤ costJ s)
    (stitch_feas : ∀ a b, feas1 a → feas2 b → feasJ (stitch a b))
    (stitch_cost : ∀ a b, costJ (stitch a b) = cost1 a + cost2 b)
    (optJ : Joint) (hfJ : feasJ optJ) (hoJ : ∀ s, feasJ s → costJ optJ ≤ costJ s)
    (opt1 : Blob1) (hf1 : feas1 opt1) (ho1 : ∀ a, feas1 a → cost1 opt1 ≤ cost1 a)
    (opt2 : Blob2) (hf2 : feas2 opt2) (ho2 : ∀ b, feas2 b → cost2 opt2 ≤ cost2 b) :
    costJ optJ = cost1 opt1 + cost2 opt2 ∧ feasJ (stitch opt1 opt2) := by
  have hcomb_feas : feasJ (stitch opt1 opt2) := stitch_feas opt1 opt2 hf1 hf2
  have h_upper : costJ optJ ≤ cost1 opt1 + cost2 opt2 := by
    rw [← stitch_cost opt1 opt2]
    exact hoJ (stitch opt1 opt2) hcomb_feas
  have hp := proj_feas optJ hfJ
  have h1 : cost1 opt1 ≤ cost1 (proj1 optJ) := ho1 (proj1 optJ) hp.1
  have h2 : cost2 opt2 ≤ cost2 (proj2 optJ) := ho2 (proj2 optJ) hp.2
  have h_lower : cost1 opt1 + cost2 opt2 ≤ costJ optJ :=
    Nat.le_trans (Nat.add_le_add h1 h2) (proj_cost optJ hfJ)
  exact ⟨Nat.le_antisymm h_upper h_lower, hcomb_feas⟩

/-! ## 4. Witness 1: `9×9` `n=5` Layer-0 Existential Swap Counterexample

Derived from a 13-prime `n=5` Blake expansion after removing 4 essentials.
Unique collapsible prime is column 3 (`0-10-`, mask `11`), whose 4 free faces
have residual masks `3, 8, 1, 10`.  `opt = 4` (`optW1 = 142`), whereas swapping
column 3 for **any** of its 4 free faces raises the minimum cover cost to `5`.
-/

def w1AllRows : Nat := 511

def covW1 (s : Nat) : Nat :=
  (if s.testBit 0 then 34 else 0) |||
  (if s.testBit 1 then 68 else 0) |||
  (if s.testBit 2 then 272 else 0) |||
  (if s.testBit 3 then 11 else 0) |||
  (if s.testBit 4 then 5 else 0) |||
  (if s.testBit 5 then 24 else 0) |||
  (if s.testBit 6 then 384 else 0) |||
  (if s.testBit 7 then 160 else 0) |||
  (if s.testBit 8 then 192 else 0)

/-- Expanded `9`-column table replacing column 3 (`11`) by free-face mask `fm` at bit 8. -/
def covW1Swap (fm s : Nat) : Nat :=
  (if s.testBit 0 then 34 else 0) |||
  (if s.testBit 1 then 68 else 0) |||
  (if s.testBit 2 then 272 else 0) |||
  (if s.testBit 3 then 5 else 0) |||
  (if s.testBit 4 then 24 else 0) |||
  (if s.testBit 5 then 384 else 0) |||
  (if s.testBit 6 then 160 else 0) |||
  (if s.testBit 7 then 192 else 0) |||
  (if s.testBit 8 then fm else 0)

def pop9 (s : Nat) : Nat :=
  (if s.testBit 0 then 1 else 0) +
  (if s.testBit 1 then 1 else 0) +
  (if s.testBit 2 then 1 else 0) +
  (if s.testBit 3 then 1 else 0) +
  (if s.testBit 4 then 1 else 0) +
  (if s.testBit 5 then 1 else 0) +
  (if s.testBit 6 then 1 else 0) +
  (if s.testBit 7 then 1 else 0) +
  (if s.testBit 8 then 1 else 0)

def optW1 : Nat := 142
def expW1 : Nat := 59

theorem layer0_n5_9x9_swap_counterexample :
    covW1 optW1 = w1AllRows ∧ pop9 optW1 = 4 ∧
    (∀ s : Nat, s < 2 ^ 9 → covW1 s = w1AllRows → 4 ≤ pop9 s) ∧
    covW1Swap 3 expW1 = w1AllRows ∧ pop9 expW1 = 5 ∧
    (∀ s : Nat, s < 2 ^ 9 → covW1Swap 3 s = w1AllRows → 5 ≤ pop9 s) ∧
    (∀ s : Nat, s < 2 ^ 9 → covW1Swap 8 s = w1AllRows → 5 ≤ pop9 s) ∧
    (∀ s : Nat, s < 2 ^ 9 → covW1Swap 1 s = w1AllRows → 5 ≤ pop9 s) ∧
    (∀ s : Nat, s < 2 ^ 9 → covW1Swap 10 s = w1AllRows → 5 ≤ pop9 s) := by
  native_decide

/-! ## 5. Witness 2: `12×13` `n=6` Bridged Double-6-Cycle Include Counterexample

Derived from a 15-prime `n=6` Blake expansion after removing essentials
`00000-` and `11000-`.  Column 0 (`--0000`, mask `65`) is the **unique**
collapsible prime, bridging Blob A (rows `0..5`, mask `63`) and Blob B
(rows `6..11`, mask `4032`).
* `opt = 6` (`optW2 = 4810`, excluding column 0).
* Every cover that includes column 0 (`s.testBit 0 = true`) has cost `≥ 7`
  (`inW2 = 2861` attains `7`).
-/

def w2AllRows : Nat := 4095

def covW2 (s : Nat) : Nat :=
  (if s.testBit 0 then 65 else 0) |||
  (if s.testBit 1 then 9 else 0) |||
  (if s.testBit 2 then 36 else 0) |||
  (if s.testBit 3 then 6 else 0) |||
  (if s.testBit 4 then 3 else 0) |||
  (if s.testBit 5 then 24 else 0) |||
  (if s.testBit 6 then 48 else 0) |||
  (if s.testBit 7 then 576 else 0) |||
  (if s.testBit 8 then 2304 else 0) |||
  (if s.testBit 9 then 384 else 0) |||
  (if s.testBit 10 then 192 else 0) |||
  (if s.testBit 11 then 1536 else 0) |||
  (if s.testBit 12 then 3072 else 0)

def pop13 (s : Nat) : Nat :=
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
  (if s.testBit 12 then 1 else 0)

def optW2 : Nat := 4810
def inW2 : Nat := 2861

theorem layer0_n6_12x13_include_counterexample :
    covW2 optW2 = w2AllRows ∧ pop13 optW2 = 6 ∧ optW2.testBit 0 = false ∧
    (∀ s : Nat, s < 2 ^ 13 → covW2 s = w2AllRows → 6 ≤ pop13 s) ∧
    covW2 inW2 = w2AllRows ∧ pop13 inW2 = 7 ∧ inW2.testBit 0 = true ∧
    (∀ s : Nat, s < 2 ^ 13 → s.testBit 0 = true → covW2 s = w2AllRows → 7 ≤ pop13 s) := by
  native_decide

#print axioms legal_expansion_opt_le
#print axioms zero_loss_pushdown_exact
#print axioms blob_partition_opt_additive
#print axioms layer0_n5_9x9_swap_counterexample
#print axioms layer0_n6_12x13_include_counterexample

end Layer0CubeArray
end TopoSpine
