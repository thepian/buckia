"""
Test fixtures and utilities for Buckia testing
"""

import os
import tempfile
import time
import uuid
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Generator

import pytest
import yaml
from dotenv import load_dotenv

from buckia import BucketConfig, BuckiaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("buckia.test")

# Load environment variables from .env file if it exists
# Only load variables that are not already set in the environment
dotenv_path = Path(os.path.dirname(os.path.dirname(__file__))) / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path, override=False)

# Unique test ID to prevent conflicts between test runs
TEST_RUN_ID = str(uuid.uuid4())[:8]

# Test file sizes (in bytes)
TEST_FILE_SIZES = {
    "small": 1024,  # 1 KB
    "medium": 1024 * 100,  # 100 KB
    "large": 1024 * 1024,  # 1 MB
}


def pytest_addoption(parser):
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


@pytest.fixture(scope="session")
def test_config(request) -> Dict[str, Any]:
    """Load test configuration from file"""
    config_path = request.config.getoption("--config")

    # Check config file exists
    if not os.path.exists(config_path):
        # Try environment variables if config file doesn't exist
        if os.environ.get("BUNNY_API_KEY") and os.environ.get("BUNNY_STORAGE_ZONE"):
            return {
                "provider": "bunny",
                "bucket_name": os.environ.get("BUNNY_STORAGE_ZONE"),
                "auth": {
                    "api_key": os.environ.get("BUNNY_API_KEY"),
                    "storage_api_key": os.environ.get("BUNNY_STORAGE_API_KEY"),
                },
                "sync": {
                    "delete_orphaned": True,
                    "max_workers": 4,
                },
                "checksum_algorithm": "sha256",
            }
        else:
            pytest.fail(
                f"Test config file not found: {config_path} and no environment variables set"
            )

    # Load config from file
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


@pytest.fixture(scope="session")
def bucket_config(test_config) -> BucketConfig:
    """Create a BucketConfig object from test configuration"""
    return BucketConfig(
        provider=test_config["provider"],
        bucket_name=test_config["bucket_name"],
        credentials=test_config["auth"],
        delete_orphaned=test_config.get("sync", {}).get("delete_orphaned", False),
        max_workers=test_config.get("sync", {}).get("max_workers", 4),
        checksum_algorithm=test_config.get("checksum_algorithm", "sha256"),
    )


@pytest.fixture(scope="session")
def buckia_client(bucket_config) -> BuckiaClient:
    """Create a BuckiaClient instance for tests"""
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
                pytest.skip(
                    f"Skipping test due to connection failure: {connection_results}"
                )
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
def test_file_factory(temp_directory) -> Callable[[str, int], Path]:
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
    temp_directory, test_file_factory
) -> Callable[[str, Dict[str, int]], Path]:
    """Factory to create test directories with multiple files"""

    def _create_directory(name: str, files: Dict[str, int] = None) -> Path:
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
        if files:
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


@pytest.fixture(scope="function", autouse=True)
def test_setup_teardown(request):
    """Setup and teardown for each test"""
    # Setup - Log test start
    test_name = request.node.name
    module_name = request.node.module.__name__
    
    logger.info(f"Starting test: {module_name}::{test_name}")
    
    # Run the test
    yield
    
    # Teardown - Log test end
    logger.info(f"Completed test: {module_name}::{test_name}")


@pytest.fixture(scope="function")
def remote_test_prefix(request) -> str:
    """Generate a unique prefix for remote test files"""
    # Create a unique ID for each test by combining the global ID with the test name
    test_name_hash = str(hash(request.node.name) % 10000).zfill(4)
    test_id = f"buckia_test_{TEST_RUN_ID}_{test_name_hash}"
    
    # Log the test prefix
    logger.info(f"Test '{request.node.name}' using remote prefix: {test_id}")
    return test_id


@pytest.fixture(scope="function")
def cleanup_remote_files(
    request, buckia_client, remote_test_prefix
) -> Callable[[], None]:
    """Delete test files and directories from remote storage after test"""

    def _cleanup():
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
            logger.info(f"Cleaning up {len(test_files)} remote files with prefix: {remote_test_prefix}")
            
            # Sort paths by length in descending order to delete deeper paths first
            # This helps ensure we clean up nested directories properly
            for remote_path in sorted(test_files, key=len, reverse=True):
                buckia_client.delete_file(remote_path)
            
            # After deleting all files, try to delete any empty directories
            # Extract unique directory paths from file paths
            dirs_to_clean = set()
            for file_path in test_files:
                # Extract directory components
                path_parts = file_path.split('/')
                for i in range(1, len(path_parts)):
                    dir_path = '/'.join(path_parts[:i])
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
