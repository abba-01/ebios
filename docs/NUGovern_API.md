# NUGovern API Documentation

**Layer 6 of eBIOS: HTTP API for Governance and Attestation**

## Philosophy

> "Governance through transparent interfaces."

NUGovern exposes the entire eBIOS stack through a RESTful HTTP API, enabling remote operation execution, policy management, audit queries, and cryptographic attestation. Every action is logged, every policy is auditable, and every attestation is verifiable.

## Base URL

```
http://localhost:8000
```

## OpenAPI Documentation

Interactive documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Authentication

**Current Status**: No authentication (v0.1.0)

**Planned** (v1.0.0): JWT-based authentication with role-based access control

## Endpoints

### Health Check

#### `GET /`

Health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "layers": {
    "nucore": true,
    "nuledger": true,
    "nuguard": true,
    "nupolicy": true
  }
}
```

---

## NUCore Operations

### Execute Operation

#### `POST /operations/execute`

Execute NUCore operation with monitoring and ledger logging.

**Request Body**:
```json
{
  "operation": "add",
  "inputs": [[10.0, 0.5], [20.0, 1.0]],
  "params": null
}
```

**Parameters**:
- `operation` (string): Operation type (`add`, `multiply`, `compose`, `catch`, `flip`)
- `inputs` (array): List of `[nominal, uncertainty]` pairs
- `params` (object, optional): Operation-specific parameters (e.g., `lambda_margin` for multiply)

**Response** (200 OK):
```json
{
  "result": [30.0, 1.12],
  "coverage": 0.037,
  "invariant_passed": true,
  "ledger_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Fields**:
- `result`: Output `[nominal, uncertainty]` pair
- `coverage`: Coverage ratio (u/|n|)
- `invariant_passed`: Whether invariants were satisfied
- `ledger_id`: Ledger entry ID (if auto_log enabled)

**Errors**:
- `400 Bad Request`: Invalid operation or inputs
- `500 Internal Server Error`: Operation execution failed

**Example - Addition**:
```bash
curl -X POST http://localhost:8000/operations/execute \
  -H "Content-Type: application/json" \
  -d '{"operation":"add","inputs":[[10.0,0.5],[20.0,1.0]]}'
```

**Example - Multiplication with Parameter**:
```bash
curl -X POST http://localhost:8000/operations/execute \
  -H "Content-Type: application/json" \
  -d '{"operation":"multiply","inputs":[[10.0,0.5],[20.0,1.0]],"params":{"lambda_margin":1.5}}'
```

---

## Policy Management

### List Policies

#### `GET /policies`

List all available policies.

**Response** (200 OK):
```json
["ConservativePolicy", "PermissivePolicy", "AuditOnlyPolicy"]
```

### Create Policy

#### `POST /policies`

Create new policy file.

**Request Body**:
```json
{
  "name": "ProductionPolicy",
  "description": "Production monitoring policy",
  "version": "1.0.0",
  "rules": [
    {"type": "InvariantRule"},
    {"type": "CoverageRule", "threshold": 0.1, "level": "warning"}
  ],
  "escalation": {
    "halt_on_critical": false,
    "auto_log": true
  },
  "metadata": {
    "author": "DevOps",
    "environment": "production"
  }
}
```

**Response** (200 OK):
```json
{
  "name": "ProductionPolicy",
  "version": "1.0.0",
  "description": "Production monitoring policy",
  "policy_hash": "a3f5e8d9c2b4f1a7...",
  "signed": false,
  "rules_count": 2
}
```

### Get Policy

#### `GET /policies/{name}`

Retrieve specific policy and activate it (reconfigure monitor).

**Response** (200 OK):
```json
{
  "name": "ProductionPolicy",
  "version": "1.0.0",
  "description": "Production monitoring policy",
  "policy_hash": "a3f5e8d9c2b4f1a7...",
  "signed": false,
  "rules_count": 2
}
```

**Errors**:
- `404 Not Found`: Policy does not exist

### Activate Policy

#### `PUT /policies/{name}/activate`

Activate policy (reconfigure monitor to use policy rules).

**Response** (200 OK):
```json
{
  "message": "Policy 'ProductionPolicy' activated",
  "policy": {
    "name": "ProductionPolicy",
    "version": "1.0.0",
    "description": "Production monitoring policy",
    "policy_hash": "a3f5e8d9c2b4f1a7...",
    "signed": false,
    "rules_count": 2
  }
}
```

---

## Ledger Queries

### Get Ledger Entries

#### `GET /ledger/entries`

Query ledger entries with optional filtering and pagination.

**Query Parameters**:
- `operation_id` (string, optional): Trace specific operation
- `limit` (integer, default=100): Maximum entries to return
- `offset` (integer, default=0): Offset for pagination

**Response** (200 OK):
```json
[
  {
    "op_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": 1,
    "operation": "add",
    "inputs": [[10.0, 0.5], [20.0, 1.0]],
    "output": [30.0, 1.12],
    "coverage": 0.037,
    "invariant_passed": true,
    "parent_id": null,
    "signature": "base64_signature..."
  }
]
```

**Example - Get all entries**:
```bash
curl http://localhost:8000/ledger/entries
```

**Example - Trace specific operation**:
```bash
curl "http://localhost:8000/ledger/entries?operation_id=550e8400-e29b-41d4-a716-446655440000"
```

**Example - Pagination**:
```bash
curl "http://localhost:8000/ledger/entries?limit=10&offset=20"
```

### Verify Ledger Integrity

#### `GET /ledger/verify`

Verify complete ledger integrity via Merkle tree.

**Response** (200 OK):
```json
{
  "valid": true,
  "entries": 42,
  "root": "7f8c3d2a1b4e5f6g..."
}
```

**Fields**:
- `valid`: Whether ledger passes integrity check
- `entries`: Total number of entries
- `root`: Current Merkle root hash

---

## Monitoring

### Get Monitor Statistics

#### `GET /monitor/stats`

Retrieve current monitor statistics.

**Response** (200 OK):
```json
{
  "total_events": 42,
  "violations": 3,
  "rules": [
    "InvariantRule",
    "CoverageRule(threshold=0.1)"
  ],
  "handlers": 1,
  "auto_log": true,
  "halt_on_critical": false
}
```

### Reset Monitor

#### `POST /monitor/reset`

Reset monitor statistics (events and violations counters).

**Response** (200 OK):
```json
{
  "message": "Monitor statistics reset"
}
```

---

## Attestation

### Create Attestation

#### `POST /attestation`

Create cryptographic attestation for policy or ledger.

**Request Body**:
```json
{
  "attestation_type": "policy",
  "target_id": "ProductionPolicy"
}
```

**Parameters**:
- `attestation_type` (string): Type of attestation (`policy`, `ledger`)
- `target_id` (string, optional): Target identifier (policy name for `policy` type)

**Response** (200 OK):
```json
{
  "attestation_type": "policy",
  "target_id": "ProductionPolicy",
  "timestamp": "2025-10-20T00:00:00Z",
  "hash": "a3f5e8d9c2b4f1a7...",
  "signature": "base64_signature...",
  "verified": false
}
```

**Fields**:
- `attestation_type`: Type of attestation
- `target_id`: Target identifier
- `timestamp`: Attestation timestamp (ISO 8601)
- `hash`: SHA-256 hash (policy hash or Merkle root)
- `signature`: Cryptographic signature (policy signature or "merkle_root")
- `verified`: Whether signature/integrity is verified

**Example - Policy Attestation**:
```bash
curl -X POST http://localhost:8000/attestation \
  -H "Content-Type: application/json" \
  -d '{"attestation_type":"policy","target_id":"ProductionPolicy"}'
```

**Example - Ledger Attestation**:
```bash
curl -X POST http://localhost:8000/attestation \
  -H "Content-Type: application/json" \
  -d '{"attestation_type":"ledger"}'
```

**Errors**:
- `404 Not Found`: Target policy not found
- `400 Bad Request`: Invalid attestation type or missing target_id

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters or body
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

---

## Running the Server

### Development Mode

```bash
python src/nugovern/server.py
```

Server starts at `http://0.0.0.0:8000`

### Production Mode (with Uvicorn)

```bash
uvicorn src.nugovern.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment (Planned)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src /app/src
EXPOSE 8000
CMD ["uvicorn", "src.nugovern.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Client Examples

### Python Client

```python
import requests

# Execute operation
response = requests.post("http://localhost:8000/operations/execute", json={
    "operation": "add",
    "inputs": [[10.0, 0.5], [20.0, 1.0]]
})
result = response.json()
print(f"Result: {result['result']}, Coverage: {result['coverage']}")

# Create policy
policy_response = requests.post("http://localhost:8000/policies", json={
    "name": "MyPolicy",
    "description": "Custom policy",
    "version": "1.0.0",
    "rules": [{"type": "InvariantRule"}],
    "escalation": {"halt_on_critical": True, "auto_log": True}
})

# Activate policy
activate = requests.put("http://localhost:8000/policies/MyPolicy/activate")
print(activate.json()['message'])

# Query ledger
ledger = requests.get("http://localhost:8000/ledger/entries?limit=10")
entries = ledger.json()
print(f"Retrieved {len(entries)} ledger entries")

# Verify ledger
verify = requests.get("http://localhost:8000/ledger/verify")
print(f"Ledger valid: {verify.json()['valid']}")
```

### cURL Examples

See individual endpoint sections above for cURL examples.

---

## Integration with eBIOS Stack

| Layer | API Integration |
|-------|-----------------|
| **Layer 1 (NUCore)** | `/operations/execute` for all operations |
| **Layer 3 (NULedger)** | `/ledger/*` for audit queries and verification |
| **Layer 4 (NUGuard)** | `/monitor/*` for statistics and reset |
| **Layer 5 (NUPolicy)** | `/policies/*` for policy management |
| **Layer 6 (NUGovern)** | `/attestation` for cryptographic proofs |

---

## Versioning

**Current Version**: 0.1.0

**Versioning Scheme**: Semantic Versioning (MAJOR.MINOR.PATCH)

**API Compatibility**: Breaking changes will increment MAJOR version

---

## Rate Limiting (Planned)

**v1.0.0 will include**:
- Rate limiting per IP address
- Configurable limits via policy files
- HTTP 429 Too Many Requests responses

---

## Security Considerations

1. **No Authentication (v0.1.0)**: Current version has no authentication. **Do not expose to public networks**.

2. **HTTPS Required (Production)**: Always use HTTPS in production deployments.

3. **Policy Signing**: While policies can be signed, signature verification is optional in v0.1.0.

4. **Ledger Immutability**: Once entries are in the ledger, they cannot be modified or deleted.

5. **Monitor Configuration**: Activating a policy reconfigures the monitor globally for all subsequent operations.

---

## References

- **NUCore Operations**: `/docs/NUCore_SPEC.md`
- **NULedger Audit Log**: `/docs/NULedger_SPEC.md`
- **NUGuard Monitoring**: `/docs/NUGuard_POLICY.md`
- **NUPolicy Management**: `/docs/NUPolicy_SPEC.md`
- **eBIOS Architecture**: `/docs/README.md`

---

## Version

- **NUGovern Version**: 0.1.0
- **eBIOS Layer**: 6
- **Status**: Active development (PHASE 6)

---

**NUGovern** — Governance through transparent interfaces.

*"Every action logged. Every policy auditable. Every attestation verifiable."*
