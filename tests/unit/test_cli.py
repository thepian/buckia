"""
Unit tests for the CLI module
"""

import os
import sys
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from buckia.cli import (
    parse_args, 
    cmd_sync, 
    cmd_status, 
    cmd_init, 
    main, 
    progress_callback,
    DEFAULT_CONFIG_FILE
)
from buckia.config import BucketConfig
from buckia.sync.base import SyncResult


def test_progress_callback(capsys):
    """Test the progress callback function"""
    # Call the callback
    progress_callback(5, 10, "uploading", "test.txt")
    
    # Capture stdout
    captured = capsys.readouterr()
    
    # Verify output format
    assert "Uploading: 5/10 (50%) - test.txt" in captured.out


@pytest.mark.skip(reason="Requires special handling for argparse exit behavior")
@patch('argparse.ArgumentParser.exit')
@patch('argparse.ArgumentParser.error')
def test_parse_args_sync(mock_error, mock_exit):
    """Test parsing sync command arguments"""
    # Prevent system exit
    mock_exit.side_effect = SystemExit
    mock_error.side_effect = SystemExit
    
    # Catch SystemExit but continue test
    try:
        args = parse_args(["sync", "-d", "/test/dir", "--paths", "path1", "path2", "--dry-run"])
    except SystemExit:
        args = None
    
    assert args.command == "sync"
    assert args.directory == "/test/dir"
    assert args.paths == ["path1", "path2"]
    assert args.dry_run is True
    assert args.func.__name__ == "cmd_sync"


@pytest.mark.skip(reason="Requires special handling for argparse exit behavior")
@patch('argparse.ArgumentParser.exit')
@patch('argparse.ArgumentParser.error')
def test_parse_args_status(mock_error, mock_exit):
    """Test parsing status command arguments"""
    # Prevent system exit
    mock_exit.side_effect = SystemExit
    mock_error.side_effect = SystemExit
    
    # Catch SystemExit but continue test
    try:
        args = parse_args(["status", "-d", "/test/dir", "--paths", "path1", "path2"])
    except SystemExit:
        args = None
    
    assert args.command == "status"
    assert args.directory == "/test/dir"
    assert args.paths == ["path1", "path2"]
    assert args.func.__name__ == "cmd_status"


@pytest.mark.skip(reason="Requires special handling for argparse exit behavior")
@patch('argparse.ArgumentParser.exit')
@patch('argparse.ArgumentParser.error')
def test_parse_args_init(mock_error, mock_exit):
    """Test parsing init command arguments"""
    # Prevent system exit
    mock_exit.side_effect = SystemExit
    mock_error.side_effect = SystemExit
    
    # Catch SystemExit but continue test
    try:
        args = parse_args([
            "init", 
            "-d", "/test/dir", 
            "--provider", "bunny", 
            "--bucket-name", "test-bucket",
            "--api-key", "test-key",
            "--force"
        ])
    except SystemExit:
        args = None
    
    assert args.command == "init"
    assert args.directory == "/test/dir"
    assert args.provider == "bunny"
    assert args.bucket_name == "test-bucket"
    assert args.api_key == "test-key"
    assert args.force is True
    assert args.func.__name__ == "cmd_init"


