"""
models.py

Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class OperationType(str, Enum):
    """Supported NUCore operations"""
    ADD = "add"
    MULTIPLY = "multiply"
    COMPOSE = "compose"
    CATCH = "catch"
    FLIP = "flip"


class OperationRequest(BaseModel):
    """Request to execute NUCore operation"""
    operation: OperationType
    inputs: List[Tuple[float, float]] = Field(
        description="List of (nominal, uncertainty) pairs"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional operation parameters (e.g., lambda_margin for multiply)"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]],
            "params": None
        }
    })


class OperationResponse(BaseModel):
    """Response from NUCore operation"""
    result: Tuple[float, float] = Field(
        description="Output (nominal, uncertainty) pair"
    )
    coverage: float = Field(
        description="Coverage ratio u/|n|"
    )
    invariant_passed: bool = Field(
        description="Whether invariants were satisfied"
    )
    ledger_id: Optional[str] = Field(
        default=None,
        description="Ledger entry ID if logged"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "result": [30.0, 1.12],
            "coverage": 0.037,
            "invariant_passed": True,
            "ledger_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    })


class PolicyRequest(BaseModel):
    """Request to create or update policy"""
    name: str = Field(description="Unique policy name")
    description: str = Field(description="Policy description")
    version: str = Field(description="Semantic version (x.y.z)")
    rules: List[Dict[str, Any]] = Field(description="List of rule configurations")
    escalation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Escalation settings"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "ProductionPolicy",
            "description": "Production monitoring policy",
            "version": "1.0.0",
            "rules": [
                {"type": "InvariantRule"},
                {"type": "CoverageRule", "threshold": 0.1, "level": "warning"}
            ],
            "escalation": {"halt_on_critical": False, "auto_log": True},
            "metadata": {"author": "DevOps", "environment": "production"}
        }
    })


class PolicyResponse(BaseModel):
    """Response with policy information"""
    name: str
    version: str
    description: str
    policy_hash: str
    signed: bool
    rules_count: int

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "ProductionPolicy",
            "version": "1.0.0",
            "description": "Production monitoring policy",
            "policy_hash": "a3f5e8d9...",
            "signed": False,
            "rules_count": 2
        }
    })


class LedgerQuery(BaseModel):
    """Query parameters for ledger operations"""
    operation_id: Optional[str] = Field(
        default=None,
        description="Operation ID to trace"
    )
    limit: Optional[int] = Field(
        default=100,
        description="Maximum number of entries to return"
    )
    offset: Optional[int] = Field(
        default=0,
        description="Offset for pagination"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "operation_id": None,
            "limit": 100,
            "offset": 0
        }
    })


class LedgerEntryResponse(BaseModel):
    """Response with ledger entry information"""
    op_id: str
    timestamp: int
    operation: str
    inputs: List[Tuple[float, float]]
    output: Tuple[float, float]
    coverage: float
    invariant_passed: bool
    parent_id: Optional[str]
    signature: str

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "op_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": 1,
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]],
            "output": [30.0, 1.12],
            "coverage": 0.037,
            "invariant_passed": True,
            "parent_id": None,
            "signature": "base64_signature..."
        }
    })


class MonitorStatsResponse(BaseModel):
    """Response with monitor statistics"""
    total_events: int
    violations: int
    rules: List[str]
    handlers: int
    auto_log: bool
    halt_on_critical: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_events": 42,
            "violations": 3,
            "rules": ["InvariantRule", "CoverageRule(threshold=0.1)"],
            "handlers": 1,
            "auto_log": True,
            "halt_on_critical": False
        }
    })


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="Service status")
    version: str = Field(description="API version")
    layers: Dict[str, bool] = Field(description="Layer availability")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "version": "0.1.0",
            "layers": {
                "nucore": True,
                "nuledger": True,
                "nuguard": True,
                "nupolicy": True
            }
        }
    })


class AttestationRequest(BaseModel):
    """Request for system attestation"""
    attestation_type: str = Field(
        description="Type of attestation (policy, operation, ledger)"
    )
    target_id: Optional[str] = Field(
        default=None,
        description="ID of target to attest (policy name, op_id, etc.)"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "attestation_type": "policy",
            "target_id": "ProductionPolicy"
        }
    })


class AttestationResponse(BaseModel):
    """Attestation response with cryptographic proof"""
    attestation_type: str
    target_id: str
    timestamp: str
    hash: str
    signature: str
    verified: bool

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "attestation_type": "policy",
            "target_id": "ProductionPolicy",
            "timestamp": "2025-10-20T00:00:00Z",
            "hash": "a3f5e8d9...",
            "signature": "base64_signature...",
            "verified": True
        }
    })
