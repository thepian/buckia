"""
Test fixtures and utilities for Buckia testing
"""

import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Generator

import pytest
import yaml
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest
from dotenv import load_dotenv

from buckia import BucketConfig, BuckiaClient, BuckiaConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("buckia.test")

# Load environment variables from .env file if it exists
# For integration tests, we always want to load from .env if it exists
dotenv_path = Path(os.path.dirname(os.path.dirname(__file__))) / ".env"
if dotenv_path.exists():
    # Always load and override environment variables from .env
    load_dotenv(dotenv_path=dotenv_path, override=True)
    logger.info("Loaded environment variables from .env file")

# Unique test ID to prevent conflicts between test runs
TEST_RUN_ID = str(uuid.uuid4())[:8]

# Test file sizes (in bytes)
TEST_FILE_SIZES = {
    "small": 1024,  # 1 KB
    "medium": 1024 * 100,  # 100 KB
    "large": 1024 * 1024,  # 1 MB
}


def pytest_addoption(parser: Config) -> None:
    """Add command-line options for tests"""
    parser.addoption(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "config", "test_config.yaml"),
        help="Path to test configuration file. Default: tests/config/test_config.yaml",
    )
    parser.addoption(
        "--skip-cleanup",
        action="store_true",
        help="Skip cleaning up test data after tests",
    )
    parser.addoption(
        "--preserve-remote",
        action="store_true",
        help="Preserve remote files and directories for debugging",
    )
    parser.addoption(
        "--show-env-vars",
        action="store_true",
        help="Show all token-related environment variables at the start of the test session",
    )


def pytest_configure(config: Config) -> None:
    """Configure pytest with our custom options."""
    # If --show-env-vars option is specified, show all relevant environment variables
    if config.getoption("--show-env-vars"):
        list_token_env_vars()


@pytest.fixture(scope="session")
def test_config(request: FixtureRequest) -> Dict[str, Dict[str, Any]]:
    """
    Load test configuration from file.
    This can now be either a single bucket config or a multi-bucket config.
    """
    config_path = request.config.getoption("--config")

    # Check config file exists
    if not os.path.exists(config_path):
        # Try environment variables if config file doesn't exist
        if os.environ.get("BUNNY_API_KEY") and os.environ.get("BUNNY_STORAGE_ZONE"):
            # Create a default config using environment variables
            return {
                "default": {  # Use "default" as the bucket name
                    "provider": "bunny",
                    "bucket_name": "buckia-test",
                    "token_context": "demo",  # Use the fixed demo token context
                    "delete_orphaned": True,
                    "max_workers": 4,
                    "checksum_algorithm": "sha256",
                },
                "long_term": {
                    "provider": "b2",
                    "bucket_name": "buckia-test",
                    "token_context": "test",
                    "delete_orphaned": True,
                    "max_workers": 4,
                    "checksum_algorithm": "sha256",
                },
            }
        else:
            pytest.fail(
                f"Test config file not found: {config_path} and no environment variables set"
            )

    # Load config from file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Handle both old-style (single bucket) and new-style (multi-bucket) configs
    if isinstance(config, dict) and config.get("provider"):
        # Old style config - wrap it in a dict with "default" key
        logger.info("Converting single bucket config to multi-bucket format with 'default' key")
        return {"default": config}
    else:
        # New style multi-bucket config - use as is
        return config


# We now use the real TokenManager which gets tokens from environment variables
# Environment variables follow the format: buckia.<namespace>.<context>
# For example, the Bunny.net API key would be in buckia.buckia.bunny


@pytest.fixture(scope="session")
def buckia_config(test_config: Dict[str, Dict[str, Any] | BucketConfig]) -> BuckiaConfig:
    """
    Create a BuckiaConfig object from test configuration.
    This contains all bucket configurations defined in the test config.
    """
    buckia_config = BuckiaConfig()

    # Convert test_config dict to BuckiaConfig
    for bucket_name, bucket_config_data in test_config.items():
        # Create BucketConfig for each entry
        bucket_config = BucketConfig(
            provider=bucket_config_data["provider"],
            bucket_name=bucket_config_data["bucket_name"],
            # Use token_context from config or default to "demo"
            token_context=bucket_config_data.get("token_context", "demo"),
            delete_orphaned=bucket_config_data.get("delete_orphaned", False),
            max_workers=bucket_config_data.get("max_workers", 4),
            checksum_algorithm=bucket_config_data.get("checksum_algorithm", "sha256"),
        )

        # Add to BuckiaConfig
        buckia_config.configs[bucket_name] = bucket_config

    return buckia_config


