# Security Module Tests

This directory contains comprehensive tests for all security modules in the AI Log Platform integration.

## Test Files

- `test_security_identity_governance.py` - Tests for Identity Governance Agent (IGA)
- `test_security_threat_vector.py` - Tests for Threat Vector Agent (TVA)
- `test_security_correlation_rca.py` - Tests for Correlation & RCA Agent (CRA)
- `test_security_persona_baseline.py` - Tests for Persona Baseline Agent (PBA)
- `test_security_soar_automation.py` - Tests for SOAR Automation Agent (SAA)
- `test_security_threat_detection.py` - Tests for Threat Detection Service (NATS integration)

## Running Tests

### Using Makefile (Recommended)

All tests run in Docker containers to ensure consistent environment:

```bash
# Run all tests
make test

# Run all security module tests
make test-security

# Run tests for specific agent
make test-iga    # Identity Governance Agent
make test-tva    # Threat Vector Agent
make test-cra    # Correlation & RCA Agent
make test-pba    # Persona Baseline Agent
make test-saa    # SOAR Automation Agent
make test-threat-detection  # Threat Detection Service

# Run with coverage
make test-coverage
```

### Running Locally

If you have Python environment set up:

```bash
cd tests
python -m pytest -v test_security_*.py
```

## Test Structure

Each test file follows this structure:

1. **Fixtures**: Set up test database, organizations, and service instances
2. **Service Tests**: Test core service methods
3. **Integration Tests**: Test interactions between services
4. **Edge Cases**: Test error handling and boundary conditions

## Dependencies

Tests require:
- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0` (for async tests)
- `pytest-cov>=4.1.0` (for coverage)
- `pytest-mock>=3.11.0` (for mocking)

All dependencies are installed in the Docker backend container.

## Notes

- Tests use SQLite in-memory database for speed
- Neo4j and NATS are mocked in unit tests
- Integration tests can be run separately with `make test-integration`
- Coverage reports are generated in `htmlcov/` directory

