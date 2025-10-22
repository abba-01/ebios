"""
NUCore: Nominal/Uncertainty Algebra Kernel

Layer 1 of the eBIOS stack — deterministic epistemic computation.

N/U Algebra is not a probabilistic method but a deterministic contract between
math and ethics: every operation is enclosure-preserving, constant-time, and auditable.

Core operations: ⊕ (add), ⊗ (multiply), ⊙ (compose), Catch, Flip

Invariants:
- Non-negativity: u ≥ 0 for all operations
- Enclosure preservation: [n-u, n+u] bounds maintained
- Constant-time execution: O(1) complexity for all operations
- Monotonicity: Uncertainty never decreases without explicit composition

Formal proofs: /verification/NUProof/
"""

from .operations import add, multiply, compose, catch, flip
from .validators import validate, assert_invariants

__all__ = [
    'add',
    'multiply',
    'compose',
    'catch',
    'flip',
    'validate',
    'assert_invariants',
]

__version__ = '0.1.0'
__layer__ = 1  # Layer 1 of eBIOS stack
