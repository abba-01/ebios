# NUProof: Formal Verification Framework

**eBIOS Layer 2: Mathematical proof system for NUCore operations**

## Overview

NUProof provides formal verification of NUCore's mathematical properties using Lean 4 theorem prover. Every operation in NUCore has corresponding formal proofs guaranteeing correctness.

> "Verification is not a bureaucratic act — it is the ceremony that proves the system's integrity. eBIOS does not request trust; it performs it."

## Proven Theorems

### Core Invariants

1. **Non-Negativity** (`NonNegativity.lean`)
   - Theorem: ∀ operations OP: u_out ≥ 0
   - Status: Complete (proven by construction)

2. **Enclosure Preservation** (`Enclosure.lean`)
   - Theorem: Output intervals contain all possible results
   - Status: Skeleton (requires interval arithmetic lemmas)

3. **Constant-Time Complexity** (`Complexity.lean`)
   - Theorem: All operations execute in O(1) time and space
   - Status: Skeleton (meta-theorem about computational model)

### Algebraic Properties

4. **Addition Properties** (`AddProperties.lean`)
   - Commutativity: a ⊕ b = b ⊕ a (Complete)
   - Associativity: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) (Skeleton)

5. **Flip Involution** (`FlipInvolutive.lean`)
   - Theorem: Flip(Flip(x)) = x
   - Status: Complete

6. **Composition Reduction** (`ComposeReduction.lean`)
   - Theorem: u_out ≤ min(u₁, u₂)
   - Status: Skeleton (requires algebraic manipulation)

7. **Monotonicity** (`Monotonicity.lean`)
   - Theorem: Operations preserve or increase uncertainty
   - Status: Skeleton (requires inequality lemmas)

## Project Structure

```
/verification/NUProof/
  NUCore.lean              -- Core definitions
  NonNegativity.lean       -- u ≥ 0 proofs
  Enclosure.lean           -- Interval containment proofs
  AddProperties.lean       -- Addition algebraic properties
  FlipInvolutive.lean      -- Flip involution proof
  ComposeReduction.lean    -- Composition reduces uncertainty
  Complexity.lean          -- O(1) complexity proof
  Monotonicity.lean        -- Uncertainty monotonicity

  lakefile.lean            -- Lean project configuration
  lean-toolchain           -- Lean version specification

  generate_proof_hashes.py -- Cryptographic hash generator
  proof_manifest.json      -- Signed proof hashes
  README.md                -- This file
```

## Building Proofs

### Prerequisites

```bash
# Install Lean 4
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Update Lean toolchain
elan update
```

### Build and Verify

```bash
cd verification/NUProof

# Fetch dependencies (Mathlib)
lake update

# Build proofs
lake build

# Check specific proof
lean NonNegativity.lean
```

### Generate Proof Hashes

```bash
# Install Python dependencies
pip install cryptography

# Generate signed proof hashes
python generate_proof_hashes.py
```

This creates `proof_manifest.json` with:
- SHA-256 hash of each proof file
- Ed25519 signature for attestation
- Proof status (complete vs skeleton)

## Proof Status Levels

| Status | Meaning |
|--------|---------|
| **Complete** | Fully formalized with `#check` passing, no `sorry` |
| **Skeleton** | Structure defined, contains `sorry` or `axiom` placeholders |

Current status:
- **Complete**: 3 theorems (NonNegativity, FlipInvolutive, AddCommutativity)
- **Skeleton**: 5 theorems (require additional lemmas)

## Integration with eBIOS

### Layer 2 Attestation

Each proof generates a cryptographic attestation:

```json
{
  "filename": "NonNegativity.lean",
  "sha256": "a7f3c8d9...",
  "signature": "ed25519:e4b2f1a8...",
  "status": "complete"
}
```

These attestations are embedded in:
- **Layer 3 (NULedger)**: Proof hashes logged in Merkle chain
- **Layer 7 (Certification)**: Proof status included in compliance reports

### CI Integration

The GitHub Actions pipeline automatically:
1. Builds all Lean proofs on commit
2. Generates proof hashes
3. Fails if any complete proof contains `sorry`
4. Updates proof manifest

See `.github/workflows/verify-proofs.yml`

## Extending Proofs

To add a new theorem:

1. **Create proof file** (e.g., `NewTheorem.lean`)
2. **Import dependencies**: `import NUProof.NUCore`
3. **State theorem**: Use `theorem` keyword
4. **Provide proof or `sorry`**
5. **Update this README** with theorem description
6. **Regenerate hashes**: `python generate_proof_hashes.py`

Example:

```lean
import NUProof.NUCore

namespace NUCore

theorem my_new_property (p : NUPair) :
  p.u ≥ 0 := by
  exact p.h_nonneg

end NUCore
```

## Philosophy

### Truth as Data Structure

Every proof is:
- **Formal**: Written in Lean's type theory
- **Checkable**: Verifiable by Lean kernel
- **Attested**: Cryptographically signed hash

This is not "code review" — it's **mathematical certainty**.

### Verification Without Trust

> "Verification is local; trust is global. eBIOS is the common denominator for honesty."

Anyone can:
1. Download the proofs
2. Run Lean to verify them
3. Check the proof hashes
4. Validate the signatures

No trust required — only computation.

## Development Roadmap

### Near-term (PHASE 2)
- ✅ Create proof skeletons for all theorems
- ✅ Set up Lean project structure
- ✅ Implement proof hash generation
- ⏳ Add CI pipeline for automated verification
- ⏳ Complete AddAssociativity proof
- ⏳ Complete Enclosure proofs

### Medium-term (PHASE 3+)
- Complete all skeleton proofs
- Add Coq alternative implementations
- Formal verification of Python implementation correspondence
- Hardware attestation integration

## License

Apache License 2.0 with immutability requirement (see eBIOS LICENSE)

## References

- **Lean 4**: https://leanprover.github.io/
- **Mathlib**: https://leanprover-community.github.io/
- **eBIOS Specification**: `/docs/README.md`
- **NUCore Specification**: `/docs/NUCore_SPEC.md`

---

**NUProof** — Mathematical proof that uncertainty is honest.

*"Truth is a data structure, not a declaration."*
