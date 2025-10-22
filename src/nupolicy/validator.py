"""
validator.py

Policy validation and schema checking.

Ensures policy files conform to the expected structure and contain
valid rule configurations for NUGuard.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class PolicyValidationError(Exception):
    """Raised when policy validation fails"""
    pass


@dataclass
class ValidationResult:
    """
    Result of policy validation

    Attributes:
        valid: Whether policy is valid
        errors: List of validation errors
        warnings: List of validation warnings
    """
    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self) -> bool:
        return self.valid


class PolicyValidator:
    """
    Validates policy structure and rule configurations

    Ensures policies conform to NUGuard requirements and best practices.
    """

    REQUIRED_FIELDS = ['version', 'name', 'description', 'rules']
    VALID_RULE_TYPES = [
        'CoverageRule',
        'InvariantRule',
        'ThresholdRule',
        'CompositeRule',
        'CustomRule'
    ]
    VALID_EVENT_LEVELS = ['info', 'warning', 'error', 'critical']
    VALID_ESCALATION_KEYS = ['halt_on_critical', 'auto_log']

    @classmethod
    def validate(cls, policy_dict: Dict[str, Any]) -> ValidationResult:
        """
        Validate policy structure

        Args:
            policy_dict: Policy dictionary to validate

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Check required fields in config
        config = policy_dict.get('config', {})

        for field in cls.REQUIRED_FIELDS:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate version format
        if 'version' in config:
            version = config['version']
            if not cls._is_valid_version(version):
                errors.append(f"Invalid version format: {version} (expected semantic versioning)")

        # Validate rules
        rules = config.get('rules', [])
        if not isinstance(rules, list):
            errors.append("'rules' must be a list")
        else:
            if len(rules) == 0:
                warnings.append("No rules defined (policy will not detect violations)")

            for i, rule in enumerate(rules):
                rule_errors = cls._validate_rule(rule, i)
                errors.extend(rule_errors)

        # Validate escalation settings
        escalation = config.get('escalation', {})
        if not isinstance(escalation, dict):
            errors.append("'escalation' must be a dictionary")
        else:
            for key in escalation:
                if key not in cls.VALID_ESCALATION_KEYS:
                    warnings.append(f"Unknown escalation key: {key}")

        # Validate metadata
        metadata = config.get('metadata', {})
        if not isinstance(metadata, dict):
            errors.append("'metadata' must be a dictionary")

        # Check for signature
        if policy_dict.get('signature') is None:
            warnings.append("Policy is not signed (signature verification disabled)")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def _is_valid_version(version: str) -> bool:
        """Check if version follows semantic versioning"""
        parts = version.split('.')
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)

    @classmethod
    def _validate_rule(cls, rule: Dict[str, Any], index: int) -> List[str]:
        """Validate individual rule configuration"""
        errors = []

        if not isinstance(rule, dict):
            errors.append(f"Rule {index}: must be a dictionary")
            return errors

        # Check rule type
        rule_type = rule.get('type')
        if rule_type is None:
            errors.append(f"Rule {index}: missing 'type' field")
        elif rule_type not in cls.VALID_RULE_TYPES:
            errors.append(f"Rule {index}: unknown rule type '{rule_type}'")

        # Validate specific rule types
        if rule_type == 'CoverageRule':
            if 'threshold' not in rule:
                errors.append(f"Rule {index}: CoverageRule missing 'threshold'")
            elif not isinstance(rule['threshold'], (int, float)):
                errors.append(f"Rule {index}: threshold must be numeric")
            elif rule['threshold'] < 0 or rule['threshold'] > 1:
                errors.append(f"Rule {index}: threshold must be between 0 and 1")

        elif rule_type == 'ThresholdRule':
            if 'max_uncertainty' not in rule:
                errors.append(f"Rule {index}: ThresholdRule missing 'max_uncertainty'")
            elif not isinstance(rule['max_uncertainty'], (int, float)):
                errors.append(f"Rule {index}: max_uncertainty must be numeric")
            elif rule['max_uncertainty'] < 0:
                errors.append(f"Rule {index}: max_uncertainty must be non-negative")

        elif rule_type == 'CompositeRule':
            if 'rules' not in rule:
                errors.append(f"Rule {index}: CompositeRule missing 'rules' list")
            if 'mode' in rule and rule['mode'] not in ['and', 'or']:
                errors.append(f"Rule {index}: mode must be 'and' or 'or'")

        # Validate event level
        if 'level' in rule:
            level = rule['level']
            if level not in cls.VALID_EVENT_LEVELS:
                errors.append(f"Rule {index}: invalid event level '{level}'")

        return errors

    @classmethod
    def validate_and_raise(cls, policy_dict: Dict[str, Any]) -> None:
        """
        Validate policy and raise exception if invalid

        Args:
            policy_dict: Policy dictionary to validate

        Raises:
            PolicyValidationError: If policy is invalid
        """
        result = cls.validate(policy_dict)

        if not result.valid:
            error_msg = "Policy validation failed:\n"
            error_msg += "\n".join(f"  - {err}" for err in result.errors)
            raise PolicyValidationError(error_msg)
