/-!
# L6 — Cochains, cup product, Leibniz rule over F2 (Loop 4)

Concrete, finite, Mathlib-free.  Cochains on the 3-simplex [0123] with values in F2 (= `Bool`,
addition = `xor`).  Cup product of 1-cochains: `(α ∪ β)(i j k) = α(ij) · β(jk)`.

Proved by exhaustive evaluation (`decide`) over all values of the edge variables that occur
(the Python test `test_one_cochain_leibniz_on_a_3_simplex_exhaustively` checks all `2^12` pairs):

* `cup_leibniz`:  `δ(α ∪ β) = δα ∪ β + α ∪ δβ`  on [0123];
* `coboundary_squared_zero`: `δδf = 0` for 0-cochains on a triangle (and each 2-face of [0123]).

**Not formalized here (documented as an open item; no unfinished proofs):** the Lusternik–Schnirelmann cup-length
bound — if X is covered by k subcomplexes on each of which every class of H^{≥1}(X; F2)
restricts to 0, then the cup-length of X is < k.  The Python side (`core/cohomology.py`,
`tests/test_cohomology.py`) *computes* cup-length and checks this bound on the 7-vertex torus
(cup-length 2, so ≥ 3 pieces) and the 2-sphere.  Claim C23 (ledger): tested, not proved.
-/

namespace TopoSpine
namespace Cocycle

abbrev F2 := Bool

/-- `(δα)(i j k) = α(jk) + α(ik) + α(ij)` as an xor of three edge values. -/
def dEdge (ab bc ac : F2) : F2 := bc ^^ ac ^^ ab

/-- Leibniz rule on the 3-simplex [0123] for 1-cochains α, β.  Only the six edge values that
occur are quantified (the other six edge values of each cochain do not enter either side). -/
theorem cup_leibniz :
    ∀ a01 a02 a12 b12 b13 b23 : Bool,
      -- δ(α∪β)(0123) = (α∪β)(123) + (α∪β)(023) + (α∪β)(013) + (α∪β)(012)
      ((a12 && b23) ^^ (a02 && b23) ^^ (a01 && b13) ^^ (a01 && b12)) =
        -- (δα ∪ β)(0123) = (δα)(012) · β(23)   and   (α ∪ δβ)(0123) = α(01) · (δβ)(123)
        (((dEdge a01 a12 a02) && b23) ^^ (a01 && (dEdge b12 b23 b13))) := by
  decide

/-- δδ = 0 on 0-cochains over a triangle [012]. -/
theorem coboundary_squared_zero :
    ∀ f0 f1 f2 : Bool,
      dEdge (f0 ^^ f1) (f1 ^^ f2) (f0 ^^ f2) = false := by
  decide

/-- Cup product of a 0-cochain with a 1-cochain: Leibniz on an edge [01]… on a triangle [012]. -/
theorem cup_leibniz_zero_one :
    ∀ f0 f1 a01 a12 a02 : Bool,
      -- δ(f∪a)(012) = (f∪a)(12) + (f∪a)(02) + (f∪a)(01), (f∪a)(ij) = f(i)·a(ij)
      ((f1 && a12) ^^ (f0 && a02) ^^ (f0 && a01)) =
        -- (δf∪a)(012) + (f∪δa)(012) = (f0+f1)·a(12) + f0·(δa)(012)
        (((f0 ^^ f1) && a12) ^^ (f0 && (dEdge a01 a12 a02))) := by
  decide

#print axioms cup_leibniz

end Cocycle
end TopoSpine
