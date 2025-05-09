"""
Backblaze B2 synchronization backend for Buckia
"""

import logging
import os
from typing import Any, Dict

# Import B2 SDK classes
from b2sdk._internal.account_info.in_memory import InMemoryAccountInfo

# Import API and account info from the version-specific modules
from b2sdk.v2.api import B2Api

# Import exceptions - try different locations based on version
try:
    # For newer SDK versions
    from b2sdk._internal.exception import B2Error, FileNotPresent
except ImportError:
    # For older versions
    try:
        from b2sdk.exception import B2Error, FileNotPresent
    except ImportError:
        from b2sdk.v2.exception import B2Error, FileNotPresent

# Import download destination from v1 (available in 2.8.1)

from ..config import BucketConfig

# Import TokenManager for API token management
from ..security import TokenManager
from .base import BaseSync

# Configure logging
logger = logging.getLogger("buckia.b2")


class B2Sync(BaseSync):
    """Synchronization backend for Backblaze B2 storage

    > uv run buckia token set demo_id
    """

    config: BucketConfig
    bucket_name: str
    application_key_id: str
    application_key: str

    def __init__(self, config: dict[str, Any] | BucketConfig):
        """Initialize the Backblaze B2 backend with configuration"""
        super().__init__(config)

        # Extract B2-specific settings
        self.bucket_name = getattr(self.config, "bucket_name", "")

        # First check if application_key_id is provided in provider_settings
        # Check various field names that could contain the application key ID
        self.application_key_id = self.config.get_provider_setting("application_key_id")
        if not self.application_key_id:
            self.application_key_id = self.config.get_provider_setting("token_id")

        # If not provided in config, try to get from TokenManager
        if not self.application_key_id:
            try:
                # Get bucket context name (default to provider name)
                context = getattr(self.config, "token_context", None) or "b2"
                token_manager = TokenManager(namespace="buckia")
                token_id = token_manager.get_token_id(context)
                if token_id:
                    logger.info(
                        f"Using API key ID from token manager for bucket context: {context}"
                    )
                    self.application_key_id = token_id
                token = token_manager.get_token(context)
                if token:
                    logger.info(f"Using API key from token manager for bucket context: {context}")
                    self.application_key = token
            except Exception as e:
                logger.warning(f"Failed to get token from keyring: {e}")
        # Check for various field names that could contain the application key
        self.application_key = self.config.get_provider_setting("token", self.application_key)
        if not self.application_key:
            self.application_key = self.config.get_provider_setting(
                "application_key", self.application_key
            )
        self.hostname = self.config.get_provider_setting(
            "hostname", "s3.us-west-001.backblazeb2.com"
        )
        self.storage_region = getattr(self.config, "region", "")
        self.authenticated_cdn_endpoint = self.config.get_provider_setting(
            "authenticated_cdn_endpoint"
        )
        self.cdn_url = self.config.get_provider_setting("cdn_url")
        self.pull_zone_name = self.config.get_provider_setting("pull_zone_name")

        # Initialize B2 SDK objects
        self.info = InMemoryAccountInfo()
        self.b2_api = B2Api(self.info)
        self.bucket = None
        self.authorized = False

    def connect(self) -> bool:
        """Establish connection to Backblaze B2"""
        # First check if we have the required credentials
        if not self.application_key_id:
            logger.error("B2 connection failed: Missing application_key_id (token_id)")
            logger.error(
                "Please set application_key_id in provider_settings or configure token_id in TokenManager"
            )
            return False

        if not self.application_key:
            logger.error("B2 connection failed: Missing application_key (token)")
            logger.error(
                "Please set application_key in provider_settings or configure token in TokenManager"
            )
            return False

        if not self.bucket_name:
            logger.error("B2 connection failed: Missing bucket_name")
            logger.error("Please set bucket_name in your configuration")
            return False

        try:
            # Authorize account
            logger.debug(
                f"Authorizing B2 account with application_key_id: {self.application_key_id[:4]}...{self.application_key_id[-4:] if len(self.application_key_id) > 8 else ''}"
            )
            self.b2_api.authorize_account(
                "production", self.application_key_id, self.application_key
            )
            self.authorized = True
            logger.debug("B2 account authorization successful")

            # Get the bucket
            logger.debug(f"Retrieving bucket: {self.bucket_name}")
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            logger.info(f"Connected to Backblaze B2 bucket: {self.bucket_name}")
            return True
        except B2Error as e:
            # Extract error details from B2Error
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            # Provide more specific error messages based on error code/status
            if "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 authorization failed: Invalid credentials (code: {error_code})")
                logger.error("Check your application_key_id and application_key")
            elif "not_found" in str(e).lower() or error_status == 404:
                logger.error(f"B2 bucket not found: {self.bucket_name}")
                logger.error(
                    "Verify that the bucket exists and that your application key has access to it"
                )
            elif "bad_request" in str(e).lower() or error_status == 400:
                logger.error(f"B2 bad request: {e}")
                logger.error("Check your request parameters and B2 configuration")
            else:
                logger.error(f"B2 API error (code: {error_code}, status: {error_status}): {e}")

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details: {repr(e)}")
            return False
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error connecting to Backblaze B2 ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Backblaze B2 and provide detailed diagnostic information

        Returns:
            Dictionary with test results and error information
        """
        results = {
            "b2_auth": False,
            "bucket_access": False,
            "errors": [],
            "warnings": [],
            "success": False,
        }

        # Validate required parameters
        if not self.application_key_id:
            results["errors"].append("Missing application_key_id (token_id)")
            results["errors"].append(
                "Please set application_key_id in provider_settings or configure token_id in TokenManager"
            )
            return results

        if not self.application_key:
            results["errors"].append("Missing application_key (token)")
            results["errors"].append(
                "Please set application_key in provider_settings or configure token in TokenManager"
            )
            return results

        if not self.bucket_name:
            results["errors"].append("Missing bucket_name parameter")
            results["errors"].append("Please set bucket_name in your configuration")
            return results

        # Test B2 authorization
        try:
            logger.debug(
                f"Testing B2 authorization with key ID: {self.application_key_id[:4]}...{self.application_key_id[-4:] if len(self.application_key_id) > 8 else ''}"
            )
            self.b2_api.authorize_account(
                "production", self.application_key_id, self.application_key
            )
            results["b2_auth"] = True
            logger.debug("B2 authorization test successful")
        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            error_message = f"B2 authorization failed (code: {error_code}, status: {error_status})"
            results["errors"].append(error_message)

            if "unauthorized" in str(e).lower() or error_status == 401:
                results["errors"].append(
                    "Invalid credentials. Check your application_key_id and application_key"
                )
            elif "bad_request" in str(e).lower() or error_status == 400:
                results["errors"].append(f"Bad request: {e}")
            else:
                results["errors"].append(f"B2 API error: {e}")

            logger.error(f"B2 authorization test failed: {error_message}")
            return results
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"Unexpected error during B2 authorization ({error_type}): {e}"
            results["errors"].append(error_message)
            logger.error(error_message)
            return results

        # Test bucket access
        try:
            logger.debug(f"Testing access to bucket: {self.bucket_name}")
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            results["bucket_access"] = True
            logger.debug("B2 bucket access test successful")
        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            error_message = f"B2 bucket access failed (code: {error_code}, status: {error_status})"
            results["errors"].append(error_message)

            if "not_found" in str(e).lower() or error_status == 404:
                results["errors"].append(f"Bucket '{self.bucket_name}' not found or not accessible")
                results["errors"].append(
                    "Verify that the bucket exists and that your application key has access to it"
                )
            else:
                results["errors"].append(f"B2 API error: {e}")

            logger.error(f"B2 bucket access test failed: {error_message}")
        except Exception as e:
            error_type = type(e).__name__
            error_message = f"Unexpected error accessing bucket ({error_type}): {e}"
            results["errors"].append(error_message)
            logger.error(error_message)

        # Set overall success flag
        results["success"] = results["b2_auth"] and results["bucket_access"]

        # Add any hints or warnings
        if results["b2_auth"] and not results["bucket_access"]:
            results["warnings"].append(
                "Your credentials are valid but you don't have access to the specified bucket"
            )
            results["warnings"].append(
                "Check that the bucket name is correct and that your application key has access to it"
            )

        return results

    def list_remote_files(self, path: str | None = None) -> Dict[str, Dict[str, Any]]:
        """
        List files in B2 bucket

        Args:
            path: Optional path prefix to list files from

        Returns:
            Dictionary mapping file paths to metadata
        """
        remote_files = {}
        operation = "list_files"

        # Connect if not already connected
        if not self.authorized:
            logger.debug(f"Not authorized, attempting to connect before {operation}")
            if not self.connect():
                logger.error(f"Cannot {operation}: Failed to establish connection to B2")
                return remote_files

        try:
            # Normalize path for use as prefix
            prefix = path.rstrip("/") + "/" if path else ""
            logger.debug(f"Listing B2 files with prefix: '{prefix}'")

            # List all file versions in the bucket with the given prefix
            file_count = 0
            for file_version, _ in self.bucket.ls(prefix, latest_only=True):
                # Skip folders (they are represented by zero-length files with names ending in '/')
                if file_version.file_name.endswith("/"):
                    continue

                # For B2, we need to remove the prefix to make the path relative
                remote_path = file_version.file_name
                file_count += 1

                # Add file metadata
                remote_files[remote_path] = {
                    "ObjectName": os.path.basename(remote_path),
                    "IsDirectory": False,
                    "Path": remote_path,
                    "Size": file_version.size,
                    "Checksum": file_version.content_sha1,
                    "LastModified": file_version.upload_timestamp,
                    "FileId": file_version.id_,
                }

            logger.debug(f"Listed {file_count} files from B2 bucket: {self.bucket_name}")

        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            if "not_found" in str(e).lower() or error_status == 404:
                logger.error(f"B2 {operation} failed: Bucket or path not found")
                logger.error(f"Bucket: {self.bucket_name}, Path prefix: '{prefix}'")
            elif "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 {operation} failed: Unauthorized access")
                logger.error("Your application key may not have permission to list files")
            else:
                logger.error(
                    f"B2 API error during {operation} (code: {error_code}, status: {error_status}): {e}"
                )

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details during {operation}: {repr(e)}")

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error during B2 {operation} ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")

        return remote_files

    def upload_file(self, local_file_path: str, remote_path: str) -> bool:
        """
        Upload a file to B2

        Args:
            local_file_path: Path to local file to upload
            remote_path: Destination path on B2

        Returns:
            True if upload successful, False otherwise
        """
        operation = "upload_file"

        # Check if local file exists
        if not os.path.exists(local_file_path):
            logger.error(f"B2 {operation} failed: Local file not found: {local_file_path}")
            return False

        # Check if local file is readable
        if not os.access(local_file_path, os.R_OK):
            logger.error(f"B2 {operation} failed: Local file not readable: {local_file_path}")
            logger.error("Check file permissions")
            return False

        # Connect if not already connected
        if not self.authorized:
            logger.debug(f"Not authorized, attempting to connect before {operation}")
            if not self.connect():
                logger.error(f"Cannot {operation}: Failed to establish connection to B2")
                return False

        try:
            # Normalize remote path (B2 doesn't like leading slashes)
            remote_path = remote_path.lstrip("/")

            # Get file info
            file_size = os.path.getsize(local_file_path)
            logger.debug(
                f"Uploading file: {local_file_path} ({file_size} bytes) to B2 path: {remote_path}"
            )

            # For small files, use upload_bytes
            if file_size < 5 * 1024 * 1024:  # 5 MB
                logger.debug(f"Using upload_bytes for small file: {file_size} bytes")
                with open(local_file_path, "rb") as f:
                    file_data = f.read()
                self.bucket.upload_bytes(
                    file_data, remote_path, file_info={"mode": "uploaded_by_buckia"}
                )
            else:
                # For larger files, use upload_local_file
                logger.debug(f"Using upload_local_file for large file: {file_size} bytes")
                self.bucket.upload_local_file(
                    local_file_path, remote_path, file_info={"mode": "uploaded_by_buckia"}
                )

            logger.info(f"Successfully uploaded: {remote_path}")
            return True

        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            if "capacity" in str(e).lower() or "storage_cap" in str(e).lower():
                logger.error(f"B2 {operation} failed: Storage capacity exceeded")
                logger.error(f"File: {local_file_path} ({file_size} bytes)")
            elif "file_already_exists" in str(e).lower():
                logger.error(
                    f"B2 {operation} failed: File already exists and cannot be overwritten"
                )
                logger.error(f"Remote path: {remote_path}")
                logger.error("You may need to delete the existing file first")
            elif "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 {operation} failed: Unauthorized access")
                logger.error("Your application key may not have write permission")
            elif "request_timeout" in str(e).lower() or "timeout" in str(e).lower():
                logger.error(f"B2 {operation} failed: Request timed out")
                logger.error(f"File: {local_file_path} ({file_size} bytes)")
                logger.error("Consider uploading smaller files or improving network connection")
            else:
                logger.error(
                    f"B2 API error during {operation} (code: {error_code}, status: {error_status}): {e}"
                )

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details during {operation}: {repr(e)}")
            return False

        except IOError as e:
            logger.error(f"IO error during B2 {operation}: {e}")
            logger.error(f"File: {local_file_path}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error during B2 {operation} ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

    def download_file(self, remote_path: str, local_file_path: str) -> bool:
        """
        Download a file from B2

        Note: This method has compatibility issues with B2 SDK 2.8.1.
        The download functionality needs to be revisited and fixed in a future update.
        Currently, the integration test for this functionality is using a placeholder.

        Args:
            remote_path: Path to file on B2
            local_file_path: Path to save file locally

        Returns:
            True if download successful, False otherwise
        """
        operation = "download_file"

        # Connect if not already connected
        if not self.authorized:
            logger.debug(f"Not authorized, attempting to connect before {operation}")
            if not self.connect():
                logger.error(f"Cannot {operation}: Failed to establish connection to B2")
                return False

        # Check if local directory is writable
        try:
            local_dir = os.path.dirname(local_file_path)
            if not os.path.exists(local_dir):
                logger.debug(f"Creating directory: {local_dir}")
                os.makedirs(local_dir, exist_ok=True)
            elif not os.access(local_dir, os.W_OK):
                logger.error(f"B2 {operation} failed: Local directory not writable: {local_dir}")
                logger.error("Check directory permissions")
                return False
        except Exception as e:
            logger.error(f"B2 {operation} failed: Cannot create directory: {local_dir}")
            logger.error(f"Error: {e}")
            return False

        try:
            # Normalize remote path (B2 doesn't like leading slashes)
            remote_path = remote_path.lstrip("/")
            logger.debug(
                f"Downloading file from B2 path: {remote_path} to local path: {local_file_path}"
            )

            # Try to get file info first to verify it exists
            try:
                file_info = self.bucket.get_file_info_by_name(remote_path)
                logger.debug(
                    f"Found file to download: {remote_path}, id: {file_info.id_}, size: {file_info.size}"
                )
            except FileNotPresent:
                logger.error(f"B2 {operation} failed: File not found on B2: {remote_path}")
                return False

            # Create the destination directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(local_file_path)), exist_ok=True)

            # For B2 v2 SDK, download file directly using download_by_name
            try:
                # Get file ID first
                file_info = self.bucket.get_file_info_by_name(remote_path)
                file_id = file_info.id_

                # Use the B2 API to download the file directly to local_file_path
                self.b2_api.download_file_by_id(file_id, local_file_path)
            except Exception as e:
                logger.error(f"B2 download error: {e}")
                return False

            # Verify download was successful by checking if file exists
            if not os.path.exists(local_file_path):
                logger.error(f"B2 {operation} failed: Downloaded file not found: {local_file_path}")
                return False

            # Verify file is not empty
            if os.path.getsize(local_file_path) == 0:
                logger.error(f"B2 {operation} failed: Downloaded file is empty: {local_file_path}")
                # Remove empty file
                os.unlink(local_file_path)
                return False

            logger.info(f"Successfully downloaded: {remote_path}")
            return True

        except FileNotPresent:
            logger.error(f"B2 {operation} failed: File not found on B2: {remote_path}")
            logger.error(f"Bucket: {self.bucket_name}")
            return False

        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            if "not_found" in str(e).lower() or error_status == 404:
                logger.error(f"B2 {operation} failed: File not found: {remote_path}")
                logger.error(f"Bucket: {self.bucket_name}")
            elif "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 {operation} failed: Unauthorized access")
                logger.error("Your application key may not have read permission")
            elif "request_timeout" in str(e).lower() or "timeout" in str(e).lower():
                logger.error(f"B2 {operation} failed: Request timed out")
                logger.error(f"Remote path: {remote_path}")
                logger.error("The file may be too large or network connection too slow")
            else:
                logger.error(
                    f"B2 API error during {operation} (code: {error_code}, status: {error_status}): {e}"
                )

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details during {operation}: {repr(e)}")
            return False

        except IOError as e:
            logger.error(f"IO error during B2 {operation}: {e}")
            logger.error(f"Local file: {local_file_path}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error during B2 {operation} ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """
        Delete a file from B2

        Args:
            remote_path: Path to file on B2 to delete

        Returns:
            True if deletion successful or file doesn't exist, False on error
        """
        operation = "delete_file"

        # Connect if not already connected
        if not self.authorized:
            logger.debug(f"Not authorized, attempting to connect before {operation}")
            if not self.connect():
                logger.error(f"Cannot {operation}: Failed to establish connection to B2")
                return False

        try:
            # Normalize remote path (B2 doesn't like leading slashes)
            remote_path = remote_path.lstrip("/")
            logger.debug(f"Attempting to delete file: {remote_path}")

            # Check if file exists
            file_version = None
            try:
                file_info = self.bucket.get_file_info_by_name(remote_path)
                file_version = file_info.id_
                logger.debug(f"Found file to delete: {remote_path}, version: {file_version}")
            except FileNotPresent:
                logger.warning(f"File not found for deletion: {remote_path}")
                return True  # File doesn't exist, so deletion "succeeded"

            # Delete the file
            if file_version:
                logger.debug(f"Deleting file version: {file_version}")
                self.bucket.delete_file_version(file_version, remote_path)

            logger.info(f"Successfully deleted: {remote_path}")
            return True

        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            if "not_found" in str(e).lower() or error_status == 404:
                logger.warning(f"B2 {operation}: File not found or already deleted: {remote_path}")
                return True  # Consider this a success since the file doesn't exist
            elif "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 {operation} failed: Unauthorized access")
                logger.error("Your application key may not have delete permission")
            else:
                logger.error(
                    f"B2 API error during {operation} (code: {error_code}, status: {error_status}): {e}"
                )

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details during {operation}: {repr(e)}")
            return False

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error during B2 {operation} ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")
            return False

    def get_public_url(self, remote_path: str) -> str:
        """
        Get a public URL for a file in B2

        Args:
            remote_path: Path to file on B2

        Returns:
            URL to access the file, or empty string on error
        """
        operation = "get_public_url"

        # Connect if not already connected
        if not self.authorized:
            logger.debug(f"Not authorized, attempting to connect before {operation}")
            if not self.connect():
                logger.error(f"Cannot {operation}: Failed to establish connection to B2")
                return ""

        try:
            # Normalize remote path (B2 doesn't like leading slashes)
            remote_path = remote_path.lstrip("/")
            logger.debug(f"Getting public URL for file: {remote_path}")

            # Get download URL from B2
            download_url = self.bucket.get_download_url(remote_path)
            logger.debug(f"Generated public URL: {download_url}")
            return download_url

        except B2Error as e:
            error_code = getattr(e, "code", "unknown")
            error_status = getattr(e, "status", 0)

            if "not_found" in str(e).lower() or error_status == 404:
                logger.error(f"B2 {operation} failed: File not found: {remote_path}")
            elif "unauthorized" in str(e).lower() or error_status == 401:
                logger.error(f"B2 {operation} failed: Unauthorized access")
            else:
                logger.error(
                    f"B2 API error during {operation} (code: {error_code}, status: {error_status}): {e}"
                )

            # Log the full error details at debug level for troubleshooting
            logger.debug(f"B2 error details during {operation}: {repr(e)}")
            return ""

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Unexpected error during B2 {operation} ({error_type}): {e}")
            logger.debug(f"Full error details: {repr(e)}")
            return ""
