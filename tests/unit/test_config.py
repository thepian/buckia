"""
Unit tests for the configuration module
"""

import json
import os
import tempfile

import pytest
import yaml

from buckia.config import BucketConfig, BuckiaConfig


def test_bucket_config_init() -> None:
    """Test BucketConfig initialization with basic parameters"""
    config = BucketConfig(provider="test-provider", bucket_name="test-bucket")

    assert config.provider == "test-provider"
    assert config.bucket_name == "test-bucket"
    assert config.credentials == {}
    assert config.sync_paths == []
    assert config.delete_orphaned is False
    assert config.max_workers == 4
    assert config.checksum_algorithm == "sha256"
    assert config.conflict_resolution == "local_wins"
    assert config.region is None
    assert config.provider_settings == {}


def test_bucket_config_init_with_all_params() -> None:
    """Test BucketConfig initialization with all parameters"""
    sync_paths = ["path1", "path2"]
    provider_settings = {"setting1": "value1"}

    config = BucketConfig(
        provider="test-provider",
        bucket_name="test-bucket",
        sync_paths=sync_paths,
        delete_orphaned=True,
        max_workers=8,
        checksum_algorithm="md5",
        conflict_resolution="remote_wins",
        region="us-east-1",
        provider_settings=provider_settings,
    )

    assert config.provider == "test-provider"
    assert config.bucket_name == "test-bucket"
    assert config.sync_paths == sync_paths
    assert config.delete_orphaned is True
    assert config.max_workers == 8
    assert config.checksum_algorithm == "md5"
    assert config.conflict_resolution == "remote_wins"
    assert config.region == "us-east-1"
    assert config.provider_settings == provider_settings


