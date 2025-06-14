# Buckia CLI Reference

The Buckia command-line interface provides comprehensive tools for cloud storage sync, PDF generation, team management, and enterprise backoffice operations.

## Installation

```bash
# Install Buckia
pip install buckia

# Verify installation
buckia --version

# Show help
buckia --help
```

## Command Structure

```bash
buckia [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS] [ARGUMENTS]
```

### Global Options

| Option          | Description                                                      |
| --------------- | ---------------------------------------------------------------- |
| `--config PATH` | Path to configuration file (.buckia, .buckia.yaml, .buckia.toml) |
| `--verbose, -v` | Enable verbose output                                            |
| `--quiet, -q`   | Suppress non-error output                                        |
| `--dry-run`     | Show what would be done without executing                        |
| `--help, -h`    | Show help message                                                |
| `--version`     | Show version information                                         |

## Core Commands (Available Now)

### File Synchronization

```bash
buckia sync [--bucket BUCKET] [--dry-run] [--verbose]
buckia status [--bucket BUCKET]
buckia test-connection [--bucket BUCKET] [--all]
```

- Sync files between local and cloud storage
- Check sync status and file statistics
- Test connectivity to configured buckets

### PDF Generation

```bash
buckia pdf render HTML_FILE BUCKET_NAME ID FILENAME [--local-only] [--output-dir DIR]
```

- Render HTML files to PDF using WeasyPrint
- Upload to cloud storage or save locally
- Support for custom templates and styling

### Configuration Management

```bash
buckia config show [--bucket BUCKET]
buckia config validate
buckia config init [--format yaml|toml]
```

- Display current configuration (.buckia files)
- Validate configuration syntax and structure
- Initialize new configuration files

### Authentication

```bash
buckia auth set CONTEXT [--username USER] [--password PASS]
buckia auth list
buckia auth remove CONTEXT
buckia auth test CONTEXT
```

- Manage stored credentials in system keyring
- Support for multiple provider contexts
- Secure credential storage and testing

## Enterprise Commands (Planned)

### User Management

```bash
buckia user migrate --user-id USER --target-tier TIER --team-id TEAM
buckia user suspend --user-id USER --team-id TEAM [--duration DAYS]
buckia user list --team-id TEAM [--tier TIER] [--status STATUS]
buckia user create --team-id TEAM --tier TIER --email EMAIL
```

- Migrate users between subscription tiers
- Suspend/restore user access with notifications
- List and filter users by team and status
- Bulk user provisioning and management

### Content Operations

```bash
buckia content deduplicate --user-id USER --team-id TEAM [--similarity THRESHOLD]
buckia content moderate --team-id TEAM [--sensitivity LEVEL] [--auto-flag]
buckia content optimize --team-id TEAM [--storage-tier TIER] [--age DAYS]
buckia content classify --team-id TEAM [--retrain] [--confidence MIN]
```

- Remove duplicate recordings and content
- AI-powered content moderation and flagging
- Storage optimization and lifecycle management
- Content classification and training data generation

### System Administration

```bash
buckia system stats --team-id TEAM [--period PERIOD] [--format FORMAT]
buckia system migrate-storage --team-id TEAM --source PROVIDER --target PROVIDER
buckia system cleanup --team-id TEAM [--dry-run] [--age DAYS]
buckia system backup --team-id TEAM [--incremental] [--verify]
```

- Generate detailed usage and analytics reports
- Migrate data between storage providers
- Clean up orphaned files and optimize storage
- Automated backup and disaster recovery

### Database Management

```bash
buckia db repair --user-id USER --team-id TEAM [--corruption-check LEVEL]
buckia db backup --team-id TEAM [--compress] [--encrypt]
buckia db migrate --team-id TEAM --version VERSION [--rollback]
buckia db sync --user-id USER [--force] [--conflict-resolution STRATEGY]
```

- Repair corrupted SQLite databases
- Automated database backup and restoration
- Schema migrations and version management
- Synchronize database changes across devices

### Bulk Operations

```bash
buckia bulk import-users --source FILE --team-id TEAM [--mapping COLUMN]
buckia bulk export-data --team-id TEAM --format FORMAT [--filter CRITERIA]
buckia bulk apply-changes --team-id TEAM --changes FILE [--dry-run]
buckia bulk notify --team-id TEAM --template TEMPLATE [--filter CRITERIA]
```

- Import users from CSV/JSON with team assignment
- Export team data for analysis or migration
- Apply bulk configuration or policy changes
- Send notifications to user groups

### Audit & Compliance

```bash
buckia audit sharing --team-id TEAM [--content-id ID] [--timeline] [--export]
buckia audit access --team-id TEAM [--period PERIOD] [--geo-distribution]
buckia audit changes --team-id TEAM [--user-id USER] [--since DATE]
buckia privacy forget-user --user-id USER --team-id TEAM [--compliance GDPR]
```

- Analyze content sharing patterns and relationships
- Generate access logs and usage analytics
- Track configuration and data changes
- GDPR/privacy compliance tools

## Quick Examples

### File Sync Operations

