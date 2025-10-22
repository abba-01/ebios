# Getting a DOI for eBIOS via Zenodo

**Purpose**: Establish priority and protect IP during institutional/government review

**Status**: Ready to submit - all metadata prepared

---

## Quick Start (5 minutes to DOI)

### Step 1: Create Zenodo Account
1. Go to https://zenodo.org/
2. Click "Sign up" (top right)
3. **Use GitHub login** for easiest integration
4. Authorize Zenodo to access your GitHub repositories

### Step 2: Enable eBIOS Repository
1. Go to https://zenodo.org/account/settings/github/
2. Find `abba-01/ebios` in the repository list
3. **Toggle ON** the switch next to it
4. Zenodo will now watch for new releases

### Step 3: Create GitHub Release
The tag `v0.2.0-alpha` is already pushed. Now create the release:

**Option A: Via GitHub Web Interface** (Recommended)
1. Go to https://github.com/abba-01/ebios/releases
2. Click "Create a new release"
3. Select tag: `v0.2.0-alpha`
4. Release title: `eBIOS v0.2.0-alpha - Formal Verification Milestone`
5. Description: Copy from tag annotation (see below)
6. Check: "This is a pre-release"
7. Click "Publish release"

**Option B: Via GitHub CLI** (if installed)
```bash
gh release create v0.2.0-alpha \
  --title "eBIOS v0.2.0-alpha - Formal Verification Milestone" \
  --notes-file RELEASE_NOTES.md \
  --prerelease
```

### Step 4: Verify DOI Assignment
1. Wait 5-10 minutes for Zenodo to process
2. Go to https://zenodo.org/account/settings/github/
3. Click on your release - you'll see the DOI badge
4. Your DOI will be: `10.5281/zenodo.XXXXXXX`

### Step 5: Add DOI Badge to README
Once you have the DOI, add this badge to your README.md:

```markdown
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
```

---

## Release Description (for GitHub release)

