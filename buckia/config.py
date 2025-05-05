"""
Configuration management for Buckia
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BucketConfig:
    """Configuration for storage bucket synchronization"""
    
    # Basic configuration
    provider: str  # Provider type: 'bunny', 's3', 'linode'
    bucket_name: str  # Name of the bucket/storage zone
    
    # Authentication
    credentials: Dict[str, str] = field(default_factory=dict)  # Provider-specific credentials
    
    # Cache settings
    cache_dir: Optional[str] = None  # Local cache directory
    
    # Sync settings
    sync_paths: List[str] = field(default_factory=list)  # Paths to sync (relative to local path)
    delete_orphaned: bool = False  # Whether to delete files on remote that don't exist locally
    max_workers: int = 4  # Maximum number of concurrent operations
    
    # Advanced settings
    checksum_algorithm: str = "sha256"  # Algorithm for file checksums
    conflict_resolution: str = "local_wins"  # Conflict resolution strategy
    region: Optional[str] = None  # Region for the bucket (if applicable)
    
    # Provider-specific settings
    provider_settings: Dict[str, Any] = field(default_factory=dict)  # Additional provider-specific settings
    
    @classmethod
    def from_file(cls, config_path: str) -> 'BucketConfig':
        """Load configuration from a YAML or JSON file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        # Determine file type by extension
        ext = os.path.splitext(config_path)[1].lower()
        
        with open(config_path, 'r') as f:
            if ext in ('.yaml', '.yml'):
                config_data = yaml.safe_load(f)
            elif ext == '.json':
                config_data = json.load(f)
            else:
                # Default to YAML for .buckia files
                config_data = yaml.safe_load(f)
        
        # Extract basic settings
        provider = config_data.get('provider')
        bucket_name = config_data.get('bucket_name')
        
        if not provider or not bucket_name:
            raise ValueError("Missing required fields in config: provider and/or bucket_name")
            
        # Extract other settings
        credentials = config_data.get('auth', {})
        cache_dir = config_data.get('cache_dir')
        
        # Extract sync settings
        sync_settings = config_data.get('sync', {})
        sync_paths = sync_settings.get('paths', [])
        delete_orphaned = sync_settings.get('delete_orphaned', False)
        max_workers = sync_settings.get('max_workers', 4)
        
        # Advanced settings
        checksum_algorithm = config_data.get('checksum_algorithm', 'sha256')
        conflict_resolution = config_data.get('conflict_resolution', 'local_wins')
        region = config_data.get('region')
        
        # Any other provider-specific settings
        provider_settings = {k: v for k, v in config_data.items() 
                            if k not in ('provider', 'bucket_name', 'auth', 'cache_dir', 
                                         'sync', 'checksum_algorithm', 'conflict_resolution', 'region')}
        
        return cls(
            provider=provider,
            bucket_name=bucket_name,
            credentials=credentials,
            cache_dir=cache_dir,
            sync_paths=sync_paths,
            delete_orphaned=delete_orphaned,
            max_workers=max_workers,
            checksum_algorithm=checksum_algorithm,
            conflict_resolution=conflict_resolution,
            region=region,
            provider_settings=provider_settings
        )
        
    def save(self, config_path: str) -> None:
        """Save configuration to a YAML or JSON file"""
        ext = os.path.splitext(config_path)[1].lower()
        
        # Prepare data structure
        config_data = {
            'provider': self.provider,
            'bucket_name': self.bucket_name,
            'auth': self.credentials,
            'region': self.region,
            'cache_dir': self.cache_dir,
            'checksum_algorithm': self.checksum_algorithm,
            'conflict_resolution': self.conflict_resolution,
            'sync': {
                'paths': self.sync_paths,
                'delete_orphaned': self.delete_orphaned,
                'max_workers': self.max_workers
            }
        }
        
        # Add provider-specific settings
        for key, value in self.provider_settings.items():
            config_data[key] = value
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        
        # Write to file
        with open(config_path, 'w') as f:
            if ext == '.json':
                json.dump(config_data, f, indent=2)
            else:
                # Default to YAML
                yaml.dump(config_data, f, default_flow_style=False)
                
    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get a credential value by key with optional default"""
        return self.credentials.get(key, default)
        
    def get_provider_setting(self, key: str, default: Any = None) -> Any:
        """Get a provider-specific setting by key with optional default"""
        return self.provider_settings.get(key, default) 