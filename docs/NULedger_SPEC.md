# NULedger Specification

**Layer 3 of eBIOS: Cryptographic Audit Ledger**

## Overview

NULedger is the immutable audit log layer of eBIOS, providing cryptographically signed, Merkle-chained logging of all NUCore operations. It enforces the principle that every computation must leave a verifiable trace.

> "Truth is a data structure, not a declaration."

## Purpose

NULedger ensures that:
1. **Complete Auditability**: Every NUCore operation is logged with full provenance
2. **Tamper Evidence**: Any modification to history is cryptographically detectable
3. **Causal Traceability**: Complete parent-child chains can be reconstructed
4. **Cryptographic Attestation**: All entries are signed with eBIOS Layer 0 keypair

## Architecture

```
NULedger (Layer 3)
├── Ledger Core          -- Append-only log with Ed25519 signing
├── Merkle Tree          -- O(log n) verification and tamper detection
├── Storage Backends     -- Memory, SQLite, LMDB options
└── CLI Tool             -- Audit trail queries and verification
```

### Integration with eBIOS Stack

| Layer | Integration |
|-------|-------------|
| **Layer 0 (eBIOS)** | Signs entries with Layer 0 keypair |
| **Layer 1 (NUCore)** | All operations generate ledger entries |
| **Layer 2 (NUProof)** | Proof hashes logged in ledger |
| **Layer 4 (NUGuard)** | Reads ledger for runtime monitoring |
| **Layer 6 (NUGovern)** | Provides audit API access |

## Data Structures

### LedgerEntry

```python
@dataclass
class LedgerEntry:
    timestamp: int              # Monotonic counter (not wall clock)
    op_id: str                  # UUID for this operation
    parent_id: Optional[str]    # Parent operation (causal chain)
    operation: str              # Operation name (add, multiply, etc.)
    inputs: List[tuple]         # Input N/U pairs
    output: tuple               # Output N/U pair
    coverage: float             # u/|n| ratio
    invariant_passed: bool      # Whether invariants held
    signature: str              # Ed25519 signature of entry hash
```

**Properties**:
- **Immutable**: No field can be modified after creation
- **Self-Hashing**: Entry hash excludes signature (for signing)
- **Serializable**: JSON and msgpack supported

### Ledger

```python
class Ledger:
    def append(
        operation: str,
        inputs: List[tuple],
        output: tuple,
        coverage: float,
        invariant_passed: bool,
        parent_id: Optional[str] = None
    ) -> LedgerEntry

    def trace(op_id: str) -> List[LedgerEntry]

    def get_root() -> str

    def verify_integrity() -> bool
```

**Properties**:
- **Append-Only**: No updates or deletes
- **Merkle-Chained**: Each append updates Merkle root
- **Backend-Agnostic**: Supports multiple storage engines

## Core Operations

### 1. Append Entry

**Signature**:
```python
entry = ledger.append(
    operation="add",
    inputs=[(10.0, 0.5), (20.0, 1.0)],
    output=(30.0, 1.12),
    coverage=0.037,
    invariant_passed=True,
    parent_id=None  # Optional: link to parent operation
)
```

**Process**:
1. Generate unique UUID for `op_id`
2. Increment monotonic timestamp counter
3. Create entry (without signature)
4. Compute SHA-256 hash of entry
5. Sign hash with Ed25519 private key
6. Append entry hash to Merkle tree
7. Store entry in backend
8. Return signed entry

**Complexity**: O(log n) due to Merkle tree update

**Guarantees**:
- Timestamp is strictly monotonic
- Signature is cryptographically valid
- Merkle root includes this entry

---

### 2. Trace Causal Chain

**Signature**:
```python
chain = ledger.trace(op_id)
```

**Returns**: List of entries from root ancestor to `op_id` (chronological order)

**Example**:
```python
# Create causal chain
e1 = ledger.append("add", [...], (...), 0.1, True)
e2 = ledger.append("multiply", [...], (...), 0.2, True, parent_id=e1.op_id)
e3 = ledger.append("compose", [...], (...), 0.15, True, parent_id=e2.op_id)

# Trace from leaf
chain = ledger.trace(e3.op_id)
# Returns: [e1, e2, e3]
```

**Complexity**: O(k) where k is chain depth

**Use Cases**:
- Debugging: "How did we arrive at this result?"
- Compliance: "What operations led to this decision?"
- Provenance: "Who is responsible for this value?"

---

### 3. Verify Integrity

**Signature**:
```python
is_valid = ledger.verify_integrity()
```

**Checks**:
1. **Monotonic Timestamps**: Each entry has `timestamp > previous.timestamp`
2. **Merkle Consistency**: Computed Merkle root matches stored root
3. **Signature Validity**: (requires public key, optional)

**Returns**: `True` if all checks pass, `False` otherwise

