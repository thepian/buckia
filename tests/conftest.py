"""
Test fixtures and utilities for Buckia testing
"""

import os
import time
import uuid
import pytest
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, Callable, Generator

from buckia import BuckiaClient, BucketConfig

# Unique test ID to prevent conflicts between test runs
TEST_RUN_ID = str(uuid.uuid4())[:8]

# Test file sizes (in bytes)
TEST_FILE_SIZES = {
    'small': 1024,        # 1 KB
    'medium': 1024*100,   # 100 KB
    'large': 1024*1024,   # 1 MB
}


def pytest_addoption(parser):
    """Add command-line options for tests"""
    parser.addoption(
        "--config", 
        default=os.path.join(os.path.dirname(__file__), "config", "test_config.yaml"),
        help="Path to test configuration file. Default: tests/config/test_config.yaml"
    )
    parser.addoption(
        "--skip-cleanup", 
        action="store_true", 
        help="Skip cleaning up test data after tests"
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
            pytest.fail(f"Test config file not found: {config_path} and no environment variables set")
    
    # Load config from file
    with open(config_path, 'r') as f:
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
    if os.environ.get("CI") or os.environ.get("BUNNY_API_KEY"):
        # Test connection in CI or when real credentials are provided
        connection_results = client.test_connection()
        if not any(connection_results.values()):
            pytest.fail(f"Failed to connect to {bucket_config.provider}: {connection_results}")
    else:
        # Skip connection test for local development without real credentials
        pytest.skip("Skipping connection tests - no real credentials provided")
    
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
        with open(file_path, 'wb') as f:
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
def test_directory_factory(temp_directory, test_file_factory) -> Callable[[str, Dict[str, int]], Path]:
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
                with open(file_path, 'wb') as f:
                    header = f"TEST_FILE_{TEST_RUN_ID}_{name}/{file_name}_{time.time()}".encode()
                    padding_size = size - len(header)
                    if padding_size > 0:
                        padding = os.urandom(padding_size)
                        f.write(header + padding)
                    else:
                        f.write(header[:size])
        
        return dir_path
    
    return _create_directory


@pytest.fixture(scope="function")
def remote_test_prefix() -> str:
    """Generate a unique prefix for remote test files"""
    return f"buckia_test_{TEST_RUN_ID}"


@pytest.fixture(scope="function")
def cleanup_remote_files(request, buckia_client, remote_test_prefix) -> Callable[[], None]:
    """Delete test files from remote storage after test"""
    def _cleanup():
        """Delete all files with the test prefix"""
        skip_cleanup = request.config.getoption("--skip-cleanup")
        if skip_cleanup:
            print(f"\nSkipping cleanup of remote files with prefix: {remote_test_prefix}")
            return
            
        print(f"\nCleaning up remote files with prefix: {remote_test_prefix}")
        remote_files = buckia_client.list_files()
        for remote_path in list(remote_files.keys()):
            if remote_path.startswith(remote_test_prefix):
                buckia_client.delete_file(remote_path)
    
    # Register cleanup to run after test
    request.addfinalizer(_cleanup)
    return _cleanup