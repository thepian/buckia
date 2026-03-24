# Python API Reference

Buckia provides a simple, consistent Python API for all storage providers.

## Installation

```bash
# Basic installation
pip install buckia

# Install with specific provider support
pip install 'buckia[bunny]'   # Bunny.net
pip install 'buckia[s3]'      # AWS S3
pip install 'buckia[linode]'  # Linode Object Storage

# All providers + development tools
pip install 'buckia[bunny,s3,linode,dev]'

# Development installation (editable)
uv tool install --editable --force .
```

## Core Classes

### BucketConfig

```python
from buckia import BucketConfig

config = BucketConfig(
    provider="bunny",       # bunny | s3 | linode | b2
    bucket_name="my-bucket",
    credentials={...}       # Provider-specific credentials
)
```

### BuckiaClient

```python
from buckia import BuckiaClient, BucketConfig

config = BucketConfig(provider="bunny", bucket_name="my-bucket")
client = BuckiaClient(config)
```

## Sync Operations

### Basic Local to Remote Sync

```python
from buckia import BuckiaClient, BucketConfig

config = BucketConfig(
    provider="bunny",
    bucket_name="my-storage-zone"
)

client = BuckiaClient(config)
result = client.sync(
    local_path="./assets",
    delete_orphaned=True
)
```

### Advanced Sync with Options

```python
from buckia import BuckiaClient, BucketConfig

config = BucketConfig(
    provider="s3",
    bucket_name="my-bucket",
    region="us-west-2"
)

client = BuckiaClient(config)
result = client.sync(
    local_path="./project",
    max_workers=8,
    delete_orphaned=True,
    include_pattern=r".*\.(jpg|png|gif)$",
    exclude_pattern=r"^\..*",   # Exclude hidden files
    dry_run=False,
    sync_paths=["images/", "documents/important.pdf"]
)
```

### Progress Reporting

```python
def report_progress(current, total, action, path):
    percent = int(current * 100 / total) if total > 0 else 0
    print(f"{action.capitalize()}: {current}/{total} ({percent}%) - {path}")

client.sync(
    local_path="./project",
    progress_callback=report_progress
)
```

### Sync Result

```python
result = client.sync(local_path="./assets")
print(f"Uploaded: {result.uploaded}")
print(f"Downloaded: {result.downloaded}")
print(f"Deleted: {result.deleted}")
print(f"Errors: {result.errors}")
```

## Multi-Bucket Configuration

Buckia supports a multi-config structure — one config file with multiple named buckets:

```python
from buckia import BuckiaClient, BucketConfig

# Load from .buckia config file (multi-bucket format)
client = BuckiaClient.from_config(".buckia", bucket="production")
result = client.sync(local_path="./dist", delete_orphaned=True)
```

See the [Configuration Overview](configuration/overview.md) for the `.buckia` file format.

## Token Management

```python
from buckia.security import TokenManager

token_manager = TokenManager()

# Save a token
token_manager.save_token("bunny", "your-api-key")

# Retrieve a token
token = token_manager.get_token("bunny")

# List available contexts
contexts = token_manager.list_bucket_contexts()

# Delete a token
token_manager.delete_token("bunny")
```

## See Also

- [Configuration Overview](configuration/overview.md) — `.buckia` file format
- [Sync Features](features/sync.md) — upload-only, create-only patterns, state cache
- [CLI Reference](cli/overview.md) — command-line usage
- [Swift API](mobile/swift.md) — iOS/macOS native API
