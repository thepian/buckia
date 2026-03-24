# Buckia - Bucket backing of an App with a local DB and assets

[![PyPI version](https://img.shields.io/pypi/v/buckia.svg)](https://pypi.org/project/buckia/)
[![Python Versions](https://img.shields.io/pypi/pyversions/buckia.svg)](https://pypi.org/project/buckia/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Unit Tests](https://github.com/thepian/buckia/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/thepian/buckia/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/thepian/buckia/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/thepian/buckia/actions/workflows/integration-tests.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manages a local cache matched by content in a remote cloud Storage Bucket. A local cache for files belonging to a single user is mirrored in a user-specific directory in the Storage Bucket. Designed to support mobile apps that manage data locally but need to secure or share it by pushing a copy to the cloud.

Buckia provides a unified interface for Bunny.net, AWS S3, Linode Object Storage, and Backblaze B2.

## Installation

```bash
pip install "buckia[bunny]"    # Bunny.net
pip install "buckia[s3]"       # AWS S3
pip install "buckia[linode]"   # Linode
pip install "buckia[b2]"       # Backblaze B2
pip install "buckia[bunny,s3,linode,b2]"  # All providers
```

## Quick Start

```bash
# Sync local directory to cloud bucket
buckia sync

# Preview changes without executing
buckia sync --dry-run

# Sync a specific named bucket from .buckia config
buckia sync --bucket production
```

See [Configuration Overview](docs/configuration/overview.md) for the `.buckia` config file format.

## Documentation

### User Guides
- [Configuration Overview](docs/configuration/overview.md) — `.buckia` file format and options
- [Basic Configuration](docs/configuration/basic.md) — Single-bucket quickstart
- [CLI Reference](docs/cli/overview.md) — All commands and options
- [Python API Reference](docs/api-reference.md) — Python library usage
- [Sync Features](docs/features/sync.md) — Upload-only, create-only, state cache

### Developer Guides
- [Development Guide](docs/development/guide.md) — Setup and contribution workflow
- [Architecture](docs/development/architecture.md) — System design and backend structure
- [Testing Guide](docs/TESTING.md) — Running and writing tests
- [CI Pipeline](docs/development/CI.md) — Continuous integration

### Operations
- [Release Process](docs/operations/release.md) — Publishing to PyPI
- [Secrets Management](docs/operations/secrets.md) — Secure credential handling

### Mobile Platforms
- [Swift / iOS / macOS](docs/mobile/swift.md) — Native Apple platform integration

### Project
- [Roadmap](docs/project/roadmap.md) — Planned features
- [Changelog](docs/CHANGELOG.md) — Version history

## License

Released under the AGPL v3 license. (c) 2019–2026 Henrik Vendelbo