@pytest.fixture(scope="session")
def bucket_config(buckia_config: BuckiaConfig) -> BucketConfig:
    """
    Create a BucketConfig object from test configuration.
    Uses the 'default' bucket config from the multi-bucket config.
    """
    # Extract the default bucket config from the multi-bucket config
    if "default" not in buckia_config:
        # If no default bucket is defined, use the first one
        bucket_name = next(iter(buckia_config.configs.keys()))
        logger.warning(f"No 'default' bucket config found, using '{bucket_name}' instead")
        return buckia_config.configs[bucket_name]
    else:
        return buckia_config.configs["default"]


@pytest.fixture(scope="session")
def bucket_config_long_term(buckia_config: BuckiaConfig) -> BucketConfig:
    """
    Create a BucketConfig object for long-term storage.
    Uses the 'long_term' bucket config from the multi-bucket config.
    """
    # Extract the long-term bucket config from the multi-bucket config
    if "long_term" not in buckia_config:
        # If no long-term bucket is defined, use the first one
        bucket_name = next(iter(buckia_config.configs.keys()))
        logger.warning(f"No 'long_term' bucket config found, using '{bucket_name}' instead")
        return buckia_config.configs[bucket_name]
    else:
        return buckia_config.configs["long_term"]


# The patch_token_manager fixture has been removed.
# We now use the actual TokenManager implementation which retrieves tokens
# from environment variables in the format buckia.<namespace>.<context>
# For example: buckia.buckia.bunny, buckia.buckia.bunny_storage, etc.
# When running tests locally, create a .env file with your API tokens.
# See TESTING.md for details.


@pytest.fixture(scope="session")
def bucket_client_long_term(bucket_config_long_term: BucketConfig) -> BuckiaClient:
    """Create a BuckiaClient instance for long-term storage tests"""
    # Initialize a client with the bucket_config
    # Note: The patch_token_manager fixture will be applied automatically
    # because it has autouse=True
    client = BuckiaClient(bucket_config_long_term)

    # Check if we're running in CI or have valid credentials
    # or integration tests are explicitly enabled
    run_integration = os.environ.get("CI") == "1"

    if run_integration:
        # Verify that credentials work
        try:
            connection_results = client.test_connection()
            if not any(connection_results.values()):
                pytest.skip(f"Skipping test due to connection failure: {connection_results}")
        except Exception as e:
            pytest.skip(f"Connection error: {str(e)}")
    else:
        # Skip connection test for local development without real credentials
        pytest.skip("Skipping connection tests - integration tests not enabled")

    return client


@pytest.fixture(scope="session")
def buckia_client(bucket_config: BucketConfig) -> BuckiaClient:
    """Create a BuckiaClient instance for tests"""
    # Initialize a client with the bucket_config
    # Note: The patch_token_manager fixture will be applied automatically
    # because it has autouse=True
    client = BuckiaClient(bucket_config)

    # Check if we're running in CI or have valid credentials
    # or integration tests are explicitly enabled
    run_integration = (
        os.environ.get("CI") == "1"
        or os.environ.get("BUNNY_API_KEY")
        or os.environ.get("RUN_INTEGRATION_TESTS") == "1"
    )

    if run_integration:
        # Only test connections when we actually have credentials
        if not os.environ.get("BUNNY_API_KEY"):
            pytest.skip("Skipping Bunny.net tests - no API key provided")

        # Verify that credentials work
        try:
            connection_results = client.test_connection()
            if not any(connection_results.values()):
                pytest.skip(f"Skipping test due to connection failure: {connection_results}")
        except Exception as e:
            pytest.skip(f"Connection error: {str(e)}")
    else:
        # Skip connection test for local development without real credentials
        pytest.skip("Skipping connection tests - integration tests not enabled")

    return client


