# Next Steps: eBIOS v1.0.0 Roadmap

**Current Version**: v0.3.0 (Production Ready)  
**Target Version**: v1.0.0  
**Target Date**: January 2026  
**Status**: Planning Phase

---

## Current Status Summary

✅ **v0.3.0 Complete** (2025-10-29):
- 100% formal verification (0 sorry statements)
- PostgreSQL backend deployed
- Rate limiting active (100 req/min)
- Live API: http://got.gitgap.org:8080
- 194/194 tests passing

---

## Phase 1: Security Hardening (4-6 weeks)

### 1.1 JWT Authentication
**Priority**: HIGH  
**Effort**: 2 weeks

**Tasks**:
- [ ] Install PyJWT library
- [ ] Create JWT token generation endpoint
- [ ] Implement token validation middleware
- [ ] Add refresh token mechanism
- [ ] Update API endpoints to require authentication
- [ ] Write authentication tests

**Implementation**:
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

**Deliverables**:
- `/auth/login` endpoint
- `/auth/refresh` endpoint  
- JWT middleware for all protected routes
- Documentation updates

---

### 1.2 RBAC (Role-Based Access Control)
**Priority**: HIGH  
**Effort**: 2 weeks

**Roles**:
- `admin`: Full access (all operations)
- `operator`: Execute operations, query ledger
- `auditor`: Read-only access (query, verify)
- `guest`: Health check only

**Implementation**:
```python
from functools import wraps

def require_role(role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if user.role not in get_allowed_roles(role):
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.post("/operations/execute")
@require_role("operator")
async def execute_operation(request: OperationRequest):
    ...
```

**Database Schema**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_username ON users(username);
```

**Deliverables**:
- User management endpoints
- Role-based authorization middleware
- Migration script for user table
- Admin CLI for user management

---

### 1.3 Mandatory Policy Signing
**Priority**: MEDIUM  
**Effort**: 1 week

**Current State**: Policies can be unsigned  
**Target State**: All policies must be signed with Ed25519

**Implementation**:
```python
def validate_policy_signature(policy: Policy) -> bool:
    if not policy.signature:
        raise ValueError("Policy must be signed")
    
    # Verify Ed25519 signature
    public_key = get_policy_public_key()
    message = policy.to_canonical_bytes()
    return verify_signature(public_key, message, policy.signature)
```

**Deliverables**:
- Policy signing CLI tool
- Signature validation in policy loader
- Key management documentation
- Updated policy examples

---

## Phase 2: Infrastructure (3-4 weeks)

### 2.1 Docker Containerization
**Priority**: HIGH  
**Effort**: 1 week

**Files to Create**:

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY tests/ ./tests/

# Run as non-root
RUN useradd -m ebios
USER ebios

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "src.nugovern.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  ebios:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:17
    environment:
      - POSTGRES_DB=ebios
      - POSTGRES_USER=ebios
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Deliverables**:
- Multi-stage Dockerfile
- docker-compose.yml for local development
- Kubernetes manifests (deployment, service, configmap)
- CI/CD pipeline for container builds

---

### 2.2 HTTPS with Reverse Proxy
**Priority**: HIGH  
**Effort**: 1 week

**Option 1: Nginx Reverse Proxy**

`nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name api.ebios.org;

    ssl_certificate /etc/letsencrypt/live/api.ebios.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.ebios.org/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.ebios.org;
    return 301 https://$server_name$request_uri;
}
```

**Option 2: Traefik (Docker-native)**

`docker-compose.yml` (updated):
```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - letsencrypt:/letsencrypt

  ebios:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ebios.rule=Host(`api.ebios.org`)"
      - "traefik.http.routers.ebios.entrypoints=websecure"
      - "traefik.http.routers.ebios.tls.certresolver=letsencrypt"
```

**Deliverables**:
- Nginx configuration (Option 1)
- Traefik labels (Option 2)
- Let's Encrypt auto-renewal
- HTTPS redirect configuration

---

### 2.3 Automated Database Backups
**Priority**: MEDIUM  
**Effort**: 3 days

**Backup Script**:
```bash
#!/bin/bash
# /usr/local/bin/ebios-backup.sh

BACKUP_DIR="/var/backups/ebios"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ebios_$DATE.sql.gz"

# Create backup
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"

# Upload to S3/DigitalOcean Spaces
aws s3 cp "$BACKUP_FILE" s3://ebios-backups/$(basename $BACKUP_FILE)

# Clean up old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Cron Schedule**:
```cron
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/ebios-backup.sh

# Hourly backup during business hours
0 9-17 * * 1-5 /usr/local/bin/ebios-backup.sh
```

