"""
Unit tests for the BaseSync class and SyncResult
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from buckia.config import BucketConfig
from buckia.sync.base import BaseSync, SyncResult, SyncState, SyncStateEntry


class TestSyncImplementation(BaseSync):
    """Concrete implementation of BaseSync for testing"""

    def __init__(self, config):
        super().__init__(config)
        self.remote_files = {}
        self.connect_result = True

    def connect(self):
        return self.connect_result

    def test_connection(self):
        return {"test": True}

    def list_remote_files(self, path=None):
        return self.remote_files

    def upload_file(self, local_file_path, remote_path):
        self.remote_files[remote_path] = {"Size": os.path.getsize(local_file_path)}
        return True

    def download_file(self, remote_path, local_file_path):
        return remote_path in self.remote_files

    def delete_file(self, remote_path):
        if remote_path in self.remote_files:
            del self.remote_files[remote_path]
            return True
        return False

    def get_public_url(self, remote_path):
        return f"https://example.com/{remote_path}"


def test_sync_result_init():
    """Test SyncResult initialization"""
    # Test with defaults
    result = SyncResult()
    assert result.success is True
    assert result.uploaded == 0
    assert result.downloaded == 0
    assert result.deleted == 0
    assert result.failed == 0
    assert result.unchanged == 0
    assert result.errors == []
    assert result.protected_skipped == 0
    assert result.cached == 0  # Kept for backward compatibility but no longer used

    # Test with custom values
    result = SyncResult(
        success=False,
        uploaded=5,
        downloaded=3,
        deleted=1,
        failed=2,
        unchanged=10,
        errors=["Error 1", "Error 2"],
        protected_skipped=3,
        cached=4,
    )

    assert result.success is False
    assert result.uploaded == 5
    assert result.downloaded == 3
    assert result.deleted == 1
    assert result.failed == 2
    assert result.unchanged == 10
    assert result.errors == ["Error 1", "Error 2"]
    assert result.protected_skipped == 3
    assert result.cached == 4  # Kept for backward compatibility but no longer used

    # Test error list initialization
    result = SyncResult()
    assert result.errors == []

    result = SyncResult(errors=None)
    assert result.errors == []


def test_sync_result_str():
    """Test SyncResult string representation"""
    result = SyncResult(
        uploaded=5,
        downloaded=3,
        deleted=1,
        unchanged=10,
        cached=2,
        protected_skipped=1,
        failed=0,
    )

    result_str = str(result)

    assert "5 uploaded" in result_str
    assert "3 downloaded" in result_str
    assert "1 deleted" in result_str
    assert "10 unchanged" in result_str
    assert "2 cached" in result_str  # Kept for backward compatibility
    assert "1 protected skipped" in result_str
    assert "0 failed" in result_str


def test_base_sync_init():
    """Test BaseSync initialization"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    assert sync.config is config
    assert sync.logger.name == "buckia.TestSyncImplementation"


