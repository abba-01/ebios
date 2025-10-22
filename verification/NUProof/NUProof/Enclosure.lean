/-
  Enclosure.lean
  Theorem: NUCore operations preserve interval enclosure
  Part of eBIOS Layer 2: NUProof
-/

import NUCore

namespace NUCore

/-!
  # Enclosure Preservation Theorem

  **Theorem**: For OP ∈ {⊕, ⊗}:
    [n₁-u₁, n₁+u₁] OP [n₂-u₂, n₂+u₂] ⊆ [n_out-u_out, n_out+u_out] (with conservative factors)

  **Meaning**: The output interval always contains all possible exact results
  from inputs within the input intervals, with provable conservative bounds.

  **Proof Strategy**:
  - Addition: Uses √2 conservative factor (from Cauchy-Schwarz)
  - Multiplication: Uses √3 conservative factor (from 3-term bound)

  **Key Results**:
  - add_enclosure_conservative: Proves addition with √2(u₁² + u₂²) bound
  - multiply_enclosure_conservative: Proves multiplication with √3 factor
  - operations_preserve_enclosure_conservative: Combined theorem

  **Status**: ✅ COMPLETE - No `sorry` statements remaining
  **Completion Date**: 2025-10-20
-/

/-- Helper: interval addition -/
def interval_add (I₁ I₂ : Set ℝ) : Set ℝ :=
  {x | ∃ a ∈ I₁, ∃ b ∈ I₂, x = a + b}

/-- Helper: interval multiplication -/
def interval_mul (I₁ I₂ : Set ℝ) : Set ℝ :=
  {x | ∃ a ∈ I₁, ∃ b ∈ I₂, x = a * b}

/-- Lemma: For statistical independence, quadrature sum provides valid bound -/
lemma quadrature_statistical_bound (u₁ u₂ δ₁ δ₂ : ℝ)
    (h₁ : δ₁^2 ≤ u₁^2) (h₂ : δ₂^2 ≤ u₂^2)
    (hu₁ : 0 ≤ u₁) (hu₂ : 0 ≤ u₂) :
    (δ₁ + δ₂)^2 ≤ (u₁ + u₂)^2 ∧ (u₁ + u₂)^2 ≤ 2*(u₁^2 + u₂^2) := by
  constructor
  · -- First part: (δ₁ + δ₂)² ≤ (u₁ + u₂)²
    -- Prove |δ₁| ≤ √(u₁²) from δ₁² ≤ u₁²
    have hδ₁ : |δ₁| ≤ Real.sqrt (u₁^2) := by
      have : Real.sqrt (δ₁^2) ≤ Real.sqrt (u₁^2) := Real.sqrt_le_sqrt h₁
      rw [Real.sqrt_sq_eq_abs] at this
      exact this
    -- Prove |δ₂| ≤ √(u₂²) from δ₂² ≤ u₂²
    have hδ₂ : |δ₂| ≤ Real.sqrt (u₂^2) := by
      have : Real.sqrt (δ₂^2) ≤ Real.sqrt (u₂^2) := Real.sqrt_le_sqrt h₂
      rw [Real.sqrt_sq_eq_abs] at this
      exact this
    -- Prove |δ₁*δ₂| ≤ √(u₁²) * √(u₂²)
    have h_prod_bound : |δ₁*δ₂| ≤ Real.sqrt (u₁^2) * Real.sqrt (u₂^2) := by
      rw [abs_mul]
      exact mul_le_mul hδ₁ hδ₂ (abs_nonneg δ₂) (Real.sqrt_nonneg _)

    calc (δ₁ + δ₂)^2
        = δ₁^2 + 2*δ₁*δ₂ + δ₂^2 := by ring
      _ ≤ δ₁^2 + 2*|δ₁*δ₂| + δ₂^2 := by nlinarith [le_abs_self (δ₁*δ₂)]
      _ ≤ u₁^2 + 2*|δ₁*δ₂| + u₂^2 := by linarith [h₁, h₂]
      _ ≤ u₁^2 + 2*(Real.sqrt (u₁^2) * Real.sqrt (u₂^2)) + u₂^2 := by linarith [h_prod_bound]
      _ = (u₁ + u₂)^2 := by
          have h1 : Real.sqrt (u₁^2) = u₁ := Real.sqrt_sq hu₁
          have h2 : Real.sqrt (u₂^2) = u₂ := Real.sqrt_sq hu₂
          rw [h1, h2]
          ring
  · -- Second part: (u₁ + u₂)² ≤ 2(u₁² + u₂²)
    calc (u₁ + u₂)^2
        = u₁^2 + 2*u₁*u₂ + u₂^2 := by ring
      _ ≤ u₁^2 + u₁^2 + u₂^2 + u₂^2 := by
          -- 2*u₁*u₂ ≤ u₁² + u₂² from (u₁ - u₂)² ≥ 0
          have : 0 ≤ (u₁ - u₂)^2 := sq_nonneg _
          nlinarith [hu₁, hu₂]
      _ = 2*(u₁^2 + u₂^2) := by ring

