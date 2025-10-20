# eBIOS Documentation

**Epistemic BIOS: A Cryptographically Sealed Substrate for Provable Computation**

## Documentation Index

This directory contains complete specifications for all eBIOS layers.

### Layer Specifications

1. **[NUCore_SPEC.md](NUCore_SPEC.md)** - Layer 1: N/U Algebra Kernel
   - Nominal/Uncertainty operations (⊕, ⊗, ⊙, Catch, Flip)
   - Mathematical foundations and invariants
   - Performance characteristics (all O(1))

2. **[NUProof_SPEC.md](NUProof_SPEC.md)** - Layer 2: Formal Verification *(planned)*
   - Lean 4 theorem proofs
   - Property verification
   - Proof attestation system

3. **[NULedger_SPEC.md](NULedger_SPEC.md)** - Layer 3: Cryptographic Audit Ledger
   - Append-only operation log
   - Merkle tree integrity
   - Ed25519 signatures

4. **[NUGuard_POLICY.md](NUGuard_POLICY.md)** - Layer 4: Runtime Monitoring
   - Violation detection
   - Event escalation
   - Policy enforcement

5. **[NUPolicy_SPEC.md](NUPolicy_SPEC.md)** - Layer 5: Policy Management
   - JSON policy files
   - Cryptographic signing
   - NUGuard integration

6. **[NUGovern_API.md](NUGovern_API.md)** - Layer 6: HTTP API
   - RESTful endpoints
   - Request/response schemas
   - Client examples

### Additional Documentation

- **[COMPLIANCE.md](COMPLIANCE.md)** - Compliance and certification
- **[TRACEABILITY.md](TRACEABILITY.md)** - Requirements traceability matrix
- **[ARCHITECTURE_FINAL.md](ARCHITECTURE_FINAL.md)** - Complete system architecture

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/abba-01/ebios.git
cd ebios

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

### Usage Examples

#### NUCore (Direct)

```python
from src.nucore import add, multiply

# Addition with uncertainty propagation
n_out, u_out = add(10.0, 0.5, 20.0, 1.0)
# Result: (30.0, 1.12)
```

#### NUGovern (HTTP API)

```bash
# Start server
python src/nugovern/server.py

# Execute operation
curl -X POST http://localhost:8000/operations/execute \
  -H "Content-Type: application/json" \
  -d '{"operation":"add","inputs":[[10.0,0.5],[20.0,1.0]]}'
```

#### NUPolicy (Policy-Driven)

```python
from src.nupolicy import PolicyManager
from src.nupolicy.integration import create_monitor_from_policy
from src.nuledger import Ledger

# Load policy
manager = PolicyManager()
policy = manager.load_policy("conservative")

# Create monitor from policy
ledger = Ledger()
monitor = create_monitor_from_policy(policy, ledger=ledger)

# Monitor operations
from src.nucore import add
n, u = add(10.0, 0.5, 20.0, 1.0)
monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n, u))
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 6: NUGovern                        │
│              HTTP API for Governance & Attestation          │
│                    (FastAPI + Uvicorn)                      │
├─────────────────────────────────────────────────────────────┤
│                    Layer 5: NUPolicy                        │
│              Policy Management & Configuration              │
│               (JSON policies + Ed25519 signing)             │
├─────────────────────────────────────────────────────────────┤
│                    Layer 4: NUGuard                         │
│              Runtime Monitoring & Violation Detection       │
│                   (Event-driven monitoring)                 │
├─────────────────────────────────────────────────────────────┤
│                    Layer 3: NULedger                        │
│              Cryptographic Audit Ledger                     │
│            (Merkle tree + Ed25519 + SHA-256)                │
├─────────────────────────────────────────────────────────────┤
│                    Layer 2: NUProof                         │
│              Formal Verification Framework                  │
│                    (Lean 4 proofs)                          │
├─────────────────────────────────────────────────────────────┤
│                    Layer 1: NUCore                          │
│              N/U Algebra Computation Kernel                 │
│            (Deterministic uncertainty propagation)          │
├─────────────────────────────────────────────────────────────┤
│                    Layer 0: eBIOS                           │
│              Immutable Foundation (4 functions)             │
│           Verify • Seal • Unseal • Attest                   │
└─────────────────────────────────────────────────────────────┘
```

## Core Philosophy

> **"You can run what you want above it, but you can't hide what you did."**

eBIOS enforces three principles:

1. **Immutability**: No updates, no deletes, only appends
2. **Provability**: Every claim is mathematically verifiable
3. **Accountability**: Every action generates an auditable trace

## Test Coverage

| Layer | Tests | Status |
|-------|-------|--------|
| NUCore | 39 | ✅ 100% |
| NULedger | 38 | ✅ 100% |
| NUGuard | 32 | ✅ 100% |
| NUPolicy | 41 | ✅ 100% |
| NUGovern | 22 | ✅ 100% |
| **TOTAL** | **172** | **✅ 100%** |

## Performance Characteristics

| Operation | Complexity | Actual Performance |
|-----------|------------|-------------------|
| NUCore operations | O(1) | < 1μs |
| Ledger append | O(log n) | < 1ms |
| Ledger query | O(k) | < 5ms (k=100) |
| Monitor check | O(r) | < 100μs (r=5 rules) |
| Policy validation | O(r) | < 1ms |
| API endpoint | O(op) | < 10ms |

Tested with n=1000+ entries, r=10+ rules.

## Security Model

### Cryptographic Primitives

- **Ed25519**: Digital signatures (ledger, policies)
- **SHA-256**: Content fingerprinting (Merkle tree, policy hashes)
- **Merkle Trees**: O(log n) integrity proofs

### Invariants Enforced

1. **Non-negativity**: u ≥ 0 always
2. **Enclosure preservation**: Intervals remain conservative
3. **Monotonic timestamps**: Ledger ordering cannot be violated
4. **Append-only**: No updates or deletes in ledger
5. **Signature integrity**: Tampering invalidates signatures

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## License

Apache 2.0 with immutability clause - see [LICENSE](../LICENSE)

## References

- **Repository**: https://github.com/abba-01/ebios
- **Issues**: https://github.com/abba-01/ebios/issues
- **Documentation**: All specs in `/docs` directory

## Version

- **eBIOS Version**: 0.1.0
- **Status**: Development (Phases 0-6 complete)
- **Last Updated**: 2025-10-20

---

**eBIOS** — Truth is a data structure, not a declaration.
