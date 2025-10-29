# eBIOS v1.0.0 Deployment Guide

**Version**: 1.0.0
**Target Environments**: Production, Staging, Development
**Last Updated**: 2025-10-29

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Option 1: Docker Compose (Recommended)](#option-1-docker-compose-recommended)
5. [Option 2: Systemd Service](#option-2-systemd-service)
6. [Option 3: Kubernetes](#option-3-kubernetes)
7. [Database Setup](#database-setup)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Environment Variables](#environment-variables)
10. [Health Checks](#health-checks)
11. [Monitoring Setup](#monitoring-setup)
12. [Backup Configuration](#backup-configuration)
13. [Troubleshooting](#troubleshooting)
14. [Security Hardening](#security-hardening)
15. [Migration from v0.3.0](#migration-from-v030)

---

## Overview

eBIOS v1.0.0 introduces significant infrastructure improvements:

✅ JWT authentication
✅ RBAC (4 roles)
✅ Docker containerization
✅ PostgreSQL clustering support
✅ Automated backups
✅ Prometheus monitoring

This guide covers production-ready deployment strategies for all environments.

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- OS: Linux (Ubuntu 22.04+, RHEL 9+, or equivalent)

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 100 GB SSD
- OS: Linux with kernel 5.10+

### Software Dependencies

| Software | Minimum Version | Purpose |
|----------|----------------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| PostgreSQL | 17.0+ | Database (can be managed) |
| Nginx | 1.24+ | Reverse proxy (optional) |
| Python | 3.12+ | For non-Docker deployments |
| Git | 2.40+ | Source code management |

### Network Requirements

- **Inbound Ports**:
  - 443 (HTTPS) - Public API access
  - 8080 (HTTP) - Internal API (behind reverse proxy)
  - 5432 (PostgreSQL) - Database (private network only)
  - 9090 (Prometheus) - Metrics (internal only)

- **Outbound Access**:
  - GitHub (443) - Source code
  - Docker Hub (443) - Container images
  - PyPI (443) - Python packages
  - S3/Spaces (443) - Backup storage (optional)

---

## Deployment Options

### Quick Comparison

| Feature | Docker Compose | Systemd | Kubernetes |
|---------|---------------|---------|------------|
| Ease of Setup | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Scalability | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Monitoring | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Complexity | Low | Medium | High |
| Recommended For | Small-Medium | Legacy systems | Enterprise |

---

## Option 1: Docker Compose (Recommended)

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/abba-01/ebios.git
cd ebios

# Checkout v1.0.0
git checkout v1.0.0
```

### Step 2: Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit configuration
vim .env
```

**Required Variables** (`.env`):
```bash
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=ebios
POSTGRES_USER=ebios
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>
DATABASE_URL=postgresql://ebios:<PASSWORD>@postgres:5432/ebios

# Security (CRITICAL - Change these!)
JWT_SECRET_KEY=<GENERATE_WITH: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Rate Limiting
RATE_LIMIT=100/minute

# Monitoring
PROMETHEUS_ENABLED=true

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

**Generate Secure Secrets:**
```bash
# JWT secret key (64 characters)
openssl rand -hex 32

# PostgreSQL password (32 characters)
openssl rand -base64 24
```

### Step 3: Build and Deploy

```bash
# Build Docker image
docker-compose build

# Start services (without monitoring)
docker-compose up -d

# OR: Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ebios
```

### Step 4: Verify Deployment

```bash
# Health check
curl http://localhost:8080/

# Expected response:
# {"status":"healthy","version":"1.0.0","service":"eBIOS"}

# Test authentication
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Should return JWT tokens
```

### Step 5: Configure Nginx Reverse Proxy

```bash
# Copy Nginx configuration
sudo cp nginx/ebios.conf /etc/nginx/sites-available/ebios
sudo ln -s /etc/nginx/sites-available/ebios /etc/nginx/sites-enabled/

# Edit domain name
sudo vim /etc/nginx/sites-available/ebios
# Change: server_name api.ebios.org; → your domain

# Get SSL certificate (Let's Encrypt)
sudo certbot certonly --nginx -d api.your-domain.com

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 6: Create Admin User

⚠️ **Security Critical**: Change default credentials immediately!

```bash
# Connect to container
docker-compose exec ebios bash

# Run user management CLI (when implemented)
python -m nugovern.users create \
  --username your_admin \
  --password <STRONG_PASSWORD> \
  --role admin

# Exit container
exit
```

**Until user management CLI is ready**, manually change passwords in `src/nugovern/auth.py` and rebuild:

```python
# In src/nugovern/auth.py, replace USERS dictionary with:
USERS = {
    "your_admin": User(
        username="your_admin",
        hashed_password=pwd_context.hash("YOUR_STRONG_PASSWORD"),
        role=Role.ADMIN
    )
}
```

Then rebuild:
```bash
docker-compose build ebios
docker-compose up -d ebios
```

---

## Option 2: Systemd Service

⚠️ **CRITICAL SECURITY REQUIREMENT**: Must use Python virtual environment

**Supported**: ✅ Systemd with venv
**NOT Supported**: ❌ Bare metal with system Python (vulnerable RPM packages)

**Why**: System Python packages (setuptools 69.0.3, urllib3 1.26.19) have unpatched HIGH severity vulnerabilities (CVE-2025-47273, CVE-2025-50181). Virtual environments properly isolate and use secure versions.

For deployment on existing infrastructure without Docker.

### Step 1: Prepare Environment

```bash
# Install Python 3.12+
sudo dnf install python3.12 python3.12-pip

# Create application directory
sudo mkdir -p /opt/ebios
sudo chown $USER:$USER /opt/ebios

# Clone repository
cd /opt/ebios
git clone https://github.com/abba-01/ebios.git .
git checkout v1.0.0

# ⚠️ CRITICAL: Create virtual environment (REQUIRED for security)
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies (will use secure versions, NOT vulnerable RPM packages)
pip install --upgrade pip
pip install -r requirements.txt

# Verify security fixes applied
pip list | grep -E '(cryptography|starlette|setuptools|urllib3)'
# Expected: cryptography 46.0.3+, starlette 0.49.1+, setuptools 80.9.0+
```

### Step 2: Configure Environment

```bash
# Create environment file
cat > /opt/ebios/.env << 'EOF'
POSTGRES_HOST=db-postgresql-nyc3-12345-do-user-67890-0.b.db.ondigitalocean.com
POSTGRES_PORT=25060
POSTGRES_DB=ebios
POSTGRES_USER=doadmin
POSTGRES_PASSWORD=<YOUR_DB_PASSWORD>
DATABASE_URL=postgresql://doadmin:<PASSWORD>@<HOST>:25060/ebios?sslmode=require

JWT_SECRET_KEY=<GENERATE_WITH_OPENSSL>
JWT_ALGORITHM=HS256
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Secure permissions
chmod 600 /opt/ebios/.env
```

### Step 3: Create Systemd Service

```bash
sudo vim /etc/systemd/system/ebios.service
```

**Service Configuration:**
```ini
[Unit]
Description=eBIOS API Server v1.0.0
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ebios
Group=ebios
WorkingDirectory=/opt/ebios
Environment="PATH=/opt/ebios/venv/bin"
EnvironmentFile=/opt/ebios/.env

# ⚠️ CRITICAL: Must use venv Python (NOT /usr/bin/python3)
# This ensures security fixes are applied (setuptools 80.9.0+, urllib3 2.5.0+)
ExecStart=/opt/ebios/venv/bin/python -m uvicorn \
    src.nugovern.server_v1:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4 \
    --log-level info

# Restart policy
Restart=always
RestartSec=10
StartLimitBurst=3
StartLimitInterval=60

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/ebios/logs

# Resource limits
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

### Step 4: Create Service User

```bash
# Create dedicated user
sudo useradd -r -s /bin/false ebios
sudo chown -R ebios:ebios /opt/ebios

# Create log directory
sudo mkdir -p /opt/ebios/logs
sudo chown ebios:ebios /opt/ebios/logs
```

### Step 5: Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable ebios

# Start service
sudo systemctl start ebios

# Check status
sudo systemctl status ebios

# View logs
sudo journalctl -u ebios -f
```

---

## Option 3: Kubernetes

For enterprise deployments with high availability requirements.

### Step 1: Create Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ebios
  labels:
    name: ebios
    environment: production
```

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 2: Create Secrets

```bash
# Create database secret
kubectl create secret generic ebios-db \
  --namespace=ebios \
  --from-literal=host=<DB_HOST> \
  --from-literal=port=25060 \
  --from-literal=database=ebios \
  --from-literal=user=doadmin \
  --from-literal=password=<DB_PASSWORD>

# Create JWT secret
kubectl create secret generic ebios-jwt \
  --namespace=ebios \
  --from-literal=secret-key=$(openssl rand -hex 32)

# Verify secrets
kubectl get secrets -n ebios
```

### Step 3: Create ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ebios-config
  namespace: ebios
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  JWT_ALGORITHM: "HS256"
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "60"
  JWT_REFRESH_TOKEN_EXPIRE_DAYS: "30"
  RATE_LIMIT: "100/minute"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 4: Create Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ebios
  namespace: ebios
  labels:
    app: ebios
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ebios
  template:
    metadata:
      labels:
        app: ebios
        version: v1.0.0
    spec:
      containers:
      - name: ebios
        image: ghcr.io/abba-01/ebios:1.0.0
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: ebios-db
              key: host
        - name: POSTGRES_PORT
          valueFrom:
            secretKeyRef:
              name: ebios-db
              key: port
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: ebios-db
              key: database
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: ebios-db
              key: user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ebios-db
              key: password
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ebios-jwt
              key: secret-key
        envFrom:
        - configMapRef:
            name: ebios-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
      restartPolicy: Always
```

```bash
kubectl apply -f k8s/deployment.yaml
```

### Step 5: Create Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ebios
  namespace: ebios
  labels:
    app: ebios
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: ebios
```

```bash
kubectl apply -f k8s/service.yaml
```

### Step 6: Create Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ebios
  namespace: ebios
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.ebios.org
    secretName: ebios-tls
  rules:
  - host: api.ebios.org
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ebios
            port:
              number: 80
```

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 7: Verify Deployment

```bash
# Check pods
kubectl get pods -n ebios

# Check service
kubectl get svc -n ebios

# Check ingress
kubectl get ingress -n ebios

# View logs
kubectl logs -n ebios -l app=ebios --tail=100 -f

# Test health check
kubectl exec -n ebios -it deployment/ebios -- curl http://localhost:8080/
```

---

## Database Setup

### DigitalOcean Managed PostgreSQL (Recommended)

1. **Create Database Cluster**:
   - Go to DigitalOcean Control Panel
   - Databases → Create Database
   - Choose: PostgreSQL 17
   - Plan: Basic ($15/mo) or Professional ($60/mo)
   - Region: Same as API server
   - Enable: Private Network, Automated Backups

2. **Create Database**:
   ```sql
   CREATE DATABASE ebios;
   ```

3. **Connection String**:
   ```
   postgresql://doadmin:PASSWORD@HOST:25060/ebios?sslmode=require
   ```

4. **Firewall Rules**:
   - Add your server's IP to trusted sources
   - OR: Use VPC private network (recommended)

### Self-Hosted PostgreSQL

```bash
# Install PostgreSQL 17
sudo dnf install postgresql17-server

# Initialize database
sudo postgresql-setup --initdb

# Start service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql << 'EOF'
CREATE USER ebios WITH PASSWORD '<STRONG_PASSWORD>';
CREATE DATABASE ebios OWNER ebios;
GRANT ALL PRIVILEGES ON DATABASE ebios TO ebios;
\q
EOF

# Configure pg_hba.conf
sudo vim /var/lib/pgsql/data/pg_hba.conf
# Add: host    ebios    ebios    10.0.0.0/8    scram-sha-256

# Reload configuration
sudo systemctl reload postgresql
```

### Database Schema

Schema is automatically created on first startup by `PostgreSQLBackend._create_schema()`:

```sql
CREATE TABLE IF NOT EXISTS ledger (
    timestamp BIGINT NOT NULL,
    op_id TEXT PRIMARY KEY,
    parent_id TEXT,
    operation TEXT NOT NULL,
    inputs JSONB NOT NULL,
    output JSONB NOT NULL,
    coverage DOUBLE PRECISION NOT NULL,
    invariant_passed BOOLEAN NOT NULL,
    signature TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_timestamp ON ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_operation ON ledger(operation);
CREATE INDEX IF NOT EXISTS idx_parent_id ON ledger(parent_id);
```

---

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo dnf install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d api.your-domain.com

# Certificate files:
# - Certificate: /etc/letsencrypt/live/api.your-domain.com/fullchain.pem
# - Private Key: /etc/letsencrypt/live/api.your-domain.com/privkey.pem

# Auto-renewal (certbot installs timer automatically)
sudo systemctl status certbot-renew.timer

# Test renewal
sudo certbot renew --dry-run
```

### Custom SSL Certificate

```bash
# Copy certificate files
sudo mkdir -p /etc/ssl/ebios
sudo cp fullchain.pem /etc/ssl/ebios/
sudo cp privkey.pem /etc/ssl/ebios/
sudo chmod 600 /etc/ssl/ebios/privkey.pem

# Update Nginx configuration
sudo vim /etc/nginx/sites-available/ebios

# Change certificate paths:
ssl_certificate /etc/ssl/ebios/fullchain.pem;
ssl_certificate_key /etc/ssl/ebios/privkey.pem;

# Reload Nginx
sudo systemctl reload nginx
```

### SSL Security Testing

```bash
# Test SSL configuration
openssl s_client -connect api.your-domain.com:443 -servername api.your-domain.com

# Check certificate expiry
openssl x509 -in /etc/letsencrypt/live/api.your-domain.com/fullchain.pem -noout -dates

# SSL Labs test
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.your-domain.com
```

---

## Environment Variables

### Complete Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_HOST` | Yes | - | PostgreSQL hostname |
| `POSTGRES_PORT` | Yes | - | PostgreSQL port (usually 25060 for DO) |
| `POSTGRES_DB` | Yes | - | Database name |
| `POSTGRES_USER` | Yes | - | Database user |
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `DATABASE_URL` | Yes | - | Full PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | - | JWT signing key (64+ chars) |
| `JWT_ALGORITHM` | No | HS256 | JWT algorithm (HS256 recommended) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | 60 | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | 30 | Refresh token lifetime |
| `RATE_LIMIT` | No | 100/minute | Rate limit (requests/window) |
| `ENVIRONMENT` | No | production | Environment name |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `PROMETHEUS_ENABLED` | No | true | Enable Prometheus metrics |
| `BACKUP_DIR` | No | /var/backups/ebios | Backup directory |
| `BACKUP_RETENTION_DAYS` | No | 30 | Backup retention period |
| `S3_BUCKET` | No | - | S3 bucket for backups (optional) |
| `S3_ENDPOINT` | No | - | S3 endpoint (for DigitalOcean Spaces) |

---

## Health Checks

### HTTP Health Check

```bash
# Basic health check
curl http://localhost:8080/

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "eBIOS",
  "timestamp": "2025-10-29T14:32:10Z",
  "layers": {
    "layer0_nu_algebra": "operational",
    ...
  },
  "database": {
    "status": "connected",
    "type": "postgresql",
    "version": "17.6"
  }
}
```

### Database Connectivity

```bash
# Test PostgreSQL connection
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"
```

### Service Status (Systemd)

```bash
# Check service status
sudo systemctl status ebios

# Check if process is running
ps aux | grep uvicorn

# Check port binding
sudo ss -tlnp | grep 8080
```

### Docker Container Health

```bash
# Check container health
docker ps --filter name=ebios

# View health check logs
docker inspect ebios | jq '.[0].State.Health'

# Execute health check manually
docker exec ebios curl -f http://localhost:8080/ || exit 1
```

---

## Monitoring Setup

### Prometheus Configuration

Already configured in `monitoring/prometheus.yml`. To enable:

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Access Prometheus UI
open http://localhost:9090

# Query examples:
# - ebios_requests_total
# - rate(ebios_requests_total[5m])
# - ebios_request_duration_seconds
```

### Grafana Dashboard

```bash
# Access Grafana
open http://localhost:3000

# Default credentials (change immediately!)
# Username: admin
# Password: admin

# Add Prometheus data source:
# 1. Configuration → Data Sources → Add data source
# 2. Select Prometheus
# 3. URL: http://prometheus:9090
# 4. Save & Test

# Import eBIOS dashboard:
# 1. Dashboards → Import
# 2. Upload JSON: monitoring/grafana-dashboard.json
```

### Log Monitoring

```bash
# Real-time logs (Docker)
docker-compose logs -f ebios

# Real-time logs (Systemd)
sudo journalctl -u ebios -f

# Search logs
sudo journalctl -u ebios --since "1 hour ago" | grep ERROR

# Export logs
sudo journalctl -u ebios --since today > ebios_logs_$(date +%Y%m%d).txt
```

---

## Backup Configuration

### Automated Backups

```bash
# Copy backup script
sudo cp scripts/backup.sh /usr/local/bin/ebios-backup
sudo chmod +x /usr/local/bin/ebios-backup

# Configure environment
sudo vim /etc/ebios/backup.env
```

**Backup Environment** (`/etc/ebios/backup.env`):
```bash
POSTGRES_HOST=db-postgresql-nyc3-12345.db.ondigitalocean.com
POSTGRES_PORT=25060
POSTGRES_DB=ebios
POSTGRES_USER=doadmin
POSTGRES_PASSWORD=<DB_PASSWORD>
BACKUP_DIR=/var/backups/ebios
RETENTION_DAYS=30
S3_BUCKET=ebios-backups
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
```

### Cron Schedule

```bash
# Edit crontab
sudo crontab -e

# Daily backup at 2 AM
0 2 * * * source /etc/ebios/backup.env && /usr/local/bin/ebios-backup

# Hourly backup during business hours (9 AM - 5 PM, Mon-Fri)
0 9-17 * * 1-5 source /etc/ebios/backup.env && /usr/local/bin/ebios-backup
```

### Manual Backup

```bash
# Run backup manually
source /etc/ebios/backup.env
/usr/local/bin/ebios-backup

# Verify backup
ls -lh $BACKUP_DIR/

# Test restore (to different database)
gunzip < /var/backups/ebios/ebios_20251029_020000.sql.gz | \
  PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d ebios_test
```

### S3/Spaces Configuration

```bash
# Install AWS CLI
pip install awscli

# Configure DigitalOcean Spaces
aws configure --profile digitalocean
# AWS Access Key ID: <YOUR_SPACES_KEY>
# AWS Secret Access Key: <YOUR_SPACES_SECRET>
# Default region: nyc3
# Default output format: json

# Set endpoint in backup.env
S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
AWS_PROFILE=digitalocean
```

---

## Troubleshooting

### Service Won't Start

**Symptom**: `systemctl start ebios` fails

**Diagnosis**:
```bash
# Check service status
sudo systemctl status ebios -l

# View full logs
sudo journalctl -u ebios -xe

# Check if port is in use
sudo ss -tlnp | grep 8080

# Check environment file
sudo cat /opt/ebios/.env
```

**Common Causes**:
1. Port 8080 already in use → Change port or kill conflicting process
2. Database unreachable → Check firewall, VPC, credentials
3. Missing environment variables → Verify `.env` file
4. Permission denied → Check file ownership (`chown ebios:ebios`)

---

### Database Connection Errors

**Symptom**: "Could not connect to database"

**Diagnosis**:
```bash
# Test database connection
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB

# Check SSL mode
psql "$DATABASE_URL"

# Test from container
docker exec ebios env | grep POSTGRES
```

**Common Causes**:
1. Firewall blocking → Add server IP to trusted sources
2. Wrong credentials → Verify username/password
3. SSL required but not specified → Add `?sslmode=require` to URL
4. Database doesn't exist → Create database first

---

### Authentication Failures

**Symptom**: "401 Unauthorized" or "Incorrect username or password"

**Diagnosis**:
```bash
# Test login endpoint
curl -v -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Check if JWT secret is set
docker exec ebios env | grep JWT_SECRET_KEY

# Verify user exists in code
docker exec ebios grep -A5 "USERS = {" src/nugovern/auth.py
```

**Common Causes**:
1. Default credentials not changed → Check `src/nugovern/auth.py`
2. JWT_SECRET_KEY not set → Generate and set in `.env`
3. Password hash mismatch → Regenerate password hash

---

### Rate Limiting Issues

**Symptom**: "429 Too Many Requests"

**Diagnosis**:
```bash
# Check rate limit configuration
curl -I http://localhost:8080/ | grep X-RateLimit

# View rate limit settings
docker exec ebios env | grep RATE_LIMIT
```

**Solutions**:
1. Increase limit in `.env`: `RATE_LIMIT=1000/minute`
2. Use batch operations: `/operations/batch`
3. Implement caching on client side
4. Wait for rate limit window to reset (check `Retry-After` header)

---

### High Memory Usage

**Symptom**: Container or service using >2GB RAM

**Diagnosis**:
```bash
# Check memory usage (Docker)
docker stats ebios

# Check memory usage (Systemd)
systemctl status ebios | grep Memory

# View process details
ps aux --sort=-%mem | head -10
```

**Solutions**:
1. Reduce worker count: `--workers 2` (default: 4)
2. Increase memory limit: `MemoryMax=4G` (systemd)
3. Check for memory leaks in logs
4. Restart service regularly (cron: `systemctl restart ebios`)

---

## Security Hardening

### Production Checklist

- [ ] **Change default credentials** in `src/nugovern/auth.py`
- [ ] **Generate strong JWT secret** (64+ characters)
- [ ] **Use environment variables** for all secrets (no hardcoded values)
- [ ] **Enable SSL/TLS** with Let's Encrypt or custom certificate
- [ ] **Configure firewall** (only allow 443, 22, and internal ports)
- [ ] **Restrict database access** to VPC/private network only
- [ ] **Enable audit logging** (all auth events, operation failures)
- [ ] **Set up automated backups** with offsite storage (S3/Spaces)
- [ ] **Implement token blacklist** for logout functionality
- [ ] **Add rate limiting** to authentication endpoints
- [ ] **Run security scan** (`bandit -r src/`, `safety check`)
- [ ] **Update dependencies** regularly (`pip install --upgrade`)
- [ ] **Monitor security advisories** (GitHub Security, CVE databases)
- [ ] **Restrict metrics endpoint** to localhost/monitoring systems
- [ ] **Enable HSTS** in Nginx configuration
- [ ] **Implement fail2ban** for SSH and API endpoints
- [ ] **Use non-root user** for service execution
- [ ] **Set resource limits** (CPU, memory, file descriptors)
- [ ] **Enable SELinux/AppArmor** for container isolation
- [ ] **Regular penetration testing** (annually or after major changes)

### Firewall Configuration (firewalld)

```bash
# Allow HTTPS
sudo firewall-cmd --permanent --add-service=https

# Allow SSH (from specific IP)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="YOUR_IP" service name="ssh" accept'

# Block all other incoming
sudo firewall-cmd --set-default-zone=drop

# Allow internal services (adjust interface)
sudo firewall-cmd --permanent --zone=internal --add-interface=eth1
sudo firewall-cmd --permanent --zone=internal --add-service=postgresql
sudo firewall-cmd --permanent --zone=internal --add-port=9090/tcp

# Reload
sudo firewall-cmd --reload
```

---

## Migration from v0.3.0

### Pre-Migration Checklist

- [ ] **Backup v0.3.0 database** (full dump)
- [ ] **Test v1.0.0 in staging** environment first
- [ ] **Plan downtime window** (estimated: 30 minutes)
- [ ] **Notify users** of maintenance window
- [ ] **Prepare rollback plan** (revert to v0.3.0 if needed)

### Migration Steps

#### 1. Backup Current System

```bash
# Stop v0.3.0 service
sudo systemctl stop ebios

# Backup database
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios > ebios_v0.3.0_backup_$(date +%Y%m%d).sql

# Backup configuration
sudo cp -r /opt/ebios /opt/ebios_v0.3.0_backup
```

#### 2. Deploy v1.0.0

```bash
# Update repository
cd /opt/ebios
git fetch --all --tags
git checkout v1.0.0

# Install new dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

#### 3. Update Environment

```bash
# Add JWT configuration to .env
cat >> /opt/ebios/.env << 'EOF'

# JWT Authentication (v1.0.0)
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
EOF
```

#### 4. Update Systemd Service

```bash
# Update service file
sudo vim /etc/systemd/system/ebios.service

# Change ExecStart to use new server:
ExecStart=/opt/ebios/venv/bin/python -m uvicorn \
    src.nugovern.server_v1:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4 \
    --log-level info

# Reload systemd
sudo systemctl daemon-reload
```

#### 5. Start v1.0.0

```bash
# Start service
sudo systemctl start ebios

# Check status
sudo systemctl status ebios

# Test health check
curl http://localhost:8080/

# Test authentication
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### 6. Verify Migration

```bash
# Query ledger (should show v0.3.0 operations)
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" "http://localhost:8080/ledger/query?limit=10"

# Execute test operation (should work with new auth)
curl -X POST http://localhost:8080/operations/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "add",
    "inputs": {
      "a": {"nominal": 1.0, "uncertainty": 0.05},
      "b": {"nominal": 2.0, "uncertainty": 0.1}
    }
  }'
```

### Rollback Procedure (if needed)

```bash
# Stop v1.0.0
sudo systemctl stop ebios

# Restore v0.3.0 code
sudo rm -rf /opt/ebios
sudo mv /opt/ebios_v0.3.0_backup /opt/ebios

# Restore database
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d ebios < ebios_v0.3.0_backup_20251029.sql

# Restore old service
git checkout v0.3.0

# Update service file
sudo vim /etc/systemd/system/ebios.service
# Change ExecStart back to: src.nugovern.server:app

# Reload and start
sudo systemctl daemon-reload
sudo systemctl start ebios
```

---

## Appendix

### A. Quick Reference Commands

**Docker Compose**:
```bash
docker-compose up -d                  # Start services
docker-compose down                   # Stop services
docker-compose logs -f ebios          # View logs
docker-compose restart ebios          # Restart API
docker-compose exec ebios bash        # Shell into container
docker-compose ps                     # List services
```

**Systemd**:
```bash
sudo systemctl start ebios            # Start service
sudo systemctl stop ebios             # Stop service
sudo systemctl restart ebios          # Restart service
sudo systemctl status ebios           # Check status
sudo journalctl -u ebios -f           # View logs
sudo systemctl enable ebios           # Enable auto-start
```

**Database**:
```bash
psql "$DATABASE_URL"                  # Connect to database
pg_dump "$DATABASE_URL" > backup.sql  # Backup database
psql "$DATABASE_URL" < backup.sql     # Restore database
```

### B. Performance Tuning

**Uvicorn Workers**:
```bash
# Calculate optimal workers: (2 * CPU_cores) + 1
# 4-core CPU → 9 workers
uvicorn src.nugovern.server_v1:app --workers 9
```

**PostgreSQL Connection Pooling** (future enhancement):
```python
# In server_v1.py, use connection pooling
from psycopg2 import pool
db_pool = pool.SimpleConnectionPool(minconn=1, maxconn=20, dsn=DATABASE_URL)
```

**Nginx Caching** (for read-only endpoints):
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=ebios_cache:10m;

location /ledger/query {
    proxy_cache ebios_cache;
    proxy_cache_valid 200 5m;
    proxy_pass http://ebios_backend;
}
```

### C. Support Resources

- **Documentation**: https://docs.ebios.org
- **GitHub Issues**: https://github.com/abba-01/ebios/issues
- **Email**: support@ebios.org
- **API Docs**: https://api.ebios.org/docs

---

**Last Updated**: 2025-10-29
**Version**: 1.0.0
**Deployment Status**: Production Ready

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