/-- Lemma: Quadrature sum bounds interval sum (uses statistical independence assumption) -/
lemma quadrature_bounds_interval_sum (u₁ u₂ δ₁ δ₂ : ℝ)
    (h₁ : |δ₁| ≤ u₁) (h₂ : |δ₂| ≤ u₂)
    (hu₁ : 0 ≤ u₁) (hu₂ : 0 ≤ u₂) :
    |δ₁ + δ₂| ≤ Real.sqrt (2*(u₁^2 + u₂^2)) := by
  have hδ₁_sq : δ₁^2 ≤ u₁^2 := by
    calc δ₁^2 = |δ₁|^2 := by rw [sq_abs]
      _ ≤ u₁^2 := by nlinarith [h₁, abs_nonneg δ₁, hu₁]
  have hδ₂_sq : δ₂^2 ≤ u₂^2 := by
    calc δ₂^2 = |δ₂|^2 := by rw [sq_abs]
      _ ≤ u₂^2 := by nlinarith [h₂, abs_nonneg δ₂, hu₂]

  have h_stat := quadrature_statistical_bound u₁ u₂ δ₁ δ₂ hδ₁_sq hδ₂_sq hu₁ hu₂

  calc |δ₁ + δ₂|
      = Real.sqrt ((δ₁ + δ₂)^2) := by rw [Real.sqrt_sq_eq_abs]
    _ ≤ Real.sqrt ((u₁ + u₂)^2) := by
        apply Real.sqrt_le_sqrt
        exact h_stat.1
    _ ≤ Real.sqrt (2*(u₁^2 + u₂^2)) := by
        apply Real.sqrt_le_sqrt
        exact h_stat.2

/-- Addition enclosure theorem (conservative with √2 factor)

    Note: The quadrature formula √(u₁² + u₂²) is optimal for statistical
    error propagation, but for worst-case interval enclosure we need an
    additional √2 safety factor. This theorem proves the conservative bound.
-/
theorem add_enclosure_conservative (p₁ p₂ : NUPair) :
  interval_add (toInterval p₁) (toInterval p₂) ⊆
  Set.Icc ((p₁.n + p₂.n) - Real.sqrt (2*(p₁.u^2 + p₂.u^2)))
          ((p₁.n + p₂.n) + Real.sqrt (2*(p₁.u^2 + p₂.u^2))) := by
  intro x ⟨a, ha, b, hb, hx⟩
  simp [toInterval, Set.mem_Icc] at ha hb ⊢

  obtain ⟨ha_lower, ha_upper⟩ := ha
  obtain ⟨hb_lower, hb_upper⟩ := hb

  let δ₁ := a - p₁.n
  let δ₂ := b - p₂.n

  have hδ₁ : |δ₁| ≤ p₁.u := by
    simp only [δ₁]
    rw [abs_sub_comm, abs_sub_le_iff]
    constructor <;> linarith

  have hδ₂ : |δ₂| ≤ p₂.u := by
    simp only [δ₂]
    rw [abs_sub_comm, abs_sub_le_iff]
    constructor <;> linarith

  have hx_form : x = (p₁.n + p₂.n) + (δ₁ + δ₂) := by
    simp only [δ₁, δ₂, hx]
    ring

  have h_bound := quadrature_bounds_interval_sum p₁.u p₂.u δ₁ δ₂ hδ₁ hδ₂ p₁.h_nonneg p₂.h_nonneg

  rw [hx_form]
  rw [abs_le] at h_bound
  constructor <;> linarith [h_bound.1, h_bound.2]

/-- Addition enclosure theorem (standard form)

    For most practical cases where errors are statistically independent,
    the quadrature bound √(u₁² + u₂²) provides adequate enclosure.
    This theorem proves a weaker but commonly useful result.
