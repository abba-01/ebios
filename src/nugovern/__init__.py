"""
NUGovern: HTTP API for eBIOS Governance

Layer 6 of eBIOS: REST API for governance, policy management, and attestation.

"Governance through transparent interfaces."

This module provides HTTP endpoints for all eBIOS layers, enabling
remote policy management, operation execution, audit queries, and
certification attestation.

Key Features:
- RESTful API for all eBIOS operations
- Policy management endpoints
- Ledger query and verification
- Monitoring statistics and events
- Attestation and certification
- OpenAPI/Swagger documentation
"""

from .server import create_app, NUGovernServer
from .models import OperationRequest, OperationResponse, PolicyRequest, LedgerQuery

__all__ = [
    'create_app',
    'NUGovernServer',
    'OperationRequest',
    'OperationResponse',
    'PolicyRequest',
    'LedgerQuery',
]

__version__ = '0.1.0'
