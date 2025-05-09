# Mocks for Testing

This directory contains mock implementations used for testing.

### Flexible Token Sources

The mock supports multiple sources for tokens, with a priority order:

1. **Local Development (not in CI):**

   - First tries to read from the real system keyring
   - Falls back to environment variables
   - Maintains an in-memory cache

2. **CI Environment:**
   - Reads only from environment variables
   - Never tries to access the real keyring

### Usage

The mock is automatically applied to all tests through a pytest fixture in `conftest.py`. It will retrieve tokens using the appropriate method based on the environment.

#### Available Token Contexts

The mock supports these token contexts:

- `bunny` - Uses the `BUNNY_API_KEY` environment variable or keyring
- `bunny_storage` - Uses the `BUNNY_STORAGE_API_KEY` environment variable or keyring
- `s3` - Uses the `AWS_ACCESS_KEY_ID` environment variable or keyring
- `linode` - Uses the `LINODE_API_KEY` environment variable or keyring

#### Local Development Setup

When developing locally, you can:

1. Store tokens in your system keyring:

   ```bash
   # Using the real CLI to store tokens
   buckia token set bunny
   ```

2. Or use environment variables, which can be loaded from a `.env` file:
   ```bash
   # .env file (don't check this into git!)
   BUNNY_API_KEY=your-api-key
   buckia.buckia.demo=your-storage-api-key
   ```

### How the Mocking Works

The pytest fixture uses monkeypatching to replace the real TokenManager implementation with our mock:

```python
@pytest.fixture(autouse=True)
def patch_token_manager(monkeypatch, mock_token_manager):
    # Create a mock module
    mock_module = MagicMock()
    mock_module.TokenManager = MockTokenManager

    # Replace the real module with our mock
    monkeypatch.setitem(sys.modules, "buckia.security", mock_module)
    monkeypatch.setitem(sys.modules, "buckia.security.token_manager", mock_module)

    # Make sure our mock is used when imported
    monkeypatch.setattr("buckia.security.TokenManager", MockTokenManager)
```

This ensures that any code importing or using `TokenManager` will get our mock implementation, while still preserving the ability to use real tokens securely during development.
