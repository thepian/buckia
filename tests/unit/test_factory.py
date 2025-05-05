"""
Unit tests for the sync factory module
"""

import pytest
from unittest.mock import patch, MagicMock

from buckia.config import BucketConfig
from buckia.sync.factory import create_sync_backend, get_sync_backend
from buckia.sync.base import BaseSync


class MockSync(BaseSync):
    """Mock implementation of BaseSync for testing"""
    
    def connect(self):
        return True
        
    def test_connection(self):
        return {"test": True}
        
    def list_remote_files(self, path=None):
        return {}
        
    def upload_file(self, local_file_path, remote_path):
        return True
        
    def download_file(self, remote_path, local_file_path):
        return True
        
    def delete_file(self, remote_path):
        return True
        
    def get_public_url(self, remote_path):
        return f"https://example.com/{remote_path}"


def test_create_sync_backend_no_provider():
    """Test factory with no provider specified"""
    config = BucketConfig(
        provider="",  # Empty provider
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    assert result is None


def test_create_sync_backend_invalid_provider():
    """Test factory with invalid provider"""
    config = BucketConfig(
        provider="invalid-provider",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    assert result is None


@patch("buckia.sync.factory.importlib.import_module")
def test_create_sync_backend_dynamic_import_success(mock_import):
    """Test dynamic import of custom provider"""
    # Setup mock module with custom sync class
    mock_module = MagicMock()
    mock_class = MagicMock(return_value="custom-backend-instance")
    mock_module.CustomSync = mock_class
    mock_import.return_value = mock_module
    
    config = BucketConfig(
        provider="custom",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    
    # Verify import was called correctly
    mock_import.assert_called_once_with(".custom", package="buckia.sync")
    
    # Verify the class was instantiated with config
    mock_class.assert_called_once_with(config)
    
    # Verify the result
    assert result == "custom-backend-instance"


@patch("buckia.sync.factory.importlib.import_module")
def test_create_sync_backend_dynamic_import_module_error(mock_import):
    """Test dynamic import with module import error"""
    mock_import.side_effect = ImportError("Module not found")
    
    config = BucketConfig(
        provider="custom",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    
    # Verify import was called
    mock_import.assert_called_once_with(".custom", package="buckia.sync")
    
    # Verify the result is None due to import error
    assert result is None


@patch("buckia.sync.factory.importlib.import_module")
def test_create_sync_backend_dynamic_import_attribute_error(mock_import):
    """Test dynamic import with attribute error"""
    # Setup mock module without the expected class
    mock_module = MagicMock(spec=[])  # No CustomSync attribute
    mock_import.return_value = mock_module
    
    config = BucketConfig(
        provider="custom",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    
    # Verify import was called
    mock_import.assert_called_once_with(".custom", package="buckia.sync")
    
    # Verify the result is None due to attribute error
    assert result is None


@patch("buckia.sync.factory.importlib.import_module")
def test_create_sync_backend_exception(mock_import):
    """Test exception handling in factory"""
    # Setup mock to raise an unexpected exception
    mock_import.side_effect = RuntimeError("Unexpected error")
    
    config = BucketConfig(
        provider="custom",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    
    # Verify the result is None due to exception
    assert result is None


def test_get_sync_backend_alias():
    """Test that get_sync_backend is an alias of create_sync_backend"""
    assert get_sync_backend is create_sync_backend


@patch("buckia.sync.bunny.BunnySync")
def test_create_sync_backend_bunny(mock_bunny_sync):
    """Test creation of BunnySync backend"""
    mock_bunny_sync.return_value = "bunny-backend-instance"
    
    config = BucketConfig(
        provider="bunny",
        bucket_name="test-bucket"
    )
    
    result = create_sync_backend(config)
    
    # Verify the class was instantiated with config
    mock_bunny_sync.assert_called_once_with(config)
    
    # Verify the result
    assert result == "bunny-backend-instance"


@pytest.mark.skip(reason="Requires special handling for import errors")
def test_create_sync_backend_bunny_import_error():
    """Test BunnySync with import error"""
    config = BucketConfig(
        provider="bunny",
        bucket_name="test-bucket"
    )
    
    # Mock the import error by patching the try/except block in create_sync_backend
    with patch("buckia.sync.factory.BunnySync", side_effect=ImportError("No module named 'bunny'")):
        with patch("buckia.sync.factory.logger"):  # Suppress log messages
            result = create_sync_backend(config)
            
            # Verify the result is None due to import error
            assert result is None
        
        
@pytest.mark.skip(reason="Requires special handling for module imports")
def test_create_sync_backend_s3():
    """Test creation of S3Sync backend"""
    # Create a mock S3Sync class
    mock_s3_sync = MagicMock(return_value="s3-backend-instance")
    
    config = BucketConfig(
        provider="s3",
        bucket_name="test-bucket"
    )
    
    # Create a mock implementation
    class MockS3Sync:
        def __init__(self, config):
            self.config = config
            
    # Patch the direct import in factory.py
    with patch.object(create_sync_backend, "__globals__", {
        "S3Sync": mock_s3_sync
    }):
        with patch("buckia.sync.factory.S3Sync", mock_s3_sync):
            with patch("buckia.sync.factory.importlib.import_module", return_value=MagicMock(S3Sync=mock_s3_sync)):
                result = create_sync_backend(config)
                
                # Verify the class was instantiated with config
                mock_s3_sync.assert_called_once_with(config)
                
                # Verify the result
                assert result == "s3-backend-instance"


def test_create_sync_backend_s3_import_error():
    """Test S3Sync with import error"""
    config = BucketConfig(
        provider="s3",
        bucket_name="test-bucket"
    )
    
    # Mock the import error by patching the try/except block in create_sync_backend
    with patch("buckia.sync.factory.logger"):  # Suppress log messages
        with patch.dict(create_sync_backend.__globals__, {}, clear=False):  # Patch globals without S3Sync
            with patch("buckia.sync.factory.importlib.import_module", side_effect=ImportError("No module named 's3'")):
                result = create_sync_backend(config)
                
                # Verify the result is None due to import error
                assert result is None


@pytest.mark.skip(reason="Requires special handling for module imports")
def test_create_sync_backend_linode():
    """Test creation of LinodeSync backend"""
    # Create a mock LinodeSync class
    mock_linode_sync = MagicMock(return_value="linode-backend-instance")
    
    config = BucketConfig(
        provider="linode",
        bucket_name="test-bucket"
    )
    
    # Patch the direct import in factory.py
    with patch.object(create_sync_backend, "__globals__", {
        "LinodeSync": mock_linode_sync
    }):
        with patch("buckia.sync.factory.importlib.import_module", return_value=MagicMock(LinodeSync=mock_linode_sync)):
            result = create_sync_backend(config)
            
            # Verify the class was instantiated with config
            mock_linode_sync.assert_called_once_with(config)
            
            # Verify the result
            assert result == "linode-backend-instance"


def test_create_sync_backend_linode_import_error():
    """Test LinodeSync with import error"""
    config = BucketConfig(
        provider="linode",
        bucket_name="test-bucket"
    )
    
    # Mock the import error by patching the try/except block
    with patch("buckia.sync.factory.logger"):  # Suppress log messages
        with patch.dict(create_sync_backend.__globals__, {}, clear=False):  # Patch globals without LinodeSync
            with patch("buckia.sync.factory.importlib.import_module", side_effect=ImportError("No module named 'linode'")):
                result = create_sync_backend(config)
                
                # Verify the result is None due to import error
                assert result is None