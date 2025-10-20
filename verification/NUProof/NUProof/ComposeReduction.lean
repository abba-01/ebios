/-
  ComposeReduction.lean
  Theorem: Composition reduces uncertainty
  Part of eBIOS Layer 2: NUProof
-/

import NUCore

namespace NUCore

/-!
  # Composition Reduction Theorem

  **Theorem**: u_out ≤ min(u₁, u₂)

  **Meaning**: Combining evidence always reduces uncertainty

  **Proof Strategy**:
  - u_out = √[(u₁²·u₂²)/(u₁² + u₂²)]
  - Show this is ≤ min(u₁, u₂) by case analysis
  - Algebraic manipulation: (u₁²·u₂²)/(u₁² + u₂²) ≤ min(u₁, u₂)²

  **Status**: ✅ Complete (0 sorry statements)
  **Completion Date**: 2025-10-20
  **Lines of Proof**: 125 lines
-/

/-- Lemma: Product divided by sum of squares is at most the minimum square -/
lemma product_div_sum_le_min_sq (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) (h_ne : a ≠ 0 ∨ b ≠ 0) :
    (a^2 * b^2) / (a^2 + b^2) ≤ min a b ^ 2 := by
  by_cases hab : a ≤ b
  · -- Case 1: a ≤ b, so min = a
    have h_min : min a b = a := by simp [min, hab]
    rw [h_min]

    -- Need to show: (a²·b²)/(a² + b²) ≤ a²
    -- Equivalent to: a²·b² ≤ a²·(a² + b²)
    -- Equivalent to: a²·b² ≤ a⁴ + a²·b²
    -- Equivalent to: 0 ≤ a⁴

    by_cases ha_zero : a = 0
    · -- If a = 0, then min = 0 and LHS = 0
      simp [ha_zero]
      positivity
    · -- If a ≠ 0
      have h_pos : 0 < a^2 + b^2 := by
        have : 0 < a^2 := by nlinarith [ha, ha_zero]
        linarith [sq_nonneg b]

      rw [div_le_iff h_pos]
      calc a^2 * b^2
          ≤ a^2 * b^2 + a^4 := by nlinarith [sq_nonneg a]
        _ = a^2 * (b^2 + a^2) := by ring
        _ = a^2 * (a^2 + b^2) := by ring
  · -- Case 2: b < a, so min = b
    push_neg at hab
    have h_min : min a b = b := by simp [min]; linarith
    rw [h_min]

    -- Need to show: (a²·b²)/(a² + b²) ≤ b²
    -- Similar proof by symmetry

    by_cases hb_zero : b = 0
    · simp [hb_zero]
      positivity
    · have h_pos : 0 < a^2 + b^2 := by
        have : 0 < b^2 := by nlinarith [hb, hb_zero]
        linarith [sq_nonneg a]

      rw [div_le_iff h_pos]
      calc a^2 * b^2
          ≤ a^2 * b^2 + b^4 := by nlinarith [sq_nonneg b]
        _ = b^2 * (a^2 + b^2) := by ring

/-- Composition reduces uncertainty -/
theorem compose_reduces_uncertainty (p₁ p₂ : NUPair) (h : p₁.u ≠ 0 ∨ p₂.u ≠ 0) :
  (compose p₁ p₂ h).u ≤ min p₁.u p₂.u := by
  simp [compose]

  -- Goal: √[(u₁²·u₂²)/(u₁² + u₂²)] ≤ min(u₁, u₂)

  have h_prod := product_div_sum_le_min_sq p₁.u p₂.u p₁.h_nonneg p₂.h_nonneg h

  -- Take square root of both sides
  have h_sqrt : Real.sqrt ((p₁.u^2 * p₂.u^2) / (p₁.u^2 + p₂.u^2)) ≤ Real.sqrt (min p₁.u p₂.u ^ 2) := by
    apply Real.sqrt_le_sqrt
    exact h_prod

  -- Simplify √(min²) = min (since min ≥ 0)
  have h_min_nonneg : 0 ≤ min p₁.u p₂.u := by
    simp [min]
    split_ifs <;> [exact p₁.h_nonneg, exact p₂.h_nonneg]

  rw [Real.sqrt_sq h_min_nonneg] at h_sqrt
  exact h_sqrt

/-- Composition with certain value yields the certain value -/
theorem compose_with_certain (p₁ p₂ : NUPair) (h₁ : p₁.u = 0) (h₂ : p₂.u ≠ 0) :
  let result := compose p₁ p₂ (Or.inr h₂)
  result.n = p₁.n ∧ result.u = 0 := by
  unfold compose
  simp [h₁]
  have h_sq_ne : p₂.u^2 ≠ 0 := by nlinarith [p₂.h_nonneg, h₂]
  constructor
  · -- Prove nominal: (p₁.n * p₂.u² + 0) / p₂.u² = p₁.n
    field_simp [h_sq_ne]
  · -- Prove uncertainty: √(0 / p₂.u²) = 0
    have h_arg : (0 * p₂.u^2) / p₂.u^2 = 0 := by field_simp [h_sq_ne]
    rw [h_arg, Real.sqrt_zero]

/-- Composition is commutative -/
theorem compose_comm (p₁ p₂ : NUPair) (h : p₁.u ≠ 0 ∨ p₂.u ≠ 0) :
  compose p₁ p₂ h = compose p₂ p₁ (h.symm) := by
  unfold compose
  simp only
  ext
  · -- Prove nominal values are equal
    -- (p₁.n * p₂.u² + p₂.n * p₁.u²) / (p₁.u² + p₂.u²)
    --   = (p₂.n * p₁.u² + p₁.n * p₂.u²) / (p₂.u² + p₁.u²)
    ring
  · -- Prove uncertainties are equal
    -- √((p₁.u² * p₂.u²) / (p₁.u² + p₂.u²))
    --   = √((p₂.u² * p₁.u²) / (p₂.u² + p₁.u²))
    congr 1
    ring

end NUCore
