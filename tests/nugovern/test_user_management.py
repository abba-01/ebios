"""
test_user_management.py

Comprehensive tests for User Management API (v1.1+)

Tests all CRUD operations for user management:
- POST /users - Create user (admin only)
- GET /users - List users (admin only)
- GET /users/{username} - Get user (admin only)
- PUT /users/{username} - Update user (admin only)
- PUT /users/{username}/password - Change password (user + admin)
- DELETE /users/{username} - Delete user (admin only)
"""

import pytest
from fastapi.testclient import TestClient

from src.nugovern.server import create_app
from src.nugovern.user_db import get_user_db


@pytest.fixture
def client():
    """Create test client with fresh user database"""
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
def operator_token(client, admin_token):
    """Get operator JWT token (reset password if changed by previous tests)"""
    # Try to login with default password
    response = client.post("/auth/login", json={
        "username": "operator",
        "password": "operator123"
    })

    # If login fails (password changed by previous test), reset it
    if response.status_code != 200:
        # Reset password as admin
        client.put("/users/operator/password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "operator123"})

        # Try login again
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


class TestCreateUser:
    """Tests for POST /users (create user)"""

    def test_create_user_success(self, client, admin_token):
        """Test creating new user as admin"""
        response = client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "testuser",
                "password": "testpass123",
                "role": "operator",
                "disabled": False
            })

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["role"] == "operator"
        assert data["disabled"] is False
        assert "password" not in data  # Password should not be in response

    def test_create_user_duplicate(self, client, admin_token):
        """Test creating user with existing username fails"""
        # Create first user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "duplicate",
                "password": "pass123",
                "role": "operator",
                "disabled": False
            })

        # Try to create duplicate
        response = client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "duplicate",
                "password": "pass456",
                "role": "auditor",
                "disabled": False
            })

        assert response.status_code == 409  # Conflict
        assert "already exists" in response.json()["message"]

    def test_create_user_invalid_role(self, client, admin_token):
        """Test creating user with invalid role fails"""
        response = client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "baduser",
                "password": "pass123",
                "role": "superuser",  # Invalid role
                "disabled": False
            })

        assert response.status_code == 400
        assert "Invalid role" in response.json()["message"]

    def test_create_user_no_auth(self, client):
        """Test creating user without authentication fails"""
        response = client.post("/users", json={
            "username": "noauth",
            "password": "pass123",
            "role": "operator",
            "disabled": False
        })

        assert response.status_code == 403  # FastAPI returns 403 for missing token

    def test_create_user_operator_forbidden(self, client, operator_token):
        """Test creating user as operator fails (admin only)"""
        response = client.post("/users",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "username": "newuser",
                "password": "pass123",
                "role": "operator",
                "disabled": False
            })

        assert response.status_code == 403

    def test_create_user_disabled(self, client, admin_token):
        """Test creating disabled user"""
        response = client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "disableduser",
                "password": "pass123",
                "role": "guest",
                "disabled": True
            })

        assert response.status_code == 201
        data = response.json()
        assert data["disabled"] is True


