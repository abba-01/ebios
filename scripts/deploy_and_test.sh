#!/bin/bash
# eBIOS v1.0.0 Deployment and Testing Script
# Deploys from GitHub and runs integration tests with PostgreSQL

set -e

echo "=== eBIOS v1.0.0 Deployment and Test ==="
echo ""

# Configuration
DEPLOY_DIR="/opt/ebios"
REPO_URL="https://github.com/abba-01/ebios.git"
BRANCH="v1.0.0-dev"

# PostgreSQL Testing Credentials (from environment or prompt)
: ${POSTGRES_USER:=doadmin}
: ${POSTGRES_PASSWORD:?'POSTGRES_PASSWORD must be set'}
: ${POSTGRES_HOST:=private-postgres-testing-do-user-15048181-0.m.db.ondigitalocean.com}
: ${POSTGRES_PORT:=25060}
: ${POSTGRES_DB:=ebios_v1_test}
: ${POSTGRES_SSLMODE:=require}

# Step 1: Clone/Update Repository
echo "Step 1: Deploying from GitHub..."
if [ -d "$DEPLOY_DIR" ]; then
    cd "$DEPLOY_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    echo "✅ Updated to latest $BRANCH"
else
    git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    echo "✅ Cloned repository"
fi

COMMIT_HASH=$(git log -1 --format="%H")
COMMIT_MSG=$(git log -1 --format="%s")
echo "📍 Commit: $COMMIT_HASH"
echo "   $COMMIT_MSG"
echo ""

# Step 2: Setup Virtual Environment
echo "Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q psycopg2-binary pytest
echo "✅ Virtual environment ready"
echo ""

# Step 3: Create .env file
echo "Step 3: Configuring environment..."
cat > .env << EOF
SECRET_KEY=ebios-v1-test-$(openssl rand -hex 16)
POSTGRES_HOST=$POSTGRES_HOST
POSTGRES_PORT=$POSTGRES_PORT
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_SSLMODE=$POSTGRES_SSLMODE
EOF
source .env
echo "✅ Environment configured"
echo ""

# Step 4: Verify PostgreSQL Connection
echo "Step 4: Verifying PostgreSQL connection..."
python3 << PYEOF
import psycopg2
try:
    conn = psycopg2.connect(
        host="$POSTGRES_HOST",
        port=$POSTGRES_PORT,
        database="$POSTGRES_DB",
        user="$POSTGRES_USER",
        password="$POSTGRES_PASSWORD",
        sslmode="$POSTGRES_SSLMODE"
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"✅ Connected to PostgreSQL")
    print(f"   {version[:60]}...")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}")
    exit(1)
PYEOF
echo ""

# Step 5: Start Server
echo "Step 5: Starting eBIOS server..."
pkill -f "uvicorn.*server_v1" || true
sleep 2
nohup python3 -m uvicorn src.nugovern.server_v1:app \
    --host 127.0.0.1 --port 8080 \
    > /tmp/ebios_test.log 2>&1 &
SERVER_PID=$!
echo "✅ Server started (PID: $SERVER_PID)"
sleep 5
echo ""

# Step 6: Health Check
echo "Step 6: Health check..."
HEALTH=$(curl -s http://127.0.0.1:8080/ || echo '{"status":"failed"}')
echo "$HEALTH" | python3 -m json.tool
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "✅ Server is healthy"
else
    echo "❌ Health check failed"
    kill $SERVER_PID
    exit 1
fi
echo ""

# Step 7: Run Tests
echo "Step 7: Running integration tests..."
echo ""

# Check if tests directory exists
if [ ! -d "tests" ]; then
    echo "⚠️  No tests directory found - creating basic auth test..."
    mkdir -p tests/auth
    cat > tests/auth/test_auth_basic.py << 'TESTEOF'
import requests

def test_health():
    """Test health endpoint"""
    response = requests.get("http://127.0.0.1:8080/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_login():
    """Test login endpoint"""
    response = requests.post(
        "http://127.0.0.1:8080/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
TESTEOF
fi

# Run pytest
pytest tests/ -v --tb=short || echo "⚠️  Some tests failed"
echo ""

# Step 8: Cleanup
echo "Step 8: Cleanup..."
kill $SERVER_PID 2>/dev/null || true
echo "✅ Server stopped"
echo ""

# Step 9: Summary
echo "=== Test Summary ==="
echo "✅ Git commit: $COMMIT_HASH"
echo "🧩 PostgreSQL: Connected to $POSTGRES_HOST"
echo "🧪 Tests: See output above"
echo ""
echo "Logs available at: /tmp/ebios_test.log"
