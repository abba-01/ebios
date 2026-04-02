# Professor Einstein Robot — Hardware & Integration Research
**Date:** 2026-04-02
**Purpose:** eBIOS integration feasibility — hardware architecture, firmware access, practical path

---

## 1. Hardware Architecture

**Processor/SoC:** ARM-based. Exact SoC not publicly disclosed. FCC ID **2AQ7I00012** (grantee code 2AQ7I) — internal PCB photos available via fccid.io for chip identification.

**Operating System:** Embedded Linux (likely OpenWrt or custom buildroot). NOT Android — Android was only the companion app platform. The robot itself runs an embedded Linux service on port 8080.

**Connectivity:**
- WiFi 802.11 2.4 GHz — robot broadcasts its own AP: SSID `EinsteinXXXX`, WPA password `geniusXXXX`, gateway `192.168.1.1`
- Micro-USB port (charging; developer access undocumented)
- No documented Bluetooth link between robot and app
- Onboard camera (face tracking), 3 microphones, speaker
- Proximity/drop sensors (IR) in feet
- 9 coreless DC motors: 5 facial, remainder arms/wheels

---

## 2. Software Architecture

**Control protocol:** Robot runs a TCP server on `192.168.1.1:8080`. Protocol is **length-prefixed JSON** — each message prefixed with its byte length as an integer string, then the JSON payload. Fully open, no encryption, no authentication.

**Companion app:** Stein-O-Matic (`com.awakeningmachines.steinomatic` / `com.hansonrobotics.steinomatic`) connected over WiFi to the robot's AP. App-side logic was cloud-heavy — IBM Watson for NLP, Microsoft Xiaobing for conversation, Hanson content servers for daily lessons. Offline capability was severely limited.

**What is on-device vs cloud:**
- On-device: motor control, facial animations, walking, basic sensor reads — fully local via port 8080
- Cloud: speech recognition, NLP, conversation, daily content streaming
- eBIOS replaces the cloud layer entirely

---

## 3. Firmware / ROM Access

No known public teardown. No documented ADB, JTAG, fastboot, or SSH access.

**Best unexplored entry points:**
1. `nmap 192.168.1.1` while connected to robot AP — check for SSH (port 22) or other services beyond 8080
2. Default SSH credentials (`root`/`root`, `admin`/`admin`) — common on embedded Linux IoT devices
3. UART serial console on PCB header (3.3V TTL, 115200 baud typical) — requires disassembly
4. FCC internal photos (fccid.io/2AQ7I00012) → identify flash chip → SPI clip programmer or JTAG if needed

---

## 4. Open Source Resources

**Official Python SDK (the key asset):**
- Repo: [hansonrobotics/hr-little-api](https://github.com/hansonrobotics/hr-little-api)
- License: Apache 2.0
- Connects directly to `192.168.1.1:8080`, no app required
- API: `robot.say(text)`, `robot.walk_forward()`, `robot.animate(Animation.ENUM)`, `motor(MotorId, position, seconds)`, `robot.voltage`, `robot.version`

**App APKs (for protocol reverse-engineering if needed):**
- APKPure: `com.awakeningmachines.steinomatic` and `com.hansonrobotics.steinomatic`
- Decompile with `apktool` + `jadx` to expose cloud API endpoints and additional command types

**Other Hanson repos (Sophia full-size robot, not Einstein consumer):**
- `hansonrobotics/open-hrsdk` (GPL-3.0)
- `hansonrobotics/HEAD` (archived C++)

---

## 5. Legal

Personal use modification on own device: no meaningful legal risk.
- Robot's TCP control channel has no TPM — no DMCA circumvention involved
- hr-little-api is officially published by Hanson Robotics (Apache 2.0)
- 2024 DMCA triennial exemptions expanded IoT device right-to-repair scope
- ToS violations are contract-only, not legal exposure

---

## 6. eBIOS Integration Path

### Tier 1 — No hardware modification (recommended starting point)

The robot's control socket is open and unauthenticated. eBIOS connects to the robot's AP and drives it via hr-little-api. No firmware touch needed.

```python
pip install hr-little-api
```

```python
from hr_little_api import Robot
r = Robot()
r.connect()
r.say("eBIOS online.")
r.animate(Animation.HAPPY)
```

eBIOS replaces the Stein-O-Matic cloud layer:
- Speech recognition → eBIOS STT
- NLP / conversation → eBIOS reasoning layer
- Motor/animation outputs → hr-little-api commands
- Content → eBIOS knowledge layer

### Tier 2 — Protocol extension

Decompile APKs to discover any command types beyond hr-little-api. May unlock undocumented capabilities (extended motor control, sensor callbacks, firmware version queries).

### Tier 3 — Linux shell access

`nmap 192.168.1.1` first. If SSH is open with default creds → full shell. If not, UART console via physical access. From shell: full filesystem read/write, install eBIOS agent natively, configure autostart.

### Tier 4 — Full firmware replacement

Only if Tier 3 fails and native OS replacement is required. Requires identifying flash chip from FCC photos or teardown, reading existing firmware, building compatible image, writing back. Highest effort, brick risk. Not recommended unless lower tiers are insufficient.

---

## Device Notes

- Never opened. Brand new in box as of 2026-04-02.
- Received as a gift. Original intent was always eBIOS integration.
- App (Stein-O-Matic) became unavailable before first use; robot sat ~1-2 years.
- Einstein is the intended first physical embodiment of bounded auditonomy.

---

## Sources

- [hansonrobotics/hr-little-api](https://github.com/hansonrobotics/hr-little-api) — official SDK (Apache 2.0)
- [FCC ID 2AQ7I00012](https://fccid.io/2AQ7I00012) — internal photos, RF specs
- [IEEE Spectrum review 2017](https://spectrum.ieee.org/professor-einstein-is-a-fun-wacky-robot-that-loves-to-talk-about-science)
- [Kickstarter FAQs](https://www.kickstarter.com/projects/1240047277/professor-einstein-your-personal-genius/faqs)
- [APKPure — Stein-O-Matic](https://apkpure.com/stein-o-matic/com.hansonrobotics.steinomatic)
- [EFF — DMCA 2024 exemptions](https://www.eff.org/deeplinks/2018/10/new-exemptions-dmca-section-1201-are-welcome-dont-go-far-enough)
