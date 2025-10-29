# Multi-stage Dockerfile for eBIOS
# Optimized for production deployment

# Stage 1: Build stage (if we had compiled components)
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt \
    && pip install --user --no-cache-dir \
    python-jose[cryptography] \
    passlib[bcrypt] \
    python-multipart \
    prometheus-client

# Stage 2: Runtime stage
FROM python:3.12-slim

LABEL maintainer="All Your Baseline LLC"
LABEL description="eBIOS - Epistemic Computation with Formal Verification"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY verification/ ./verification/
COPY README.md LICENSE ./

# Create non-root user
RUN useradd -m -u 1000 ebios && \
    chown -R ebios:ebios /app

# Switch to non-root user
USER ebios

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Run application
CMD ["python", "-m", "uvicorn", "src.nugovern.server_v1:app", "--host", "0.0.0.0", "--port", "8080"]