def test_calculate_checksum():
    """Test calculate_checksum method"""
    config = BucketConfig(provider="test", bucket_name="test-bucket", checksum_algorithm="sha256")

    sync = TestSyncImplementation(config)

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            temp_file.write(b"test content")
            temp_file.flush()

            # Calculate checksum
            checksum = sync.calculate_checksum(temp_file.name)

            # Verify it's a non-empty string
            assert isinstance(checksum, str)
            assert len(checksum) > 0

            # Test with md5 algorithm
            config.checksum_algorithm = "md5"
            md5_checksum = sync.calculate_checksum(temp_file.name)

            assert isinstance(md5_checksum, str)
            assert len(md5_checksum) > 0
            assert md5_checksum != checksum  # Different algorithm, different checksum

            # Test with sha1 algorithm
            config.checksum_algorithm = "sha1"
            sha1_checksum = sync.calculate_checksum(temp_file.name)

            assert isinstance(sha1_checksum, str)
            assert len(sha1_checksum) > 0
            assert sha1_checksum != checksum  # Different algorithm, different checksum

            # Test with unsupported algorithm (should default to sha256)
            config.checksum_algorithm = "unknown"
            unknown_checksum = sync.calculate_checksum(temp_file.name)

            assert unknown_checksum == checksum  # Should fall back to sha256

            # Test with nonexistent file
            os.unlink(temp_file.name)
            nonexistent_checksum = sync.calculate_checksum(temp_file.name)

            assert nonexistent_checksum == ""  # Empty string for errors

        finally:
            # Clean up in case unlink failed
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def test_get_local_files():
    """Test get_local_files method"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file in the root
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")

        # Create a subdirectory
        os.makedirs(os.path.join(temp_dir, "subdir"))

        # Create a file in the subdirectory
        with open(os.path.join(temp_dir, "subdir", "file2.txt"), "w") as f:
            f.write("file2 content")

        # Get local files
        with patch.object(sync, "calculate_checksum", return_value="checksum"):
            local_files = sync.get_local_files(temp_dir)

            # Should find both files with Windows/Unix path separator handling
            assert "file1.txt" in local_files
            assert local_files["file1.txt"] == "checksum"

            # The path is normalized to use forward slashes
            file2_path = "subdir/file2.txt"
            assert file2_path in local_files
            assert local_files[file2_path] == "checksum"


def test_get_local_files_in_paths():
    """Test get_local_files_in_paths method"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files in different subdirectories
        os.makedirs(os.path.join(temp_dir, "dir1"))
        os.makedirs(os.path.join(temp_dir, "dir2"))
        os.makedirs(os.path.join(temp_dir, "dir3"))

        # Create files in each directory
        with open(os.path.join(temp_dir, "dir1", "file1.txt"), "w") as f:
            f.write("file1 content")

        with open(os.path.join(temp_dir, "dir2", "file2.txt"), "w") as f:
            f.write("file2 content")

        with open(os.path.join(temp_dir, "dir3", "file3.txt"), "w") as f:
            f.write("file3 content")

        # Get local files from only dir1 and dir2
        with patch.object(sync, "calculate_checksum", return_value="checksum"):
            paths = ["dir1", "dir2"]
            local_files = sync.get_local_files_in_paths(temp_dir, paths)

            # Should find files in dir1 and dir2 but not dir3
            assert "dir1/file1.txt" in local_files
            assert "dir2/file2.txt" in local_files
            assert "dir3/file3.txt" not in local_files

            # Test with a specific file path
            paths = ["dir3/file3.txt"]
            local_files = sync.get_local_files_in_paths(temp_dir, paths)

            # Should find only the specific file
            assert "dir1/file1.txt" not in local_files
            assert "dir2/file2.txt" not in local_files
            assert "dir3/file3.txt" in local_files

            # Test with a nonexistent path
            paths = ["nonexistent"]
            local_files = sync.get_local_files_in_paths(temp_dir, paths)

            # Should be empty
            assert len(local_files) == 0


def test_sync_basic():
    """Test the basic sync operation"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")

        with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
            f.write("file2 content")

        # Setup remote files - one existing, one new to download
        sync.remote_files = {
            "file1.txt": {"Size": 100, "Checksum": "remote-checksum"},
            "file3.txt": {"Size": 200, "Checksum": "remote-checksum"},
        }

        # Mock methods
        with patch.object(sync, "calculate_checksum") as mock_checksum:
            with patch.object(sync, "upload_file") as mock_upload:
                with patch.object(sync, "download_file") as mock_download:
                    with patch.object(sync, "delete_file") as mock_delete:
                        # Set up checksums that differ from remote
                        mock_checksum.return_value = "local-checksum"
                        mock_upload.return_value = True
                        mock_download.return_value = True
                        mock_delete.return_value = True

                        # Run the sync
                        result = sync.sync(local_path=temp_dir, max_workers=2, delete_orphaned=True)

                        # All operations should succeed
                        assert result.success is True

                        # file1.txt - modified locally, should be uploaded
                        # file2.txt - new locally, should be uploaded
                        # file3.txt - exists only remotely, should be downloaded
                        assert result.uploaded == 2
                        assert result.downloaded == 1
                        assert result.deleted == 1  # file3.txt from remote would be deleted
                        assert result.failed == 0

                        # Check upload calls
                        assert mock_upload.call_count == 2

                        # Check download calls
                        assert mock_download.call_count == 1


def test_sync_dry_run():
    """Test sync with dry_run=True"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")

        # Setup remote files
        sync.remote_files = {"file2.txt": {"Size": 100, "Checksum": "remote-checksum"}}

        # Mock methods
        with patch.object(sync, "calculate_checksum") as mock_checksum:
            with patch.object(sync, "upload_file") as mock_upload:
                with patch.object(sync, "download_file") as mock_download:
                    with patch.object(sync, "delete_file") as mock_delete:
                        # Set up checksums
                        mock_checksum.return_value = "local-checksum"

                        # Run the sync with dry_run=True
                        result = sync.sync(local_path=temp_dir, delete_orphaned=True, dry_run=True)

                        # All operations should succeed, but no actual changes
                        assert result.success is True

                        # No actual uploads, downloads, or deletions
                        assert mock_upload.call_count == 0
                        assert mock_download.call_count == 0
                        assert mock_delete.call_count == 0


