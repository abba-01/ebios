# NUGuard Policy

**Layer 4 of eBIOS: Runtime Monitoring and Violation Detection**

## Philosophy

> "Failure is allowed. Lying about failure is not."

NUGuard does not prevent failures — it prevents **hiding** failures. Every violation is detected, logged, and escalated. Operators cannot claim ignorance when the monitor recorded the truth.

## Core Principle

Autonomous systems must be accountable. NUGuard enforces accountability by:

1. **Continuous Monitoring**: Every operation is checked against rules
2. **Transparent Violations**: All events are logged to NULedger
3. **Configurable Escalation**: Operators choose how to respond
4. **No Suppression**: Events cannot be silently discarded

## Policy Model

### Detection → Logging → Escalation

```
Operation → Monitor.check() → Event? → Handlers → Ledger
```

Every NUCore operation flows through the monitor. If rules are violated, events are generated and processed through configured handlers. All events (including failures) are logged to NULedger for audit.

### Event Levels

| Level | Meaning | Example | Default Action |
|-------|---------|---------|----------------|
| **INFO** | Normal observation | Large value detected | Log only |
| **WARNING** | Potential issue | Coverage > threshold | Log + notify |
| **ERROR** | Violation detected | Excessive uncertainty | Log + escalate |
| **CRITICAL** | Severe violation | Invariant failed | Log + halt |

## Default Rules

NUGuard ships with two default rules:

1. **InvariantRule**: Detects mathematical violations
   - Negative uncertainty (u < 0)
   - NaN values
   - Infinite nominal values
   - **Level**: CRITICAL

2. **CoverageRule**: Detects epistemic deterioration
   - Coverage ratio (u/|n|) > threshold
   - **Default threshold**: 0.1 (10%)
   - **Level**: WARNING

## Example Policies

### Conservative Policy (Low Risk Tolerance)

```python
config = MonitorConfig(
    rules=[
        InvariantRule(),
        CoverageRule(threshold=0.05, level=EventLevel.ERROR),
        ThresholdRule(max_uncertainty=1.0, level=EventLevel.WARNING)
    ],
    halt_on_critical=True
)
```

### Permissive Policy (High Risk Tolerance)

```python
config = MonitorConfig(
    rules=[
        InvariantRule(),  # Only critical violations
        CoverageRule(threshold=0.5, level=EventLevel.WARNING)
    ],
    halt_on_critical=False
)
```

### Audit-Only Policy

```python
config = MonitorConfig(
    rules=[InvariantRule()],
    auto_log=True,
    halt_on_critical=False
)
```

## Accountability Guarantee

NUGuard provides three guarantees:

1. **Detection**: All violations matching configured rules are detected
2. **Logging**: All events are logged to NULedger (if configured)
3. **Immutability**: Logged events cannot be altered or deleted

This means:
- Operators **can** configure lenient rules
- Operators **can** choose not to halt on violations
- Operators **cannot** hide that violations occurred

## Integration with eBIOS Stack

| Layer | Integration |
|-------|-------------|
| **Layer 1 (NUCore)** | All operations monitored |
| **Layer 3 (NULedger)** | Events logged for audit |
| **Layer 5 (NUPolicy)** | Rules configured via policy files |
| **Layer 6 (NUGovern)** | Violation statistics exposed via API |

## Operator Responsibilities

Operators using NUGuard must:

1. **Define Rules**: Choose appropriate thresholds for their domain
2. **Configure Handlers**: Decide how events are processed
3. **Review Logs**: Periodically audit NULedger for violations
4. **Update Policies**: Adjust rules based on operational experience

Operators **cannot**:
- Suppress events matching configured rules
- Alter logged events retroactively
- Hide violations from audit trail

## Examples

### Basic Monitoring

```python
from nuguard import Monitor
from nucore import add

monitor = Monitor()  # Uses default rules

n1, u1 = 10.0, 0.5
n2, u2 = 20.0, 1.0
n_out, u_out = add(n1, u1, n2, u2)

passed = monitor.monitor("add", [(n1, u1), (n2, u2)], (n_out, u_out))
print(f"Passed: {passed}")
```

### With Ledger Integration

```python
from nuguard import Monitor, MonitorConfig, CoverageRule
from nuledger import Ledger

ledger = Ledger()
config = MonitorConfig(
    rules=[CoverageRule(threshold=0.05)],
    auto_log=True
)
monitor = Monitor(config, ledger=ledger)

# Operations are monitored and logged
event = monitor.check("multiply", [(10.0, 5.0)], (100.0, 50.0))
if event:
    print(f"Violation: {event}")
    # Event is already logged to ledger

# Audit trail preserved
chain = ledger.trace(event.op_id)
```

### Custom Event Handling

```python
from nuguard import Monitor, MonitorConfig, EventHandler

class AlertHandler(EventHandler):
    def handle(self, event):
        if event.level == EventLevel.CRITICAL:
            send_alert(f"CRITICAL: {event.message}")

config = MonitorConfig(handlers=[AlertHandler()])
monitor = Monitor(config)
```

## Philosophy

### Truth vs Comfort

NUGuard prioritizes **truth** over **comfort**. Violations are uncomfortable, but hiding them is unacceptable.

### Accountability Without Punishment

Logging failures is not punishment — it's honesty. Failed invariants are logged with `invariant_passed=False` and infinite uncertainty. This allows:
- Root cause analysis
- Pattern detection
- Process improvement

### Local Enforcement, Global Trust

Operators control their local policies, but all policies generate auditable traces. Trust emerges from verifiable history, not from promises.

## References

- **NUCore Operations**: `/docs/NUCore_SPEC.md`
- **NULedger Audit Log**: `/docs/NULedger_SPEC.md`
- **eBIOS Architecture**: `/docs/README.md`

## Version

- **NUGuard Version**: 0.1.0
- **eBIOS Layer**: 4
- **Status**: Active development (PHASE 4)

---

**NUGuard** — Monitoring that cannot be silenced.

*"Failure is allowed. Lying about failure is not."*