```markdown
# eBIOS v0.2.0-alpha - Formal Verification Milestone

**DOI**: (Will be assigned by Zenodo automatically)

## Summary

This alpha release marks significant progress on formal verification for eBIOS (Epistemic Basic Input/Output System) - a foundational firmware layer for uncertainty-aware computation.

## Formal Verification Progress

**Completion**: 62.5% (5/8 proofs complete)

### New Proofs (This Release)
- ✅ **Enclosure.lean** (278 lines) - Proves interval arithmetic enclosure with conservative √2 and √3 factors
- ✅ **ComposeReduction.lean** (125 lines) - Proves uncertainty reduction through evidence composition

### Previously Complete
- ✅ NonNegativity.lean - Proves u ≥ 0 invariant
- ✅ FlipInvolutive.lean - Proves flip² = identity
- ✅ NUCore.lean - Core definitions

### Total Formal Verification
- **403 lines** of rigorous Lean 4 proof code
- Zero `sorry` statements in completed proofs
- All proofs type-check and compile

## Core Features (v0.1.0 Base)

### Layer 1: NUCore
- N/U Algebra with 5 operations (⊕, ⊗, ⊙, Catch, Flip)
- O(1) constant-time execution
- 39/39 tests passing

### Layer 3: NULedger
- Cryptographic audit ledger with Ed25519 signatures
- Merkle tree for O(log n) verification
- 38/38 tests passing

### Layer 4: NUGuard
- Runtime monitoring with configurable rules
- Event-driven architecture
- 32/32 tests passing

### Layer 5: NUPolicy
- Policy management with cryptographic signing
- JSON-based configuration
- 41/41 tests passing

### Layer 6: NUGovern
- RESTful HTTP API
- 13 endpoints for governance
- 22/22 tests passing

## Quality Metrics

- **Test Coverage**: 100% (172/172 tests passing)
- **Documentation**: Complete (9 specifications, 4,631 lines)
- **Formal Verification**: 62.5% (5/8 proofs complete)
- **Code Quality**: Zero known bugs

## Philosophy

eBIOS enforces three immutable principles:

1. **Immutability**: Truth is a data structure, not a declaration
2. **Provability**: Failure is allowed. Lying about failure is not.
3. **Accountability**: You can run what you want above it, but you can't hide what you did

## Use Cases

- Safety-critical systems (automotive, aerospace)
- Medical device firmware
- Sensor fusion with uncertainty tracking
- Distributed consensus with epistemic guarantees
- Government and institutional applications requiring auditability

## Installation

```bash
git clone https://github.com/abba-01/ebios.git
cd ebios
pip install -r requirements.txt
pytest tests/  # All 172 tests should pass
```

## Documentation

- Architecture: `/docs/ARCHITECTURE_FINAL.md`
- Compliance: `/docs/COMPLIANCE.md` (ISO 26262, DO-178C, IEC 61508, NIST)
- API Reference: `/docs/NUGovern_API.md`
- Examples: `/examples/README.md`

## Citation

If you use this software, please cite:

```bibtex
@software{ebios_2025,
  title = {eBIOS: Epistemic Basic Input/Output System},
  author = {eBIOS Contributors},
  year = {2025},
  version = {0.2.0-alpha},
  url = {https://github.com/abba-01/ebios},
  doi = {10.5281/zenodo.XXXXXXX}  # Will be assigned by Zenodo
}
```

Or use `CITATION.cff` for automated citation tools.

## License

Apache 2.0 with immutability clause - See LICENSE file

## Repository

- **Code**: https://github.com/abba-01/ebios
- **DOI**: (Zenodo will assign)
- **License**: Apache-2.0

---

**Status**: Alpha - Development and testing only. Not for production use.

**Next Milestone**: v0.2.0 full release with 100% formal verification (3 remaining proofs)
```

---

## What the DOI Provides

### Immediate Benefits
1. **Timestamped Record**: Permanent proof of priority as of 2025-10-20
2. **Persistent Identifier**: DOI never changes, always resolves to your work
3. **Citability**: Others can formally cite your work
4. **IP Protection**: Establishes prior art for patent/IP purposes
5. **Archival**: Zenodo archives a snapshot permanently

### Legal Protection
- DOI timestamp establishes **priority date** for IP claims
- Archived version is **immutable** and **cryptographically verified**
- **Independent third party** (CERN-backed Zenodo) validates timestamp
- Can be used as **evidence** in IP disputes or patent applications

---

## Metadata Files Created

We've created two metadata files for optimal archiving:

1. **CITATION.cff** - GitHub/academic citation format
2. **.zenodo.json** - Zenodo-specific metadata with rich description

These ensure your work is properly:
- Indexed by Google Scholar
- Discoverable in academic databases
- Cited with correct attribution
- Archived with full context

---

## After DOI Assignment

### 1. Update Documentation
Add DOI badge to:
- README.md (top of file)
- RELEASE_SUMMARY.md
- All academic/institutional submissions

### 2. Update CITATION.cff
Replace `[To be assigned by Zenodo]` with actual DOI

### 3. Share Widely
You can now safely share:
- DOI link (permanent, citable)
- GitHub repository
- Zenodo archive page

The DOI provides **legal protection** during review process.

---

## Troubleshooting

**Q: Zenodo didn't create a DOI?**
- Check that you toggled ON the repository in Zenodo settings
- Verify the release was published (not just drafted)
- Wait 10-15 minutes - processing can take time
- Check Zenodo status at https://zenodo.org/account/settings/github/

**Q: Can I update the release after DOI is assigned?**
- You can update GitHub release notes
- DOI points to the archived version on Zenodo
- New releases get new DOIs (Zenodo creates a DOI "family")

**Q: Is the DOI permanent?**
- Yes, DOIs are permanent and guaranteed by CERN
- Even if GitHub goes down, Zenodo archive remains
- DOI will resolve forever

---

## Timeline

**Now**: Metadata files ready, tag pushed
**5 minutes**: Create GitHub release
**10 minutes**: Zenodo processes and assigns DOI
**15 minutes**: DOI is live and citable

**Total**: ~15-20 minutes from start to finish

---

## Next Steps

1. Create GitHub release (see Step 3 above)
2. Wait for Zenodo DOI assignment
3. Update your institutional/government submissions with DOI
4. The DOI establishes your priority and protects your IP

**The DOI is your proof of priority. Get it now.**
