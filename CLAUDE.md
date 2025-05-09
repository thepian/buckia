# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### General Behavior Protocol

Always provide complete, untruncated versions of code and text updates unless explicitly requested otherwise by the user.

## Tools-Dependent Protocols

The following instructions apply only when tools/MCP Servers are accessible:

# Memory

Follow these steps for each interaction:

1. User Identification:
   - You should assume that you are interacting with default_user
   - If you have not identified default_user, proactively try to do so.
2. Memory Retrieval:
   - Always begin your chat by saying only "Remembering..." and retrieve all relevant information from your knowledge graph
   - Always refer to your knowledge graph as your "memory"
3. Memory:
   - While conversing with the user, be attentive to any new information that falls into these categories:
     a) Basic Identity (age, gender, location, job title, education level, etc.)
     b) Behaviors (interests, habits, etc.)
     c) Preferences (communication style, preferred language, etc.)
     d) Goals (goals, targets, aspirations, etc.)
     e) Relationships (personal and professional relationships up to 3 degrees of separation)
4. Memory Update:
   - If any new information was gathered during the interaction, ask the user if they want it to be saved, and if so update your memory as follows:
     a) Create entities for recurring organizations, people, and significant events
     b) Connect them to the current entities using relations
     c) Store facts about them as observations

# Filesystem - Access Configuration

- Access Directory: `/Volumes/Projects/Evidently/buckia/`
- Whenever modifying the directory in the filesystem, make a git commit documenting what has changed

# Required Tools Usage

- Sequential Thinking: Always use when available
- Brave Search: Use for research validation and source citation
  - Validate statements with research
  - Provide source URLs
  - Support claims with relevant references

# Codebase Overview

## Documentation Structure

The documentation for Buckia is organized into the following categories based on purpose, topic, and audience:

### User Documentation

- **Getting Started Guide**: Introduction and basic usage (`/docs/getting-started.md`)
- **Configuration Guide**: Detailed configuration options (`/docs/configuration.md`) - moved from BUCKIA_CONFIG.md
- **CLI Reference**: Command line interface usage (`/docs/cli-reference.md`)
- **API Reference**: Programming interface documentation (`/docs/api-reference.md`)
- **Feature Guides**:
  - **Sync Features**: Synchronization capabilities (`/docs/features/sync.md`)
  - **Security Features**: Token and authentication features (`/docs/features/security.md`) - moved from SECURITY.md
  - **Provider Guides**:
    - Bunny.net (`/docs/providers/bunny.md`)
    - AWS S3 (`/docs/providers/s3.md`)
    - Linode (`/docs/providers/linode.md`)
    - Backblaze B2 (`/docs/providers/b2.md`)

### Developer Documentation

- **Development Guide**: Setup and contribution workflow (`/docs/development/guide.md`) - moved from DEVELOP.md
- **Architecture Overview**: System design and components (`/docs/development/architecture.md`)
- **Testing Guide**: Testing procedures and strategies (`/docs/development/testing.md`) - moved from TESTING.md
- **CI Pipeline**: Continuous integration setup (`/docs/development/ci.md`) - moved from CI.md
- **IDE Configuration**:
  - VSCode setup (`/docs/development/vscode.md`) - moved from VSCODE.md
  - Other IDEs (`/docs/development/ides.md`)

### Operations Documentation

- **Release Process**: Publishing to PyPI (`/docs/operations/release.md`) - moved from PYPI_RELEASE.md
- **Security Best Practices**: Secure credential management (`/docs/operations/secrets.md`) - moved from SECRETS.md

### Project Documentation

- **Changelog**: Record of changes (`/docs/project/changelog.md`) - consolidated from CHANGELOG.md and CHANGES.md
- **Roadmap**: Future development plans (`/docs/project/roadmap.md`)
- **Contributing Guidelines**: How to contribute (`/docs/project/contributing.md`)
- **License Information**: License details (`/docs/project/license.md`)

### Mobile Platform Documentation

- **Swift Implementation Guide**: For iOS/macOS (`/docs/mobile/swift.md`)
- **Kotlin Implementation Guide**: For Android (`/docs/mobile/kotlin.md`)

This organization structure provides clear pathways for different audiences:

- End users will focus on Getting Started, Configuration, and CLI/API references
- Developers will concentrate on Development Guide, Architecture, and Testing
- Operations teams will need the Release Process and Security practices
- Project stakeholders can track progress through Changelog and Roadmap

Each document should include cross-references to related documentation to create a cohesive experience.

## Security and Authentication

Buckia uses keyring for secure storage of API tokens with environment variable fallback. See `docs/SECURITY.md` for details. Key concepts:

- API tokens are stored securely in the system keychain (macOS/Linux/Windows)
- Environment variables can be used as an alternative to keyring
- The `TokenManager` class in `buckia/security/token_manager.py` handles token operations
- Tokens are associated with "bucket contexts" (like "demo", "long_term", etc.)
- Commands support biometric authentication when available on the system

### IMPORTANT: Token Handling in Tests

When writing or modifying test code, follow these strict rules:

1. NEVER use interactive prompts in tests - all authentication must be non-interactive
2. Environment variables for tokens follow the pattern: `buckia_<namespace>_._<context>`
   Example: `buckia_buckia_demo`
3. Tests should clearly report which environment variables are missing when they fail
4. For integration tests, use a .env file when running locally (see `.env.example`)
5. CI environments use GitHub secrets for environment variables

### Token Management CLI

```bash
# Save a token for a bucket context (securely prompts for token)
buckia token set bunny

# Get a token (requires authentication)
buckia token get bunny

# List all available bucket contexts with tokens
buckia token list

# Delete a token
buckia token delete bunny
```

### API Usage

```python
from buckia.security import TokenManager

# Initialize with namespace (defaults to "buckia")
token_manager = TokenManager()

# Save a token (will prompt if token is None)
token_manager.save_token("bunny", token)

# Get a token (will trigger authentication)
token = token_manager.get_token("bunny")

# List available bucket contexts
contexts = token_manager.list_bucket_contexts()

# Delete a token
token_manager.delete_token("bunny")
```

## Development Commands

- Install dev dependencies: `uv pip install -e ".[bunny,s3,linode,dev]"`
- Install additional dependencies: `uv pip install keyring python-dotenv`
- Run all tests: `uv run scripts/run_tests.sh`
- Run only unit tests: `uv run scripts/run_tests.sh tests/unit`
- Run integration tests: `uv run -m pytest tests/integration/`
- Run specific test file: `uv run -m pytest tests/integration/test_operations.py`
- Run specific test: `uv run -m pytest tests/integration/test_operations.py::test_file_upload_download`
- Test with coverage: `uv run -m pytest --cov=buckia`

## Code Style Guidelines

- Use Python 3.7+ features (e.g., dataclasses, typing)
- Follow PEP 8 naming conventions (snake_case for variables/functions, PascalCase for classes)
- Use typing annotations for all functions/methods
- Document all public functions/classes with docstrings ("""...""")
- Keep line length under 100 characters
- Handle errors explicitly with try/except blocks, log appropriately
- Import order: standard lib, third-party packages, local modules
- Use Path from pathlib instead of string paths when feasible
- Prefer explicit error messages in assertions
- Avoid mutable default parameters in function definitions
