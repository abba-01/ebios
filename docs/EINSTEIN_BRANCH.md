# eBIOS on Professor Einstein — Branch Documentation

**Branch:** `einstein-integration`
**Base:** `master`
**Classification:** Applied eBIOS — Commercial ROM Platform Integration

---

## What This Branch Is

`einstein-integration` is the first documented application of the eBIOS framework on a **commercial, public-facing ROM system** — a device with fixed manufacturer firmware that cannot be replaced without physical intervention.

The target platform is the **Professor Einstein** personal robot by Hanson Robotics (barcode 8 4279710001 9). The robot's embedded firmware is a closed ROM — eBIOS does not replace it. Instead, eBIOS operates as the **intelligence layer above the ROM**, driving the robot through its native open control protocol.

This is eBIOS in its intended role: not replacing the substrate, but providing bounded epistemic function where none existed.

---

## The ROM Integration Model

A **ROM platform** is any commercial system where:
- The base firmware is fixed or closed (read-only from eBIOS's perspective)
- A documented control interface exists (TCP socket, serial bus, USB HID, BLE GATT, etc.)
- The manufacturer's cloud backend is absent, dead, or undesirable
- eBIOS fills the intelligence and autonomy layer that the original system no longer provides

Professor Einstein is the **prototype case** for this model. Its ROM (embedded Linux on ARM, serving JSON over TCP port 8080) is untouched. eBIOS connects to the robot's WiFi AP and becomes its brain.

**The principle generalises.** Any commercial robot, kiosk, or interactive device with an open or reversible control interface is a candidate for eBIOS ROM integration.

---

## Architecture on This Branch

```
┌─────────────────────────────────┐
│           eBIOS Layer           │  ← this branch
│  - Reasoning / NLP              │
│  - Epistemic state management   │
│  - Bounded autonomy enforcement │
│  - hr-little-api control bridge │
└────────────────┬────────────────┘
                 │ TCP JSON — 192.168.1.1:8080
┌────────────────▼────────────────┐
│     Professor Einstein ROM      │  ← untouched
│  - Embedded Linux (ARM)         │
│  - Motor control (9 actuators)  │
│  - Camera, mic, speaker         │
│  - WiFi AP (EinsteinXXXX)       │
└─────────────────────────────────┘
```

---

## Branch Scope

This branch contains:

| Path | Contents |
|------|----------|
| `docs/EINSTEIN_BRANCH.md` | This document |
| `docs/professor_einstein_integration.md` | Full hardware/firmware research, Tier 1–4 integration path |
| `einstein/` | Integration code: hr-little-api wrapper, eBIOS↔Einstein bridge |
| `ORIGIN.md` | Origin story — why Einstein, why eBIOS |

Code in `einstein/` wraps `hr-little-api` and exposes the robot as an eBIOS actuator interface. The eBIOS core (`src/`) is not modified on this branch.

---

## Status

| Item | State |
|------|-------|
| Hardware research | Complete |
| Physical device | Unopened (brand new in box) |
| Tier 1 integration (hr-little-api) | Planned — pending first power-on |
| eBIOS bridge module | Not started |
| ROM protocol reverse-engineering (Tier 2) | Not started |

---

## References

- `docs/professor_einstein_integration.md` — full technical research
- `ORIGIN.md` — project origin story
- [hansonrobotics/hr-little-api](https://github.com/hansonrobotics/hr-little-api) — Apache 2.0 control SDK
- [FCC ID 2AQ7I00012](https://fccid.io/2AQ7I00012) — hardware filing
