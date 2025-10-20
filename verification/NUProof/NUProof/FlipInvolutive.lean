/-
  FlipInvolutive.lean
  Theorem: Flip is involutive (Flip(Flip(x)) = x)
  Part of eBIOS Layer 2: NUProof
-/

import NUProof.NUCore

namespace NUCore

/-!
  # Flip Involution Theorem

  **Theorem**: Flip(Flip(x)) = x

  **Proof**: Direct by definition
  - Flip(n, u) = (-n, u)
  - Flip(-n, u) = (--n, u) = (n, u)

  **Status**: Complete
-/

/-- Flip is involutive -/
theorem flip_involutive (p : NUPair) :
  flip (flip p) = p := by
  apply NUPair.ext
  · -- -(-n) = n
    ring
  · -- u = u
    rfl

/-- Flip preserves uncertainty exactly -/
theorem flip_preserves_uncertainty (p : NUPair) :
  (flip p).u = p.u := by
  rfl

/-- Flip negates nominal exactly -/
theorem flip_negates_nominal (p : NUPair) :
  (flip p).n = -p.n := by
  rfl

end NUCore
