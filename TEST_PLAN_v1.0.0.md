# eBIOS v1.0.0 Test Plan (SSOT)

**Version**: 1.0.0
**Date**: 2025-10-29
**Status**: Test Execution Plan
**Test Environment**: tot.allyourbaseline.com (staging)

---

## Test Execution Summary

**Objective**: Comprehensive autonomous testing of v1.0.0 features before production release

**Scope**:
- ✅ Static Analysis (security, code quality)
- ✅ Dependency Scanning (vulnerabilities)
- ✅ Container Security (image scanning)
- ✅ Integration Testing (auth, RBAC, operations)
- ✅ Load Testing (performance, rate limits)
- ✅ Database Testing (PostgreSQL persistence)
- ✅ API Testing (all endpoints)

**Out of Scope**:
- ❌ Penetration testing (manual, requires authorization)
- ❌ UI testing (no UI in v1.0.0)
- ❌ Browser compatibility (API only)

---

## Test Environment Specification

### Server Configuration

**Staging Server**: tot.allyourbaseline.com
**Production Server**: got.gitgap.org (reference only, no testing)

**Hardware**:
- CPU: 2+ cores
- RAM: 4+ GB
- Disk: 20+ GB

**Software**:
- OS: RHEL 10 / Linux 6.12.0
- Docker: 24.0+
- Python: 3.12+
- PostgreSQL: 17.6 (DigitalOcean managed)

### Database Configuration

**Connection Details**:
- Host: db-postgresql-nyc3-12345-do-user-67890-0.b.db.ondigitalocean.com
- Port: 25060
- Database: ebios_staging (create new database for testing)
- SSL: Required
- Network: Private VPC (10.124.0.0/20)

### Test Data

**Default Users** (for testing):
```python
admin / admin123       # Full access
operator / operator123 # Operations + queries
auditor / auditor123   # Read-only
guest / guest123       # Health check only
```

⚠️ **Note**: These are test credentials. Production must use different passwords.

---

## Test Categories

### Category 1: Static Analysis (30 minutes)

**Objective**: Identify code quality issues and security vulnerabilities without execution

#### Test 1.1: Python Security Linting (Bandit)

**Tool**: bandit
**Command**:
```bash
bandit -r src/ -f json -o reports/bandit_report.json -ll
```

**Pass Criteria**:
- Zero HIGH severity issues
- Zero CRITICAL severity issues
- < 5 MEDIUM severity issues (review acceptable)

**Expected Findings**:
- B101: assert_used (acceptable in tests)
- B603: subprocess_without_shell_equals_true (review each)

---

#### Test 1.2: Code Quality (Pylint)

**Tool**: pylint
**Command**:
```bash
pylint src/ --output-format=json --reports=y > reports/pylint_report.json
```

**Pass Criteria**:
- Score: ≥ 8.0/10
- Zero ERROR level issues
- < 10 WARNING level issues

---

#### Test 1.3: Type Checking (Mypy)

**Tool**: mypy
**Command**:
```bash
mypy src/ --strict --json-report reports/mypy_report
```

**Pass Criteria**:
- Zero type errors in core modules (auth.py, backends.py)
- < 5 type errors in non-critical modules

---

### Category 2: Dependency Scanning (15 minutes)

**Objective**: Identify known vulnerabilities in dependencies

#### Test 2.1: Known Vulnerabilities (Safety)

**Tool**: safety
**Command**:
```bash
safety check --json > reports/safety_report.json
```

**Pass Criteria**:
- Zero CRITICAL vulnerabilities
- Zero HIGH vulnerabilities
- < 3 MEDIUM vulnerabilities (must have mitigation plan)

---

#### Test 2.2: PyPI Advisory Database (pip-audit)

**Tool**: pip-audit
**Command**:
```bash
pip-audit --desc --format json > reports/pip_audit_report.json
```

**Pass Criteria**:
- Zero vulnerabilities with CVSS ≥ 7.0
- All vulnerabilities have fix available or workaround documented

---

### Category 3: Container Security (20 minutes)

