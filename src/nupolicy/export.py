"""
export.py

Policy export and serialization.

Supports multiple export formats for policy distribution and audit.
"""

import json
from enum import Enum
from typing import Dict, Any
from .policy import Policy


class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    JSON_COMPACT = "json_compact"
    SUMMARY = "summary"


class PolicyExporter:
    """
    Export policies in various formats

    Provides serialization for policy distribution, audit, and integration.
    """

    @staticmethod
    def export(policy: Policy, format: ExportFormat = ExportFormat.JSON) -> str:
        """
        Export policy in specified format

        Args:
            policy: Policy to export
            format: Export format

        Returns:
            Serialized policy string
        """
        if format == ExportFormat.JSON:
            return PolicyExporter._export_json(policy, indent=2)
        elif format == ExportFormat.JSON_COMPACT:
            return PolicyExporter._export_json(policy, indent=None)
        elif format == ExportFormat.SUMMARY:
            return PolicyExporter._export_summary(policy)
        else:
            raise ValueError(f"Unknown export format: {format}")

    @staticmethod
    def _export_json(policy: Policy, indent: int = None) -> str:
        """Export as JSON"""
        return json.dumps(policy.to_dict(), indent=indent)

    @staticmethod
    def _export_summary(policy: Policy) -> str:
        """Export as human-readable summary"""
        lines = []
        config = policy.config

        lines.append(f"Policy: {config.name}")
        lines.append(f"Version: {config.version}")
        lines.append(f"Description: {config.description}")
        lines.append(f"Hash: {policy.policy_hash}")
        lines.append("")

        lines.append("Rules:")
        for i, rule in enumerate(config.rules, 1):
            rule_type = rule.get('type', 'Unknown')
            level = rule.get('level', 'warning')
            lines.append(f"  {i}. {rule_type} (level: {level})")

            if rule_type == 'CoverageRule':
                threshold = rule.get('threshold', 'N/A')
                lines.append(f"     - threshold: {threshold}")
            elif rule_type == 'ThresholdRule':
                max_u = rule.get('max_uncertainty', 'N/A')
                lines.append(f"     - max_uncertainty: {max_u}")

        lines.append("")
        lines.append("Escalation:")
        escalation = config.escalation
        halt = escalation.get('halt_on_critical', False)
        auto_log = escalation.get('auto_log', True)
        lines.append(f"  - halt_on_critical: {halt}")
        lines.append(f"  - auto_log: {auto_log}")

        lines.append("")
        if policy.signature:
            lines.append("Signature: VERIFIED" if policy.verify_signature() else "Signature: INVALID")
        else:
            lines.append("Signature: UNSIGNED")

        return "\n".join(lines)

    @staticmethod
    def export_to_file(policy: Policy, path: str, format: ExportFormat = ExportFormat.JSON) -> None:
        """
        Export policy to file

        Args:
            policy: Policy to export
            path: Output file path
            format: Export format
        """
        content = PolicyExporter.export(policy, format)

        with open(path, 'w') as f:
            f.write(content)
