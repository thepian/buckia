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

# Import TokenManager for API token management
from .security import TokenManager

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
    # Check for token_context parameter
    if args.token_context:
        try:
            token_manager = TokenManager(namespace="buckia")
            token = token_manager.get_token(args.token_context)
            if token:
                logger.info(f"Using token from keyring for bucket context: {args.token_context}")
                # We'll use this later when loading the config
            else:
                logger.error(f"No token found for bucket context: {args.token_context}")
                return 1
        except Exception as e:
            logger.error(f"Error retrieving token: {str(e)}")
            return 1

    # Determine config file
    config_file = args.config
    if not config_file:
        config_file = os.path.join(args.directory, DEFAULT_CONFIG_FILE)

    try:
        # Load configuration
        config = BucketConfig.from_file(config_file)

        # If token_context is specified, override the token_context in config
        if args.token_context:
            config.token_context = args.token_context

            # If we already retrieved a token above, set it directly in credentials
            if "token" in locals() and token:
                if not config.credentials:
                    config.credentials = {}
                config.credentials["api_key"] = token

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


def cmd_token(args: argparse.Namespace) -> int:
    """
    Manage API tokens securely

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # TokenManager is now always available as keyring is a dependency

    token_manager = TokenManager(namespace="buckia")

    # If no subcommand is specified, show help
    if not args.token_action:
        print("Buckia Token Management")
        print("\nUsage:")
        print("  token set <context> [--token VALUE]  Save an API token for a bucket context")
        print(
            "  token get <context>                  Retrieve an API token (requires authentication)"
        )
        print("  token list                           List available bucket contexts with tokens")
        print("  token delete <context>               Delete an API token")
        print("\nExamples:")
        print("  buckia token set bunny")
        print("  buckia token get bunny")
        print("  buckia token list")
        print("  buckia token delete bunny")
        print("\nBucket Contexts:")
        print("  test      - BunnyCDN Storage API key")
        print("  long_term - Backblaze B2 API key")
        print("  other     - Linode Object Storage key")
        print("  <custom>  - Any custom bucket context name")
        return 0

    try:
        if args.token_action == "set":
            # Get token from args or prompt
            token = args.token
            if not token:
                import getpass

                token = getpass.getpass(f"Enter API token for bucket context {args.context}: ")

            # Save token
            success = token_manager.save_token(args.context, token)
            if success:
                print(f"Token saved for bucket context: {args.context}")
                return 0
            else:
                logger.error(f"Failed to save token for bucket context: {args.context}")
                return 1

        elif args.token_action == "get":
            # Retrieve token
            token = token_manager.get_token(args.context)
            if token:
                print(token)
                return 0
            else:
                logger.error(
                    f"No token found for bucket context: {args.context} or authentication failed"
                )
                return 1

        elif args.token_action == "list":
            # List available tokens
            bucket_contexts = token_manager.list_bucket_contexts()
            if bucket_contexts:
                print("Available bucket contexts with tokens:")
                for context in bucket_contexts:
                    print(f"  - {context}")
            else:
                print("No tokens found")
            return 0

        elif args.token_action == "delete":
            # Delete token
            success = token_manager.delete_token(args.context)
            if success:
                print(f"Token deleted for bucket context: {args.context}")
                return 0
            else:
                logger.error(f"Failed to delete token for bucket context: {args.context}")
                return 1

        else:
            logger.error(f"Unknown token action: {args.token_action}")
            return 1

    except Exception as e:
        logger.error(f"Error managing tokens: {str(e)}")
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
            "sync_paths": args.paths,
            "delete_orphaned": args.delete_orphaned,
            "region": args.region,
            "token_context": args.token_context,
        }

        # Only add credentials if API key is provided
        if args.api_key:
            config_params["credentials"] = {
                "api_key": args.api_key,
            }
        elif args.token_context:
            # If token_context is specified but no API key, just reference the token
            # The actual token will be retrieved from keyring when needed
            logger.info(
                f"Configuration will use token from keyring for bucket context: {args.token_context}"
            )

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


def cmd_pdf(args: argparse.Namespace) -> int:
    """
    Render HTML to PDF and upload to bucket

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Check if subcommand is provided
    if not hasattr(args, "pdf_action") or not args.pdf_action:
        print("Buckia PDF Management")
        print("\nUsage:")
        print("  pdf render <html-file> <bucket-name> <unguessable-id> <pdf-filename>")
        print("\nExample:")
        print(
            "  buckia pdf render whitepaper.html thepia-cdn a7f3c8e9-2d4b-4c1a-9e8f-1b2c3d4e5f6a hidden-cost-brief"
        )
        return 0

    if args.pdf_action == "render":
        try:
            # Import PDF module (may fail if WeasyPrint not installed)
            from .pdf import render_pdf_command

            # Determine config file
            config_file = args.config
            if not config_file:
                config_file = os.path.join(args.directory, DEFAULT_CONFIG_FILE)

            # Render PDF
            result = render_pdf_command(
                html_file_path=args.html_file,
                bucket_name=args.bucket_name,
                unguessable_id=args.unguessable_id,
                pdf_filename=args.pdf_filename,
                config_file=config_file,
                local_only=getattr(args, "local_only", False),
                output_dir=getattr(args, "output_dir", None),
                css_override=getattr(args, "css_override", None),
            )

            # Print results
            if not args.quiet:
                print(f"PDF rendered successfully:")
                print(f"  Local file: {result['local_path']}")
                print(f"  Size: {result['size_bytes'] / 1024:.1f} KB")

                # Only check upload status if not in local-only mode
                if not getattr(args, "local_only", False):
                    if result["upload_success"]:
                        print(f"  Uploaded to: {result['remote_path']}")
                        print(f"  Public URL: {result['url']}")
                    else:
                        print(f"  Upload failed: {result.get('error', 'Unknown error')}")
                        return 1
                else:
                    print("  Local-only mode: No upload attempted")

            return 0

        except ImportError as e:
            logger.error("WeasyPrint not available. Install with: pip install buckia[pdf]")
            return 1
        except Exception as e:
            logger.error(f"Error rendering PDF: {str(e)}")
            return 1
    else:
        logger.error(f"Unknown PDF action: {args.pdf_action}")
        return 1


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command-line arguments

    Args:
        args: Command-line arguments to parse (None for sys.argv)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Buckia - Storage bucket synchronization tool")

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

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Token command
    token_parser = subparsers.add_parser("token", help="Manage API tokens securely")
    token_subparsers = token_parser.add_subparsers(dest="token_action")

    # Token set command
    set_parser = token_subparsers.add_parser("set", help="Save an API token")
    set_parser.add_argument("context", help="Bucket context name (e.g., 'bunny', 's3')")
    set_parser.add_argument("--token", help="Token value (omit to enter securely)")

    # Token get command
    get_parser = token_subparsers.add_parser("get", help="Retrieve an API token")
    get_parser.add_argument("context", help="Bucket context to retrieve token for")

    # Token list command
    token_subparsers.add_parser("list", help="List available bucket contexts with tokens")

    # Token delete command
    delete_parser = token_subparsers.add_parser("delete", help="Delete an API token")
    delete_parser.add_argument("context", help="Bucket context to delete token for")

    token_parser.set_defaults(func=cmd_token)

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize files with remote storage")
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

    sync_parser.add_argument(
        "--token-context", help="Name of bucket context to use for token retrieval"
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

    init_parser.add_argument("--bucket-name", required=True, help="Name of the bucket/storage zone")

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
        "--token-context",
        help="Name of bucket context for token retrieval (defaults to provider name)",
    )

    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing configuration file"
    )

    init_parser.set_defaults(func=cmd_init)

    # PDF command
    pdf_parser = subparsers.add_parser("pdf", help="Render HTML to PDF and upload to bucket")
    pdf_subparsers = pdf_parser.add_subparsers(dest="pdf_action", help="PDF action to execute")

    # PDF render command
    render_parser = pdf_subparsers.add_parser("render", help="Render HTML file or URL to PDF")
    render_parser.add_argument(
        "html_file", help="Path to HTML file to render OR URL to fetch HTML from"
    )
    render_parser.add_argument("bucket_name", help="Name of bucket configuration to use")
    render_parser.add_argument("unguessable_id", help="Unique identifier for PDF path")
    render_parser.add_argument(
        "pdf_filename", help="Name for output PDF file (without .pdf extension)"
    )
    render_parser.add_argument(
        "--local-only", action="store_true", help="Generate PDF locally without uploading to bucket"
    )
    render_parser.add_argument(
        "--output-dir",
        help="Directory to save PDF when using --local-only (default: current directory)",
    )
    render_parser.add_argument(
        "--css-override",
        help="Path to additional CSS file to inject into HTML before PDF generation",
    )

    pdf_parser.set_defaults(func=cmd_pdf)

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
