# Team Organization Configuration

Buckia supports team-based organization with namespaces, folder management, and isolated environments for collaborative workflows.

## Namespace Organization

Use namespaces to organize projects and teams in your `.buckia` file:

```yaml
namespace: recordthing

# Bucket names can be anything - these are just examples
demo-storage:
  provider: bunny
  bucket_name: recordthing-demo
  token_context: demo

common-storage:
  provider: bunny
  bucket_name: recordthing-common
  token_context: common

premium-storage:
  provider: bunny
  bucket_name: recordthing-premium
  token_context: premium
```

## Folder-Based Organization

### Remote Folder Management

Target specific folders within buckets:

```yaml
# Bucket name can be anything
demo-storage:
  provider: bunny
  bucket_name: recordthing-demo
  token_context: demo

  # Sync only these remote folders
  folders:
    - 2siEySuKO1wK4XiJHWQ0YxhLxd2
    - 8kLmN9pQ3rS7tU1vW5xY2zA4bC6

  # Local paths for bidirectional sync
  paths:
    - demo/ # Downloads from bucket
    - static/data/ # Uploads to bucket
```

### User-Based Folder Structure

Organize by user IDs for multi-tenant applications:

```yaml
namespace: myapp

user-storage:
  provider: s3
  bucket_name: myapp-users
  token_context: users
  region: us-east-1

  # User-specific folders
  folders:
    - user-123
    - user-456
    - user-789

  # Folder structure per user:
  # |- user-123/
  # |  |- backup.sqlite
  # |  |- originals/
  # |  |- reworked/
  # |  |- inbound/
```

## Bidirectional Sync Configuration

### Download and Upload Paths

Configure different paths for different sync directions:

```yaml
content-sync:
  provider: bunny
  bucket_name: content-storage
  token_context: content

  folders:
    - shared-content
    - user-uploads

  paths:
    # Downloads: bucket → local
    - incoming/ # Receives files from bucket
    - shared/ # Shared content downloads

    # Uploads: local → bucket
    - outgoing/ # Sends files to bucket
    - generated/ # Generated content uploads

  # Sync behavior
  delete_orphaned: true
  max_workers: 8
  conflict_resolution: newest_wins
```

### Selective Sync Patterns

Control which files sync in each direction:

```yaml
media-workflow:
  provider: bunny
  bucket_name: media-processing
  token_context: media

  folders:
    - raw-uploads
    - processed-media

  # Path-specific sync rules
  sync_rules:
    # Upload only new files
    - path: "uploads/"
      direction: "upload"
      pattern: "*.{jpg,png,mp4}"

    # Download processed files
    - path: "processed/"
      direction: "download"
      pattern: "*.{webp,mp4}"

    # Bidirectional for metadata
    - path: "metadata/"
      direction: "both"
      pattern: "*.json"
```

## Multi-Environment Setup

### Development Workflow

```yaml
namespace: myproject

# Local development
dev:
  provider: bunny
  bucket_name: myproject-dev
  domain: storage.bunnycdn.net
  region: eu
  token_context: dev

  folders:
    - dev-content

  paths:
    - dev/
    - temp/

  delete_orphaned: false # Safe for development
  max_workers: 4
  conflict_resolution: local_wins

# Staging environment
staging:
  provider: bunny
  bucket_name: myproject-staging
  domain: storage.bunnycdn.net
  region: eu
  token_context: staging

  folders:
    - staging-content

  paths:
    - dist/
    - assets/

  delete_orphaned: true
  max_workers: 6
  conflict_resolution: newest_wins

# Production environment
prod:
  provider: bunny
  bucket_name: myproject-prod
  domain: cdn.myproject.com # Custom domain
  region: eu
  token_context: prod

  folders:
    - live-content

  paths:
    - dist/

  delete_orphaned: true
  max_workers: 8
  conflict_resolution: remote_wins # Protect production
```

## Team Access Control

### Role-Based Configuration

Different team members can have different configurations:

