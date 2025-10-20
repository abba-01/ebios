/-
  NUCore.lean
  Core definitions for N/U Algebra formal verification
  Part of eBIOS Layer 2: NUProof
-/

import Mathlib.Data.Real.Basic
import Mathlib.Tactic

namespace NUCore

/-- Nominal/Uncertainty pair representation -/
structure NUPair where
  n : ℝ  -- nominal value
  u : ℝ  -- uncertainty (must be non-negative)
  h_nonneg : 0 ≤ u

/-- Addition operation: (n₁ ± u₁) ⊕ (n₂ ± u₂) = (n₁ + n₂) ± √(u₁² + u₂²) -/
def add (p₁ p₂ : NUPair) : NUPair where
  n := p₁.n + p₂.n
  u := Real.sqrt (p₁.u^2 + p₂.u^2)
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Multiplication operation: (n₁ ± u₁) ⊗ (n₂ ± u₂) = (n₁·n₂) ± √[(n₁·u₂)² + (n₂·u₁)² + (u₁·u₂)²] -/
def multiply (p₁ p₂ : NUPair) : NUPair where
  n := p₁.n * p₂.n
  u := Real.sqrt ((p₁.n * p₂.u)^2 + (p₂.n * p₁.u)^2 + (p₁.u * p₂.u)^2)
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Composition operation: uncertainty reduction through evidence combination -/
def compose (p₁ p₂ : NUPair) (h₁ : p₁.u ≠ 0 ∨ p₂.u ≠ 0) : NUPair where
  n := (p₁.n * p₂.u^2 + p₂.n * p₁.u^2) / (p₁.u^2 + p₂.u^2)
  u := Real.sqrt ((p₁.u^2 * p₂.u^2) / (p₁.u^2 + p₂.u^2))
  h_nonneg := by
    apply Real.sqrt_nonneg

/-- Flip operation: negation preserving uncertainty -/
def flip (p : NUPair) : NUPair where
  n := -p.n
  u := p.u
  h_nonneg := p.h_nonneg

/-- Interval representation [n - u, n + u] -/
def toInterval (p : NUPair) : Set ℝ :=
  Set.Icc (p.n - p.u) (p.n + p.u)

/-- Enclosure property: interval containment -/
def encloses (result : NUPair) (exact : ℝ) : Prop :=
  exact ∈ toInterval result

end NUCore