```bash
# Sync all configured buckets
buckia sync

# Sync specific bucket from .buckia config
buckia sync --bucket my-cdn-storage

# Preview changes without executing
buckia sync --bucket production --dry-run --verbose

# Check sync status
buckia status --bucket production
```

### PDF Document Generation

```bash
# Generate PDF and upload to cloud
buckia pdf render whitepaper.html thepia-cdn abc123 hidden-cost-brief

# Generate PDF locally only (no upload)
buckia pdf render whitepaper.html thepia-cdn abc123 hidden-cost-brief --local-only

# Save to specific directory
buckia pdf render report.html docs-cdn xyz789 monthly-report --local-only --output-dir ./pdfs
```

### Configuration & Setup

```bash
# Initialize new configuration
buckia config init --format yaml

# Show current configuration
buckia config show

# Validate .buckia file syntax
buckia config validate

# Test connectivity to all buckets
buckia test-connection --all

# Set up credentials for a provider
buckia auth set thepia-cdn --password "your-api-key"
```

### Enterprise Operations (Planned)

```bash
# User management
buckia user migrate --user-id user123 --target-tier premium --team-id team456

# Generate usage analytics
buckia system stats --team-id team456 --period last-month --format pdf

# Content optimization
buckia content deduplicate --user-id user123 --team-id team456 --similarity 0.95

# Compliance reporting
buckia audit access --team-id team456 --period last-quarter --geo-distribution
```

## Future Command Structure

As Buckia evolves into a comprehensive enterprise platform, the CLI will expand to support:

### Multi-Tenant Architecture

```bash
buckia --tenant TENANT_ID COMMAND [OPTIONS]
buckia tenant list [--active] [--tier TIER]
buckia tenant create --name NAME --tier TIER [--admin EMAIL]
```

### Advanced Workflow Automation

```bash
buckia workflow create --name NAME --config FILE [--schedule CRON]
buckia workflow run --name NAME [--async] [--notify EMAIL]
buckia workflow list [--status STATUS] [--team-id TEAM]
```

### Integration & API Management

```bash
buckia api generate-key --scope SCOPE [--expires DAYS]
buckia api webhook create --url URL --events EVENTS [--secret SECRET]
buckia integration setup --provider PROVIDER --config FILE
```

### Advanced Analytics & Reporting

```bash
buckia analytics generate --type TYPE --team-id TEAM [--export FORMAT]
buckia metrics collect --interval MINUTES [--dashboard URL]
buckia alerts create --condition CONDITION --action ACTION
```

## Environment Variables

| Variable             | Description                                 | Default     |
| -------------------- | ------------------------------------------- | ----------- |
| `BUCKIA_CONFIG`      | Default configuration file path             | `./.buckia` |
| `BUCKIA_LOG_LEVEL`   | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO`      |
| `BUCKIA_MAX_WORKERS` | Default max workers                         | `4`         |
| `BUCKIA_TIMEOUT`     | Default operation timeout (seconds)         | `300`       |
| `BUCKIA_TENANT_ID`   | Default tenant ID for multi-tenant setups   | `None`      |

## Exit Codes

| Code | Meaning              |
| ---- | -------------------- |
| `0`  | Success              |
| `1`  | General error        |
| `2`  | Configuration error  |
| `3`  | Authentication error |
| `4`  | Network error        |
| `5`  | Permission error     |
| `6`  | File not found       |
| `7`  | Validation error     |

## Common Workflows

### Development Workflow

```bash
# 1. Initialize configuration
buckia config init

# 2. Set up credentials
buckia auth set dev --password "dev-api-key"

# 3. Test connection
buckia test-connection --bucket dev

# 4. Sync files
buckia sync --bucket dev --dry-run
buckia sync --bucket dev
```

### Production Deployment

```bash
# 1. Validate configuration
buckia config validate

# 2. Test production connection
buckia test-connection --bucket prod

# 3. Sync with safety checks
buckia sync --bucket prod --dry-run --verbose
buckia sync --bucket prod

# 4. Verify deployment
buckia status --bucket prod
```

### Team Administration

```bash
# 1. Check team status
buckia system stats --team-id team123

# 2. Migrate user
buckia user migrate --user-id user456 --target-tier premium

# 3. Generate compliance report
buckia audit access --team-id team123 --period last-quarter
```

## Getting Help

### Command-Specific Help

```bash
# Show help for any command
buckia COMMAND --help

# Examples:
buckia sync --help
buckia pdf render --help
buckia user migrate --help
```

### Verbose Output

```bash
# Add --verbose to any command for detailed output
buckia sync --verbose
buckia pdf render file.html cdn id name --verbose
```

### Debug Mode

```bash
# Set debug logging
export BUCKIA_LOG_LEVEL=DEBUG
buckia sync

# Or use environment variable inline
BUCKIA_LOG_LEVEL=DEBUG buckia sync
```

## Next Steps

- **[Sync Commands](sync.md)** - File synchronization reference
- **[PDF Commands](pdf.md)** - PDF generation reference
- **[Team Commands](user.md)** - Team management reference
- **[Configuration](../configuration/overview.md)** - Configuration guide