class TestListUsers:
    """Tests for GET /users (list users)"""

    def test_list_users_success(self, client, admin_token):
        """Test listing users as admin"""
        response = client.get("/users",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 3  # At least admin, operator, auditor

        # Check default users exist
        usernames = [u["username"] for u in users]
        assert "admin" in usernames
        assert "operator" in usernames
        assert "auditor" in usernames

    def test_list_users_no_auth(self, client):
        """Test listing users without authentication fails"""
        response = client.get("/users")
        assert response.status_code == 403  # FastAPI returns 403 for missing token

    def test_list_users_operator_forbidden(self, client, operator_token):
        """Test listing users as operator fails (admin only)"""
        response = client.get("/users",
            headers={"Authorization": f"Bearer {operator_token}"})
        assert response.status_code == 403

    def test_list_users_auditor_forbidden(self, client, auditor_token):
        """Test listing users as auditor fails (admin only)"""
        response = client.get("/users",
            headers={"Authorization": f"Bearer {auditor_token}"})
        assert response.status_code == 403


class TestGetUser:
    """Tests for GET /users/{username} (get specific user)"""

    def test_get_user_success(self, client, admin_token):
        """Test getting user details as admin"""
        response = client.get("/users/operator",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "operator"
        assert data["role"] == "operator"
        assert "password" not in data

    def test_get_user_not_found(self, client, admin_token):
        """Test getting non-existent user fails"""
        response = client.get("/users/doesnotexist",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 404
        assert "not found" in response.json()["message"]

    def test_get_user_no_auth(self, client):
        """Test getting user without authentication fails"""
        response = client.get("/users/operator")
        assert response.status_code == 403  # FastAPI returns 403 for missing token

    def test_get_user_operator_forbidden(self, client, operator_token):
        """Test getting user as operator fails (admin only)"""
        response = client.get("/users/admin",
            headers={"Authorization": f"Bearer {operator_token}"})
        assert response.status_code == 403


class TestUpdateUser:
    """Tests for PUT /users/{username} (update user)"""

    def test_update_user_role(self, client, admin_token):
        """Test updating user role as admin"""
        # Create test user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "updatetest",
                "password": "pass123",
                "role": "guest",
                "disabled": False
            })

        # Update role
        response = client.put("/users/updatetest",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "operator"})

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "operator"
        assert data["username"] == "updatetest"

    def test_update_user_disabled(self, client, admin_token):
        """Test disabling user as admin"""
        # Create test user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "todisable",
                "password": "pass123",
                "role": "operator",
                "disabled": False
            })

        # Disable user
        response = client.put("/users/todisable",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"disabled": True})

        assert response.status_code == 200
        data = response.json()
        assert data["disabled"] is True

    def test_update_user_role_and_disabled(self, client, admin_token):
        """Test updating both role and disabled status"""
        # Create test user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "updateboth",
                "password": "pass123",
                "role": "guest",
                "disabled": False
            })

        # Update both
        response = client.put("/users/updateboth",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "auditor", "disabled": True})

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "auditor"
        assert data["disabled"] is True

    def test_update_user_not_found(self, client, admin_token):
        """Test updating non-existent user fails"""
        response = client.put("/users/doesnotexist",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "operator"})

        assert response.status_code == 404

    def test_update_user_invalid_role(self, client, admin_token):
        """Test updating user with invalid role fails"""
        # Create test user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "badrole",
                "password": "pass123",
                "role": "operator",
                "disabled": False
            })

        # Try invalid role
        response = client.put("/users/badrole",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "superadmin"})

        assert response.status_code == 400
        assert "Invalid role" in response.json()["message"]

    def test_update_user_no_auth(self, client):
        """Test updating user without authentication fails"""
        response = client.put("/users/operator",
            json={"role": "admin"})
        assert response.status_code == 403  # FastAPI returns 403 for missing token

    def test_update_user_operator_forbidden(self, client, operator_token):
        """Test updating user as operator fails (admin only)"""
        response = client.put("/users/auditor",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"role": "guest"})
        assert response.status_code == 403


