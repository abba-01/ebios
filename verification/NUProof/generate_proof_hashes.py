#!/usr/bin/env python3
"""
generate_proof_hashes.py

Generates cryptographic hashes of formal proofs for eBIOS attestation.
Each proof file is hashed and signed with the eBIOS Layer 0 keypair.

Part of PHASE 2: NUProof verification framework
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime
import subprocess
import sys

# Ed25519 signing (requires cryptography or nacl library)
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    print("Warning: cryptography library not installed. Signatures will be mocked.")


class ProofHasher:
    """Generates and signs proof hashes for eBIOS attestation"""

    def __init__(self, keypair_path=None):
        """
        Initialize with eBIOS Layer 0 keypair

        Args:
            keypair_path: Path to Ed25519 private key (PEM format)
        """
        self.keypair_path = keypair_path
        self.private_key = None

        if HAS_CRYPTO and keypair_path and Path(keypair_path).exists():
            self._load_keypair()
        else:
            self._generate_test_keypair()

    def _load_keypair(self):
        """Load existing Ed25519 keypair"""
        with open(self.keypair_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

    def _generate_test_keypair(self):
        """Generate ephemeral test keypair (for development)"""
        if HAS_CRYPTO:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            print("Generated ephemeral test keypair (use only for development!)")
        else:
            self.private_key = None

    def hash_file(self, filepath):
        """
        Generate SHA-256 hash of proof file

        Args:
            filepath: Path to .lean file

        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            sha256.update(f.read())
        return sha256.hexdigest()

    def sign_hash(self, hash_hex):
        """
        Sign hash with Ed25519 private key

        Args:
            hash_hex: Hexadecimal hash string

        Returns:
            Hexadecimal signature string
        """
        if not HAS_CRYPTO or self.private_key is None:
            # Mock signature for development
            return f"mock_sig_{hash_hex[:16]}"

        hash_bytes = bytes.fromhex(hash_hex)
        signature = self.private_key.sign(hash_bytes)
        return signature.hex()

    def process_proof_directory(self, proof_dir):
        """
        Process all .lean files in directory and generate manifest

        Args:
            proof_dir: Directory containing .lean proof files

        Returns:
            Dictionary with proof hashes and signatures
        """
        proof_dir = Path(proof_dir)
        manifest = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ebios_layer": 2,
            "component": "NUProof",
            "proofs": []
        }

        for lean_file in sorted(proof_dir.glob("*.lean")):
            print(f"Processing {lean_file.name}...")

            file_hash = self.hash_file(lean_file)
            signature = self.sign_hash(file_hash)

            proof_entry = {
                "filename": lean_file.name,
                "sha256": file_hash,
                "signature": signature,
                "status": self._check_proof_status(lean_file)
            }

            manifest["proofs"].append(proof_entry)

        return manifest

    def _check_proof_status(self, lean_file):
        """
        Check if proof contains 'sorry' (incomplete)

        Args:
            lean_file: Path to .lean file

        Returns:
            "complete" or "skeleton"
        """
        with open(lean_file, 'r') as f:
            content = f.read()

        if 'sorry' in content or 'axiom' in content:
            return "skeleton"
        return "complete"

    def save_manifest(self, manifest, output_path):
        """
        Save proof manifest as JSON

        Args:
            manifest: Proof manifest dictionary
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"\nManifest saved to {output_path}")
        print(f"Total proofs: {len(manifest['proofs'])}")

        complete_count = sum(1 for p in manifest['proofs'] if p['status'] == 'complete')
        skeleton_count = len(manifest['proofs']) - complete_count

        print(f"  Complete: {complete_count}")
        print(f"  Skeleton: {skeleton_count}")


def main():
    """Main entry point"""
    proof_dir = Path(__file__).parent
    output_path = proof_dir / "proof_manifest.json"

    print("eBIOS NUProof Hash Generator")
    print("=" * 50)
    print(f"Proof directory: {proof_dir}")
    print()

    hasher = ProofHasher()
    manifest = hasher.process_proof_directory(proof_dir)
    hasher.save_manifest(manifest, output_path)

    print("\n" + "=" * 50)
    print("Proof hashes generated successfully!")
    print("\nNOTE: Signatures are for development only.")
    print("Production deployment requires actual eBIOS Layer 0 keypair.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
