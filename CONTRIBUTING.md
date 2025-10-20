# Contributing to eBIOS

Thank you for your interest in contributing to **eBIOS** — the epistemic substrate for honest machines.

## Philosophy of Contribution

eBIOS is not a typical open-source project. Contributions are welcome, but they must **preserve the immutability guarantees** and **cryptographic integrity** that define the project. This document outlines the principles and practices for contributing effectively.

> "Truth is a data structure, not a declaration."

All contributions must uphold this principle.

## Core Principles

Every contribution to eBIOS must:

1. **Maintain Immutability** — No runtime state mutation; all updates must be append-only
2. **Preserve Determinism** — Identical inputs must produce identical outputs
3. **Extend Auditability** — All operations must generate verifiable attestations
4. **Include Formal Proofs** — New operations require formal verification of correctness
5. **Document Thoroughly** — Clear specifications explaining the "why" and the "how"

## What We Accept

### ✅ Accepted Contributions

- **Core algorithm improvements** with formal proofs of correctness
- **New attestation mechanisms** that enhance cryptographic guarantees
- **Performance optimizations** that maintain O(1) complexity bounds
- **Formal verification additions** (Coq, Lean, or equivalent theorem provers)
- **Documentation enhancements** that clarify architecture or philosophy
- **Hardware integration** for TPM, secure enclaves, or attestation devices
- **Test coverage expansions** with reproducible verification cases
- **Bug fixes** that restore immutability or determinism guarantees

### ❌ Not Accepted

- Changes introducing **mutable state** in core substrate (Layers 0–3)
- Removal or weakening of **attestation requirements**
- Features that **obscure audit trails** or reduce transparency
- Non-deterministic behavior in **core operations**
- Configuration parameters that allow **runtime behavior modification**
- "Nice to have" features that violate the **Layer 0 philosophy**

## Contribution Workflow

### 1. Open an Issue First

Before writing code, **open a GitHub issue** describing:

- **What problem you're solving** (or what capability you're adding)
- **Why it aligns with eBIOS philosophy** (immutability, attestation, provability)
- **How it maintains Layer 0 guarantees** (no mutable state, deterministic execution)

This allows maintainers to provide feedback **before** you invest time in implementation.

### 2. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/yourusername/ebios.git
cd ebios
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/nucore-division-proof` (new capability)
- `fix/ledger-signature-validation` (bug fix)
- `docs/nuproof-specification` (documentation)

### 4. Write Code + Proofs

For any new operation or algorithm:

1. **Implement the function** in the appropriate module (`/src/nucore/`, `/src/nuleger/`, etc.)
2. **Write formal proofs** in `/verification/` (Coq or Lean)
3. **Add integration tests** in `/tests/` with reproducible test cases
4. **Document thoroughly** in `/docs/` with specification markdown

#### Example: Adding a New Operation

```python
# /src/nucore/operations.py

def new_operation(n1: float, u1: float, n2: float, u2: float) -> tuple[float, float]:
    """
    New operation description.

    Invariants:
    - Non-negativity: u_out >= 0
    - Enclosure preservation: [n-u, n+u] bounds maintained
    - Constant-time: O(1) execution

    Formal proof: /verification/NUProof/new_operation.v
    """
    # Implementation ensuring O(1) complexity
    n_out = ...
    u_out = ...

    assert u_out >= 0, "Non-negativity violated"
    return (n_out, u_out)
```

```coq
(* /verification/NUProof/new_operation.v *)

Theorem new_operation_nonnegative :
  forall n1 u1 n2 u2,
  u1 >= 0 -> u2 >= 0 ->
  let (n_out, u_out) := new_operation n1 u1 n2 u2 in
  u_out >= 0.
Proof.
  (* Formal proof here *)
Qed.
```

### 5. Run Verification Tests

Before submitting:

```bash
# Run all tests
make test

# Run formal verification
make verify

# Generate attestation proof
make attest

# Check code coverage
make coverage
```

All tests must pass. All proofs must validate.

### 6. Commit with Descriptive Messages

```bash
git add .
git commit -m "feat(nucore): Add division operation with formal proof