**Complexity**: O(n) for full ledger scan

**Failure Modes**:
- Non-monotonic timestamps → tampered entry order
- Merkle root mismatch → modified entry data
- Invalid signature → forged entry (if key available)

---

### 4. Get Merkle Root

**Signature**:
```python
root = ledger.get_root()
```

**Returns**: SHA-256 hash of current Merkle root

**Properties**:
- **Unique**: Each ledger state has unique root
- **Deterministic**: Same entries → same root
- **Tamper-Evident**: Any change → different root

**Use Cases**:
- Attestation reports
- Integrity checkpoints
- Distributed verification

## Merkle Tree

### Structure

NULedger uses a **binary Merkle tree** for efficient verification:

```
         Root (H_ABCD)
        /            \
    H_AB              H_CD
   /    \            /    \
  H_A    H_B       H_C    H_D
   |      |         |      |
  E1     E2        E3     E4
```

Where:
- `H_A = SHA256(entry1.hash())`
- `H_AB = SHA256(H_A + H_B)`
- Root = `H_ABCD`

### Proof Generation

```python
proof = ledger.merkle.generate_proof(index)
```

**Returns**: `MerkleProof` with:
- `leaf_hash`: Hash of entry at index
- `path`: List of (sibling_hash, direction) tuples
- `root`: Merkle root at time of proof

**Verification**:
```python
assert proof.verify()  # Checks path leads to root
```

**Complexity**: O(log n) proof size and verification

**Use Case**: Prove entry inclusion without revealing entire ledger

## Storage Backends

### MemoryBackend

**Purpose**: In-memory storage for testing and ephemeral sessions

**Properties**:
- ✅ Fast (native Python data structures)
- ✅ Simple (no external dependencies)
- ❌ Non-persistent (data lost on exit)
- ❌ Limited capacity (RAM only)

**Usage**:
```python
backend = MemoryBackend()
ledger = Ledger(backend=backend)
```

---

### SQLiteBackend

**Purpose**: Persistent storage with ACID guarantees

**Properties**:
- ✅ Persistent (survives process restarts)
- ✅ ACID transactions
- ✅ Efficient queries (indexed)
- ✅ Cross-platform
- ✅ Small footprint (~600KB)
- ⚠️ Single-process (no concurrent writers)

**Schema**:
```sql
CREATE TABLE ledger (
    timestamp INTEGER NOT NULL,
    op_id TEXT PRIMARY KEY,
    parent_id TEXT,
    operation TEXT NOT NULL,
    inputs TEXT NOT NULL,      -- JSON array
    output TEXT NOT NULL,       -- JSON tuple
    coverage REAL NOT NULL,
    invariant_passed INTEGER NOT NULL,
    signature TEXT NOT NULL
);

CREATE INDEX idx_parent_id ON ledger(parent_id);
CREATE INDEX idx_timestamp ON ledger(timestamp);
```

**Usage**:
```python
backend = SQLiteBackend("audit.db")
ledger = Ledger(backend=backend)
```

---

### LMDBBackend (Future)

**Purpose**: High-performance embedded database for production

**Properties**:
- ✅ Ultra-fast reads (memory-mapped)
- ✅ Concurrent readers
- ✅ Compact storage
- ✅ Excellent for embedded systems
- ⏳ Status: Planned for future release

**Estimated Performance**:
- Reads: ~1M ops/sec
- Writes: ~100K ops/sec
- Storage: ~50% smaller than SQLite

## Command-Line Interface

### Installation

```bash
# Make CLI executable
chmod +x src/nuledger/cli.py

# Create symlink (optional)
ln -s src/nuledger/cli.py /usr/local/bin/nuledger
```

### Commands

#### Trace Causal Chain

```bash
nuledger trace <op_id> [--db path/to/ledger.db]
```

**Output**:
```
Causal Chain for abc-123-def-456
======================================================================

[0] ADD
    Op ID:      root-op-id
    Timestamp:  1
    Parent:     (root)
    Inputs:     [(10.0, 0.5), (20.0, 1.0)]
    Output:     (30.0, 1.12)
    Coverage:   0.037333
    Invariants: ✓ PASS
    Signature:  ed25519:a7f3c8d9e1b4f2a6...

[1] MULTIPLY
    Op ID:      abc-123-def-456
    Timestamp:  2
    Parent:     root-op-id
    Inputs:     [(30.0, 1.12), (2.0, 0.1)]
    Output:     (60.0, 5.64)
    Coverage:   0.094000
    Invariants: ✓ PASS
    Signature:  ed25519:b2c4d7a8f3e1...

Chain length: 2 operations
Merkle root:  e4b2f1a8c3d79fa...
```

---

#### Verify Integrity

```bash
nuledger verify [--db path/to/ledger.db]
```

