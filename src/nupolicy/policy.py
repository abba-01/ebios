"""
policy.py

Policy file management and loading.

Policy files define NUGuard monitoring rules, thresholds, and escalation
behavior. All policies are signed with Ed25519 to prevent tampering.
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, UTC
import base64

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


@dataclass
class PolicyConfig:
    """
    Policy configuration structure

    Attributes:
        version: Policy version (semantic versioning)
        name: Human-readable policy name
        description: Policy description
        rules: List of rule configurations
        escalation: Escalation settings (halt_on_critical, auto_log)
        metadata: Additional metadata (author, created_at, etc.)
    """
    version: str
    name: str
    description: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    escalation: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyConfig':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Policy:
    """
    Signed policy object

    Combines PolicyConfig with cryptographic signature for integrity.

    Attributes:
        config: Policy configuration
        signature: Ed25519 signature (base64 encoded)
        public_key: Public key for verification (base64 encoded)
        policy_hash: SHA-256 hash of config
    """
    config: PolicyConfig
    signature: Optional[str] = None
    public_key: Optional[str] = None
    policy_hash: Optional[str] = None

    def __post_init__(self):
        """Generate hash if not provided"""
        if self.policy_hash is None:
            self.policy_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of policy config"""
        config_bytes = json.dumps(
            self.config.to_dict(),
            sort_keys=True
        ).encode('utf-8')
        return hashlib.sha256(config_bytes).hexdigest()

    def verify_signature(self) -> bool:
        """
        Verify Ed25519 signature

        Returns:
            True if signature is valid, False otherwise

        Raises:
            ValueError: If cryptography library not available
        """
        if not CRYPTO_AVAILABLE:
            raise ValueError("cryptography library required for signature verification")

        if self.signature is None or self.public_key is None:
            return False

        try:
            # Decode public key
            public_key_bytes = base64.b64decode(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

            # Decode signature
            signature_bytes = base64.b64decode(self.signature)

            # Verify signature on policy hash
            public_key.verify(
                signature_bytes,
                self.policy_hash.encode('utf-8')
            )

            return True
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'config': self.config.to_dict(),
            'signature': self.signature,
            'public_key': self.public_key,
            'policy_hash': self.policy_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Policy':
        """Create from dictionary"""
        config = PolicyConfig.from_dict(data['config'])
        return cls(
            config=config,
            signature=data.get('signature'),
            public_key=data.get('public_key'),
            policy_hash=data.get('policy_hash')
        )


class PolicyLoader:
    """
    Loads and validates policy files

    Supports JSON format with optional signature verification.
    """

    @staticmethod
    def load_from_file(path: Path, require_signature: bool = False) -> Policy:
        """
        Load policy from JSON file

        Args:
            path: Path to policy file
            require_signature: Require valid signature

        Returns:
            Policy object

        Raises:
            ValueError: If policy invalid or signature check fails
        """
        with open(path, 'r') as f:
            data = json.load(f)

        policy = Policy.from_dict(data)

        # Verify signature if required
        if require_signature:
            if not policy.verify_signature():
                raise ValueError(f"Policy signature verification failed: {path}")

        return policy

    @staticmethod
    def load_from_string(content: str, require_signature: bool = False) -> Policy:
        """
        Load policy from JSON string

        Args:
            content: JSON policy content
            require_signature: Require valid signature

        Returns:
            Policy object
        """
        data = json.loads(content)
        policy = Policy.from_dict(data)

        if require_signature and not policy.verify_signature():
            raise ValueError("Policy signature verification failed")

        return policy

    @staticmethod
    def sign_policy(policy: Policy, private_key_path: Path) -> Policy:
        """
        Sign policy with Ed25519 private key

        Args:
            policy: Policy to sign
            private_key_path: Path to private key file (PEM format)

        Returns:
            Policy with signature and public key

        Raises:
            ValueError: If cryptography library not available
        """
        if not CRYPTO_AVAILABLE:
            raise ValueError("cryptography library required for signing")

        # Load private key
        with open(private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

        # Sign policy hash
        signature = private_key.sign(policy.policy_hash.encode('utf-8'))

        # Get public key
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # Update policy
        policy.signature = base64.b64encode(signature).decode('utf-8')
        policy.public_key = base64.b64encode(public_key_bytes).decode('utf-8')

        return policy


class PolicyManager:
    """
    Manages policy lifecycle and versioning

    Maintains history of policy changes with complete audit trail.
    """

    def __init__(self, policy_dir: Optional[Path] = None):
        """
        Initialize policy manager

        Args:
            policy_dir: Directory for storing policies
        """
        self.policy_dir = Path(policy_dir) if policy_dir else Path('./governance/policies')
        self.policy_dir.mkdir(parents=True, exist_ok=True)
        self.current_policy: Optional[Policy] = None
        self.policy_history: List[Policy] = []

    def load_policy(self, name: str, require_signature: bool = False) -> Policy:
        """
        Load policy by name

        Args:
            name: Policy name (without .json extension)
            require_signature: Require valid signature

        Returns:
            Policy object
        """
        path = self.policy_dir / f"{name}.json"
        policy = PolicyLoader.load_from_file(path, require_signature)
        self.current_policy = policy
        self.policy_history.append(policy)
        return policy

    def save_policy(self, policy: Policy, name: str) -> Path:
        """
        Save policy to file

        Args:
            policy: Policy to save
            name: Policy name

        Returns:
            Path to saved file
        """
        path = self.policy_dir / f"{name}.json"

        with open(path, 'w') as f:
            json.dump(policy.to_dict(), f, indent=2)

        return path

    def create_policy(
        self,
        name: str,
        description: str,
        rules: List[Dict[str, Any]],
        escalation: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Policy:
        """
        Create new policy

        Args:
            name: Policy name
            description: Policy description
            rules: Rule configurations
            escalation: Escalation settings
            metadata: Additional metadata

        Returns:
            New Policy object
        """
        config = PolicyConfig(
            version="1.0.0",
            name=name,
            description=description,
            rules=rules,
            escalation=escalation or {},
            metadata=metadata or {
                'created_at': datetime.now(UTC).isoformat(),
                'author': 'NUPolicy'
            }
        )

        policy = Policy(config=config)
        self.current_policy = policy
        return policy

    def list_policies(self) -> List[str]:
        """
        List all available policies

        Returns:
            List of policy names
        """
        return [
            p.stem for p in self.policy_dir.glob("*.json")
        ]

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get policy change history

        Returns:
            List of policy summaries with versions and hashes
        """
        return [
            {
                'version': p.config.version,
                'name': p.config.name,
                'hash': p.policy_hash,
                'metadata': p.config.metadata
            }
            for p in self.policy_history
        ]
