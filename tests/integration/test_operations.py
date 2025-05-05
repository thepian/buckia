"""
Integration tests for common file operations across providers
"""

import os
import time
import pytest
from pathlib import Path


def test_file_upload_download(buckia_client, test_file_factory, remote_test_prefix, cleanup_remote_files):
    """Test basic file upload and download operations"""
    # Create test files of different sizes
    test_files = {
        "small.txt": 1024,         # 1 KB
        "medium.txt": 1024 * 100,  # 100 KB
        "large.txt": 1024 * 1024,  # 1 MB
    }
    
    local_files = {}
    remote_paths = {}
    
    # Upload test files
    for name, size in test_files.items():
        # Create the file
        local_file = test_file_factory(name, size)
        local_files[name] = local_file
        
        # Generate remote path
        remote_path = f"{remote_test_prefix}/{name}"
        remote_paths[name] = remote_path
        
        # Upload and verify
        upload_result = buckia_client.upload_file(str(local_file), remote_path)
        assert upload_result, f"Upload failed for {name}"
    
    # List remote files to verify uploads
    remote_files = buckia_client.list_files()
    for name, remote_path in remote_paths.items():
        assert remote_path in remote_files, f"Uploaded file {remote_path} not found in remote storage"
    
    # Download files
    for name, local_file in local_files.items():
        # Create download path
        download_path = local_file.with_suffix(".downloaded")
        
        # Download the file
        download_result = buckia_client.download_file(remote_paths[name], str(download_path))
        assert download_result, f"Download failed for {name}"
        
        # Verify file size
        assert download_path.exists(), f"Downloaded file {download_path} does not exist"
        assert download_path.stat().st_size == local_file.stat().st_size, f"Size mismatch for {name}"
    
    # Delete files
    for name, remote_path in remote_paths.items():
        delete_result = buckia_client.delete_file(remote_path)
        assert delete_result, f"Delete failed for {name}"


def test_file_listing(buckia_client, test_file_factory, remote_test_prefix, cleanup_remote_files):
    """Test file listing operations"""
    # Upload a few files with the same prefix
    prefixed_files = [
        f"{remote_test_prefix}/list/file1.txt",
        f"{remote_test_prefix}/list/file2.txt",
        f"{remote_test_prefix}/list/nested/file3.txt",
    ]
    
    # Create and upload the files
    for remote_path in prefixed_files:
        local_file = test_file_factory(os.path.basename(remote_path))
        buckia_client.upload_file(str(local_file), remote_path)
    
    # List all files
    all_files = buckia_client.list_files()
    assert isinstance(all_files, dict), "list_files should return a dictionary"
    
    # Check that our test files are included
    for remote_path in prefixed_files:
        assert remote_path in all_files, f"File {remote_path} not found in listing"
    
    # Test path-based listing
    list_path = f"{remote_test_prefix}/list"
    list_result = buckia_client.list_files(list_path)
    
    # Check that we only get files under the specified path
    for remote_path in prefixed_files:
        if remote_path.startswith(f"{list_path}/"):
            assert remote_path in list_result, f"File {remote_path} not found in path-based listing"
    
    # Delete test files
    for remote_path in prefixed_files:
        buckia_client.delete_file(remote_path)


def test_file_operations_with_special_characters(buckia_client, test_file_factory, remote_test_prefix, cleanup_remote_files):
    """Test file operations with special characters in filenames"""
    # Test files with special characters
    special_files = {
        "file with spaces.txt": 1024,
        "file-with-hyphens.txt": 1024,
        "file_with_underscores.txt": 1024,
        "file.with.dots.txt": 1024,
    }
    
    local_files = {}
    remote_paths = {}
    
    # Upload test files
    for name, size in special_files.items():
        # Create the file
        local_file = test_file_factory(name, size)
        local_files[name] = local_file
        
        # Generate remote path
        remote_path = f"{remote_test_prefix}/{name}"
        remote_paths[name] = remote_path
        
        # Upload and verify
        upload_result = buckia_client.upload_file(str(local_file), remote_path)
        assert upload_result, f"Upload failed for {name}"
    
    # List remote files to verify uploads
    remote_files = buckia_client.list_files()
    for name, remote_path in remote_paths.items():
        assert remote_path in remote_files, f"Uploaded file {remote_path} not found in remote storage"
    
    # Download files
    for name, local_file in local_files.items():
        # Create download path
        download_path = local_file.with_suffix(".downloaded")
        
        # Download the file
        download_result = buckia_client.download_file(remote_paths[name], str(download_path))
        assert download_result, f"Download failed for {name}"
        
        # Verify file size
        assert download_path.exists(), f"Downloaded file {download_path} does not exist"
        assert download_path.stat().st_size == local_file.stat().st_size, f"Size mismatch for {name}"
    
    # Delete files
    for name, remote_path in remote_paths.items():
        delete_result = buckia_client.delete_file(remote_path)
        assert delete_result, f"Delete failed for {name}"


def test_binary_file_operations(buckia_client, temp_directory, remote_test_prefix, cleanup_remote_files):
    """Test operations with binary files"""
    # Create a binary file (small image)
    binary_file_path = temp_directory / "test_image.png"
    
    # Create a small PNG image (1x1 pixel, red)
    with open(binary_file_path, 'wb') as f:
        # PNG header
        f.write(b'\x89PNG\r\n\x1a\n')
        # IHDR chunk
        f.write(b'\x00\x00\x00\x0d')  # length
        f.write(b'IHDR')
        f.write(b'\x00\x00\x00\x01')  # width=1
        f.write(b'\x00\x00\x00\x01')  # height=1
        f.write(b'\x08\x02\x00\x00\x00')  # bit depth=8, color type=2, etc.
        f.write(b'\xd3\x10\x3d\x39')  # CRC
        # IDAT chunk
        f.write(b'\x00\x00\x00\x0c')  # length
        f.write(b'IDAT')
        f.write(b'\x08\xd7\x63\x60\x60\x60\x00\x00\x00\x02\x00\x01')  # compressed data
        f.write(b'\x48\xaf\xbc\x7e')  # CRC
        # IEND chunk
        f.write(b'\x00\x00\x00\x00')  # length
        f.write(b'IEND')
        f.write(b'\xaeB`\x82')  # CRC
    
    # Upload binary file
    remote_path = f"{remote_test_prefix}/test_image.png"
    upload_result = buckia_client.upload_file(str(binary_file_path), remote_path)
    assert upload_result, "Binary file upload failed"
    
    # Download binary file
    download_path = temp_directory / "test_image_downloaded.png"
    download_result = buckia_client.download_file(remote_path, str(download_path))
    assert download_result, "Binary file download failed"
    
    # Verify file size and content
    assert download_path.exists(), "Downloaded binary file does not exist"
    assert download_path.stat().st_size == binary_file_path.stat().st_size, "Binary file size mismatch"
    
    # Compare file contents
    with open(binary_file_path, 'rb') as f1, open(download_path, 'rb') as f2:
        assert f1.read() == f2.read(), "Binary file content mismatch"
    
    # Delete the file
    delete_result = buckia_client.delete_file(remote_path)
    assert delete_result, "Binary file deletion failed"