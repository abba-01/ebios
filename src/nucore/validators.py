"""
NUCore Validators: Invariant checking and verification

Provides O(1) validation functions to ensure epistemic integrity.

All validators run in constant time regardless of input complexity.
"""

import math
import time
from typing import Tuple, Callable

NU = Tuple[float, float]


def validate(n: float, u: float) -> bool:
    """
    Validate a nominal-uncertainty pair.

    Args:
        n: Nominal value
        u: Uncertainty value

    Returns:
        True if valid (u >= 0, no NaN/Inf), False otherwise

    Complexity: O(1) - fixed-time validation
    """
    if math.isnan(n) or math.isnan(u):
        return False
    if math.isinf(n):
        return False
    if u < 0:
        return False
    return True


def assert_invariants(n: float, u: float, operation: str = "unknown") -> None:
    """
    Assert all NUCore invariants hold for a given (n, u) pair.

    Args:
        n: Nominal value
        u: Uncertainty value
        operation: Name of operation for error reporting

    Raises:
        AssertionError: If any invariant is violated

    Invariants checked:
        - Non-negativity: u >= 0
        - Finiteness: n is finite (not NaN or Inf)
        - Validity: u is finite or explicitly infinite (for error states)

    Complexity: O(1)
    """
    assert not math.isnan(n), f"{operation}: Nominal is NaN"
    assert not math.isnan(u), f"{operation}: Uncertainty is NaN"
    assert not math.isinf(n), f"{operation}: Nominal is infinite"
    assert u >= 0, f"{operation}: Non-negativity violated (u={u})"


def verify_constant_time(
    operation: Callable[..., tuple[float, float]],
    args1: tuple[float, ...],
    args2: tuple[float, ...],
    tolerance_ns: int = 1000,
    iterations: int = 1000
) -> bool:
    """
    Verify that an operation executes in constant time.

    Runs the operation multiple times with different inputs and checks
    that execution time variance is within tolerance.

    Args:
        operation: Function to test
        args1: First set of arguments
        args2: Second set of arguments (should be different complexity)
        tolerance_ns: Maximum acceptable time difference in nanoseconds
        iterations: Number of runs for averaging

    Returns:
        True if operation is constant-time within tolerance

    Note: This is a heuristic check, not a formal proof.
          For formal verification, see /verification/NUProof/

    Complexity: O(iterations) but verifies O(1) property
    """
    # Warm-up runs
    for _ in range(100):
        operation(*args1)
        operation(*args2)

    # Time first argument set
    start1 = time.perf_counter_ns()
    for _ in range(iterations):
        operation(*args1)
    end1 = time.perf_counter_ns()
    time1 = (end1 - start1) / iterations

    # Time second argument set
    start2 = time.perf_counter_ns()
    for _ in range(iterations):
        operation(*args2)
    end2 = time.perf_counter_ns()
    time2 = (end2 - start2) / iterations

    # Check variance
    diff = abs(time1 - time2)
    return diff < tolerance_ns


def verify_enclosure(
    n1: float, u1: float,
    n2: float, u2: float,
    n_out: float, u_out: float,
    operation: str = "unknown"
) -> bool:
    """
    Verify enclosure property for binary operations.

    Checks that the output interval [n_out - u_out, n_out + u_out]
    properly contains the theoretical result interval.

    Args:
        n1, u1: First input pair
        n2, u2: Second input pair
        n_out, u_out: Output pair
        operation: Name of operation ("add" or "multiply")

    Returns:
        True if enclosure property holds

    Complexity: O(1)
    """
    # Compute theoretical bounds
    if operation == "add":
        min_theoretical = (n1 - u1) + (n2 - u2)
        max_theoretical = (n1 + u1) + (n2 + u2)
    elif operation == "multiply":
        corners = [
            (n1 - u1) * (n2 - u2),
            (n1 - u1) * (n2 + u2),
            (n1 + u1) * (n2 - u2),
            (n1 + u1) * (n2 + u2),
        ]
        min_theoretical = min(corners)
        max_theoretical = max(corners)
    else:
        raise ValueError(f"Unknown operation for enclosure check: {operation}")

    # Check output bounds contain theoretical bounds (with small tolerance)
    epsilon = 1e-10
    min_output = n_out - u_out
    max_output = n_out + u_out

    return (min_output <= min_theoretical + epsilon and
            max_output >= max_theoretical - epsilon)


def verify_monotonicity(u_in: float, u_out: float, operation: str = "unknown") -> bool:
    """
    Verify monotonicity property: uncertainty never decreases
    unless explicitly composed.

    Args:
        u_in: Input uncertainty (or max of inputs)
        u_out: Output uncertainty
        operation: Name of operation

    Returns:
        True if monotonicity holds (u_out >= u_in for non-composition ops)

    Note: Compose operation is exempt (it reduces uncertainty by design)

    Complexity: O(1)
    """
    if operation == "compose":
        # Compose reduces uncertainty - monotonicity does not apply
        return True

    # For other operations, uncertainty should not decrease
    epsilon = 1e-10
    return u_out >= u_in - epsilon


def coverage_ratio(n: float, u: float) -> float:
    """
    Compute coverage ratio: u / |n|

    High ratio indicates high epistemic uncertainty relative to estimate.

    Args:
        n: Nominal value
        u: Uncertainty

    Returns:
        u / |n| if n != 0, else infinity

    Complexity: O(1)

    Used by: NUGuard runtime monitoring
    """
    if n == 0:
        return float('inf') if u > 0 else 0.0

    return u / abs(n)


def is_certain(_n: float, u: float, epsilon: float = 1e-10) -> bool:
    """
    Check if a value is effectively certain (u ≈ 0).

    Args:
        _n: Nominal value (unused, kept for API consistency)
        u: Uncertainty
        epsilon: Tolerance for "zero" uncertainty

    Returns:
        True if u <= epsilon

    Complexity: O(1)
    """
    return u <= epsilon


def is_uncertain(n: float, u: float, threshold: float = 1.0) -> bool:
    """
    Check if a value has significant uncertainty.

    Args:
        n: Nominal value
        u: Uncertainty
        threshold: Coverage ratio threshold

    Returns:
        True if coverage_ratio(n, u) >= threshold

    Complexity: O(1)
    """
    return coverage_ratio(n, u) >= threshold