class TestChangePassword:
    """Tests for PUT /users/{username}/password (change password)"""

    def test_change_own_password(self, client, operator_token):
        """Test user can change their own password"""
        response = client.put("/users/operator/password",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"new_password": "newpass123"})

        assert response.status_code == 200
        assert "successfully" in response.json()["message"]

        # Verify new password works
        login_response = client.post("/auth/login", json={
            "username": "operator",
            "password": "newpass123"
        })
        assert login_response.status_code == 200

    def test_admin_change_other_password(self, client, admin_token):
        """Test admin can change other user's password"""
        response = client.put("/users/operator/password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "adminchanged123"})

        assert response.status_code == 200
        assert "successfully" in response.json()["message"]

        # Verify new password works
        login_response = client.post("/auth/login", json={
            "username": "operator",
            "password": "adminchanged123"
        })
        assert login_response.status_code == 200

    def test_change_password_forbidden(self, client, operator_token):
        """Test user cannot change other user's password"""
        response = client.put("/users/admin/password",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"new_password": "hacked123"})

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["message"]

    def test_change_password_not_found(self, client, admin_token):
        """Test changing password for non-existent user fails"""
        response = client.put("/users/doesnotexist/password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "pass123"})

        assert response.status_code == 404

    def test_change_password_no_auth(self, client):
        """Test changing password without authentication fails"""
        response = client.put("/users/operator/password",
            json={"new_password": "pass123"})
        assert response.status_code == 403  # FastAPI returns 403 for missing token


class TestDeleteUser:
    """Tests for DELETE /users/{username} (delete user)"""

    def test_delete_user_success(self, client, admin_token):
        """Test deleting user as admin"""
        # Create test user
        client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "todelete",
                "password": "pass123",
                "role": "guest",
                "disabled": False
            })

        # Delete user
        response = client.delete("/users/todelete",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify user is gone
        get_response = client.get("/users/todelete",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client, admin_token):
        """Test deleting non-existent user fails"""
        response = client.delete("/users/doesnotexist",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 404

    def test_delete_self_forbidden(self, client, admin_token):
        """Test admin cannot delete their own account"""
        response = client.delete("/users/admin",
            headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 400
        assert "Cannot delete your own" in response.json()["message"]

    def test_delete_user_no_auth(self, client):
        """Test deleting user without authentication fails"""
        response = client.delete("/users/operator")
        assert response.status_code == 403  # FastAPI returns 403 for missing token

    def test_delete_user_operator_forbidden(self, client, operator_token):
        """Test deleting user as operator fails (admin only)"""
        response = client.delete("/users/auditor",
            headers={"Authorization": f"Bearer {operator_token}"})
        assert response.status_code == 403


class TestUserManagementIntegration:
    """Integration tests for complete user lifecycle"""

    def test_complete_user_lifecycle(self, client, admin_token):
        """Test full user lifecycle: create, update, change password, delete"""
        # 1. Create user
        create_response = client.post("/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "lifecycle",
                "password": "initial123",
                "role": "guest",
                "disabled": False
            })
        assert create_response.status_code == 201

        # 2. Verify user exists
        get_response = client.get("/users/lifecycle",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert get_response.status_code == 200
        assert get_response.json()["role"] == "guest"

        # 3. Update role
        update_response = client.put("/users/lifecycle",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "operator"})
        assert update_response.status_code == 200
        assert update_response.json()["role"] == "operator"

        # 4. Change password
        password_response = client.put("/users/lifecycle/password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"new_password": "changed123"})
        assert password_response.status_code == 200

        # 5. Verify new password works
        login_response = client.post("/auth/login", json={
            "username": "lifecycle",
            "password": "changed123"
        })
        assert login_response.status_code == 200

        # 6. Disable user
        disable_response = client.put("/users/lifecycle",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"disabled": True})
        assert disable_response.status_code == 200

        # 7. Verify disabled user cannot login
        login_disabled = client.post("/auth/login", json={
            "username": "lifecycle",
            "password": "changed123"
        })
        assert login_disabled.status_code == 401

        # 8. Delete user
        delete_response = client.delete("/users/lifecycle",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert delete_response.status_code == 200

        # 9. Verify user is gone
        final_get = client.get("/users/lifecycle",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert final_get.status_code == 404

    def test_user_list_reflects_changes(self, client, admin_token):
        """Test that user list reflects all changes"""
        # Get initial count
        initial_response = client.get("/users",
            headers={"Authorization": f"Bearer {admin_token}"})
        initial_count = len(initial_response.json())

        # Create 3 users
        for i in range(3):
            client.post("/users",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "username": f"listtest{i}",
                    "password": "pass123",
                    "role": "guest",
                    "disabled": False
                })

        # Verify count increased
        after_create = client.get("/users",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert len(after_create.json()) == initial_count + 3

        # Delete 2 users
        for i in range(2):
            client.delete(f"/users/listtest{i}",
                headers={"Authorization": f"Bearer {admin_token}"})

        # Verify count decreased
        after_delete = client.get("/users",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert len(after_delete.json()) == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
