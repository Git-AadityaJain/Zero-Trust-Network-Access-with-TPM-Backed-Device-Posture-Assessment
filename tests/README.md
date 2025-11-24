# Integration Tests

This directory is for project-wide integration tests (if any).

## Test Organization

### DPA Tests
DPA-specific tests are located in `dpa/tests/`:
- Configuration, core, enrollment, fingerprint, posture, and TPM tests
- See `dpa/tests/README.md` for details

### Backend Tests
Backend-specific tests are located in `backend/tests/`:
- `test_all_endpoints.py` - API endpoint tests
- `test_data.py` - Test data fixtures
- `test_signature.py` - Signature verification tests

### Keycloak Verification
Keycloak verification script is located in `backend/scripts/verify_keycloak.py`