def test_sync_with_errors():
    """Test sync with errors in operations"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")

        # Setup remote files
        sync.remote_files = {"file2.txt": {"Size": 100, "Checksum": "remote-checksum"}}

        # Mock methods
        with patch.object(sync, "calculate_checksum") as mock_checksum:
            with patch.object(sync, "upload_file") as mock_upload:
                with patch.object(sync, "download_file") as mock_download:
                    # Set up checksums
                    mock_checksum.return_value = "local-checksum"

                    # Make operations fail
                    mock_upload.return_value = False
                    mock_download.side_effect = Exception("Download error")

                    # Run the sync
                    result = sync.sync(local_path=temp_dir)

                    # Operations should fail
                    assert result.success is False
                    assert result.failed == 2  # Both upload and download failed
                    assert len(result.errors) == 2


def test_sync_with_nonexistent_path():
    """Test sync with a nonexistent local path"""
    config = BucketConfig(provider="test", bucket_name="test-bucket")

    sync = TestSyncImplementation(config)

    # Create a temporary directory to use as a parent
    with tempfile.TemporaryDirectory() as temp_dir:
        # Nonexistent subdirectory
        nonexistent_path = os.path.join(temp_dir, "nonexistent")

        # This should raise NotADirectoryError
        with pytest.raises(NotADirectoryError):
            sync.sync(local_path=nonexistent_path)


# ---------------------------------------------------------------------------
# SyncState tests
# ---------------------------------------------------------------------------


def test_sync_state_load_missing_file():
    """Missing state file returns None without raising."""
    with tempfile.TemporaryDirectory() as tmp:
        state = SyncState.load(os.path.join(tmp, "nonexistent.json"))
        assert state is None


def test_sync_state_load_corrupt_file():
    """Corrupt JSON returns None without raising."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json{{")
        path = f.name
    try:
        assert SyncState.load(path) is None
    finally:
        os.unlink(path)


def test_sync_state_load_version_mismatch():
    """State file with a different version is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"version": 99, "bucket": "x", "synced_at": "", "files": {}}, f)
        path = f.name
    try:
        assert SyncState.load(path) is None
    finally:
        os.unlink(path)


def test_sync_state_save_and_load_roundtrip():
    """Saved state can be loaded back with the same data."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "state.json")
        state = SyncState(bucket="my-bucket")
        state.update_file("data/file.parquet", checksum="abc123", size=1024, mtime=1700000000.0)
        state.save(path)

        loaded = SyncState.load(path)
        assert loaded is not None
        assert loaded.bucket == "my-bucket"
        assert loaded.version == 1
        assert "data/file.parquet" in loaded.files
        entry = loaded.files["data/file.parquet"]
        assert entry.checksum == "abc123"
        assert entry.size == 1024
        assert entry.mtime == 1700000000.0


# ---------------------------------------------------------------------------
# State cache in get_local_files
# ---------------------------------------------------------------------------


def test_get_local_files_state_cache_hit():
    """Files whose mtime and size match the state cache skip calculate_checksum."""
    config = BucketConfig(provider="test", bucket_name="test-bucket")
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "data.parquet")
        with open(fpath, "wb") as f:
            f.write(b"x" * 512)

        stat = os.stat(fpath)
        state = SyncState(bucket="test-bucket")
        state.update_file("data.parquet", checksum="cached-checksum", size=stat.st_size, mtime=stat.st_mtime)

        with patch.object(sync, "calculate_checksum") as mock_checksum:
            files = sync.get_local_files(tmp, state=state)

        assert files["data.parquet"] == "cached-checksum"
        mock_checksum.assert_not_called()


def test_get_local_files_state_cache_miss_on_size():
    """File with changed size recomputes checksum even if mtime matches."""
    config = BucketConfig(provider="test", bucket_name="test-bucket")
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "data.parquet")
        with open(fpath, "wb") as f:
            f.write(b"x" * 512)

        stat = os.stat(fpath)
        state = SyncState(bucket="test-bucket")
        # Store a different size to simulate a changed file
        state.update_file("data.parquet", checksum="stale-checksum", size=999, mtime=stat.st_mtime)

        with patch.object(sync, "calculate_checksum", return_value="fresh-checksum") as mock_checksum:
            files = sync.get_local_files(tmp, state=state)

        assert files["data.parquet"] == "fresh-checksum"
        mock_checksum.assert_called_once()


# ---------------------------------------------------------------------------
# upload_only mode
# ---------------------------------------------------------------------------


def test_sync_upload_only_no_downloads():
    """upload_only=True means no files are ever downloaded."""
    config = BucketConfig(provider="test", bucket_name="test-bucket", upload_only=True)
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "local.txt"), "w") as f:
            f.write("local content")

        # Remote has an extra file that would normally be downloaded
        sync.remote_files = {"remote-only.txt": {"Size": 100, "Checksum": "remote-cksum"}}

        with patch.object(sync, "calculate_checksum", return_value="local-cksum"):
            with patch.object(sync, "upload_file", return_value=True):
                with patch.object(sync, "download_file") as mock_download:
                    result = sync.sync(local_path=tmp)

        assert result.downloaded == 0
        mock_download.assert_not_called()


