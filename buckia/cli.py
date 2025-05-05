#!/usr/bin/env python3
"""
Command-line interface for Buckia
"""

import argparse
import logging
import os
import sys
from typing import List

from .client import BuckiaClient
from .config import BucketConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("buckia.cli")

DEFAULT_CONFIG_FILE = ".buckia"


def progress_callback(current: int, total: int, action: str, path: str) -> None:
    """Progress callback for sync operations"""
    percent = int(current * 100 / total) if total > 0 else 0
    print(f"{action.capitalize()}: {current}/{total} ({percent}%) - {path}")


def cmd_sync(args: argparse.Namespace) -> int:
    """
    Synchronize files with remote storage

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Determine config file
    config_file = args.config
    if not config_file:
        config_file = os.path.join(args.directory, DEFAULT_CONFIG_FILE)

    try:
        # Load configuration
        config = BucketConfig.from_file(config_file)

        # Create client
        client = BuckiaClient(config)

        # Prepare sync parameters
        sync_params = {
            "local_path": args.directory,
            "dry_run": args.dry_run,
            "progress_callback": progress_callback if not args.quiet else None,
        }

        # Add optional parameters if specified
        if args.paths:
            sync_paths: List[str] = args.paths
            sync_params["sync_paths"] = sync_paths

        if args.delete_orphaned is not None:
            sync_params["delete_orphaned"] = args.delete_orphaned

        if args.max_workers:
            sync_params["max_workers"] = args.max_workers

        # Run synchronization
        result = client.sync(**sync_params)

        # Print summary
        if not args.quiet:
            print("\nSync completed")

        # Return success if no failures
        if hasattr(result, "success"):
            return 0 if result.success else 1
        return 0

    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """
    Show status of the synchronization

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Determine config file
    config_file = args.config
    if not config_file:
        config_file = os.path.join(args.directory, DEFAULT_CONFIG_FILE)

    try:
        # Load configuration
        config = BucketConfig.from_file(config_file)

        # Create client
        client = BuckiaClient(config)

        # Test connection
        connection_results = client.test_connection()
        print("Connection status:")
        for method, status in connection_results.items():
            if status is None:
                print(f"  {method}: Not configured")
            else:
                print(f"  {method}: {'Connected' if status else 'Failed'}")

        # Run sync in dry-run mode to get status
        result = client.sync(
            local_path=args.directory,
            sync_paths=args.paths,
            dry_run=True,
            progress_callback=None,
        )

        # Print summary
        print("\nSync status:")
        print(f"  Files to upload: {getattr(result, 'uploaded', 0)}")
        print(f"  Files to download: {getattr(result, 'downloaded', 0)}")
        print(f"  Files to delete: {getattr(result, 'deleted', 0)}")
        print(f"  Unchanged files: {getattr(result, 'unchanged', 0)}")
        print(f"  Write-protected files: {getattr(result, 'protected_skipped', 0)}")

        return 0

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    """
    Initialize a new configuration file

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Determine config file
    config_file = args.config
    if not config_file:
        config_file = os.path.join(args.directory, DEFAULT_CONFIG_FILE)

    # Check if config already exists
    if os.path.exists(config_file) and not args.force:
        logger.error(f"Configuration file already exists: {config_file}")
        logger.error("Use --force to overwrite")
        return 1

    try:
        # Create basic configuration
        config_params = {
            "provider": args.provider,
            "bucket_name": args.bucket_name,
            "credentials": {
                "api_key": args.api_key,
            },
            "sync_paths": args.paths,
            "delete_orphaned": args.delete_orphaned,
            "region": args.region,
        }

        # Remove None values
        config_params = {k: v for k, v in config_params.items() if v is not None}

        config = BucketConfig(**config_params)

        # Save configuration
        config.save(config_file)

        print(f"Configuration created: {config_file}")
        return 0

    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        return 1


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments

    Args:
        args: Command-line arguments to parse (None for sys.argv)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Buckia - Storage bucket synchronization tool"
    )

    # Common arguments
    parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Directory to synchronize (default: current directory)",
    )

    parser.add_argument(
        "-c",
        "--config",
        help=f"Configuration file (default: {DEFAULT_CONFIG_FILE} in directory)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Sync command
    sync_parser = subparsers.add_parser(
        "sync", help="Synchronize files with remote storage"
    )
    sync_parser.add_argument(
        "--paths",
        nargs="+",
        help="Specific paths to synchronize (relative to directory)",
    )

    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    sync_parser.add_argument(
        "--delete-orphaned",
        action="store_true",
        dest="delete_orphaned",
        help="Delete files on remote that don't exist locally",
    )

    sync_parser.add_argument(
        "--no-delete-orphaned",
        action="store_false",
        dest="delete_orphaned",
        help="Don't delete files on remote that don't exist locally",
    )

    sync_parser.add_argument(
        "--max-workers", type=int, help="Maximum number of concurrent operations"
    )

    sync_parser.set_defaults(func=cmd_sync, delete_orphaned=None)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show synchronization status")
    status_parser.add_argument(
        "--paths", nargs="+", help="Specific paths to check (relative to directory)"
    )
    status_parser.set_defaults(func=cmd_status)

    # Init command
    init_parser = subparsers.add_parser("init", help="Create a new configuration file")
    init_parser.add_argument(
        "--provider",
        required=True,
        choices=["bunny", "s3", "linode"],
        help="Storage provider",
    )

    init_parser.add_argument(
        "--bucket-name", required=True, help="Name of the bucket/storage zone"
    )

    init_parser.add_argument("--api-key", help="API key for the storage provider")

    init_parser.add_argument("--region", help="Region for the bucket")

    init_parser.add_argument("--cache-dir", help="Local cache directory")

    init_parser.add_argument(
        "--paths",
        nargs="+",
        help="Specific paths to synchronize (relative to directory)",
    )

    init_parser.add_argument(
        "--delete-orphaned",
        action="store_true",
        help="Delete files on remote that don't exist locally",
    )

    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration file"
    )

    init_parser.set_defaults(func=cmd_init)

    # Parse arguments
    parsed_args = parser.parse_args(args)

    # Set log level based on verbosity
    if parsed_args.verbose:
        logging.getLogger("buckia").setLevel(logging.DEBUG)
    elif parsed_args.quiet:
        logging.getLogger("buckia").setLevel(logging.WARNING)

    # Ensure command is provided
    if not hasattr(parsed_args, "func"):
        parser.print_help()
        sys.exit(1)

    return parsed_args


def main() -> int:
    """
    Main entry point for the command-line interface

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        args = parse_args()
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
