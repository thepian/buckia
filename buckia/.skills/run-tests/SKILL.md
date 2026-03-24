---
name: run-tests
description: How to run tests for the buckia project. Use this skill whenever asked to run tests, check if something works, verify a change, or confirm test results in the buckia repo. Triggers on "run tests", "does this pass", "check tests", "run unit tests", "run integration tests", "verify my changes".
---

# Running Tests in Buckia

## Quick reference

| What | Command |
|---|---|
| Unit tests only (fast, no credentials) | `uv run scripts/run_tests.sh tests/unit` |
| All tests | `uv run scripts/run_tests.sh` |
| Integration tests | `uv run -m pytest tests/integration/` |
| Single file | `uv run -m pytest tests/integration/test_sync.py` |
| Single test | `uv run -m pytest tests/integration/test_sync.py::test_sync_with_filters` |
| With coverage | `uv run scripts/run_tests.sh tests/unit --cov` |

## Test structure

```
tests/
  unit/           # Fast, no network, no credentials
  integration/    # Requires live bucket credentials
  conftest.py     # Shared fixtures
```

## Integration test credentials

Integration tests need a `.env` file or environment variables. The pattern is:

```
buckia_<namespace>_<context>=<token>
# e.g.
buckia_buckia_demo=your-bunny-api-key
```

Copy `.env.example` to `.env` and fill in values. Without credentials, integration tests are skipped automatically.

## Known pre-existing failures

These 5 tests in `tests/unit/test_cli_help.py` fail on `main` and are **not caused by your changes**:

- `TestCLIHelpParsing::test_config_help_parsing`
- `TestCLIHelpParsing::test_auth_help_parsing`
- `TestCLIHelpContent::test_main_help_contains_commands`
- `TestCLIHelpContent::test_sync_help_contains_options`
- `TestCLIVersionFlag::test_version_flag_parsing`
- `TestCLIHelpAccessibility::test_subcommand_help_is_specific`
- `TestCLIHelpFlags::test_subcommand_help_flags[--help]`
- `TestCLIHelpFlags::test_subcommand_help_flags[-h]`

They test for a `config` subcommand and `--version` flag that don't exist yet. Ignore them when assessing whether your changes broke anything.

## Verifying changes didn't break anything

1. Run unit tests before and after — compare pass counts
2. The baseline is: **98 passed, 5 skipped, 5 pre-existing failures**
3. If you see more than 5 failures, something regressed
4. When you fix test failures, you must update the run-tests skill with new state of pre-existing failures.

## Mock patterns in unit tests

Unit tests use `MagicMock()` for args. When adding new CLI arguments, you **must** add `args.new_arg = None` in any test that constructs a mock args namespace — otherwise the truthy mock attribute will be passed to the real code.

Example pattern to follow in `tests/unit/test_cli.py`:
```python
args = MagicMock()
args.config = "/test/config"
args.directory = "/test/dir"
args.include_pattern = None   # must be explicit
args.exclude_pattern = None   # must be explicit
```