# ---------------------------------------------------------------------------
# create_only_patterns
# ---------------------------------------------------------------------------


def test_sync_create_only_pattern_existing_remote_not_uploaded():
    """Files matching create_only_patterns that exist on remote are skipped (no upload, no checksum)."""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket",
        upload_only=True,
        create_only_patterns=["*.parquet"],
    )
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "data.parquet"), "wb") as f:
            f.write(b"parquet data")

        # Same file already exists on remote
        sync.remote_files = {"data.parquet": {"Size": 100, "Checksum": "remote-cksum"}}

        with patch.object(sync, "calculate_checksum", return_value="local-cksum"):
            with patch.object(sync, "upload_file") as mock_upload:
                result = sync.sync(local_path=tmp)

        assert result.unchanged == 1
        mock_upload.assert_not_called()


def test_sync_create_only_pattern_absent_from_remote_uploaded():
    """Files matching create_only_patterns that are absent from remote ARE uploaded."""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket",
        upload_only=True,
        create_only_patterns=["*.parquet"],
    )
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "new.parquet"), "wb") as f:
            f.write(b"parquet data")

        sync.remote_files = {}  # Nothing on remote yet

        with patch.object(sync, "calculate_checksum", return_value="local-cksum"):
            with patch.object(sync, "upload_file", return_value=True) as mock_upload:
                result = sync.sync(local_path=tmp)

        assert result.uploaded == 1
        mock_upload.assert_called_once()


def test_sync_create_only_pattern_not_downloaded():
    """Files matching create_only_patterns are never downloaded even if absent locally."""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket",
        create_only_patterns=["archive/*.parquet"],
    )
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        # Remote has a parquet that doesn't exist locally
        sync.remote_files = {"archive/old.parquet": {"Size": 100, "Checksum": "remote-cksum"}}

        with patch.object(sync, "calculate_checksum", return_value="local-cksum"):
            with patch.object(sync, "download_file") as mock_download:
                sync.sync(local_path=tmp)

        mock_download.assert_not_called()


# ---------------------------------------------------------------------------
# force_full_sync
# ---------------------------------------------------------------------------


def test_sync_force_full_sync_ignores_state():
    """force_full_sync=True causes calculate_checksum to be called even for cached files."""
    config = BucketConfig(provider="test", bucket_name="test-bucket")
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "file.txt")
        with open(fpath, "w") as f:
            f.write("content")

        stat = os.stat(fpath)
        # Write a valid state file
        state_path = os.path.join(tmp, ".buckia_state.json")
        state = SyncState(bucket="test-bucket")
        state.update_file("file.txt", checksum="cached-cksum", size=stat.st_size, mtime=stat.st_mtime)
        state.save(state_path)

        with patch.object(sync, "calculate_checksum", return_value="fresh-cksum") as mock_checksum:
            sync.sync(local_path=tmp, force_full_sync=True)

        # checksum must have been recomputed despite valid cache
        mock_checksum.assert_called()


# ---------------------------------------------------------------------------
# State cache: bucket mismatch
# ---------------------------------------------------------------------------


def test_sync_state_bucket_mismatch_ignored():
    """State cache is ignored when its bucket doesn't match config.bucket_name."""
    config = BucketConfig(provider="test", bucket_name="correct-bucket")
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        fpath = os.path.join(tmp, "file.txt")
        with open(fpath, "w") as f:
            f.write("content")

        stat = os.stat(fpath)
        state_path = os.path.join(tmp, ".buckia_state.json")
        state = SyncState(bucket="wrong-bucket")  # different bucket
        state.update_file("file.txt", checksum="cached-cksum", size=stat.st_size, mtime=stat.st_mtime)
        state.save(state_path)

        with patch.object(sync, "calculate_checksum", return_value="fresh-cksum") as mock_checksum:
            sync.sync(local_path=tmp)

        # Cache should have been ignored, so checksum was recomputed
        mock_checksum.assert_called()


# ---------------------------------------------------------------------------
# State saved after sync
# ---------------------------------------------------------------------------


def test_sync_saves_state_after_success():
    """State file is written after a successful sync."""
    config = BucketConfig(provider="test", bucket_name="test-bucket")
    sync = TestSyncImplementation(config)

    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "file.txt"), "w") as f:
            f.write("content")

        sync.remote_files = {}
        state_path = os.path.join(tmp, ".buckia_state.json")
        assert not os.path.exists(state_path)

        with patch.object(sync, "calculate_checksum", return_value="cksum"):
            with patch.object(sync, "upload_file", return_value=True):
                result = sync.sync(local_path=tmp)

        assert result.success
        assert os.path.exists(state_path)
        loaded = SyncState.load(state_path)
        assert loaded is not None
        assert loaded.bucket == "test-bucket"
        assert "file.txt" in loaded.files
