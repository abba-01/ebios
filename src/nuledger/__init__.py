"""
NULedger: Cryptographic Audit Ledger for eBIOS

Layer 3 of eBIOS: Coverage ledger with Merkle chain attestation.

"Truth is a data structure, not a declaration."

This module provides immutable, cryptographically signed logging of all
NUCore operations. Every operation generates an audit entry that is:
- Signed with eBIOS Layer 0 keypair (Ed25519)
- Chained via Merkle tree
- Timestamped with monotonic counter
- Traceable through complete causal history

Key Features:
- Append-only ledger (no updates or deletes)
- Merkle tree for O(log n) verification
- Multiple backends (memory, SQLite, LMDB)
- CLI for audit trail queries
- Complete operation coverage tracking
"""

from .ledger import Ledger, LedgerEntry
from .merkle import MerkleTree
from .backends import MemoryBackend, SQLiteBackend

__all__ = [
    'Ledger',
    'LedgerEntry',
    'MerkleTree',
    'MemoryBackend',
    'SQLiteBackend',
]

__version__ = '0.1.0'
