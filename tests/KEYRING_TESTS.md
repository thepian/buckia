# Testing with Keyring Integration

Buckia uses the keyring library to store sensitive API tokens securely. The tests are designed to work with this approach using an enhanced mock TokenManager that supports both local development and CI environments.

## Setup for Integration Tests

There are multiple ways to provide API tokens for testing:

### 1. Use the System Keyring (Local Development)

When developing locally, you can store your tokens in the system keyring:

```bash
# Use the real Buckia CLI to store tokens
buckia token set bunny
buckia token set bunny_storage  # If using separate storage API key
```

The test mock will automatically retrieve these tokens from your keyring when running tests locally.

### 2. Environment Variables

Set these environment variables before running tests:

```bash
# For Bunny.net tests
export BUNNY_API_KEY=your-api-key
export BUNNY_STORAGE_API_KEY=your-storage-api-key  # Optional
export BUNNY_STORAGE_ZONE=your-storage-zone-name

# For S3 tests
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export S3_BUCKET_NAME=your-bucket-name

# For Linode tests
export LINODE_API_KEY=your-linode-api-key
export LINODE_BUCKET_NAME=your-bucket-name
```

You can also place these in a `.env` file in the project root, which will be loaded automatically. The test framework will always load variables from .env, overriding existing environment variables.

Example `.env` file:

```
BUNNY_API_KEY=my-api-key-here
BUNNY_STORAGE_ZONE=my-storage-zone
RUN_INTEGRATION_TESTS=1
```

**Important: Don't check your .env file into git! Add it to your .gitignore to prevent accidental commits.**

Additionally, you can enable integration tests explicitly:

```bash
export RUN_INTEGRATION_TESTS=1
```

### 3. Configuration File

Edit `test_config.yaml` to set your `token_context` and other configuration values. The configuration doesn't contain the actual tokens - those come from either the keyring or environment variables.

## Smart Mock TokenManager Behavior

The MockTokenManager used in tests has enhanced behavior compared to a simple mock:

1. **Environment Detection:**

   - Detects if running in CI environment (`CI=1`)
   - Uses appropriate token sources based on the environment

2. **Token Sources (Priority Order):**

   - **Local Development:**

     1. First tries the system keyring
     2. Falls back to environment variables if no token in keyring
     3. Maintains an in-memory cache for consistency during test runs

   - **CI Environment:**
     1. Only uses environment variables (never attempts keyring access)
     2. Caches tokens in memory during test run

3. **Authentication:**
   - Never prompts for authentication, even when using the real keyring
   - Has consistent behavior for testing

## Running Tests with Custom Configuration

You can specify a custom configuration file:

```bash
pytest --config=/path/to/custom-config.yaml

# Or, to run a specific test
pytest --config=/path/to/custom-config.yaml tests/integration/test_bunny.py
```

## Preserving Test Files

By default, tests clean up any files they create on the remote storage. If you need to debug an issue, you can preserve these files:

```bash
pytest --preserve-remote
```

Or skip cleanup entirely:

```bash
pytest --skip-cleanup
```

## Controlling Test Environment

To explicitly test CI behavior locally:

```bash
# Force CI behavior (only use environment variables, never keyring)
CI=1 pytest
```
