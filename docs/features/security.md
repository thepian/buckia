# Secure API Token Management with Keyring Integration

## Overview

This document outlines the approach for securely managing API tokens and token IDs in Buckia with keyring integration support. Instead of storing sensitive API tokens or user identifiers directly in config files, Buckia uses the system's secure credential storage (via keyring) to protect both API tokens and token IDs.

## Token Management Architecture

Buckia implements a secure token management system that:

1. Stores API tokens and token IDs in the system's secure credential storage (keychain on macOS, libsecret on Linux, credential manager on Windows)
2. Supports biometric authentication (when available on the platform)
3. Falls back to environment variables when keyring is unavailable
4. Keeps sensitive credentials out of configuration files
5. Provides a consistent CLI interface for managing tokens and token IDs
6. Allows user identification through token IDs separate from API tokens

## Keyring Integration

### Token Storage Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  Config     │────▶│  TokenMgr   │────▶│  Keyring    │
│  (no creds) │     │  (retrieves)│     │  (stores)   │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Authentication Methods

1. **Keyring with Biometric**

   - macOS: Touch ID integration through LocalAuthentication framework
   - Linux: Fingerprint or polkit integration
   - Windows: Windows Hello integration

2. **Keyring with Password Fallback**
   - Password verification when biometrics unavailable
   - System credential storage protection

## Environment Variable Support

For environments where keyring is not available or for CI/CD pipelines, Buckia supports using environment variables as an alternative to keyring storage. Environment variables follow these naming conventions:

For API tokens:

```
buckia_<namespace>_<context>   # Lowercase
BUCKIA_<NAMESPACE>_<CONTEXT>   # Or uppercase
```

For token IDs:

```
buckia_<namespace>_<context>_id   # Lowercase
BUCKIA_<NAMESPACE>_<CONTEXT>_ID   # Or uppercase
```

For example:

- `buckia_buckia_test` or `BUCKIA_BUCKIA_TEST`: API key for Bunny.net
- `buckia_buckia_test_id` or `BUCKIA_BUCKIA_TEST_ID`: User ID for Bunny.net authentication
- `buckia_buckia_long_term` or `BUCKIA_BUCKIA_LONG_TERM`: Storage API key for Bunny.net demo context
- `buckia_buckia_long_term_id` or `BUCKIA_BUCKIA_LONG_TERM_ID`: Application Key ID for Backblaze B2 demo context
- `buckia_buckia_s3` or `BUCKIA_BUCKIA_S3`: AWS S3 API key
- `buckia_buckia_s3_id` or `BUCKIA_BUCKIA_S3_ID`: User ID for AWS S3 authentication

The system will first check for the lowercase version of the environment variable, and if not found, will try the uppercase version. This allows for compatibility with different environment setups that may enforce uppercase naming conventions.

When a token is requested, Buckia will:

1. First try to retrieve it from the system keyring
2. If keyring retrieval fails, check for an appropriate environment variable
3. Use the token if found in either location

This approach is particularly useful for:

- CI/CD pipelines where keyring access isn't available
- Containerized environments
- Testing and development scenarios

## CLI Commands for Token Management

Buckia provides a set of commands to manage API tokens and token IDs securely:

### Save a Token

```bash
# Will prompt securely for the token value
buckia token set demo

# Provide token directly (less secure)
uv run buckia token set buckia_demo --token "your-api-key"
uv run buckia token set buckia_demo_id --token "your-api-key-id"

# Save a token for a custom service
uv run uv run buckia token set custom-provider
```

### Save a Token ID

```bash
# Will prompt securely for the token ID value
buckia token-id set bunny

# Provide token ID directly (less secure)
buckia token-id set bunny --id "your-user-id"
```

### Save Both Token and Token ID Together

```bash
# Will prompt securely for both values
buckia token set-with-id bunny

# Provide values directly (less secure)
buckia token set-with-id bunny --token "your-api-key" --id "your-user-id"
```

### Retrieve a Token

```bash
# Will attempt biometric authentication on supported platforms
buckia token get bunny
```

This command will:

- Try to use Touch ID/biometric authentication on supported platforms
- Fall back to password verification if biometrics are not available
- Print the token if authentication succeeds

### Retrieve a Token ID

```bash
# Will attempt biometric authentication on supported platforms
buckia token-id get bunny
```

### Retrieve Both Token and Token ID

```bash
# Will attempt biometric authentication on supported platforms
buckia token get-with-id bunny
```

