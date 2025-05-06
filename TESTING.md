# Buckia Testing Guide

This document provides instructions for testing the Buckia library, including running the test suite, customizing test behavior, and troubleshooting common issues.

## Running Tests

### Test Commands

```bash
# Run all tests
uv run scripts/run_tests.sh

# Run only unit tests
uv run scripts/run_tests.sh tests/unit

# Run integration tests
uv run -m pytest tests/integration/

# Run specific test file
uv run -m pytest tests/integration/test_operations.py

# Run specific test
uv run -m pytest tests/integration/test_operations.py::test_file_upload_download

# Test with coverage
uv run -m pytest --cov=buckia
```

### Test Options

Several command-line options are available to customize test behavior:

```bash
# Use a custom test configuration file
uv run -m pytest --config=path/to/config.yaml

# Skip cleaning up test data (useful for debugging)
uv run -m pytest --skip-cleanup

# Preserve remote files and directories for debugging
uv run -m pytest --preserve-remote
```

## Test Configuration

### Configuration File

Tests use a configuration file located at `tests/config/test_config.yaml` by default. You can create this file based on the provided example:

```bash
cp tests/config/test_config.yaml.example tests/config/test_config.yaml
```

Edit this file to include your provider-specific credentials.

### Environment Variables

You can also configure tests using environment variables:

- `BUNNY_API_KEY`: API key for Bunny.net tests
- `BUNNY_STORAGE_API_KEY`: Storage API key for Bunny.net
- `BUNNY_STORAGE_ZONE`: Storage zone name for Bunny.net
- `RUN_INTEGRATION_TESTS`: Set to "1" to enable integration tests

## Test Types

### Unit Tests

Unit tests in the `tests/unit/` directory test individual components in isolation using mocks. These tests don't require actual credentials and run quickly.

### Integration Tests

Integration tests in the `tests/integration/` directory test actual interactions with cloud storage providers. These tests require valid credentials for the corresponding providers.

## Common Test Files

- **test_operations.py**: Tests basic file operations (upload, download, list, delete)
- **test_sync.py**: Tests directory synchronization functionality
- **test_error_handling.py**: Tests error handling and edge cases

## Debug and Troubleshooting

### Preserving Test Files

Use the `--preserve-remote` flag to keep remote files and directories after tests, allowing you to inspect them for debugging:

```bash
uv run -m pytest tests/integration/test_sync.py::test_sync_dry_run --preserve-remote
```

### Remote Test Prefixes

Each test uses a unique remote prefix for its files in the format `buckia_test_{uuid}_{test_hash}`. This allows multiple test runs to operate in parallel without conflicts.

The test output will show the exact prefix used for each test, for example:

```
Test 'test_sync_dry_run' using remote prefix: buckia_test_abcd1234_5678
```

You can use this prefix to manually examine or clean up test files if needed.

### Logging

Tests use Python's logging system, with output displayed during test execution. For more verbose output, run pytest with the `-v` flag:

```bash
uv run -m pytest -v tests/integration/test_sync.py
```