**Objective**: Scan Docker image for vulnerabilities

#### Test 3.1: Docker Image Scan (Trivy)

**Tool**: trivy
**Command**:
```bash
docker build -t ebios:1.0.0-test .
trivy image --severity HIGH,CRITICAL --format json --output reports/trivy_report.json ebios:1.0.0-test
```

**Pass Criteria**:
- Zero CRITICAL vulnerabilities
- < 5 HIGH vulnerabilities
- All HIGH vulnerabilities in base image (python:3.12-slim) are acceptable if no fix available

---

#### Test 3.2: Docker Bench Security

**Tool**: docker-bench-security
**Command**:
```bash
docker run --net host --pid host --cap-add audit_control \
  -v /var/lib:/var/lib -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc --label docker_bench_security \
  docker/docker-bench-security
```

**Pass Criteria**:
- Zero WARN on critical checks (1.*, 2.*, 4.1)
- Document all INFO findings

---

### Category 4: Integration Testing (60 minutes)

**Objective**: Test complete workflows end-to-end

#### Test 4.1: Authentication Flow

**Test Cases**:

**TC-AUTH-001**: Successful Login
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

Expected: 200 OK, access_token + refresh_token returned
```

**TC-AUTH-002**: Failed Login (Wrong Password)
```bash
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}'

Expected: 401 Unauthorized
```

**TC-AUTH-003**: Token Refresh
```bash
curl -X POST http://localhost:8080/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<VALID_REFRESH_TOKEN>"}'

Expected: 200 OK, new access_token returned
```

**TC-AUTH-004**: Get Current User
```bash
curl http://localhost:8080/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

Expected: 200 OK, user info with username, role, permissions
```

**TC-AUTH-005**: Logout
```bash
curl -X POST http://localhost:8080/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

Expected: 200 OK, success message
```

**Pass Criteria**: 5/5 test cases pass

---

#### Test 4.2: RBAC Authorization

**Test Cases**:

**TC-RBAC-001**: Admin Access to All Endpoints
```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Test all endpoints
curl http://localhost:8080/operations/execute -H "Authorization: Bearer $TOKEN"
curl http://localhost:8080/ledger/query -H "Authorization: Bearer $TOKEN"
curl http://localhost:8080/metrics -H "Authorization: Bearer $TOKEN"

Expected: All return 200 OK (or 422 for missing data, not 403)
```

**TC-RBAC-002**: Operator Access (Operations + Queries)
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"operator","password":"operator123"}' | jq -r '.access_token')

curl -X POST http://localhost:8080/operations/execute -H "Authorization: Bearer $TOKEN" -d '{...}'
curl http://localhost:8080/ledger/query -H "Authorization: Bearer $TOKEN"
curl http://localhost:8080/metrics -H "Authorization: Bearer $TOKEN"

Expected: operations ✅, ledger ✅, metrics ❌ (403 Forbidden)
```

**TC-RBAC-003**: Auditor Access (Read-Only)
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"auditor","password":"auditor123"}' | jq -r '.access_token')

curl http://localhost:8080/ledger/query -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8080/operations/execute -H "Authorization: Bearer $TOKEN"

Expected: ledger ✅, operations ❌ (403 Forbidden)
```

**TC-RBAC-004**: Guest Access (Health Only)
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"guest","password":"guest123"}' | jq -r '.access_token')

curl http://localhost:8080/
curl http://localhost:8080/operations/execute -H "Authorization: Bearer $TOKEN"

Expected: health ✅, operations ❌ (403 Forbidden)
```

**Pass Criteria**: All RBAC rules correctly enforced (4/4 test cases)

---

#### Test 4.3: Operations Execution

**Test Cases**:

**TC-OPS-001**: Addition
```bash
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "add",
    "inputs": {
      "a": {"nominal": 5.0, "uncertainty": 0.2},
      "b": {"nominal": 3.0, "uncertainty": 0.1}
    }
  }'

Expected: 200 OK, result = 8.0 ± 0.224, invariant_passed = true
```

