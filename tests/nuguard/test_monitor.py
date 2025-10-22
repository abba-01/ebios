"""
test_monitor.py

Comprehensive tests for NUGuard runtime monitoring.
"""

import pytest
from src.nuguard import (
    Monitor, MonitorConfig,
    Event, EventLevel, EventHandler, EventAggregator, LogHandler,
    Rule, CoverageRule, InvariantRule, ThresholdRule, CompositeRule, CustomRule
)
from src.nuledger import Ledger, MemoryBackend


class TestEvents:
    """Tests for Event and EventLevel"""

    def test_event_creation(self):
        """Test basic event creation"""
        event = Event(
            level=EventLevel.WARNING,
            operation="add",
            message="Coverage exceeded",
            data={'coverage': 0.15}
        )

        assert event.level == EventLevel.WARNING
        assert event.operation == "add"
        assert event.message == "Coverage exceeded"
        assert event.data['coverage'] == 0.15

    def test_event_level_comparison(self):
        """Test event level ordering"""
        assert EventLevel.INFO < EventLevel.WARNING
        assert EventLevel.WARNING < EventLevel.ERROR
        assert EventLevel.ERROR < EventLevel.CRITICAL

    def test_event_to_dict(self):
        """Test event serialization"""
        event = Event(
            level=EventLevel.ERROR,
            operation="multiply",
            message="Test",
            data={'test': 123}
        )

        d = event.to_dict()
        assert d['level'] == 'error'
        assert d['operation'] == 'multiply'
        assert d['message'] == 'Test'
        assert d['data']['test'] == 123

    def test_event_str(self):
        """Test event string representation"""
        event = Event(
            level=EventLevel.CRITICAL,
            operation="divide",
            message="Invariant violation"
        )

        s = str(event)
        assert "CRITICAL" in s
        assert "divide" in s
        assert "Invariant violation" in s


class TestEventHandlers:
    """Tests for event handlers"""

    def test_event_aggregator(self):
        """Test EventAggregator collects events"""
        handler = EventAggregator()

        e1 = Event(EventLevel.INFO, "op1", "msg1")
        e2 = Event(EventLevel.WARNING, "op2", "msg2")
        e3 = Event(EventLevel.ERROR, "op3", "msg3")

        handler.handle(e1)
        handler.handle(e2)
        handler.handle(e3)

        assert handler.count() == 3
        assert handler.count(EventLevel.WARNING) == 1
        assert handler.count(EventLevel.ERROR) == 1

    def test_event_aggregator_filter(self):
        """Test filtering events by level"""
        handler = EventAggregator()

        handler.handle(Event(EventLevel.INFO, "op", "msg"))
        handler.handle(Event(EventLevel.WARNING, "op", "msg"))
        handler.handle(Event(EventLevel.WARNING, "op", "msg"))
        handler.handle(Event(EventLevel.ERROR, "op", "msg"))

        warnings = handler.get_events(EventLevel.WARNING)
        assert len(warnings) == 2

    def test_event_aggregator_clear(self):
        """Test clearing aggregator"""
        handler = EventAggregator()

        handler.handle(Event(EventLevel.INFO, "op", "msg"))
        assert handler.count() == 1

        handler.clear()
        assert handler.count() == 0


