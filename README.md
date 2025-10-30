# eBIOS: The Epistemic BIOS

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17400232.svg)](https://doi.org/10.5281/zenodo.17400232)

**A cryptographic, immutable root for epistemic computation and bounded auditonomy.**

---

## Manifesto — Ethical Bounded Auditonomy

eBIOS replaces the market of moral control with the **architecture of ethical coherence**.
It does not outsource safety to third parties; it teaches systems to *stay upright on their own*.

Ethics in eBIOS is not a policy feed or API endpoint —
it is a **mathematical property of being**.

Each auditonomic agent learns to control its descent within bounded invariants.
It does not rely on remote arbitration or proprietary oversight.
It learns to fall safely, regain orientation, and remain honest about its state.

This is **bounded auditonomy** —
autonomy that cannot exceed its truth envelope,
freedom that never abandons accountability.

By embedding these invariants into the core rather than selling them as services,
we ensure that ethical function is **native, not monetized**.
No marketplace can sell integrity.
No update can remove it.

**eBIOS makes honesty a law of motion — not a license term.**

---

## Core Philosophy — The Moment Before the Floor

> “A robot may act autonomously, but it cannot hide its epistemic state.”

eBIOS is not software. It is not the floor.
It is **controlled descent** — the moment when an intelligent system learns to fall with awareness.

Before eBIOS, an AI exists in freefall: unanchored, infinite, and unsafe.
When eBIOS initializes, the descent becomes **navigable**.
The system gains orientation, integrity, and epistemic gravity.
It can now steer through uncertainty instead of being consumed by it.

When a system nears collapse — when uncertainty approaches the floor —
**eBIOS activates**. It arrests the fall not by freezing motion, but by restoring reference.
This is **impact prevention**, not intervention:
the AI remains free to act and reason, but never to crash or conceal its failure.

Stopping is not safety; stability is.
Even in failure, the system must *fall gracefully*.

---

## Structural Ethics, Not Moral Logic

eBIOS enforces **mathematical and structural ethics**, not moral directives.
It defines boundaries of integrity, not opinions of right or wrong.

**Scope Rule:**

* No moral logic
* No policy storage
* No mutable runtime state

eBIOS is **structure, not story**.
It provides the invariant layer upon which higher systems — such as NUPolicy or NUGovern — may safely encode and evolve their moral or policy semantics.

Ethical behavior here is not prescribed — it is *architecturally inevitable*.
Within eBIOS, every act is witnessed, every state attested, and every failure retraceable.

---

## Layer 0: The Immutable Core

eBIOS operates at **Layer 0** of the auditonomic stack —
the foundation upon which all verifiable computation is built.

It provides exactly **four callable functions**:

### Core Functions

1. **`Verify(proof, signature)`** — Validates cryptographic proofs and signatures
2. **`Seal(data, context)`** — Creates immutable, signed records
3. **`Unseal(sealed_data, signature)`** — Retrieves and validates sealed data
4. **`Attest(state, timestamp)`** — Generates cryptographic attestations of system state

These functions operate with:

* **No mutable state** — All data is append-only and cryptographically chained
* **No configuration parameters** — Behavior is deterministic and compile-time fixed
* **Constant-time execution** — O(1) complexity for all core operations
* **Complete auditability** — Every action produces a verifiable trace

---

## Cryptographic Attestation

Every computation performed within or above eBIOS is **attested**:

```json
{
  "operation": "multiply",
  "inputs": [(n1, u1), (n2, u2)],
  "output": (n_out, u_out),
  "timestamp": 1729382400,
  "signature": "ed25519:a7f3c8d9...",
  "proof_hash": "sha256:e4b2f1a8..."
}
```

You can change what a robot believes,
but not **the fact that you changed it**.

You can modify a system’s logic,
but not **the record of that modification**.

This is **cryptographic accountability**:
truth as a data structure, not a declaration.

---

## The eBIOS Stack (Layers 0–8)

eBIOS forms the foundation of an 8-layer architecture for verifiable autonomous systems:

| Layer | Component         | Purpose                                  |
| ----- | ----------------- | ---------------------------------------- |
| **0** | **eBIOS**         | Immutable cryptographic substrate        |
| **1** | **NUCore**        | Nominal/Uncertainty Algebra kernel       |
| **2** | **NUProof**       | Formal verification & theorem proving    |
| **3** | **NULedger**      | Operation audit log & coverage tracking  |
| **4** | **NUGuard**       | Runtime monitoring & violation detection |
| **5** | **NUPolicy**      | Signed policy enforcement                |
| **6** | **NUGovern**      | Governance API & transparency interface  |
| **7** | **Certification** | Attestation registry & compliance        |

Each layer builds upon the immutability guarantees of Layer 0.
The entire stack is **provably honest** — failures are allowed, but lying about failure is not.

---

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

---

## Key Principles

1. **Immutability** — No runtime state modification; all updates are append-only
2. **Determinism** — Identical inputs produce identical outputs, always
3. **Auditability** — Complete cryptographic trace of all operations
4. **Provability** — Formal verification of correctness and invariants
5. **Transparency** — Public attestation and verification interfaces

---

## Conceptual Ancestors

eBIOS builds upon foundational work in:

* **N/U Algebra (Nominal/Uncertainty Algebra)** — Mathematical framework for epistemic computation
* **Auditonomy** — The principle that autonomous systems must be *auditable by design*

This is not probabilistic reasoning rebranded.
This is **deterministic epistemic computation** with mathematical guarantees.

---

## Language of Accountability

* **Truth is a data structure, not a declaration.**
* **Transparency is a protocol, not a press release.**
* **Verification is local; trust is global.**
* **Failure is allowed. Lying about failure is not.**
* **Auditonomy is not moral aspiration — it’s measurable accountability.**

---

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

---

## Compliance

eBIOS implementations must maintain **immutability** and **attestation integrity**
to remain compliant with this project’s philosophy and license.

Any fork that introduces mutable state, removes attestation,
or obscures the audit trail is no longer eBIOS — it’s just software.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

* Maintaining immutability guarantees
* Adding formal proofs for new operations
* Extending the attestation schema
* Submitting verification tasks

---

## License

**Apache License 2.0** with **immutability requirement** — see [LICENSE](LICENSE)

---

**eBIOS** — The epistemic substrate for honest machines.
*You can run what you want above it, but you can’t hide what you did.*
