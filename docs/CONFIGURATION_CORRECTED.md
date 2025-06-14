# Buckia Configuration - Corrected Documentation

This document summarizes the corrected understanding of how Buckia configuration works.

## Key Corrections Made

### 1. Configuration File Format
**Corrected**: Buckia supports multiple file formats:
- `.buckia` (YAML format, most common)
- `.buckia.yaml` (YAML format, explicit)
- `.buckia.toml` (TOML format)

### 2. Configuration Structure
**Corrected**: The top-level keys are bucket names, which can be anything descriptive:

```yaml
# ✅ CORRECT - Bucket names can be anything
my-dev-storage:
  provider: bunny
  bucket_name: actual-bucket-name
  token_context: dev

production-cdn:
  provider: bunny
  bucket_name: prod-bucket-name
  token_context: prod

user-backups:
  provider: s3
  bucket_name: backup-bucket
  token_context: backup
  region: us-east-1
```

**Previously Incorrect**: Documentation showed single-bucket format or assumed specific naming patterns.

### 3. Minimum Requirements
**Corrected**: 
- At least one bucket MUST be defined
- Without buckets, the configuration is useless
- You can have any number of buckets with any names

```yaml
# ✅ MINIMUM VIABLE CONFIG
my-storage:
  provider: bunny
  bucket_name: actual-bucket-name
  token_context: demo
```

### 4. Bucket Naming
**Corrected**: 
- Top-level keys (bucket names in config) can be anything descriptive
- They are just identifiers for CLI usage
- The actual bucket name is specified in `bucket_name` field

```yaml
# ✅ CORRECT - Descriptive names
development-assets:
  bucket_name: myproject-dev-assets
  
production-cdn:
  bucket_name: myproject-prod-cdn
  
team-alpha-storage:
  bucket_name: recordthing-alpha
```

## Updated Examples

### Basic Single Bucket
```yaml
# .buckia file
website-storage:
  provider: bunny
  bucket_name: my-website
  token_context: website
  paths:
    - "dist/"
```

### Multiple Buckets
```yaml
# .buckia file
dev-storage:
  provider: bunny
  bucket_name: myproject-dev
  token_context: dev
  delete_orphaned: false

prod-storage:
  provider: bunny
  bucket_name: myproject-prod
  token_context: prod
  delete_orphaned: true

cdn-assets:
  provider: s3
  bucket_name: myproject-cdn
  token_context: cdn
  region: us-east-1
```

### Team Organization
```yaml
# .buckia file
namespace: recordthing

demo-env:
  provider: bunny
  bucket_name: recordthing-demo
  token_context: demo
  folders:
    - 2siEySuKO1wK4XiJHWQ0YxhLxd2

premium-env:
  provider: bunny
  bucket_name: recordthing-premium
  token_context: premium
  folders:
    - user123
    - user456
```

### PDF Generation
```yaml
# .buckia file
document-cdn:
  provider: bunny
  bucket_name: docs-cdn
  token_context: docs
  paths:
    - "whitepapers/"
  pdf:
    base_url: "https://cdn.example.com/insights"
    path_template: "{id}/{name}"
    weasyprint_options:
      presentational_hints: true
      optimize_images: true
```

### TOML Format
```toml
# .buckia.toml file
[my-storage]
provider = "bunny"
bucket_name = "actual-bucket-name"
token_context = "demo"
paths = ["dist/"]

[my-cdn]
provider = "s3"
bucket_name = "cdn-bucket"
token_context = "cdn"
region = "us-east-1"
```

## CLI Usage with Corrected Understanding

### Sync Specific Buckets
```bash
# Use the bucket name from config (top-level key)
buckia sync --bucket dev-storage
buckia sync --bucket prod-storage
buckia sync --bucket cdn-assets
```

### PDF Generation
```bash
# Use the bucket name from config
buckia pdf render index.html document-cdn unique-id my-doc
buckia pdf render index.html document-cdn unique-id my-doc --local-only
```

### Configuration Management
```bash
# Show all buckets
buckia config show

# Test specific bucket
buckia test-connection --bucket dev-storage
```

## Documentation Files Updated

1. **docs/configuration/overview.md** - Corrected basic structure and examples
2. **docs/configuration/basic.md** - Fixed single bucket examples
3. **docs/configuration/pdf.md** - Updated PDF configuration examples
4. **docs/configuration/teams.md** - Fixed team organization examples
5. **docs/cli/overview.md** - Updated CLI reference

## Key Takeaways

1. **Bucket names are arbitrary** - Use descriptive names that make sense for your project
2. **At least one bucket required** - Configuration is useless without buckets
3. **Multiple formats supported** - YAML and TOML both work
4. **Top-level structure is buckets** - No "single bucket" legacy format
5. **CLI uses config bucket names** - Reference buckets by their config names

This corrected understanding aligns with the actual Buckia implementation and the record-thing project example provided.
