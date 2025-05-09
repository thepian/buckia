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
delete_orphaned: true
max_workers: 4
checksum_algorithm: sha256
```

**IMPORTANT:** Never commit this file to version control. It's added to `.gitignore`.

### 2. Setting Up GitHub Actions for CI

#### Secrets Configuration:

In your GitHub repository, add the following secrets:

- `BUNNY_API_KEY`: Your Bunny.net API key (under account settings)
- `buckia.buckia.demo`: Your Bunny.net Storage API key (under FTP & API Access)
- `PYPI_USERNAME`: Your PyPI username (for publishing)
- `PYPI_PASSWORD`: Your PyPI password or token (for publishing)

#### GitHub Actions Workflows:

The repository contains several GitHub Actions workflows:

1. **Unit Tests** (`.github/workflows/unit-tests.yml`)

   - Runs all unit tests
   - Triggered on pushes to main and pull requests
   - Runs on multiple Python versions (3.9, 3.10, 3.11, 3.12)
   - Uses UV for dependency management

2. **Integration Tests** (`.github/workflows/integration-tests.yml`)

   - Runs integration tests against real storage providers
   - Triggered on pushes to main and pull requests
   - Requires secrets for authentication with storage providers
   - Includes options for running extended test suites

3. **Linting** (`.github/workflows/lint.yml`)

   - Runs code quality checks (black, isort, flake8, mypy)
   - Ensures code style consistency
   - Triggered on pushes to main and pull requests
   - Complements the local pre-commit hook that runs Black

4. **Publishing** (`.github/workflows/publish.yml`)
   - Builds and publishes package to PyPI
   - Triggered when a tag matching v\* is pushed (e.g., v1.0.0)
   - Uses PYPI_USERNAME and PYPI_PASSWORD secrets

#### Using UV in GitHub Actions

All workflows use UV (https://github.com/astral-sh/uv) instead of pip for package management. Here's why:

**Benefits of Using UV in CI:**

- **Faster Dependency Resolution**: UV resolves dependencies 10-100x faster than pip, reducing setup time
- **Better Caching**: UV's caching system is more efficient, leading to higher cache hit rates between runs
- **Consistency**: Using the same package manager in CI as in local development ensures reproducibility
- **Lockfile Precision**: UV handles lockfiles better, ensuring consistent dependencies across environments

**Practical Performance Impact:**

- 20-40% faster dependency resolution steps
- 5-15% reduction in total CI time (most time is spent running tests, not installing dependencies)
- Greatest benefits seen in projects with complex dependency trees and matrix testing

**Tradeoffs:**

- Small overhead for installing UV itself (~5-10 seconds)
- For very simple projects, benefits may be minimal

For Buckia, UV provides a good balance of speed, consistency, and future-proofing as the project grows.

## Running Integration Tests

### Locally:

```bash
# Run all integration tests
uv run -m pytest tests/integration

# Run specific test categories
uv run -m pytest tests/integration/test_bunny.py
uv run -m pytest tests/integration/test_operations.py
uv run -m pytest tests/integration/test_sync.py

# Run with detailed output
uv run -m pytest tests/integration -v
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

- [x] Create integration test directory structure
- [x] Set up pytest fixtures for Bunny.net testing
- [x] Implement test file generation utilities
- [x] Add tests for basic file operations
- [x] Add tests for synchronization functionality
- [x] Add tests for error handling
- [x] Create GitHub Actions workflow
- [x] Document test coverage and results
- [x] Implement cleanup procedures for test data
- [x] Set up publishing workflow to PyPI
- [x] Configure workflow to use UV for dependency management

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
