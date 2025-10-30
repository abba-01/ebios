"""
user_db.py

PostgreSQL backend for user management in eBIOS v1.0.0

Provides:
- User CRUD operations
- PostgreSQL persistence
- Fallback to in-memory storage if PostgreSQL unavailable
"""

from typing import Optional, List, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys

from .auth import UserInDB, get_password_hash, Role


class UserDatabase:
    """User database with PostgreSQL backend"""

    def __init__(self, backend=None):
        """
        Initialize user database

        Args:
            backend: Optional PostgreSQL connection parameters
        """
        self.backend = backend
        self.in_memory_users = {}

        if backend:
            try:
                self._init_schema()
                self._seed_default_users()
                print("✅ User database: PostgreSQL backend", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  User database PostgreSQL init failed: {e}", file=sys.stderr)
                print("⚠️  Falling back to in-memory storage", file=sys.stderr)
                self.backend = None
                self._seed_default_users_memory()
        else:
            print("⚠️  User database: In-memory storage (not production-ready)", file=sys.stderr)
            self._seed_default_users_memory()

    def _get_connection(self):
        """Get PostgreSQL connection"""
        if not self.backend:
            return None

        return psycopg2.connect(
            host=self.backend['host'],
            port=self.backend['port'],
            database=self.backend['database'],
            user=self.backend['user'],
            password=self.backend['password'],
            sslmode=self.backend.get('sslmode', 'require')
        )

    def _init_schema(self):
        """Initialize users table schema"""
        conn = self._get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(255) PRIMARY KEY,
                    hashed_password TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    disabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on role
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
            """)

            conn.commit()
            cur.close()
        finally:
            conn.close()

    def _seed_default_users(self):
        """Seed default users in PostgreSQL"""
        default_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': Role.ADMIN,
                'disabled': False
            },
            {
                'username': 'operator',
                'password': 'operator123',
                'role': Role.OPERATOR,
                'disabled': False
            },
            {
                'username': 'auditor',
                'password': 'auditor123',
                'role': Role.AUDITOR,
                'disabled': False
            }
        ]

        for user_data in default_users:
            # Check if user exists
            existing = self.get_user(user_data['username'])
            if not existing:
                self.create_user(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role'],
                    disabled=user_data['disabled']
                )

    def _seed_default_users_memory(self):
        """Seed default users in memory"""
        self.in_memory_users = {
            "admin": UserInDB(
                username="admin",
                role=Role.ADMIN,
                hashed_password="$2b$12$AYy0KPaL8iLcOOZhCDGmouDelCRTxEyoYiw.j2s6JGDbpAm6XRU.e",  # admin123
                disabled=False
            ),
            "operator": UserInDB(
                username="operator",
                role=Role.OPERATOR,
                hashed_password="$2b$12$./IEPKpV3gopDFfForvRB.HvErtNNV75Rpib4AEJ2/EWAR8duHjIa",  # operator123
                disabled=False
            ),
            "auditor": UserInDB(
                username="auditor",
                role=Role.AUDITOR,
                hashed_password="$2b$12$zS2zC.gcXPcbN3Jf5GXz5ulQ65fj6hofgYa3yqE7.CYDwhasn9.HS",  # auditor123
                disabled=False
            ),
        }

    def create_user(self, username: str, password: str, role: str, disabled: bool = False) -> UserInDB:
        """
        Create a new user

        Args:
            username: Username
            password: Plain text password (will be hashed)
            role: User role
            disabled: Whether user is disabled

        Returns:
            Created user
        """
        hashed_password = get_password_hash(password)

        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO users (username, hashed_password, role, disabled)
                    VALUES (%s, %s, %s, %s)
                """, (username, hashed_password, role, disabled))
                conn.commit()
                cur.close()
            finally:
                conn.close()
        else:
            self.in_memory_users[username] = UserInDB(
                username=username,
                hashed_password=hashed_password,
                role=role,
                disabled=disabled
            )

        return UserInDB(
            username=username,
            hashed_password=hashed_password,
            role=role,
            disabled=disabled
        )

    def get_user(self, username: str) -> Optional[UserInDB]:
        """
        Get user by username

        Args:
            username: Username to retrieve

        Returns:
            User if found, None otherwise
        """
        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT username, hashed_password, role, disabled
                    FROM users
                    WHERE username = %s
                """, (username,))

                row = cur.fetchone()
                cur.close()

                if row:
                    return UserInDB(**dict(row))
                return None
            finally:
                conn.close()
        else:
            return self.in_memory_users.get(username)

    def list_users(self) -> List[UserInDB]:
        """
        List all users

        Returns:
            List of all users
        """
        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute("""
                    SELECT username, hashed_password, role, disabled
                    FROM users
                    ORDER BY username
                """)

                rows = cur.fetchall()
                cur.close()

                return [UserInDB(**dict(row)) for row in rows]
            finally:
                conn.close()
        else:
            return list(self.in_memory_users.values())

    def update_user(self, username: str, role: Optional[str] = None, disabled: Optional[bool] = None) -> Optional[UserInDB]:
        """
        Update user properties

        Args:
            username: Username to update
            role: New role (optional)
            disabled: New disabled status (optional)

        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None

        if role is not None:
            user.role = role
        if disabled is not None:
            user.disabled = disabled

        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE users
                    SET role = %s, disabled = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s
                """, (user.role, user.disabled, username))
                conn.commit()
                cur.close()
            finally:
                conn.close()
        else:
            self.in_memory_users[username] = user

        return user

    def update_password(self, username: str, new_password: str) -> Optional[UserInDB]:
        """
        Update user password

        Args:
            username: Username to update
            new_password: New plain text password (will be hashed)

        Returns:
            Updated user if found, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None

        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password

        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE users
                    SET hashed_password = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s
                """, (hashed_password, username))
                conn.commit()
                cur.close()
            finally:
                conn.close()
        else:
            self.in_memory_users[username] = user

        return user

    def delete_user(self, username: str) -> bool:
        """
        Delete user

        Args:
            username: Username to delete

        Returns:
            True if deleted, False if not found
        """
        user = self.get_user(username)
        if not user:
            return False

        if self.backend:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM users WHERE username = %s", (username,))
                deleted = cur.rowcount > 0
                conn.commit()
                cur.close()
                return deleted
            finally:
                conn.close()
        else:
            if username in self.in_memory_users:
                del self.in_memory_users[username]
                return True
            return False


# Global user database instance
_user_db: Optional[UserDatabase] = None


def get_user_db() -> UserDatabase:
    """Get global user database instance"""
    global _user_db

    if _user_db is None:
        # Try to initialize with PostgreSQL
        from src.nuledger.backends import POSTGRES_AVAILABLE

        if POSTGRES_AVAILABLE:
            db_host = os.getenv('POSTGRES_HOST')
            db_port = int(os.getenv('POSTGRES_PORT', '5432'))
            db_name = os.getenv('POSTGRES_DB', 'ebios')
            db_user = os.getenv('POSTGRES_USER')
            db_password = os.getenv('POSTGRES_PASSWORD')

            if all([db_host, db_port, db_name, db_user, db_password]):
                try:
                    backend = {
                        'host': db_host,
                        'port': db_port,
                        'database': db_name,
                        'user': db_user,
                        'password': db_password,
                        'sslmode': os.getenv('POSTGRES_SSLMODE', 'require')
                    }
                    _user_db = UserDatabase(backend=backend)
                except Exception as e:
                    print(f"⚠️  Failed to initialize PostgreSQL user DB: {e}", file=sys.stderr)
                    _user_db = UserDatabase()
            else:
                _user_db = UserDatabase()
        else:
            _user_db = UserDatabase()

    return _user_db