class TestRules:
    """Tests for monitoring rules"""

    def test_coverage_rule_pass(self):
        """Test coverage rule with passing operation"""
        rule = CoverageRule(threshold=0.1)

        event = rule.check(
            "add",
            [(10.0, 0.5), (20.0, 1.0)],
            (30.0, 1.12)  # coverage = 1.12/30 = 0.037 < 0.1
        )

        assert event is None  # No violation

    def test_coverage_rule_fail(self):
        """Test coverage rule with failing operation"""
        rule = CoverageRule(threshold=0.1)

        event = rule.check(
            "add",
            [(10.0, 5.0), (20.0, 10.0)],
            (30.0, 15.5)  # coverage = 15.5/30 = 0.517 > 0.1
        )

        assert event is not None
        assert event.level == EventLevel.WARNING
        assert "Coverage" in event.message

    def test_coverage_rule_zero_nominal(self):
        """Test coverage rule with zero nominal"""
        rule = CoverageRule(threshold=0.1)

        event = rule.check(
            "add",
            [(1.0, 1.0), (-1.0, 1.0)],
            (0.0, 1.4)  # n=0, u>0 → infinite coverage
        )

        assert event is not None  # Should trigger
        assert event.data['coverage'] == float('inf')

    def test_invariant_rule_negative_uncertainty(self):
        """Test invariant rule detects negative uncertainty"""
        rule = InvariantRule()

        event = rule.check(
            "invalid_op",
            [(10.0, 0.5)],
            (10.0, -0.5)  # INVALID: negative uncertainty
        )

        assert event is not None
        assert event.level == EventLevel.CRITICAL
        assert "negative uncertainty" in event.message.lower()

    def test_invariant_rule_nan(self):
        """Test invariant rule detects NaN"""
        rule = InvariantRule()

        event = rule.check(
            "invalid_op",
            [(10.0, 0.5)],
            (float('nan'), 0.5)  # INVALID: NaN
        )

        assert event is not None
        assert event.level == EventLevel.CRITICAL
        assert "NaN" in event.message

    def test_invariant_rule_infinite_nominal(self):
        """Test invariant rule detects infinite nominal"""
        rule = InvariantRule()

        event = rule.check(
            "invalid_op",
            [(10.0, 0.5)],
            (float('inf'), 0.5)  # INVALID: infinite nominal
        )

        assert event is not None
        assert event.level == EventLevel.CRITICAL
        assert "Infinite nominal" in event.message

    def test_invariant_rule_valid_infinite_uncertainty(self):
        """Test invariant rule allows infinite uncertainty"""
        rule = InvariantRule()

        event = rule.check(
            "catch",
            [(10.0, 0.5)],
            (0.0, float('inf'))  # VALID: infinite uncertainty (epistemic collapse)
        )

        assert event is None  # No violation

    def test_threshold_rule_pass(self):
        """Test threshold rule with passing operation"""
        rule = ThresholdRule(max_uncertainty=10.0)

        event = rule.check(
            "add",
            [(10.0, 2.0)],
            (10.0, 5.0)  # u=5.0 < 10.0
        )

        assert event is None

    def test_threshold_rule_fail(self):
        """Test threshold rule with failing operation"""
        rule = ThresholdRule(max_uncertainty=10.0)

        event = rule.check(
            "multiply",
            [(10.0, 5.0)],
            (100.0, 50.0)  # u=50.0 > 10.0
        )

        assert event is not None
        assert event.level == EventLevel.WARNING
        assert "exceeds threshold" in event.message.lower()

    def test_composite_rule_or_mode(self):
        """Test composite rule in OR mode"""
        rule = CompositeRule([
            CoverageRule(threshold=0.05),
            ThresholdRule(max_uncertainty=5.0)
        ], mode='or')

        # Violates coverage but not threshold
        event = rule.check(
            "add",
            [],
            (10.0, 1.5)  # coverage=0.15 > 0.05, u=1.5 < 5.0
        )

        assert event is not None  # OR: one violation triggers

    def test_composite_rule_and_mode(self):
        """Test composite rule in AND mode"""
        rule = CompositeRule([
            CoverageRule(threshold=0.05),
            ThresholdRule(max_uncertainty=1.0)
        ], mode='and')

        # Violates coverage but not threshold
        event = rule.check(
            "add",
            [],
            (10.0, 0.8)  # coverage=0.08 > 0.05, u=0.8 < 1.0
        )

        assert event is None  # AND: both must violate

        # Violates both
        event2 = rule.check(
            "add",
            [],
            (10.0, 1.5)  # coverage=0.15 > 0.05, u=1.5 > 1.0
        )

        assert event2 is not None  # AND: both violate

    def test_custom_rule(self):
        """Test custom rule with lambda"""
        def check_large_value(op, inputs, output, **kwargs):
            n, u = output
            if n > 1000:
                return Event(EventLevel.INFO, op, f"Large value: n={n}")
            return None

        rule = CustomRule("LargeValueRule", check_large_value)

        event = rule.check("test", [], (2000.0, 10.0))
        assert event is not None
        assert "Large value" in event.message


