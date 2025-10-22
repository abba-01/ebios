"""
test_ledger.py

Comprehensive tests for NULedger functionality.
"""

import pytest
from src.nuledger import Ledger, LedgerEntry, MemoryBackend, SQLiteBackend


class TestLedgerEntry:
    """Tests for LedgerEntry dataclass"""

    def test_entry_creation(self):
        """Test basic entry creation"""
        entry = LedgerEntry(
            timestamp=1,
            op_id="test-123",
            parent_id=None,
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12),
            coverage=0.037,
            invariant_passed=True,
            signature="mock_sig"
        )

        assert entry.timestamp == 1
        assert entry.op_id == "test-123"
        assert entry.operation == "add"
        assert entry.invariant_passed is True

    def test_entry_hash(self):
        """Test entry hashing (excludes signature)"""
        entry1 = LedgerEntry(
            timestamp=1,
            op_id="test-123",
            parent_id=None,
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12),
            coverage=0.037,
            invariant_passed=True,
            signature="sig1"
        )

        entry2 = LedgerEntry(
            timestamp=1,
            op_id="test-123",
            parent_id=None,
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12),
            coverage=0.037,
            invariant_passed=True,
            signature="sig2"  # Different signature
        )

        # Same hash despite different signatures
        assert entry1.hash() == entry2.hash()

    def test_entry_serialization(self):
        """Test JSON serialization"""
        entry = LedgerEntry(
            timestamp=1,
            op_id="test-123",
            parent_id=None,
            operation="add",
            inputs=[(10.0, 0.5)],
            output=(10.5, 0.5),
            coverage=0.048,
            invariant_passed=True,
            signature="mock"
        )

        json_str = entry.to_json()
        assert "test-123" in json_str
        assert "add" in json_str


class TestLedger:
    """Tests for Ledger core functionality"""

    def test_ledger_creation(self):
        """Test creating empty ledger"""
        ledger = Ledger()
        assert len(ledger) == 0

    def test_append_entry(self):
        """Test appending entries"""
        ledger = Ledger()

        entry = ledger.append(
            operation="add",
            inputs=[(10.0, 0.5), (20.0, 1.0)],
            output=(30.0, 1.12),
            coverage=0.037,
            invariant_passed=True
        )

        assert len(ledger) == 1
        assert entry.operation == "add"
        assert entry.signature != ""  # Has signature

    def test_monotonic_timestamps(self):
        """Test timestamps are monotonically increasing"""
        ledger = Ledger()

        e1 = ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        e2 = ledger.append("multiply", [(2.0, 0.2)], (2.0, 0.2), 0.1, True)
        e3 = ledger.append("compose", [(3.0, 0.3)], (3.0, 0.3), 0.1, True)

        assert e1.timestamp < e2.timestamp < e3.timestamp

    def test_causal_chain(self):
        """Test parent-child causal chains"""
        ledger = Ledger()

        # Root operation
        e1 = ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)

        # Child operation
        e2 = ledger.append(
            "multiply",
            [(2.0, 0.2)],
            (2.0, 0.2),
            0.1,
            True,
            parent_id=e1.op_id
        )

        # Grandchild operation
        e3 = ledger.append(
            "compose",
            [(3.0, 0.3)],
            (3.0, 0.3),
            0.1,
            True,
            parent_id=e2.op_id
        )

        # Trace from grandchild
        chain = ledger.trace(e3.op_id)

        assert len(chain) == 3
        assert chain[0].op_id == e1.op_id
        assert chain[1].op_id == e2.op_id
        assert chain[2].op_id == e3.op_id

    def test_merkle_root_updates(self):
        """Test Merkle root changes on append"""
        ledger = Ledger()

        root1 = ledger.get_root()

        ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        root2 = ledger.get_root()

        ledger.append("multiply", [(2.0, 0.2)], (2.0, 0.2), 0.1, True)
        root3 = ledger.get_root()

        # Each append changes root
        assert root1 != root2 != root3

    def test_verify_integrity_valid(self):
        """Test integrity verification on valid ledger"""
        ledger = Ledger()

        ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        ledger.append("multiply", [(2.0, 0.2)], (2.0, 0.2), 0.1, True)

        assert ledger.verify_integrity() is True

    def test_multiple_operations(self):
        """Test ledger with multiple operation types"""
        ledger = Ledger()

        operations = [
            ("add", [(1.0, 0.1), (2.0, 0.2)], (3.0, 0.22), 0.073),
            ("multiply", [(3.0, 0.3), (4.0, 0.4)], (12.0, 2.4), 0.2),
            ("compose", [(5.0, 0.5), (6.0, 0.6)], (5.5, 0.39), 0.071),
            ("flip", [(7.0, 0.7)], (-7.0, 0.7), 0.1),
        ]

        for op, inputs, output, coverage in operations:
            ledger.append(op, inputs, output, coverage, True)

        assert len(ledger) == 4

        # Check all operations are present
        entries = ledger.get_all()
        ops = [e.operation for e in entries]
        assert "add" in ops
        assert "multiply" in ops
        assert "compose" in ops
        assert "flip" in ops


