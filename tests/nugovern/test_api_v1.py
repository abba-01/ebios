"""
test_api_v1.py

Comprehensive tests for NUGovern HTTP API v1.0.0 with JWT authentication.
"""

import pytest
from fastapi.testclient import TestClient

from src.nugovern import create_app


@pytest.fixture
def client():
    """Create test client with v1.0.0 API"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin JWT token"""
    response = client.post("/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def operator_token(client):
    """Get operator JWT token"""
    response = client.post("/auth/login", json={
        "username": "operator",
        "password": "operator123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auditor_token(client):
    """Get auditor JWT token"""
    response = client.post("/auth/login", json={
        "username": "auditor",
        "password": "auditor123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def operator_headers(operator_token):
    """Get authorization headers with operator token"""
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture
def auditor_headers(auditor_token):
    """Get authorization headers with auditor token"""
    return {"Authorization": f"Bearer {auditor_token}"}


class TestHealthEndpoint:
    """Tests for health check endpoint (no auth required)"""

    def test_health_check(self, client):
        """Test health check returns status"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'healthy'
        assert data['version'] == '1.0.0'
        assert 'layers' in data
        assert data['layers']['nucore'] is True
        assert data['layers']['auth'] is True
        assert data['layers']['rbac'] is True


class TestAuthenticationEndpoints:
    """Tests for authentication endpoints"""

    def test_login_admin(self, client):
        """Test login with admin credentials"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_operator(self, client):
        """Test login with operator credentials"""
        response = client.post("/auth/login", json={
            "username": "operator",
            "password": "operator123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_auditor(self, client):
        """Test login with auditor credentials"""
        response = client.post("/auth/login", json={
            "username": "auditor",
            "password": "auditor123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        assert response.status_code == 401

    def test_refresh_token(self, client, admin_token):
        """Test refreshing access token"""
        # First login to get refresh token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestOperationsEndpoint:
    """Tests for NUCore operations (require operator or admin role)"""

    def test_execute_add_operation(self, client, operator_headers):
        """Test ADD operation with authentication"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
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

    def test_execute_multiply_operation(self, client, operator_headers):
        """Test MULTIPLY operation"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "multiply",
                "inputs": [[10.0, 0.5], [20.0, 1.0]],
                "params": {"lambda_margin": 1.0}
            })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == pytest.approx(200.0)
        assert data['invariant_passed'] is True

    def test_execute_compose_operation(self, client, operator_headers):
        """Test COMPOSE operation"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "compose",
                "inputs": [[10.0, 5.0], [10.0, 3.0]]
            })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == pytest.approx(10.0)
        assert data['result'][1] < 5.0  # Uncertainty should reduce

    def test_execute_catch_operation(self, client, operator_headers):
        """Test CATCH operation"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "catch",
                "inputs": [[10.0, 0.5]]
            })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == 10.0
        assert data['result'][1] == 0.5

    def test_execute_flip_operation(self, client, operator_headers):
        """Test FLIP operation"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "flip",
                "inputs": [[10.0, 0.5]]
            })

        assert response.status_code == 200
        data = response.json()

        assert data['result'][0] == -10.0
        assert data['result'][1] == 0.5

    def test_operation_without_auth(self, client):
        """Test operation fails without authentication"""
        response = client.post("/operations/execute", json={
            "operation": "add",
            "inputs": [[10.0, 0.5], [20.0, 1.0]]
        })
        assert response.status_code == 403  # Forbidden without auth

    def test_operation_with_auditor_role(self, client, auditor_headers):
        """Test operation fails with auditor role (read-only)"""
        response = client.post("/operations/execute",
            headers=auditor_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        assert response.status_code == 403  # Auditor can't execute operations

    def test_invalid_operation_inputs(self, client, operator_headers):
        """Test operation with wrong number of inputs"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5]]  # Should be 2 inputs
            })

        assert response.status_code == 400


class TestLedgerEndpoints:
    """Tests for ledger querying (require auditor, operator, or admin role)"""

    def test_query_ledger_empty(self, client, auditor_headers):
        """Test querying empty ledger"""
        response = client.get("/ledger/query", headers=auditor_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_query_ledger_after_operations(self, client, operator_headers, auditor_headers):
        """Test querying ledger after operations"""
        # Execute some operations as operator
        client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "multiply",
                "inputs": [[5.0, 0.1], [10.0, 0.2]]
            })

        # Query as auditor
        response = client.get("/ledger/query?limit=10", headers=auditor_headers)
        assert response.status_code == 200

    def test_query_ledger_without_auth(self, client):
        """Test ledger query fails without authentication"""
        response = client.get("/ledger/query")
        assert response.status_code == 403

    def test_ledger_pagination(self, client, operator_headers, auditor_headers):
        """Test ledger pagination"""
        # Execute multiple operations
        for i in range(5):
            client.post("/operations/execute",
                headers=operator_headers,
                json={
                    "operation": "add",
                    "inputs": [[float(i), 0.1], [1.0, 0.1]]
                })

        # Get first 2
        response = client.get("/ledger/query?limit=2&offset=0", headers=auditor_headers)
        assert response.status_code == 200

        # Get next 2
        response = client.get("/ledger/query?limit=2&offset=2", headers=auditor_headers)
        assert response.status_code == 200


class TestRBACPermissions:
    """Tests for Role-Based Access Control"""

    def test_admin_can_execute_operations(self, client, auth_headers):
        """Test admin can execute operations"""
        response = client.post("/operations/execute",
            headers=auth_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        assert response.status_code == 200

    def test_operator_can_execute_operations(self, client, operator_headers):
        """Test operator can execute operations"""
        response = client.post("/operations/execute",
            headers=operator_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        assert response.status_code == 200

    def test_auditor_cannot_execute_operations(self, client, auditor_headers):
        """Test auditor cannot execute operations"""
        response = client.post("/operations/execute",
            headers=auditor_headers,
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        assert response.status_code == 403

    def test_auditor_can_query_ledger(self, client, auditor_headers):
        """Test auditor can query ledger"""
        response = client.get("/ledger/query", headers=auditor_headers)
        assert response.status_code == 200

    def test_invalid_token(self, client):
        """Test request with invalid token"""
        response = client.post("/operations/execute",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "operation": "add",
                "inputs": [[10.0, 0.5], [20.0, 1.0]]
            })
        assert response.status_code == 401


class TestBatchOperations:
    """Tests for batch operation execution"""

    def test_batch_operations(self, client, operator_headers):
        """Test executing batch operations"""
        response = client.post("/operations/batch",
            headers=operator_headers,
            json=[
                {
                    "operation": "add",
                    "inputs": [[10.0, 0.5], [20.0, 1.0]]
                },
                {
                    "operation": "multiply",
                    "inputs": [[5.0, 0.1], [10.0, 0.2]]
                }
            ])

        assert response.status_code == 200
        data = response.json()
        assert data['total_operations'] == 2
        assert data['successful'] == 2
        assert len(data['results']) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
