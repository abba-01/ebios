/-
  NonNegativity.lean
  Theorem: All NUCore operations preserve non-negative uncertainty (u ≥ 0)
  Part of eBIOS Layer 2: NUProof
-/

import NUProof.NUCore

namespace NUCore

/-!
  # Non-Negativity Theorem

  **Theorem**: ∀ operations OP ∈ {⊕, ⊗, ⊙, Flip}: u_out ≥ 0

  **Proof Strategy**:
  - Addition: u = √(u₁² + u₂²) ≥ 0 by sqrt_nonneg
  - Multiplication: u = √(...) ≥ 0 by sqrt_nonneg
  - Composition: u = √(...) ≥ 0 by sqrt_nonneg
  - Flip: u' = u, preserved by construction

  **Status**: Skeleton (requires full formalization)
-/

/-- Addition preserves non-negativity (proven by construction) -/
theorem add_nonneg (p₁ p₂ : NUPair) :
  0 ≤ (add p₁ p₂).u := by
  exact (add p₁ p₂).h_nonneg

/-- Multiplication preserves non-negativity (proven by construction) -/
theorem multiply_nonneg (p₁ p₂ : NUPair) :
  0 ≤ (multiply p₁ p₂).u := by
  exact (multiply p₁ p₂).h_nonneg

/-- Composition preserves non-negativity (proven by construction) -/
theorem compose_nonneg (p₁ p₂ : NUPair) (h : p₁.u ≠ 0 ∨ p₂.u ≠ 0) :
  0 ≤ (compose p₁ p₂ h).u := by
  exact (compose p₁ p₂ h).h_nonneg

/-- Flip preserves non-negativity -/
theorem flip_nonneg (p : NUPair) :
  0 ≤ (flip p).u := by
  exact (flip p).h_nonneg

/-- Main non-negativity theorem: all operations preserve u ≥ 0 -/
theorem all_operations_nonneg :
  (∀ p₁ p₂ : NUPair, 0 ≤ (add p₁ p₂).u) ∧
  (∀ p₁ p₂ : NUPair, 0 ≤ (multiply p₁ p₂).u) ∧
  (∀ p₁ p₂ : NUPair, ∀ h, 0 ≤ (compose p₁ p₂ h).u) ∧
  (∀ p : NUPair, 0 ≤ (flip p).u) := by
  constructor
  · exact fun p₁ p₂ => add_nonneg p₁ p₂
  constructor
  · exact fun p₁ p₂ => multiply_nonneg p₁ p₂
  constructor
  · exact fun p₁ p₂ h => compose_nonneg p₁ p₂ h
  · exact fun p => flip_nonneg p

end NUCore
