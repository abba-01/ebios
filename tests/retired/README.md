# Retired Tests

This directory contains tests that are **no longer compatible** with the current eBIOS API architecture.

## test_api_v0_legacy.py

**Status**: ⚠️ INCOMPATIBLE - DO NOT USE

**Original Purpose**: Comprehensive tests for NUGovern HTTP API v0.x

**Why It Can't Be Used**:

These tests were written for the original v0.x API which had **no authentication**. The current eBIOS API (v1.0+) requires **JWT authentication** for all operations except the health check endpoint.

### Specific Incompatibilities:

1. **Missing Authentication Headers**: Tests make requests without JWT tokens
   - Result: 403 Forbidden responses on all protected endpoints
   - Current API requires `Authorization: Bearer <token>` header

2. **Architectural Changes**:
   - v0.x: Public API, no auth required
   - v1.0+: JWT authentication + RBAC (admin, operator, auditor, guest roles)

3. **Test Failures**:
   - 19/22 tests fail with authentication errors
   - Only health check endpoint works without auth
   - All operation, ledger, policy, and monitor endpoints now require valid JWT tokens

### Replacement:

The authenticated v1.0.0 API is **fully tested** in:
- `tests/nugovern/test_api_v1.py` - **25/25 tests passing (100% coverage)**

This includes comprehensive testing of:
- JWT authentication (login, refresh)
- RBAC enforcement (all 4 roles)
- All operation endpoints with authentication
- Ledger queries with role-based access
- Batch operations
- Rate limiting
- Error handling

### Historical Reference:

This file is preserved for **historical reference only** to show the evolution from unauthenticated (v0.x) to authenticated (v1.0+) API architecture.

**Do not attempt to run these tests** - they are fundamentally incompatible with the current system.

---

## Migration Notes

If you need to test unauthenticated API behavior, you would need to:
1. Temporarily disable JWT requirements in server configuration
2. Remove `Depends(require_role(...))` from endpoint decorators
3. Update tests to match current response formats

However, this is **NOT RECOMMENDED** as it defeats the security architecture of eBIOS v1.0+.

## Current Test Status

- ✅ `test_api_v1.py`: 25/25 passing (100%) - Authenticated API
- ⚠️ `test_api_v0_legacy.py`: 19/22 failing - Legacy unauthenticated API (RETIRED)
- **Total Active Tests**: 197/197 passing (100%)
