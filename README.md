# Buckia - Bucket backing of an App with a local DB and assets

[![PyPI version](https://img.shields.io/pypi/v/buckia.svg)](https://pypi.org/project/buckia/)
[![Python Versions](https://img.shields.io/pypi/pyversions/buckia.svg)](https://pypi.org/project/buckia/)
[![License](https://img.shields.io/github/license/evidently/buckia.svg)](https://github.com/evidently/buckia/blob/main/LICENSE)
[![Unit Tests](https://github.com/evidently/buckia/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/evidently/buckia/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/evidently/buckia/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/evidently/buckia/actions/workflows/integration-tests.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manages a local cache matched by content in a remote cloud Storage Bucket.
A local cache for files belonging to a single user is mirrored in a user specific directory in the Storage Bucket. It is intended to support mobile Apps that manage data locally, but need to secure it or share it by pushing a copy to the cloud.

Buckia library provides a unified interface for interacting with multiple storage providers including Bunny.net, S3, and Linode. It is designed to simplify file synchronization, management, and access across different storage backends.


## APP Support (Swift/Kotlin)

Apps download the assets folder `<demo-team-id>` in order to show demo content. It does not upload to the folder in the Common Storage Bucket. The folder is saved in the App Documents folder as `<demo-team-id>`.

Common Storage Bucket - Holds demo-team folder and common user folders.
Premium Storage Bucket - Holds demo-team folder and premium user folders.
Enterprise Storage Bucket (Dedicated) - Holds demo-team folder and enterprise user folders.

The app creates a new User as needed with an UID. It syncs `<my-user-id>` folder to the Storage Bucket along with a copy of the local SQLite DB, if backup is enabled. 
Locally it would be saved as a `<my-user-id>` folder under the local App Documents folder beside the App Specific SQLite DB.

The App can reset all data by deleting user folder and cloning the SQLite DB from the demo-team folder. It can update to the latest demo data by sync'ing the `<demo-team-id>` folder, and applying the contents of the `App.sqlite` in the `<demo-team-id>` to the local user folder DB.


## CLI Support (Python)

On the Server and Admin PC the bucket content can be managed using the `buckia` CLI.

A local `assets/demo/<demo-team-id>` holds the contents of `<demo-team-id>` in the Storage Bucket.
The folder holds demo images and clips along with SQLite database `App.sqlite`.

Other local `assets/backup/<user-id>` holds the contents of `<user-id>` in the Storage Bucket.
The folder holds backups of content for a specific user.


## Synchronization Capabilities

Buckia sync supports a range of configuration options and deployment scenarios:

### Core Sync Features

- **Bi-directional synchronization** - with the option to configure one way for some files
- **Concurrent operations** - Configurable number of parallel transfers for optimal performance
- **Orphaned file cleanup** - Optionally delete remote files that no longer exist locally
- **Multi-platform support**: Native implementations for Swift (iOS/macOS), and Kotlin (Android), plus Python

### Local File Management

- **Local cache support** - Maintain a separate local cache directory that maps into the main tree
- **Path mapping** - Flexible path translation between local and remote systems
- **Directory structure preservation** - Maintain your exact directory structure in remote storage

The local cache directory receives updates is used to sync bidirectionally. 
Additional paths and files configured will be uploaded to the server as needed.


### Authentication and Connection Options

- **Multiple authentication methods** - Support for API keys, passwords, access tokens
- **Connection pooling** - Reuse connections for better performance
- **Automatic retries** - Configurable retry behavior for transient errors
- **Rate limiting** - Built-in rate limiting to comply with provider restrictions

### Provider-Specific Features

- **Bunny.net specific**
  - Integration with Bunny.net's CDN and Pull Zones
  - Cache purging capabilities
  - Support for both Storage API and Edge Storage
  - Optional use of bunnycdnpython package or direct API calls

- **S3 specific**
  - Support for AWS S3 and S3-compatible storage (MinIO, DigitalOcean Spaces)
  - Bucket policy and ACL management
  - Multipart uploads for large files
  - Transfer acceleration

- **Linode specific**
  - Object lifecycle management
  - CORS configuration
  - Custom metadata

### Advanced Features

- **Dry-run mode** - Preview synchronization actions without making changes
- **Progress reporting** - Real-time progress updates during synchronization
- **Detailed logging** - Configurable logging levels for debugging and auditing
- **Custom file filtering** - Include/exclude patterns for selecting files to sync

## Example Sync Configurations

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

### Advanced Sync with Multiple Options

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
    exclude_pattern=r"^\..*",  # Exclude hidden files
    dry_run=False,
    sync_paths=["images/", "documents/important.pdf"]
)
```

### Progress Reporting During Sync

```python
def report_progress(current, total, action, path):
    percent = int(current * 100 / total) if total > 0 else 0
    print(f"{action.capitalize()}: {current}/{total} ({percent}%) - {path}")

client.sync(
    local_path="./project",
    progress_callback=report_progress
)
```

## Cross-Platform Support

Buckia is designed to work seamlessly across:

- **Operating Systems** - Windows, macOS, Linux
- **Languages** - Python implementation with Swift and Kotlin bindings planned
- **Runtime Environments** - Server environments, CI/CD pipelines, desktop applications

## Getting Started

For detailed installation and usage instructions, please see [DEVELOP.md](DEVELOP.md).

## Platforms

The App user will access the local cache and the Storage Bucket with the library implemented for Swift and Kotlin.
Development, Admin and Server Scripts are written in Python using the library also implemented in Python.

### Bucket Types

- Bunny (bunny.net)
- Linode (linode.com)
- S3

## Architecture

Buckia follows a pluggable architecture with the following components:

```
                   ┌─────────────────┐
                   │  Buckia Client  │
                   └────────┬────────┘
                            │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼─────────┐     │         ┌──────▼─────────┐
│ Local File Manager│     │         │ Remote Manager │
└─────────┬─────────┘     │         └──────┬─────────┘
          │         ┌─────▼────┐            │
          │         │ Sync     │            │
          └─────────► Manager  ◄────────────┘
                    └──────────┘
                          │
                   ┌──────▼───────┐
                   │ Bucket       │
                   │ Adapters     │
                   └──────────────┘
                         / \
                        /   \
   ┌──────────────────┐/     \┌──────────────┐┌──────────────┐
   │  Bunny Adapter   │       │ S3 Adapter   ││Linode Adapter│
   └──────────────────┘       └──────────────┘└──────────────┘
```

### Backend-Independent Design

The library uses a plugin-based architecture that allows for easy addition of new storage backends:

1. **Abstract Base Class**: All backend implementations inherit from the `BaseSync` abstract base class, which defines the required interface.
2. **Factory Pattern**: A factory creates the appropriate backend based on the configuration.
3. **Common Interface**: All backends implement the same methods (`upload_file`, `download_file`, etc.) allowing the client to work with any provider.
4. **Configuration Adapters**: Provider-specific settings are normalized to a common format.

This approach allows users to switch providers with minimal code changes and enables cross-platform implementations to share the same architecture.

## API

Buckia provides a simple, consistent API across all platforms:

A multi-config structure is used. One per domain.

```python
# Python example
from buckia import BuckiaClient, BucketConfig

# Create a configuration
config = BucketConfig(
    provider="bunny",
    bucket_name="my-bucket",
    credentials={...}

# Create a client
client = BuckiaClient(config)

# Sync with remote
result = client.sync(
    local_path="/path/to/project",
    sync_paths=["images/", "documents/reports/"],
    delete_orphaned=True
)

print(f"Sync completed: {result.uploaded} uploaded, {result.downloaded} downloaded")
```

Pluggable implementation of Bucket backends in separate files.
Large files can be broken down by composition.

## CLI

The Python package installs the `buckia` command for syncing against the server from a directory with a `.buckia` config.

```bash
# Basic usage
buckia sync

# Sync specific paths only
buckia sync --paths images/ videos/

# Dry run to preview changes
buckia sync --dry-run

# Use specific config file
buckia sync --config .buckia-staging

# Show sync status
buckia status
```

## Configuration File

The `.buckia` configuration file defines how synchronization behaves between your local filesystem and remote storage buckets. This file should be placed in the root directory of your project.

All paths defined in the configuration file are relative to the directory containing the `.buckia` file.

### Configuration Structure

The top level of the configuration contains one or more bucket configurations, with each bucket identified by a unique key (typically matching the bucket name):

```yaml
bucket-name-1:
  # Configuration for first bucket
  
bucket-name-2:
  # Configuration for second bucket
```

### Configuration Options

Each bucket configuration supports the following options:

| Option | Description | Type | Required |
|--------|-------------|------|----------|
| `provider` | Storage provider type (`bunny`, `s3`, or `linode`) | String | Yes |
| `bucket_name` | Name of the remote bucket/storage zone | String | Yes |
| `domain` | Domain for the storage service | String | No |
| `region` | Geographic region for the bucket | String | No |
| `storage_zone` | Storage zone name (Bunny.net specific) | String | No |
| `pull_zone` | Pull zone name (Bunny.net specific) | String | No |
| `api_key` | API key for authentication | String | Yes* |
| `storage_api_key` | Storage-specific API key (Bunny.net specific) | String | No |
| `password` | Password for protected buckets | String | No |
| `folders` | List of top-level folders to sync | Array | No |
| `paths` | Local paths to sync with the bucket | Array | No |
| `files` | Map of local file paths to remote paths for bidirectional sync | Object | No |
| `upload_files` | Map of local file paths to remote paths for upload-only sync | Object | No |
| `delete_orphaned` | Whether to delete remote files that don't exist locally | Boolean | No |
| `max_workers` | Maximum number of concurrent operations | Integer | No |
| `checksum_algorithm` | Algorithm for file checksums (`sha256`, `md5`, etc.) | String | No |
| `conflict_resolution` | How to resolve conflicts (`local_wins`, `remote_wins`, `newest_wins`, `ask`) | String | No |

\* Authentication method required, but varies by provider

### Path Configuration Behavior

- **paths**: List of local paths to sync bidirectionally with the bucket
  - The first entry in the `paths` list will receive incoming changes from the bucket
  - All entries in the `paths` list will be uploaded to the bucket as needed
  
- **files**: Map of specific files for bidirectional synchronization
  - Key: Local file path
  - Value: Remote file path in the bucket
  
- **upload_files**: Map of files for upload-only synchronization
  - Key: Local file path
  - Value: Remote file path in the bucket

### Example Configuration

```yaml
common-assets:
  # Basic config
  provider: bunny
  bucket_name: common-assets
  domain: storage.bunnycdn.net
  region: eu-central

  # Authentication
  api_key: YOUR_API_KEY
  storage_api_key: YOUR_STORAGE_API_KEY
  password: YOUR_PASSWORD  # Optional for password-protected buckets

  # Folders to sync (top-level directories in the bucket)
  folders:
  - 123-456-789-ABC

  # Sync settings
  paths:
    - demo/        # Will receive incoming changes from the bucket
    - static/data/ # Will be uploaded to the bucket
  delete_orphaned: true
  max_workers: 8

  # Advanced settings
  checksum_algorithm: sha256
  conflict_resolution: local_wins  # Options: local_wins, remote_wins, newest_wins, ask
```

In this example, changes to files in the `demo/` directory will be synchronized bidirectionally with the bucket, while files in `static/data/` will be uploaded to the bucket but remote changes won't be downloaded to this directory.

### Primary Configuration Scenario

The bucket is organised in top level UID directories that map to user IDs. The IDs must not be guessable as the server isn't required to implement directory level access control. If the App has a valid ID, it can read and write the data.
Mobile Apps are configured to sync with a single User directory

Initial team/user ID
Default SQLite DB.
Reset to the default

Sync from default folder, team folder and my folder.

Document App Data Logic

CLI folder data logic


## Implementation Details

### Sync Process

The sync process follows these steps:

1. **Scan**: Scan local and remote files to build file manifests
2. **Compare**: Compare manifests to identify changes
3. **Apply Cache**: Apply any changes from the cache directory
4. **Plan**: Create a plan for uploads, downloads, and deletions
5. **Execute**: Execute the plan with parallel operations
6. **Verify**: Verify completed transfers

### File Tracking

Files are tracked using:
- File paths (relative to root directory)
- Content checksums (SHA-256 by default)
- Modification timestamps
- File metadata (MIME types, etc.)

### Backend Implementation

The library currently includes implementations for:

- **Bunny.net**: Complete implementation with support for both direct API and bunnycdnpython
- **S3**: Placeholder implementation (skeleton)
- **Linode**: Placeholder implementation (skeleton)

To add a new backend:
1. Create a new class that inherits from `BaseSync`
2. Implement all required methods from the base class
3. Add the backend to the factory in `sync/factory.py`

## Installation

To install the Python library:

```bash
# Basic installation
pip install buckia

# Install with specific backend support
pip install buckia[bunny]  # For Bunny.net support
pip install buckia[s3]     # For AWS S3 support
pip install buckia[linode] # For Linode Object Storage support

# Install with all backends and development tools
pip install buckia[bunny,s3,linode,dev]
```

## Project Structure

```
buckia/
├── __init__.py
├── client.py           # Main client interface
├── config.py           # Configuration handling
├── cli.py              # Command-line interface
└── sync/
    ├── __init__.py
    ├── base.py         # Base synchronization classes
    ├── factory.py      # Backend factory
    ├── bunny.py        # Bunny.net implementation
    ├── s3.py           # S3 implementation
    └── linode.py       # Linode implementation
```

## TODO list

- Implement Swift client for iOS/macOS
- Implement Kotlin client for Android
- Add encryption support for sensitive files
- Add bandwidth throttling
- Add delta sync for large files
- Implement conflict resolution UI
- Add S3 adapter
- Add Linode adapter
- Implement parallel downloads/uploads
- Add integrity verification

## Test Coverage

Integration tests run through the Buckia features against a test bucket that is cleared/setup/synced/etc.
Unit testing done where significant functionality is present in the code.

Test suite includes:
- Unit tests for core functionality
- Integration tests with mock storage backends
- End-to-end tests with real storage providers
- Performance benchmarks for large datasets

## License

This is released under AGPL license.

The GNU Affero General Public License is a free, copyleft license for software and other kinds of works, specifically designed to ensure cooperation with the community in the case of network server software.

When you distribute copies of such a program, whether gratis or for a fee, you must pass on to the recipients the same freedoms that you received. You must make sure that they, too, receive or can get the source code.

(c) 2019-2025 by Henrik Vendelbo
