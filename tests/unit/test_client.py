"""
Unit tests for the BuckiaClient class
"""

import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from buckia import BuckiaClient, BucketConfig


class MockBackend:
    """Mock backend for testing the client"""
    
    def __init__(self, config):
        self.config = config
        self.connected = False
        
    def connect(self):
        self.connected = True
        return True
        
    def test_connection(self):
        return {"api_key": True}
        
    def sync(self, **kwargs):
        """Mock sync operation"""
        return {
            "success": True,
            "uploaded": 5,
            "downloaded": 3,
            "deleted": 1,
            "unchanged": 10,
            "failed": 0,
            "errors": []
        }
        
    def upload_file(self, local_file_path, remote_path):
        """Mock upload operation"""
        return os.path.exists(local_file_path)
        
    def download_file(self, remote_path, local_file_path):
        """Mock download operation"""
        return True
        
    def delete_file(self, remote_path):
        """Mock delete operation"""
        return True
        
    def get_public_url(self, remote_path):
        """Mock URL generation"""
        return f"https://example.com/{remote_path}"
        
    def list_remote_files(self, path=None):
        """Mock file listing"""
        return {
            "file1.txt": {"Size": 100, "LastModified": "2023-01-01"},
            "file2.txt": {"Size": 200, "LastModified": "2023-01-02"}
        }
        
    def close(self):
        """Mock close operation"""
        self.connected = False


def test_client_init_with_config_object():
    """Test BuckiaClient initialization with a BucketConfig object"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        # Check the client has the right config
        assert client.config is config
        
        # Check the backend was created with the config
        mock_get_backend.assert_called_once_with(config)
        
        # Check the client has the backend
        assert client.backend is mock_backend


def test_client_init_with_dict():
    """Test BuckiaClient initialization with a dict"""
    config_dict = {
        "provider": "test",
        "bucket_name": "test-bucket",
        "credentials": {"api_key": "test-key"}
    }
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MagicMock()
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config_dict)
        
        # Check the config is a BucketConfig object
        assert isinstance(client.config, BucketConfig)
        assert client.config.provider == "test"
        assert client.config.bucket_name == "test-bucket"
        assert client.config.credentials == {"api_key": "test-key"}
        
        # Check the backend was created with the config
        mock_get_backend.assert_called_once()
        
        # Check the client has the backend
        assert client.backend is mock_backend


def test_client_init_with_config_path():
    """Test BuckiaClient initialization with a config file path"""
    config_data = {
        "provider": "test",
        "bucket_name": "test-bucket",
        "auth": {"api_key": "test-key"}
    }
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Write config data to file
            yaml.dump(config_data, temp_file)
            temp_file.flush()
            
            with patch("buckia.client.get_sync_backend") as mock_get_backend:
                mock_backend = MagicMock()
                mock_get_backend.return_value = mock_backend
                
                client = BuckiaClient(temp_file.name)
                
                # Check the config is a BucketConfig object with correct values
                assert isinstance(client.config, BucketConfig)
                assert client.config.provider == "test"
                assert client.config.bucket_name == "test-bucket"
                assert client.config.credentials == {"api_key": "test-key"}
                
                # Check the backend was created with the config
                mock_get_backend.assert_called_once()
                
                # Check the client has the backend
                assert client.backend is mock_backend
                
        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_client_init_invalid_config_type():
    """Test BuckiaClient with invalid config type"""
    with pytest.raises(TypeError):
        BuckiaClient(123)  # Invalid config type (int)


def test_client_init_invalid_config_dict():
    """Test BuckiaClient with invalid config dict (missing required fields)"""
    with pytest.raises(ValueError):
        BuckiaClient({"provider": "test"})  # Missing bucket_name


def test_client_init_backend_creation_failure():
    """Test BuckiaClient when backend creation fails"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend", return_value=None):
        with pytest.raises(ValueError):
            BuckiaClient(config)


def test_client_init_backend_connection_warning():
    """Test BuckiaClient when backend connection fails (warning)"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MagicMock()
        mock_backend.connect.return_value = False
        mock_get_backend.return_value = mock_backend
        
        # Should not raise exception, just log warning
        client = BuckiaClient(config)
        
        assert client.backend is mock_backend
        mock_backend.connect.assert_called_once()


def test_client_sync():
    """Test BuckiaClient sync method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket",
        max_workers=4,
        delete_orphaned=False
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        # Test sync with defaults
        result = client.sync("/tmp/test")
        
        # Check result was returned
        assert result["success"] is True
        assert result["uploaded"] == 5
        assert result["downloaded"] == 3
        
        # Test sync with overrides
        result = client.sync(
            local_path="/tmp/test2",
            max_workers=8,
            delete_orphaned=True,
            include_pattern="*.txt",
            exclude_pattern="temp_*",
            dry_run=True,
            sync_paths=["folder1", "folder2"]
        )
        
        # Check result was returned
        assert result["success"] is True


def test_client_test_connection():
    """Test BuckiaClient test_connection method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        result = client.test_connection()
        
        assert result == {"api_key": True}
        

def test_client_upload_file():
    """Test BuckiaClient upload_file method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        # Test with nonexistent file
        result = client.upload_file("/nonexistent/file.txt")
        assert not result
        
        # Test with file and explicit remote path
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            try:
                temp_file.write(b"test content")
                temp_file.flush()
                
                result = client.upload_file(temp_file.name, "remote/path/file.txt")
                assert result
                
                # Test with file and default remote path
                result = client.upload_file(temp_file.name)
                assert result
                
            finally:
                os.unlink(temp_file.name)


def test_client_download_file():
    """Test BuckiaClient download_file method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test download with nonexistent parent directory
            local_path = os.path.join(temp_dir, "new_subdir", "file.txt")
            result = client.download_file("remote/file.txt", local_path)
            
            # Directory should be created
            assert os.path.exists(os.path.dirname(local_path))
            assert result


def test_client_delete_file():
    """Test BuckiaClient delete_file method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        result = client.delete_file("remote/file.txt")
        assert result


def test_client_get_public_url():
    """Test BuckiaClient get_public_url method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        url = client.get_public_url("remote/file.txt")
        assert url == "https://example.com/remote/file.txt"


def test_client_list_files():
    """Test BuckiaClient list_files method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        # Test with no path
        files = client.list_files()
        assert "file1.txt" in files
        assert "file2.txt" in files
        
        # Test with path
        files = client.list_files("folder")
        assert "file1.txt" in files
        assert "file2.txt" in files


def test_client_close():
    """Test BuckiaClient close method"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        client = BuckiaClient(config)
        
        # Close the client
        client.close()
        
        # Backend should be closed
        assert not mock_backend.connected


def test_client_context_manager():
    """Test BuckiaClient as context manager"""
    config = BucketConfig(
        provider="test",
        bucket_name="test-bucket"
    )
    
    with patch("buckia.client.get_sync_backend") as mock_get_backend:
        mock_backend = MockBackend(config)
        mock_get_backend.return_value = mock_backend
        
        # Use client as context manager
        with BuckiaClient(config) as client:
            # Do some operations
            client.list_files()
            
        # Backend should be closed after context exit
        assert not mock_backend.connected