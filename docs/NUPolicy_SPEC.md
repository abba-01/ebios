# NUPolicy Specification

**Layer 5 of eBIOS: Policy Management and Governance**

## Philosophy

> "Policy is data, not code."

NUPolicy externalizes monitoring rules from code into signed, versioned, auditable policy files. Operators can define their own risk tolerance, but they cannot hide what they choose. Every policy decision is cryptographically sealed and traceable.

## Core Principle

Autonomous systems require configurable governance without sacrificing accountability. NUPolicy provides:

1. **External Configuration**: Policies are data files, not hardcoded logic
2. **Cryptographic Signing**: Ed25519 signatures prevent policy tampering
3. **Version Control**: All policy changes are tracked with complete history
4. **NUGuard Integration**: Policies directly configure runtime monitoring
5. **Audit Trail**: Policy application is logged to NULedger

## Policy Model

### Structure

```json
{
  "config": {
    "version": "1.0.0",
    "name": "PolicyName",
    "description": "Human-readable description",
    "rules": [
      {
        "type": "CoverageRule",
        "threshold": 0.05,
        "level": "warning"
      }
    ],
    "escalation": {
      "halt_on_critical": true,
      "auto_log": true
    },
    "metadata": {
      "author": "eBIOS",
      "created_at": "2025-10-20T00:00:00Z",
      "domain": "safety-critical"
    }
  },
  "signature": "base64_ed25519_signature",
  "public_key": "base64_public_key",
  "policy_hash": "sha256_hash"
}
```

### Policy Components

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Semantic version (x.y.z) |
| `name` | string | Yes | Unique policy identifier |
| `description` | string | Yes | Human-readable purpose |
| `rules` | array | Yes | List of monitoring rules |
| `escalation` | object | No | Escalation configuration |
| `metadata` | object | No | Additional context |
| `signature` | string | No | Ed25519 signature (base64) |
| `public_key` | string | No | Public key for verification (base64) |
| `policy_hash` | string | Auto | SHA-256 hash of config |

## Supported Rules

### InvariantRule

Detects mathematical violations (always CRITICAL level).

```json
{
  "type": "InvariantRule"
}
```

**Detects:**
- Negative uncertainty (u < 0)
- NaN values
- Infinite nominal values

### CoverageRule

Monitors coverage ratio (u/|n|).

```json
{
  "type": "CoverageRule",
  "threshold": 0.05,
  "level": "warning"
}
```

**Parameters:**
- `threshold`: Maximum acceptable u/|n| ratio (0.0 to 1.0)
- `level`: Event level (info, warning, error, critical)

### ThresholdRule

Checks absolute uncertainty value.

```json
{
  "type": "ThresholdRule",
  "max_uncertainty": 10.0,
  "level": "error"
}
```

**Parameters:**
- `max_uncertainty`: Maximum absolute uncertainty value
- `level`: Event level

### CompositeRule

Combines multiple rules with AND/OR logic.

```json
{
  "type": "CompositeRule",
  "mode": "and",
  "rules": [
    {"type": "CoverageRule", "threshold": 0.05},
    {"type": "ThresholdRule", "max_uncertainty": 5.0}
  ]
}
```

**Parameters:**
- `mode`: "and" or "or"
- `rules`: Array of sub-rules

## Escalation Settings

```json
{
  "halt_on_critical": true,
  "auto_log": true
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `halt_on_critical` | boolean | false | Stop execution on CRITICAL events |
| `auto_log` | boolean | true | Automatically log events to NULedger |

## Policy Lifecycle

### 1. Creation

```python
from nupolicy import PolicyManager

manager = PolicyManager()
policy = manager.create_policy(
    name="ConservativePolicy",
    description="Low risk tolerance",
    rules=[
        {"type": "InvariantRule"},
        {"type": "CoverageRule", "threshold": 0.05, "level": "error"}
    ],
    escalation={"halt_on_critical": True, "auto_log": True}
)
```

### 2. Validation

```python
from nupolicy import PolicyValidator

result = PolicyValidator.validate(policy.to_dict())
if not result.valid:
    print("Errors:", result.errors)
    print("Warnings:", result.warnings)
```

### 3. Signing (Optional)

```python
from nupolicy import PolicyLoader

