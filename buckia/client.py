"""
Main client interface for Buckia
"""

import logging
import os
from typing import Any, Callable, Dict, Optional, Union

from .config import BucketConfig, BuckiaConfig

# Import TokenManager for API token management
from .security import TokenManager
from .sync import SyncResult
from .sync.factory import get_sync_backend

# Configure logging
logger = logging.getLogger("buckia.client")


class BuckiaClient:
    """
    Main client interface for interacting with storage buckets

    This class provides a unified interface to different storage backends.
    """

    config: BucketConfig

    def __init__(
        self,
        config: Union[BucketConfig, BuckiaConfig, Dict[str, Any], str],
        bucket_name: Optional[str] = None,
    ):
        """
        Initialize the client with configuration

        Args:
            config: Configuration as BucketConfig, BuckiaConfig, dict, or path to config file
            bucket_name: For BuckiaConfig, the name of the bucket configuration to use
                         (required when using BuckiaConfig with multiple buckets)
        """
        # Handle string path - could load either BucketConfig or BuckiaConfig
        if isinstance(config, str):
            try:
                # First try loading as a multi-bucket configuration
                buckia_config = BuckiaConfig.from_file(config)

                # If successful, select the appropriate bucket config
                if bucket_name:
                    if bucket_name in buckia_config:
                        self.config = buckia_config[bucket_name]
                    else:
                        raise ValueError(
                            f"Bucket configuration '{bucket_name}' not found in {config}"
                        )
                else:
                    # Try to get the "default" bucket or the first one
                    if "default" in buckia_config:
                        self.config = buckia_config["default"]
                    elif len(buckia_config.configs) == 1:
                        # If there's only one bucket, use it
                        self.config = next(iter(buckia_config.configs.values()))
                    else:
                        # Multiple buckets but no default
                        available_buckets = ", ".join(buckia_config.configs.keys())
                        raise ValueError(
                            f"Multiple bucket configurations found in {config}. "
                            f"Please specify bucket_name from: {available_buckets}"
                        )
            except (ValueError, KeyError):
                # Fallback to loading as a single bucket configuration
                logger.info(f"Loading {config} as a single bucket configuration")
                self.config = BucketConfig.from_file(config)

        # Handle BuckiaConfig
        elif isinstance(config, BuckiaConfig):
            buckia_config: BuckiaConfig = config
            if bucket_name:
                if bucket_name in config:
                    self.config = config[bucket_name]
                else:
                    available_buckets = ", ".join(buckia_config.configs.keys())
                    raise ValueError(
                        f"Bucket configuration '{bucket_name}' not found. "
                        f"Available buckets: {available_buckets}"
                    )
            else:
                # Try to get the "default" bucket or the first one
                if "default" in config:
                    self.config = config["default"]
                elif len(buckia_config.configs) == 1:
                    # If there's only one bucket, use it
                    self.config = next(iter(buckia_config.configs.values()))
                else:
                    # Multiple buckets but no default
                    available_buckets = ", ".join(buckia_config.configs.keys())
                    raise ValueError(
                        f"Multiple bucket configurations found. "
                        f"Please specify bucket_name from: {available_buckets}"
                    )

        # Handle dict (convert to BucketConfig)
        elif isinstance(config, Dict):
            # Create from dict
            if "provider" not in config or "bucket_name" not in config:
                raise ValueError("Configuration dict must contain 'provider' and 'bucket_name'")
            self.config = BucketConfig(**config)

        # Handle BucketConfig
        elif isinstance(config, BucketConfig):
            # Use provided config
            self.config = config

        else:
            raise TypeError(
                "Config must be a BucketConfig, BuckiaConfig, dict, or path to config file"
            )

        # Check if we need to get credentials from token manager
        if not self.config.credentials:
            # Get bucket context name (default to provider name)
            context = self.config.token_context or self.config.provider

            try:
                # Get token from keyring
                token_manager = TokenManager(namespace="buckia")
                token = token_manager.get_token(context)
                if token:
                    logger.info(f"Using API key from token manager for bucket context: {context}")
                    # Use token for authentication
                    self.config.credentials = {"api_key": token}
            except Exception as e:
                logger.warning(f"Failed to get token from keyring: {e}")

        # Create backend
        backend = get_sync_backend(self.config)
        if backend is None:
            raise ValueError(f"Failed to create sync backend for provider: {self.config.provider}")
        self.backend = backend  # Now backend is guaranteed to be non-None

        # Try to connect
        if not self.backend.connect():
            logger.warning(
                f"Failed to connect to {self.config.provider} bucket: {self.config.bucket_name}"
            )

    def sync(
        self,
        local_path: str,
        max_workers: int | None = None,
        delete_orphaned: bool | None = None,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        sync_paths: list[str] | None = None,
    ) -> SyncResult:
        """
        Synchronize files between local directory and remote storage

        Args:
            local_path: Path to local directory to sync
            max_workers: Maximum number of concurrent operations
            delete_orphaned: Whether to delete files on remote that don't exist locally
            include_pattern: Regex pattern for files to include
            exclude_pattern: Regex pattern for files to exclude
            dry_run: If True, only report what would be done without making changes
            progress_callback: Callback function for reporting progress
            sync_paths: Specific paths to sync (relative to local_path)

        Returns:
            Dict with synchronization results
        """
        # Use config values as defaults if parameters not specified
        if max_workers is None:
            max_workers = self.config.max_workers

        if delete_orphaned is None:
            delete_orphaned = self.config.delete_orphaned

        if sync_paths is None:
            sync_paths = self.config.sync_paths

        logger.info(f"Starting sync operation for {local_path}")
        logger.debug(
            f"Sync parameters: max_workers={max_workers}, "
            f"delete_orphaned={delete_orphaned}, dry_run={dry_run}"
        )

        # Convert local_path to a string path
        local_path_str = str(local_path)

        # Perform the synchronization using the backend
        result = self.backend.sync(
            local_path=local_path_str,
            max_workers=max_workers,
            delete_orphaned=delete_orphaned,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
            dry_run=dry_run,
            progress_callback=progress_callback,
            sync_paths=sync_paths,
        )

        logger.info(f"Sync operation completed: {result}")
        return result

    def test_connection(self) -> Dict[str, bool]:
        """
        Test connection to the remote storage

        Returns:
            Dictionary with test results for various authentication methods
        """
        return self.backend.test_connection()

    def upload_file(self, local_file_path: str, remote_path: str | None = None) -> bool:
        """
        Upload a single file to remote storage

        Args:
            local_file_path: Path to local file
            remote_path: Path on remote storage (if None, will use basename of local_file_path)

        Returns:
            True if upload successful, False otherwise
        """
        if not os.path.exists(local_file_path):
            logger.error(f"Local file not found: {local_file_path}")
            return False

        if remote_path is None:
            remote_path = os.path.basename(local_file_path)

        return self.backend.upload_file(local_file_path, remote_path)

    def download_file(self, remote_path: str, local_file_path: str) -> bool:
        """
        Download a file from remote storage

        Args:
            remote_path: Path on remote storage
            local_file_path: Path to save locally

        Returns:
            True if download successful, False otherwise
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True)

        return self.backend.download_file(remote_path, local_file_path)

    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from remote storage

        Args:
            remote_path: Path on remote storage

        Returns:
            True if deletion successful, False otherwise
        """
        return self.backend.delete_file(remote_path)

    def get_public_url(self, remote_path: str) -> str:
        """
        Get a public URL for a file in storage

        Args:
            remote_path: Path to the file in storage

        Returns:
            URL to access the file
        """
        return self.backend.get_public_url(remote_path)

    def list_files(self, path: str | None = None) -> Dict[str, Dict[str, Any]]:
        """
        List files on the remote storage

        Args:
            path: Optional path to list (None for all files)

        Returns:
            Dictionary mapping file paths to metadata
        """
        return self.backend.list_remote_files(path)

    def close(self) -> None:
        """Close the client and release resources"""
        if hasattr(self.backend, "close"):
            self.backend.close()

    def __enter__(self) -> "BuckiaClient":
        """Support context manager protocol"""
        return self

    def __exit__(
        self, exc_type: Optional[Exception], exc_val: Optional[type], exc_tb: Optional[Any]
    ) -> None:
        """Close the client when exiting context"""
        self.close()