### List Available Tokens

```bash
buckia token list
```

### Delete a Token

```bash
buckia token delete bunny
```

### Delete a Token ID

```bash
buckia token-id delete bunny
```

## Integration with Configuration

The `.buckia` configuration file does NOT contain API tokens. Instead, it references which token should be used:

```yaml
provider: bunny
bucket_name: example-bucket
region: de
token_service: bunny # References the token name in keyring, defaults to provider
paths:
  - path/to/sync
delete_orphaned: false
max_workers: 4
```

When tokens are not in the config file, Buckia will:

1. Check if the token service is specified (defaults to provider name)
2. Look up the token in the system keyring
3. Prompt for authentication if needed
4. Use the token for the operation

## Implementation Details

### Token Manager

Buckia uses a `TokenManager` class to handle secure token storage and retrieval for both API tokens and token IDs:

```python
from buckia.security import TokenManager

# Initialize the token manager
token_manager = TokenManager()

# Get a token with authentication
api_key = token_manager.get_token("bunny")
if api_key:
    # Use the API key
    ...
else:
    # Handle authentication failure
    ...

# Get a token ID with authentication
token_id = token_manager.get_token_id("bunny")
if token_id:
    # Use the token ID for user identification
    ...
else:
    # Handle authentication failure
    ...

# Get both token and token ID together
token, token_id = token_manager.get_token_with_id("bunny")
if token and token_id:
    # Use both for authentication and identification
    ...
else:
    # Handle authentication failure
    ...

# Save a token ID
token_manager.save_token_id("bunny", "your-user-id")

# Save both token and token ID together
token_manager.save_token_with_id("bunny", "your-api-key", "your-user-id")

# Delete a token ID
token_manager.delete_token_id("bunny")
```

### Client Integration

The `BuckiaClient` will automatically use the token manager when API credentials are not provided directly:

```python
from buckia.client import BuckiaClient
from buckia.config import BucketConfig

# Load config without credentials
config = BucketConfig.from_file(".buckia")

# Client will attempt to get credentials from token manager
client = BuckiaClient(config)
```

### Backend-Specific Credential Management

Different storage backends may use different credential fields. For example, Backblaze B2 requires both an application key and an application key ID:

```python
# B2 backend uses token for application_key and token_id for application_key_id
from buckia.security import TokenManager

token_manager = TokenManager()
token_manager.save_token("b2", "YOUR_APPLICATION_KEY")
token_manager.save_token_id("b2", "YOUR_APPLICATION_KEY_ID")

# When you create a client for B2, it will automatically retrieve both
from buckia.client import BuckiaClient
from buckia.config import BucketConfig

config = BucketConfig(provider="b2", bucket_name="my-bucket", token_context="b2")
client = BuckiaClient(config)
```

You can also specify the application_key_id directly in your configuration:

```yaml
provider: b2
bucket_name: my-b2-bucket
provider_settings:
  application_key_id: 001234567890abcdef0123456
```

## Security Considerations

1. **Token Storage**

   - Always use system keychains when available
   - Fall back to environment variables if keyring is unavailable
   - Environment variables follow the format `buckia_<namespace>_<context>` or `BUCKIA_<NAMESPACE>_<CONTEXT>` for tokens
   - And `buckia_<namespace>_<context>_id` or `BUCKIA_<NAMESPACE>_<CONTEXT>_ID` for token IDs
   - Never store tokens or token IDs in plain text configuration files

2. **Authentication**

   - Prefer biometric when available
   - Use password verification as fallback
   - Implement proper session management

3. **Transport Security**

   - All API communications use HTTPS
   - Validate server certificates
   - Connection testing validates credentials

4. **Audit Trail**
   - Log authentication attempts (success/failure)
   - Track token usage
   - Token refresh and rotation support

## Implementation Roadmap

1. **Phase 1: Core Integration**

   - ✅ Implement TokenManager with keyring integration
   - ✅ Implement token ID support in TokenManager
   - ✅ Implement B2 backend with token ID (application_key_id) support
   - Update Config class to support token service references
   - Integrate TokenManager with BuckiaClient
   - Add CLI commands for token and token ID management

2. **Phase 2: Enhanced Security**

   - Improve biometric authentication on all platforms
   - Add token rotation support
   - Implement session management
   - Add support for token ID verification

3. **Phase 3: Advanced Features**
   - Support for token sharing between related services
   - Multi-factor authentication options
   - Token permissions and scopes
   - Role-based token ID management