**TC-OPS-002**: Multiplication
```bash
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "multiply",
    "inputs": {
      "a": {"nominal": 2.5, "uncertainty": 0.1},
      "b": {"nominal": 4.0, "uncertainty": 0.2}
    }
  }'

Expected: 200 OK, result ≈ 10.0 ± 0.566, invariant_passed = true
```

**TC-OPS-003**: Division (Valid)
```bash
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "divide",
    "inputs": {
      "a": {"nominal": 10.0, "uncertainty": 0.5},
      "b": {"nominal": 2.0, "uncertainty": 0.1}
    }
  }'

Expected: 200 OK, result ≈ 5.0 ± uncertainty, invariant_passed = true
```

**TC-OPS-004**: Division by Zero (Invalid)
```bash
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "divide",
    "inputs": {
      "a": {"nominal": 10.0, "uncertainty": 0.5},
      "b": {"nominal": 0.0, "uncertainty": 0.0}
    }
  }'

Expected: 400 Bad Request or 422 Unprocessable Entity
```

**TC-OPS-005**: Square Root
```bash
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "sqrt",
    "inputs": {
      "x": {"nominal": 16.0, "uncertainty": 0.5}
    }
  }'

Expected: 200 OK, result = 4.0 ± uncertainty, invariant_passed = true
```

**Pass Criteria**: 4/5 valid operations succeed, 1 invalid operation rejected (5/5 total)

---

#### Test 4.4: Batch Operations

**Test Cases**:

**TC-BATCH-001**: Multiple Operations (Atomic)
```bash
curl -X POST http://localhost:8080/operations/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
      }
    ]
  }'

Expected: 200 OK, 2 results, all invariants passed
```

**TC-BATCH-002**: Batch with Failure (Rollback)
```bash
curl -X POST http://localhost:8080/operations/batch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [
      {
        "operation": "add",
        "inputs": {"a": {"nominal": 1.0, "uncertainty": 0.1}, "b": {"nominal": 2.0, "uncertainty": 0.1}}
      },
      {
        "operation": "divide",
        "inputs": {"a": {"nominal": 10.0, "uncertainty": 0.5}, "b": {"nominal": 0.0, "uncertainty": 0.0}}
      }
    ]
  }'

Expected: 400/422, NO operations committed (atomic rollback)
```

**Pass Criteria**: Batch operations work atomically (2/2)

---

#### Test 4.5: Ledger Queries

**Test Cases**:

**TC-LEDGER-001**: Query All Operations
```bash
curl http://localhost:8080/ledger/query?limit=100 \
  -H "Authorization: Bearer $TOKEN"

Expected: 200 OK, list of operations with pagination info
```

**TC-LEDGER-002**: Query by Operation Type
```bash
curl "http://localhost:8080/ledger/query?operation=multiply&limit=10" \
  -H "Authorization: Bearer $TOKEN"

Expected: 200 OK, only multiply operations returned
```

**TC-LEDGER-003**: Query by Time Range
```bash
START_TIME=$(date -d '1 hour ago' +%s)
END_TIME=$(date +%s)

curl "http://localhost:8080/ledger/query?start_time=$START_TIME&end_time=$END_TIME" \
  -H "Authorization: Bearer $TOKEN"

Expected: 200 OK, operations within time range
```

**TC-LEDGER-004**: Verify Operation Signature
```bash
# Get an operation ID from previous query
OP_ID="<op_id_from_query>"

curl "http://localhost:8080/ledger/verify/$OP_ID" \
  -H "Authorization: Bearer $TOKEN"

Expected: 200 OK, signature_valid = true
```

**Pass Criteria**: All ledger queries work (4/4)

---

### Category 5: Database Testing (30 minutes)

**Objective**: Verify PostgreSQL persistence and integrity

#### Test 5.1: Database Connection

```bash
# Test connection to DigitalOcean PostgreSQL
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios_staging -c "SELECT version();"

Expected: PostgreSQL 17.6 version string
```

---

#### Test 5.2: Schema Creation

