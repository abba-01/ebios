/-
  NUCore.lean
  Core definitions for N/U Algebra formal verification
  Part of eBIOS Layer 2: NUProof
-/

import Mathlib.Data.Real.Basic
import Mathlib.Tactic

namespace NUCore

/-- Nominal/Uncertainty pair representation -/
@[ext]
structure NUPair where
  n : ℝ  -- nominal value
  u : ℝ  -- uncertainty (must be non-negative)
  h_nonneg : 0 ≤ u

/-- Addition operation: (n₁ ± u₁) ⊕ (n₂ ± u₂) = (n₁ + n₂) ± √(u₁² + u₂²) -/
noncomputable def add (p₁ p₂ : NUPair) : NUPair where
  n := p₁.n + p₂.n
  u := Real.sqrt (p₁.u^2 + p₂.u^2)
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Multiplication operation: (n₁ ± u₁) ⊗ (n₂ ± u₂) = (n₁·n₂) ± √[(n₁·u₂)² + (n₂·u₁)² + (u₁·u₂)²] -/
noncomputable def multiply (p₁ p₂ : NUPair) : NUPair where
  n := p₁.n * p₂.n
  u := Real.sqrt ((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Composition operation: uncertainty reduction through evidence combination -/
noncomputable def compose (p₁ p₂ : NUPair) (h₁ : p₁.u ≠ 0 ∨ p₂.u ≠ 0) : NUPair where
  n := (p₁.n * p₂.u^2 + p₂.n * p₁.u^2) / (p₁.u^2 + p₂.u^2)
  u := Real.sqrt ((p₁.u^2 * p₂.u^2) / (p₁.u^2 + p₂.u^2))
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Flip operation: negation preserving uncertainty -/
-- Note: This is the negation flip (-n, u). It IS involutive: flip(flip(p)) = p.
-- Distinct from the NASA Paper's B operator (u, |n|) which is NOT involutive.
def flip (p : NUPair) : NUPair where
  n := -p.n
  u := p.u
  h_nonneg := p.h_nonneg

/-- NASA Paper B operator: swap nominal and uncertainty with absolute value -/
-- B(n, u) = (u, |n|)
-- This is NOT involutive. B² ≠ id in general.
-- Property: B² is idempotent (B⁴ = B²), and B³ = B (period-2 from B¹).
-- B(n, u)   = (u, |n|)
-- B²(n, u)  = (|n|, u)   [since u ≥ 0, |u| = u]
-- B³(n, u)  = (u, |n|)   = B(n, u)
-- So B³ = B: the operator cycles with period 2 after the first application.
noncomputable def swapFlip (p : NUPair) : NUPair where
  n := p.u
  u := |p.n|
  h_nonneg := abs_nonneg p.n

/-- Interval representation [n - u, n + u] -/
def toInterval (p : NUPair) : Set ℝ :=
  Set.Icc (p.n - p.u) (p.n + p.u)

/-- Enclosure property: interval containment -/
def encloses (result : NUPair) (exact : ℝ) : Prop :=
  exact ∈ toInterval result

end NUCore
