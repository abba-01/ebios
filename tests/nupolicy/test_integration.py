"""
test_integration.py

Integration tests for NUPolicy with NUGuard.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.nupolicy import Policy, PolicyConfig, PolicyManager
from src.nupolicy.integration import policy_to_monitor_config, create_monitor_from_policy
from src.nuguard import Monitor, EventLevel
from src.nuledger import Ledger, MemoryBackend
from src.nucore import add


class TestPolicyToMonitorConfig:
    """Tests for policy-to-monitor conversion"""

    def test_convert_simple_policy(self):
        """Test converting simple policy to MonitorConfig"""
        config = PolicyConfig(
            version="1.0.0",
            name="SimplePolicy",
            description="Simple test policy",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.05, 'level': 'warning'},
                {'type': 'InvariantRule', 'level': 'critical'}
            ],
            escalation={'halt_on_critical': False, 'auto_log': True}
        )

        policy = Policy(config=config)
        monitor_config = policy_to_monitor_config(policy)

        assert len(monitor_config.rules) == 2
        assert monitor_config.halt_on_critical is False
        assert monitor_config.auto_log is True

    def test_convert_coverage_rule(self):
        """Test CoverageRule conversion"""
        config = PolicyConfig(
            version="1.0.0",
            name="CoveragePolicy",
            description="Coverage rule test",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.1, 'level': 'error'}
            ]
        )

        policy = Policy(config=config)
        monitor_config = policy_to_monitor_config(policy)

        assert len(monitor_config.rules) == 1
        rule = monitor_config.rules[0]
        assert 'CoverageRule' in rule.name()
        assert rule.threshold == 0.1
        assert rule.level == EventLevel.ERROR

    def test_convert_threshold_rule(self):
        """Test ThresholdRule conversion"""
        config = PolicyConfig(
            version="1.0.0",
            name="ThresholdPolicy",
            description="Threshold rule test",
            rules=[
                {'type': 'ThresholdRule', 'max_uncertainty': 5.0, 'level': 'warning'}
            ]
        )

        policy = Policy(config=config)
        monitor_config = policy_to_monitor_config(policy)

        rule = monitor_config.rules[0]
        assert 'ThresholdRule' in rule.name()
        assert rule.max_uncertainty == 5.0

    def test_convert_composite_rule(self):
        """Test CompositeRule conversion"""
        config = PolicyConfig(
            version="1.0.0",
            name="CompositePolicy",
            description="Composite rule test",
            rules=[
                {
                    'type': 'CompositeRule',
                    'mode': 'and',
                    'rules': [
                        {'type': 'CoverageRule', 'threshold': 0.05},
                        {'type': 'ThresholdRule', 'max_uncertainty': 10.0}
                    ]
                }
            ]
        )

        policy = Policy(config=config)
        monitor_config = policy_to_monitor_config(policy)

        rule = monitor_config.rules[0]
        assert 'CompositeRule' in rule.name()
        assert rule.mode == 'and'
        assert len(rule.rules) == 2


class TestCreateMonitorFromPolicy:
    """Tests for creating Monitor from policy"""

    def test_create_monitor_basic(self):
        """Test basic monitor creation from policy"""
        config = PolicyConfig(
            version="1.0.0",
            name="MonitorPolicy",
            description="Monitor creation test",
            rules=[
                {'type': 'InvariantRule'}
            ]
        )

        policy = Policy(config=config)
        monitor = create_monitor_from_policy(policy)

        assert isinstance(monitor, Monitor)
        assert len(monitor.config.rules) == 1

    def test_create_monitor_with_ledger(self):
        """Test monitor creation with ledger integration"""
        config = PolicyConfig(
            version="1.0.0",
            name="LedgerPolicy",
            description="Ledger integration test",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.01}
            ],
            escalation={'auto_log': True}
        )

        policy = Policy(config=config)
        ledger = Ledger(backend=MemoryBackend())
        monitor = create_monitor_from_policy(policy, ledger=ledger)

        assert monitor.ledger is ledger
        assert monitor.config.auto_log is True


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_full_workflow_policy_to_monitoring(self):
        """Test complete workflow: policy creation -> monitoring -> audit"""
        # Create policy
        config = PolicyConfig(
            version="1.0.0",
            name="E2EPolicy",
            description="End-to-end test policy",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.05, 'level': 'warning'}
            ],
            escalation={'auto_log': True, 'halt_on_critical': False}
        )

        policy = Policy(config=config)

        # Create monitor with ledger
        ledger = Ledger(backend=MemoryBackend())
        monitor = create_monitor_from_policy(policy, ledger=ledger)

        # Good operation (should pass)
        n1, u1 = 10.0, 0.1
        n2, u2 = 20.0, 0.2
        n_out, u_out = add(n1, u1, n2, u2)

        event1 = monitor.check("add", [(n1, u1), (n2, u2)], (n_out, u_out))
        assert event1 is None  # No violation

        # Bad operation (high uncertainty)
        n3, u3 = 10.0, 5.0
        n4, u4 = 20.0, 10.0
        n_bad, u_bad = add(n3, u3, n4, u4)

        event2 = monitor.check("add", [(n3, u3), (n4, u4)], (n_bad, u_bad))
        assert event2 is not None  # Violation detected
        assert event2.level == EventLevel.WARNING

        # Check ledger recorded the violation
        assert len(ledger) == 1
        entry = ledger.get_all()[0]
        assert entry.operation == "guard_add"

    def test_policy_file_roundtrip(self):
        """Test saving policy to file and loading for monitoring"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create policy
            manager = PolicyManager(policy_dir=Path(tmpdir))
            policy = manager.create_policy(
                name="RoundtripPolicy",
                description="Test roundtrip",
                rules=[
                    {'type': 'InvariantRule', 'level': 'critical'},
                    {'type': 'CoverageRule', 'threshold': 0.1, 'level': 'warning'}
                ],
                escalation={'halt_on_critical': True}
            )

            # Save to file
            manager.save_policy(policy, "roundtrip")

            # Load from file
            loaded_policy = manager.load_policy("roundtrip")

            # Create monitor from loaded policy
            monitor = create_monitor_from_policy(loaded_policy)

            # Verify configuration
            assert len(monitor.config.rules) == 2
            assert monitor.config.halt_on_critical is True

    def test_multiple_policies_different_monitors(self):
        """Test multiple policies create different monitors"""
        # Strict policy
        strict_config = PolicyConfig(
            version="1.0.0",
            name="StrictPolicy",
            description="Strict monitoring",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.01, 'level': 'error'}
            ]
        )

        # Lenient policy
        lenient_config = PolicyConfig(
            version="1.0.0",
            name="LenientPolicy",
            description="Lenient monitoring",
            rules=[
                {'type': 'CoverageRule', 'threshold': 0.5, 'level': 'warning'}
            ]
        )

        strict_policy = Policy(config=strict_config)
        lenient_policy = Policy(config=lenient_config)

        strict_monitor = create_monitor_from_policy(strict_policy)
        lenient_monitor = create_monitor_from_policy(lenient_policy)

        # Same operation, different results
        n_out, u_out = (10.0, 0.5)  # coverage = 0.05

        strict_event = strict_monitor.check("test", [], (n_out, u_out))
        lenient_event = lenient_monitor.check("test", [], (n_out, u_out))

        assert strict_event is not None  # Fails strict (0.05 > 0.01)
        assert lenient_event is None  # Passes lenient (0.05 < 0.5)

    def test_policy_version_tracking(self):
        """Test policy version changes are tracked"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PolicyManager(policy_dir=Path(tmpdir))

            # Version 1
            policy_v1 = manager.create_policy(
                name="EvolvingPolicy",
                description="Version 1",
                rules=[
                    {'type': 'CoverageRule', 'threshold': 0.1}
                ]
            )
            policy_v1.config.version = "1.0.0"
            manager.save_policy(policy_v1, "evolving_v1")

            # Version 2 (stricter)
            policy_v2 = manager.create_policy(
                name="EvolvingPolicy",
                description="Version 2",
                rules=[
                    {'type': 'CoverageRule', 'threshold': 0.05}  # Stricter
                ]
            )
            policy_v2.config.version = "2.0.0"
            manager.save_policy(policy_v2, "evolving_v2")

            # Load both versions
            manager.load_policy("evolving_v1")
            manager.load_policy("evolving_v2")

            # Check history
            history = manager.get_history()
            assert len(history) == 2
            assert history[0]['version'] == "1.0.0"
            assert history[1]['version'] == "2.0.0"

    def test_invalid_policy_detection(self):
        """Test that invalid policies are rejected"""
        # Policy with invalid rule type
        config = PolicyConfig(
            version="1.0.0",
            name="InvalidPolicy",
            description="Has invalid rule",
            rules=[
                {'type': 'NonExistentRule', 'param': 123}
            ]
        )

        policy = Policy(config=config)

        # Should fail validation
        from src.nupolicy import PolicyValidationError
        with pytest.raises(PolicyValidationError):
            policy_to_monitor_config(policy, validate=True)

        # Should succeed if validation disabled
        monitor_config = policy_to_monitor_config(policy, validate=False)
        # Will have no rules since NonExistentRule is unknown (defaults not added when rules list non-empty)
        # Actually, MonitorConfig will add default rules if rules list is empty after conversion
        # Since NonExistentRule is ignored, the list will be empty, so defaults are added
        assert len(monitor_config.rules) == 2  # Default InvariantRule and CoverageRule added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
