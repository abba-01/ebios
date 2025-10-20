"""
test_api.py

Comprehensive tests for NUGovern HTTP API.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile

from src.nugovern import create_app, NUGovernServer
from src.nuledger import MemoryBackend


@pytest.fixture
def server():
    """Create test server with temp directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        server = NUGovernServer(
            ledger_backend=MemoryBackend(),
            policy_dir=Path(tmpdir)
        )
        yield server


@pytest.fixture
def client(server):
    """Create test client"""
    app = create_app(server)
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self, client):
        """Test health check returns status"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'healthy'
        assert data['version'] == '0.1.0'
        assert 'layers' in data
        assert data['layers']['nucore'] is True


class TestOperationsEndpoint:
    """Tests for NUCore operations"""

    def test_execute_add_operation(self, client):
        """Test ADD operation"""
        response = client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]],
            "params": None
        })

        assert response.status_code == 200
        data = response.json()

        assert 'result' in data
        assert len(data['result']) == 2
        assert data['result'][0] == pytest.approx(30.0)
        assert data['result'][1] == pytest.approx(1.12, rel=0.01)
        assert data['invariant_passed'] is True
        assert data['coverage'] > 0

    def test_execute_multiply_operation(self, client):
        """Test MULTIPLY operation"""
        response = client.post("/operations/execute", json={
            "operation": "multiply",
            "inputs": [[10.0, 0.5], [20.0, 1.0]],
            "params": {"lambda_margin": 1.0}
        })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == pytest.approx(200.0)
        assert data['invariant_passed'] is True

    def test_execute_compose_operation(self, client):
        """Test COMPOSE operation"""
        response = client.post("/operations/execute", json={
            "operation": "compose",
            "inputs": [[10.0, 5.0], [10.0, 3.0]]
        })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == pytest.approx(10.0)
        assert data['result'][1] < 5.0  # Uncertainty should reduce

    def test_execute_catch_operation(self, client):
        """Test CATCH operation"""
        response = client.post("/operations/execute", json={
            "operation": "catch",
            "inputs": [[10.0, 0.5]]
        })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == 10.0
        assert data['result'][1] == 0.5

    def test_execute_flip_operation(self, client):
        """Test FLIP operation"""
        response = client.post("/operations/execute", json={
            "operation": "flip",
            "inputs": [[10.0, 0.5]]
        })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == -10.0
        assert data['result'][1] == 0.5

    def test_invalid_operation_inputs(self, client):
        """Test operation with wrong number of inputs"""
        response = client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5]]  # Should be 2 inputs
        })

        assert response.status_code == 400

    def test_operation_creates_ledger_entry(self, client):
        """Test that operations are logged to ledger"""
        # Execute operation
        response = client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })

        assert response.status_code == 200
        ledger_id = response.json()['ledger_id']
        assert ledger_id is not None

        # Query ledger
        ledger_response = client.get("/ledger/entries")
        assert ledger_response.status_code == 200

        entries = ledger_response.json()
        assert len(entries) >= 1


class TestPolicyEndpoints:
    """Tests for policy management"""

    def test_create_policy(self, client):
        """Test creating new policy"""
        response = client.post("/policies", json={
            "name": "TestPolicy",
            "description": "Test policy",
            "version": "1.0.0",
            "rules": [
                {"type": "InvariantRule"},
                {"type": "CoverageRule", "threshold": 0.1, "level": "warning"}
            ],
            "escalation": {"halt_on_critical": False, "auto_log": True},
            "metadata": {"author": "test"}
        })

        assert response.status_code == 200
        data = response.json()

        assert data['name'] == "TestPolicy"
        assert data['version'] == "1.0.0"
        assert data['rules_count'] == 2
        assert data['signed'] is False

    def test_list_policies(self, client, server):
        """Test listing policies"""
        # Create a policy first
        server.create_policy(type('Request', (), {
            'name': 'Policy1',
            'description': 'Test',
            'version': '1.0.0',
            'rules': [],
            'escalation': None,
            'metadata': None
        })())

        response = client.get("/policies")
        assert response.status_code == 200

        policies = response.json()
        assert isinstance(policies, list)
        assert "Policy1" in policies

    def test_get_policy(self, client, server):
        """Test retrieving specific policy"""
        # Create policy
        server.create_policy(type('Request', (), {
            'name': 'RetrieveTest',
            'description': 'Test retrieval',
            'version': '1.0.0',
            'rules': [{"type": "InvariantRule"}],
            'escalation': None,
            'metadata': None
        })())

        response = client.get("/policies/RetrieveTest")
        assert response.status_code == 200

        data = response.json()
        assert data['name'] == "RetrieveTest"
        assert data['rules_count'] == 1

    def test_get_nonexistent_policy(self, client):
        """Test getting policy that doesn't exist"""
        response = client.get("/policies/DoesNotExist")
        assert response.status_code == 404

    def test_activate_policy(self, client, server):
        """Test activating policy (reconfiguring monitor)"""
        # Create policy
        server.create_policy(type('Request', (), {
            'name': 'ActivateTest',
            'description': 'Test activation',
            'version': '1.0.0',
            'rules': [
                {"type": "CoverageRule", "threshold": 0.01, "level": "error"}
            ],
            'escalation': {"halt_on_critical": True},
            'metadata': None
        })())

        response = client.put("/policies/ActivateTest/activate")
        assert response.status_code == 200

        data = response.json()
        assert 'message' in data
        assert 'ActivateTest' in data['message']

        # Verify monitor was reconfigured
        assert server.monitor.config.halt_on_critical is True


