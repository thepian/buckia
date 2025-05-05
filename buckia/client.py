"""
Main client interface for Buckia
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path

from .config import BucketConfig
from .sync import create_sync_backend, SyncResult
from .sync.factory import get_sync_backend

# Configure logging
logger = logging.getLogger('buckia.client')

class BuckiaClient:
    """
    Main client interface for interacting with storage buckets
    
    This class provides a unified interface to different storage backends.
    """
    
    def __init__(self, config: Union[BucketConfig, Dict[str, Any], str]):
        """
        Initialize the client with configuration
        
        Args:
            config: Configuration as BucketConfig object, dict, or path to config file
        """
        if isinstance(config, str):
            # Load from file
            self.config = BucketConfig.from_file(config)
        elif isinstance(config, dict):
            # Create from dict
            if 'provider' not in config or 'bucket_name' not in config:
                raise ValueError("Configuration dict must contain 'provider' and 'bucket_name'")
            self.config = BucketConfig(**config)
        elif isinstance(config, BucketConfig):
            # Use provided config
            self.config = config
        else:
            raise TypeError("Config must be a BucketConfig object, dict, or path to config file")
            
        # Create backend
        self.backend = get_sync_backend(self.config)
        if not self.backend:
            raise ValueError(f"Failed to create sync backend for provider: {self.config.provider}")
            
        # Try to connect
        if not self.backend.connect():
            logger.warning(f"Failed to connect to {self.config.provider} bucket: {self.config.bucket_name}")
    
    def sync(
        self, 
        local_path: str,
        max_workers: Optional[int] = None,
        delete_orphaned: Optional[bool] = None,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        dry_run: bool = False,
        progress_callback: Optional[Callable] = None,
        sync_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
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
        logger.debug(f"Sync parameters: max_workers={max_workers}, "
                    f"delete_orphaned={delete_orphaned}, dry_run={dry_run}")
        
        # Convert local_path to a Path object
        local_path = Path(local_path)
        
        # Perform the synchronization using the backend
        result = self.backend.sync(
            local_path=local_path,
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
    
    def upload_file(self, local_file_path: str, remote_path: Optional[str] = None) -> bool:
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
    
    def list_files(self, path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List files on the remote storage
        
        Args:
            path: Optional path to list (None for all files)
            
        Returns:
            Dictionary mapping file paths to metadata
        """
        return self.backend.list_remote_files(path)
    
    def close(self):
        """Close the client and release resources"""
        if hasattr(self.backend, 'close'):
            self.backend.close()
            
    def __enter__(self):
        """Support context manager protocol"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the client when exiting context"""
        self.close() 