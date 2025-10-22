"""
monitor.py

NUGuard runtime monitoring system.

The Monitor watches NUCore operations in real-time, checking for
violations and escalating events through configured handlers.

"Failure is allowed. Lying about failure is not."
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .rules import Rule, CoverageRule, InvariantRule
from .events import Event, EventHandler, EventLevel


@dataclass
class MonitorConfig:
    """
    Configuration for Monitor

    Attributes:
        rules: List of rules to check
        handlers: List of event handlers
        auto_log: Automatically log to ledger (if provided)
        halt_on_critical: Halt execution on CRITICAL events
    """
    rules: List[Rule] = field(default_factory=list)
    handlers: List[EventHandler] = field(default_factory=list)
    auto_log: bool = True
    halt_on_critical: bool = False

    def __post_init__(self):
        """Add default rules if none provided"""
        # Only add defaults if rules list was not explicitly provided
        # (Check if it's the default empty list from field factory)
        if len(self.rules) == 0:
            # Default: check invariants and 10% coverage
            self.rules = [
                InvariantRule(),
                CoverageRule(threshold=0.1, level=EventLevel.WARNING)
            ]


class Monitor:
    """
    Runtime monitoring system for NUCore operations

    The Monitor checks operations against configured rules and
    escalates events through registered handlers.

    Example:
        from nuguard import Monitor, MonitorConfig, CoverageRule
        from nuledger import Ledger

        ledger = Ledger()
        config = MonitorConfig(
            rules=[CoverageRule(threshold=0.05)],
            auto_log=True
        )
        monitor = Monitor(config, ledger=ledger)

        # Monitor an operation
        event = monitor.check(
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12)
        )

        if event:
            print(f"Violation detected: {event}")
    """

    def __init__(self, config: Optional[MonitorConfig] = None, ledger=None):
        """
        Initialize monitor

        Args:
            config: Monitor configuration (uses defaults if None)
            ledger: Optional NULedger instance for event logging
        """
        self.config = config or MonitorConfig()
        self.ledger = ledger
        self.event_count = 0
        self.violation_count = 0

    def check(
        self,
        operation: str,
        inputs: List[tuple],
        output: tuple,
        **kwargs
    ) -> Optional[Event]:
        """
        Check operation against all rules

        Args:
            operation: Operation name (add, multiply, etc.)
            inputs: Input N/U pairs
            output: Output N/U pair
            **kwargs: Additional context for rules

        Returns:
            First event detected, or None if no violations

        Side Effects:
            - Increments event_count if event generated
            - Calls all registered handlers
            - Optionally logs to ledger
        """
        # Check all rules
        for rule in self.config.rules:
            event = rule.check(operation, inputs, output, **kwargs)

            if event is not None:
                self.event_count += 1

                if event.level in (EventLevel.ERROR, EventLevel.CRITICAL):
                    self.violation_count += 1

                # Process through handlers
                self._handle_event(event)

                # Return first violation
                return event

        return None

    def monitor(
        self,
        operation: str,
        inputs: List[tuple],
        output: tuple,
        **kwargs
    ) -> bool:
        """
        Monitor operation and return pass/fail

        Args:
            operation: Operation name
            inputs: Input N/U pairs
            output: Output N/U pair
            **kwargs: Additional context

        Returns:
            True if no violations, False otherwise
        """
        event = self.check(operation, inputs, output, **kwargs)
        return event is None

    def escalate(self, event: Event) -> None:
        """
        Manually escalate an event

        Args:
            event: Event to escalate

        Use this to manually trigger event processing without
        running rule checks.
        """
        self.event_count += 1

        if event.level in (EventLevel.ERROR, EventLevel.CRITICAL):
            self.violation_count += 1

        self._handle_event(event)

    def _handle_event(self, event: Event) -> None:
        """
        Process event through all handlers

        Args:
            event: Event to process
        """
        # Auto-log to ledger
        if self.config.auto_log and self.ledger is not None:
            self._log_to_ledger(event)

        # Run handlers
        for handler in self.config.handlers:
            if handler.should_handle(event):
                try:
                    handler.handle(event)
                except Exception as e:
                    # Handler failure shouldn't break monitoring
                    print(f"Handler {handler.__class__.__name__} failed: {e}")

        # Halt on critical if configured
        if self.config.halt_on_critical and event.level == EventLevel.CRITICAL:
            raise RuntimeError(
                f"CRITICAL EVENT: {event.message}\n"
                f"Halting execution as configured."
            )

    def _log_to_ledger(self, event: Event) -> None:
        """
        Log event to NULedger

        Args:
            event: Event to log
        """
        if self.ledger is None:
            return

        # Extract data
        inputs = event.data.get('inputs', [])
        output = event.data.get('output', (0.0, float('inf')))
        coverage = event.data.get('coverage', float('inf'))

        # Determine if invariants passed
        invariant_passed = event.level != EventLevel.CRITICAL

        # Log to ledger
        entry = self.ledger.append(
            operation=f"guard_{event.operation}",
            inputs=inputs,
            output=output,
            coverage=coverage,
            invariant_passed=invariant_passed
        )

        # Update event with ledger ID
        event.op_id = entry.op_id

    def stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics

        Returns:
            Dictionary with event counts and configuration
        """
        return {
            'total_events': self.event_count,
            'violations': self.violation_count,
            'rules': [r.name() for r in self.config.rules],
            'handlers': len(self.config.handlers),
            'auto_log': self.config.auto_log,
            'halt_on_critical': self.config.halt_on_critical
        }

    def reset(self) -> None:
        """Reset monitoring statistics"""
        self.event_count = 0
        self.violation_count = 0

    def add_rule(self, rule: Rule) -> None:
        """
        Add rule to monitoring

        Args:
            rule: Rule to add
        """
        self.config.rules.append(rule)

    def add_handler(self, handler: EventHandler) -> None:
        """
        Add event handler

        Args:
            handler: Handler to add
        """
        self.config.handlers.append(handler)

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"Monitor(rules={len(self.config.rules)}, "
            f"handlers={len(self.config.handlers)}, "
            f"events={self.event_count}, "
            f"violations={self.violation_count})"
        )
