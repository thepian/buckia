"""
Unit tests for the BaseSync class and SyncResult
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from buckia.config import BucketConfig
from buckia.sync.base import BaseSync, SyncResult


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
        cached=4
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
        failed=0
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
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    sync = TestSyncImplementation(config)
    
    assert sync.config is config
    assert sync.logger.name == "buckia.TestSyncImplementation"


def test_calculate_checksum():
    """Test calculate_checksum method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket",
        checksum_algorithm="sha256"
    )
    
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
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
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
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
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
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
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
            "file3.txt": {"Size": 200, "Checksum": "remote-checksum"}
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
                        result = sync.sync(
                            local_path=temp_dir,
                            max_workers=2,
                            delete_orphaned=True
                        )
                        
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
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    sync = TestSyncImplementation(config)
    
    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")
            
        # Setup remote files
        sync.remote_files = {
            "file2.txt": {"Size": 100, "Checksum": "remote-checksum"}
        }
        
        # Mock methods
        with patch.object(sync, "calculate_checksum") as mock_checksum:
            with patch.object(sync, "upload_file") as mock_upload:
                with patch.object(sync, "download_file") as mock_download:
                    with patch.object(sync, "delete_file") as mock_delete:
                        # Set up checksums
                        mock_checksum.return_value = "local-checksum"
                        
                        # Run the sync with dry_run=True
                        result = sync.sync(
                            local_path=temp_dir,
                            delete_orphaned=True,
                            dry_run=True
                        )
                        
                        # All operations should succeed, but no actual changes
                        assert result.success is True
                        
                        # No actual uploads, downloads, or deletions
                        assert mock_upload.call_count == 0
                        assert mock_download.call_count == 0
                        assert mock_delete.call_count == 0


@pytest.mark.skip(reason="cache_dir functionality has been removed")
def test_sync_with_cache_dir():
    """Test sync with cache_dir (functionality removed)"""
    # This test is kept as reference but skipped since cache_dir functionality was removed
    pass


def test_sync_with_errors():
    """Test sync with errors in operations"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    sync = TestSyncImplementation(config)
    
    # Create a temporary directory with files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
            f.write("file1 content")
            
        # Setup remote files
        sync.remote_files = {
            "file2.txt": {"Size": 100, "Checksum": "remote-checksum"}
        }
        
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
                    result = sync.sync(
                        local_path=temp_dir
                    )
                    
                    # Operations should fail
                    assert result.success is False
                    assert result.failed == 2  # Both upload and download failed
                    assert len(result.errors) == 2


def test_sync_with_nonexistent_path():
    """Test sync with a nonexistent local path"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    sync = TestSyncImplementation(config)
    
    # Create a temporary directory to use as a parent
    with tempfile.TemporaryDirectory() as temp_dir:
        # Nonexistent subdirectory
        nonexistent_path = os.path.join(temp_dir, "nonexistent")
        
        # This should raise NotADirectoryError
        with pytest.raises(NotADirectoryError):
            sync.sync(local_path=nonexistent_path)


@pytest.mark.skip(reason="cache_dir functionality has been removed")
def test_sync_with_nonexistent_cache_dir():
    """Test sync with a nonexistent cache directory (functionality removed)"""
    # This test is kept as reference but skipped since cache_dir functionality was removed
    pass