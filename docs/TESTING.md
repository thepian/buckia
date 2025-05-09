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

# Show all token-related environment variables at the start of the test session
uv run -m pytest --show-env-vars
```

#### Debugging Token Environment Variables

For debugging token-related issues, you can use the following approaches:

1. Use the `--show-env-vars` flag to see all token-related environment variables:

```bash
uv run -m pytest --show-env-vars
```

This will display:

- Which environment variables are found/missing
- Whether a .env file was detected
- A summary of available tokens

2. Manually check for required environment variables:

```bash
# Check if a specific token is available
echo $buckia.buckia.bunny

# List all buckia-related environment variables
env | grep buckia
```

When running integration tests, the output will show which environment variables are missing, helping you to identify configuration issues.

## Test Configuration

### Configuration File

Tests use a configuration file located at `tests/config/test_config.yaml` by default.

Edit this file to include your provider-specific credentials.

### Environment Variables and API Token Management

The tests now use the actual TokenManager implementation which retrieves tokens from environment variables. The naming convention for environment variables follows the pattern:

```
buckia.<namespace>.<context>
```

For integration tests, the following environment variable is REQUIRED:

- `buckia.buckia.demo`: API key for integration tests (currently bunny.net API key)

All integration tests use the fixed token context "demo" for consistency. Additional provider-specific variables:

- `BUNNY_STORAGE_ZONE`: Storage zone name for Bunny.net
- `RUN_INTEGRATION_TESTS`: Set to "1" to enable integration tests

Other token contexts (not currently used in tests):

- `buckia.buckia.bunny`: API key for Bunny.net
- `buckia.buckia.bunny_storage`: Storage API key for Bunny.net
- `buckia.buckia.s3`: AWS S3 access key
- `buckia.buckia.linode`: Linode object storage token

#### Using .env Files (Recommended for Local Development)

For local development, you can create a `.env` file in the project root with your API tokens, following the naming convention:

```bash
# Create a .env file (not checked into version control)
cat > .env << EOF
# Required for all integration tests (currently using bunny.net API key)
buckia.buckia.demo=your-bunny-api-key

# Storage zone configuration
BUNNY_STORAGE_ZONE=your-storage-zone

# Enable integration tests
RUN_INTEGRATION_TESTS=1
EOF
```

The test fixtures will automatically load variables from this file when running integration tests. This approach keeps sensitive credentials out of your configuration files and test code.

#### No Interactive Prompts During Tests

IMPORTANT: The TokenManager NEVER prompts for authentication during integration tests. It relies solely on:

1. Environment variables (preferred)
2. Keyring without authentication (fallback)

If the required environment variables are missing, integration tests should clearly indicate which variables are needed, not prompt for them. This is critical for both:

- CI/CD pipelines where environment variables are set as GitHub Actions secrets
- Local development where variables come from .env files

Integration tests will report missing variables with clear error messages to help diagnose configuration issues. This non-interactive behavior is intentional and should be maintained throughout all test code.

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
