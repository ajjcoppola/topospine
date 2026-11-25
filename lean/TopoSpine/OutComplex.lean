/-!
# L5b — Out_complex 4-step reduction and the P₆ collar lock-in counterexample

Formalizes the `Out_complex` simplification of collapsible-cube reduction:

1. Remove the collapsible prime `FF_c`, keeping intersection faces in `Out_complex`.
2. Solve `M = MinCov(Out_complex)`.
3. If `M` already covers `FF_c`, return `M`.
4. Otherwise return `ReducedCov(M ∪ {FF_c})`.

What is proved here (no external axioms beyond Lean's kernel):

* `out_collapse_feasible`: feasibility holds unconditionally whenever `M` covers the
  rows outside `FF_c` and `ReducedCov` preserves coverage.
* `step3_optimal_from_in_bound`: because every exclude-`FF_c` cover is automatically
  feasible on `Out_complex` (`R_out ⊆ R`), Step 3 needs *only* the comparison against
  covers that include `FF_c`.
* `out_collapse_optimal`: full 4-step optimality under `H_out`.
* `path6_collar_lockin`: machine-checked (`decide`) counterexample on the 6-vertex,
  5-edge Boolean path `P₆` (`1000 — 0000 — 0010 — 0011 — 0111 — 0101`), proving that
  keeping the intersection vertex `0000` in `Out_complex` allows a minimum cover `M`
  of `Out_complex` (cost 3) for which `M ∪ {FF_c}` is *irredundant* of cost 4 while
  the global minimum cover has cost 3.
-/

namespace TopoSpine
namespace OutComplex

/-- The 4-step `Out_complex` decision rule. -/
def outCollapse {Cover : Type}
    (coversFF : Cover → Bool) (addFFReduced : Cover → Cover) (M : Cover) : Cover :=
  if coversFF M then M else addFFReduced M

/-- Feasibility of the 4-step rule holds without any optimality hypothesis. -/
theorem out_collapse_feasible {Cover : Type}
    (feasible : Cover → Prop)
    (coversFF : Cover → Bool) (addFFReduced : Cover → Cover) (M : Cover)
    (h_step3 : coversFF M = true → feasible M)
    (h_step4 : coversFF M = false → feasible (addFFReduced M)) :
    feasible (outCollapse coversFF addFFReduced M) := by
  unfold outCollapse
  cases h : coversFF M with
  | true => simpa [h] using h_step3 h
  | false => simpa [h] using h_step4 h

/-- In Step 3 (`coversFF M = true`), the exclude-`FF_c` bound is free from `R_out ⊆ R`;
only the comparison against covers that use `FF_c` is needed. -/
theorem step3_optimal_from_in_bound {Cover : Type}
    (feasible outFeasible usesFF : Cover → Prop)
    (cost : Cover → Nat)
    (M : Cover)
    (hM_feas : feasible M)
    (hM_opt_out : ∀ c, outFeasible c → cost M ≤ cost c)
    (h_out_relax : ∀ c, feasible c → ¬ usesFF c → outFeasible c)
    (h_vs_in : ∀ c, feasible c → usesFF c → cost M ≤ cost c)
    (h_dec : ∀ c, usesFF c ∨ ¬ usesFF c) :
    feasible M ∧ ∀ c, feasible c → cost M ≤ cost c := by
  refine ⟨hM_feas, ?_⟩
  intro c hc
  cases h_dec c with
  | inl hin => exact h_vs_in c hc hin
  | inr hout => exact hM_opt_out c (h_out_relax c hc hout)

/-- Full 4-step optimality under `Out_complex` transport `(H_out)`. -/
theorem out_collapse_optimal {Cover : Type}
    (feasible : Cover → Prop)
    (cost : Cover → Nat)
    (coversFF : Cover → Bool) (addFFReduced : Cover → Cover) (M : Cover)
    (h_step3_feas : coversFF M = true → feasible M)
    (h_step4_feas : coversFF M = false → feasible (addFFReduced M))
    (h_step3_cost : coversFF M = true → ∀ c, feasible c → cost M ≤ cost c)
    (h_step4_cost : coversFF M = false → ∀ c, feasible c → cost (addFFReduced M) ≤ cost c) :
    feasible (outCollapse coversFF addFFReduced M) ∧
      ∀ c, feasible c → cost (outCollapse coversFF addFFReduced M) ≤ cost c := by
  unfold outCollapse
  cases h : coversFF M with
  | true =>
    simpa [h] using ⟨h_step3_feas h, h_step3_cost h⟩
  | false =>
    simpa [h] using ⟨h_step4_feas h, h_step4_cost h⟩

/-! ## Concrete counterexample: 6-vertex path `P₆` (collar lock-in)

**Not a cyclic core** for the free-face / vertex-row local-transform question
(the path still has essential edges).  Retained as a Boolean `Out_complex`
witness only.

Vertices `v0..v5` (`1000, 0000, 0010, 0011, 0111, 0101`), bitmask `63 = 0b111111`.
Edges `e0..e4` (`-000, 00-0, 001-, 0-11, 01-1`):
* `e0` (`FF_c`, bit 0) covers `{v0, v1}` = `3`
* `e1` (bit 1) covers `{v1, v2}` = `6`
* `e2` (bit 2) covers `{v2, v3}` = `12`
* `e3` (bit 3) covers `{v3, v4}` = `24`
* `e4` (bit 4) covers `{v4, v5}` = `48`

`Out_complex` drops `e0` (`s &&& 1 = 0`) and drops only the exclusive free vertex `v0`,
keeping the shared intersection vertex `v1 = 0000`: `outRows = 62 = 0b111110`.
-/

/-- Rows covered by an edge subset `s` (5-bit mask). -/
def covMask (s : Nat) : Nat :=
  (if s.testBit 0 then 3 else 0) |||
  (if s.testBit 1 then 6 else 0) |||
  (if s.testBit 2 then 12 else 0) |||
  (if s.testBit 3 then 24 else 0) |||
  (if s.testBit 4 then 48 else 0)

/-- Unit-weight cost (number of selected edges among `e0..e4`). -/
def pop5 (s : Nat) : Nat :=
  (if s.testBit 0 then 1 else 0) +
  (if s.testBit 1 then 1 else 0) +
  (if s.testBit 2 then 1 else 0) +
  (if s.testBit 3 then 1 else 0) +
  (if s.testBit 4 then 1 else 0)

def allRows : Nat := 63
def outRows : Nat := 62
def mBad : Nat := 26       -- {e1, e3, e4} = 0b11010, cost 3 on Out_complex
def step4Ans : Nat := 27   -- {e0, e1, e3, e4} = 0b11011, irredundant of cost 4
def optCov : Nat := 21     -- {e0, e2, e4} = 0b10101, global minimum of cost 3

/-- Every part of the `P₆` collar lock-in phenomenon is verified exhaustively. -/
theorem path6_collar_lockin :
    -- 1. mBad avoids FF_c (e0), covers Out_complex, and has minimum cost 3 on Out_complex
    (mBad &&& 1 = 0) ∧
    (covMask mBad &&& outRows = outRows) ∧
    (pop5 mBad = 3) ∧
    (∀ s, s < 32 → s &&& 1 = 0 → covMask s &&& outRows = outRows → 3 ≤ pop5 s) ∧
    -- 2. mBad does NOT cover FF_c, so Step 4 fires
    (covMask mBad ≠ allRows) ∧
    -- 3. Adding FF_c yields step4Ans of cost 4, and dropping ANY chosen edge breaks coverage
    (mBad ||| 1 = step4Ans) ∧
    (covMask step4Ans = allRows) ∧
    (pop5 step4Ans = 4) ∧
    (∀ i, i < 5 → step4Ans.testBit i = true → covMask (step4Ans ^^^ (1 <<< i)) ≠ allRows) ∧
    -- 4. Yet the true minimum cover optCov covers all 6 vertices with cost 3 < 4
    (covMask optCov = allRows) ∧
    (pop5 optCov = 3) := by
  decide

#print axioms out_collapse_optimal
#print axioms path6_collar_lockin

end OutComplex
end TopoSpine
