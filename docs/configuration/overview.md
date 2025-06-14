# Buckia Configuration Overview

The `.buckia` configuration file is the central control point for all Buckia operations. It defines storage providers, sync behavior, PDF generation settings, and bucket organization.

## Configuration File Formats

Buckia supports multiple configuration file formats:

- **`.buckia`** - YAML format (most common)
- **`.buckia.yaml`** - YAML format (explicit)
- **`.buckia.toml`** - TOML format

## Configuration File Location

Buckia searches for configuration files in this order:

1. **Current directory**: `./.buckia`, `./.buckia.yaml`, or `./.buckia.toml`
2. **Specified path**: `--config path/to/config`
3. **User home**: `~/.buckia/config.yaml`

## Basic Structure

**Important**: The configuration file must define at least one bucket. Without buckets, the configuration is useless and Buckia cannot operate.

### YAML Format (.buckia or .buckia.yaml)

```yaml
# Bucket name can be anything descriptive
my-dev-storage:
  provider: bunny
  bucket_name: actual-bucket-name
  token_context: demo
  paths:
    - "dist/"
  delete_orphaned: false

my-prod-storage:
  provider: bunny
  bucket_name: prod-bucket-name
  token_context: prod
  paths:
    - "dist/"
  delete_orphaned: true
```

### TOML Format (.buckia.toml)

```toml
[my-dev-storage]
provider = "bunny"
bucket_name = "actual-bucket-name"
token_context = "demo"
paths = ["dist/"]
delete_orphaned = false

[my-prod-storage]
provider = "bunny"
bucket_name = "prod-bucket-name"
token_context = "prod"
paths = ["dist/"]
delete_orphaned = true
```

## Multiple Buckets (Any Number)

You can define any number of buckets with descriptive names:

```yaml
# YAML format - any bucket names you want
namespace: myproject

demo-storage:
  provider: bunny
  bucket_name: myproject-demo
  domain: storage.bunnycdn.net
  region: eu
  token_context: demo

  # Folder-based organization
  folders:
    - 2siEySuKO1wK4XiJHWQ0YxhLxd2

  # Bidirectional sync
  paths:
    - demo/ # Downloads from bucket
    - static/data/ # Uploads to bucket

  delete_orphaned: true
  max_workers: 8
  checksum_algorithm: sha256
  conflict_resolution: local_wins

cdn-assets:
  provider: bunny
  bucket_name: myproject-cdn
  token_context: cdn
  paths:
    - "whitepapers/"
  pdf:
    base_url: "https://cdn.myproject.com"
    path_template: "{id}/{name}"

user-backups:
  provider: s3
  bucket_name: myproject-backups
  token_context: backup
  region: us-east-1
  paths:
    - "backups/"
```

## Core Configuration Sections

### 1. Provider Settings

- **provider**: Storage provider (`bunny`, `s3`, `b2`)
- **bucket_name**: Target bucket/container name
- **token_context**: Credential context in keyring
- **region**: Provider-specific region (S3, Bunny)
- **domain**: Custom domain for Bunny CDN

### 2. Sync Configuration

- **paths**: Local directories to sync
- **folders**: Remote bucket folders to target
- **delete_orphaned**: Remove remote files not in local
- **max_workers**: Concurrent upload threads
- **conflict_resolution**: How to handle conflicts

### 3. Advanced Features

- **PDF generation**: HTML-to-PDF with cloud upload
- **Namespace**: Project organization
- **Provider settings**: Custom provider options

## Configuration Patterns

### Development Workflow

```yaml
# Bucket names can be anything descriptive
development:
  provider: bunny
  bucket_name: myproject-dev
  token_context: dev
  delete_orphaned: false # Safe for development
  max_workers: 4

staging-env:
  provider: bunny
  bucket_name: myproject-staging
  token_context: staging
  delete_orphaned: true # Moderate sync
  max_workers: 6

production:
  provider: bunny
  bucket_name: myproject-prod
  token_context: prod
  delete_orphaned: true # Full sync
  max_workers: 8
```

### Content Management

```yaml
# Descriptive bucket names for different purposes
static-assets:
  provider: bunny
  bucket_name: assets-bucket
  token_context: assets
  paths:
    - "dist/assets/"
    - "dist/images/"

document-generation:
  provider: bunny
  bucket_name: docs-bucket
  token_context: docs
  paths:
    - "whitepapers/"
  pdf:
    base_url: "https://cdn.example.com"
    path_template: "{id}/{name}"
```

### Team Isolation

```yaml
namespace: recordthing

# Any bucket names work - these are just examples
team-alpha-storage:
  provider: bunny
  bucket_name: recordthing-alpha
  token_context: team-alpha
  folders:
    - user123
    - user456

team-beta-storage:
  provider: bunny
  bucket_name: recordthing-beta
  token_context: team-beta
  folders:
    - user789
    - user012
```

## Next Steps

- **[Basic Configuration](basic.md)**: Simple single-bucket setup
- **[Multi-Bucket Setup](multi-bucket.md)**: Managing multiple environments
- **[Team Organization](teams.md)**: Namespace and folder management
- **[Provider Settings](providers.md)**: Provider-specific configuration
- **[PDF Generation](pdf.md)**: HTML-to-PDF with cloud upload
- **[Sync Behavior](sync.md)**: Advanced sync options
- **[Security](security.md)**: Credential management and access control

## Migration Guide

**Important**: Buckia requires at least one bucket to be defined. The old "single bucket" format is not supported - you must always define named buckets.

### Creating Your First Configuration

**Minimum viable configuration:**

```yaml
# .buckia file - must have at least one bucket
my-storage:
  provider: bunny
  bucket_name: actual-bucket-name
  token_context: demo
```

### Adding Multiple Buckets

```yaml
# .buckia file - any number of buckets with any names
development:
  provider: bunny
  bucket_name: myproject-dev
  token_context: dev

production:
  provider: bunny
  bucket_name: myproject-prod
  token_context: prod

cdn-assets:
  provider: s3
  bucket_name: myproject-cdn
  token_context: cdn
  region: us-east-1
```

### Adding Team Organization

```yaml
# .buckia file with namespace
namespace: myproject

team-storage:
  provider: bunny
  bucket_name: myproject-team
  token_context: team
  folders:
    - main-content
    - user-data
```

## Best Practices

1. **Use descriptive bucket names** that include project/team identifiers
2. **Organize by environment** (dev, staging, prod)
3. **Set appropriate worker counts** based on bandwidth
4. **Use conflict resolution** that matches your workflow
5. **Test with delete_orphaned: false** before enabling deletion
6. **Secure credentials** using system keyring
7. **Document team folder structure** for collaboration
