"""
NUCore Integration Tests

Validates all operations against documented invariants and properties.

Test categories:
- Basic correctness
- Invariant preservation
- Enclosure properties
- Constant-time execution
- Edge cases
"""

import pytest
import math
from src.nucore.operations import add, multiply, compose, catch, flip
from src.nucore.validators import (
    validate,
    assert_invariants,
    verify_enclosure,
    verify_monotonicity,
    coverage_ratio,
    is_certain,
    is_uncertain,
)


class TestAddition:
    """Test ⊕ (add) operation"""

    def test_basic_addition(self):
        """Basic addition correctness"""
        n1, u1 = 10.0, 0.5
        n2, u2 = 20.0, 1.0
        n_out, u_out = add(n1, u1, n2, u2)

        assert n_out == 30.0
        assert u_out == pytest.approx(math.sqrt(0.5**2 + 1.0**2))

    def test_nonnegative_uncertainty(self):
        """Addition preserves non-negativity"""
        n1, u1 = 5.0, 0.1
        n2, u2 = 3.0, 0.2
        n_out, u_out = add(n1, u1, n2, u2)

        assert u_out >= 0

    def test_enclosure_property(self):
        """Addition produces valid interval (quadrature rule)"""
        n1, u1 = 10.0, 1.0
        n2, u2 = 20.0, 2.0
        n_out, u_out = add(n1, u1, n2, u2)

        # Quadrature: u_out = √(u1² + u2²)
        expected_u = math.sqrt(u1**2 + u2**2)
        assert u_out == pytest.approx(expected_u)

        # Output uncertainty should be less than sum (more accurate than naive)
        assert u_out <= (u1 + u2)

    def test_commutativity(self):
        """a ⊕ b = b ⊕ a"""
        n1, u1 = 7.0, 0.3
        n2, u2 = 13.0, 0.7

        result1 = add(n1, u1, n2, u2)
        result2 = add(n2, u2, n1, u1)

        assert result1[0] == pytest.approx(result2[0])
        assert result1[1] == pytest.approx(result2[1])

    def test_associativity(self):
        """(a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)"""
        n1, u1 = 1.0, 0.1
        n2, u2 = 2.0, 0.2
        n3, u3 = 3.0, 0.3

        # Left association
        temp1 = add(n1, u1, n2, u2)
        left = add(temp1[0], temp1[1], n3, u3)

        # Right association
        temp2 = add(n2, u2, n3, u3)
        right = add(n1, u1, temp2[0], temp2[1])

        assert left[0] == pytest.approx(right[0])
        assert left[1] == pytest.approx(right[1], rel=1e-10)

    def test_zero_uncertainty(self):
        """Adding certain values"""
        n1, u1 = 10.0, 0.0
        n2, u2 = 20.0, 0.0
        n_out, u_out = add(n1, u1, n2, u2)

        assert n_out == 30.0
        assert u_out == 0.0
        assert is_certain(n_out, u_out)


class TestMultiplication:
    """Test ⊗ (multiply) operation"""

    def test_basic_multiplication(self):
        """Basic multiplication correctness"""
        n1, u1 = 10.0, 0.5
        n2, u2 = 2.0, 0.1
        n_out, u_out = multiply(n1, u1, n2, u2)

        assert n_out == 20.0
        assert u_out > 0  # Non-negative

    def test_nonnegative_uncertainty(self):
        """Multiplication preserves non-negativity"""
        n1, u1 = 5.0, 0.1
        n2, u2 = 3.0, 0.2
        n_out, u_out = multiply(n1, u1, n2, u2)

        assert u_out >= 0

    def test_enclosure_property(self):
        """Multiplication produces valid interval (conservative rule)"""
        n1, u1 = 10.0, 1.0
        n2, u2 = 5.0, 0.5
        n_out, u_out = multiply(n1, u1, n2, u2)

        # Conservative multiplication includes cross-term
        expected_u = math.sqrt((n1*u2)**2 + (n2*u1)**2 + (u1*u2)**2)
        assert u_out == pytest.approx(expected_u)

        # Non-negative uncertainty
        assert u_out >= 0

    def test_commutativity(self):
        """a ⊗ b = b ⊗ a"""
        n1, u1 = 7.0, 0.3
        n2, u2 = 3.0, 0.2

        result1 = multiply(n1, u1, n2, u2)
        result2 = multiply(n2, u2, n1, u1)

        assert result1[0] == pytest.approx(result2[0])
        assert result1[1] == pytest.approx(result2[1])

    def test_conservative_with_cross_term(self):
        """Multiplication includes (u1·u2)² term"""
        n1, u1 = 10.0, 1.0
        n2, u2 = 10.0, 1.0
        n_out, u_out = multiply(n1, u1, n2, u2)

        # Check that cross-term contributes
        expected = math.sqrt((n1*u2)**2 + (n2*u1)**2 + (u1*u2)**2)
        assert u_out == pytest.approx(expected)

    def test_zero_uncertainty(self):
        """Multiplying certain values"""
        n1, u1 = 5.0, 0.0
        n2, u2 = 4.0, 0.0
        n_out, u_out = multiply(n1, u1, n2, u2)

        assert n_out == 20.0
        assert u_out == 0.0


