"""
events.py

Event system for NUGuard violations and escalations.

Events represent detected issues during runtime monitoring.
Each event has a severity level and can trigger various handlers.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable
import time


class EventLevel(Enum):
    """Event severity levels"""
    INFO = "info"           # Informational, no action required
    WARNING = "warning"     # Potential issue, monitor closely
    ERROR = "error"         # Violation detected, escalate
    CRITICAL = "critical"   # Severe violation, immediate action

    def __lt__(self, other):
        """Allow level comparison"""
        levels = [EventLevel.INFO, EventLevel.WARNING, EventLevel.ERROR, EventLevel.CRITICAL]
        return levels.index(self) < levels.index(other)


@dataclass
class Event:
    """
    Monitoring event

    Represents a detected violation or notable condition during
    NUCore operation execution.

    Attributes:
        level: Event severity (INFO, WARNING, ERROR, CRITICAL)
        operation: Operation name that triggered event
        message: Human-readable description
        data: Additional context (coverage, threshold, etc.)
        timestamp: Unix timestamp when event occurred
        op_id: Ledger operation ID (if logged)
    """
    level: EventLevel
    operation: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    op_id: Optional[str] = None

    def __str__(self) -> str:
        """Human-readable representation"""
        return f"[{self.level.value.upper()}] {self.operation}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'level': self.level.value,
            'operation': self.operation,
            'message': self.message,
            'data': self.data,
            'timestamp': self.timestamp,
            'op_id': self.op_id
        }


class EventHandler:
    """
    Base class for event handlers

    Handlers process events when they occur. Subclass this to create
    custom handlers (e.g., logging, alerting, halting).

    Example:
        class LogHandler(EventHandler):
            def handle(self, event: Event) -> None:
                print(f"EVENT: {event}")
    """

    def handle(self, event: Event) -> None:
        """
        Process event

        Args:
            event: Event to handle

        Override this method in subclasses.
        """
        pass

    def should_handle(self, event: Event) -> bool:
        """
        Check if this handler should process event

        Args:
            event: Event to check

        Returns:
            True if handler should process this event

        Override to filter events by level, operation, etc.
        """
        return True


class LogHandler(EventHandler):
    """Handler that logs events to stdout"""

    def handle(self, event: Event) -> None:
        """Print event to stdout"""
        print(f"[{event.timestamp:.2f}] {event}")


class LedgerHandler(EventHandler):
    """Handler that logs events to NULedger"""

    def __init__(self, ledger):
        """
        Initialize with ledger

        Args:
            ledger: NULedger instance
        """
        self.ledger = ledger

    def handle(self, event: Event) -> None:
        """Log event to ledger"""
        # Extract operation details from event data
        inputs = event.data.get('inputs', [])
        output = event.data.get('output', (0.0, float('inf')))
        coverage = event.data.get('coverage', float('inf'))
        invariant_passed = event.level != EventLevel.CRITICAL

        # Append to ledger
        entry = self.ledger.append(
            operation=f"guard_{event.operation}",
            inputs=inputs,
            output=output,
            coverage=coverage,
            invariant_passed=invariant_passed
        )

        # Update event with op_id
        event.op_id = entry.op_id


class HaltHandler(EventHandler):
    """Handler that halts execution on CRITICAL events"""

    def should_handle(self, event: Event) -> bool:
        """Only handle CRITICAL events"""
        return event.level == EventLevel.CRITICAL

    def handle(self, event: Event) -> None:
        """Raise exception to halt execution"""
        raise RuntimeError(
            f"CRITICAL EVENT: {event.message}\n"
            f"Operation: {event.operation}\n"
            f"Data: {event.data}"
        )


class EventAggregator(EventHandler):
    """Handler that collects events for later analysis"""

    def __init__(self):
        """Initialize empty event list"""
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        """Collect event"""
        self.events.append(event)

    def get_events(self, level: Optional[EventLevel] = None) -> List[Event]:
        """
        Get collected events

        Args:
            level: Filter by level (None = all events)

        Returns:
            List of events
        """
        if level is None:
            return self.events.copy()
        return [e for e in self.events if e.level == level]

    def clear(self) -> None:
        """Clear collected events"""
        self.events.clear()

    def count(self, level: Optional[EventLevel] = None) -> int:
        """
        Count events

        Args:
            level: Filter by level (None = all events)

        Returns:
            Number of events
        """
        return len(self.get_events(level))


class ConditionalHandler(EventHandler):
    """Handler that wraps another handler with a condition"""

    def __init__(self, handler: EventHandler, condition: Callable[[Event], bool]):
        """
        Initialize with handler and condition

        Args:
            handler: Handler to wrap
            condition: Function that returns True if event should be handled
        """
        self.handler = handler
        self.condition = condition

    def should_handle(self, event: Event) -> bool:
        """Check condition"""
        return self.condition(event)

    def handle(self, event: Event) -> None:
        """Delegate to wrapped handler"""
        self.handler.handle(event)
