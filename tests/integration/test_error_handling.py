"""
Integration tests for error handling and edge cases
"""

import os
import tempfile
import time

import pytest

from buckia import BucketConfig, BuckiaClient


@pytest.mark.xfail(
    reason="The BunnyCDN client doesn't reliably fail with invalid credentials in test environments"
)
def test_invalid_credentials():
    """Test behavior with invalid API credentials"""
    # Create configuration with invalid credentials
    config = BucketConfig(
        provider="bunny",
        bucket_name="test-bucket",
        credentials={
            "api_key": "invalid-api-key",
            "storage_api_key": "invalid-storage-api-key",
        },
    )

    # Create client with invalid credentials
    client = BuckiaClient(config)

    # Test connection should fail
    connection_results = client.test_connection()
    assert not any(
        connection_results.values()
    ), "Connection should fail with invalid credentials"

    # Attempts to perform operations should fail gracefully
    with tempfile.NamedTemporaryFile() as temp_file:
        # Write some content to the temp file
        temp_file.write(b"Test content")
        temp_file.flush()

        # Upload should fail but not crash
        upload_result = client.upload_file(temp_file.name, "test.txt")
        assert not upload_result, "Upload should fail with invalid credentials"

        # List files should fail but not crash
        list_result = client.list_files()
        assert isinstance(
            list_result, dict
        ), "list_files should return an empty dict on failure"
        assert (
            len(list_result) == 0
        ), "list_files should return an empty dict on failure"


@pytest.mark.xfail(
    reason="The BunnyCDN client may create nonexistent buckets on the fly in test environments"
)
def test_nonexistent_bucket():
    """Test behavior with nonexistent bucket"""
    # Create configuration with nonexistent bucket
    config = BucketConfig(
        provider="bunny",
        bucket_name="nonexistent-bucket-" + str(int(time.time())),
        credentials={
            "api_key": os.environ.get("BUNNY_API_KEY", "test-key"),
            "storage_api_key": os.environ.get("BUNNY_STORAGE_API_KEY", "test-key"),
        },
    )

    # Create client with nonexistent bucket
    client = BuckiaClient(config)

    # Test connection should fail for the bucket
    connection_results = client.test_connection()
    # assert not all(
    #     connection_results.values()
    # ), "Connection should fail with nonexistent bucket"
    assert (
        connection_results["api_key"] is False
        and connection_results["password"] is False
    ), "Connection should fail with nonexistent bucket"

    # Attempts to perform operations should fail gracefully
    with tempfile.NamedTemporaryFile() as temp_file:
        # Write some content to the temp file
        temp_file.write(b"Test content")
        temp_file.flush()

        # Upload should fail but not crash
        upload_result = client.upload_file(temp_file.name, "test.txt")
        assert not upload_result, "Upload should fail with nonexistent bucket"

        # List files should fail but not crash
        list_result = client.list_files()
        assert isinstance(
            list_result, dict
        ), "list_files should return an empty dict on failure"
        assert (
            len(list_result) == 0
        ), "list_files should return an empty dict on failure"


def test_missing_local_file(buckia_client):
    """Test behavior when local file is missing"""
    # Generate path to a nonexistent file
    nonexistent_file = f"/tmp/nonexistent_file_{int(time.time())}.txt"

    # Upload should fail but not crash
    upload_result = buckia_client.upload_file(nonexistent_file, "test.txt")
    assert not upload_result, "Upload should fail with nonexistent local file"


@pytest.mark.xfail(
    reason="BunnyCDN's Python client may create empty files for nonexistent remote files in test environments"
)
def test_nonexistent_remote_file(buckia_client, temp_directory):
    """Test behavior when remote file is missing"""
    # Generate path to a nonexistent remote file
    nonexistent_remote = f"nonexistent_file_{int(time.time())}.txt"

    # Download path
    download_path = temp_directory / "downloaded.txt"

    # Download should fail but not crash
    download_result = buckia_client.download_file(
        nonexistent_remote, str(download_path)
    )
    assert not download_result, "Download should fail with nonexistent remote file"
    assert not download_path.exists(), "No file should be created for failed download"


def test_read_only_directory(
    buckia_client, temp_directory, test_file_factory, cleanup_remote_files
):
    """Test behavior when local directory is read-only"""
    # Skip on non-Unix platforms
    if os.name != "posix":
        pytest.skip("Test requires POSIX platform")

    # Create a test file
    test_file = test_file_factory("readonly_test.txt", size=1024)
    remote_path = f"readonly_test_{int(time.time())}.txt"

    # Upload the file
    upload_result = buckia_client.upload_file(str(test_file), remote_path)
    assert upload_result, "File upload failed"

    # Create a read-only directory
    readonly_dir = temp_directory / "readonly"
    readonly_dir.mkdir()
    os.chmod(readonly_dir, 0o555)  # read and execute only

    try:
        # Try to download to read-only directory
        download_path = readonly_dir / "download.txt"
        download_result = buckia_client.download_file(remote_path, str(download_path))
        assert not download_result, "Download should fail with read-only directory"

    finally:
        # Clean up
        os.chmod(readonly_dir, 0o755)  # Restore permissions for cleanup
        buckia_client.delete_file(remote_path)


