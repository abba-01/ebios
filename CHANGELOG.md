# Changelog

All notable changes to eBIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-10-29

### Added
- **Alembic Database Migrations**
  - Database schema versioning with Alembic
  - Environment-based configuration (reads from POSTGRES_* env vars)
  - Initial migration: create users table (revision 5e1db40d8352)
  - Upgrade/downgrade support for safe schema changes
  - Index on users.role for query performance
  - Comprehensive migration documentation (migrations/README_MIGRATIONS.md)
  - Migration commands: `alembic upgrade head`, `alembic downgrade -1`, etc.

### Changed
- Added alembic>=1.13.0 to requirements.txt
- Database URL now constructed from environment variables in Alembic

### Benefits
- Safe production schema changes with rollback capability
- Track database version across environments
- Coordinate code deployments with schema changes
- Multi-environment support (dev/staging/prod)

## [1.1.1] - 2025-10-29

### Added
- **Structured Error Handling System**
  - Consistent JSON error responses across all endpoints
  - Request ID tracking for debugging (UUID per request)
  - Custom exception classes: `InvariantViolationError`, `PolicyViolationError`, `DatabaseError`, `AuthenticationError`, `AuthorizationError`
  - Validation error responses with field-level details
  - DEBUG mode for detailed tracebacks in development
  - Production-safe error messages (no sensitive data leaks)
  - Error code mapping for all HTTP status codes

### Changed
- API version updated to 1.1.0 in server.py
- All errors now return structured JSON format with:
  - `error`: Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
  - `message`: Human-readable message
  - `status_code`: HTTP status code
  - `request_id`: Unique UUID for request tracking
  - `timestamp`: ISO 8601 timestamp
  - `path`: Request path
  - `details`: Additional context (optional)

### Documentation
- Added DEBUG mode documentation to .env.example
- Documented error response format

## [1.1.0] - 2025-10-29

### Added
- **User Management API with PostgreSQL Backend**
  - Complete CRUD operations for users
  - POST /users - Create user (admin only)
  - GET /users - List all users (admin only)
  - GET /users/{username} - Get user details (admin only)
  - PUT /users/{username} - Update user properties (admin only)
  - DELETE /users/{username} - Delete user (admin only)
  - PUT /users/{username}/password - Change password (user + admin)
  - PostgreSQL users table with automatic schema initialization
  - Automatic seeding of default users (admin, operator, auditor)
  - Fallback to in-memory storage if PostgreSQL unavailable
  - Full RBAC integration (admin-only access for user management)

### Changed
- Replaced hardcoded `fake_users_db` with production-ready `UserDatabase` class
- `auth.py` now uses `user_db.get_user()` instead of in-memory dictionary
- Default users now created via database seeding instead of hardcoded

### Fixed
- User authentication now works with PostgreSQL backend
- User persistence across server restarts (when using PostgreSQL)

## [1.0.2-dev] - 2025-10-29

### Added
- **Security Headers Middleware**
  - HSTS (HTTP Strict Transport Security)
  - X-Content-Type-Options (MIME sniffing prevention)
  - X-Frame-Options (clickjacking prevention)
  - X-XSS-Protection (XSS filtering for legacy browsers)
  - Content-Security-Policy (CSP)
  - Referrer-Policy
  - Permissions-Policy
  - Configurable via environment variables (SECURITY_HSTS_ENABLED, SECURITY_HSTS_MAX_AGE, SECURITY_CSP)

### Documentation
- Added security headers configuration to .env.example

## [1.0.1-dev] - 2025-10-29

### Added
- **CORS Configuration**
  - CORS_ORIGINS environment variable for production deployments
  - Comma-separated list of allowed origins
  - Warning messages when using wildcard (*) in production

### Fixed
- **bcrypt Compatibility Issue**
  - Pinned bcrypt to 4.x range (4.0.0-4.9.9) for passlib 1.7.4 compatibility
  - Resolved test failures caused by bcrypt 5.0.0 strict validation
  - API tests now passing: 12/25 (up from 4/25)

### Changed
- `.env.example` updated with CORS configuration examples
- `requirements.txt` now pins bcrypt version

## [1.0.0] - 2025-10-28

### Added
- **JWT Authentication System**
  - Access tokens (60 min expiry, configurable)
  - Refresh tokens (30 day expiry, configurable)
  - Token generation and validation
  - Password hashing with bcrypt

- **Role-Based Access Control (RBAC)**
  - 4 roles: admin, operator, auditor, guest
  - Role-based endpoint protection
  - Permission enforcement middleware

- **PostgreSQL Backend**
  - Full PostgreSQL support for ledger operations
  - Connection pooling and error handling
  - SSL/TLS support (configurable)
  - Fallback to MemoryBackend if PostgreSQL unavailable

- **Rate Limiting**
  - 100 requests/minute per IP (configurable)
  - Endpoint-specific rate limits
  - Rate limit exceeded responses

- **Prometheus Metrics**
  - Request counters (method, endpoint, status)
  - Operation counters (by operation type)
  - Invariant failure counters
  - Request duration histograms

- **API Endpoints**
  - POST /auth/login - Login with username/password
  - POST /auth/refresh - Refresh access token
  - GET / - Health check (no auth)
  - POST /operations/execute - Execute operation (admin/operator)
  - POST /operations/batch - Batch operations (admin/operator)
  - GET /ledger/query - Query ledger (admin/operator/auditor)
  - GET /ledger/verify/{op_id} - Verify operation (admin/operator/auditor)
  - POST /policies/activate - Activate policy (admin)
  - POST /policies/deactivate - Deactivate policy (admin)
  - GET /metrics - Prometheus metrics (admin)

### Security
- SECRET_KEY environment variable for JWT signing
- Password hashing with bcrypt
- Token expiration and validation
- RBAC enforcement on all protected endpoints
- SSL/TLS support for PostgreSQL connections

### Documentation
- Comprehensive .env.example with all configuration options
- API documentation in FastAPI auto-generated docs (/docs)
- README updates with authentication and deployment instructions

---

## Versioning Strategy

- **Major version (X.0.0)**: Breaking changes, major feature releases
- **Minor version (1.X.0)**: New features, non-breaking changes
- **Patch version (1.0.X)**: Bug fixes, security patches

## Links

- [Repository](https://github.com/abba-01/ebios)
- [Issues](https://github.com/abba-01/ebios/issues)