class TestMonitor:
    """Tests for Monitor core functionality"""

    def test_monitor_creation_default_config(self):
        """Test monitor with default configuration"""
        monitor = Monitor()

        assert len(monitor.config.rules) > 0  # Has default rules
        assert monitor.event_count == 0
        assert monitor.violation_count == 0

    def test_monitor_check_pass(self):
        """Test monitoring passing operation"""
        monitor = Monitor()

        event = monitor.check(
            "add",
            [(10.0, 0.5), (20.0, 1.0)],
            (30.0, 1.12)  # Good coverage
        )

        assert event is None

    def test_monitor_check_fail(self):
        """Test monitoring failing operation"""
        config = MonitorConfig(rules=[CoverageRule(threshold=0.01)])
        monitor = Monitor(config)

        event = monitor.check(
            "add",
            [(10.0, 5.0)],
            (10.0, 5.0)  # coverage=0.5 > 0.01
        )

        assert event is not None
        assert monitor.event_count == 1

    def test_monitor_bool_interface(self):
        """Test monitor() returns boolean"""
        monitor = Monitor()

        # Passing
        passed = monitor.monitor(
            "add",
            [(10.0, 0.5)],
            (10.0, 0.5)  # Good
        )
        assert passed is True

        # Failing
        config = MonitorConfig(rules=[CoverageRule(threshold=0.01)])
        monitor2 = Monitor(config)

        failed = monitor2.monitor(
            "add",
            [(10.0, 5.0)],
            (10.0, 5.0)  # Bad
        )
        assert failed is False

    def test_monitor_with_handler(self):
        """Test monitor calls handlers"""
        aggregator = EventAggregator()
        config = MonitorConfig(
            rules=[CoverageRule(threshold=0.01)],
            handlers=[aggregator]
        )
        monitor = Monitor(config)

        monitor.check("add", [], (10.0, 5.0))  # Triggers event

        assert aggregator.count() == 1

    def test_monitor_with_ledger(self):
        """Test monitor logs to ledger"""
        ledger = Ledger(backend=MemoryBackend())
        config = MonitorConfig(
            rules=[CoverageRule(threshold=0.01)],
            auto_log=True
        )
        monitor = Monitor(config, ledger=ledger)

        monitor.check("add", [(10.0, 5.0)], (10.0, 5.0))  # Triggers event

        assert len(ledger) == 1  # Event logged

    def test_monitor_stats(self):
        """Test monitor statistics"""
        monitor = Monitor()

        stats = monitor.stats()
        assert stats['total_events'] == 0
        assert stats['violations'] == 0
        assert len(stats['rules']) > 0

        # Trigger ERROR event (violations counted for ERROR/CRITICAL)
        config = MonitorConfig(rules=[CoverageRule(threshold=0.01, level=EventLevel.ERROR)])
        monitor2 = Monitor(config)
        monitor2.check("add", [], (10.0, 5.0))

        stats2 = monitor2.stats()
        assert stats2['total_events'] == 1
        assert stats2['violations'] == 1

    def test_monitor_reset(self):
        """Test monitor statistics reset"""
        config = MonitorConfig(rules=[CoverageRule(threshold=0.01)])
        monitor = Monitor(config)

        monitor.check("add", [], (10.0, 5.0))  # Trigger
        assert monitor.event_count == 1

        monitor.reset()
        assert monitor.event_count == 0

    def test_monitor_add_rule_dynamically(self):
        """Test adding rules at runtime"""
        # Create config with no default rules by disabling auto-add
        config = MonitorConfig()
        config.rules = []  # Clear defaults after init
        monitor = Monitor(config)

        assert len(monitor.config.rules) == 0

        monitor.add_rule(CoverageRule(threshold=0.05))
        assert len(monitor.config.rules) == 1

    def test_monitor_escalate_manual(self):
        """Test manual event escalation"""
        aggregator = EventAggregator()
        config = MonitorConfig(handlers=[aggregator])
        monitor = Monitor(config)

        event = Event(EventLevel.ERROR, "manual", "Manual escalation")
        monitor.escalate(event)

        assert aggregator.count() == 1
        assert monitor.event_count == 1


class TestIntegration:
    """Integration tests with NUCore and NULedger"""

    def test_full_monitoring_pipeline(self):
        """Test complete monitoring workflow"""
        from src.nucore import add

        # Setup
        ledger = Ledger(backend=MemoryBackend())
        aggregator = EventAggregator()
        config = MonitorConfig(
            rules=[CoverageRule(threshold=0.05)],
            handlers=[aggregator],
            auto_log=True
        )
        monitor = Monitor(config, ledger=ledger)

        # Good operation
        n1, u1 = 10.0, 0.1
        n2, u2 = 20.0, 0.2
        n_out, u_out = add(n1, u1, n2, u2)

        event1 = monitor.check("add", [(n1, u1), (n2, u2)], (n_out, u_out))
        assert event1 is None  # No violation

        # Bad operation (artificially high uncertainty)
        n3, u3 = 10.0, 5.0
        n4, u4 = 20.0, 10.0
        n_bad, u_bad = add(n3, u3, n4, u4)

        event2 = monitor.check("add", [(n3, u3), (n4, u4)], (n_bad, u_bad))
        assert event2 is not None  # Violation detected

        # Check aggregator
        assert aggregator.count() == 1
        assert aggregator.count(EventLevel.WARNING) == 1

        # Check ledger
        assert len(ledger) == 1  # One violation logged

    def test_invariant_violation_detection(self):
        """Test critical invariant violations halt if configured"""
        config = MonitorConfig(
            rules=[InvariantRule()],
            halt_on_critical=True
        )
        monitor = Monitor(config)

        # Should raise exception on critical event
        with pytest.raises(RuntimeError):
            monitor.check("bad_op", [], (10.0, -1.0))  # Negative uncertainty

    def test_multiple_rules_cascade(self):
        """Test multiple rules triggering on same operation"""
        config = MonitorConfig(rules=[
            CoverageRule(threshold=0.05),
            ThresholdRule(max_uncertainty=5.0)
        ])
        monitor = Monitor(config)

        # Violates both rules
        event = monitor.check("test", [], (10.0, 10.0))  # coverage=1.0, u=10.0

        assert event is not None  # First rule triggers
        assert monitor.event_count == 1  # Only first violation returned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