@pytest.fixture(scope="function")
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def test_file_factory(temp_directory: Generator[Path, None, None]) -> Callable[[str, int], Path]:
    """Factory to create test files with specific sizes and content"""

    def _create_file(name: str, size: int = 1024) -> Path:
        """Create a test file with specified size

        Args:
            name: Name for the test file
            size: Size in bytes

        Returns:
            Path to the created file
        """
        file_path = temp_directory / name

        # Create file with random content of the specified size
        with open(file_path, "wb") as f:
            # Make the content somewhat unique and identifiable
            header = f"TEST_FILE_{TEST_RUN_ID}_{name}_{time.time()}".encode()
            padding_size = size - len(header)
            if padding_size > 0:
                padding = os.urandom(padding_size)
                f.write(header + padding)
            else:
                f.write(header[:size])

        return file_path

    return _create_file


@pytest.fixture(scope="function")
def test_directory_factory(
    temp_directory: Generator[Path, None, None], test_file_factory: Callable[[str, int], Path]
) -> Callable[[str, Dict[str, int]], Path]:
    """Factory to create test directories with multiple files"""

    def _create_directory(name: str, files: Dict[str, int] = {}) -> Path:
        """Create a test directory with files

        Args:
            name: Name for the test directory
            files: Dictionary mapping file names to sizes

        Returns:
            Path to the created directory
        """
        dir_path = temp_directory / name
        dir_path.mkdir(exist_ok=True)

        # Create specified files
        for file_name, size in files.items():
            file_path = dir_path / file_name
            # Create parent directories if needed (for nested files)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                header = f"TEST_FILE_{TEST_RUN_ID}_{name}/{file_name}_{time.time()}".encode()
                padding_size = size - len(header)
                if padding_size > 0:
                    padding = os.urandom(padding_size)
                    f.write(header + padding)
                else:
                    f.write(header[:size])

        return dir_path

    return _create_directory


def list_token_env_vars(verbose: bool = False) -> None:
    """
    Debug function to list all relevant environment variables for Buckia tokens

    Args:
        verbose: If True, show values (masked) of environment variables
    """
    logger.info("=== Checking environment variables for Buckia tokens ===")

    # Also check for .env file
    dotenv_paths = [
        Path.cwd() / ".env",
        Path(os.path.dirname(os.path.dirname(__file__))) / ".env",
        Path.home() / ".buckia" / ".env",
    ]

    env_file_found = False
    for path in dotenv_paths:
        if path.exists():
            logger.info(f"Found .env file: {path}")
            env_file_found = True
            break

    if not env_file_found:
        logger.warning("No .env file found. Create one from .env.example for local testing.")

    # First check for the "demo" token context used by all integration tests
    demo_env_var = "buckia_buckia_demo"
    found_vars = 0

    # Check for the primary demo token context first (used by all integration tests)
    if os.environ.get(demo_env_var):
        value = os.environ.get(demo_env_var)
        masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"

        if verbose:
            logger.info(f"✓ Found {demo_env_var} = {masked_value} (REQUIRED for integration tests)")
        else:
            logger.info(f"✓ Found {demo_env_var} (REQUIRED for integration tests)")
        found_vars += 1
    else:
        logger.error(
            f"!!! MISSING {demo_env_var} - This environment variable is REQUIRED for integration tests !!!"
        )

    # Known bucket contexts from token_manager.py (these are not currently used in tests)
    known_contexts = ["bunny", "bunny_storage", "s3", "linode", "b2"]

    # Check for environment variables in the buckia.<namespace>.<context> format
    logger.info("Checking other token contexts (not currently used in tests):")
    for context in known_contexts:
        env_name = f"buckia_buckia_{context}"
        if os.environ.get(env_name):
            # Mask the value for security
            value = os.environ.get(env_name)
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"

            if verbose:
                logger.info(f"✓ Found {env_name} = {masked_value}")
            else:
                logger.info(f"✓ Found {env_name}")
            found_vars += 1
        else:
            logger.info(f"- Not found: {env_name}")

    # Check for legacy environment variables as well
    legacy_vars = {
        "BUNNY_API_KEY": "bunny",
        "BUNNY_STORAGE_API_KEY": "bunny_storage",
        "AWS_ACCESS_KEY_ID": "s3",
        "LINODE_TOKEN": "linode",
        "B2_APPLICATION_KEY": "b2",
    }

    for env_name, context in legacy_vars.items():
        if os.environ.get(env_name):
            if verbose:
                value = os.environ.get(env_name)
                masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
                logger.info(
                    f"✓ Found legacy variable {env_name} = {masked_value} (prefer buckia.buckia.{context})"
                )
            else:
                logger.info(f"✓ Found legacy variable {env_name} (prefer buckia.buckia.{context})")
            found_vars += 1

    # Check for buckia configuration variables
    config_vars = ["BUNNY_STORAGE_ZONE", "AWS_REGION", "LINODE_BUCKET", "B2_APPLICATION_KEY_ID"]
    for var in config_vars:
        if os.environ.get(var):
            if verbose:
                logger.info(f"✓ Found config variable {var} = {os.environ.get(var)}")
            else:
                logger.info(f"✓ Found config variable {var}")
            found_vars += 1

    # Log summary
    if found_vars == 0:
        logger.error(
            "!!! No token environment variables found. Tests requiring authentication will fail !!!"
        )
        logger.error(
            "Create a .env file using .env.example as a template, or set environment variables manually."
        )
    else:
        logger.info(f"Found {found_vars} token-related environment variables")

    logger.info("=" * 60)


