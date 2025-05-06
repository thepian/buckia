"""
Unit tests for the configuration module
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from buckia.config import BucketConfig


def test_bucket_config_init():
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


def test_bucket_config_init_with_all_params():
    """Test BucketConfig initialization with all parameters"""
    credentials = {"api_key": "test-key"}
    sync_paths = ["path1", "path2"]
    provider_settings = {"setting1": "value1"}

    config = BucketConfig(
        provider="test-provider",
        bucket_name="test-bucket",
        credentials=credentials,
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
    assert config.credentials == credentials
    assert config.sync_paths == sync_paths
    assert config.delete_orphaned is True
    assert config.max_workers == 8
    assert config.checksum_algorithm == "md5"
    assert config.conflict_resolution == "remote_wins"
    assert config.region == "us-east-1"
    assert config.provider_settings == provider_settings


def test_from_file_yaml():
    """Test loading config from YAML file"""
    with tempfile.NamedTemporaryFile(
        suffix=".yaml", mode="w", delete=False
    ) as temp_file:
        try:
            # Create a test YAML config
            config_data = {
                "provider": "test-provider",
                "bucket_name": "test-bucket",
                "auth": {"api_key": "test-key"},
                "sync": {
                    "paths": ["path1", "path2"],
                    "delete_orphaned": True,
                    "max_workers": 8,
                },
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
            assert config.credentials == {"api_key": "test-key"}
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


def test_from_file_json():
    """Test loading config from JSON file"""
    with tempfile.NamedTemporaryFile(
        suffix=".json", mode="w", delete=False
    ) as temp_file:
        try:
            # Create a test JSON config
            config_data = {
                "provider": "test-provider",
                "bucket_name": "test-bucket",
                "auth": {"api_key": "test-key"},
                "sync": {
                    "paths": ["path1", "path2"],
                    "delete_orphaned": True,
                    "max_workers": 8,
                },
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
            assert config.credentials == {"api_key": "test-key"}
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


def test_from_file_missing():
    """Test loading config from a non-existent file"""
    with pytest.raises(FileNotFoundError):
        BucketConfig.from_file("/nonexistent/path/to/config.yaml")


def test_from_file_invalid():
    """Test loading config from an invalid file (missing required fields)"""
    with tempfile.NamedTemporaryFile(
        suffix=".yaml", mode="w", delete=False
    ) as temp_file:
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


def test_save_yaml():
    """Test saving config to YAML file"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        try:
            # Create a config
            config = BucketConfig(
                provider="test-provider",
                bucket_name="test-bucket",
                credentials={"api_key": "test-key"},
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
            assert saved_data["auth"] == {"api_key": "test-key"}
            assert saved_data["sync"]["paths"] == ["path1", "path2"]
            assert saved_data["sync"]["delete_orphaned"] is True
            assert saved_data["sync"]["max_workers"] == 8
            assert saved_data["checksum_algorithm"] == "md5"
            assert saved_data["conflict_resolution"] == "remote_wins"
            assert saved_data["region"] == "us-east-1"
            assert saved_data["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_save_json():
    """Test saving config to JSON file"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        try:
            # Create a config
            config = BucketConfig(
                provider="test-provider",
                bucket_name="test-bucket",
                credentials={"api_key": "test-key"},
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
            assert saved_data["auth"] == {"api_key": "test-key"}
            assert saved_data["sync"]["paths"] == ["path1", "path2"]
            assert saved_data["sync"]["delete_orphaned"] is True
            assert saved_data["sync"]["max_workers"] == 8
            assert saved_data["checksum_algorithm"] == "md5"
            assert saved_data["conflict_resolution"] == "remote_wins"
            assert saved_data["region"] == "us-east-1"
            assert saved_data["custom_setting"] == "custom_value"

        finally:
            # Clean up temp file
            os.unlink(temp_file.name)


def test_get_credential():
    """Test get_credential method"""
    config = BucketConfig(
        provider="test-provider",
        bucket_name="test-bucket",
        credentials={"api_key": "test-key", "secret": "test-secret"},
    )

    assert config.get_credential("api_key") == "test-key"
    assert config.get_credential("secret") == "test-secret"
    assert config.get_credential("nonexistent") is None
    assert config.get_credential("nonexistent", "default") == "default"


def test_get_provider_setting():
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
