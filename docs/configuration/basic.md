# Basic Configuration

This guide covers setting up a simple `.buckia` configuration file with one bucket.

## File Formats

Buckia supports multiple configuration file formats:

- **`.buckia`** - YAML format (most common)
- **`.buckia.yaml`** - YAML format (explicit)
- **`.buckia.toml`** - TOML format

## Quick Start

**Important**: You must define at least one bucket. The bucket name (top-level key) can be anything descriptive.

### YAML Format (.buckia)

```yaml
# Bucket name can be anything you want
my-project-storage:
  provider: bunny
  bucket_name: actual-bucket-name
  token_context: demo
  paths:
    - "dist/"
  delete_orphaned: false
  max_workers: 4
```

### TOML Format (.buckia.toml)

```toml
[my-project-storage]
provider = "bunny"
bucket_name = "actual-bucket-name"
token_context = "demo"
paths = ["dist/"]
delete_orphaned = false
max_workers = 4
```

## Required Fields

### provider

The cloud storage provider to use:

- `bunny` - Bunny CDN Storage
- `s3` - Amazon S3
- `b2` - Backblaze B2

```yaml
provider: bunny
```

### bucket_name

The name of your storage bucket/container:

```yaml
bucket_name: my-project-storage
```

### token_context

The credential context name stored in your system keyring:

```yaml
token_context: demo
```

## Optional Fields

### paths

Local directories to sync (defaults to current directory):

```yaml
paths:
  - "dist/"
  - "assets/"
  - "uploads/"
```

### delete_orphaned

Whether to delete remote files not present locally:

```yaml
delete_orphaned: false # Safe default
# delete_orphaned: true  # Use with caution
```

### max_workers

Number of concurrent upload threads:

```yaml
max_workers: 4 # Good for most connections
# max_workers: 8  # For faster connections
# max_workers: 2  # For slower connections
```

### checksum_algorithm

Algorithm for file integrity verification:

```yaml
checksum_algorithm: sha256 # Default
# checksum_algorithm: md5   # Faster but less secure
```

### conflict_resolution

How to handle sync conflicts:

```yaml
conflict_resolution: local_wins # Default
# conflict_resolution: remote_wins
# conflict_resolution: newest_wins
# conflict_resolution: ask
```

## Provider-Specific Settings

### Bunny CDN

```yaml
# Bucket name can be anything
bunny-storage:
  provider: bunny
  bucket_name: my-storage-zone
  token_context: bunny_demo
  region: "" # Bunny doesn't use regions
```

### Amazon S3

```yaml
# Bucket name can be anything
s3-storage:
  provider: s3
  bucket_name: my-s3-bucket
  token_context: aws_demo
  region: us-east-1 # Required for S3
```

### Backblaze B2

```yaml
# Bucket name can be anything
b2-storage:
  provider: b2
  bucket_name: my-b2-bucket
  token_context: b2_demo
  provider_settings:
    application_key_id: "001234567890abcdef0123456"
```

## Setting Up Credentials

### 1. Install Buckia

```bash
pip install buckia
```

### 2. Store Credentials

```bash
# For Bunny CDN
buckia auth set bunny_demo --password "your-api-key"

# For AWS S3
buckia auth set aws_demo --username "access-key-id" --password "secret-access-key"

# For Backblaze B2
buckia auth set b2_demo --username "application-key-id" --password "application-key"
```

### 3. Test Configuration

```bash
# Test connection
buckia test-connection

# Dry run sync
buckia sync --dry-run
```

## Common Patterns

### Static Website

```yaml
# Bucket name can be anything
website-storage:
  provider: bunny
  bucket_name: my-website
  token_context: website
  paths:
    - "dist/"
  delete_orphaned: true
  max_workers: 6
```

### Asset Storage

```yaml
# Bucket name can be anything
asset-storage:
  provider: s3
  bucket_name: my-assets
  token_context: assets
  region: us-west-2
  paths:
    - "uploads/"
    - "media/"
  delete_orphaned: false
  max_workers: 4
```

### Backup Storage

```yaml
# Bucket name can be anything
backup-storage:
  provider: b2
  bucket_name: my-backups
  token_context: backup
  paths:
    - "backups/"
  delete_orphaned: false
  max_workers: 2
  provider_settings:
    application_key_id: "your-key-id"
```

## Usage Examples

### Sync Files

```bash
# Sync all configured paths
buckia sync

# Dry run to see what would be synced
buckia sync --dry-run

# Verbose output
buckia sync --verbose
```

### Check Status

```bash
# Show configuration
buckia config show

# Test connection
buckia test-connection

# Show sync status
buckia status
```

## Troubleshooting

### Common Issues

**Authentication Failed**

```bash
# Check stored credentials
buckia auth list

# Re-set credentials
buckia auth set your_context --password "new-password"
```

**Sync Failures**

```bash
# Check configuration
buckia config validate

# Test with dry run
buckia sync --dry-run --verbose
```

**Permission Errors**

- Ensure your API key has write permissions
- Check bucket/container exists
- Verify region settings for S3

### Getting Help

```bash
# Show all commands
buckia --help

# Show sync options
buckia sync --help

# Show configuration options
buckia config --help
```

## Next Steps

Once you have basic sync working:

1. **[Multi-Bucket Setup](multi-bucket.md)** - Manage multiple environments
2. **[PDF Generation](pdf.md)** - Add HTML-to-PDF capabilities
3. **[Team Organization](teams.md)** - Scale to team workflows
4. **[Advanced Sync](sync.md)** - Fine-tune sync behavior