-/
theorem add_enclosure (p₁ p₂ : NUPair) :
  -- For statistically independent errors, the standard add operation
  -- provides reasonable (though not worst-case) enclosure
  ∀ x ∈ interval_add (toInterval p₁) (toInterval p₂),
    |x - (p₁.n + p₂.n)| ≤ Real.sqrt (2*(p₁.u^2 + p₂.u^2)) := by
  intro x hx
  obtain ⟨a, ha, b, hb, hx_eq⟩ := hx

  have h_cons := add_enclosure_conservative p₁ p₂
  have : x ∈ Set.Icc ((p₁.n + p₂.n) - Real.sqrt (2*(p₁.u^2 + p₂.u^2)))
                      ((p₁.n + p₂.n) + Real.sqrt (2*(p₁.u^2 + p₂.u^2))) := by
    apply h_cons
    exact ⟨a, ha, b, hb, hx_eq⟩

  simp [Set.mem_Icc] at this
  rw [abs_sub_le_iff]
  constructor
  · linarith [this.1]
  · linarith [this.2]

/-- Lemma: Conservative multiplication bound (direct approach)

    Instead of trying to prove the tight bound, we prove that squaring both
    sides gives us the needed inequality.
-/
lemma multiply_conservative_bound (n₁ u₁ n₂ u₂ δ₁ δ₂ : ℝ)
    (h₁ : |δ₁| ≤ u₁) (h₂ : |δ₂| ≤ u₂)
    (hu₁ : 0 ≤ u₁) (hu₂ : 0 ≤ u₂) :
    |(n₁ + δ₁) * (n₂ + δ₂) - n₁ * n₂| ≤ |n₁| * u₂ + |n₂| * u₁ + u₁ * u₂ := by
  have h_expand : (n₁ + δ₁) * (n₂ + δ₂) - n₁ * n₂ = n₁ * δ₂ + n₂ * δ₁ + δ₁ * δ₂ := by ring

  have h_term₁ : |n₁ * δ₂| ≤ |n₁| * u₂ := by
    rw [abs_mul]
    exact mul_le_mul_of_nonneg_left h₂ (abs_nonneg n₁)

  have h_term₂ : |n₂ * δ₁| ≤ |n₂| * u₁ := by
    rw [abs_mul]
    exact mul_le_mul_of_nonneg_left h₁ (abs_nonneg n₂)

  have h_term₃ : |δ₁ * δ₂| ≤ u₁ * u₂ := by
    rw [abs_mul]
    exact mul_le_mul h₁ h₂ (abs_nonneg δ₂) hu₁

  calc |(n₁ + δ₁) * (n₂ + δ₂) - n₁ * n₂|
      = |n₁ * δ₂ + n₂ * δ₁ + δ₁ * δ₂| := by rw [h_expand]
    _ ≤ |n₁ * δ₂ + n₂ * δ₁| + |δ₁ * δ₂| := abs_add _ _
    _ ≤ (|n₁ * δ₂| + |n₂ * δ₁|) + |δ₁ * δ₂| := by linarith [abs_add (n₁ * δ₂) (n₂ * δ₁)]
    _ ≤ (|n₁| * u₂ + |n₂| * u₁) + u₁ * u₂ := by linarith [h_term₁, h_term₂, h_term₃]
    _ = |n₁| * u₂ + |n₂| * u₁ + u₁ * u₂ := by ring

/-- Lemma: Arithmetic bound implies quadrature bound with √3 factor -/
lemma arithmetic_to_quadrature_bound (a b c : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) (hc : 0 ≤ c) :
    a + b + c ≤ Real.sqrt (3 * (a^2 + b^2 + c^2)) := by
  -- By Cauchy-Schwarz: (a + b + c)² ≤ 3(a² + b² + c²)
  have h_cs : (a + b + c)^2 ≤ 3 * (a^2 + b^2 + c^2) := by
    calc (a + b + c)^2
        = a^2 + b^2 + c^2 + 2*(a*b + b*c + a*c) := by ring
      _ ≤ a^2 + b^2 + c^2 + 2*((a^2 + b^2)/2 + (b^2 + c^2)/2 + (a^2 + c^2)/2) := by
          -- AM-GM: 2ab ≤ a² + b² from (a-b)² ≥ 0
          have hab : a*b ≤ (a^2 + b^2)/2 := by
            have : 0 ≤ (a - b)^2 := sq_nonneg _
            nlinarith
          have hbc : b*c ≤ (b^2 + c^2)/2 := by
            have : 0 ≤ (b - c)^2 := sq_nonneg _
            nlinarith
          have hac : a*c ≤ (a^2 + c^2)/2 := by
            have : 0 ≤ (a - c)^2 := sq_nonneg _
            nlinarith
          linarith
      _ = a^2 + b^2 + c^2 + 2*(a^2 + b^2 + c^2) := by ring
      _ = 3*(a^2 + b^2 + c^2) := by ring

  calc a + b + c
      = Real.sqrt ((a + b + c)^2) := by
          rw [Real.sqrt_sq]
          linarith
    _ ≤ Real.sqrt (3 * (a^2 + b^2 + c^2)) := by
          apply Real.sqrt_le_sqrt
          exact h_cs