def test_from_file_yaml() -> None:
    """Test loading config from YAML file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Create a test YAML config
            config_data = {
                "provider": "test-provider",
                "bucket_name": "test-bucket",
                "paths": ["path1", "path2"],
                "delete_orphaned": True,
                "max_workers": 8,
                "checksum_algorithm": "md5",
                "conflict_resolution": "remote_wins",
                "region": "us-east-1",
                "custom_setting": "custom_value",
            }

            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Load the config from file
            config = BucketConfig.from_file(temp_file.name)

            # Check the loaded config
            assert config.provider == "test-provider"
            assert config.bucket_name == "test-bucket"
            assert config.sync_paths == ["path1", "path2"]
            assert config.delete_orphaned is True
            assert config.max_workers == 8
            assert config.checksum_algorithm == "md5"
            assert config.conflict_resolution == "remote_wins"
            assert config.region == "us-east-1"
            assert "custom_setting" in config.provider_settings
            assert config.provider_settings["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_from_file_json() -> None:
    """Test loading config from JSON file"""
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as temp_file:
        try:
            # Create a test JSON config
            config_data = {
                "provider": "test-provider",
                "bucket_name": "test-bucket",
                "paths": ["path1", "path2"],
                "delete_orphaned": True,
                "max_workers": 8,
                "checksum_algorithm": "md5",
                "conflict_resolution": "remote_wins",
                "region": "us-east-1",
                "custom_setting": "custom_value",
            }

            json.dump(config_data, temp_file)
            temp_file.flush()

            # Load the config from file
            config = BucketConfig.from_file(temp_file.name)

            # Check the loaded config
            assert config.provider == "test-provider"
            assert config.bucket_name == "test-bucket"
            assert config.sync_paths == ["path1", "path2"]
            assert config.delete_orphaned is True
            assert config.max_workers == 8
            assert config.checksum_algorithm == "md5"
            assert config.conflict_resolution == "remote_wins"
            assert config.region == "us-east-1"
            assert "custom_setting" in config.provider_settings
            assert config.provider_settings["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_from_file_missing() -> None:
    """Test loading config from a non-existent file"""
    with pytest.raises(FileNotFoundError):
        BucketConfig.from_file("/nonexistent/path/to/config.yaml")


def test_from_file_invalid() -> None:
    """Test loading config from an invalid file (missing required fields)"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Create an invalid YAML config (missing required fields)
            config_data = {
                "provider": "test-provider",
                # Missing bucket_name
            }

            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Attempt to load the invalid config
            with pytest.raises(ValueError):
                BucketConfig.from_file(temp_file.name)

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_save_yaml() -> None:
    """Test saving config to YAML file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        try:
            # Create a config
            config = BucketConfig(
                provider="test-provider",
                bucket_name="test-bucket",
                sync_paths=["path1", "path2"],
                delete_orphaned=True,
                max_workers=8,
                checksum_algorithm="md5",
                conflict_resolution="remote_wins",
                region="us-east-1",
                provider_settings={"custom_setting": "custom_value"},
            )

            # Save the config to file
            config.save(temp_file.name)

            # Load and verify the saved config
            with open(temp_file.name, "r") as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["provider"] == "test-provider"
            assert saved_data["bucket_name"] == "test-bucket"
            assert saved_data["paths"] == ["path1", "path2"]
            assert saved_data["delete_orphaned"] is True
            assert saved_data["max_workers"] == 8
            assert saved_data["checksum_algorithm"] == "md5"
            assert saved_data["conflict_resolution"] == "remote_wins"
            assert saved_data["region"] == "us-east-1"
            assert saved_data["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_save_json() -> None:
    """Test saving config to JSON file"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        try:
            # Create a config
            config = BucketConfig(
                provider="test-provider",
                bucket_name="test-bucket",
                sync_paths=["path1", "path2"],
                delete_orphaned=True,
                max_workers=8,
                checksum_algorithm="md5",
                conflict_resolution="remote_wins",
                region="us-east-1",
                provider_settings={"custom_setting": "custom_value"},
            )

            # Save the config to file
            config.save(temp_file.name)

            # Load and verify the saved config
            with open(temp_file.name, "r") as f:
                saved_data = json.load(f)

            assert saved_data["provider"] == "test-provider"
            assert saved_data["bucket_name"] == "test-bucket"
            assert saved_data["paths"] == ["path1", "path2"]
            assert saved_data["delete_orphaned"] is True
            assert saved_data["max_workers"] == 8
            assert saved_data["checksum_algorithm"] == "md5"
            assert saved_data["conflict_resolution"] == "remote_wins"
            assert saved_data["region"] == "us-east-1"
            assert saved_data["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_get_provider_setting() -> None:
    """Test get_provider_setting method"""
    config = BucketConfig(
        provider="test-provider",
        bucket_name="test-bucket",
        provider_settings={"setting1": "value1", "setting2": "value2"},
    )

    assert config.get_provider_setting("setting1") == "value1"
    assert config.get_provider_setting("setting2") == "value2"
    assert config.get_provider_setting("nonexistent") is None
    assert config.get_provider_setting("nonexistent", "default") == "default"


# Tests for BuckiaConfig class


def test_buckia_config_init() -> None:
    """Test BuckiaConfig initialization"""
    config = BuckiaConfig()
    assert config.configs == {}


def test_buckia_config_getitem_setitem() -> None:
    """Test BuckiaConfig dictionary-like access"""
    # Create bucket configurations
    bucket1 = BucketConfig(provider="bunny", bucket_name="bucket1")
    bucket2 = BucketConfig(provider="s3", bucket_name="bucket2")

    # Create buckia config
    config = BuckiaConfig()

    # Add buckets
    config["dev"] = bucket1
    config["prod"] = bucket2

    # Access buckets
    assert config["dev"] == bucket1
    assert config["prod"] == bucket2

    # Test KeyError for nonexistent bucket
    with pytest.raises(KeyError):
        _ = config["nonexistent"]


def test_buckia_config_contains() -> None:
    """Test BuckiaConfig contains method"""
    # Create bucket configurations
    bucket = BucketConfig(provider="bunny", bucket_name="bucket1")

    # Create buckia config
    config = BuckiaConfig()
    config["dev"] = bucket

    # Test contains
    assert "dev" in config
    assert "nonexistent" not in config


def test_buckia_config_iteration() -> None:
    """Test BuckiaConfig iteration methods"""
    # Create bucket configurations
    bucket1 = BucketConfig(provider="bunny", bucket_name="bucket1")
    bucket2 = BucketConfig(provider="s3", bucket_name="bucket2")

    # Create buckia config
    config = BuckiaConfig()
    config["dev"] = bucket1
    config["prod"] = bucket2

    # Test iteration of keys
    keys = list(config)
    assert sorted(keys) == ["dev", "prod"]

    # Test items method
    items = list(config.items())
    assert len(items) == 2
    assert dict(items) == {"dev": bucket1, "prod": bucket2}

    # Test get method
    assert config.get("dev") == bucket1
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", bucket1) == bucket1


def test_buckia_config_from_file_yaml() -> None:
    """Test loading BuckiaConfig from YAML file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Create a test YAML config with multiple buckets
            config_data = {
                "default": {
                    "provider": "bunny",
                    "bucket_name": "default-bucket",
                    "token_context": "demo",
                    "paths": ["path1", "path2"],
                    "delete_orphaned": True,
                    "max_workers": 4,
                    "checksum_algorithm": "sha256",
                },
                "production": {
                    "provider": "bunny",
                    "bucket_name": "prod-bucket",
                    "token_context": "prod",
                    "delete_orphaned": True,
                    "max_workers": 8,
                    "region": "us-east-1",
                },
            }

            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Load the config from file
            config = BuckiaConfig.from_file(temp_file.name)

            # Check the loaded config
            assert "default" in config
            assert "production" in config

            # Check default bucket config
            default = config["default"]
            assert default.provider == "bunny"
            assert default.bucket_name == "default-bucket"
            assert default.token_context == "demo"
            assert default.sync_paths == ["path1", "path2"]
            assert default.delete_orphaned is True
            assert default.max_workers == 4
            assert default.checksum_algorithm == "sha256"

            # Check production bucket config
            prod = config["production"]
            assert prod.provider == "bunny"
            assert prod.bucket_name == "prod-bucket"
            assert prod.token_context == "prod"
            assert prod.delete_orphaned is True
            assert prod.max_workers == 8
            assert prod.region == "us-east-1"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_buckia_config_from_file_missing() -> None:
    """Test loading BuckiaConfig from a non-existent file"""
    with pytest.raises(FileNotFoundError):
        BuckiaConfig.from_file("/nonexistent/path/to/config.yaml")


def test_buckia_config_from_file_invalid() -> None:
    """Test loading BuckiaConfig from an invalid file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Create an invalid YAML config (not a dictionary)
            config_data = ["not", "a", "dictionary"]

            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Attempt to load the invalid config
            with pytest.raises(ValueError):
                BuckiaConfig.from_file(temp_file.name)

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_buckia_config_from_file_no_valid_buckets() -> None:
    """Test loading BuckiaConfig with no valid bucket configurations"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as temp_file:
        try:
            # Create a YAML config with invalid bucket configs
            config_data = {
                "default": {
                    # Missing provider and bucket_name
                    "token_context": "demo",
                },
                "production": "not a dictionary",
            }

            yaml.dump(config_data, temp_file)
            temp_file.flush()

            # Attempt to load the config with no valid buckets
            with pytest.raises(ValueError):
                BuckiaConfig.from_file(temp_file.name)

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_buckia_config_save_yaml() -> None:
    """Test saving BuckiaConfig to YAML file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        try:
            # Create a config with multiple buckets
            config = BuckiaConfig()

            config["default"] = BucketConfig(
                provider="bunny",
                bucket_name="default-bucket",
                token_context="demo",
                sync_paths=["path1", "path2"],
                delete_orphaned=True,
                max_workers=4,
            )

            config["production"] = BucketConfig(
                provider="s3",
                bucket_name="prod-bucket",
                token_context="prod",
                delete_orphaned=True,
                max_workers=8,
                region="us-east-1",
            )

            # Save the config to file
            config.save(temp_file.name)

            # Load and verify the saved config
            with open(temp_file.name, "r") as f:
                saved_data = yaml.safe_load(f)

            # Check that both buckets were saved
            assert "default" in saved_data
            assert "production" in saved_data

            # Check default bucket details
            default = saved_data["default"]
            assert default["provider"] == "bunny"
            assert default["bucket_name"] == "default-bucket"
            assert default["token_context"] == "demo"
            assert default["paths"] == ["path1", "path2"]

            # Check production bucket details
            prod = saved_data["production"]
            assert prod["provider"] == "s3"
            assert prod["bucket_name"] == "prod-bucket"
            assert prod["region"] == "us-east-1"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_buckia_config_default_path() -> None:
    """Test default_config_path method"""
    path = BuckiaConfig.default_config_path()
    expected_path = os.path.join(os.path.expanduser("~"), ".buckia", "config.yaml")
    assert path == expected_path
