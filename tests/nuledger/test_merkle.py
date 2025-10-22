"""
test_merkle.py

Tests for Merkle tree implementation.
"""

import pytest
from src.nuledger.merkle import MerkleTree, MerkleProof


class TestMerkleTree:
    """Tests for MerkleTree"""

    def test_empty_tree(self):
        """Test empty Merkle tree"""
        tree = MerkleTree()
        assert len(tree) == 0

        import hashlib
        expected_root = hashlib.sha256(b'').hexdigest()
        assert tree.root() == expected_root

    def test_single_leaf(self):
        """Test tree with single leaf"""
        tree = MerkleTree()
        tree.append("leaf1_hash")

        assert len(tree) == 1
        assert tree.root() == "leaf1_hash"

    def test_two_leaves(self):
        """Test tree with two leaves"""
        tree = MerkleTree()
        tree.append("leaf1")
        tree.append("leaf2")

        assert len(tree) == 2

        # Root should be hash of concatenation
        import hashlib
        expected = hashlib.sha256("leaf1leaf2".encode()).hexdigest()
        assert tree.root() == expected

    def test_multiple_appends(self):
        """Test appending multiple leaves"""
        tree = MerkleTree()

        roots = []
        for i in range(10):
            tree.append(f"leaf{i}")
            roots.append(tree.root())

        # Each append changes root
        assert len(set(roots)) == 10

    def test_root_caching(self):
        """Test that root is cached until next append"""
        tree = MerkleTree()
        tree.append("leaf1")
        tree.append("leaf2")

        root1 = tree.root()
        root2 = tree.root()

        # Should be same (cached)
        assert root1 == root2

        tree.append("leaf3")
        root3 = tree.root()

        # Should differ (cache invalidated)
        assert root3 != root1

    def test_deterministic_root(self):
        """Test that identical trees have identical roots"""
        tree1 = MerkleTree()
        tree2 = MerkleTree()

        leaves = ["hash1", "hash2", "hash3", "hash4", "hash5"]

        for leaf in leaves:
            tree1.append(leaf)
            tree2.append(leaf)

        assert tree1.root() == tree2.root()

    def test_odd_number_leaves(self):
        """Test tree with odd number of leaves"""
        tree = MerkleTree()

        # Add 3 leaves (odd)
        tree.append("leaf1")
        tree.append("leaf2")
        tree.append("leaf3")

        root = tree.root()
        assert root is not None

    def test_power_of_two_leaves(self):
        """Test tree with power-of-2 leaves"""
        tree = MerkleTree()

        # Add 8 leaves (power of 2)
        for i in range(8):
            tree.append(f"leaf{i}")

        root = tree.root()
        assert root is not None


class TestMerkleProof:
    """Tests for Merkle proof generation and verification"""

    def test_generate_proof_single_leaf(self):
        """Test proof for single-leaf tree"""
        tree = MerkleTree()
        tree.append("leaf1")

        proof = tree.generate_proof(0)

        assert proof.leaf_hash == "leaf1"
        assert proof.root == "leaf1"
        assert len(proof.path) == 0  # No siblings

    def test_generate_proof_two_leaves(self):
        """Test proof for two-leaf tree"""
        tree = MerkleTree()
        tree.append("leaf1")
        tree.append("leaf2")

        # Proof for first leaf
        proof0 = tree.generate_proof(0)
        assert proof0.leaf_hash == "leaf1"
        assert len(proof0.path) == 1

        # Proof for second leaf
        proof1 = tree.generate_proof(1)
        assert proof1.leaf_hash == "leaf2"
        assert len(proof1.path) == 1

    def test_verify_proof_valid(self):
        """Test verification of valid proof"""
        tree = MerkleTree()

        for i in range(8):
            tree.append(f"leaf{i}")

        # Generate proof for leaf 3
        proof = tree.generate_proof(3)

        # Verify it
        assert proof.verify() is True

    def test_verify_proof_all_leaves(self):
        """Test all leaves have valid proofs"""
        tree = MerkleTree()

        for i in range(10):
            tree.append(f"leaf{i}")

        # Verify every leaf
        for i in range(10):
            proof = tree.generate_proof(i)
            assert proof.verify() is True

    def test_proof_path_length(self):
        """Test proof path length is O(log n)"""
        tree = MerkleTree()

        # Add 16 leaves (2^4)
        for i in range(16):
            tree.append(f"leaf{i}")

        proof = tree.generate_proof(0)

        # Path length should be log2(16) = 4
        assert len(proof.path) == 4

    def test_invalid_proof(self):
        """Test that tampered proof fails verification"""
        tree = MerkleTree()

        for i in range(8):
            tree.append(f"leaf{i}")

        proof = tree.generate_proof(3)

        # Tamper with proof
        original_root = proof.root
        proof.root = "tampered_root"

        assert proof.verify() is False

        # Restore and verify
        proof.root = original_root
        assert proof.verify() is True

    def test_proof_index_out_of_range(self):
        """Test that invalid index raises error"""
        tree = MerkleTree()
        tree.append("leaf1")

        with pytest.raises(IndexError):
            tree.generate_proof(1)

        with pytest.raises(IndexError):
            tree.generate_proof(-1)

    def test_proof_large_tree(self):
        """Test proof generation for large tree"""
        tree = MerkleTree()

        # Add 1000 leaves
        for i in range(1000):
            tree.append(f"leaf{i}")

        # Verify proof for random leaf
        proof = tree.generate_proof(500)
        assert proof.verify() is True

        # Path length should be ~log2(1000) ≈ 10
        assert len(proof.path) <= 11


class TestMerkleTreeProperties:
    """Property-based tests for Merkle tree"""

    def test_append_monotonicity(self):
        """Test that appending never decreases tree size"""
        tree = MerkleTree()

        sizes = []
        for i in range(20):
            tree.append(f"leaf{i}")
            sizes.append(len(tree))

        # Sizes should be strictly increasing
        assert sizes == list(range(1, 21))

    def test_root_changes_on_append(self):
        """Test that root always changes when appending"""
        tree = MerkleTree()
        tree.append("leaf1")

        roots = []
        for i in range(2, 11):
            old_root = tree.root()
            tree.append(f"leaf{i}")
            new_root = tree.root()

            roots.append(new_root)
            assert old_root != new_root

    def test_proof_consistency(self):
        """Test that proofs remain valid as tree grows"""
        tree = MerkleTree()

        # Add initial leaves
        for i in range(4):
            tree.append(f"leaf{i}")

        # Generate proof
        old_root = tree.root()
        proof = tree.generate_proof(2)
        assert proof.verify() is True
        assert proof.root == old_root

        # Add more leaves
        for i in range(4, 8):
            tree.append(f"leaf{i}")

        new_root = tree.root()

        # Root has changed
        assert old_root != new_root

        # Old proof still verifies (against its embedded root)
        # But it doesn't match the new tree root
        assert proof.verify() is True  # Self-consistent
        assert proof.root != new_root  # But outdated

        # New proof for same index matches new root
        new_proof = tree.generate_proof(2)
        assert new_proof.verify() is True
        assert new_proof.root == new_root


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
