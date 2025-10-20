"""
merkle.py

Merkle Tree implementation for NULedger audit chain.

Provides O(log n) verification of entry inclusion and tamper detection.
All hashes are SHA-256.
"""

import hashlib
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MerkleProof:
    """Proof of inclusion in Merkle tree"""
    leaf_hash: str
    path: List[Tuple[str, str]]  # (hash, direction: 'left' or 'right')
    root: str

    def verify(self) -> bool:
        """
        Verify this Merkle proof

        Returns:
            True if proof is valid, False otherwise
        """
        current = self.leaf_hash

        for sibling_hash, direction in self.path:
            if direction == 'left':
                combined = sibling_hash + current
            else:
                combined = current + sibling_hash

            current = hashlib.sha256(combined.encode()).hexdigest()

        return current == self.root


class MerkleTree:
    """
    Merkle Tree for cryptographic audit chain

    Properties:
    - Append-only (no deletions)
    - Efficient verification (O(log n))
    - Tamper-evident (any change modifies root)

    Example:
        tree = MerkleTree()
        tree.append("entry1_hash")
        tree.append("entry2_hash")
        root = tree.root()  # Current Merkle root
        proof = tree.generate_proof(0)  # Proof for first entry
        assert proof.verify()
    """

    def __init__(self):
        """Initialize empty Merkle tree"""
        self.leaves: List[str] = []
        self._root: Optional[str] = None

    def append(self, leaf_hash: str) -> None:
        """
        Append new leaf to tree

        Args:
            leaf_hash: SHA-256 hash of entry to append

        Complexity: O(log n) for root recomputation
        """
        self.leaves.append(leaf_hash)
        self._root = None  # Invalidate cached root

    def root(self) -> str:
        """
        Compute current Merkle root

        Returns:
            SHA-256 hash of root node

        Complexity: O(n) worst case, O(1) if cached
        """
        if self._root is not None:
            return self._root

        if not self.leaves:
            # Empty tree has empty root
            self._root = hashlib.sha256(b'').hexdigest()
            return self._root

        # Build tree bottom-up
        current_level = self.leaves[:]

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                left = current_level[i]

                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    # Odd number: duplicate last node
                    right = left

                combined = left + right
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)

            current_level = next_level

        self._root = current_level[0]
        return self._root

    def generate_proof(self, index: int) -> MerkleProof:
        """
        Generate Merkle proof for leaf at index

        Args:
            index: Index of leaf (0-based)

        Returns:
            MerkleProof that can be verified independently

        Raises:
            IndexError: If index out of range

        Complexity: O(log n)
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Index {index} out of range [0, {len(self.leaves)})")

        leaf_hash = self.leaves[index]
        path = []

        # Build tree and track path
        current_level = self.leaves[:]
        current_index = index

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                left = current_level[i]

                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = left

                # Track sibling for proof path
                if i == current_index:
                    sibling = right
                    direction = 'right'
                    path.append((sibling, direction))
                    next_index = i // 2
                elif i + 1 == current_index:
                    sibling = left
                    direction = 'left'
                    path.append((sibling, direction))
                    next_index = i // 2
                else:
                    next_index = -1  # Not in this subtree

                combined = left + right
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)

                if i == current_index or i + 1 == current_index:
                    current_index = next_index

            current_level = next_level

        return MerkleProof(
            leaf_hash=leaf_hash,
            path=path,
            root=self.root()
        )

    def __len__(self) -> int:
        """Return number of leaves in tree"""
        return len(self.leaves)

    def __repr__(self) -> str:
        """String representation"""
        return f"MerkleTree(leaves={len(self.leaves)}, root={self.root()[:16]}...)"