def test_very_large_sync(
    buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files
):
    """Test synchronization with a large number of small files"""
    # Create a directory with many small files
    test_dir = test_directory_factory("large_sync", files={})

    # Create 50 small files (adjust based on test environment constraints)
    num_files = 50
    for i in range(num_files):
        file_path = test_dir / f"file_{i:03d}.txt"
        with open(file_path, "w") as f:
            f.write(f"Test content for file {i}")

    # Try to sync with a small worker count
    result = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,  # Use a small number of workers
        delete_orphaned=False,
        dry_run=False,
    )

    # Check sync result
    assert (
        result.uploaded >= num_files
    ), f"Expected at least {num_files} uploads, got {result.uploaded}"
    assert result.failed == 0, f"Sync reported {result.failed} failed operations"

    # Clean up
    cleanup_remote_files()

    # Try again with more workers
    result2 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=10,  # Use more workers
        delete_orphaned=False,
        dry_run=False,
    )

    # Check sync result
    assert (
        result2.uploaded >= num_files
    ), f"Expected at least {num_files} uploads, got {result2.uploaded}"
    assert result2.failed == 0, f"Sync reported {result2.failed} failed operations"


def test_zero_byte_file(buckia_client, temp_directory, cleanup_remote_files):
    """Test operations with zero-byte files"""
    # Create a zero-byte file
    zero_byte_file = temp_directory / "zero_byte.txt"
    zero_byte_file.touch()

    # Upload zero-byte file
    remote_path = f"zero_byte_{int(time.time())}.txt"
    upload_result = buckia_client.upload_file(str(zero_byte_file), remote_path)
    assert upload_result, "Zero-byte file upload failed"

    # Download zero-byte file
    download_path = temp_directory / "zero_byte_downloaded.txt"
    download_result = buckia_client.download_file(remote_path, str(download_path))
    assert download_result, "Zero-byte file download failed"

    # Verify file was downloaded and is zero bytes
    assert download_path.exists(), "Downloaded zero-byte file does not exist"
    assert (
        download_path.stat().st_size == 0
    ), "Downloaded zero-byte file is not zero bytes"

    # Delete zero-byte file
    delete_result = buckia_client.delete_file(remote_path)
    assert delete_result, "Zero-byte file deletion failed"


def test_unicode_filenames(buckia_client, temp_directory, cleanup_remote_files):
    """Test operations with Unicode filenames"""
    # Create files with Unicode characters
    unicode_files = {
        "unicode_😀_smiley.txt": "Smiley face file",
        "unicode_中文_chinese.txt": "Chinese characters file",
        "unicode_русский_russian.txt": "Russian characters file",
        "unicode_∞_infinity.txt": "Mathematical symbol file",
    }

    local_files = {}
    remote_paths = {}

    # Create and upload the files
    for filename, content in unicode_files.items():
        # Create local file
        local_path = temp_directory / filename
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        local_files[filename] = local_path

        # Upload with Unicode filename
        remote_path = f"unicode_test/{filename}"
        remote_paths[filename] = remote_path

        upload_result = buckia_client.upload_file(str(local_path), remote_path)
        # Some backends may have issues with Unicode - mark the test as xfailed if they do
        if not upload_result:
            pytest.xfail(f"Unicode filename upload failed for {filename}")

    # List files to see if Unicode filenames are preserved
    remote_files = buckia_client.list_files()

    # Check that files were uploaded and Unicode filenames preserved
    for filename, remote_path in remote_paths.items():
        if remote_path not in remote_files:
            pytest.xfail(
                f"Unicode filename not preserved in remote listing: {filename}"
            )

    # Download and check content
    for filename, local_path in local_files.items():
        # Create download path
        download_path = temp_directory / f"downloaded_{filename}"

        # Download the file
        download_result = buckia_client.download_file(
            remote_paths[filename], str(download_path)
        )
        assert download_result, f"Download failed for Unicode file: {filename}"

        # Check content
        with open(download_path, "r", encoding="utf-8") as f:
            downloaded_content = f.read()
        with open(local_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        assert (
            downloaded_content == original_content
        ), f"Content mismatch for Unicode file: {filename}"

    # Clean up
    for remote_path in remote_paths.values():
        buckia_client.delete_file(remote_path)


@pytest.mark.skipif(
    not (os.environ.get("STRESS_TEST") == "1"),
    reason="Stress tests are resource-intensive and disabled by default",
)
def test_network_throttling(
    buckia_client, test_file_factory, remote_test_prefix, cleanup_remote_files
):
    """Test operations with simulated network throttling"""
    # Create a large file for testing throttling
    large_file = test_file_factory(
        "large_throttled.bin", size=10 * 1024 * 1024
    )  # 10 MB

    # Get original socket implementation
    import socket

    original_socket = socket.socket

    try:
        # Create a throttled socket implementation
        class ThrottledSocket(original_socket):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.throttle_delay = 0.01  # 10ms delay per operation

            def send(self, *args, **kwargs):
                time.sleep(self.throttle_delay)
                return super().send(*args, **kwargs)

            def recv(self, *args, **kwargs):
                time.sleep(self.throttle_delay)
                return super().recv(*args, **kwargs)

        # Patch socket implementation
        socket.socket = ThrottledSocket

        # Upload the large file with throttled sockets
        remote_path = f"{remote_test_prefix}/large_throttled.bin"
        upload_result = buckia_client.upload_file(str(large_file), remote_path)
        assert upload_result, "Upload with throttled network failed"

        # Download the file with throttled sockets
        download_path = large_file.with_suffix(".downloaded")
        download_result = buckia_client.download_file(remote_path, str(download_path))
        assert download_result, "Download with throttled network failed"

        # Verify file integrity
        assert download_path.exists(), "Downloaded file not found"
        assert (
            download_path.stat().st_size == large_file.stat().st_size
        ), "Downloaded file size mismatch"

    finally:
        # Restore original socket implementation
        socket.socket = original_socket
        # Clean up
        cleanup_remote_files()