class TestLedgerEndpoints:
    """Tests for ledger querying"""

    def test_get_ledger_entries_empty(self, client):
        """Test getting ledger entries when empty"""
        response = client.get("/ledger/entries")
        assert response.status_code == 200

        entries = response.json()
        assert isinstance(entries, list)

    def test_get_ledger_entries_with_operations(self, client):
        """Test getting ledger entries after operations"""
        # Execute some operations
        client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })
        client.post("/operations/execute", json={
            "operation": "multiply",
            "inputs": [[5.0, 0.1], [10.0, 0.2]]
        })

        response = client.get("/ledger/entries")
        assert response.status_code == 200

        entries = response.json()
        assert len(entries) == 2

        # Check entry structure
        entry = entries[0]
        assert 'op_id' in entry
        assert 'operation' in entry
        assert 'inputs' in entry
        assert 'output' in entry
        assert 'coverage' in entry

    def test_ledger_pagination(self, client):
        """Test ledger pagination"""
        # Execute multiple operations
        for i in range(5):
            client.post("/operations/execute", json={
                "operation": "add",
                "inputs": [[float(i), 0.1], [1.0, 0.1]]
            })

        # Get first 2
        response = client.get("/ledger/entries?limit=2&offset=0")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get next 2
        response = client.get("/ledger/entries?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_verify_ledger(self, client):
        """Test ledger integrity verification"""
        # Add some entries
        client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })

        response = client.get("/ledger/verify")
        assert response.status_code == 200

        data = response.json()
        assert data['valid'] is True
        assert 'entries' in data
        assert 'root' in data


class TestMonitorEndpoints:
    """Tests for monitor statistics"""

    def test_get_monitor_stats(self, client):
        """Test getting monitor statistics"""
        response = client.get("/monitor/stats")
        assert response.status_code == 200

        data = response.json()
        assert 'total_events' in data
        assert 'violations' in data
        assert 'rules' in data
        assert isinstance(data['rules'], list)

    def test_reset_monitor(self, client):
        """Test resetting monitor statistics"""
        # Generate some events by executing operations
        client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })

        # Reset
        response = client.post("/monitor/reset")
        assert response.status_code == 200

        # Verify stats reset
        stats_response = client.get("/monitor/stats")
        data = stats_response.json()
        assert data['total_events'] == 0


class TestAttestationEndpoints:
    """Tests for attestation endpoints"""

    def test_create_policy_attestation(self, client, server):
        """Test creating attestation for policy"""
        # Create policy
        server.create_policy(type('Request', (), {
            'name': 'AttestPolicy',
            'description': 'For attestation',
            'version': '1.0.0',
            'rules': [{"type": "InvariantRule"}],
            'escalation': None,
            'metadata': None
        })())

        response = client.post("/attestation", json={
            "attestation_type": "policy",
            "target_id": "AttestPolicy"
        })

        assert response.status_code == 200
        data = response.json()

        assert data['attestation_type'] == "policy"
        assert data['target_id'] == "AttestPolicy"
        assert 'hash' in data
        assert 'timestamp' in data
        assert data['verified'] is False  # Unsigned

    def test_create_ledger_attestation(self, client):
        """Test creating attestation for ledger"""
        # Add some entries
        client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })

        response = client.post("/attestation", json={
            "attestation_type": "ledger",
            "target_id": None
        })

        assert response.status_code == 200
        data = response.json()

        assert data['attestation_type'] == "ledger"
        assert 'hash' in data  # Merkle root
        assert data['verified'] is True  # Ledger integrity

    def test_attestation_nonexistent_policy(self, client):
        """Test attestation for non-existent policy"""
        response = client.post("/attestation", json={
            "attestation_type": "policy",
            "target_id": "NonExistent"
        })

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
