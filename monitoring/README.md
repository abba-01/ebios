# eBIOS Monitoring Setup

This directory contains monitoring configurations for eBIOS.

## Overview

eBIOS exports Prometheus metrics which can be visualized using Grafana dashboards.

## Architecture

```
eBIOS API (/metrics endpoint)
    ↓
Prometheus (scrapes metrics)
    ↓
Grafana (visualizes data)
```

## Quick Start

### 1. Start Prometheus

Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ebios'
    static_configs:
      - targets: ['localhost:8080']  # eBIOS API address
    metrics_path: '/metrics'
    # Add authentication header for /metrics endpoint (admin only)
    bearer_token: 'your-admin-jwt-token-here'
```

Start Prometheus:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. Start Grafana

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

Access Grafana at http://localhost:3000 (default login: admin/admin)

### 3. Add Prometheus Data Source

1. Navigate to Configuration → Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. Set URL: `http://prometheus:9090` (or `http://localhost:9090` if not using Docker networking)
5. Click "Save & Test"

### 4. Import eBIOS Dashboard

1. Navigate to Create → Import
2. Upload `grafana/ebios-dashboard.json`
3. Select your Prometheus data source
4. Click "Import"

## Metrics Available

### Request Metrics
- `ebios_requests_total` - Total HTTP requests (labels: method, endpoint, status)
- `ebios_request_duration_seconds` - Request duration histogram

### Operation Metrics
- `ebios_operations_total` - Total operations executed (labels: operation)
- `ebios_invariant_failures_total` - Count of invariant failures

### System Metrics (from prometheus-client)
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `process_start_time_seconds` - Process start time

## Dashboard Panels

The eBIOS dashboard includes:

1. **Request Rate** - Requests per second over time
2. **Request Duration (p95)** - 95th and 99th percentile latency
3. **HTTP Status Codes** - Distribution of 2xx, 4xx, 5xx responses
4. **Operations by Type** - Rate of each operation type (add, multiply, etc.)
5. **Invariant Failures** - Rate of mathematical invariant violations
6. **Total Requests (24h)** - Daily request volume
7. **Error Rate** - Percentage of 4xx/5xx responses
8. **Uptime** - Service uptime
9. **Request Latency Heatmap** - Latency distribution over time
10. **Top Endpoints** - Most-used API endpoints
11. **Error Log** - Recent error events

## Alerts (Optional)

Create `alerts.yml` for Prometheus:

```yaml
groups:
  - name: ebios_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(ebios_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(ebios_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "p95 latency is {{ $value }}s"

      - alert: InvariantFailures
        expr: rate(ebios_invariant_failures_total[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Mathematical invariant failures detected"
          description: "Invariant failure rate: {{ $value }}/sec"
```

## Production Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your-secure-password
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana:/etc/grafana/provisioning/dashboards

volumes:
  prometheus-data:
  grafana-data:
```

Start stack:
```bash
docker-compose up -d
```

### Kubernetes Deployment

For Kubernetes, use:
- **Prometheus Operator** for managing Prometheus
- **ServiceMonitor** CRD to scrape eBIOS /metrics
- **Grafana Helm Chart** with dashboard provisioning

Example ServiceMonitor:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ebios
spec:
  selector:
    matchLabels:
      app: ebios
  endpoints:
  - port: http
    path: /metrics
    bearerTokenSecret:
      name: ebios-admin-token
      key: token
```

## Troubleshooting

### Prometheus not scraping metrics
1. Check eBIOS /metrics endpoint is accessible
2. Verify authentication (admin JWT token required)
3. Check Prometheus targets page: http://localhost:9090/targets

### Grafana shows "No data"
1. Verify Prometheus data source is configured
2. Check Prometheus is receiving metrics: http://localhost:9090/graph
3. Verify time range in Grafana dashboard

### High cardinality warnings
If you see high cardinality warnings, consider:
- Limiting the number of unique label values
- Using label aggregation in queries
- Adjusting Prometheus retention settings

## Security

- **Authentication**: The /metrics endpoint requires admin role authentication
- **Network**: Restrict Prometheus/Grafana access to authorized networks
- **Credentials**: Use strong passwords for Grafana admin account
- **TLS**: Enable TLS for production deployments

## See Also

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [eBIOS Metrics Endpoint](../src/nugovern/server.py#L433)