signed_policy = PolicyLoader.sign_policy(
    policy,
    private_key_path=Path("governance/keys/policy_key.pem")
)
```

### 4. Storage

```python
manager.save_policy(signed_policy, "conservative")
```

### 5. Loading

```python
loaded_policy = manager.load_policy(
    "conservative",
    require_signature=True  # Enforce signature verification
)
```

### 6. Application

```python
from nupolicy.integration import create_monitor_from_policy
from nuledger import Ledger

ledger = Ledger()
monitor = create_monitor_from_policy(loaded_policy, ledger=ledger)

# Now use monitor for operations
from nucore import add
n_out, u_out = add(10.0, 0.5, 20.0, 1.0)
monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n_out, u_out))
```

## Example Policies

### Conservative (Safety-Critical)

```json
{
  "config": {
    "version": "1.0.0",
    "name": "ConservativePolicy",
    "description": "Low risk tolerance for safety-critical systems",
    "rules": [
      {"type": "InvariantRule"},
      {"type": "CoverageRule", "threshold": 0.05, "level": "error"},
      {"type": "ThresholdRule", "max_uncertainty": 1.0, "level": "warning"}
    ],
    "escalation": {
      "halt_on_critical": true,
      "auto_log": true
    }
  }
}
```

**Use Case:** Autonomous vehicles, medical devices, aerospace systems

### Permissive (Experimental)

```json
{
  "config": {
    "version": "1.0.0",
    "name": "PermissivePolicy",
    "description": "High risk tolerance for experimental systems",
    "rules": [
      {"type": "InvariantRule"},
      {"type": "CoverageRule", "threshold": 0.5, "level": "warning"}
    ],
    "escalation": {
      "halt_on_critical": false,
      "auto_log": true
    }
  }
}
```

**Use Case:** Research prototypes, exploratory data analysis, testing

### Audit-Only (Production)

```json
{
  "config": {
    "version": "1.0.0",
    "name": "AuditOnlyPolicy",
    "description": "Log violations but never halt",
    "rules": [
      {"type": "InvariantRule"},
      {"type": "CoverageRule", "threshold": 0.1, "level": "warning"}
    ],
    "escalation": {
      "halt_on_critical": false,
      "auto_log": true
    }
  }
}
```

**Use Case:** Production systems with external monitoring, high-availability services

## Validation Rules

PolicyValidator enforces:

1. **Required Fields**: version, name, description, rules
2. **Semantic Versioning**: x.y.z format
3. **Rule Type Validation**: Must be CoverageRule, InvariantRule, ThresholdRule, CompositeRule, or CustomRule
4. **Parameter Validation**:
   - CoverageRule: threshold in [0, 1]
   - ThresholdRule: max_uncertainty >= 0
   - CompositeRule: mode in ["and", "or"]
5. **Event Level Validation**: Must be info, warning, error, or critical
6. **Escalation Keys**: Only halt_on_critical and auto_log allowed

## Export Formats

### JSON (Default)

```python
from nupolicy import PolicyExporter, ExportFormat

json_str = PolicyExporter.export(policy, ExportFormat.JSON)
```

### JSON Compact

```python
compact = PolicyExporter.export(policy, ExportFormat.JSON_COMPACT)
```

### Summary (Human-Readable)

```python
summary = PolicyExporter.export(policy, ExportFormat.SUMMARY)
```

**Example Output:**
```
Policy: ConservativePolicy
Version: 1.0.0
Description: Low risk tolerance for safety-critical systems
Hash: a3f5e8d9...

Rules:
  1. InvariantRule (level: critical)
  2. CoverageRule (level: error)
     - threshold: 0.05
  3. ThresholdRule (level: warning)
     - max_uncertainty: 1.0

Escalation:
  - halt_on_critical: True
  - auto_log: True

Signature: VERIFIED
```

## Integration with eBIOS Stack

| Layer | Integration |
|-------|-------------|
| **Layer 1 (NUCore)** | Policy rules monitor NUCore operations |
| **Layer 3 (NULedger)** | Policy application logged for audit |
| **Layer 4 (NUGuard)** | Policies configure Monitor instances |
| **Layer 6 (NUGovern)** | REST API for policy management |
| **Layer 7 (NUCertify)** | Policies included in certification attestations |

## Cryptographic Signatures

### Signature Generation

```python
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Generate key pair (one-time)
private_key = ed25519.Ed25519PrivateKey.generate()

