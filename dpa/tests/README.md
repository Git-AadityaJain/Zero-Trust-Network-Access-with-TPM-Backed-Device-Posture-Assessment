# DPA Tests

This directory contains test files for the Device Posture Agent (DPA) module.

## Test Files

- `test_config.py` - Configuration tests
- `test_core.py` - Core functionality tests
- `test_enrollment.py` - Device enrollment tests
- `test_fingerprint.py` - Device fingerprinting tests
- `test_posture.py` - Posture collection tests
- `test_posture_scheduler.py` - Posture scheduler tests
- `test_posture_submission.py` - Posture submission tests
- `test_secrets.py` - Secret storage tests
- `test_signing.py` - Signing functionality tests
- `test_tpm.py` - TPM integration tests
- `test_integration.py` - Basic integration tests
- `test_integration_complete.py` - Complete integration test suite

## Running Tests

### Individual Test
```bash
# Run a specific test
python dpa/tests/test_enrollment.py
```

### All DPA Tests
```bash
# From project root
python -m pytest dpa/tests/

# Or using unittest
python -m unittest discover -s dpa/tests -p "test_*.py"
```

### Integration Tests
```bash
# Run integration tests
python dpa/tests/test_integration_complete.py
```

## Test Requirements

Make sure you have installed the DPA requirements:
```bash
pip install -r dpa/requirements.txt
```

## Note

Backend-specific tests are located in `backend/tests/`:
- `test_all_endpoints.py` - API endpoint tests
- `test_data.py` - Test data fixtures
- `test_signature.py` - Signature verification tests