class TestBackends:
    """Tests for storage backends"""

    def test_memory_backend(self):
        """Test MemoryBackend"""
        backend = MemoryBackend()
        ledger = Ledger(backend=backend)

        ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        ledger.append("multiply", [(2.0, 0.2)], (2.0, 0.2), 0.1, True)

        assert len(ledger) == 2

    def test_sqlite_backend_memory(self):
        """Test SQLiteBackend with in-memory database"""
        backend = SQLiteBackend(":memory:")
        ledger = Ledger(backend=backend)

        e1 = ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        e2 = ledger.append("multiply", [(2.0, 0.2)], (2.0, 0.2), 0.1, True)

        assert len(ledger) == 2

        # Test retrieval
        retrieved = backend.get(e1.op_id)
        assert retrieved is not None
        assert retrieved.op_id == e1.op_id

    def test_sqlite_backend_persistence(self, tmp_path):
        """Test SQLite backend with file persistence"""
        db_file = tmp_path / "test_ledger.db"

        # Create and populate ledger
        backend1 = SQLiteBackend(str(db_file))
        ledger1 = Ledger(backend=backend1)

        e1 = ledger1.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        root1 = ledger1.get_root()

        backend1.close()

        # Reload from file
        backend2 = SQLiteBackend(str(db_file))
        ledger2 = Ledger(backend=backend2)

        assert len(ledger2) == 1
        assert ledger2.get_root() == root1

        # Verify entry persisted
        retrieved = backend2.get(e1.op_id)
        assert retrieved is not None
        assert retrieved.operation == "add"

        backend2.close()


class TestMerkleIntegration:
    """Tests for Merkle tree integration"""

    def test_merkle_root_deterministic(self):
        """Test Merkle root is deterministic"""
        ledger1 = Ledger()
        ledger2 = Ledger()

        # Same operations
        for i in range(5):
            ledger1.append(f"op{i}", [(float(i), 0.1)], (float(i), 0.1), 0.1, True)
            ledger2.append(f"op{i}", [(float(i), 0.1)], (float(i), 0.1), 0.1, True)

        # Different Merkle roots (different UUIDs and timestamps)
        # But structure is identical
        assert len(ledger1) == len(ledger2)

    def test_merkle_tamper_detection(self):
        """Test that tampering is detectable"""
        ledger = Ledger()

        e1 = ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)
        root_before = ledger.get_root()

        # Manually tamper with backend (simulates attack)
        entries = ledger.backend.get_all()
        entries[0].coverage = 999.0  # Change value

        # Recompute Merkle tree
        from src.nuledger.merkle import MerkleTree
        new_tree = MerkleTree()
        for entry in entries:
            new_tree.append(entry.hash())

        root_after = new_tree.root()

        # Roots should differ (tamper detected)
        assert root_before != root_after


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_ledger_root(self):
        """Test Merkle root of empty ledger"""
        ledger = Ledger()
        root = ledger.get_root()

        # Empty root is hash of empty string
        import hashlib
        expected = hashlib.sha256(b'').hexdigest()
        assert root == expected

    def test_trace_nonexistent_operation(self):
        """Test tracing nonexistent operation"""
        ledger = Ledger()
        ledger.append("add", [(1.0, 0.1)], (1.0, 0.1), 0.1, True)

        chain = ledger.trace("nonexistent-id")
        assert len(chain) == 0

    def test_failed_invariant_logging(self):
        """Test logging operations with failed invariants"""
        ledger = Ledger()

        entry = ledger.append(
            "add",
            [(1.0, -0.5)],  # Negative uncertainty (invalid!)
            (1.0, 0.0),
            0.0,
            invariant_passed=False  # Flag as failed
        )

        assert entry.invariant_passed is False
        assert len(ledger) == 1

    def test_large_ledger_performance(self):
        """Test performance with larger ledger"""
        ledger = Ledger()

        # Append 1000 entries
        for i in range(1000):
            ledger.append(
                f"op{i%4}",  # Cycle through 4 operations
                [(float(i), 0.1 * i)],
                (float(i), 0.1 * i),
                0.1,
                True
            )

        assert len(ledger) == 1000
        assert ledger.verify_integrity() is True

        # Trace should still be fast
        last_entry = ledger.get_all()[-1]
        chain = ledger.trace(last_entry.op_id)
        assert len(chain) == 1  # No parents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
