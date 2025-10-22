"""
rules.py

Violation detection rules for NUGuard.

Rules define conditions that trigger monitoring events.
Each rule checks a specific property (coverage, invariants, etc.)
and generates events when violations are detected.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .events import Event, EventLevel


class Rule(ABC):
    """
    Base class for monitoring rules

    Rules check properties of NUCore operations and generate
    events when violations are detected.

    Subclass this to create custom rules.
    """

    @abstractmethod
    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """
        Check if operation violates rule

        Args:
            operation: Operation name (add, multiply, etc.)
            inputs: Input N/U pairs
            output: Output N/U pair
            **kwargs: Additional context

        Returns:
            Event if violation detected, None otherwise
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Return rule name"""
        pass


class CoverageRule(Rule):
    """
    Rule that checks coverage ratio (u/|n|)

    Triggers events when uncertainty exceeds threshold relative to nominal value.

    Example:
        rule = CoverageRule(threshold=0.1)  # 10% coverage
        event = rule.check("add", [...], (100.0, 15.0))  # 15% coverage → WARNING
    """

    def __init__(self, threshold: float = 0.1, level: EventLevel = EventLevel.WARNING):
        """
        Initialize coverage rule

        Args:
            threshold: Maximum acceptable coverage ratio (u/|n|)
            level: Event level to generate on violation
        """
        self.threshold = threshold
        self.level = level

    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """Check coverage ratio"""
        n_out, u_out = output

        # Compute coverage
        if n_out == 0:
            coverage = float('inf') if u_out > 0 else 0.0
        else:
            coverage = u_out / abs(n_out)

        # Check threshold
        if coverage > self.threshold:
            return Event(
                level=self.level,
                operation=operation,
                message=f"Coverage {coverage:.4f} exceeds threshold {self.threshold:.4f}",
                data={
                    'coverage': coverage,
                    'threshold': self.threshold,
                    'inputs': inputs,
                    'output': output
                }
            )

        return None

    def name(self) -> str:
        """Return rule name"""
        return f"CoverageRule(threshold={self.threshold})"


class InvariantRule(Rule):
    """
    Rule that checks NUCore invariants

    Triggers CRITICAL events when invariants are violated:
    - Negative uncertainty (u < 0)
    - NaN values
    - Infinite nominal values

    These violations should never occur in correct NUCore implementations.
    """

    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """Check invariants"""
        n_out, u_out = output

        # Check for negative uncertainty
        if u_out < 0:
            return Event(
                level=EventLevel.CRITICAL,
                operation=operation,
                message=f"INVARIANT VIOLATION: Negative uncertainty u={u_out}",
                data={
                    'violation': 'negative_uncertainty',
                    'inputs': inputs,
                    'output': output
                }
            )

        # Check for NaN
        if n_out != n_out or u_out != u_out:  # NaN check
            return Event(
                level=EventLevel.CRITICAL,
                operation=operation,
                message="INVARIANT VIOLATION: NaN detected",
                data={
                    'violation': 'nan',
                    'inputs': inputs,
                    'output': output
                }
            )

        # Check for infinite nominal
        if abs(n_out) == float('inf'):
            return Event(
                level=EventLevel.CRITICAL,
                operation=operation,
                message="INVARIANT VIOLATION: Infinite nominal value",
                data={
                    'violation': 'infinite_nominal',
                    'inputs': inputs,
                    'output': output
                }
            )

        return None

    def name(self) -> str:
        """Return rule name"""
        return "InvariantRule"


class ThresholdRule(Rule):
    """
    Rule that checks absolute uncertainty threshold

    Triggers events when uncertainty exceeds absolute value
    (independent of nominal value).

    Example:
        rule = ThresholdRule(max_uncertainty=10.0)
        event = rule.check("add", [...], (100.0, 15.0))  # u=15 > 10 → WARNING
    """

    def __init__(self, max_uncertainty: float, level: EventLevel = EventLevel.WARNING):
        """
        Initialize threshold rule

        Args:
            max_uncertainty: Maximum acceptable uncertainty
            level: Event level to generate on violation
        """
        self.max_uncertainty = max_uncertainty
        self.level = level

    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """Check absolute uncertainty"""
        n_out, u_out = output

        if u_out > self.max_uncertainty:
            return Event(
                level=self.level,
                operation=operation,
                message=f"Uncertainty {u_out:.4f} exceeds threshold {self.max_uncertainty:.4f}",
                data={
                    'uncertainty': u_out,
                    'threshold': self.max_uncertainty,
                    'inputs': inputs,
                    'output': output
                }
            )

        return None

    def name(self) -> str:
        """Return rule name"""
        return f"ThresholdRule(max={self.max_uncertainty})"


class CompositeRule(Rule):
    """
    Rule that combines multiple rules with AND/OR logic

    Example:
        rule = CompositeRule([
            CoverageRule(0.1),
            ThresholdRule(5.0)
        ], mode='or')  # Trigger if ANY rule violates
    """

    def __init__(self, rules: List[Rule], mode: str = 'or'):
        """
        Initialize composite rule

        Args:
            rules: List of rules to combine
            mode: 'or' (any violation) or 'and' (all violations)
        """
        self.rules = rules
        self.mode = mode.lower()

        if self.mode not in ('or', 'and'):
            raise ValueError("mode must be 'or' or 'and'")

    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """Check all rules"""
        events = []

        for rule in self.rules:
            event = rule.check(operation, inputs, output, **kwargs)
            if event is not None:
                events.append(event)

        # OR mode: return first violation
        if self.mode == 'or' and events:
            return events[0]

        # AND mode: return only if all rules violated
        if self.mode == 'and' and len(events) == len(self.rules):
            # Combine messages
            messages = [e.message for e in events]
            return Event(
                level=max(e.level for e in events),
                operation=operation,
                message=f"Multiple violations: {'; '.join(messages)}",
                data={
                    'violations': [e.to_dict() for e in events]
                }
            )

        return None

    def name(self) -> str:
        """Return rule name"""
        rule_names = [r.name() for r in self.rules]
        return f"CompositeRule({self.mode}: {', '.join(rule_names)})"


class CustomRule(Rule):
    """
    Rule with custom check function

    Allows defining rules without subclassing.

    Example:
        def check_fn(op, inputs, output, **kwargs):
            n, u = output
            if n > 1000:
                return Event(EventLevel.INFO, op, "Large value detected")
            return None

        rule = CustomRule("LargeValueRule", check_fn)
    """

    def __init__(self, rule_name: str, check_fn):
        """
        Initialize custom rule

        Args:
            rule_name: Name for this rule
            check_fn: Function(operation, inputs, output, **kwargs) -> Optional[Event]
        """
        self.rule_name = rule_name
        self.check_fn = check_fn

    def check(self, operation: str, inputs: List[tuple], output: tuple,
              **kwargs) -> Optional[Event]:
        """Delegate to custom function"""
        return self.check_fn(operation, inputs, output, **kwargs)

    def name(self) -> str:
        """Return rule name"""
        return self.rule_name
