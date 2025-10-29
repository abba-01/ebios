"""
backends.py

Storage backends for NULedger.

Provides multiple backend options:
- MemoryBackend: In-memory (for testing)
- SQLiteBackend: Lightweight persistent storage
- PostgreSQLBackend: Production-grade clustered storage
- LMDBBackend: High-performance embedded database (future)
"""

import sqlite3
import json
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

if TYPE_CHECKING:
    from .ledger import LedgerEntry


class Backend(ABC):
    """Abstract base class for ledger storage backends"""

    @abstractmethod
    def append(self, entry: 'LedgerEntry') -> None:
        """Append entry to storage"""
        pass

    @abstractmethod
    def get(self, op_id: str) -> Optional['LedgerEntry']:
        """Get entry by operation ID"""
        pass

    @abstractmethod
    def get_all(self) -> List['LedgerEntry']:
        """Get all entries in chronological order"""
        pass


class MemoryBackend(Backend):
    """
    In-memory storage backend

    Use for:
    - Testing
    - Ephemeral sessions
    - Small ledgers that fit in RAM

    Data is lost when process exits.
    """

    def __init__(self):
        """Initialize empty in-memory storage"""
        self.entries: List['LedgerEntry'] = []
        self.index: dict = {}  # op_id -> entry

    def append(self, entry: 'LedgerEntry') -> None:
        """Append entry to memory"""
        self.entries.append(entry)
        self.index[entry.op_id] = entry

    def get(self, op_id: str) -> Optional['LedgerEntry']:
        """Get entry by ID"""
        return self.index.get(op_id)

    def get_all(self) -> List['LedgerEntry']:
        """Get all entries"""
        return self.entries.copy()


