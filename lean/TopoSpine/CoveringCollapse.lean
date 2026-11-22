import TopoSpine.OptimalityTransport

/-!
# L5' — Covering-mode collapse (face insertion) and transport

Loop 3.  `CoveringAwareCollapsePass` (Python) replaces a column `c` of the covering IR by a
free face `f` *in place* and records a decode map `f ↦ c`.  This file proves the
IR-level facts the Python regression tests rely on:

* `replaceCol_length`      — the number of columns is preserved;
* `replaceCol_ne_nil`      — a nonempty covering IR is never emptied;
* `decode_replace`         — decoding the inserted face recovers the original IR
                             (when the face is fresh);
* `covering_collapse_transport` — optimality transport (alias of `transport_optimum`)
                             to be instantiated with `encode := replace`, `decode := decode`
                             once `CoverAdmissibleFreeFace` supplies the four inequalities.

Schema-level: the cover feasibility/cost inequalities are *not* proved here; they remain
the admissibility hypothesis checked by the Python auditor (claim C17).
-/

namespace TopoSpine

/-- Replace column id `c` by `f` at the same position. -/
def replaceCol (c f : Nat) (xs : List Nat) : List Nat :=
  xs.map (fun x => if x = c then f else x)

/-- Decode map: send the inserted face `f` back to its parent column `c`. -/
def decodeCol (c f : Nat) (xs : List Nat) : List Nat :=
  xs.map (fun x => if x = f then c else x)

theorem replaceCol_length (c f : Nat) (xs : List Nat) :
    (replaceCol c f xs).length = xs.length := by
  simp [replaceCol]

theorem replaceCol_ne_nil (c f : Nat) {xs : List Nat} (h : xs ≠ []) :
    replaceCol c f xs ≠ [] := by
  intro hx
  apply h
  have hl := replaceCol_length c f xs
  rw [hx] at hl
  exact List.length_eq_zero.mp hl.symm

theorem decode_replace (c f : Nat) :
    ∀ xs : List Nat, f ∉ xs → decodeCol c f (replaceCol c f xs) = xs := by
  intro xs
  induction xs with
  | nil => intro _; rfl
  | cons a t ih =>
    intro h
    have hfa : f ≠ a := fun e => h (by simp [e])
    have hft : f ∉ t := fun e => h (List.mem_cons_of_mem _ e)
    have iht := ih hft
    by_cases hac : a = c
    · simp [replaceCol, decodeCol, hac] at *
      exact iht
    · have hfa' : ¬ a = f := fun e => hfa e.symm
      simp [replaceCol, decodeCol, hac, hfa'] at *
      exact iht

/-- Covering-mode collapse transports optimality: a named alias (a `def` of the proof term)
of `transport_optimum`. -/
def covering_collapse_transport := @transport_optimum

end TopoSpine
