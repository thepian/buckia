"""
Integration tests for synchronization functionality
"""

import os
import re
import time
import shutil
import pytest
from pathlib import Path


def test_basic_sync(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test basic synchronization (upload new files)"""
    # Create a test directory with files
    test_files = {
        "file1.txt": 1024,        # 1 KB
        "file2.txt": 1024 * 10,   # 10 KB
        "nested/file3.txt": 1024, # Nested file
        "nested/deep/file4.txt": 512,  # Deeply nested file
    }
    
    test_dir = test_directory_factory("sync_basic", files=test_files)
    
    # Ensure nested directories exist
    os.makedirs(test_dir / "nested" / "deep", exist_ok=True)
    
    # Sync the directory
    result = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        dry_run=False,
    )
    
    # Check sync result
    assert result.uploaded >= len(test_files), f"Expected at least {len(test_files)} uploads, got {result.uploaded}"
    assert result.failed == 0, f"Sync reported {result.failed} failed operations"
    
    # List remote files to verify uploads
    remote_files = buckia_client.list_files()
    
    for file_path in test_files.keys():
        remote_path = f"{test_dir.name}/{file_path}"
        assert remote_path in remote_files, f"Uploaded file {remote_path} not found in remote files"


def test_sync_with_updates(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test synchronization with file updates"""
    # Create initial test files
    test_files = {
        "update1.txt": 1024,
        "update2.txt": 1024,
        "unchanged.txt": 1024,
    }
    
    test_dir = test_directory_factory("sync_updates", files=test_files)
    
    # Initial sync
    result1 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        dry_run=False,
    )
    
    assert result1.uploaded >= len(test_files), "Initial sync failed"
    
    # Modify some files
    for file_to_update in ["update1.txt", "update2.txt"]:
        file_path = test_dir / file_to_update
        with open(file_path, 'ab') as f:
            f.write(b"\nUpdated content " + os.urandom(100))
    
    # Sync again
    result2 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        dry_run=False,
    )
    
    # Should have updated 2 files
    assert result2.uploaded >= 2, f"Expected at least 2 updated files, got {result2.uploaded}"
    # 1 file should be unchanged
    assert result2.unchanged >= 1, f"Expected at least 1 unchanged file, got {result2.unchanged}"


def test_sync_with_deletions(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test synchronization with orphaned file deletion"""
    # Create initial test files
    test_files = {
        "keep1.txt": 1024,
        "keep2.txt": 1024,
        "delete1.txt": 1024,
        "delete2.txt": 1024,
    }
    
    test_dir = test_directory_factory("sync_deletions", files=test_files)
    
    # Initial sync
    result1 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,  # Don't delete orphaned files initially
        dry_run=False,
    )
    
    assert result1.uploaded >= len(test_files), "Initial sync failed"
    
    # Delete some local files
    for file_to_delete in ["delete1.txt", "delete2.txt"]:
        file_path = test_dir / file_to_delete
        os.remove(file_path)
    
    # Sync with delete_orphaned=True
    result2 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=True,  # Now delete orphaned files
        dry_run=False,
    )
    
    # Should have deleted 2 files
    assert result2.deleted >= 2, f"Expected at least 2 deleted files, got {result2.deleted}"
    
    # Verify that deleted files are no longer in remote storage
    remote_files = buckia_client.list_files()
    for file_to_delete in ["delete1.txt", "delete2.txt"]:
        remote_path = f"{test_dir.name}/{file_to_delete}"
        assert remote_path not in remote_files, f"Deleted file {remote_path} still found in remote storage"
    
    # Verify that kept files are still in remote storage
    for file_to_keep in ["keep1.txt", "keep2.txt"]:
        remote_path = f"{test_dir.name}/{file_to_keep}"
        assert remote_path in remote_files, f"Kept file {remote_path} not found in remote storage"


def test_sync_with_filters(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test synchronization with include/exclude patterns"""
    # Create test files with different extensions
    test_files = {
        "document1.txt": 1024,
        "document2.txt": 1024,
        "image1.png": 1024,
        "image2.png": 1024,
        "data.json": 1024,
        "script.js": 1024,
    }
    
    test_dir = test_directory_factory("sync_filters", files=test_files)
    
    # Sync only text files
    result1 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        include_pattern=r".*\.txt$",  # Only include .txt files
        dry_run=False,
    )
    
    # Should have uploaded only txt files (2)
    txt_files = [f for f in test_files.keys() if f.endswith('.txt')]
    assert result1.uploaded >= len(txt_files), f"Expected to upload {len(txt_files)} .txt files, got {result1.uploaded}"
    
    # Verify that only txt files are in remote storage
    remote_files = buckia_client.list_files()
    for file_name in test_files.keys():
        remote_path = f"{test_dir.name}/{file_name}"
        if file_name.endswith('.txt'):
            assert remote_path in remote_files, f"Text file {remote_path} not found in remote storage"
        else:
            assert remote_path not in remote_files, f"Non-text file {remote_path} found in remote storage"
    
    # Clean up for next test
    cleanup_remote_files()
    
    # Sync with exclude pattern
    result2 = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        exclude_pattern=r".*\.(png|json)$",  # Exclude .png and .json files
        dry_run=False,
    )
    
    # Should have uploaded txt and js files, but not png or json
    non_excluded_files = [f for f in test_files.keys() if not (f.endswith('.png') or f.endswith('.json'))]
    assert result2.uploaded >= len(non_excluded_files), \
        f"Expected to upload {len(non_excluded_files)} non-excluded files, got {result2.uploaded}"
    
    # Verify that only non-excluded files are in remote storage
    remote_files = buckia_client.list_files()
    for file_name in test_files.keys():
        remote_path = f"{test_dir.name}/{file_name}"
        if file_name.endswith('.png') or file_name.endswith('.json'):
            assert remote_path not in remote_files, f"Excluded file {remote_path} found in remote storage"
        else:
            assert remote_path in remote_files, f"Non-excluded file {remote_path} not found in remote storage"