```yaml
# Admin configuration
namespace: company

admin-access:
  provider: s3
  bucket_name: company-admin
  token_context: admin
  region: us-east-1

  folders:
    - all-teams
    - system-backups

  paths:
    - admin/
    - backups/
    - reports/

  delete_orphaned: true
  max_workers: 8

# Developer configuration
dev-access:
  provider: s3
  bucket_name: company-dev
  token_context: developer
  region: us-east-1

  folders:
    - team-alpha
    - team-beta

  paths:
    - src/
    - builds/

  delete_orphaned: false
  max_workers: 4
```

## Advanced Team Patterns

### Content Distribution Network

```yaml
namespace: contentcdn

# Global CDN
global-cdn:
  provider: bunny
  bucket_name: global-content
  domain: cdn.example.com
  token_context: cdn-global

  folders:
    - static-assets
    - media-files

  paths:
    - dist/assets/
    - dist/media/

  # PDF generation for documents
  pdf:
    base_url: "https://cdn.example.com/docs"
    path_template: "{category}/{id}/{name}"

# Regional CDN
regional-cdn:
  provider: bunny
  bucket_name: regional-content
  domain: eu-cdn.example.com
  region: eu
  token_context: cdn-eu

  folders:
    - eu-content

  paths:
    - dist/localized/eu/
```

### Multi-Tenant Application

```yaml
namespace: saas-platform

# Tenant isolation
tenant-alpha:
  provider: s3
  bucket_name: saas-tenant-alpha
  token_context: tenant-alpha
  region: us-west-2

  folders:
    - user-data
    - app-assets

  paths:
    - tenants/alpha/

  # Tenant-specific settings
  delete_orphaned: true
  max_workers: 6
  checksum_algorithm: sha256

tenant-beta:
  provider: s3
  bucket_name: saas-tenant-beta
  token_context: tenant-beta
  region: eu-west-1

  folders:
    - user-data
    - app-assets

  paths:
    - tenants/beta/

  delete_orphaned: true
  max_workers: 6
  checksum_algorithm: sha256
```

## CLI Usage for Teams

### Environment-Specific Commands

```bash
# Sync specific environment
buckia sync --bucket dev
buckia sync --bucket staging
buckia sync --bucket prod

# Folder-specific sync
buckia sync --bucket user-storage --folder user-123

# Team namespace operations
buckia --config ./team-config/.buckia sync --bucket shared
```

### Batch Operations

```bash
# Sync all environments
for env in dev staging prod; do
  buckia sync --bucket $env
done

# User-specific operations
for user in user-123 user-456; do
  buckia sync --bucket user-storage --folder $user
done
```

## Best Practices

### Organization

1. **Use descriptive namespaces** - Include project/company name
2. **Consistent naming** - Follow team conventions
3. **Environment separation** - Clear dev/staging/prod boundaries
4. **Folder isolation** - Separate user/team data

### Security

1. **Separate credentials** - Different tokens per environment
2. **Least privilege** - Minimal required permissions
3. **Audit access** - Track who accesses what
4. **Backup strategies** - Regular backups of critical data

### Performance

1. **Optimize worker counts** - Based on team size and bandwidth
2. **Strategic deletion** - Careful with `delete_orphaned`
3. **Conflict resolution** - Match team workflow
4. **Monitor usage** - Track storage and bandwidth

### Collaboration

1. **Document folder structure** - Clear team guidelines
2. **Shared configurations** - Version control `.buckia` files
3. **Communication** - Coordinate sync operations
4. **Testing** - Use dry runs for changes

## Troubleshooting

### Common Team Issues

**Folder Access Denied**

```bash
# Check folder permissions
buckia test-connection --bucket team-storage --folder user-123

# Verify credentials
buckia auth list
```

**Sync Conflicts**

```bash
# Check conflict resolution
buckia config show --bucket team-storage

# Manual conflict resolution
buckia sync --bucket team-storage --conflict-resolution ask
```

**Performance Issues**

```bash
# Reduce workers for shared bandwidth
buckia sync --bucket team-storage --max-workers 2

# Check network usage
buckia sync --bucket team-storage --verbose
```

## Next Steps

- **[Sync Configuration](sync.md)** - Advanced sync behavior
- **[Security](security.md)** - Team access control
- **[CLI Reference](../cli/sync.md)** - Complete sync commands
- **[Monitoring](../operations/monitoring.md)** - Team usage monitoring
