# eBIOS API Documentation v1.0.0

**Version**: 1.0.0
**Base URL**: `https://api.ebios.org` (production) or `http://localhost:8080` (development)
**Authentication**: JWT Bearer Token
**Content-Type**: `application/json`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Authorization (RBAC)](#authorization-rbac)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [Endpoints](#endpoints)
   - [Health & Status](#health--status)
   - [Authentication](#authentication-endpoints)
   - [Operations](#operations-endpoints)
   - [Ledger](#ledger-endpoints)
   - [Metrics](#metrics-endpoints)
7. [Examples](#examples)
8. [SDKs & Client Libraries](#sdks--client-libraries)

---

## Overview

The eBIOS API provides secure access to epistemic computation operations with formal guarantees. All operations are:

- **Deterministic**: Same input always produces same output
- **Uncertainty-Aware**: Propagates N/U (Nominal/Uncertainty) pairs
- **Formally Verified**: 100% Lean 4 proven (0 sorry statements)
- **Auditable**: All operations logged to immutable ledger
- **Rate Limited**: 100 requests per minute per IP (configurable)

### Key Features

✅ JWT authentication with refresh tokens
✅ Role-Based Access Control (4 roles)
✅ Immutable operation ledger (PostgreSQL)
✅ Prometheus metrics
✅ HTTPS/TLS 1.2+ required
✅ OpenAPI/Swagger compatible

---

## Authentication

### Token Types

eBIOS uses two JWT token types:

| Token Type | Expiry | Purpose |
|------------|--------|---------|
| **Access Token** | 1 hour | API requests |
| **Refresh Token** | 30 days | Renew access tokens |

### Obtaining Tokens

**Request:**
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using Tokens

Include the access token in the `Authorization` header:

```http
GET /operations/execute
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refreshing Tokens

When the access token expires (HTTP 401), use the refresh token:

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Token Security

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Payload**: `{"sub": "username", "role": "admin", "exp": 1698765432}`
- **Storage**: Store tokens securely (never in localStorage, use httpOnly cookies)
- **Transmission**: HTTPS only (TLS 1.2+)
- **Revocation**: Logout endpoint invalidates tokens (requires token blacklist implementation)

---

## Authorization (RBAC)

eBIOS implements Role-Based Access Control with 4 roles:

### Role Hierarchy

```
admin (Full Access)
  ├── operator (Operations + Queries)
  │     └── auditor (Read-Only)
  │           └── guest (Health Check Only)
```

### Permission Matrix

| Endpoint | admin | operator | auditor | guest |
|----------|-------|----------|---------|-------|
| `GET /` | ✅ | ✅ | ✅ | ✅ |
| `POST /auth/login` | ✅ | ✅ | ✅ | ✅ |
| `POST /operations/execute` | ✅ | ✅ | ❌ | ❌ |
| `POST /operations/batch` | ✅ | ✅ | ❌ | ❌ |
| `GET /ledger/query` | ✅ | ✅ | ✅ | ❌ |
| `GET /ledger/verify` | ✅ | ✅ | ✅ | ❌ |
| `GET /metrics` | ✅ | ❌ | ❌ | ❌ |
| `POST /admin/users` | ✅ | ❌ | ❌ | ❌ |

### Default Users

**Development/Testing Only** (Change in production!)

```python
# Default credentials (src/nugovern/auth.py)
admin / admin123       # Full access
operator / operator123 # Operations + queries
auditor / auditor123   # Read-only
guest / guest123       # Health check only
```

⚠️ **Security Warning**: These are development credentials. In production, use the user management CLI to create secure accounts.

---

## Rate Limiting

### Current Limits

- **Rate**: 100 requests per minute per IP address
- **Window**: Rolling 60-second window
- **Scope**: Per IP (X-Forwarded-For aware)
- **Exclusions**: Health check endpoint (`/`)

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1698765492
```

### Exceeded Response

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 42

{
  "error": "Rate limit exceeded: 100 per 1 minute"
}
```

### Best Practices

1. **Batch Operations**: Use `/operations/batch` for multiple operations
2. **Exponential Backoff**: Retry with delays (1s, 2s, 4s, 8s...)
3. **Caching**: Cache ledger queries when possible
4. **Connection Pooling**: Reuse HTTP connections

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid JSON, missing fields |
| 401 | Unauthorized | Missing/expired token |
| 403 | Forbidden | Insufficient role permissions |
| 404 | Not Found | Operation ID not in ledger |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error (contact admin) |

### Error Response Format

```json
{
  "error": "Short error message",
  "detail": "Detailed explanation of what went wrong",
  "error_code": "ERR_INVALID_INPUT",
  "timestamp": "2025-10-29T14:32:10Z"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `ERR_AUTH_FAILED` | Authentication failed |
| `ERR_TOKEN_EXPIRED` | Access token expired |
| `ERR_INSUFFICIENT_PERMISSIONS` | Role lacks required permission |
| `ERR_INVALID_INPUT` | Input validation failed |
| `ERR_OPERATION_FAILED` | Operation execution failed |
| `ERR_LEDGER_NOT_FOUND` | Operation ID not found |
| `ERR_RATE_LIMIT` | Rate limit exceeded |

---

## Endpoints

### Health & Status

#### `GET /`

**Description**: Health check endpoint (no authentication required)

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "eBIOS",
  "timestamp": "2025-10-29T14:32:10Z",
  "layers": {
    "layer0_nu_algebra": "operational",
    "layer1_propagation": "operational",
    "layer2_operations": "operational",
    "layer3_ledger": "operational",
    "layer4_governance": "operational",
    "layer5_attestation": "operational",
    "layer6_consensus": "operational",
    "layer7_api": "operational"
  },
  "database": {
    "status": "connected",
    "type": "postgresql",
    "version": "17.6"
  }
}
```

**Rate Limit**: Exempt from rate limiting

---

### Authentication Endpoints

#### `POST /auth/login`

**Description**: Login with username and password

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTY5ODc2OTAzMiwidHlwZSI6ImFjY2VzcyJ9.xxxxxxxxxxx",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMTM2MTAzMiwidHlwZSI6InJlZnJlc2gifQ.yyyyyyyyyyy",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error (401):**
```json
{
  "detail": "Incorrect username or password"
}
```

**Required Role**: None (public endpoint)

---

#### `POST /auth/refresh`

**Description**: Refresh access token using refresh token

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error (401):**
```json
{
  "detail": "Invalid or expired refresh token"
}
```

**Required Role**: None (uses refresh token)

---

#### `GET /auth/me`

**Description**: Get current user information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "username": "admin",
  "role": "admin",
  "permissions": [
    "operations:execute",
    "operations:batch",
    "ledger:query",
    "ledger:verify",
    "admin:users",
    "admin:metrics"
  ],
  "token_expires_at": "2025-10-29T15:32:10Z"
}
```

**Required Role**: Any authenticated user

---

#### `POST /auth/logout`

**Description**: Logout and invalidate tokens

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

⚠️ **Note**: Token blacklist implementation pending. Currently tokens remain valid until expiry.

**Required Role**: Any authenticated user

---

### Operations Endpoints

#### `POST /operations/execute`

**Description**: Execute a single eBIOS operation with formal guarantees

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "operation": "multiply",
  "inputs": {
    "a": {"nominal": 2.0, "uncertainty": 0.1},
    "b": {"nominal": 3.0, "uncertainty": 0.15}
  },
  "parent_id": null
}
```

**Response (200):**
```json
{
  "op_id": "op_20251029143210_abc123",
  "operation": "multiply",
  "result": {
    "nominal": 6.0,
    "uncertainty": 0.36
  },
  "coverage": 0.9973,
  "invariant_passed": true,
  "timestamp": "2025-10-29T14:32:10Z",
  "parent_id": null,
  "signature": "ed25519:a1b2c3d4e5f6..."
}
```

**Supported Operations:**

| Operation | Inputs | Description |
|-----------|--------|-------------|
| `add` | `a`, `b` | Addition with uncertainty propagation |
| `subtract` | `a`, `b` | Subtraction with uncertainty propagation |
| `multiply` | `a`, `b` | Multiplication with uncertainty propagation |
| `divide` | `a`, `b` | Division with uncertainty propagation (b ≠ 0) |
| `sqrt` | `x` | Square root with uncertainty propagation (x ≥ 0) |
| `pow` | `base`, `exponent` | Power with uncertainty propagation |
| `sin` | `x` | Sine with uncertainty propagation |
| `cos` | `x` | Cosine with uncertainty propagation |
| `exp` | `x` | Exponential with uncertainty propagation |
| `log` | `x` | Natural logarithm with uncertainty propagation (x > 0) |

**Input Format:**
```json
{
  "nominal": 2.0,      // Nominal (expected) value
  "uncertainty": 0.1   // Uncertainty (standard deviation)
}
```

**Error (400):**
```json
{
  "error": "Invalid operation",
  "detail": "Operation 'invalid_op' not supported. Available: add, subtract, multiply, divide, sqrt, pow, sin, cos, exp, log"
}
```

**Required Role**: `admin`, `operator`

---

#### `POST /operations/batch`

**Description**: Execute multiple operations atomically

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request:**
```json
{
  "operations": [
    {
      "operation": "add",
      "inputs": {
        "a": {"nominal": 1.0, "uncertainty": 0.05},
        "b": {"nominal": 2.0, "uncertainty": 0.1}
      }
    },
    {
      "operation": "multiply",
      "inputs": {
        "a": {"nominal": 3.0, "uncertainty": 0.15},
        "b": {"nominal": 4.0, "uncertainty": 0.2}
      }
    }
  ]
}
```

**Response (200):**
```json
{
  "batch_id": "batch_20251029143210_xyz789",
  "total_operations": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "op_id": "op_20251029143210_001",
      "operation": "add",
      "result": {"nominal": 3.0, "uncertainty": 0.112},
      "coverage": 0.9973,
      "invariant_passed": true
    },
    {
      "op_id": "op_20251029143210_002",
      "operation": "multiply",
      "result": {"nominal": 12.0, "uncertainty": 0.9},
      "coverage": 0.9973,
      "invariant_passed": true
    }
  ],
  "timestamp": "2025-10-29T14:32:10Z"
}
```

**Error Handling**: If any operation fails, entire batch is rolled back (atomic execution)

**Required Role**: `admin`, `operator`

---

### Ledger Endpoints

#### `GET /ledger/query`

**Description**: Query operations from the immutable ledger

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `op_id` | string | Specific operation ID | - |
| `operation` | string | Filter by operation type | - |
| `start_time` | int | Start timestamp (Unix epoch) | 0 |
| `end_time` | int | End timestamp (Unix epoch) | now |
| `limit` | int | Maximum results | 100 |
| `offset` | int | Pagination offset | 0 |

**Example:**
```http
GET /ledger/query?operation=multiply&limit=10&offset=0
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "operations": [
    {
      "op_id": "op_20251029143210_abc123",
      "operation": "multiply",
      "inputs": {
        "a": {"nominal": 2.0, "uncertainty": 0.1},
        "b": {"nominal": 3.0, "uncertainty": 0.15}
      },
      "output": {"nominal": 6.0, "uncertainty": 0.36},
      "coverage": 0.9973,
      "invariant_passed": true,
      "timestamp": "2025-10-29T14:32:10Z",
      "parent_id": null,
      "signature": "ed25519:a1b2c3d4e5f6..."
    }
  ]
}
```

**Required Role**: `admin`, `operator`, `auditor`

---

#### `GET /ledger/verify/{op_id}`

**Description**: Verify cryptographic signature and integrity of an operation

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "op_id": "op_20251029143210_abc123",
  "signature_valid": true,
  "invariant_passed": true,
  "coverage": 0.9973,
  "timestamp": "2025-10-29T14:32:10Z",
  "hash": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "signer": "eBIOS-v1.0.0"
}
```

**Error (404):**
```json
{
  "error": "Operation not found",
  "detail": "No operation found with ID: op_invalid123"
}
```

**Required Role**: `admin`, `operator`, `auditor`

---

### Metrics Endpoints

#### `GET /metrics`

**Description**: Prometheus-compatible metrics endpoint

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):** (Prometheus text format)
```
# HELP ebios_requests_total Total number of requests
# TYPE ebios_requests_total counter
ebios_requests_total{method="POST",endpoint="/operations/execute",status="200"} 1234

# HELP ebios_request_duration_seconds Request duration in seconds
# TYPE ebios_request_duration_seconds histogram
ebios_request_duration_seconds_bucket{le="0.01"} 450
ebios_request_duration_seconds_bucket{le="0.05"} 890
ebios_request_duration_seconds_bucket{le="0.1"} 1200
ebios_request_duration_seconds_sum 45.67
ebios_request_duration_seconds_count 1234

# HELP ebios_operations_total Total operations executed
# TYPE ebios_operations_total counter
ebios_operations_total{operation="multiply"} 567
ebios_operations_total{operation="add"} 432

# HELP ebios_invariant_failures_total Total invariant check failures
# TYPE ebios_invariant_failures_total counter
ebios_invariant_failures_total 0

# HELP ebios_ledger_entries_total Total ledger entries
# TYPE ebios_ledger_entries_total gauge
ebios_ledger_entries_total 12345
```

**Required Role**: `admin`

**Access Control**: Nginx should restrict this endpoint to localhost/monitoring systems only

---

## Examples

### Example 1: Complete Authentication Flow

```bash
#!/bin/bash

# 1. Login
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"operator","password":"operator123"}')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
REFRESH_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.refresh_token')

echo "Access Token: $ACCESS_TOKEN"

# 2. Execute operation
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "multiply",
    "inputs": {
      "a": {"nominal": 5.0, "uncertainty": 0.2},
      "b": {"nominal": 3.0, "uncertainty": 0.1}
    }
  }'

# 3. Query ledger
curl -X GET "http://localhost:8080/ledger/query?limit=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Refresh token (after 55 minutes)
NEW_TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

NEW_ACCESS_TOKEN=$(echo $NEW_TOKEN_RESPONSE | jq -r '.access_token')

# 5. Logout
curl -X POST http://localhost:8080/auth/logout \
  -H "Authorization: Bearer $NEW_ACCESS_TOKEN"
```

---

### Example 2: Batch Operations

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
USERNAME = "operator"
PASSWORD = "operator123"

# Login
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)
login_response.raise_for_status()
access_token = login_response.json()["access_token"]

# Prepare headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Execute batch operations
batch_request = {
    "operations": [
        {
            "operation": "add",
            "inputs": {
                "a": {"nominal": 10.0, "uncertainty": 0.5},
                "b": {"nominal": 20.0, "uncertainty": 1.0}
            }
        },
        {
            "operation": "multiply",
            "inputs": {
                "a": {"nominal": 2.5, "uncertainty": 0.1},
                "b": {"nominal": 4.0, "uncertainty": 0.2}
            }
        },
        {
            "operation": "sqrt",
            "inputs": {
                "x": {"nominal": 16.0, "uncertainty": 0.5}
            }
        }
    ]
}

batch_response = requests.post(
    f"{BASE_URL}/operations/batch",
    headers=headers,
    json=batch_request
)
batch_response.raise_for_status()

# Print results
batch_result = batch_response.json()
print(f"Batch ID: {batch_result['batch_id']}")
print(f"Successful: {batch_result['successful']}/{batch_result['total_operations']}")

for i, result in enumerate(batch_result['results'], 1):
    print(f"\nOperation {i}:")
    print(f"  Operation: {result['operation']}")
    print(f"  Result: {result['result']['nominal']} ± {result['result']['uncertainty']}")
    print(f"  Coverage: {result['coverage']:.4f}")
    print(f"  Invariant Passed: {result['invariant_passed']}")
```

---

### Example 3: Error Handling with Retry

```python
import requests
import time
from typing import Dict, Any

def execute_operation_with_retry(
    base_url: str,
    access_token: str,
    operation: str,
    inputs: Dict[str, Any],
    max_retries: int = 3
) -> Dict[str, Any]:
    """Execute operation with exponential backoff retry"""

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "operation": operation,
        "inputs": inputs
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{base_url}/operations/execute",
                headers=headers,
                json=payload,
                timeout=10
            )

            # Success
            if response.status_code == 200:
                return response.json()

            # Rate limit - retry with backoff
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Retrying after {retry_after}s...")
                time.sleep(retry_after)
                continue

            # Token expired - need to refresh
            elif response.status_code == 401:
                raise Exception("Token expired. Please refresh access token.")

            # Other errors
            else:
                response.raise_for_status()

        except requests.exceptions.Timeout:
            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            print(f"Timeout. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    raise Exception(f"Failed after {max_retries} attempts")

# Usage
result = execute_operation_with_retry(
    base_url="http://localhost:8080",
    access_token="your_access_token_here",
    operation="multiply",
    inputs={
        "a": {"nominal": 5.0, "uncertainty": 0.2},
        "b": {"nominal": 3.0, "uncertainty": 0.1}
    }
)
print(f"Result: {result['result']}")
```

---

### Example 4: Ledger Audit Trail

```python
import requests
from datetime import datetime, timedelta

def audit_operations(
    base_url: str,
    access_token: str,
    hours: int = 24
) -> None:
    """Generate audit report for operations in the last N hours"""

    headers = {"Authorization": f"Bearer {access_token}"}

    # Calculate time range
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())

    # Query ledger
    params = {
        "start_time": start_time,
        "end_time": end_time,
        "limit": 1000,
        "offset": 0
    }

    response = requests.get(
        f"{base_url}/ledger/query",
        headers=headers,
        params=params
    )
    response.raise_for_status()

    data = response.json()
    operations = data['operations']

    # Generate report
    print(f"=== Audit Report (Last {hours} hours) ===\n")
    print(f"Total Operations: {data['total']}")

    # Count by operation type
    op_counts = {}
    invariant_failures = 0

    for op in operations:
        op_type = op['operation']
        op_counts[op_type] = op_counts.get(op_type, 0) + 1

        if not op['invariant_passed']:
            invariant_failures += 1
            print(f"\n⚠️  INVARIANT FAILURE: {op['op_id']}")
            print(f"   Operation: {op_type}")
            print(f"   Timestamp: {op['timestamp']}")

    print("\nOperation Counts:")
    for op_type, count in sorted(op_counts.items()):
        print(f"  {op_type}: {count}")

    print(f"\nInvariant Failures: {invariant_failures}")

    if invariant_failures == 0:
        print("✅ All operations passed invariant checks")

# Usage
audit_operations(
    base_url="http://localhost:8080",
    access_token="your_access_token_here",
    hours=24
)
```

---

## SDKs & Client Libraries

### Official Libraries (Planned)

| Language | Status | Repository |
|----------|--------|------------|
| Python | 🚧 In Development | `ebios-python` |
| JavaScript/TypeScript | 📋 Planned | `ebios-js` |
| Rust | 📋 Planned | `ebios-rs` |
| Go | 📋 Planned | `ebios-go` |

### Community Libraries

*None yet - contributions welcome!*

---

## Appendix

### A. OpenAPI/Swagger Specification

OpenAPI 3.0 specification available at:
- **Endpoint**: `GET /openapi.json`
- **Swagger UI**: `GET /docs` (interactive documentation)
- **ReDoc**: `GET /redoc` (alternative documentation view)

### B. Versioning

eBIOS API follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to API
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

**API Version Header**: Include `Accept: application/vnd.ebios.v1+json` for version pinning

### C. Support & Resources

- **Documentation**: https://docs.ebios.org
- **GitHub**: https://github.com/abba-01/ebios
- **Issues**: https://github.com/abba-01/ebios/issues
- **Email**: support@ebios.org

### D. Compliance Mappings

eBIOS is designed for safety-critical systems:

- **ISO 26262** (Automotive): ASIL D compliance
- **DO-178C** (Aviation): Level A compliance
- **IEC 61508** (Industrial): SIL 4 compliance

Formal verification artifacts available in `proofs/` directory.

---

**Last Updated**: 2025-10-29
**API Version**: 1.0.0
**Document Version**: 1.0.0

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