**Deliverables**:
- Automated backup script
- S3/Spaces upload integration
- Restore procedure documentation
- Backup monitoring alerts

---

## Phase 3: Monitoring & Observability (2-3 weeks)

### 3.1 Prometheus + Grafana
**Priority**: MEDIUM  
**Effort**: 1.5 weeks

**Metrics to Track**:
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query time
- Rate limit hits
- Active connections
- Memory/CPU usage

**Implementation**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
request_count = Counter('ebios_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('ebios_request_duration_seconds', 'Request duration')
active_connections = Gauge('ebios_active_connections', 'Active connections')

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.observe(duration)
    return response
```

**Grafana Dashboards**:
1. API Performance (latency, throughput)
2. System Resources (CPU, memory, disk)
3. Database Metrics (connections, query time)
4. Security Events (rate limits, auth failures)

**Deliverables**:
- Prometheus exporter in API
- Grafana dashboard JSONs
- Alert rules (high latency, errors, etc.)
- Runbook for common issues

---

### 3.2 Centralized Logging
**Priority**: LOW  
**Effort**: 3 days

**Options**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Cloud provider (CloudWatch, Stackdriver)

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

@app.post("/operations/execute")
async def execute_operation(request: OperationRequest):
    logger.info("operation_started", 
                operation=request.operation,
                input_count=len(request.inputs))
    
    result = server.execute_operation(request)
    
    logger.info("operation_completed",
                operation=request.operation,
                result=result.result,
                ledger_id=result.ledger_id)
    
    return result
```

**Deliverables**:
- Structured logging configuration
- Log aggregation setup
- Log retention policies
- Search/query documentation

---

## Phase 4: Production Hardening (3-4 weeks)

### 4.1 Security Audit
**Priority**: CRITICAL  
**Effort**: 2 weeks (external)

**Scope**:
- API security (injection, XSS, CSRF)
- Authentication/authorization
- Database security
- Cryptographic implementations
- Infrastructure configuration
- Dependency vulnerabilities

**Tools**:
- OWASP ZAP (automated scanning)
- Burp Suite (manual testing)
- Safety (Python dependency check)
- Bandit (static analysis)

**Deliverables**:
- Security audit report
- Vulnerability remediation plan
- Security best practices document
- Penetration testing results

---

### 4.2 Load Testing
**Priority**: HIGH  
**Effort**: 1 week

**Target**: 1000+ requests/second

**Tools**:
- Locust (Python-based)
- k6 (JavaScript-based)
- Apache JMeter

**Test Scenarios**:
```python
from locust import HttpUser, task, between

class eBIOSUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/")
    
    @task(2)
    def execute_add(self):
        self.client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[5.0, 0.1], [3.0, 0.2]]
        })
    
    @task(1)
    def query_ledger(self):
        self.client.get("/ledger/entries")
```

**Run**:
```bash
locust -f loadtest.py --host http://got.gitgap.org:8080 --users 1000 --spawn-rate 10
```

**Metrics to Measure**:
- Maximum sustained throughput
- Response time at load
- Error rate under stress
- Resource utilization
- Database connection pool exhaustion

**Deliverables**:
- Load test scripts
- Performance benchmark report
- Bottleneck analysis
- Optimization recommendations

---

### 4.3 Disaster Recovery
**Priority**: MEDIUM  
**Effort**: 1 week

**Components**:
1. **Backup Strategy**
   - RPO (Recovery Point Objective): 1 hour
   - RTO (Recovery Time Objective): 4 hours

2. **Restore Procedures**
   ```bash
   # Restore from backup
   gunzip < ebios_20251029_020000.sql.gz | psql $DATABASE_URL
   
   # Verify integrity
   curl http://got.gitgap.org:8080/ledger/verify
   ```

3. **High Availability**
   - Database replication (primary + replica)
   - Multi-region deployment (optional)
   - Health checks + auto-restart

4. **Incident Response Plan**
   - Alert escalation procedures
   - On-call rotation
   - Runbooks for common issues

**Deliverables**:
- DR playbook
- Restore verification tests
- HA configuration (if applicable)
- Incident response documentation

---

## Phase 5: Release Preparation (2 weeks)

### 5.1 Production-Ready Defaults
**Priority**: HIGH  
**Effort**: 1 week

**Configuration**:
```python
# config/production.py
PRODUCTION_CONFIG = {
    "database": {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
    },
    "api": {
        "rate_limit": "100/minute",
        "cors_origins": ["https://app.ebios.org"],
        "request_timeout": 30,
    },
    "security": {
        "jwt_expiry": 3600,  # 1 hour
        "require_https": True,
        "password_min_length": 12,
    },
    "monitoring": {
        "prometheus_enabled": True,
        "log_level": "INFO",
    }
}
```

**Environment Variables**:
```bash
# .env.production
NODE_ENV=production
DB_POOL_SIZE=20
RATE_LIMIT=100/minute
JWT_EXPIRY=3600
LOG_LEVEL=INFO
```

**Deliverables**:
- Production configuration file
- Environment variable documentation
- Configuration validation script
- Migration guide from v0.3.0

---

### 5.2 Enterprise Documentation
**Priority**: HIGH  
**Effort**: 1 week

**Documents to Create**:
1. **Deployment Guide** (50 pages)
   - Prerequisites
   - Step-by-step installation
   - Configuration options
   - Troubleshooting

2. **API Reference** (100 pages)
   - All endpoints documented
   - Authentication examples
   - Error codes
   - Rate limits

3. **Security Guide** (30 pages)
   - Threat model
   - Best practices
   - Compliance mappings
   - Audit procedures

4. **Operations Manual** (40 pages)
   - Monitoring dashboards
   - Backup/restore procedures
   - Incident response
   - Capacity planning

**Deliverables**:
- Complete documentation set
- PDF/HTML versions
- Example configurations
- Quick start guides

---

### 5.3 Certification Artifacts
**Priority**: MEDIUM  
**Effort**: 1 week

**For ISO 26262 / DO-178C / IEC 61508**:

1. **Formal Verification Package**
   - All Lean 4 proofs (✅ already complete)
   - Theorem statements
   - Proof dependencies
   - Verification report

2. **Test Coverage Report**
   - Unit test results (194/194)
   - Integration test results
   - Code coverage metrics
   - Traceability matrix

3. **Audit Trail**
   - Git commit history
   - Code review records
   - Security audit results
   - Penetration test results

4. **Safety Analysis**
   - Hazard analysis
   - Risk assessment
   - Mitigation strategies
   - Safety requirements

**Deliverables**:
- Certification package (ZIP)
- Requirements traceability matrix
- Safety case documentation
- Compliance checklist

---

## Timeline

### November 2025
- Week 1-2: JWT + RBAC
- Week 3-4: Policy signing + Docker

### December 2025
- Week 1: HTTPS + Backups
- Week 2-3: Prometheus/Grafana + Logging
- Week 4: Holiday break

### January 2026
- Week 1: Security audit
- Week 2: Load testing + DR
- Week 3: Production defaults + Docs
- Week 4: **v1.0.0 Release** 🎉

---

## Success Criteria for v1.0.0

- [ ] JWT authentication working
- [ ] RBAC with 4 roles (admin, operator, auditor, guest)
- [ ] All policies signed (mandatory)
- [ ] Docker image published
- [ ] HTTPS enabled
- [ ] Automated backups (daily)
- [ ] Prometheus metrics exported
- [ ] Security audit complete (0 critical issues)
- [ ] Load tested (1000+ req/sec)
- [ ] Complete documentation set
- [ ] Certification artifacts prepared

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Security vulnerabilities found | Medium | High | External audit, automated scanning |
| Performance doesn't meet target | Low | Medium | Load testing early, optimization |
| Breaking changes for users | Medium | Medium | Migration guide, deprecation notices |
| Timeline slips | Medium | Low | Phased approach, MVP first |

---

## Budget Estimate

**External Services**:
- Security audit: $5,000 - $10,000
- SSL certificates: $0 (Let's Encrypt)
- Cloud infrastructure: $200/month (current)

**Time Investment**:
- Development: 10-12 weeks
- Testing: 3-4 weeks
- Documentation: 2-3 weeks
- **Total**: ~4 months

---

## Questions to Address

1. **Authentication**: Use external provider (Auth0, Keycloak) or build in-house?
2. **Deployment**: Kubernetes or simpler (Docker Compose, systemd)?
3. **Monitoring**: Self-hosted (Prometheus/Grafana) or cloud (Datadog, New Relic)?
4. **Database**: Stay with DigitalOcean Managed or self-hosted PostgreSQL?
5. **Domains**: What domain for API? (api.ebios.org, ebios-api.allyourbaseline.com)

---

## Getting Started

**Next Immediate Steps**:
1. Review this roadmap with stakeholders
2. Prioritize features (MVP vs nice-to-have)
3. Set up development branch for v1.0.0
4. Begin Phase 1.1 (JWT authentication)

**To Begin Development**:
```bash
# Create v1.0.0 branch
git checkout -b v1.0.0-dev

# Install additional dependencies
pip install pyjwt python-jose[cryptography]

# Set up test database for development
docker-compose up -d postgres
```

---

**Status**: Ready to begin v1.0.0 development  
**Target**: January 2026  
**Philosophy**: Production-ready, security-first, formally verified

🚀 Let's build v1.0.0!
