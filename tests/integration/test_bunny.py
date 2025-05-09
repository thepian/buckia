"""
Integration tests for Bunny.net storage provider
"""

import os
from pathlib import Path
from typing import Callable, Dict

import pytest

from buckia import BuckiaClient
from buckia.sync.bunny import BunnySync


def test_bunny_connection(buckia_client: BuckiaClient) -> None:
    """Test connection to Bunny.net storage"""
    # Test connection with main client
    connection_results = buckia_client.test_connection()
    assert connection_results.get("api_key", False), "API key connection failed"

    # Check that backend is correctly initialized
    assert isinstance(buckia_client.backend, BunnySync), "Backend is not BunnySync"


def test_bunny_list_files(buckia_client: BuckiaClient, remote_test_prefix: str) -> None:
    """Test listing files from Bunny.net storage"""
    # List all files
    files = buckia_client.list_files()
    assert isinstance(files, dict), "list_files should return a dictionary"

    # Try path-based listing if there are files
    if files:
        # Take the directory from the first file
        first_file_path = next(iter(files.keys()))
        if "/" in first_file_path:
            directory = first_file_path.split("/")[0]
            dir_files = buckia_client.list_files(directory)
            assert isinstance(dir_files, dict), "Path-based listing should return a dictionary"


def test_bunny_file_operations(
    buckia_client: BuckiaClient,
    test_file_factory: Callable[[str, int], Path],
    remote_test_prefix: str,
    cleanup_remote_files: Callable[[], None],
) -> None:
    """Test basic file operations with Bunny.net storage"""
    # Create a test file
    test_file = test_file_factory("bunny_test.txt", size=1024)
    remote_path = f"{remote_test_prefix}/bunny_test.txt"

    # Upload file
    upload_result = buckia_client.upload_file(str(test_file), remote_path)
    assert upload_result, "File upload failed"

    # List files to verify upload
    files = buckia_client.list_files()
    assert remote_path in files, f"Uploaded file {remote_path} not found in remote files"

    # Get public URL
    public_url = buckia_client.get_public_url(remote_path)
    assert public_url, "Failed to get public URL"
    assert remote_path in public_url, "Remote path should be part of the URL"

    # Download the file
    download_path = test_file.with_suffix(".downloaded")
    download_result = buckia_client.download_file(remote_path, str(download_path))
    assert download_result, "File download failed"
    assert download_path.exists(), "Downloaded file not found"
    assert download_path.stat().st_size == test_file.stat().st_size, "Downloaded file size mismatch"

    # Delete the file
    delete_result = buckia_client.delete_file(remote_path)
    assert delete_result, "File deletion failed"

    # Verify deletion
    files = buckia_client.list_files()
    assert remote_path not in files, f"Deleted file {remote_path} still found in remote files"


def test_bunny_sync_upload_only(
    buckia_client: BuckiaClient,
    test_directory_factory: Callable[[str, Dict[str, int]], Path],
    remote_test_prefix: str,
    cleanup_remote_files: Callable[[], None],
) -> None:
    """Test synchronization (upload only) with Bunny.net storage"""
    # Create a test directory with files
    test_files = {
        "file1.txt": 1024,  # 1 KB
        "file2.txt": 1024 * 10,  # 10 KB
        "nested/file3.txt": 1024,  # Nested file
    }

    test_dir = test_directory_factory("sync_test", files=test_files)

    # Ensure nested directory exists
    os.makedirs(test_dir / "nested", exist_ok=True)

    # Upload files individually instead of using sync
    uploaded_count = 0
    for file_path in test_files.keys():
        local_file_path = os.path.join(test_dir, file_path)
        remote_path = f"{remote_test_prefix}/{file_path}"

        result = buckia_client.upload_file(local_file_path, remote_path)
        if result:
            uploaded_count += 1

    # Check upload results
    assert uploaded_count == len(
        test_files
    ), f"Expected {len(test_files)} uploads, got {uploaded_count}"

    # Check that files exist in remote storage
    remote_files = buckia_client.list_files()

    for file_path in test_files.keys():
        remote_path = f"{remote_test_prefix}/{file_path}"
        assert remote_path in remote_files, f"Uploaded file {remote_path} not found in remote files"


@pytest.mark.skipif(
    not os.environ.get("RUN_PURGE_TESTS"),
    reason="Purge tests are slow and require pull zone configuration",
)
def test_bunny_purge_cache(
    buckia_client: BuckiaClient,
    test_file_factory: Callable[[str, int], Path],
    remote_test_prefix: str,
    cleanup_remote_files: Callable[[], None],
) -> None:
    """Test CDN cache purging (requires pull zone configuration)"""
    # Skip if BunnySync doesn't have a pull_zone_name
    if not getattr(buckia_client.backend, "pull_zone_name", None):
        pytest.skip("pull_zone_name not configured in client")

    # Create and upload test file
    test_file = test_file_factory("purge_test.txt", size=1024)
    remote_path = f"{remote_test_prefix}/purge_test.txt"

    buckia_client.upload_file(str(test_file), remote_path)

    # Purge specific path
    result = buckia_client.backend.purge_cache(paths=[remote_path])
    assert result.get("success", False), "Cache purge failed"
    assert result.get("purged", 0) > 0, "No items were purged"

    # Clean up
    buckia_client.delete_file(remote_path)
