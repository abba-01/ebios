"""
integration.py

NUGuard integration for policy-driven monitoring.

Converts policy files into NUGuard Monitor configurations.
"""

from typing import Optional
from .policy import Policy
from .validator import PolicyValidator, PolicyValidationError


def policy_to_monitor_config(policy: Policy, validate: bool = True):
    """
    Convert policy to NUGuard MonitorConfig

    Args:
        policy: Policy to convert
        validate: Validate policy before conversion

    Returns:
        MonitorConfig object

    Raises:
        PolicyValidationError: If policy is invalid
    """
    # Import here to avoid circular dependency
    from src.nuguard import MonitorConfig, CoverageRule, InvariantRule, ThresholdRule, CompositeRule, EventLevel

    # Validate policy if requested
    if validate:
        PolicyValidator.validate_and_raise(policy.to_dict())

    config = policy.config
    rules = []

    # Convert each rule
    for rule_dict in config.rules:
        rule_type = rule_dict.get('type')
        level_str = rule_dict.get('level', 'warning')
        level = EventLevel[level_str.upper()]

        if rule_type == 'CoverageRule':
            threshold = rule_dict.get('threshold', 0.1)
            rules.append(CoverageRule(threshold=threshold, level=level))

        elif rule_type == 'InvariantRule':
            rules.append(InvariantRule())  # InvariantRule always CRITICAL, no level param

        elif rule_type == 'ThresholdRule':
            max_uncertainty = rule_dict.get('max_uncertainty', 10.0)
            rules.append(ThresholdRule(max_uncertainty=max_uncertainty, level=level))

        elif rule_type == 'CompositeRule':
            # Recursively build composite rules
            sub_rules = []
            for sub_rule_dict in rule_dict.get('rules', []):
                sub_type = sub_rule_dict.get('type')
                sub_level_str = sub_rule_dict.get('level', 'warning')
                sub_level = EventLevel[sub_level_str.upper()]

                if sub_type == 'CoverageRule':
                    sub_rules.append(CoverageRule(
                        threshold=sub_rule_dict.get('threshold', 0.1),
                        level=sub_level
                    ))
                elif sub_type == 'ThresholdRule':
                    sub_rules.append(ThresholdRule(
                        max_uncertainty=sub_rule_dict.get('max_uncertainty', 10.0),
                        level=sub_level
                    ))

            mode = rule_dict.get('mode', 'or')
            rules.append(CompositeRule(sub_rules, mode=mode))

    # Get escalation settings
    escalation = config.escalation
    halt_on_critical = escalation.get('halt_on_critical', False)
    auto_log = escalation.get('auto_log', True)

    # Create MonitorConfig
    return MonitorConfig(
        rules=rules,
        halt_on_critical=halt_on_critical,
        auto_log=auto_log
    )


def create_monitor_from_policy(policy: Policy, ledger=None, validate: bool = True):
    """
    Create NUGuard Monitor from policy

    Args:
        policy: Policy to use
        ledger: Optional NULedger instance
        validate: Validate policy before conversion

    Returns:
        Monitor object configured per policy
    """
    from src.nuguard import Monitor

    monitor_config = policy_to_monitor_config(policy, validate=validate)
    return Monitor(config=monitor_config, ledger=ledger)