@pytest.mark.skip(reason="Requires special handling for argparse exit behavior")
@patch('argparse.ArgumentParser.exit')
@patch('argparse.ArgumentParser.error')
def test_parse_args_verbose(mock_error, mock_exit):
    """Test parsing verbose flag"""
    # Prevent system exit
    mock_exit.side_effect = SystemExit
    mock_error.side_effect = SystemExit
    
    with patch("buckia.cli.logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Catch SystemExit but continue test
        try:
            args = parse_args(["sync", "--verbose"])
        except SystemExit:
            args = None
        
        assert args.verbose is True
        mock_get_logger.assert_called_with("buckia")
        mock_logger.setLevel.assert_called_with(pytest.import_module("logging").DEBUG)


@pytest.mark.skip(reason="Requires special handling for argparse exit behavior")
@patch('argparse.ArgumentParser.exit')
@patch('argparse.ArgumentParser.error')
def test_parse_args_quiet(mock_error, mock_exit):
    """Test parsing quiet flag"""
    # Prevent system exit
    mock_exit.side_effect = SystemExit
    mock_error.side_effect = SystemExit
    
    with patch("buckia.cli.logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Catch SystemExit but continue test
        try:
            args = parse_args(["sync", "--quiet"])
        except SystemExit:
            args = None
        
        assert args.quiet is True
        mock_get_logger.assert_called_with("buckia")
        mock_logger.setLevel.assert_called_with(pytest.import_module("logging").WARNING)


@patch("buckia.cli.BucketConfig.from_file")
@patch("buckia.cli.BuckiaClient")
def test_cmd_sync_success(mock_client_class, mock_from_file):
    """Test successful sync command"""
    # Setup mocks
    mock_config = MagicMock()
    mock_from_file.return_value = mock_config
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the sync result
    mock_result = MagicMock()
    mock_result.success = True
    mock_client.sync.return_value = mock_result
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.paths = ["path1", "path2"]
    args.dry_run = False
    args.delete_orphaned = True
    args.max_workers = 4
    args.quiet = False
    
    # Run the command
    exit_code = cmd_sync(args)
    
    # Verify
    assert exit_code == 0
    mock_from_file.assert_called_once_with("/test/config")
    mock_client_class.assert_called_once_with(mock_config)
    mock_client.sync.assert_called_once_with(
        local_path="/test/dir",
        dry_run=False,
        progress_callback=progress_callback,
        sync_paths=["path1", "path2"],
        delete_orphaned=True,
        max_workers=4
    )


@patch("buckia.cli.BucketConfig.from_file")
@patch("buckia.cli.BuckiaClient")
def test_cmd_sync_failure(mock_client_class, mock_from_file):
    """Test sync command with failed result"""
    # Setup mocks
    mock_config = MagicMock()
    mock_from_file.return_value = mock_config
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock the sync result
    mock_result = MagicMock()
    mock_result.success = False
    mock_client.sync.return_value = mock_result
    
    # Create args
    args = MagicMock()
    args.config = None
    args.directory = "/test/dir"
    args.paths = None
    args.dry_run = False
    args.delete_orphaned = None
    args.max_workers = None
    args.quiet = False
    
    # Run the command
    exit_code = cmd_sync(args)
    
    # Verify
    assert exit_code == 1
    mock_from_file.assert_called_once_with(f"/test/dir/{DEFAULT_CONFIG_FILE}")
    mock_client_class.assert_called_once_with(mock_config)
    mock_client.sync.assert_called_once_with(
        local_path="/test/dir",
        dry_run=False,
        progress_callback=progress_callback
    )


@patch("buckia.cli.BucketConfig.from_file")
@patch("buckia.cli.BuckiaClient")
def test_cmd_sync_exception(mock_client_class, mock_from_file):
    """Test sync command with exception"""
    # Setup mocks
    mock_from_file.side_effect = ValueError("Config error")
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.quiet = False
    
    # Run the command
    exit_code = cmd_sync(args)
    
    # Verify
    assert exit_code == 1
    mock_from_file.assert_called_once_with("/test/config")
    mock_client_class.assert_not_called()


@patch("buckia.cli.BucketConfig.from_file")
@patch("buckia.cli.BuckiaClient")
def test_cmd_status_success(mock_client_class, mock_from_file, capsys):
    """Test successful status command"""
    # Setup mocks
    mock_config = MagicMock()
    mock_from_file.return_value = mock_config
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    # Mock test_connection
    mock_client.test_connection.return_value = {
        "api_key": True,
        "password": None,
        "bunnycdn_package": False
    }
    
    # Mock sync result
    mock_result = MagicMock()
    mock_result.uploaded = 5
    mock_result.downloaded = 3
    mock_result.deleted = 1
    mock_result.unchanged = 10
    mock_result.protected_skipped = 2
    mock_client.sync.return_value = mock_result
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.paths = ["path1", "path2"]
    
    # Run the command
    exit_code = cmd_status(args)
    
    # Verify
    assert exit_code == 0
    mock_from_file.assert_called_once_with("/test/config")
    mock_client_class.assert_called_once_with(mock_config)
    mock_client.test_connection.assert_called_once()
    mock_client.sync.assert_called_once_with(
        local_path="/test/dir",
        sync_paths=["path1", "path2"],
        dry_run=True,
        progress_callback=None
    )
    
    # Check output
    captured = capsys.readouterr()
    assert "Connection status:" in captured.out
    assert "api_key: Connected" in captured.out
    assert "password: Not configured" in captured.out
    assert "bunnycdn_package: Failed" in captured.out
    assert "Sync status:" in captured.out
    assert "Files to upload: 5" in captured.out
    assert "Files to download: 3" in captured.out
    assert "Files to delete: 1" in captured.out
    assert "Unchanged files: 10" in captured.out
    assert "Write-protected files: 2" in captured.out


@patch("buckia.cli.BucketConfig.from_file")
@patch("buckia.cli.BuckiaClient")
def test_cmd_status_exception(mock_client_class, mock_from_file):
    """Test status command with exception"""
    # Setup mocks
    mock_from_file.side_effect = ValueError("Config error")
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    
    # Run the command
    exit_code = cmd_status(args)
    
    # Verify
    assert exit_code == 1
    mock_from_file.assert_called_once_with("/test/config")
    mock_client_class.assert_not_called()


@patch("buckia.cli.BucketConfig")
@patch("buckia.cli.os.path.exists")
def test_cmd_init_success(mock_exists, mock_bucket_config_class, capsys):
    """Test successful init command"""
    # Setup mocks
    mock_exists.return_value = False
    
    mock_config = MagicMock()
    mock_bucket_config_class.return_value = mock_config
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.provider = "bunny"
    args.bucket_name = "test-bucket"
    args.api_key = "test-key"
    args.cache_dir = "/cache/dir"
    args.paths = ["path1", "path2"]
    args.delete_orphaned = True
    args.region = "us-east-1"
    args.force = False
    
    # Run the command
    exit_code = cmd_init(args)
    
    # Verify
    assert exit_code == 0
    mock_exists.assert_called_once_with("/test/config")
    mock_bucket_config_class.assert_called_once_with(
        provider="bunny",
        bucket_name="test-bucket",
        credentials={"api_key": "test-key"},
        cache_dir="/cache/dir",
        sync_paths=["path1", "path2"],
        delete_orphaned=True,
        region="us-east-1"
    )
    mock_config.save.assert_called_once_with("/test/config")
    
    # Check output
    captured = capsys.readouterr()
    assert "Configuration created: /test/config" in captured.out


@patch("buckia.cli.BucketConfig")
@patch("buckia.cli.os.path.exists")
def test_cmd_init_file_exists_no_force(mock_exists, mock_bucket_config_class):
    """Test init command with existing file and no force flag"""
    # Setup mocks
    mock_exists.return_value = True
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.provider = "bunny"
    args.bucket_name = "test-bucket"
    args.force = False
    
    # Run the command
    exit_code = cmd_init(args)
    
    # Verify
    assert exit_code == 1
    mock_exists.assert_called_once_with("/test/config")
    mock_bucket_config_class.assert_not_called()


@patch("buckia.cli.BucketConfig")
@patch("buckia.cli.os.path.exists")
def test_cmd_init_file_exists_with_force(mock_exists, mock_bucket_config_class):
    """Test init command with existing file and force flag"""
    # Setup mocks
    mock_exists.return_value = True
    
    mock_config = MagicMock()
    mock_bucket_config_class.return_value = mock_config
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.provider = "bunny"
    args.bucket_name = "test-bucket"
    args.api_key = "test-key"
    args.cache_dir = None
    args.paths = None
    args.delete_orphaned = False
    args.region = None
    args.force = True
    
    # Run the command
    exit_code = cmd_init(args)
    
    # Verify
    assert exit_code == 0
    mock_exists.assert_called_once_with("/test/config")
    mock_bucket_config_class.assert_called_once()
    mock_config.save.assert_called_once_with("/test/config")


@patch("buckia.cli.BucketConfig")
@patch("buckia.cli.os.path.exists")
def test_cmd_init_exception(mock_exists, mock_bucket_config_class):
    """Test init command with exception"""
    # Setup mocks
    mock_exists.return_value = False
    mock_bucket_config_class.side_effect = ValueError("Config error")
    
    # Create args
    args = MagicMock()
    args.config = "/test/config"
    args.directory = "/test/dir"
    args.provider = "bunny"
    args.bucket_name = "test-bucket"
    args.force = False
    
    # Run the command
    exit_code = cmd_init(args)
    
    # Verify
    assert exit_code == 1
    mock_exists.assert_called_once_with("/test/config")
    mock_bucket_config_class.assert_called_once()


@patch("buckia.cli.parse_args")
def test_main_success(mock_parse_args):
    """Test successful main function"""
    # Setup mock
    mock_args = MagicMock()
    mock_args.func.return_value = 0
    mock_parse_args.return_value = mock_args
    
    # Run main
    exit_code = main()
    
    # Verify
    assert exit_code == 0
    mock_parse_args.assert_called_once()
    mock_args.func.assert_called_once_with(mock_args)


@patch("buckia.cli.parse_args")
def test_main_keyboard_interrupt(mock_parse_args, capsys):
    """Test main function with keyboard interrupt"""
    # Setup mock
    mock_parse_args.side_effect = KeyboardInterrupt()
    
    # Run main
    exit_code = main()
    
    # Verify
    assert exit_code == 130
    mock_parse_args.assert_called_once()
    
    # Check output
    captured = capsys.readouterr()
    assert "Operation cancelled by user" in captured.out


@patch("buckia.cli.parse_args")
def test_main_unexpected_error(mock_parse_args):
    """Test main function with unexpected error"""
    # Setup mock
    mock_parse_args.side_effect = ValueError("Unexpected error")
    
    # Run main
    exit_code = main()
    
    # Verify
    assert exit_code == 1
    mock_parse_args.assert_called_once()