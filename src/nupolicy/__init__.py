"""
NUPolicy: Policy & Governance for eBIOS

Layer 5 of eBIOS: Policy file management and governance interfaces.

"Policy is data, not code."

This module provides:
- Policy file loading and validation
- Cryptographic signature verification
- NUGuard rule configuration from policies
- Policy versioning and audit trail
- Export and introspection APIs

Key Features:
- JSON/YAML policy format
- Ed25519 signature verification
- Immutable policy versioning
- Complete integration with NUGuard
- Governance API endpoints
"""

from .policy import Policy, PolicyConfig, PolicyLoader, PolicyManager
from .validator import PolicyValidator, PolicyValidationError
from .export import PolicyExporter, ExportFormat

__all__ = [
    'Policy',
    'PolicyConfig',
    'PolicyLoader',
    'PolicyManager',
    'PolicyValidator',
    'PolicyValidationError',
    'PolicyExporter',
    'ExportFormat',
]

__version__ = '0.1.0'