class SQLiteBackend(Backend):
    """
    SQLite storage backend

    Use for:
    - Persistent audit logs
    - Embedded systems
    - Single-process applications

    Features:
    - ACID transactions
    - Efficient queries
    - Cross-platform
    - ~600KB footprint

    Example:
        backend = SQLiteBackend("audit.db")
        ledger = Ledger(backend=backend)
    """

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize SQLite backend

        Args:
            db_path: Path to SQLite database file
                    Use ":memory:" for in-memory database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_schema()

    def _create_schema(self) -> None:
        """Create ledger table if it doesn't exist"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                timestamp INTEGER NOT NULL,
                op_id TEXT PRIMARY KEY,
                parent_id TEXT,
                operation TEXT NOT NULL,
                inputs TEXT NOT NULL,
                output TEXT NOT NULL,
                coverage REAL NOT NULL,
                invariant_passed INTEGER NOT NULL,
                signature TEXT NOT NULL
            )
        """)

        # Index for fast parent lookups
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_parent_id
            ON ledger(parent_id)
        """)

        # Index for timestamp ordering
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON ledger(timestamp)
        """)

        self.conn.commit()

    def append(self, entry: 'LedgerEntry') -> None:
        """Append entry to SQLite database"""
        self.conn.execute("""
            INSERT INTO ledger
            (timestamp, op_id, parent_id, operation, inputs, output,
             coverage, invariant_passed, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.timestamp,
            entry.op_id,
            entry.parent_id,
            entry.operation,
            json.dumps(entry.inputs),
            json.dumps(entry.output),
            entry.coverage,
            1 if entry.invariant_passed else 0,
            entry.signature
        ))
        self.conn.commit()

    def get(self, op_id: str) -> Optional['LedgerEntry']:
        """Get entry by operation ID"""
        # Import here to avoid circular dependency
        from .ledger import LedgerEntry

        cursor = self.conn.execute("""
            SELECT timestamp, op_id, parent_id, operation, inputs, output,
                   coverage, invariant_passed, signature
            FROM ledger
            WHERE op_id = ?
        """, (op_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        return LedgerEntry(
            timestamp=row[0],
            op_id=row[1],
            parent_id=row[2],
            operation=row[3],
            inputs=json.loads(row[4]),
            output=json.loads(row[5]),
            coverage=row[6],
            invariant_passed=bool(row[7]),
            signature=row[8]
        )

    def get_all(self) -> List['LedgerEntry']:
        """Get all entries in chronological order"""
        # Import here to avoid circular dependency
        from .ledger import LedgerEntry

        cursor = self.conn.execute("""
            SELECT timestamp, op_id, parent_id, operation, inputs, output,
                   coverage, invariant_passed, signature
            FROM ledger
            ORDER BY timestamp ASC
        """)

        entries = []
        for row in cursor.fetchall():
            entries.append(LedgerEntry(
                timestamp=row[0],
                op_id=row[1],
                parent_id=row[2],
                operation=row[3],
                inputs=json.loads(row[4]),
                output=json.loads(row[5]),
                coverage=row[6],
                invariant_passed=bool(row[7]),
                signature=row[8]
            ))

        return entries

    def close(self) -> None:
        """Close database connection"""
        self.conn.close()

    def __del__(self):
        """Cleanup on garbage collection"""
        if hasattr(self, 'conn'):
            self.conn.close()


class PostgreSQLBackend(Backend):
    """
    PostgreSQL storage backend

    Use for:
    - Production deployments
    - Multi-process applications
    - Clustered/distributed systems
    - Cloud-managed databases (DigitalOcean, AWS RDS, etc.)

    Features:
    - ACID transactions
    - Concurrent access
    - Replication support
    - Advanced indexing
    - Connection pooling

    Example:
        backend = PostgreSQLBackend(
            host="dbaas-db-xxx.ondigitalocean.com",
            port=25060,
            database="ebios",
            user="doadmin",
            password="xxx",
            sslmode="require"
        )
        ledger = Ledger(backend=backend)
    """

    def __init__(self, host: str, port: int, database: str,
                 user: str, password: str, sslmode: str = "require"):
        """
        Initialize PostgreSQL backend

        Args:
            host: PostgreSQL server hostname
            port: PostgreSQL server port
            database: Database name
            user: Database user
            password: Database password
            sslmode: SSL mode (require, verify-full, etc.)
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError(
                "psycopg2 not available. Install with: pip install psycopg2-binary"
            )

        self.conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode
        )
        self.conn.autocommit = False
        self._create_schema()

    def _create_schema(self) -> None:
        """Create ledger table if it doesn't exist"""
        with self.conn.cursor() as cur:
            cur.execute("""
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
                )
            """)

            # Index for fast parent lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_id
                ON ledger(parent_id)
            """)

            # Index for timestamp ordering
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON ledger(timestamp)
            """)

        self.conn.commit()

    def append(self, entry: 'LedgerEntry') -> None:
        """Append entry to PostgreSQL database"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ledger
                (timestamp, op_id, parent_id, operation, inputs, output,
                 coverage, invariant_passed, signature)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                entry.timestamp,
                entry.op_id,
                entry.parent_id,
                entry.operation,
                json.dumps(entry.inputs),
                json.dumps(entry.output),
                entry.coverage,
                entry.invariant_passed,
                entry.signature
            ))
        self.conn.commit()

    def get(self, op_id: str) -> Optional['LedgerEntry']:
        """Get entry by operation ID"""
        from .ledger import LedgerEntry

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, op_id, parent_id, operation, inputs, output,
                       coverage, invariant_passed, signature
                FROM ledger
                WHERE op_id = %s
            """, (op_id,))

            row = cur.fetchone()
            if row is None:
                return None

            return LedgerEntry(
                timestamp=row[0],
                op_id=row[1],
                parent_id=row[2],
                operation=row[3],
                inputs=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                output=json.loads(row[5]) if isinstance(row[5], str) else row[5],
                coverage=row[6],
                invariant_passed=row[7],
                signature=row[8]
            )

    def get_all(self) -> List['LedgerEntry']:
        """Get all entries in chronological order"""
        from .ledger import LedgerEntry

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, op_id, parent_id, operation, inputs, output,
                       coverage, invariant_passed, signature
                FROM ledger
                ORDER BY timestamp ASC
            """)

            entries = []
            for row in cur.fetchall():
                entries.append(LedgerEntry(
                    timestamp=row[0],
                    op_id=row[1],
                    parent_id=row[2],
                    operation=row[3],
                    inputs=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                    output=json.loads(row[5]) if isinstance(row[5], str) else row[5],
                    coverage=row[6],
                    invariant_passed=row[7],
                    signature=row[8]
                ))

            return entries

    def close(self) -> None:
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup on garbage collection"""
        self.close()


class LMDBBackend(Backend):
    """
    LMDB storage backend (future implementation)

    LMDB (Lightning Memory-Mapped Database) provides:
    - Ultra-fast reads (memory-mapped)
    - ACID transactions
    - Compact storage
    - Excellent for embedded systems

    Requires: lmdb Python package

    Status: Placeholder for future implementation
    """

    def __init__(self, db_path: str):
        """
        Initialize LMDB backend

        Args:
            db_path: Path to LMDB database directory
        """
        raise NotImplementedError(
            "LMDB backend not yet implemented. "
            "Use MemoryBackend or SQLiteBackend for now."
        )

    def append(self, entry: 'LedgerEntry') -> None:
        raise NotImplementedError()

    def get(self, op_id: str) -> Optional['LedgerEntry']:
        raise NotImplementedError()

    def get_all(self) -> List['LedgerEntry']:
        raise NotImplementedError()