def test_sync_specific_paths(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test synchronization with specific paths"""
    # Create test files in different paths
    test_files = {
        "root_file.txt": 1024,
        "docs/doc1.txt": 1024,
        "docs/doc2.txt": 1024,
        "images/img1.png": 1024,
        "images/img2.png": 1024,
        "data/data1.json": 1024,
        "data/data2.json": 1024,
    }
    
    test_dir = test_directory_factory("sync_paths", files=test_files)
    
    # Ensure directories exist
    for dir_name in ["docs", "images", "data"]:
        os.makedirs(test_dir / dir_name, exist_ok=True)
    
    # Sync only specific paths
    sync_paths = ["docs", "data/data1.json"]
    result = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        sync_paths=sync_paths,
        dry_run=False,
    )
    
    # Count how many files should be synced
    expected_synced_count = 0
    for file_path in test_files.keys():
        if any(file_path.startswith(path) for path in sync_paths) or file_path in sync_paths:
            expected_synced_count += 1
    
    # Should have uploaded only files in specified paths
    assert result.uploaded >= expected_synced_count, \
        f"Expected to upload {expected_synced_count} files in specified paths, got {result.uploaded}"
    
    # Verify that only files in specified paths are in remote storage
    remote_files = buckia_client.list_files()
    for file_path in test_files.keys():
        remote_path = f"{test_dir.name}/{file_path}"
        should_be_synced = any(file_path.startswith(path) for path in sync_paths) or file_path in sync_paths
        
        if should_be_synced:
            assert remote_path in remote_files, f"Path-specified file {remote_path} not found in remote storage"
        else:
            assert remote_path not in remote_files, f"Non-specified file {remote_path} found in remote storage"


def test_sync_dry_run(buckia_client, test_directory_factory, remote_test_prefix, cleanup_remote_files):
    """Test synchronization in dry run mode"""
    # Create test files
    test_files = {
        "dry_run1.txt": 1024,
        "dry_run2.txt": 1024,
    }
    
    test_dir = test_directory_factory("sync_dry_run", files=test_files)
    
    # Initial remote file list
    initial_remote_files = set(buckia_client.list_files().keys())
    
    # Sync in dry run mode
    result = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        dry_run=True,  # Dry run mode
    )
    
    # Should report files that would be uploaded
    assert result.uploaded >= len(test_files), \
        f"Dry run should report {len(test_files)} files to upload, got {result.uploaded}"
    
    # Verify that no files were actually uploaded
    after_dry_run_remote_files = set(buckia_client.list_files().keys())
    assert initial_remote_files == after_dry_run_remote_files, "Dry run should not change remote files"
    
    # Now do a real sync
    real_result = buckia_client.sync(
        local_path=str(test_dir),
        max_workers=2,
        delete_orphaned=False,
        dry_run=False,  # Real sync
    )
    
    # Verify that files were actually uploaded
    after_real_sync_remote_files = set(buckia_client.list_files().keys())
    assert len(after_real_sync_remote_files) > len(initial_remote_files), "Real sync should add files"
    
    # Verify synced files
    for file_name in test_files.keys():
        remote_path = f"{test_dir.name}/{file_name}"
        assert remote_path in after_real_sync_remote_files, f"File {remote_path} not found after real sync"