**Output** (success):
```
✅ Ledger integrity verified!

  Entries:     1,234
  Merkle root: e4b2f1a8c3d79fa...
```

**Output** (failure):
```
❌ Ledger integrity check FAILED!

Possible causes:
  - Tampered entries
  - Invalid signatures
  - Non-monotonic timestamps
```

---

#### Show Statistics

```bash
nuledger stats [--db path/to/ledger.db]
```

**Output**:
```
NULedger Statistics
======================================================================

Total Entries:        1,234
Merkle Root:          e4b2f1a8c3d79fa...
Average Coverage:     0.082456
Failed Invariants:    0

Operations:
  add              523  ( 42.4%)
  multiply         412  ( 33.4%)
  compose          256  ( 20.7%)
  flip              43  (  3.5%)
```

---

#### Export to JSON

```bash
nuledger export audit_report.json [--db path/to/ledger.db]
```

**Output File**:
```json
{
  "merkle_root": "e4b2f1a8c3d79fa...",
  "entry_count": 1234,
  "entries": [
    {
      "timestamp": 1,
      "op_id": "...",
      "operation": "add",
      ...
    }
  ]
}
```

---

#### Show Merkle Root

```bash
nuledger root [--db path/to/ledger.db]
```

**Output**:
```
e4b2f1a8c3d79fa6b2c1d8e9f0a3b7c4d1e2f5a8b9c0d3e6f1a4b7c2d5e8f1a
```

## Integration Patterns

### Pattern 1: NUCore Operation Logging

```python
from nucore import add
from nuledger import Ledger

ledger = Ledger()

# Perform operation
n1, u1 = 10.0, 0.5
n2, u2 = 20.0, 1.0
n_out, u_out = add(n1, u1, n2, u2)

# Log to ledger
entry = ledger.append(
    operation="add",
    inputs=[(n1, u1), (n2, u2)],
    output=(n_out, u_out),
    coverage=u_out / abs(n_out) if n_out != 0 else float('inf'),
    invariant_passed=True
)

print(f"Logged: {entry.op_id}")
```

---

### Pattern 2: Chained Operations

```python
ledger = Ledger()

# First operation
e1 = ledger.append("add", [...], (...), 0.1, True)

# Second operation (depends on first)
e2 = ledger.append(
    "multiply",
    [...],
    (...),
    0.2,
    True,
    parent_id=e1.op_id  # Link to parent
)

# Trace chain
chain = ledger.trace(e2.op_id)
assert len(chain) == 2
```

---

### Pattern 3: Failed Invariant Logging

```python
# Operation with failed invariant
try:
    result = some_operation(invalid_input)
except InvariantViolation as e:
    # Still log the failure!
    entry = ledger.append(
        operation="failed_op",
        inputs=[invalid_input],
        output=(0.0, float('inf')),  # Infinite uncertainty
        coverage=float('inf'),
        invariant_passed=False  # Flag as failed
    )

    raise  # Re-raise after logging
```

> "Failure is allowed. Lying about failure is not."

---

### Pattern 4: Merkle Proof Verification

```python
ledger = Ledger()

# Add 1000 entries
for i in range(1000):
    ledger.append(f"op{i}", [...], (...), 0.1, True)

# Generate proof for entry 500
proof = ledger.merkle.generate_proof(500)

# Verify proof (O(log n), not O(n)!)
assert proof.verify()

# Export proof for external verification
proof_data = {
    "leaf_hash": proof.leaf_hash,
    "path": proof.path,
    "root": proof.root
}
```

## Cryptographic Attestation

### Signing Process

1. **Entry Creation**: Create `LedgerEntry` with `signature=""`
2. **Hashing**: Compute `SHA256(entry.to_json())` excluding signature
3. **Signing**: Sign hash with Ed25519 private key
4. **Storage**: Store entry with embedded signature

**Key Management**:
- Private key: eBIOS Layer 0 keypair (never exposed)
- Public key: Published for verification
- Rotation: Not supported (immutability requirement)

### Verification Process

```python
def verify_entry(entry: LedgerEntry, public_key) -> bool:
    # 1. Extract signature
    signature = bytes.fromhex(entry.signature)

    # 2. Recompute entry hash (without signature)
    entry_copy = entry.to_dict()
    entry_copy.pop('signature')
    entry_hash = hashlib.sha256(
        json.dumps(entry_copy, sort_keys=True).encode()
    ).digest()

    # 3. Verify signature
    try:
        public_key.verify(signature, entry_hash)
        return True
    except:
        return False
```

### Attestation Report

```json
{
  "ledger_snapshot": {
    "merkle_root": "e4b2f1a8c3d79fa...",
    "entry_count": 1234,
    "timestamp": "2025-10-20T12:00:00Z",
    "signature": "ed25519:a7f3c8d9e1b4f2a6..."
  },
  "proof": {
    "entry_index": 500,
    "leaf_hash": "b2c4d7a8f3e1...",
    "merkle_path": [...]
  }
}
```

