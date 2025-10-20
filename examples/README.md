# eBIOS Examples

Complete usage examples demonstrating all layers of the eBIOS stack.

## Quick Start

### 1. Basic Usage (All Layers)

```bash
python examples/basic_usage.py
```

Demonstrates:
- NUCore operations (add, multiply, compose, catch, flip)
- Ledger audit logging
- Runtime monitoring with NUGuard
- Policy-driven configuration
- Complete end-to-end workflow

### 2. HTTP API Demo

```bash
# Terminal 1: Start API server
python src/nugovern/server.py

# Terminal 2: Run demo
python examples/api_demo.py
```

Demonstrates:
- Remote operation execution
- Policy management via HTTP
- Ledger queries with pagination
- Monitor statistics
- Cryptographic attestation

## Example Files

| File | Description | Layers |
|------|-------------|--------|
| **basic_usage.py** | Core eBIOS functionality | 1, 3, 4, 5 |
| **api_demo.py** | HTTP API usage | 6 (all layers via API) |

## Running Examples

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# For API demo only
pip install requests
```

### Example 1: Direct Python Usage

```python
from src.nucore import add
from src.nuledger import Ledger
from src.nuguard import Monitor

# Create components
ledger = Ledger()
monitor = Monitor(ledger=ledger)

# Execute with monitoring
n, u = add(10.0, 0.5, 20.0, 1.0)
monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n, u))

# Verify audit trail
print(f"Logged operations: {len(ledger)}")
print(f"Integrity: {ledger.verify_integrity()}")
```

### Example 2: Policy-Driven

```python
from src.nupolicy import PolicyManager
from src.nupolicy.integration import create_monitor_from_policy
from src.nuledger import Ledger

# Load policy
manager = PolicyManager()
policy = manager.load_policy("conservative")

# Create monitor from policy
ledger = Ledger()
monitor = create_monitor_from_policy(policy, ledger=ledger)

# Operations now use policy rules
from src.nucore import add
n, u = add(10.0, 0.5, 20.0, 1.0)
event = monitor.check("add", [(10.0, 0.5), (20.0, 1.0)], (n, u))
```

### Example 3: HTTP API

```bash
# Execute operation
curl -X POST http://localhost:8000/operations/execute \
  -H "Content-Type: application/json" \
  -d '{"operation":"add","inputs":[[10.0,0.5],[20.0,1.0]]}'

# Query ledger
curl http://localhost:8000/ledger/entries?limit=10

# Verify integrity
curl http://localhost:8000/ledger/verify

# Generate attestation
curl -X POST http://localhost:8000/attestation \
  -H "Content-Type: application/json" \
  -d '{"attestation_type":"ledger"}'
```

## Example Scenarios

### Scenario 1: Sensor Fusion

```python
from src.nucore import compose
from src.nuguard import Monitor, MonitorConfig, CoverageRule

# GPS reading: 100.0 meters ± 10.0 meters
gps_n, gps_u = 100.0, 10.0

# IMU reading: 100.0 meters ± 5.0 meters
imu_n, imu_u = 100.0, 5.0

# Fuse sensors (uncertainty reduction)
fused_n, fused_u = compose(gps_n, gps_u, imu_n, imu_u)

print(f"GPS: {gps_n} ± {gps_u}")
print(f"IMU: {imu_n} ± {imu_u}")
print(f"Fused: {fused_n:.2f} ± {fused_u:.2f}")  # Reduced uncertainty
```

### Scenario 2: Safety-Critical Monitoring

```python
from src.nupolicy import PolicyManager
from src.nupolicy.integration import create_monitor_from_policy
from src.nuledger import Ledger

# Load safety-critical policy
manager = PolicyManager()
policy = manager.load_policy("conservative")

# Create monitor with strict rules
ledger = Ledger()
monitor = create_monitor_from_policy(policy, ledger=ledger)

# Execute safety-critical operation
from src.nucore import multiply
velocity = 50.0  # m/s ± 2.0
time = 10.0      # s ± 0.5

distance_n, distance_u = multiply(velocity, 2.0, time, 0.5)

# Monitor with policy
event = monitor.check(
    "multiply",
    [(velocity, 2.0), (time, 0.5)],
    (distance_n, distance_u)
)

if event:
    print(f"Policy violation: {event.message}")
else:
    print(f"Distance: {distance_n:.2f} ± {distance_u:.2f} meters")

# Verify audit trail
assert ledger.verify_integrity(), "Ledger integrity failed!"
```

### Scenario 3: Distributed System via API

```python
import requests

# Node 1: Execute operation
response = requests.post("http://node1:8000/operations/execute", json={
    "operation": "add",
    "inputs": [[10.0, 0.5], [20.0, 1.0]]
})

ledger_id = response.json()["ledger_id"]

# Node 2: Verify operation was logged
response = requests.get(f"http://node1:8000/ledger/entries")
entries = response.json()

# Node 3: Verify ledger integrity
response = requests.get("http://node1:8000/ledger/verify")
assert response.json()["valid"], "Integrity check failed!"
```

## Creating Custom Examples

### 1. Create Custom Policy

```bash
# Create policy JSON file
cat > governance/policies/my_policy.json << 'EOF'
{
  "config": {
    "version": "1.0.0",
    "name": "MyCustomPolicy",
    "description": "Custom monitoring policy",
    "rules": [
      {"type": "InvariantRule"},
      {"type": "CoverageRule", "threshold": 0.05, "level": "error"}
    ],
    "escalation": {
      "halt_on_critical": true,
      "auto_log": true
    }
  }
}
EOF

# Use in code
from src.nupolicy import PolicyManager
manager = PolicyManager()
policy = manager.load_policy("my_policy")
```

### 2. Custom Monitoring Rule

```python
from src.nuguard import CustomRule, Event, EventLevel

def my_check(operation, inputs, output, **kwargs):
    n, u = output
    if n > 1000:
        return Event(
            EventLevel.WARNING,
            operation,
            f"Large nominal value: {n}"
        )
    return None

rule = CustomRule("LargeValueRule", my_check)
```

### 3. Custom Backend

```python
from src.nuledger import Backend

class MyBackend(Backend):
    def __init__(self):
        self.entries = []

    def append(self, entry):
        self.entries.append(entry)

    def get_all(self):
        return self.entries

    # Implement other methods...

# Use custom backend
from src.nuledger import Ledger
ledger = Ledger(backend=MyBackend())
```

## Troubleshooting

### Issue: Module not found

```bash
# Ensure you're in the ebios directory
cd /got/ebios

# Or add to Python path
export PYTHONPATH=/got/ebios:$PYTHONPATH
```

### Issue: API server not responding

```bash
# Check if server is running
curl http://localhost:8000/

# Start server if needed
python src/nugovern/server.py
```

### Issue: Policy not found

```bash
# Check available policies
ls governance/policies/*.json

# Verify policy path in code
from src.nupolicy import PolicyManager
manager = PolicyManager(policy_dir='/got/ebios/governance/policies')
```

## Next Steps

1. **Run the examples**: Start with `basic_usage.py`
2. **Read the docs**: See `docs/README.md` for specifications
3. **Modify examples**: Experiment with different parameters
4. **Create policies**: Add custom policies in `governance/policies/`
5. **Deploy API**: Use `uvicorn` for production deployment

## References

- **Documentation**: `/docs/README.md`
- **API Reference**: `/docs/NUGovern_API.md`
- **Layer Specs**: `/docs/*_SPEC.md`
- **Tests**: `/tests/` for more examples

---

**eBIOS Examples** - Learn by doing.