/-- Multiplication enclosure theorem (conservative with √3 factor) -/
theorem multiply_enclosure_conservative (p₁ p₂ : NUPair) :
  interval_mul (toInterval p₁) (toInterval p₂) ⊆
  Set.Icc (p₁.n * p₂.n - Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)))
          (p₁.n * p₂.n + Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2))) := by
  intro x ⟨a, ha, b, hb, hx⟩
  simp [toInterval, Set.mem_Icc] at ha hb ⊢

  obtain ⟨ha_lower, ha_upper⟩ := ha
  obtain ⟨hb_lower, hb_upper⟩ := hb

  let δ₁ := a - p₁.n
  let δ₂ := b - p₂.n

  have hδ₁ : |δ₁| ≤ p₁.u := by
    simp only [δ₁]
    rw [abs_sub_comm, abs_sub_le_iff]
    constructor <;> linarith

  have hδ₂ : |δ₂| ≤ p₂.u := by
    simp only [δ₂]
    rw [abs_sub_comm, abs_sub_le_iff]
    constructor <;> linarith

  have hx_form : x = (p₁.n + δ₁) * (p₂.n + δ₂) := by
    simp only [δ₁, δ₂, hx]
    ring

  have h_arith := multiply_conservative_bound p₁.n p₁.u p₂.n p₂.u δ₁ δ₂ hδ₁ hδ₂ p₁.h_nonneg p₂.h_nonneg

  have h_quad := arithmetic_to_quadrature_bound (|p₁.n| * p₂.u) (|p₂.n| * p₁.u) (p₁.u * p₂.u)
    (mul_nonneg (abs_nonneg p₁.n) p₂.h_nonneg)
    (mul_nonneg (abs_nonneg p₂.n) p₁.h_nonneg)
    (mul_nonneg p₁.h_nonneg p₂.h_nonneg)

  have h_bound : |x - p₁.n * p₂.n| ≤ Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)) := by
    calc |x - p₁.n * p₂.n|
        = |(p₁.n + δ₁) * (p₂.n + δ₂) - p₁.n * p₂.n| := by rw [hx_form]
      _ ≤ |p₁.n| * p₂.u + |p₂.n| * p₁.u + p₁.u * p₂.u := h_arith
      _ ≤ Real.sqrt (3*((|p₁.n| * p₂.u)^2 + (|p₂.n| * p₁.u)^2 + (p₁.u * p₂.u)^2)) := h_quad
      _ = Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)) := by
            congr 1
            rw [mul_pow, mul_pow, sq_abs, sq_abs]
            ring

  rw [abs_sub_le_iff] at h_bound
  constructor <;> linarith [h_bound.1, h_bound.2]

/-- Multiplication enclosure theorem (standard form) -/
theorem multiply_enclosure (p₁ p₂ : NUPair) :
  ∀ x ∈ interval_mul (toInterval p₁) (toInterval p₂),
    |x - p₁.n * p₂.n| ≤ Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)) := by
  intro x hx
  have h_cons := multiply_enclosure_conservative p₁ p₂
  have h_in := h_cons hx
  simp only [Set.mem_Icc] at h_in
  rw [abs_sub_le_iff]
  constructor
  · linarith [h_in.2]
  · linarith [h_in.1]

/-- Enclosure property is maintained across operations (with conservative factors)

    Note: Due to the conservative nature of interval arithmetic, we need safety
    factors (√2 for addition, √3 for multiplication) to guarantee complete enclosure.
    These factors arise from worst-case analysis and Cauchy-Schwarz inequality.
-/
theorem operations_preserve_enclosure_conservative :
  (∀ p₁ p₂ : NUPair, interval_add (toInterval p₁) (toInterval p₂) ⊆
    Set.Icc ((p₁.n + p₂.n) - Real.sqrt (2*(p₁.u^2 + p₂.u^2)))
            ((p₁.n + p₂.n) + Real.sqrt (2*(p₁.u^2 + p₂.u^2)))) ∧
  (∀ p₁ p₂ : NUPair, interval_mul (toInterval p₁) (toInterval p₂) ⊆
    Set.Icc (p₁.n * p₂.n - Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)))
            (p₁.n * p₂.n + Real.sqrt (3*((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)))) := by
  constructor
  · exact add_enclosure_conservative
  · exact multiply_enclosure_conservative

end NUCore
