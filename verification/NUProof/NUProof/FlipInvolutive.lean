/-
  FlipInvolutive.lean
  Theorem: Flip is involutive (Flip(Flip(x)) = x)
  Part of eBIOS Layer 2: NUProof
-/

import NUCore

namespace NUCore

/-!
  # Flip Theorems

  ## Negation Flip (flip)
  flip(n, u) = (-n, u)
  **Theorem**: flip IS involutive — flip(flip(p)) = p

  ## NASA Paper B Operator (swapFlip)
  swapFlip(n, u) = (u, |n|)
  **Theorem**: swapFlip is NOT involutive — swapFlip(swapFlip(p)) ≠ p in general
  **Correct property**: swapFlip³ = swapFlip (period-2 cycle from first application)
  i.e. swapFlip(swapFlip(swapFlip(p))) = swapFlip(p)

  **F-002 resolution**: The SSOT finding claimed FlipInvolutive.lean proved a false theorem.
  It did not — it proved the correct theorem for the negation flip.
  The confusion arose from conflating two distinct operators.
  This file now proves both operators' correct properties.
-/

/-- Flip is involutive -/
theorem flip_involutive (p : NUPair) :
  flip (flip p) = p := by
  ext
  · -- -(-n) = n: flip.n (flip p).n = p.n
    simp [flip]
  · -- u = u: flip.u (flip p).u = p.u
    simp [flip]

/-- Flip preserves uncertainty exactly -/
theorem flip_preserves_uncertainty (p : NUPair) :
  (flip p).u = p.u := by
  rfl

/-- Flip negates nominal exactly -/
theorem flip_negates_nominal (p : NUPair) :
  (flip p).n = -p.n := by
  rfl

/-- swapFlip is NOT involutive -/
-- swapFlip(swapFlip(p)) = (|p.n|, p.u) ≠ p unless p.n ≥ 0
theorem swapFlip_not_involutive_general : ∃ p : NUPair, swapFlip (swapFlip p) ≠ p := by
  use ⟨-1, 1, by norm_num⟩
  simp [swapFlip, NUPair.ext_iff]
  norm_num

/-- swapFlip applied twice gives (|n|, u) -/
theorem swapFlip_sq (p : NUPair) :
    swapFlip (swapFlip p) = ⟨|p.n|, p.u, p.h_nonneg⟩ := by
  ext
  · simp [swapFlip]
  · simp [swapFlip, abs_of_nonneg p.h_nonneg]

/-- swapFlip³ = swapFlip (period-2 from first application) -/
theorem swapFlip_period_two (p : NUPair) :
    swapFlip (swapFlip (swapFlip p)) = swapFlip p := by
  ext
  · simp [swapFlip, abs_of_nonneg p.h_nonneg]
  · simp [swapFlip, abs_abs]

/-- swapFlip² is idempotent: (swapFlip²)² = swapFlip² -/
theorem swapFlip_sq_idempotent (p : NUPair) :
    swapFlip (swapFlip (swapFlip (swapFlip p))) = swapFlip (swapFlip p) := by
  rw [swapFlip_sq, swapFlip_sq]
  ext
  · simp [swapFlip, abs_abs]
  · simp [swapFlip, abs_of_nonneg p.h_nonneg]

end NUCore