```bash
# Verify ledger table exists
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios_staging -c "\d ledger"

Expected: Table structure with columns: timestamp, op_id, parent_id, operation, inputs, output, coverage, invariant_passed, signature
```

---

#### Test 5.3: Data Persistence

```bash
# Execute operation via API
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"operation":"add","inputs":{"a":{"nominal":1.0,"uncertainty":0.1},"b":{"nominal":2.0,"uncertainty":0.1}}}'

# Query database directly
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios_staging -c "SELECT op_id, operation FROM ledger ORDER BY timestamp DESC LIMIT 1;"

Expected: Operation visible in database
```

---

#### Test 5.4: Data Integrity

```bash
# Count operations via API
API_COUNT=$(curl -s http://localhost:8080/ledger/query?limit=1 -H "Authorization: Bearer $TOKEN" | jq '.total')

# Count operations in database
DB_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios_staging -t -c "SELECT COUNT(*) FROM ledger;")

Expected: API_COUNT == DB_COUNT (no data loss)
```

**Pass Criteria**: All database tests pass (4/4)

---

### Category 6: Load Testing (45 minutes)

**Objective**: Verify performance and rate limiting under load

#### Test 6.1: Rate Limit Enforcement

```bash
# Send 101 requests rapidly
for i in {1..101}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/ >> rate_test.log
done

# Count 200s and 429s
SUCCESSFUL=$(grep -c "200" rate_test.log)
RATE_LIMITED=$(grep -c "429" rate_test.log)

Expected: SUCCESSFUL = 100, RATE_LIMITED = 1 (or more if very fast)
```

---

#### Test 6.2: Concurrent Requests (Sustained Load)

**Tool**: Apache Bench (ab)
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -p operation_payload.json \
  http://localhost:8080/operations/execute
```

**Pass Criteria**:
- 100% success rate (within rate limit)
- Mean response time: < 100ms
- P95 response time: < 200ms
- P99 response time: < 500ms

---

#### Test 6.3: Stress Test (Find Breaking Point)

**Tool**: wrk (if available) or custom Python script
```bash
# 1000 requests over 60 seconds
wrk -t4 -c50 -d60s --latency \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/
```

**Expected Behavior**:
- Rate limiting kicks in (429 responses)
- Server remains stable (no crashes)
- Memory usage stays < 2GB
- CPU usage reasonable (< 80%)

**Pass Criteria**: Server stable under stress, rate limiting works

---

### Category 7: API Compliance Testing (30 minutes)

**Objective**: Verify API contract compliance

#### Test 7.1: OpenAPI Schema Validation

```bash
# Generate OpenAPI schema (if available)
curl http://localhost:8080/openapi.json > openapi_schema.json

# Validate responses match schema
# (Manual or automated with openapi-spec-validator)
```

---

#### Test 7.2: Error Response Format

```bash
# Trigger various errors and verify format
curl -X POST http://localhost:8080/auth/login -d '{"username":"invalid"}' # 401
curl http://localhost:8080/operations/execute # 401 (no auth)
curl -X POST http://localhost:8080/operations/execute -H "Authorization: Bearer invalid" # 401

Expected: All errors return JSON with "error" or "detail" field
```

---

#### Test 7.3: HTTP Method Compliance

```bash
# Verify correct methods
curl -X GET http://localhost:8080/auth/login  # Should fail (405 Method Not Allowed)
curl -X POST http://localhost:8080/ledger/query  # Should fail (405)

