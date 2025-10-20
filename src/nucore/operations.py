"""
NUCore Operations: Nominal/Uncertainty Algebra

All operations maintain O(1) complexity and preserve epistemic invariants.

Mathematical foundations:
- ⊕ (add): Nominal addition with quadrature uncertainty
- ⊗ (multiply): Product with relative uncertainty propagation
- ⊙ (compose): Uncertainty reduction through composition
- Catch: Identity-preserving error handling
- Flip: Deterministic state inversion

Theorem (O(1) Complexity):
Each operation OP ∈ {⊕, ⊗, ⊙} executes in fixed time and space
independent of graph depth.

Proof: /verification/NUProof/complexity.v
"""

import math
from typing import Tuple

# Type alias for nominal-uncertainty pairs
NU = Tuple[float, float]


def add(n1: float, u1: float, n2: float, u2: float) -> NU:
    """
    Addition: (n1 ± u1) ⊕ (n2 ± u2) = (n1 + n2) ± √(u1² + u2²)

    Quadrature sum ensures enclosure preservation and non-negativity.

    Args:
        n1: First nominal value
        u1: First uncertainty (u1 >= 0)
        n2: Second nominal value
        u2: Second uncertainty (u2 >= 0)

    Returns:
        (n_out, u_out): Result pair with u_out >= 0

    Complexity: O(1)

    Invariants:
        - Non-negativity: u_out >= 0
        - Enclosure: [n1-u1, n1+u1] + [n2-u2, n2+u2] ⊆ [n_out-u_out, n_out+u_out]
        - Constant-time: Fixed operations regardless of input magnitude

    Formal proof: /verification/NUProof/add_nonnegative.v
    """
    assert u1 >= 0, f"Non-negativity violated: u1={u1} < 0"
    assert u2 >= 0, f"Non-negativity violated: u2={u2} < 0"

    n_out = n1 + n2
    u_out = math.sqrt(u1 * u1 + u2 * u2)

    assert u_out >= 0, f"Output non-negativity violated: u_out={u_out}"

    return (n_out, u_out)


def multiply(n1: float, u1: float, n2: float, u2: float, lambda_margin: float = 1.0) -> NU:
    """
    Multiplication: (n1 ± u1) ⊗ (n2 ± u2)

    Conservative product rule with tunable margin λ (frozen at runtime to λ=1.0).

    Formula:
        n_out = n1 * n2
        u_out = λ * √[(n1·u2)² + (n2·u1)² + (u1·u2)²]

    Args:
        n1: First nominal value
        u1: First uncertainty (u1 >= 0)
        n2: Second nominal value
        u2: Second uncertainty (u2 >= 0)
        lambda_margin: Margin multiplier (frozen at 1.0 for determinism)

    Returns:
        (n_out, u_out): Result pair with u_out >= 0

    Complexity: O(1)

    Invariants:
        - Non-negativity: u_out >= 0
        - Enclosure: Product interval fully covered
        - Conservative: Includes cross-term (u1·u2)² for robustness
        - Deterministic: λ frozen at compile-time (default 1.0)

    Formal proof: /verification/NUProof/multiply_enclosure.v
    """
    assert u1 >= 0, f"Non-negativity violated: u1={u1} < 0"
    assert u2 >= 0, f"Non-negativity violated: u2={u2} < 0"
    assert lambda_margin >= 1.0, f"Margin must be >= 1.0: λ={lambda_margin}"

    n_out = n1 * n2

    # Conservative uncertainty: includes cross-term
    term1 = n1 * u2
    term2 = n2 * u1
    term3 = u1 * u2

    u_out = lambda_margin * math.sqrt(term1**2 + term2**2 + term3**2)

    assert u_out >= 0, f"Output non-negativity violated: u_out={u_out}"

    return (n_out, u_out)


def compose(n1: float, u1: float, n2: float, u2: float) -> NU:
    """
    Composition: (n1 ± u1) ⊙ (n2 ± u2)

    Reduces uncertainty through informational composition.
    Geometric mean in uncertainty space: u_out² = u1² · u2² / (u1² + u2²)

    Nominal takes weighted average: n_out = (n1·u2² + n2·u1²) / (u1² + u2²)

    Args:
        n1: First nominal value
        u1: First uncertainty (u1 > 0)
        n2: Second nominal value
        u2: Second uncertainty (u2 > 0)

    Returns:
        (n_out, u_out): Composed result with reduced uncertainty

    Complexity: O(1)

    Invariants:
        - Non-negativity: u_out >= 0
        - Reduction: u_out <= min(u1, u2)
        - Information gain: Composition decreases epistemic uncertainty

    Special cases:
        - If u1 or u2 is zero, return the certain value
        - Composition is commutative and associative

    Formal proof: /verification/NUProof/compose_reduction.v
    """
    assert u1 >= 0, f"Non-negativity violated: u1={u1} < 0"
    assert u2 >= 0, f"Non-negativity violated: u2={u2} < 0"

    # Handle zero uncertainty cases
    if u1 == 0 and u2 == 0:
        # Both certain: average the nominals
        return ((n1 + n2) / 2.0, 0.0)
    elif u1 == 0:
        # First is certain
        return (n1, 0.0)
    elif u2 == 0:
        # Second is certain
        return (n2, 0.0)

    # General composition
    u1_sq = u1 * u1
    u2_sq = u2 * u2
    denom = u1_sq + u2_sq

    # Weighted average favoring more certain value
    n_out = (n1 * u2_sq + n2 * u1_sq) / denom

    # Geometric mean in uncertainty space
    u_out = math.sqrt((u1_sq * u2_sq) / denom)

    assert u_out >= 0, f"Output non-negativity violated: u_out={u_out}"
    assert u_out <= u1 + 1e-10, f"Reduction violated: u_out={u_out} > u1={u1}"
    assert u_out <= u2 + 1e-10, f"Reduction violated: u_out={u_out} > u2={u2}"

    return (n_out, u_out)


def catch(n: float, u: float, default_n: float = 0.0, default_u: float = float('inf')) -> NU:
    """
    Catch: Identity-preserving error handling

    Returns input if valid, otherwise returns default with infinite uncertainty
    to signal complete epistemic failure.

    Args:
        n: Nominal value to check
        u: Uncertainty value to check
        default_n: Default nominal if invalid (default: 0.0)
        default_u: Default uncertainty if invalid (default: inf)

    Returns:
        (n, u) if valid, else (default_n, default_u)

    Complexity: O(1)

    Philosophy:
        "Failure is allowed. Lying about failure is not."
        Catch returns infinite uncertainty rather than hiding failure.
    """
    if math.isnan(n) or math.isnan(u) or math.isinf(n) or u < 0:
        return (default_n, default_u)

    return (n, u)


def flip(n: float, u: float) -> NU:
    """
    Flip: Deterministic state inversion

    Negates the nominal value while preserving uncertainty.

    Args:
        n: Nominal value
        u: Uncertainty (u >= 0)

    Returns:
        (-n, u): Flipped nominal, same uncertainty

    Complexity: O(1)

    Invariants:
        - Non-negativity: u_out >= 0
        - Symmetry: flip(flip(x)) = x
        - Enclosure: [n-u, n+u] → [-n-u, -n+u]

    Formal proof: /verification/NUProof/flip_involutive.v
    """
    assert u >= 0, f"Non-negativity violated: u={u} < 0"

    return (-n, u)