- Implements division with uncertainty propagation
- Adds Coq proof of non-negativity and enclosure
- Includes 500 test cases validating invariants
- Updates NUCore_SPEC.md with operation definition

Refs: #42"
```

Use conventional commit format:
- `feat(component): description` — New feature
- `fix(component): description` — Bug fix
- `docs(component): description` — Documentation
- `test(component): description` — Test additions
- `proof(component): description` — Formal verification

### 7. Submit Pull Request

Push your branch and open a pull request:

```bash
git push origin feature/your-feature-name
```

In your PR description, include:

- **Summary**: What this PR does (1-2 sentences)
- **Motivation**: Why this change is needed
- **Proof of Correctness**: Link to formal proofs or test results
- **Immutability Check**: Confirmation that no mutable state was introduced
- **Attestation Impact**: How this affects audit trails (if applicable)
- **Related Issues**: `Closes #42` or `Refs #42`

### 8. Code Review Process

Maintainers will review for:

1. **Correctness** — Does it work as intended?
2. **Immutability** — Does it preserve append-only guarantees?
3. **Determinism** — Are outputs consistent for identical inputs?
4. **Proofs** — Are formal verifications complete and valid?
5. **Documentation** — Is the "why" and "how" clearly explained?

Be prepared to:
- Answer clarifying questions
- Revise based on feedback
- Add additional tests or proofs
- Update documentation

## Issue Templates

When opening issues, use these templates:

### Verification Task Template

```markdown
**Title**: [Verification] Prove property X for operation Y

**Description**:
- Operation: NUCore.multiply
- Property: Associativity
- Theorem: (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c)

**Acceptance Criteria**:
- [ ] Formal proof in Coq or Lean
- [ ] Proof validated by CI pipeline
- [ ] Proof hash embedded in /verification/proof_registry.json
```

### Immutable Core Update Template

```markdown
**Title**: [Core] Update to [component]

**Description**:
- Component: NULedger
- Change: Add support for batch append with Merkle tree optimization

**Immutability Check**:
- [ ] No mutable state introduced
- [ ] All updates are append-only
- [ ] Attestation signatures preserved
- [ ] Audit trail complete and unbroken

**Formal Proofs Required**:
- [ ] Proof of append-only property
- [ ] Proof of signature chain integrity
```

## Security and Attestation

If you discover a vulnerability or attestation weakness:

1. **Do NOT open a public issue**
2. **Email**: security@ebios.org (if available) or maintainers privately
3. **Provide**: Description, reproduction steps, and potential impact
4. **Wait**: For maintainer response before public disclosure

We take cryptographic integrity seriously.

## Code of Conduct

### Respectful Collaboration

- **Be precise**: Technical accuracy over emotional validation
- **Be honest**: Disagree when necessary; false agreement helps no one
- **Be clear**: Explain reasoning, especially for complex proofs
- **Be patient**: Formal verification takes time; rigor over speed

### Focus on Truth

eBIOS prioritizes **mathematical correctness** and **epistemic honesty**. Discussions should focus on:

- Provable properties
- Falsifiable claims
- Reproducible tests
- Formal verification

Avoid:
- Subjective preferences without technical justification
- Ad hominem arguments
- Unverifiable assertions
- Emotional appeals over logical reasoning

## Recognition

Contributors who provide:
- **Formal proofs** of core theorems
- **Significant attestation improvements**
- **Critical bug fixes** restoring immutability

...will be acknowledged in:
- `/docs/CONTRIBUTORS.md`
- Release notes for relevant versions
- Academic publications citing eBIOS (where applicable)

## Getting Help

- **Documentation**: Start with `/docs/` for architecture and specifications
- **Issues**: Search existing issues before opening new ones
- **Discussions**: Use GitHub Discussions for questions and design conversations
- **Email**: Contact maintainers for private security reports

## Final Note

> "Verification is local; trust is global. eBIOS is the common denominator for honesty."

Your contributions help build the epistemic substrate for honest machines. Every proof matters. Every test matters. Every line of documentation matters.

Thank you for maintaining the integrity of this project.

---

**eBIOS Contributors** — Building the floor for accountable AI.
