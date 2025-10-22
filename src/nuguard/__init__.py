"""
NUGuard: Runtime Monitoring for eBIOS

Layer 4 of eBIOS: Real-time monitoring and violation detection.

"Failure is allowed. Lying about failure is not."

This module provides runtime monitoring of NUCore operations, detecting
epistemic violations and escalating events when uncertainty exceeds
acceptable thresholds. Every violation is logged to NULedger for audit.

Key Features:
- Real-time u/|n| ratio monitoring
- Configurable threshold rules
- Automatic event escalation
- Complete integration with NULedger
- Pluggable event handlers
"""

from .monitor import Monitor, MonitorConfig
from .events import Event, EventLevel, EventHandler, EventAggregator, LogHandler, LedgerHandler
from .rules import Rule, CoverageRule, InvariantRule, ThresholdRule, CompositeRule, CustomRule

__all__ = [
    'Monitor',
    'MonitorConfig',
    'Event',
    'EventLevel',
    'EventHandler',
    'EventAggregator',
    'LogHandler',
    'LedgerHandler',
    'Rule',
    'CoverageRule',
    'InvariantRule',
    'ThresholdRule',
    'CompositeRule',
    'CustomRule',
]

__version__ = '0.1.0'