class TestComposition:
    """Test ⊙ (compose) operation"""

    def test_basic_composition(self):
        """Basic composition correctness"""
        n1, u1 = 10.0, 1.0
        n2, u2 = 12.0, 2.0
        n_out, u_out = compose(n1, u1, n2, u2)

        assert u_out < u1  # Uncertainty reduced
        assert u_out < u2
        assert u_out >= 0

    def test_uncertainty_reduction(self):
        """Composition reduces uncertainty"""
        n1, u1 = 100.0, 10.0
        n2, u2 = 110.0, 5.0
        n_out, u_out = compose(n1, u1, n2, u2)

        # u_out should be less than both inputs
        assert u_out <= u1
        assert u_out <= u2

    def test_weighted_average(self):
        """More certain value has higher weight"""
        n1, u1 = 10.0, 1.0  # More uncertain
        n2, u2 = 20.0, 0.1  # More certain
        n_out, u_out = compose(n1, u1, n2, u2)

        # n_out should be closer to n2 (more certain)
        assert abs(n_out - n2) < abs(n_out - n1)

    def test_certain_input_dominates(self):
        """If one input is certain (u=0), it dominates"""
        n1, u1 = 10.0, 0.0  # Certain
        n2, u2 = 20.0, 5.0  # Uncertain
        n_out, u_out = compose(n1, u1, n2, u2)

        assert n_out == n1
        assert u_out == 0.0

    def test_certain_second_input_dominates(self):
        """If second input is certain (u2=0), it dominates"""
        n1, u1 = 20.0, 5.0  # Uncertain
        n2, u2 = 10.0, 0.0  # Certain
        n_out, u_out = compose(n1, u1, n2, u2)

        assert n_out == n2
        assert u_out == 0.0

    def test_both_certain(self):
        """Composing two certain values"""
        n1, u1 = 10.0, 0.0
        n2, u2 = 10.0, 0.0
        n_out, u_out = compose(n1, u1, n2, u2)

        assert u_out == 0.0

    def test_commutativity(self):
        """a ⊙ b = b ⊙ a"""
        n1, u1 = 15.0, 1.5
        n2, u2 = 18.0, 0.5

        result1 = compose(n1, u1, n2, u2)
        result2 = compose(n2, u2, n1, u1)

        assert result1[0] == pytest.approx(result2[0])
        assert result1[1] == pytest.approx(result2[1])


class TestCatch:
    """Test Catch (error handling) operation"""

    def test_valid_input_passthrough(self):
        """Valid input passes through unchanged"""
        n, u = 10.0, 1.0
        n_out, u_out = catch(n, u)

        assert n_out == n
        assert u_out == u

    def test_nan_nominal_caught(self):
        """NaN nominal triggers default"""
        n, u = float('nan'), 1.0
        n_out, u_out = catch(n, u, default_n=0.0, default_u=float('inf'))

        assert n_out == 0.0
        assert math.isinf(u_out)

    def test_negative_uncertainty_caught(self):
        """Negative uncertainty triggers default"""
        n, u = 10.0, -1.0
        n_out, u_out = catch(n, u, default_n=0.0, default_u=float('inf'))

        assert n_out == 0.0
        assert math.isinf(u_out)

    def test_infinite_nominal_caught(self):
        """Infinite nominal triggers default"""
        n, u = float('inf'), 1.0
        n_out, u_out = catch(n, u, default_n=0.0, default_u=float('inf'))

        assert n_out == 0.0
        assert math.isinf(u_out)

    def test_failure_signals_infinite_uncertainty(self):
        """Failures return infinite uncertainty, not zero"""
        n, u = float('nan'), float('nan')
        n_out, u_out = catch(n, u)

        assert math.isinf(u_out), "Failure must signal infinite uncertainty"


