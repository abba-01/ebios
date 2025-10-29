"""
user_management.py

User management CLI for eBIOS v1.0.0

Features:
- Create/delete/list users
- Change passwords
- Assign roles
- Database-backed user storage

Usage:
    python -m nugovern.user_management create --username admin --password <pass> --role admin
    python -m nugovern.user_management list
    python -m nugovern.user_management change-password --username admin
    python -m nugovern.user_management delete --username user123
"""

import click
import getpass
from passlib.context import CryptContext
from typing import Optional
import os

from .auth import Role

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# TODO: Implement PostgreSQL backend for users
# For now, this is a template for future implementation
class UserStore:
    """User storage interface (to be implemented with PostgreSQL)"""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize user store"""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        # TODO: Connect to PostgreSQL
        pass

    def create_user(self, username: str, hashed_password: str, role: str) -> bool:
        """Create a new user"""
        # TODO: INSERT INTO users (username, hashed_password, role, created_at)
        print(f"⚠️  TODO: Implement PostgreSQL user storage")
        print(f"Would create user: {username} with role: {role}")
        print(f"Hashed password: {hashed_password[:20]}...")
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        # TODO: DELETE FROM users WHERE username = ?
        print(f"⚠️  TODO: Implement PostgreSQL user storage")
        print(f"Would delete user: {username}")
        return True

    def list_users(self):
        """List all users"""
        # TODO: SELECT username, role, created_at FROM users
        print(f"⚠️  TODO: Implement PostgreSQL user storage")
        print("Would list all users from database")
        return []

    def update_password(self, username: str, hashed_password: str) -> bool:
        """Update user password"""
        # TODO: UPDATE users SET hashed_password = ? WHERE username = ?
        print(f"⚠️  TODO: Implement PostgreSQL user storage")
        print(f"Would update password for user: {username}")
        return True

    def get_user(self, username: str):
        """Get user by username"""
        # TODO: SELECT * FROM users WHERE username = ?
        return None


def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < 12:
        click.echo("❌ Password must be at least 12 characters long")
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    if not has_upper:
        click.echo("❌ Password must contain at least one uppercase letter")
        return False
    if not has_lower:
        click.echo("❌ Password must contain at least one lowercase letter")
        return False
    if not has_digit:
        click.echo("❌ Password must contain at least one digit")
        return False
    if not has_special:
        click.echo("❌ Password must contain at least one special character")
        return False

    return True


@click.group()
def cli():
    """eBIOS User Management CLI"""
    pass


@cli.command()
@click.option('--username', required=True, help='Username')
@click.option('--password', default=None, help='Password (will prompt if not provided)')
@click.option('--role', type=click.Choice(['admin', 'operator', 'auditor', 'guest']), required=True, help='User role')
def create(username: str, password: Optional[str], role: str):
    """Create a new user"""

    click.echo(f"\n=== Creating User: {username} ===\n")

    # Get password if not provided
    if not password:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            click.echo("❌ Passwords do not match")
            return

    # Validate password strength
    if not validate_password_strength(password):
        return

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Create user
    store = UserStore()
    if store.create_user(username, hashed_password, role):
        click.echo(f"✅ User '{username}' created successfully with role '{role}'")
        click.echo(f"\n⚠️  IMPORTANT: User storage not yet implemented in PostgreSQL")
        click.echo(f"   For now, add this user to src/nugovern/auth.py USERS dict:")
        click.echo(f'\n"{username}": User(')
        click.echo(f'    username="{username}",')
        click.echo(f'    hashed_password="{hashed_password}",')
        click.echo(f'    role=Role.{role.upper()}')
        click.echo(f')\n')
    else:
        click.echo(f"❌ Failed to create user '{username}'")


@cli.command()
def list():
    """List all users"""

    click.echo("\n=== eBIOS Users ===\n")

    store = UserStore()
    users = store.list_users()

    if not users:
        click.echo("⚠️  TODO: PostgreSQL user storage not implemented")
        click.echo("\nCurrent users are hardcoded in src/nugovern/auth.py:")
        click.echo("  - admin (role: admin)")
        click.echo("  - operator (role: operator)")
        click.echo("  - auditor (role: auditor)")
        click.echo("  - guest (role: guest)")
        click.echo("\n⚠️  WARNING: Change these default passwords before production!")
        return

    # TODO: Format user list
    for user in users:
        click.echo(f"  - {user['username']} (role: {user['role']})")


@cli.command()
@click.option('--username', required=True, help='Username')
def change_password(username: str):
    """Change user password"""

    click.echo(f"\n=== Change Password for: {username} ===\n")

    # Get current password
    current_password = getpass.getpass("Enter current password: ")

    # TODO: Verify current password
    store = UserStore()
    user = store.get_user(username)
    if not user:
        click.echo(f"❌ User '{username}' not found")
        return

    # Get new password
    new_password = getpass.getpass("Enter new password: ")
    new_password_confirm = getpass.getpass("Confirm new password: ")

    if new_password != new_password_confirm:
        click.echo("❌ Passwords do not match")
        return

    # Validate password strength
    if not validate_password_strength(new_password):
        return

    # Hash and update
    hashed_password = pwd_context.hash(new_password)

    if store.update_password(username, hashed_password):
        click.echo(f"✅ Password changed successfully for user '{username}'")
    else:
        click.echo(f"❌ Failed to change password for user '{username}'")


@cli.command()
@click.option('--username', required=True, help='Username')
@click.confirmation_option(prompt='Are you sure you want to delete this user?')
def delete(username: str):
    """Delete a user"""

    click.echo(f"\n=== Deleting User: {username} ===\n")

    store = UserStore()
    if store.delete_user(username):
        click.echo(f"✅ User '{username}' deleted successfully")
    else:
        click.echo(f"❌ Failed to delete user '{username}'")


@cli.command()
def init_db():
    """Initialize user database schema"""

    click.echo("\n=== Initializing User Database ===\n")

    # TODO: Create PostgreSQL schema
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('admin', 'operator', 'auditor', 'guest')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        active BOOLEAN DEFAULT TRUE
    );

    CREATE INDEX IF NOT EXISTS idx_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_role ON users(role);
    """

    click.echo("SQL Schema:")
    click.echo(schema_sql)
    click.echo("\n⚠️  TODO: Execute this SQL against PostgreSQL database")
    click.echo("   Run: psql $DATABASE_URL < schema.sql")


if __name__ == '__main__':
    cli()
