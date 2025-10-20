/-
  Enclosure.lean
  Theorem: NUCore operations preserve interval enclosure
  Part of eBIOS Layer 2: NUProof
-/

import NUProof.NUCore

namespace NUCore

/-!
  # Enclosure Preservation Theorem

  **Theorem**: For OP ∈ {⊕, ⊗}:
    [n₁-u₁, n₁+u₁] OP [n₂-u₂, n₂+u₂] ⊆ [n_out-u_out, n_out+u_out]

  **Meaning**: The output interval always contains all possible exact results
  from inputs within the input intervals.

  **Proof Strategy**:
  - Addition: Direct interval arithmetic
  - Multiplication: Conservative bound with cross-term

  **Status**: Skeleton (requires interval arithmetic lemmas)
-/

/-- Helper: interval addition -/
def interval_add (I₁ I₂ : Set ℝ) : Set ℝ :=
  {x | ∃ a ∈ I₁, ∃ b ∈ I₂, x = a + b}

/-- Helper: interval multiplication -/
def interval_mul (I₁ I₂ : Set ℝ) : Set ℝ :=
  {x | ∃ a ∈ I₁, ∃ b ∈ I₂, x = a * b}

/-- Addition enclosure theorem (skeleton) -/
theorem add_enclosure (p₁ p₂ : NUPair) :
  interval_add (toInterval p₁) (toInterval p₂) ⊆ toInterval (add p₁ p₂) := by
  sorry  -- TODO: Full proof requires interval arithmetic lemmas

/-- Multiplication enclosure theorem (skeleton) -/
theorem multiply_enclosure (p₁ p₂ : NUPair) :
  interval_mul (toInterval p₁) (toInterval p₂) ⊆ toInterval (multiply p₁ p₂) := by
  sorry  -- TODO: Full proof requires conservative bound analysis

/-- Enclosure property is maintained across operations -/
theorem operations_preserve_enclosure :
  (∀ p₁ p₂ : NUPair, interval_add (toInterval p₁) (toInterval p₂) ⊆ toInterval (add p₁ p₂)) ∧
  (∀ p₁ p₂ : NUPair, interval_mul (toInterval p₁) (toInterval p₂) ⊆ toInterval (multiply p₁ p₂)) := by
  constructor
  · exact fun p₁ p₂ => add_enclosure p₁ p₂
  · exact fun p₁ p₂ => multiply_enclosure p₁ p₂

end NUCore
