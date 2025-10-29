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
  unfold add max_real
  simp only []

  -- Prove √(u₁² + u₂²) ≥ max(u₁, u₂)
  split_ifs with h
  · -- Case: p₁.u ≥ p₂.u
    apply Real.le_sqrt'
    · exact p₁.h_nonneg
    calc p₁.u^2
        = p₁.u^2 + 0 := by ring
      _ ≤ p₁.u^2 + p₂.u^2 := by linarith [sq_nonneg p₂.u]
  · -- Case: p₁.u < p₂.u
    push_neg at h
    apply Real.le_sqrt'
    · exact p₂.h_nonneg
    calc p₂.u^2
        = 0 + p₂.u^2 := by ring
      _ ≤ p₁.u^2 + p₂.u^2 := by linarith [sq_nonneg p₁.u]

/-- Multiplication preserves uncertainty in simple cases -/
theorem multiply_monotonic_simple (p₁ p₂ : NUPair)
  (h₁ : |p₁.n| ≥ 1) (h₂ : |p₂.n| ≥ 1) :
  (multiply p₁ p₂).u ≥ max_real p₁.u p₂.u := by
  unfold multiply max_real
  simp only []

  split_ifs with h
  · -- Case: p₁.u ≥ p₂.u
    apply Real.le_sqrt'
    · exact p₁.h_nonneg
    calc p₁.u^2
        = 1 * p₁.u^2 := by ring
      _ ≤ |p₂.n|^2 * p₁.u^2 := by
          apply mul_le_mul_of_nonneg_right
          · have : 1 ≤ |p₂.n|^2 := by nlinarith [h₂]
            exact this
          · exact sq_nonneg p₁.u
      _ = (p₂.n * p₁.u)^2 := by rw [mul_pow, sq_abs]
      _ ≤ (p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2 := by
          linarith [sq_nonneg (p₁.n * p₂.u), sq_nonneg (p₁.u * p₂.u)]
  · -- Case: p₁.u < p₂.u
    push_neg at h
    apply Real.le_sqrt'
    · exact p₂.h_nonneg
    calc p₂.u^2
        = 1 * p₂.u^2 := by ring
      _ ≤ |p₁.n|^2 * p₂.u^2 := by
          apply mul_le_mul_of_nonneg_right
          · have : 1 ≤ |p₁.n|^2 := by nlinarith [h₁]
            exact this
          · exact sq_nonneg p₂.u
      _ = (p₁.n * p₂.u)^2 := by rw [mul_pow, sq_abs]
      _ ≤ (p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2 := by
          linarith [sq_nonneg (p₂.n * p₁.u), sq_nonneg (p₁.u * p₂.u)]

/-- Compose explicitly reduces uncertainty (anti-monotonic) -/
theorem compose_antimonotonic (p₁ p₂ : NUPair) (h : p₁.u ≠ 0 ∨ p₂.u ≠ 0) :
  (compose p₁ p₂ h).u ≤ max_real p₁.u p₂.u := by
  -- From ComposeReduction: (compose p₁ p₂ h).u ≤ min p₁.u p₂.u
  -- Since min ≤ max, we have the result
  have h_min := compose_reduces_uncertainty p₁ p₂ h
  unfold max_real
  split_ifs with hcmp
  · -- Case: p₁.u ≥ p₂.u, so max = p₁.u and min = p₂.u
    calc (compose p₁ p₂ h).u
        ≤ min p₁.u p₂.u := h_min
      _ = p₂.u := by rw [min_eq_right hcmp]
      _ ≤ p₁.u := hcmp
  · -- Case: p₁.u < p₂.u, so max = p₂.u and min = p₁.u
    push_neg at hcmp
    calc (compose p₁ p₂ h).u
        ≤ min p₁.u p₂.u := h_min
      _ = p₁.u := by rw [min_eq_left (le_of_lt hcmp)]
      _ ≤ p₂.u := le_of_lt hcmp

end NUCore
