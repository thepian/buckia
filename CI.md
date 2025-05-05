# Buckia Integration Testing & CI

This document outlines the strategy and instructions for running integration tests against actual storage providers for the Buckia library, with a focus on Bunny.net storage.

## Integration Testing Strategy

### Goals

1. Verify Buckia functionality with real storage providers
2. Test all core operations (upload, download, delete, sync)
3. Validate error handling and edge cases
4. Provide repeatable, reliable tests that can run in CI environments

### Testing Environment

Tests will be performed against:

- Primary: Bunny.net Storage (requires a test storage zone)
- Future: AWS S3, Linode Object Storage

## Test Framework Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── integration/
│   ├── __init__.py
│   ├── test_bunny.py        # Bunny.net-specific tests
│   ├── test_operations.py   # Common file operations tests
│   └── test_sync.py         # Synchronization tests
└── unit/
    └── ...                  # Unit tests (existing)
```

## Setup Instructions

### 1. Local Development Setup

#### Prerequisites:

- Python 3.7+
- Bunny.net account with a test storage zone
- API keys with appropriate permissions

#### Installation:

```bash
# Clone the repository
git clone <repository-url>
cd buckia

# Install with development dependencies
uv pip install -e ".[dev,bunny]"

# Create test configuration
mkdir -p tests/config
```

#### Create Test Configuration:

Create a file at `tests/config/test_config.yaml` with the following structure:

```yaml
provider: bunny
bucket_name: your-test-storage-zone
auth:
  api_key: your-api-key
  storage_api_key: your-storage-api-key
sync:
  delete_orphaned: true
  max_workers: 4
checksum_algorithm: sha256
```

**IMPORTANT:** Never commit this file to version control. It's added to `.gitignore`.

### 2. Setting Up GitHub Actions for CI

#### Secrets Configuration:

In your GitHub repository, add the following secrets:

- `BUNNY_API_KEY`: Your Bunny.net API key (under account settings)
- `BUNNY_STORAGE_ZONE`: Name of your test storage zone
- `BUNNY_STORAGE_API_KEY`: Your Bunny.net Storage API key (under FTP & API Access)

#### GitHub Actions Workflow:

Create a file at `.github/workflows/integration-tests.yml` that runs the integration tests.

## Running Integration Tests

### Locally:

```bash
# Run all integration tests
pytest tests/integration

# Run specific test categories
pytest tests/integration/test_bunny.py
pytest tests/integration/test_operations.py
pytest tests/integration/test_sync.py

# Run with detailed output
pytest tests/integration -v
```

### In CI:

Integration tests will automatically run on:

- Pull requests to main branch
- Manual trigger via GitHub Actions

## Test Scope & Coverage

### Basic Operations Tests:

- File upload (single and batch)
- File download (single and batch)
- File deletion
- Listing files
- Getting public URLs

### Synchronization Tests:

- Basic sync (upload only)
- Bidirectional sync
- Deletion of orphaned files
- Path filtering
- Pattern filtering
- Dry run mode

### Error Handling Tests:

- Invalid credentials
- Network failures (simulated)
- File access issues
- Rate limiting

## TODO List

- [ ] Create integration test directory structure
- [ ] Set up pytest fixtures for Bunny.net testing
- [ ] Implement test file generation utilities
- [ ] Add tests for basic file operations
- [ ] Add tests for synchronization functionality
- [ ] Add tests for error handling
- [ ] Create GitHub Actions workflow
- [ ] Document test coverage and results
- [ ] Implement cleanup procedures for test data

## Best Practices

1. **Cleanup:** All tests should clean up after themselves
2. **Isolation:** Use unique prefixes for test files to avoid conflicts
3. **Credentials:** Never commit API keys or credentials to the repository
4. **Performance:** Batch operations where possible to reduce test runtime

## Implementation Notes

### Test Fixtures

Create reusable fixtures in `conftest.py` that handle:

- Test bucket configuration
- Temporary local files
- Cleanup procedures

### Test Data Generation

Create utilities for generating test files with:

- Various sizes (small, medium, large)
- Different content types (text, binary)
- Unique identifiers for tracking

### Testing Concurrency

Ensure tests for concurrent operations:
- Verify thread safety
- Test performance with different worker counts
- Handle race conditions properly