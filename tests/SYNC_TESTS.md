# Buckia Sync Tests Overview

This document provides an overview of the synchronization tests in the `test_sync.py` file. These tests verify the functionality of the Buckia synchronization system.

## Test Descriptions

### `test_basic_sync`

- **Purpose**: Tests basic file synchronization (uploading new files)
- **Actions**:
  - Creates a test directory with files of various sizes
  - Creates nested directories to test directory structure handling
  - Syncs the directory to remote storage
  - Verifies all files were properly uploaded

### `test_sync_with_updates`

- **Purpose**: Tests file update synchronization
- **Actions**:
  - Creates initial test files and performs first sync
  - Modifies some files (adding new content)
  - Performs a second sync
  - Verifies updated files were re-uploaded while unchanged files remained untouched

### `test_sync_with_deletions`

- **Purpose**: Tests orphaned file deletion
- **Actions**:
  - Creates initial test files and syncs them
  - Deletes some local files
  - Syncs again with `delete_orphaned=True`
  - Verifies files deleted locally are also removed from remote storage
  - Ensures kept files remain in remote storage

### `test_sync_with_filters`

- **Purpose**: Tests include/exclude patterns for file filtering
- **Actions**:
  - Creates test files with different extensions
  - Tests syncing with an include pattern (only `.txt` files)
  - Verifies only matching files are uploaded
  - Tests syncing with an exclude pattern (excluding `.png` and `.json` files)
  - Verifies excluded files are not uploaded while others are

### `test_sync_specific_paths`

- **Purpose**: Tests synchronization of specific subdirectories/files
- **Actions**:
  - Creates files in various directory paths
  - Syncs only specific paths (`docs` directory and one specific JSON file)
  - Verifies only files in specified paths are uploaded

### `test_sync_dry_run`

- **Purpose**: Tests dry run mode (simulation without actual changes)
- **Actions**:
  - Creates test files
  - Syncs in dry run mode
  - Verifies sync operations are reported but not actually performed
  - Performs a real sync afterward
  - Verifies files are actually uploaded during real sync

## Key Verification Points

Throughout these tests, the following aspects are verified:

1. **File Upload Counts**: Checks that the expected number of files are uploaded/updated/deleted
2. **Error Handling**: Ensures no operations fail (checking `failed` count)
3. **Remote File Presence**: Verifies files exist in remote storage after operations
4. **Filtering**: Ensures include/exclude patterns work correctly
5. **Path Selection**: Confirms ability to sync only specific paths
6. **Dry Run Behavior**: Validates that dry run mode reports changes without making them

These tests provide comprehensive coverage of the synchronization functionality, ensuring that all key features work as expected in various scenarios.
