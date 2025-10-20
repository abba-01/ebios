/-
  Monotonicity.lean
  Theorem: Operations preserve or increase uncertainty (except compose)
  Part of eBIOS Layer 2: NUProof
-/

import NUCore

namespace NUCore

/-!
  # Monotonicity Theorem

  **Theorem**: For OP ∈ {⊕, ⊗}: u_out ≥ max(u₁, u₂) - ε

  **Meaning**: Uncertainty never decreases without explicit composition

  **Exception**: Compose (⊙) is designed to reduce uncertainty

  **Proof Strategy**:
  - Addition: √(u₁² + u₂²) ≥ max(u₁, u₂) by Pythagorean property
  - Multiplication: More complex, requires case analysis

  **Status**: Skeleton (requires inequality lemmas)
-/

/-- Helper: maximum of two reals -/
def max_real (a b : ℝ) : ℝ := if a ≥ b then a else b

/-- Addition increases or preserves uncertainty -/
theorem add_monotonic (p₁ p₂ : NUPair) :
  (add p₁ p₂).u ≥ max_real p₁.u p₂.u := by
  sorry  -- TODO: √(u₁² + u₂²) ≥ max(u₁, u₂)

/-- Multiplication preserves uncertainty in simple cases -/
theorem multiply_monotonic_simple (p₁ p₂ : NUPair)
  (h₁ : |p₁.n| ≥ 1) (h₂ : |p₂.n| ≥ 1) :
  (multiply p₁ p₂).u ≥ max_real p₁.u p₂.u := by
  sorry  -- TODO: When |n| ≥ 1, cross-term dominates

/-- Compose explicitly reduces uncertainty (anti-monotonic) -/
theorem compose_antimonotonic (p₁ p₂ : NUPair) (h : p₁.u ≠ 0 ∨ p₂.u ≠ 0) :
  (compose p₁ p₂ h).u ≤ max_real p₁.u p₂.u := by
  sorry  -- TODO: Composition is designed to reduce

end NUCore
