"""
Bunny.net synchronization backend for Buckia
"""

import json
import logging
import os

# from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import requests

from .base import BaseSync

# Configure logging
logger = logging.getLogger("buckia.bunny")


class BunnySync(BaseSync):
    """Synchronization backend for Bunny.net storage"""

    def __init__(self, config):
        """Initialize the Bunny.net backend with configuration"""
        super().__init__(config)

        # Extract Bunny-specific settings
        self.storage_zone_name = getattr(self.config, "bucket_name", None)
        self.api_key = self.config.get_credential("api_key")
        self.storage_api_key = self.config.get_credential("storage_api_key")
        self.password = self.config.get_credential("password")
        self.hostname = self.config.get_provider_setting(
            "hostname", "storage.bunnycdn.com"
        )
        self.storage_region = getattr(self.config, "region", "")
        self.authenticated_cdn_endpoint = self.config.get_provider_setting(
            "authenticated_cdn_endpoint"
        )
        self.cdn_url = self.config.get_provider_setting("cdn_url")
        self.pull_zone_name = self.config.get_provider_setting("pull_zone_name")

        # Initialize session
        self.session = requests.Session()
        # Use storage_api_key for storage operations if available, otherwise fall back to api_key
        if self.storage_api_key:
            self.session.headers.update(
                {"AccessKey": self.storage_api_key, "Accept": "application/json"}
            )
        elif self.api_key:
            self.session.headers.update(
                {"AccessKey": self.api_key, "Accept": "application/json"}
            )

        # Always initialize bunnycdnpython client if available
        self.bunny_client = None

        # Try to import bunnycdnpython package
        try:
            # Import from bundled copy or try system installation
            try:
                from .bunnycdn.CDN import CDN  # type: ignore
                from .bunnycdn.Storage import Storage  # type: ignore

                use_bundled = True
            except ImportError:
                # Try system installation
                from BunnyCDN.CDN import CDN  # type: ignore
                from BunnyCDN.Storage import Storage  # type: ignore

                use_bundled = False

            logger.info(
                f"Using {'bundled' if use_bundled else 'system'} bunnycdnpython package"
            )

            if self.storage_api_key:
                # Initialize Storage with the correct parameter order
                storage_region = self.storage_region if self.storage_region else ""
                self.bunny_client = Storage(
                    self.storage_api_key, self.storage_zone_name, storage_region
                )
                logger.debug("Initialized bunnycdnpython client")
            else:
                logger.warning(
                    "storage_api_key not provided, cannot use bunnycdnpython package"
                )

        except ImportError:
            logger.warning(
                "bunnycdnpython package not available, falling back to direct API calls"
            )

        except Exception as e:
            logger.error(f"Failed to initialize bunnycdnpython client: {str(e)}")

    def connect(self) -> bool:
        """Establish connection to Bunny.net storage"""
        try:
            # Test API key connection
            if self.bunny_client:
                # Test using bunnycdnpython client
                try:
                    self.bunny_client.GetStoragedObjectsList()
                    logger.debug(
                        "Successfully connected to Bunny.net API using bunnycdnpython"
                    )
                    return True
                except Exception as e:
                    logger.error(f"bunnycdnpython connection error: {str(e)}")
                    # Fall back to direct API

            # Test using direct API call
            url = f"{self.storage_api_url}/{self.storage_zone_name}/"
            response = self.session.get(url)

            if response.status_code == 401:
                logger.error("Authentication failed: Invalid API key")
                return False
            elif response.status_code == 404:
                logger.error(f"Storage zone '{self.storage_zone_name}' not found")
                return False
            elif response.status_code != 200:
                logger.error(
                    f"Failed to connect to Bunny.net: {response.status_code} {response.text}"
                )
                return False

            logger.info("Successfully connected to Bunny.net API using API key")
            return True

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    def test_connection(self) -> Dict[str, bool]:
        """Test connection to Bunny.net using available authentication methods"""
        results: Dict[str, bool] = {
            "api_key": False,
            "password": False if self.password else False,
            "bunnycdn_package": False if self.bunny_client else False,
        }

        # Test API key connection
        try:
            url = f"{self.storage_api_url}/{self.storage_zone_name}/"
            logger.info(f"API call to {url}")

            # Create headers with the storage_api_key for the storage API test
            headers = {
                "AccessKey": (
                    self.storage_api_key if self.storage_api_key else self.api_key
                ),
                "Accept": "application/json",
            }

            # Use requests directly with the proper headers instead of self.session
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                results["api_key"] = True
        except Exception as e:
            logger.error(f"API key connection test failed: {str(e)}")

        # Test password connection if configured
        if self.password and self.authenticated_cdn_endpoint:
            try:
                url = f"{self.authenticated_cdn_endpoint}/"

                # Don't use the session with API key, create a direct request
                response = requests.get(url, timeout=10)

                if response.status_code in (
                    200,
                    404,
                ):  # 404 acceptable if directory empty
                    results["password"] = True
            except Exception as e:
                logger.error(f"Password connection test failed: {str(e)}")

        # Test bunnycdnpython connection if configured
        if self.bunny_client:
            try:
                self.bunny_client.GetStoragedObjectsList()
                results["bunnycdn_package"] = True
            except Exception as e:
                logger.error(f"bunnycdnpython connection test failed: {str(e)}")

        return results

    def list_remote_files(self, path: str | None = None) -> Dict[str, Dict[str, Any]]:
        """List files on Bunny.net storage"""
        remote_files: Dict[str, Dict[str, Any]] = {}

        # Ensure path is properly formatted
        if path is not None:
            path = str(path).strip()

        # Use bunnycdnpython if available
        if self.bunny_client:
            try:
                # Handle potential empty string issues by using a try-except block
                try:
                    files = self.bunny_client.GetStoragedObjectsList(path)

                    # Handle None values in files list
                    if files is None:
                        logger.warning(
                            f"GetStoragedObjectsList returned None for path '{path}'"
                        )
                        files = []

                    for item in files:
                        # Skip None items
                        if item is None:
                            continue

                        object_name: str | None = None

                        # Handle items that are strings (not dictionaries)
                        if isinstance(item, str):
                            # For string items, create a simple metadata dict
                            is_dir = item.endswith("/")
                            object_name = item.rstrip("/")

                            if is_dir:
                                # Recursively get files from subdirectory
                                subdir_path = (
                                    f"{path}/{object_name}" if path else object_name
                                )
                                subdirectory_files = self.list_remote_files(subdir_path)
                                remote_files.update(subdirectory_files)
                            else:
                                file_path: str = (
                                    f"{path}/{object_name}" if path else object_name
                                )
                                # Create basic metadata from the string
                                remote_files[file_path] = {
                                    "ObjectName": object_name,
                                    "IsDirectory": False,
                                    "Path": file_path,
                                }
                        else:
                            # Handle dictionary items - checking for different field names
                            object_name = None
                            is_directory = False

                            # Try different field names that might contain the name
                            if "ObjectName" in item:
                                object_name = item["ObjectName"]
                                is_directory = item.get("IsDirectory", False)
                            elif "Folder_Name" in item:
                                object_name = item["Folder_Name"]
                                is_directory = (
                                    True  # If it has Folder_Name, it's a directory
                                )
                            elif "File_Name" in item:
                                object_name = item["File_Name"]
                                is_directory = False

                            if object_name:
                                if is_directory:
                                    # Recursively get files from subdirectory
                                    subdir_path = (
                                        f"{path}/{object_name}" if path else object_name
                                    )
                                    subdirectory_files = self.list_remote_files(
                                        subdir_path
                                    )
                                    remote_files.update(subdirectory_files)
                                else:
                                    file_path = (
                                        f"{path}/{object_name}" if path else object_name
                                    )
                                    remote_files[file_path] = item
                            else:
                                logger.warning(
                                    f"Skipping item with unknown name format: {item}"
                                )
                except Exception as e:
                    logger.error(
                        f"Error with bunnycdnpython GetStoragedObjectsList for path '{path}': {str(e)}"
                    )
                    # We'll fall back to direct API
                else:
                    return remote_files
            except Exception as e:
                logger.error(f"Error listing files with bunnycdnpython: {str(e)}")
                # Fall back to direct API

        # Use direct API calls
        # Ensure no double slashes in URL
        clean_path = path.strip("/") if path else ""
        url_path = f"{clean_path}/" if clean_path else ""
        url = f"{self.storage_api_url}/{self.storage_zone_name}/{url_path}"

        try:
            response = self.session.get(url)

            if response.status_code != 200:
                logger.error(
                    f"Failed to list remote files: {response.status_code} {response.text}"
                )
                return remote_files

            items = response.json()

            for item in items:
                if item is None:
                    continue

                # Handle dictionary items - checking for different field names
                object_name = None
                is_directory = False

                # Try different field names that might contain the name
                if "ObjectName" in item:
                    object_name = item["ObjectName"]
                    is_directory = item.get("IsDirectory", False)
                elif "Folder_Name" in item:
                    object_name = item["Folder_Name"]
                    is_directory = True  # If it has Folder_Name, it's a directory
                elif "File_Name" in item:
                    object_name = item["File_Name"]
                    is_directory = False

                if object_name:
                    if is_directory:
                        # Recursively get files from subdirectory
                        subdir_path = f"{path}/{object_name}" if path else object_name
                        subdirectory_files = self.list_remote_files(subdir_path)
                        remote_files.update(subdirectory_files)
                    else:
                        file_path = f"{path}/{object_name}" if path else object_name
                        remote_files[file_path] = item
                else:
                    logger.warning(f"Skipping item with unknown name format: {item}")

        except requests.RequestException as e:
            logger.error(f"Error listing remote files: {str(e)}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON response when listing remote files")

        return remote_files

    def upload_file(self, local_file_path: str, remote_path: str) -> bool:
        """Upload a file to Bunny.net storage"""
        # Check if file exists
        if not os.path.exists(local_file_path):
            logger.error(f"Local file not found: {local_file_path}")
            return False

        # Use bunnycdnpython if available
        if self.bunny_client:
            try:
                # Extract filename and directory path for PutFile
                file_name = os.path.basename(local_file_path)
                local_directory = os.path.dirname(local_file_path)

                # The remote_path parameter in PutFile should not have a leading slash
                storage_path = remote_path.lstrip("/")

                # Call PutFile with the correct parameter order based on bunnycdnpython API
                self.bunny_client.PutFile(file_name, storage_path, local_directory)
                logger.info(f"Successfully uploaded with bunnycdnpython: {remote_path}")
                return True
            except Exception as e:
                logger.error(f"Error uploading with bunnycdnpython: {str(e)}")
                # Fall back to direct API

        # Use direct API calls
        url = f"{self.storage_api_url}/{self.storage_zone_name}/{remote_path}"
        content_type = self._get_content_type(local_file_path)

        try:
            with open(local_file_path, "rb") as file:
                headers = {"Content-Type": content_type}
                response = self.session.put(url, data=file, headers=headers)

            if response.status_code in (200, 201):
                logger.info(f"Successfully uploaded: {remote_path}")
                return True
            else:
                logger.error(
                    f"Failed to upload {remote_path}: {response.status_code} {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error uploading {remote_path}: {str(e)}")
            return False

    def download_file(self, remote_path: str, local_file_path: str) -> bool:
        """Download a file from Bunny.net storage"""
        # Use bunnycdnpython if available
        if self.bunny_client:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                # Create a temporary directory to download to
                local_dir = os.path.dirname(local_file_path)
                _file_name = os.path.basename(local_file_path)

                # If local_dir doesn't exist, create it
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir, exist_ok=True)

                # Download to the correct location
                self.bunny_client.DownloadFile(remote_path, local_file_path)
                logger.info(
                    f"Successfully downloaded with bunnycdnpython: {remote_path}"
                )
                return True
            except Exception as e:
                logger.error(f"Error downloading with bunnycdnpython: {str(e)}")
                # Fall back to direct API

        # Use password authentication if configured and no API key
        use_password = bool(self.password and not self.api_key)

        if use_password and not self.authenticated_cdn_endpoint:
            logger.error(
                "Password authentication requested but no authenticated_cdn_endpoint configured"
            )
            return False

        if use_password:
            # Use password authentication
            url = f"{self.authenticated_cdn_endpoint}/{remote_path}"
            headers = {}  # No API key needed, basic auth is in URL
        else:
            # Use API key authentication
            url = f"{self.storage_api_url}/{self.storage_zone_name}/{remote_path}"
            # Use storage_api_key if available, otherwise fall back to api_key
            headers = {
                "AccessKey": (
                    self.storage_api_key if self.storage_api_key else self.api_key
                )
            }

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            if use_password:
                # With password auth we use a direct request, not the self.session
                response = requests.get(url, headers=headers, stream=True)
            else:
                response = self.session.get(url, stream=True)

            if response.status_code != 200:
                logger.error(
                    f"Failed to download {remote_path}: {response.status_code} {response.text}"
                )
                return False

            with open(local_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Successfully downloaded: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading {remote_path}: {str(e)}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from Bunny.net storage"""
        # Use bunnycdnpython if available
        if self.bunny_client:
            try:
                self.bunny_client.DeleteFile(remote_path)
                logger.info(f"Successfully deleted with bunnycdnpython: {remote_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting with bunnycdnpython: {str(e)}")
                # Fall back to direct API

        # Use direct API calls
        url = f"{self.storage_api_url}/{self.storage_zone_name}/{remote_path}"

        try:
            response = self.session.delete(url)

            if response.status_code in (200, 204):
                logger.info(f"Successfully deleted: {remote_path}")
                return True
            else:
                logger.error(
                    f"Failed to delete {remote_path}: {response.status_code} {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error deleting {remote_path}: {str(e)}")
            return False

    def get_public_url(self, remote_path: str) -> str:
        """Get a public URL for a file in Bunny.net storage"""
        if self.password and self.authenticated_cdn_endpoint:
            # Use password-authenticated URL
            return f"{self.authenticated_cdn_endpoint}/{remote_path}"
        elif self.cdn_url:
            # Use CDN URL if configured
            return f"{self.cdn_url}/{remote_path}"
        else:
            # Use standard storage URL
            return f"https://{self.storage_zone_name}.{self.hostname}/{remote_path}"

    def purge_cache(self, paths: List[str] | None = None) -> Dict[str, Any]:
        """Purge files from Bunny.net cache"""
        if not self.pull_zone_name:
            logger.error("Pull zone name is required for cache purging")
            return {"success": False, "errors": ["Pull zone name not configured"]}

        results: Dict[str, Any] = {
            "success": False,
            "purged": 0,
            "failed": 0,
            "errors": [],
        }

        # URL for the purge API
        url = f"https://api.bunny.net/pullzone/{self.pull_zone_name}/purgeCache"

        try:
            if paths:
                # Purge specific paths
                for path in paths:
                    data = {"url": path}
                    response = self.session.post(url, json=data)

                    if response.status_code == 204:
                        results["purged"] += 1
                    else:
                        results["failed"] += 1
                        if isinstance(results["errors"], list):
                            results["errors"].append(
                                f"Failed to purge {path}: {response.status_code} {response.text}"
                            )
            else:
                # Purge everything
                response = self.session.post(f"{url}/purgeEverything")

                if response.status_code == 204:
                    results["purged"] = 1
                    logger.info("Successfully purged all cache")
                else:
                    results["failed"] = 1
                    if isinstance(results["errors"], list):
                        results["errors"].append(
                            f"Failed to purge cache: {response.status_code} {response.text}"
                        )

            results["success"] = results["failed"] == 0

        except Exception as e:
            if isinstance(results["errors"], list):
                results["errors"].append(f"Error purging cache: {str(e)}")

        return results

    def _get_content_type(self, filepath: str) -> str:
        """Get the content type of a file"""
        import mimetypes

        content_type, _ = mimetypes.guess_type(filepath)
        return content_type or "application/octet-stream"

    @property
    def storage_api_url(self) -> str:
        """Get the API URL for storage operations"""
        if self.storage_region:
            return f"https://storage-{self.storage_region}.bunnycdn.com"
        return f"https://{self.hostname}"
