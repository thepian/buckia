"""
Base synchronization interface for Buckia
"""

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

from ..config import BucketConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("buckia")


@dataclass
class SyncResult:
    """Result of a synchronization operation"""

    success: bool = True
    uploaded: int = 0
    downloaded: int = 0
    deleted: int = 0
    failed: int = 0
    unchanged: int = 0
    errors: List[str] | None = None
    protected_skipped: int = 0
    cached: int = 0  # Kept for backward compatibility but no longer used

    def __post_init__(self) -> None:
        # Initialize errors list if None
        if self.errors is None:
            self.errors = []
        # Ensure errors is always a list, even if it was set to None later
        # This protects against attribute errors when appending

    def __str__(self) -> str:
        return (
            f"Sync completed: {self.uploaded} uploaded, {self.downloaded} downloaded, "
            f"{self.deleted} deleted, {self.unchanged} unchanged, "
            f"{self.cached} cached, {self.protected_skipped} protected skipped, "
            f"{self.failed} failed"
        )


class BaseSync(ABC):
    """
    Abstract base class for synchronization backends

    This defines the interface that all backend implementations must follow.
    """

    config: BucketConfig

    def __init__(self, config: Dict[str, Any] | BucketConfig):
        """
        Initialize the sync backend with configuration

        Args:
            config: Configuration object with backend-specific configuration
        """
        self.config = BucketConfig(**config) if isinstance(config, dict) else config
        self.logger = logging.getLogger(f"buckia.{self.__class__.__name__}")

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the remote storage

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, bool]:
        """
        Test connection to the remote storage

        Returns:
            Dictionary with test results for various authentication methods
        """
        pass

    @abstractmethod
    def list_remote_files(self, path: str | None = None) -> Dict[str, Dict[str, Any]]:
        """
        List files on the remote storage

        Args:
            path: Optional path to list (None for all files)

        Returns:
            Dictionary mapping file paths to metadata
        """
        pass

    @abstractmethod
    def upload_file(self, local_file_path: str, remote_path: str) -> bool:
        """
        Upload a file to remote storage

        Args:
            local_file_path: Path to local file
            remote_path: Path on remote storage

        Returns:
            True if upload successful, False otherwise
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_file_path: str) -> bool:
        """
        Download a file from remote storage

        Args:
            remote_path: Path on remote storage
            local_file_path: Path to save locally

        Returns:
            True if download successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from remote storage

        Args:
            remote_path: Path on remote storage

        Returns:
            True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def get_public_url(self, remote_path: str) -> str:
        """
        Get a public URL for a file in storage

        Args:
            remote_path: Path to the file in storage

        Returns:
            URL to access the file
        """
        pass

    def calculate_checksum(self, filepath: str) -> str:
        """
        Calculate file checksum using the configured algorithm

        Args:
            filepath: Path to the file

        Returns:
            Checksum string
        """
        algorithm = getattr(self.config, "checksum_algorithm", "sha256").lower()

        if algorithm == "sha256":
            hash_func = hashlib.sha256()
        elif algorithm == "md5":
            hash_func = hashlib.md5()
        elif algorithm == "sha1":
            hash_func = hashlib.sha1()
        else:
            self.logger.warning(f"Unsupported checksum algorithm: {algorithm}, using sha256")
            hash_func = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {filepath}: {e}")
            return ""

    def get_local_files(self, local_path: Path | str) -> Dict[str, str]:
        """
        Get all files and their checksums from local directory

        Args:
            local_path: Root path to scan for files

        Returns:
            Dict mapping relative file paths to checksums
        """
        local_files = {}
        # Use Path for better cross-platform path handling
        local_path_obj = Path(local_path)

        for root, _, files in os.walk(local_path_obj):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, local_path_obj)
                # Use forward slashes for paths (storage convention)
                relative_path = relative_path.replace("\\", "/")
                local_files[relative_path] = self.calculate_checksum(full_path)

        return local_files

    def get_local_files_in_paths(
        self, local_path: Path | str, sync_paths: List[str]
    ) -> Dict[str, str]:
        """
        Get files and checksums from specified paths in local directory

        Args:
            local_path: Root path to scan for files
            sync_paths: List of paths to include (relative to local_path)

        Returns:
            Dict mapping relative file paths to checksums
        """
        local_files = {}
        local_path_obj = Path(local_path)

        for sync_path in sync_paths:
            sync_path_full = local_path_obj / sync_path

            if sync_path_full.is_file():
                # Single file
                relative_path = os.path.relpath(sync_path_full, local_path_obj)
                relative_path = relative_path.replace("\\", "/")
                local_files[relative_path] = self.calculate_checksum(str(sync_path_full))
            elif sync_path_full.is_dir():
                # Directory - get all files within
                for root, _, files in os.walk(sync_path_full):
                    for file in files:
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, local_path_obj)
                        relative_path = relative_path.replace("\\", "/")
                        local_files[relative_path] = self.calculate_checksum(full_path)
            else:
                self.logger.warning(f"Sync path not found: {sync_path}")

        return local_files

    def sync(
        self,
        local_path: Path | str,
        max_workers: int = 4,
        delete_orphaned: bool = False,
        dry_run: bool = False,
        progress_callback: Callable[[int, int, str, str], None] | None = None,
        sync_paths: list[str] | None = None,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
    ) -> SyncResult:
        """
        Synchronize local directory with remote storage

        Args:
            local_path: Path to local directory
            max_workers: Maximum number of concurrent operations
            delete_orphaned: Whether to delete files on remote that don't exist locally
            dry_run: If True, only report what would be done without making changes
            progress_callback: Callback function for reporting progress
            sync_paths: Specific files/directories to sync (relative to local_path)
            include_pattern: Regex pattern for files to include
            exclude_pattern: Regex pattern for files to exclude

        Returns:
            SyncResult with synchronization results
        """
        # This provides a default implementation - specific backends can override
        if not os.path.isdir(local_path):
            raise NotADirectoryError(f"Local path does not exist: {local_path}")

        # Normalize paths
        local_path = Path(local_path)

        # Normalize write protected paths
        protected_patterns = []
        if sync_paths:
            protected_patterns = [str(Path(p)) for p in sync_paths]

        result = SyncResult()

        # Get local files
        self.logger.info(f"Scanning local directory: {local_path}")
        if sync_paths:
            self.logger.info(f"Limiting sync to {len(sync_paths)} specific paths")
            local_files = self.get_local_files_in_paths(local_path, sync_paths)
        else:
            local_files = self.get_local_files(local_path)

        # Get remote files
        self.logger.info("Scanning remote storage...")
        remote_files = self.list_remote_files()

        # Find files to upload (new or modified)
        to_upload = []
        for relative_path, local_checksum in local_files.items():
            if relative_path not in remote_files:
                # New file
                to_upload.append(relative_path)
                self.logger.debug(f"New file to upload: {relative_path}")
            elif remote_files[relative_path].get("Checksum") != local_checksum:
                # Modified file
                to_upload.append(relative_path)
                self.logger.debug(f"Modified file to upload: {relative_path}")
            else:
                result.unchanged += 1

        # Find orphaned files to delete
        to_delete = []
        if delete_orphaned:
            for remote_path in remote_files:
                if remote_path not in local_files:
                    # If sync_paths is specified, only delete files within those paths
                    if sync_paths:
                        if any(
                            remote_path.startswith(str(p).replace("\\", "/")) for p in sync_paths
                        ):
                            to_delete.append(remote_path)
                            self.logger.debug(f"Orphaned file to delete: {remote_path}")
                    else:
                        to_delete.append(remote_path)
                        self.logger.debug(f"Orphaned file to delete: {remote_path}")

        # Find files to download
        to_download = []
        for remote_path, remote_data in remote_files.items():
            # Skip if this file is in write-protected paths
            target_path = os.path.join(local_path, remote_path)
            if protected_patterns and any(target_path.startswith(p) for p in protected_patterns):
                self.logger.debug(f"Skipping write-protected file: {remote_path}")
                result.protected_skipped += 1
                continue

            # Check if within sync_paths
            if sync_paths and not any(
                remote_path.startswith(str(p).replace("\\", "/")) for p in sync_paths
            ):
                continue

            # If file doesn't exist locally or is different, download it
            if remote_path not in local_files:
                to_download.append(remote_path)
                self.logger.debug(f"New file to download: {remote_path}")

        # Report what would be done in dry run mode
        if dry_run:
            # Update counts to reflect what would happen in a real sync
            result.uploaded = len(to_upload)
            result.downloaded = len(to_download)
            if delete_orphaned:
                result.deleted = len(to_delete)

            self.logger.info(f"DRY RUN: Would upload {result.uploaded} files")
            if delete_orphaned:
                self.logger.info(f"DRY RUN: Would delete {result.deleted} files")
            self.logger.info(f"DRY RUN: Would download {result.downloaded} files")
            self.logger.info(f"DRY RUN: Would leave {result.unchanged} files unchanged")
            self.logger.info(
                f"DRY RUN: Would skip {result.protected_skipped} write-protected files"
            )
            return result

        # Process uploads
        if to_upload:
            self.logger.info(f"Uploading {len(to_upload)} files...")
            for i, relative_path in enumerate(to_upload):
                local_file_path = os.path.join(local_path, relative_path)

                if progress_callback:
                    progress_callback(i + 1, len(to_upload), "uploading", relative_path)

                try:
                    if self.upload_file(local_file_path, relative_path):
                        result.uploaded += 1
                    else:
                        result.failed += 1
                        if result.errors is not None:
                            result.errors.append(f"Failed to upload: {relative_path}")
                except Exception as e:
                    result.failed += 1
                    if result.errors is not None:
                        result.errors.append(f"Error uploading {relative_path}: {str(e)}")

        # Process downloads
        if to_download:
            self.logger.info(f"Downloading {len(to_download)} files...")
            for i, remote_path in enumerate(to_download):
                local_file_path = os.path.join(local_path, remote_path)

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                if progress_callback:
                    progress_callback(i + 1, len(to_download), "downloading", remote_path)

                try:
                    if self.download_file(remote_path, local_file_path):
                        result.downloaded += 1
                    else:
                        result.failed += 1
                        if result.errors is not None:
                            result.errors.append(f"Failed to download: {remote_path}")
                except Exception as e:
                    result.failed += 1
                    if result.errors is not None:
                        result.errors.append(f"Error downloading {remote_path}: {str(e)}")

        # Process deletions
        if to_delete:
            self.logger.info(f"Deleting {len(to_delete)} orphaned files...")
            for i, remote_path in enumerate(to_delete):
                if progress_callback:
                    progress_callback(i + 1, len(to_delete), "deleting", remote_path)

                try:
                    if self.delete_file(remote_path):
                        result.deleted += 1
                    else:
                        result.failed += 1
                        if result.errors is not None:
                            result.errors.append(f"Failed to delete: {remote_path}")
                except Exception as e:
                    result.failed += 1
                    if result.errors is not None:
                        result.errors.append(f"Error deleting {remote_path}: {str(e)}")

        # Update success status based on failures
        result.success = result.failed == 0

        self.logger.info(str(result))
        return result