Expected: 405 Method Not Allowed for wrong methods
```

**Pass Criteria**: API follows REST conventions (3/3)

---

## Test Execution Schedule

**Total Estimated Time**: 4-5 hours

### Phase 1: Static Analysis (09:00 - 09:45)
- Bandit security scan
- Pylint code quality
- Mypy type checking
- Dependency scanning

### Phase 2: Container Security (09:45 - 10:15)
- Docker image build
- Trivy vulnerability scan
- Docker Bench security audit

### Phase 3: Environment Setup (10:15 - 10:45)
- Create staging database
- Deploy Docker Compose stack
- Verify services running
- Health check

### Phase 4: Integration Testing (10:45 - 12:00)
- Authentication flow (15 min)
- RBAC authorization (15 min)
- Operations execution (30 min)
- Batch operations (15 min)
- Ledger queries (15 min)

### Phase 5: Database Testing (12:00 - 12:30)
- Connection verification
- Schema validation
- Persistence testing
- Integrity checks

### Phase 6: Load Testing (12:30 - 13:15)
- Rate limit enforcement
- Concurrent requests
- Stress testing

### Phase 7: API Compliance (13:15 - 13:45)
- Schema validation
- Error format verification
- HTTP method compliance

### Phase 8: Report Generation (13:45 - 14:00)
- Aggregate results
- Generate test report
- Document failures
- Create recommendations

---

## Success Criteria

### Critical (Must Pass)
- ✅ Zero CRITICAL security vulnerabilities
- ✅ Authentication flow works (5/5 tests)
- ✅ RBAC correctly enforced (4/4 tests)
- ✅ Operations execute correctly (4/5 tests, 1 expected failure)
- ✅ Database persistence works (4/4 tests)
- ✅ Rate limiting enforced

### High Priority (Should Pass)
- ✅ < 5 HIGH security vulnerabilities
- ✅ Batch operations atomic (2/2 tests)
- ✅ Ledger queries work (4/4 tests)
- ✅ Load test P95 < 200ms
- ✅ API compliance (3/3 tests)

### Medium Priority (Nice to Have)
- ✅ Code quality score ≥ 8.0
- ✅ Type checking passes
- ✅ Load test P99 < 500ms
- ✅ Docker Bench < 5 warnings

---

## Test Environment Variables

```bash
# Server
export STAGING_HOST="tot.allyourbaseline.com"
export STAGING_PORT="8080"
export API_BASE_URL="http://$STAGING_HOST:$STAGING_PORT"

# Database
export DB_HOST="db-postgresql-nyc3-12345-do-user-67890-0.b.db.ondigitalocean.com"
export DB_PORT="25060"
export DB_NAME="ebios_staging"
export DB_USER="doadmin"
export DB_PASSWORD="<from secure storage>"

# JWT
export JWT_SECRET_KEY="$(openssl rand -hex 32)"

# Test credentials
export TEST_ADMIN_USER="admin"
export TEST_ADMIN_PASS="admin123"
export TEST_OPERATOR_USER="operator"
export TEST_OPERATOR_PASS="operator123"
```

---

## Test Artifacts

All test results stored in `/got/ebios/reports/`:

```
reports/
├── bandit_report.json
├── pylint_report.json
├── mypy_report/
├── safety_report.json
├── pip_audit_report.json
├── trivy_report.json
├── docker_bench_results.txt
├── integration_test_results.json
├── load_test_results.txt
├── db_test_results.txt
├── api_compliance_results.json
└── TEST_EXECUTION_REPORT.md  (final report)
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database connection fails | Medium | High | Use test database, verify credentials before starting |
| Rate limit too aggressive | Low | Medium | Adjust limits in .env if needed |
| Security vulnerabilities found | High | Medium | Document, create tickets, don't block release for LOW/MEDIUM |
| Performance below targets | Medium | Medium | Profile, optimize critical paths |
| Docker build fails | Low | High | Test build before full test run |

---

## Post-Test Actions

### If All Tests Pass (Green)
1. Generate success report
2. Tag Docker image: `ebios:1.0.0-rc1`
3. Deploy to production staging
4. Schedule production release

### If Critical Tests Fail (Red)
1. Document failures in detail
2. Create GitHub issues with priority
3. Do not proceed to production
4. Fix critical issues and re-test

### If High Priority Tests Fail (Yellow)
1. Assess impact on production readiness
2. Create mitigation plan
3. Document known issues
4. Proceed with caution or delay release

---

**Test Plan Author**: Claude Code (Autonomous)
**Review Required**: Yes (human approval before production)
**Version Control**: This document is the SSOT for v1.0.0 testing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