@pytest.fixture(scope="function", autouse=True)
def test_setup_teardown(request: FixtureRequest) -> None:
    """Setup and teardown for each test"""
    # Setup - Log test start
    test_name = request.node.name
    module_name = request.node.module.__name__

    # Only run the environment variable check once per test session
    # and only for integration tests
    if module_name.startswith("integration") and not hasattr(
        test_setup_teardown, "_env_vars_checked"
    ):
        test_setup_teardown._env_vars_checked = True
        list_token_env_vars()

    logger.info(f"Starting test: {module_name}::{test_name}")

    # Run the test
    yield

    # Teardown - Log test end
    logger.info(f"Completed test: {module_name}::{test_name}")


@pytest.fixture(scope="function")
def remote_test_prefix(request: FixtureRequest) -> str:
    """Generate a unique prefix for remote test files"""
    # Create a unique ID for each test by combining the global ID with the test name
    test_name_hash = str(hash(request.node.name) % 10000).zfill(4)
    test_id = f"buckia_test_{TEST_RUN_ID}_{test_name_hash}"

    # Log the test prefix
    logger.info(f"Test '{request.node.name}' using remote prefix: {test_id}")
    return test_id


@pytest.fixture(scope="function")
def cleanup_remote_files(
    request: FixtureRequest, buckia_client: BuckiaClient, remote_test_prefix: str
) -> Callable[[], None]:
    """Delete test files and directories from remote storage after test"""

    def _cleanup() -> None:
        """Delete all files and directories with the test prefix"""
        # Check cleanup options
        skip_cleanup = request.config.getoption("--skip-cleanup")
        preserve_remote = request.config.getoption("--preserve-remote")

        if skip_cleanup or preserve_remote:
            logger.info(f"Preserving remote files with prefix: {remote_test_prefix}")
            return

        # Find all files with the test prefix
        remote_files = buckia_client.list_files()
        test_files = [path for path in remote_files.keys() if path.startswith(remote_test_prefix)]

        if test_files:
            logger.info(
                f"Cleaning up {len(test_files)} remote files with prefix: {remote_test_prefix}"
            )

            # Sort paths by length in descending order to delete deeper paths first
            # This helps ensure we clean up nested directories properly
            for remote_path in sorted(test_files, key=len, reverse=True):
                buckia_client.delete_file(remote_path)

            # After deleting all files, try to delete any empty directories
            # Extract unique directory paths from file paths
            dirs_to_clean = set()
            for file_path in test_files:
                # Extract directory components
                path_parts = file_path.split("/")
                for i in range(1, len(path_parts)):
                    dir_path = "/".join(path_parts[:i])
                    if dir_path.startswith(remote_test_prefix):
                        dirs_to_clean.add(dir_path)

            # Delete directories from deepest to shallowest
            if dirs_to_clean:
                logger.info(f"Attempting to clean up {len(dirs_to_clean)} directories")
                for dir_path in sorted(dirs_to_clean, key=len, reverse=True):
                    try:
                        buckia_client.delete_file(dir_path)
                    except Exception as e:
                        # Ignore errors when deleting directories
                        logger.debug(f"Could not delete directory {dir_path}: {str(e)}")
        else:
            logger.info(f"No remote files found with prefix: {remote_test_prefix}")

    # Register cleanup to run after test
    request.addfinalizer(_cleanup)
    return _cleanup