## Performance Characteristics

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Append | O(log n) | O(1) |
| Trace | O(k) where k = chain depth | O(k) |
| Get Root | O(1) (cached) | O(1) |
| Verify Integrity | O(n) | O(n) |
| Generate Proof | O(log n) | O(log n) |
| Verify Proof | O(log n) | O(1) |

**Scalability**:
- 1,000 entries: ~10 levels in Merkle tree
- 1,000,000 entries: ~20 levels in Merkle tree
- 1,000,000,000 entries: ~30 levels in Merkle tree

**Storage**:
- SQLite: ~500 bytes per entry
- Memory: ~300 bytes per entry (Python objects)
- LMDB (future): ~250 bytes per entry

## Testing

### Test Coverage

**38 comprehensive tests** covering:

**LedgerEntry** (3 tests):
- Entry creation and validation
- Hashing (signature exclusion)
- JSON serialization

**Ledger** (10 tests):
- Append operations
- Monotonic timestamps
- Causal chains
- Merkle root updates
- Integrity verification
- Multiple operation types

**Backends** (3 tests):
- MemoryBackend operations
- SQLiteBackend (in-memory and persistent)
- File persistence across restarts

**Merkle Tree** (16 tests):
- Empty, single, and multiple leaves
- Root caching and determinism
- Proof generation and verification
- Odd/even leaf counts
- Large tree performance

**Edge Cases** (4 tests):
- Empty ledger root
- Nonexistent operation trace
- Failed invariant logging
- Large ledger performance (1000 entries)

**Property Tests** (3 tests):
- Append monotonicity
- Root change on append
- Proof consistency

### Running Tests

```bash
# All NULedger tests
pytest tests/nuledger/ -v

# With coverage
pytest tests/nuledger/ --cov=src/nuledger --cov-report=html

# Specific test file
pytest tests/nuledger/test_merkle.py -v
```

## Security Considerations

### Threat Model

**Assumptions**:
- ✅ Private key is secure (stored in eBIOS Layer 0)
- ✅ SQLite/LMDB backends are trusted
- ✅ Operating system is not compromised
- ❌ Adversary cannot access private key
- ❌ Adversary can read ledger contents
- ❌ Adversary can attempt to tamper with entries

**Protections**:
1. **Tamper Detection**: Merkle root changes on any modification
2. **Signature Verification**: Invalid signatures detected immediately
3. **Timestamp Monotonicity**: Entry reordering detected
4. **Immutability**: No update/delete operations exist

**Limitations**:
- ⚠️ Does not prevent read access (confidentiality not guaranteed)
- ⚠️ Does not prevent denial-of-service (availability not guaranteed)
- ⚠️ Requires secure key storage (relies on eBIOS Layer 0)

### Best Practices

1. **Key Management**:
   - Never log private key
   - Rotate public key on deployment (but keep old for verification)
   - Use hardware security module (HSM) in production

2. **Storage**:
   - Use file system permissions to restrict access
   - Enable SQLite WAL mode for better concurrency
   - Backup ledger regularly (append-only = safe backups)

3. **Monitoring**:
   - Run `verify_integrity()` periodically
   - Alert on failed invariants
   - Track Merkle root in external audit log

## Philosophy

### Truth as Data Structure

Every entry in NULedger is not a "log message" — it's a **mathematical object** with:
- SHA-256 hash (content fingerprint)
- Ed25519 signature (cryptographic attestation)
- Merkle proof (verifiable inclusion)

You don't "trust" the ledger. You **verify** it.

### Accountability Without Judgment

NULedger records what happened, not whether it was "good" or "bad":

> "Failure is allowed. Lying about failure is not."

Failed invariants are logged with `invariant_passed=False` and infinite uncertainty. This is not punishment — it's honesty.

### Local Verification, Global Trust

Anyone with the public key can verify:
1. Signatures are valid
2. Merkle root is correct
3. Causal chains are intact

No need to trust the operator. Just verify the math.

> "Verification is local; trust is global. eBIOS is the common denominator for honesty."

## References

- **Merkle Trees**: Merkle, R. (1988). "A Digital Signature Based on a Conventional Encryption Function"
- **Ed25519**: Bernstein, D. et al. (2011). "High-speed high-security signatures"
- **SQLite**: https://www.sqlite.org/
- **eBIOS Layer 0**: `/docs/README.md`
- **NUCore Operations**: `/docs/NUCore_SPEC.md`

## Version

- **NULedger Version**: 0.1.0
- **eBIOS Layer**: 3
- **Status**: Active development (PHASE 3)

---

**NULedger** — Immutable truth, cryptographically attested.

*"Truth is a data structure, not a declaration."*
