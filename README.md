# eBIOS: The Epistemic BIOS

**A cryptographic, immutable root for epistemic computation and auditonomic reasoning systems.**

## Manifesto

eBIOS is not software. It is the **floor** that free-fall occurrs — a mathematically minimal, tamper-proof layer ensuring that all higher-level systems (NUCore, NUProof, NULedger, NUGuard, etc.) remain truthful, deterministic, and auditable. It is the epistemic BIOS: a sealed, immutable core for auditonomic systems where **a robot may act autonomously, but it cannot hide its epistemic state.**

You can run what you want above it, but **you can't hide what you did.**

## Core Philosophy

> "A robot may act autonomously, but it cannot hide its epistemic state."

eBIOS enforces mathematical and ethical integrity in real-time decision systems through cryptographic attestation and immutable proof chains. It is not a framework for building AI — it is the substrate that makes AI **accountable**.

**Scope Rule**: No moral logic, no policy storage, no runtime state mutation. eBIOS is structure, not story.

## Layer 0: The Immutable Core

eBIOS operates at **Layer 0** of the auditonomic stack — the foundation upon which all verifiable computation is built. It provides exactly **four callable functions**:

### Core Functions

1. **`Verify(proof, signature)`** — Validates cryptographic proofs and signatures
2. **`Seal(data, context)`** — Creates immutable, signed records
3. **`Unseal(sealed_data, signature)`** — Retrieves and validates sealed data
4. **`Attest(state, timestamp)`** — Generates cryptographic attestations of system state

These functions operate with:
- **No mutable state** — All state is append-only and cryptographically chained
- **No configuration parameters** — Behavior is deterministic and compile-time fixed
- **Constant-time execution** — O(1) complexity for all core operations
- **Complete auditability** — Every operation produces a verifiable trace

## Cryptographic Attestation

Every computation performed within or above eBIOS is **attested**:

```
{
  "operation": "multiply",
  "inputs": [(n1, u1), (n2, u2)],
  "output": (n_out, u_out),
  "timestamp": 1729382400,
  "signature": "ed25519:a7f3c8d9...",
  "proof_hash": "sha256:e4b2f1a8..."
}
```

You can change what a robot believes, but not **the fact that you changed it**. You can modify a system's logic, but not **the record of that modification**. This is cryptographic accountability: truth as a data structure, not a declaration.

## The eBIOS Stack (Layers 0–8)

eBIOS is the foundation of an 8-layer architecture for verifiable autonomous systems:

| Layer | Component | Purpose |
|-------|-----------|---------|
| **0** | **eBIOS** | Immutable cryptographic substrate |
| **1** | **NUCore** | Nominal/Uncertainty Algebra kernel |
| **2** | **NUProof** | Formal verification & theorem proving |
| **3** | **NULedger** | Coverage & operation audit log |
| **4** | **NUGuard** | Runtime monitoring & violation detection |
| **5** | **NUPolicy** | Signed policy enforcement |
| **6** | **NUGovern** | Governance API & transparency interface |
| **7** | **Certification** | Attestation registry & compliance |

Each layer builds on the immutability guarantee of Layer 0. The entire stack is **provably honest** — failures are allowed, but lying about failure is not.

## Project Structure

```
/ebios
  /docs          — Specifications, philosophy, compliance documentation
  /src           — Core implementation (NUCore, NULedger, NUGuard, etc.)
  /tests         — Validation suites and formal verification tests
  /hardware      — Hardware attestation and TPM integration
  /verification  — Formal proofs (Coq/Lean), theorem validation
  /governance    — Policy schemas, attestation registry, audit interfaces
```

## Key Principles

1. **Immutability** — No runtime state modification; all updates are append-only
2. **Determinism** — Identical inputs produce identical outputs, always
3. **Auditability** — Complete cryptographic trace of all operations
4. **Provability** — Formal verification of correctness and invariants
5. **Transparency** — Public attestation and verification interfaces

## Conceptual Ancestors

eBIOS builds on foundational work in:

- **N/U Algebra** (Nominal/Uncertainty Algebra) — Mathematical framework for epistemic computation
- **Auditonomy** — The philosophy that autonomous systems must be auditable by design

This is not probabilistic reasoning rebranded. This is **deterministic epistemic computation** with mathematical guarantees.

## Language of Accountability

- **Truth is a data structure, not a declaration.**
- **Transparency is a protocol, not a press release.**
- **Verification is local; trust is global.**
- **Failure is allowed. Lying about failure is not.**
- **Auditonomy is not moral aspiration; it's measurable accountability.**

## Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/ebios.git
cd ebios

# Run verification tests
make verify

# Generate attestation report
make attest

# View audit trail
./nuleger trace <task_id>
```

## Compliance

eBIOS implementations must maintain **immutability** and **attestation integrity** to remain compliant with the project license and philosophy. Any fork that introduces mutable state, removes attestation, or obscures the audit trail is no longer eBIOS — it's just software.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Maintaining immutability guarantees
- Adding formal proofs for new operations
- Extending the attestation schema
- Submitting verification tasks

## License

Apache License 2.0 with immutability requirement — see [LICENSE](LICENSE)

---

**eBIOS** — The epistemic substrate for honest machines.

*"You can run what you want above it, but you can't hide what you did."*
