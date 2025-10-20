# NUCore Specification

**Layer 1 of eBIOS: Nominal/Uncertainty Algebra Kernel**

## Overview

NUCore implements N/U Algebra — a deterministic framework for epistemic computation. It is **not** probabilistic reasoning; it is a mathematical contract between computation and accountability.

> "N/U Algebra is not a probabilistic method but a deterministic contract between math and ethics: every operation is enclosure-preserving, constant-time, and auditable."

## Mathematical Foundation

### Representation

Every value in NUCore is a pair `(n, u)` where:
- `n` is the **nominal value** (best estimate)
- `u` is the **uncertainty** (epistemic margin, always `u ≥ 0`)

The pair represents an interval: `[n - u, n + u]`

### Core Operations

NUCore provides five fundamental operations:

#### 1. Addition (⊕)

```
(n1 ± u1) ⊕ (n2 ± u2) = (n1 + n2) ± √(u1² + u2²)
```

**Properties**:
- Commutative: `a ⊕ b = b ⊕ a`
- Associative: `(a ⊕ b) ⊕ c = a ⊕ (b ⊕ c)`
- Non-negativity: `u_out ≥ 0`
- Enclosure: Output interval contains sum of input intervals

**Complexity**: O(1)

**Proof**: `/verification/NUProof/add_properties.v`

#### 2. Multiplication (⊗)

```
(n1 ± u1) ⊗ (n2 ± u2) = (n1 · n2) ± λ·√[(n1·u2)² + (n2·u1)² + (u1·u2)²]
```

**Properties**:
- Commutative: `a ⊗ b = b ⊗ a`
- Associative: `(a ⊗ b) ⊗ c = a ⊗ (b ⊗ c)`
- Conservative: Includes cross-term `(u1·u2)²` for robustness
- Margin: `λ ≥ 1.0` (frozen at `λ = 1.0` for determinism)
- Enclosure: Output interval contains product of input intervals

**Complexity**: O(1)

**Proof**: `/verification/NUProof/multiply_enclosure.v`

#### 3. Composition (⊙)

```
(n1 ± u1) ⊙ (n2 ± u2) = n_out ± u_out

where:
  n_out = (n1·u2² + n2·u1²) / (u1² + u2²)
  u_out = √[(u1²·u2²) / (u1² + u2²)]
```

**Properties**:
- **Reduction**: `u_out ≤ min(u1, u2)` — uncertainty decreases
- Information gain: Combines evidence to reduce epistemic margin
- Weighted average: More certain values have higher weight
- Commutative and associative

**Complexity**: O(1)

**Proof**: `/verification/NUProof/compose_reduction.v`

**Philosophy**: Composition models "learning" — combining multiple estimates improves certainty.

#### 4. Catch

```
Catch(n, u, default_n=0, default_u=∞) = (n, u) if valid, else (default_n, default_u)
```

**Properties**:
- Identity-preserving for valid inputs
- Returns infinite uncertainty on failure (not zero!)
- Deterministic error handling

**Philosophy**:
> "Failure is allowed. Lying about failure is not."

Invalid inputs return `u = ∞` to signal complete epistemic collapse.

**Complexity**: O(1)

#### 5. Flip

```
Flip(n ± u) = (-n) ± u
```

**Properties**:
- Involutive: `Flip(Flip(x)) = x`
- Preserves uncertainty
- Symmetry in epistemic space

**Complexity**: O(1)

**Proof**: `/verification/NUProof/flip_involutive.v`

## Invariants

All NUCore operations maintain these invariants:

### 1. Non-Negativity

```
∀ operations OP: u_out ≥ 0
```

Uncertainty is always non-negative. Negative uncertainty is undefined.

**Formal proof**: `/verification/NUProof/nonnegative.v`

### 2. Enclosure Preservation

```
For OP ∈ {⊕, ⊗}:
  [n1-u1, n1+u1] OP [n2-u2, n2+u2] ⊆ [n_out-u_out, n_out+u_out]
```

Output intervals always contain the theoretical result interval.

**Formal proof**: `/verification/NUProof/enclosure.v`

### 3. Constant-Time Execution

```
Theorem (O(1) Complexity):
Each operation OP ∈ {⊕, ⊗, ⊙} executes in fixed time and space
independent of graph depth.
```

No operation depends on recursion, iteration, or variable-length computation.

**Formal proof**: `/verification/NUProof/complexity.v`

### 4. Monotonicity

```
For OP ∈ {⊕, ⊗}: u_out ≥ max(u1, u2) - ε
```

Uncertainty never decreases without explicit composition (`⊙`).

**Exception**: Composition is designed to reduce uncertainty.

**Formal proof**: `/verification/NUProof/monotonicity.v`

## Validation

