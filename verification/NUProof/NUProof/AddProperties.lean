/-
  AddProperties.lean
  Theorems: Addition commutativity and associativity
  Part of eBIOS Layer 2: NUProof
-/

import NUCore

namespace NUCore

/-!
  # Addition Algebraic Properties

  **Theorems**:
  1. Commutativity: a ⊕ b = b ⊕ a
  2. Associativity: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)

  **Proof Strategy**:
  - Both follow from commutativity/associativity of + and sqrt properties

  **Status**: Skeleton (requires NUPair equality lemmas)
-/

/-- NUPair equality: two pairs are equal if n and u are equal -/
theorem NUPair.ext {p₁ p₂ : NUPair} (hn : p₁.n = p₂.n) (hu : p₁.u = p₂.u) : p₁ = p₂ := by
  cases p₁
  cases p₂
  simp at hn hu
  subst hn hu
  rfl

/-- Addition is commutative -/
theorem add_comm (p₁ p₂ : NUPair) :
  add p₁ p₂ = add p₂ p₁ := by
  apply NUPair.ext
  · -- Nominal commutativity: n₁ + n₂ = n₂ + n₁
    ring
  · -- Uncertainty commutativity: √(u₁² + u₂²) = √(u₂² + u₁²)
    ring_nf
    rfl

/-- Addition is associative -/
theorem add_assoc (p₁ p₂ p₃ : NUPair) :
  add (add p₁ p₂) p₃ = add p₁ (add p₂ p₃) := by
  apply NUPair.ext
  · -- Nominal associativity: (n₁ + n₂) + n₃ = n₁ + (n₂ + n₃)
    ring
  · -- Uncertainty associativity (requires sqrt algebra)
    sorry  -- TODO: Requires lemma: √(√(a²+b²)² + c²) = √(a² + √(b²+c²)²)

/-- Zero uncertainty is additive identity for uncertainty -/
theorem add_zero_u (p : NUPair) (h : p.u = 0) :
  ∀ q : NUPair, (add p q).u = q.u := by
  intro q
  unfold add
  simp [h]
  ring_nf
  rw [Real.sqrt_sq (by exact q.h_nonneg)]

end NUCore
