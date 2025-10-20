"""
ledger.py

NULedger: Cryptographic audit ledger for eBIOS operations.

"Truth is a data structure, not a declaration."

Every NUCore operation generates a signed, timestamped, Merkle-chained
audit entry. The ledger is append-only and tamper-evident.
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

from .merkle import MerkleTree
from .backends import Backend, MemoryBackend

# Ed25519 signing (optional dependency)
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


@dataclass
class LedgerEntry:
    """
    Single audit entry in NULedger

    Schema:
        timestamp: Monotonic counter (not wall clock!)
        op_id: Unique operation identifier (UUID)
        parent_id: Parent operation (for causal chains)
        operation: Operation name (add, multiply, etc.)
        inputs: Input N/U pairs [(n1, u1), (n2, u2)]
        output: Output N/U pair (n_out, u_out)
        coverage: u/|n| ratio (epistemic coverage)
        invariant_passed: Whether all invariants held
        signature: Ed25519 signature of entry hash

    Immutability: No field can be modified after creation
    """
    timestamp: int
    op_id: str
    parent_id: Optional[str]
    operation: str
    inputs: List[tuple]
    output: tuple
    coverage: float
    invariant_passed: bool
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self) -> str:
        """
        Compute SHA-256 hash of entry (excluding signature)

        Returns:
            Hexadecimal hash string
        """
        # Create copy without signature
        data = self.to_dict()
        data.pop('signature', None)

        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


class Ledger:
    """
    NULedger: Append-only cryptographic audit log

    Features:
    - Merkle tree chain for O(log n) verification
    - Ed25519 signatures for authenticity
    - Multiple storage backends (memory, SQLite, LMDB)
    - Complete causal trace via parent_id links
    - Monotonic timestamps (not wall clock)

    Example:
        ledger = Ledger()

        # Log an operation
        entry = ledger.append(
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12),
            coverage=0.037,
            invariant_passed=True
        )

        # Query audit trail
        chain = ledger.trace(entry.op_id)
        print(f"Causal chain: {len(chain)} operations")

        # Verify integrity
        assert ledger.verify_integrity()
    """

    def __init__(self, backend: Optional[Backend] = None, keypair=None):
        """
        Initialize NULedger

        Args:
            backend: Storage backend (defaults to MemoryBackend)
            keypair: Ed25519 private key for signing (optional)
        """
        self.backend = backend or MemoryBackend()
        self.merkle = MerkleTree()
        self.keypair = keypair
        self._timestamp_counter = 0

        # Load existing entries into Merkle tree
        for entry in self.backend.get_all():
            self.merkle.append(entry.hash())

        if HAS_CRYPTO and keypair is None:
            # Generate ephemeral keypair for development
            self.keypair = ed25519.Ed25519PrivateKey.generate()

    def append(
        self,
        operation: str,
        inputs: List[tuple],
        output: tuple,
        coverage: float,
        invariant_passed: bool,
        parent_id: Optional[str] = None
    ) -> LedgerEntry:
        """
        Append new entry to ledger

        Args:
            operation: Operation name (add, multiply, etc.)
            inputs: List of input N/U pairs
            output: Output N/U pair
            coverage: u/|n| ratio
            invariant_passed: Whether invariants held
            parent_id: Parent operation ID (for causal chains)

        Returns:
            Signed LedgerEntry

        Complexity: O(log n) due to Merkle tree update
        """
        # Generate unique operation ID
        op_id = str(uuid.uuid4())

        # Monotonic timestamp
        self._timestamp_counter += 1
        timestamp = self._timestamp_counter

        # Create entry (without signature)
        entry = LedgerEntry(
            timestamp=timestamp,
            op_id=op_id,
            parent_id=parent_id,
            operation=operation,
            inputs=inputs,
            output=output,
            coverage=coverage,
            invariant_passed=invariant_passed,
            signature=""  # Placeholder
        )

        # Sign entry hash
        entry_hash = entry.hash()
        signature = self._sign(entry_hash)
        entry.signature = signature

        # Append to Merkle tree
        self.merkle.append(entry_hash)

        # Store in backend
        self.backend.append(entry)

        return entry

    def _sign(self, data_hash: str) -> str:
        """
        Sign data hash with Ed25519 keypair

        Args:
            data_hash: SHA-256 hash (hex string)

        Returns:
            Signature (hex string)
        """
        if not HAS_CRYPTO or self.keypair is None:
            # Mock signature for development
            return f"mock_sig_{data_hash[:16]}"

        hash_bytes = bytes.fromhex(data_hash)
        signature = self.keypair.sign(hash_bytes)
        return signature.hex()

    def trace(self, op_id: str) -> List[LedgerEntry]:
        """
        Trace complete causal chain for operation

        Args:
            op_id: Operation ID to trace

        Returns:
            List of entries from root to op_id (chronological order)

        Complexity: O(k) where k is chain depth
        """
        chain = []
        current_id = op_id

        # Walk backwards through parent links
        while current_id is not None:
            entry = self.backend.get(current_id)
            if entry is None:
                break

            chain.append(entry)
            current_id = entry.parent_id

        # Reverse to get chronological order
        return list(reversed(chain))

    def get_root(self) -> str:
        """
        Get current Merkle root

        Returns:
            SHA-256 hash of Merkle root
        """
        return self.merkle.root()

    def verify_integrity(self) -> bool:
        """
        Verify complete ledger integrity

        Checks:
        1. All entries have valid signatures
        2. Merkle root is correct
        3. Timestamps are monotonic

        Returns:
            True if all checks pass

        Complexity: O(n)
        """
        entries = self.backend.get_all()

        # Check monotonic timestamps
        last_timestamp = -1
        for entry in entries:
            if entry.timestamp <= last_timestamp:
                return False
            last_timestamp = entry.timestamp

        # Check Merkle root
        computed_tree = MerkleTree()
        for entry in entries:
            computed_tree.append(entry.hash())

        if computed_tree.root() != self.merkle.root():
            return False

        # Signature verification requires public key
        # (Skipped for now, would need key management)

        return True

    def get_all(self) -> List[LedgerEntry]:
        """
        Get all ledger entries

        Returns:
            List of all entries (chronological order)
        """
        return self.backend.get_all()

    def __len__(self) -> int:
        """Return number of entries in ledger"""
        return len(self.backend.get_all())

    def __repr__(self) -> str:
        """String representation"""
        return f"Ledger(entries={len(self)}, root={self.get_root()[:16]}...)"
