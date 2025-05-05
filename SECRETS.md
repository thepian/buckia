# Secure Credentials Management for Buckia

This document explains how to securely manage credentials for Buckia integration tests and CI processes.

## Local Development

For local development, credentials should be stored in a configuration file that is not committed to version control.

### Setting Up Local Credentials

1. Copy the example configuration file:
   ```bash
   cp tests/config/test_config.yaml.example tests/config/test_config.yaml
   ```

2. Edit `test_config.yaml` with your real API credentials:
   ```yaml
   provider: bunny
   bucket_name: your-test-storage-zone
   auth:
     api_key: your-api-key
     storage_api_key: your-storage-api-key
   ```

3. Ensure this file is in your `.gitignore` to prevent accidental commits:
   ```
   # .gitignore
   tests/config/test_config.yaml
   ```

## GitHub Actions CI

For GitHub Actions, we use repository secrets to securely store credentials.

### Setting Up GitHub Secrets

1. Go to your GitHub repository settings
2. Navigate to "Secrets" → "Actions"
3. Add the following secrets:
   - `BUNNY_API_KEY`: Your Bunny.net API key
   - `BUNNY_STORAGE_ZONE`: Name of your test storage zone
   - `BUNNY_STORAGE_API_KEY`: Your Bunny.net Storage API key

### Using Secrets in Workflows

These secrets are automatically used in the GitHub Actions workflow file:

```yaml
# .github/workflows/integration-tests.yml
env:
  BUNNY_API_KEY: ${{ secrets.BUNNY_API_KEY }}
  BUNNY_STORAGE_ZONE: ${{ secrets.BUNNY_STORAGE_ZONE }}
  BUNNY_STORAGE_API_KEY: ${{ secrets.BUNNY_STORAGE_API_KEY }}
```

## Test Storage Zone Setup

For testing, we recommend creating a dedicated storage zone in your Bunny.net account. This helps isolate testing from production data and provides a clean testing environment.

### Storage Zone Requirements

1. Create a new storage zone in your Bunny.net account
2. Grant it the following permissions:
   - Read/Write access 
   - File listing capabilities
3. Generate a storage-zone-specific API key for more restricted access

### Security Guidelines

1. Never use production API keys for testing
2. Limit the permissions of test API keys
3. Rotate API keys regularly
4. Consider using a separate Bunny.net account for testing
5. Monitor the activity on your test storage zone

## Environment Variables

As an alternative to config files, you can use environment variables:

```bash
export BUNNY_API_KEY=your-api-key
export BUNNY_STORAGE_ZONE=your-storage-zone
export BUNNY_STORAGE_API_KEY=your-storage-api-key
```

The test fixtures in `conftest.py` will automatically use these environment variables if no configuration file is found.

## Running Tests with Different Credentials

You can specify a different configuration file using the `--config` option:

```bash
pytest tests/integration --config=/path/to/other/config.yaml
```

This is helpful for testing against different environments or storage zones.