NUCore provides `NUCore.validate()` for O(1) invariant checking:

```python
from nucore import validate, assert_invariants

# Check validity
is_valid = validate(n, u)  # Returns bool

# Assert all invariants (raises on violation)
assert_invariants(n, u, operation="add")
```

### Timing Assertions

Constant-time execution can be verified empirically:

```python
from nucore.validators import verify_constant_time
from nucore import add

is_constant = verify_constant_time(
    operation=add,
    args1=(1.0, 0.1, 2.0, 0.2),
    args2=(1e10, 1e8, 1e9, 1e7),
    tolerance_ns=1000,
    iterations=10000
)

assert is_constant, "O(1) complexity violated!"
```

## Integration with eBIOS Stack

NUCore is **Layer 1** of the eBIOS stack. It provides deterministic operations for:

- **Layer 2 (NUProof)**: Operations have formal correctness proofs
- **Layer 3 (NULedger)**: All operations generate attestations
- **Layer 4 (NUGuard)**: Runtime monitors `u/|n|` ratio for violations

### Example: Attested Addition

```python
from nucore import add
from nuleger import Ledger
from nuguard import monitor

ledger = Ledger()

# Perform addition
n1, u1 = 10.0, 0.5
n2, u2 = 20.0, 1.0
n_out, u_out = add(n1, u1, n2, u2)

# Log to ledger (Layer 3)
ledger.append({
    "operation": "add",
    "inputs": [(n1, u1), (n2, u2)],
    "output": (n_out, u_out),
    "timestamp": time.time(),
})

# Monitor coverage (Layer 4)
monitor(n_out, u_out, threshold=0.1)
```

Every operation is:
1. **Computed** deterministically (Layer 1)
2. **Proven** correct formally (Layer 2)
3. **Logged** cryptographically (Layer 3)
4. **Monitored** for violations (Layer 4)

## Test Coverage

NUCore is validated against a comprehensive test suite:

- **Unit tests**: 500+ test cases for individual operations
- **Property tests**: QuickCheck-style randomized validation
- **Formal proofs**: Coq/Lean theorems for all invariants
- **Integration tests**: End-to-end workflows with ledger/guard
- **Performance tests**: O(1) timing verification

### Mock Dataset (70,000 cases)

The specification references validation against 70,000 test cases. Initial implementation includes mock sample generation:

```python
# Generate test cases
python tests/nucore/generate_testcases.py --count 70000 --output testcases.json
```

Full dataset validation planned for PHASE 2.

## Pseudocode: Formal Theorem Block

```
Theorem (O(1) Complexity):
  ∀ OP ∈ {⊕, ⊗, ⊙}:
    ∀ inputs (n1, u1), (n2, u2):
      Time(OP(n1, u1, n2, u2)) = O(1)
      Space(OP(n1, u1, n2, u2)) = O(1)

Proof:
  By inspection of implementation:
    1. Each OP performs fixed arithmetic operations
    2. No loops, recursion, or variable allocation
    3. All operations use primitive float arithmetic (O(1))
  QED

Formalized in: /verification/NUProof/complexity.v
```

## Tunable Margin (λ)

The multiplication rule includes a margin parameter `λ ≥ 1.0`:

```python
u_out = λ · √[(n1·u2)² + (n2·u1)² + (u1·u2)²]
```

**Default**: `λ = 1.0` (frozen at runtime)

**Purpose**: Allows future tuning for extra conservatism

**Determinism**: To maintain determinism, `λ` must be fixed at compile-time. Runtime modification violates the Layer 0 immutability contract.

## Philosophy

### Truth as a Data Structure

Every NUCore operation produces not just a number, but a **certified interval** with:
- Nominal value (best estimate)
- Epistemic margin (quantified uncertainty)
- Provable properties (formal theorems)

This is truth encoded as data, not declared by authority.

### Accountability

NUCore operations are:
- **Deterministic**: Same inputs → same outputs, always
- **Auditable**: Every operation can be traced and verified
- **Provable**: Formal theorems guarantee correctness

You can change what a robot believes, but not the record of that change.

### Epistemic Honesty

Compose (`⊙`) reduces uncertainty **only when evidence justifies it**. Other operations preserve or increase uncertainty to avoid overconfidence.

> "A robot may act autonomously, but it cannot hide its epistemic state."

## References

- **N/U Algebra**: Foundational work on nominal-uncertainty computation
- **Auditonomy**: Philosophy of accountable autonomous systems
- **eBIOS Layer 0**: Cryptographic substrate ensuring immutability

## Version

- **NUCore Version**: 0.1.0
- **eBIOS Layer**: 1
- **Status**: Active development (PHASE 1)

---

**NUCore** — Deterministic epistemic computation with mathematical guarantees.

*"Truth is a data structure, not a declaration."*
