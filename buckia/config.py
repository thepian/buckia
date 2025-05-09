"""
Configuration management for Buckia
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

import yaml

# Configure logging
logger = logging.getLogger("buckia.config")


@dataclass
class BucketConfig:
    """Configuration for storage bucket synchronization"""

    # Basic configuration
    provider: str  # Provider type: 'bunny', 'b2', 's3', 'linode'
    bucket_name: str  # Name of the bucket/storage zone

    # Authentication
    credentials: Dict[str, str] = field(default_factory=dict)  # Provider-specific credentials
    token_context: str | None = None  # Name of context for token retrieval in keyring

    # Sync settings
    sync_paths: List[str] = field(default_factory=list)  # Paths to sync (relative to local path)
    delete_orphaned: bool = False  # Whether to delete files on remote that don't exist locally
    max_workers: int = 4  # Maximum number of concurrent operations

    # Advanced settings
    checksum_algorithm: str = "sha256"  # Algorithm for file checksums
    conflict_resolution: str = "local_wins"  # Conflict resolution strategy
    region: str | None = None  # Region for the bucket (if applicable)

    # Provider-specific settings
    provider_settings: Dict[str, Any] = field(
        default_factory=dict
    )  # Additional provider-specific settings

    @classmethod
    def from_file(cls, config_path: str) -> "BucketConfig":
        """
        Load a single bucket configuration from a YAML or JSON file.

        Note: For multiple bucket configurations, use BuckiaConfig.from_file() instead.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Determine file type by extension
        ext = os.path.splitext(config_path)[1].lower()

        with open(config_path, "r") as f:
            if ext in (".yaml", ".yml"):
                config_data = yaml.safe_load(f)
            elif ext == ".json":
                config_data = json.load(f)
            else:
                # Default to YAML for .buckia files
                config_data = yaml.safe_load(f)

        # Check if this is a multi-bucket config
        if isinstance(config_data, dict) and not config_data.get("provider"):
            # This looks like a multi-bucket config
            logger.warning(
                f"File {config_path} appears to contain multiple bucket configurations. "
                f"Consider using BuckiaConfig.from_file() instead."
            )

            # Try to use the "default" bucket or the first one
            if "default" in config_data:
                logger.info(f"Using 'default' bucket configuration from {config_path}")
                config_data = config_data["default"]
            else:
                # Use the first bucket configuration
                bucket_name = next(iter(config_data.keys()))
                logger.info(f"Using '{bucket_name}' bucket configuration from {config_path}")
                config_data = config_data[bucket_name]

        # Extract basic settings
        if not isinstance(config_data, dict):
            raise ValueError(
                f"Invalid configuration data: expected a dictionary, got {type(config_data).__name__}"
            )

        provider = config_data.get("provider")
        bucket_name = config_data.get("bucket_name")

        if not provider or not bucket_name:
            raise ValueError("Missing required fields in config: provider and/or bucket_name")

        # Extract other settings
        token_context = config_data.get("token_context")

        # Extract sync settings
        sync_paths = config_data.get("paths", [])
        delete_orphaned = config_data.get("delete_orphaned", False)
        max_workers = config_data.get("max_workers", 4)

        # Advanced settings
        checksum_algorithm = config_data.get("checksum_algorithm", "sha256")
        conflict_resolution = config_data.get("conflict_resolution", "local_wins")
        region = config_data.get("region")

        # Any other provider-specific settings
        provider_settings = {
            k: v
            for k, v in config_data.items()
            if k
            not in (
                "provider",
                "bucket_name",
                "auth",
                "token_context",
                "sync",
                "checksum_algorithm",
                "conflict_resolution",
                "region",
            )
        }

        return cls(
            provider=provider,
            bucket_name=bucket_name,
            token_context=token_context,
            sync_paths=sync_paths,
            delete_orphaned=delete_orphaned,
            max_workers=max_workers,
            checksum_algorithm=checksum_algorithm,
            conflict_resolution=conflict_resolution,
            region=region,
            provider_settings=provider_settings,
        )

    def save(self, config_path: str) -> None:
        """Save configuration to a YAML or JSON file"""
        ext = os.path.splitext(config_path)[1].lower()

        # Prepare data structure
        config_data = {
            "provider": self.provider,
            "bucket_name": self.bucket_name,
            "region": self.region,
            "checksum_algorithm": self.checksum_algorithm,
            "conflict_resolution": self.conflict_resolution,
            "paths": self.sync_paths,
            "delete_orphaned": self.delete_orphaned,
            "max_workers": self.max_workers,
        }

        # Add token_context if specified
        if self.token_context:
            config_data["token_context"] = self.token_context

        # Add provider-specific settings
        for key, value in self.provider_settings.items():
            config_data[key] = value

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)

        # Write to file
        with open(config_path, "w") as f:
            if ext == ".json":
                json.dump(config_data, f, indent=2)
            else:
                # Default to YAML
                yaml.dump(config_data, f, default_flow_style=False)

    def get_provider_setting(self, key: str, default: Any = None) -> Any:
        """Get a provider-specific setting by key with optional default"""
        return self.provider_settings.get(key, default)