class TestFlip:
    """Test Flip (negation) operation"""

    def test_basic_flip(self):
        """Basic flip correctness"""
        n, u = 10.0, 1.0
        n_out, u_out = flip(n, u)

        assert n_out == -10.0
        assert u_out == 1.0

    def test_involutive(self):
        """Flip(Flip(x)) = x"""
        n, u = 7.5, 0.5
        n1, u1 = flip(n, u)
        n2, u2 = flip(n1, u1)

        assert n2 == pytest.approx(n)
        assert u2 == pytest.approx(u)

    def test_preserves_uncertainty(self):
        """Flip preserves uncertainty"""
        n, u = 100.0, 10.0
        n_out, u_out = flip(n, u)

        assert u_out == u


class TestValidators:
    """Test validation functions"""

    def test_validate_accepts_valid(self):
        """Validate accepts valid pairs"""
        assert validate(10.0, 1.0) is True
        assert validate(0.0, 0.0) is True
        assert validate(-5.0, 2.0) is True

    def test_validate_rejects_negative_u(self):
        """Validate rejects negative uncertainty"""
        assert validate(10.0, -1.0) is False

    def test_validate_rejects_nan(self):
        """Validate rejects NaN"""
        assert validate(float('nan'), 1.0) is False
        assert validate(10.0, float('nan')) is False

    def test_validate_rejects_infinite_n(self):
        """Validate rejects infinite nominal"""
        assert validate(float('inf'), 1.0) is False

    def test_assert_invariants_passes_valid(self):
        """Assert invariants passes for valid input"""
        # Should not raise
        assert_invariants(10.0, 1.0, operation="test")

    def test_assert_invariants_fails_negative_u(self):
        """Assert invariants fails for negative uncertainty"""
        # Updated 2025-10-22: assert_invariants now raises ValueError (not AssertionError)
        # Reason: Exceptions survive -O flag (assertions don't)
        with pytest.raises(ValueError):
            assert_invariants(10.0, -1.0, operation="test")

    def test_coverage_ratio(self):
        """Coverage ratio calculation"""
        assert coverage_ratio(10.0, 1.0) == pytest.approx(0.1)
        assert coverage_ratio(100.0, 10.0) == pytest.approx(0.1)
        assert coverage_ratio(-10.0, 2.0) == pytest.approx(0.2)

    def test_coverage_ratio_zero_nominal(self):
        """Coverage ratio with zero nominal"""
        assert math.isinf(coverage_ratio(0.0, 1.0))
        assert coverage_ratio(0.0, 0.0) == 0.0

    def test_is_certain(self):
        """Test certainty check"""
        assert is_certain(10.0, 0.0) is True
        assert is_certain(10.0, 1e-11) is True
        assert is_certain(10.0, 1.0) is False

    def test_is_uncertain(self):
        """Test uncertainty check"""
        assert is_uncertain(10.0, 10.0, threshold=1.0) is True
        assert is_uncertain(10.0, 0.5, threshold=1.0) is False


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_large_values(self):
        """Operations handle large values"""
        n1, u1 = 1e10, 1e8
        n2, u2 = 1e9, 1e7

        n_add, u_add = add(n1, u1, n2, u2)
        assert math.isfinite(n_add)
        assert math.isfinite(u_add)

    def test_small_uncertainties(self):
        """Operations handle small uncertainties"""
        n1, u1 = 10.0, 1e-10
        n2, u2 = 20.0, 1e-10

        n_out, u_out = add(n1, u1, n2, u2)
        assert u_out >= 0
        assert u_out < 1e-9

    def test_mixed_signs(self):
        """Operations handle negative nominals"""
        n1, u1 = -10.0, 1.0
        n2, u2 = 5.0, 0.5

        n_out, u_out = add(n1, u1, n2, u2)
        assert n_out == -5.0
        assert u_out > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
