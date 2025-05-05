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

- Access Directory: `/Volumes/Projects/Thepia/thepia-all/`
- Whenever modifying the directory in the filesystem, make a git commit documenting what has changed

# Required Tools Usage

- Sequential Thinking: Always use when available
- Brave Search: Use for research validation and source citation
  - Validate statements with research
  - Provide source URLs
  - Support claims with relevant references

# Codebase Overview

## Development Commands

- Install dev dependencies: `uv pip install -e ".[bunny,s3,linode,dev]"`
- Install additional dependencies: `uv pip install python-dotenv`
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