@dataclass
class BuckiaConfig:
    """
    Configuration container for multiple bucket configurations.
    This allows a single .buckia file to hold configurations for multiple buckets.
    """

    configs: Dict[str, BucketConfig] = field(default_factory=dict)

    def __getitem__(self, key: str) -> BucketConfig:
        """Get a bucket configuration by name"""
        if key not in self.configs:
            raise KeyError(f"Bucket configuration not found: {key}")
        return self.configs[key]

    def __setitem__(self, key: str, value: BucketConfig) -> None:
        """Set a bucket configuration by name"""
        self.configs[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if a bucket configuration exists"""
        return key in self.configs

    def __iter__(self) -> Iterator[str]:
        """Iterate through bucket configuration names"""
        return iter(self.configs)

    def items(self) -> Iterator[tuple[str, BucketConfig]]:
        """Iterate through bucket configurations as (name, config) pairs"""
        return self.configs.items()

    def get(self, key: str, default: Optional[BucketConfig] = None) -> Optional[BucketConfig]:
        """Get a bucket configuration by name with default value"""
        return self.configs.get(key, default)

    @classmethod
    def from_file(cls, config_path: str) -> "BuckiaConfig":
        """
        Load multiple bucket configurations from a YAML or JSON file.

        Args:
            config_path: Path to the configuration file

        Returns:
            A BuckiaConfig object containing multiple bucket configurations

        Example .buckia file format:
        ```yaml
        default:  # This is the default bucket name
          provider: bunny
          bucket_name: my-storage-zone
          token_context: demo
          # Other bucket-specific settings...

        production:  # Another named bucket configuration
          provider: b2
          bucket_name: my-production-bucket
          token_context: production
          # Other bucket-specific settings...
        ```
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Determine file type by extension
        ext = os.path.splitext(config_path)[1].lower()

        with open(config_path, "r") as f:
            if ext in (".yaml", ".yml"):
                config_data = yaml.safe_load(f)
            elif ext == ".json":
                config_data = json.load(f)
            else:
                # Default to YAML for .buckia files
                config_data = yaml.safe_load(f)

        if not isinstance(config_data, dict):
            raise ValueError(
                f"Invalid configuration format in {config_path}. Expected a dictionary."
            )

        buckia_config = cls()

        # Process each bucket configuration
        for bucket_name, bucket_data in config_data.items():
            if not isinstance(bucket_data, dict):
                logger.warning(
                    f"Skipping invalid bucket configuration for '{bucket_name}'. Expected a dictionary."
                )
                continue

            # Extract required fields
            provider = bucket_data.get("provider")
            bucket_name_value = bucket_data.get("bucket_name")

            if not provider or not bucket_name_value:
                logger.warning(
                    f"Skipping bucket configuration for '{bucket_name}'. "
                    f"Missing required fields: provider and/or bucket_name"
                )
                continue

            # Extract other fields
            token_context = bucket_data.get("token_context", bucket_name)  # Default to bucket name

            # Extract sync settings
            sync_paths = bucket_data.get("paths", [])
            delete_orphaned = bucket_data.get("delete_orphaned", False)
            max_workers = bucket_data.get("max_workers", 4)

            # Advanced settings
            checksum_algorithm = bucket_data.get("checksum_algorithm", "sha256")
            conflict_resolution = bucket_data.get("conflict_resolution", "local_wins")
            region = bucket_data.get("region")

            # Provider-specific settings (any remaining keys)
            provider_settings = {
                k: v
                for k, v in bucket_data.items()
                if k
                not in (
                    "provider",
                    "bucket_name",
                    "auth",
                    "token_context",
                    "sync",
                    "checksum_algorithm",
                    "conflict_resolution",
                    "region",
                )
            }

            # Create BucketConfig and add to our collection
            bucket_config = BucketConfig(
                provider=provider,
                bucket_name=bucket_name_value,
                token_context=token_context,
                sync_paths=sync_paths,
                delete_orphaned=delete_orphaned,
                max_workers=max_workers,
                checksum_algorithm=checksum_algorithm,
                conflict_resolution=conflict_resolution,
                region=region,
                provider_settings=provider_settings,
            )

            buckia_config.configs[bucket_name] = bucket_config

        if not buckia_config.configs:
            raise ValueError(f"No valid bucket configurations found in {config_path}")

        return buckia_config

    def save(self, config_path: str) -> None:
        """
        Save all bucket configurations to a YAML or JSON file.

        Args:
            config_path: Path to save the configuration file
        """
        ext = os.path.splitext(config_path)[1].lower()

        # Prepare data structure
        config_data = {}

        for bucket_name, bucket_config in self.configs.items():
            bucket_data = {
                "provider": bucket_config.provider,
                "bucket_name": bucket_config.bucket_name,
                "token_context": bucket_config.token_context,
                "checksum_algorithm": bucket_config.checksum_algorithm,
                "conflict_resolution": bucket_config.conflict_resolution,
                "paths": bucket_config.sync_paths,
                "delete_orphaned": bucket_config.delete_orphaned,
                "max_workers": bucket_config.max_workers,
            }

            # Add region if specified
            if bucket_config.region:
                bucket_data["region"] = bucket_config.region

            # Add provider-specific settings
            for key, value in bucket_config.provider_settings.items():
                bucket_data[key] = value

            config_data[bucket_name] = bucket_data

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)

        # Write to file
        with open(config_path, "w") as f:
            if ext == ".json":
                json.dump(config_data, f, indent=2)
            else:
                # Default to YAML
                yaml.dump(config_data, f, default_flow_style=False)

    @classmethod
    def default_config_path(cls) -> str:
        """
        Return the default path for the .buckia configuration file.

        Returns:
            Path to the default .buckia configuration file
        """
        return os.path.join(os.path.expanduser("~"), ".buckia", "config.yaml")