# Save private key
with open("policy_key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Sign policy
from nupolicy import PolicyLoader
signed_policy = PolicyLoader.sign_policy(policy, Path("policy_key.pem"))
```

### Signature Verification

```python
# Automatic verification on load
policy = PolicyLoader.load_from_file(
    Path("governance/policies/conservative.json"),
    require_signature=True
)

# Manual verification
is_valid = policy.verify_signature()
```

### Security Properties

- **Algorithm**: Ed25519 (Curve25519 signatures)
- **Hash Function**: SHA-256 for policy fingerprinting
- **Signature Target**: SHA-256 hash of policy config (not raw JSON)
- **Tamper Detection**: Any change to config invalidates signature
- **Key Management**: Private keys NEVER stored in policy files

## Policy Versioning

### Semantic Versioning

- **MAJOR** (x.0.0): Breaking changes to rule semantics
- **MINOR** (x.y.0): New rules added, backwards compatible
- **PATCH** (x.y.z): Bug fixes, clarifications

### Version History Tracking

```python
manager = PolicyManager()

# Load multiple versions
manager.load_policy("policy_v1")
manager.load_policy("policy_v2")
manager.load_policy("policy_v3")

# Get history
history = manager.get_history()
for entry in history:
    print(f"{entry['version']}: {entry['name']} (hash: {entry['hash']})")
```

## API Reference

### PolicyConfig

```python
@dataclass
class PolicyConfig:
    version: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    escalation: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Policy

```python
@dataclass
class Policy:
    config: PolicyConfig
    signature: Optional[str]
    public_key: Optional[str]
    policy_hash: Optional[str]

    def verify_signature(self) -> bool
    def to_dict(self) -> Dict[str, Any]
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Policy
```

### PolicyLoader

```python
class PolicyLoader:
    @staticmethod
    def load_from_file(path: Path, require_signature: bool = False) -> Policy

    @staticmethod
    def load_from_string(content: str, require_signature: bool = False) -> Policy

    @staticmethod
    def sign_policy(policy: Policy, private_key_path: Path) -> Policy
```

### PolicyManager

```python
class PolicyManager:
    def __init__(self, policy_dir: Optional[Path] = None)
    def load_policy(self, name: str, require_signature: bool = False) -> Policy
    def save_policy(self, policy: Policy, name: str) -> Path
    def create_policy(self, name: str, description: str, rules: List[Dict], ...) -> Policy
    def list_policies(self) -> List[str]
    def get_history(self) -> List[Dict[str, Any]]
```

### PolicyValidator

```python
class PolicyValidator:
    @classmethod
    def validate(cls, policy_dict: Dict[str, Any]) -> ValidationResult

    @classmethod
    def validate_and_raise(cls, policy_dict: Dict[str, Any]) -> None
```

### Integration Functions

```python
def policy_to_monitor_config(policy: Policy, validate: bool = True) -> MonitorConfig

def create_monitor_from_policy(policy: Policy, ledger=None, validate: bool = True) -> Monitor
```

## Performance

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Policy Hash | O(n) | n = policy JSON size |
| Signature Generation | O(1) | Ed25519 constant-time |
| Signature Verification | O(1) | Ed25519 constant-time |
| Validation | O(r) | r = number of rules |
| Load from File | O(n) | Dominated by JSON parsing |
| Monitor Conversion | O(r) | Creates r Rule objects |

## Best Practices

1. **Sign Production Policies**: Always sign policies for production systems
2. **Version Incrementally**: Follow semantic versioning strictly
3. **Document Changes**: Use metadata to track policy evolution
4. **Test Policies**: Validate policies before deployment
5. **Separate Environments**: Different policies for dev/staging/production
6. **Backup Keys**: Securely backup signing keys
7. **Rotate Keys**: Periodically rotate signing keys
8. **Audit Regularly**: Review policy history and application logs

## References

- **NUGuard Monitoring**: `/docs/NUGuard_POLICY.md`
- **NULedger Audit Log**: `/docs/NULedger_SPEC.md`
- **NUCore Operations**: `/docs/NUCore_SPEC.md`
- **eBIOS Architecture**: `/docs/README.md`

## Version

- **NUPolicy Version**: 0.1.0
- **eBIOS Layer**: 5
- **Status**: Active development (PHASE 5)

---

**NUPolicy** — Policy as immutable data.

*"Policy is data, not code."*
