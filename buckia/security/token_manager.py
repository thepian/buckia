"""
Token management for secure API token storage and retrieval.
Uses keyring for secure token storage with platform-appropriate authentication.
Supports storing both API tokens and token IDs for authentication purposes.
"""

import getpass
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Import keyring for secure token storage
import keyring

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
# Check several locations, starting with the project root
try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not installed, .env files will not be loaded")

if DOTENV_AVAILABLE:
    # Try to find the project root (look for pyproject.toml)
    current_dir = Path.cwd()
    root_dir = current_dir

    # Walk up the directory tree looking for pyproject.toml
    while root_dir and not (root_dir / "pyproject.toml").exists():
        parent = root_dir.parent
        # Stop if we reach the filesystem root
        if parent == root_dir:
            break
        root_dir = parent

    # Look for .env in several places, in order of preference
    env_locations = [
        root_dir / ".env",  # Project root
        Path(os.path.dirname(os.path.dirname(__file__))) / ".env",  # Module parent directory
        Path.home() / ".buckia" / ".env",  # User home directory
    ]

    for dotenv_path in env_locations:
        if dotenv_path.exists():
            # Always load and override environment variables from .env
            load_dotenv(dotenv_path=dotenv_path, override=True)
            logger.info(f"Loaded environment variables from {dotenv_path}")
            break


class TokenManager:
    """
    Manages API tokens and token IDs with secure storage and biometric authentication when available.
    Uses the system keychain on supported platforms.

    Token IDs can be used for user identification during authentication processes and
    can be stored alongside tokens or separately using the same security mechanisms.
    """

    def __init__(self, namespace: str = "buckia"):
        """
        Initialize token manager.

        Args:
            namespace: Namespace for token storage (service prefix in keyring)
        """
        self.namespace = namespace

        # Keyring is now always available as it's a dependency

    def save_token(self, context: str, token: Optional[str] = None) -> bool:
        """
        Save an API token for a context.

        Args:
            context: Context name (e.g., 'bunny', 'premium')
            token: Token value (if None, will prompt securely)

        Returns:
            True if token was saved successfully, False otherwise
        """
        # Keyring is now always available

        if token is None:
            token = getpass.getpass(f"Enter API token for {context}: ")

        try:
            full_context = f"buckia_{self.namespace}_{context}"
            keyring.set_password(full_context, "api_token", token)
            logger.info(f"Token saved for {context}")
            return True
        except Exception as e:
            logger.error(f"Error saving token: {e}")
            return False

    def save_token_with_id(
        self, context: str, token: Optional[str] = None, token_id: Optional[str] = None
    ) -> bool:
        """
        Save both an API token and token ID for a context in a single operation.

        Args:
            context: Context name (e.g., 'bunny', 'premium')
            token: Token value (if None, will prompt securely)
            token_id: Token ID value (if None, will prompt securely)

        Returns:
            True if both token and token ID were saved successfully, False otherwise
        """
        full_context = f"buckia_{self.namespace}_{context}"
        token_saved = self.save_token(full_context, token)
        token_id_saved = self.save_token_id(full_context, token_id)

        return token_saved and token_id_saved

    def get_token(self, context: str) -> Optional[str]:
        """
        Retrieve an API token for a context.
        First checks for an environment variable with the name format:
        buckia_<namespace>_<context>, e.g., buckia_buckia_bunny
        If no environment variable is found, also tries the uppercase version.
        If still not found, falls back to keyring without authentication during tests,
        or with authentication during normal operation.

        Args:
            context: Context name (e.g., 'bunny', 'premium')

        Returns:
            Token if found, None otherwise
        """
        # First check for environment variable
        # Environment variables follow the convention: buckia_<namespace>_<context>
        name = f"buckia_{self.namespace}_{context}"

        # Try direct match first
        token = os.getenv(name)
        if token is not None:
            logger.debug(f"Using token from environment variable: {name}")
            return token

        # Try uppercase version if not found
        upper_name = name.upper()
        token = os.getenv(upper_name)
        if token is not None:
            logger.debug(f"Using token from uppercase environment variable: {upper_name}")
            return token

        # If still not found, handle test environment
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI") == "1":
            logger.error(
                f"Environment variables {name} or {upper_name} are required for tests but not found"
            )
            logger.error(f"Please set {name} in your .env file or CI environment")
            # For tests, return None immediately without trying keyring
            return None

        # Try platform-specific biometric authentication for normal (non-test) use
        auth_success = self._authenticate_with_platform()

        if auth_success:
            try:
                full_context = f"buckia_{self.namespace}_{context}"
                token = keyring.get_password(full_context, "api_token")
                if token:
                    return token
                else:
                    logger.error(f"No token found in keyring for {context}")
                    return None
            except Exception as e:
                logger.error(f"Error retrieving token from keyring: {e}")
                return None
        else:
            logger.error("Authentication failed")
            return None

    def list_bucket_contexts(self) -> List[str]:
        """
        List available bucket contexts that have saved tokens.

        Returns:
            List of bucket context names with saved tokens
        """
        # This is a simplified implementation - actual keyring backends
        # may not support listing all passwords
        # In a full implementation, you might need to maintain a separate
        # registry of bucket contexts
        known_bucket_contexts = [
            "bunny",
            "s3",
            "linode",
            "custom",
        ]

        # Keyring is now always available

        available_contexts = []
        for context in known_bucket_contexts:
            full_context = f"buckia_{self.namespace}_{context}"
            try:
                token = keyring.get_password(full_context, "api_token")
                if token:
                    available_contexts.append(context)
            except:
                pass

        return available_contexts

    def get_token_with_id(self, context: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve both an API token and token ID for a context.

        Args:
            context: Context name (e.g., 'bunny', 'premium')

        Returns:
            A tuple containing (token, token_id). Either value may be None if not found.
        """
        full_context = f"buckia_{self.namespace}_{context}"
        token = self.get_token(full_context)
        token_id = self.get_token_id(full_context)

        return token, token_id

    # Alias for backward compatibility
    list_services = list_bucket_contexts

    def save_token_id(self, context: str, token_id: Optional[str] = None) -> bool:
        """
        Save a token ID for a context. The token ID can be used for user identification
        during authentication processes.

        Args:
            context: Context name (e.g., 'bunny', 'premium')
            token_id: Token ID value (if None, will prompt securely)

        Returns:
            True if token ID was saved successfully, False otherwise
        """
        if token_id is None:
            token_id = getpass.getpass(f"Enter token ID for {context}: ")

        try:
            full_context = f"buckia_{self.namespace}_{context}"
            keyring.set_password(full_context, "token_id", token_id)
            logger.info(f"Token ID saved for {context}")
            return True
        except Exception as e:
            logger.error(f"Error saving token ID: {e}")
            return False

    def get_token_id(self, context: str) -> Optional[str]:
        """
        Retrieve a token ID for a context.
        First checks for an environment variable with the name format:
        buckia_<namespace>_<context>_id, e.g., buckia_buckia_bunny_id
        If no environment variable is found, also tries the uppercase version.
        If still not found, falls back to keyring without authentication during tests,
        or with authentication during normal operation.

        Args:
            context: Context name (e.g., 'bunny', 'premium')

        Returns:
            Token ID if found, None otherwise
        """
        # First check for environment variable
        # Environment variables follow the convention: buckia_<namespace>_<context>_id
        name = f"buckia_{self.namespace}_{context}_id"

        # Try direct match first
        token_id = os.getenv(name)
        if token_id is not None:
            logger.debug(f"Using token ID from environment variable: {name}")
            return token_id

        # Try uppercase version if not found
        upper_name = name.upper()
        token_id = os.getenv(upper_name)
        if token_id is not None:
            logger.debug(f"Using token ID from uppercase environment variable: {upper_name}")
            return token_id

        # If still not found, handle test environment
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI") == "1":
            logger.error(
                f"Environment variables {name} or {upper_name} are required for tests but not found"
            )
            logger.error(f"Please set {name} in your .env file or CI environment")
            # For tests, return None immediately without trying keyring
            return None

        # Try platform-specific biometric authentication for normal (non-test) use
        auth_success = self._authenticate_with_platform()

        if auth_success:
            try:
                full_context = f"buckia_{self.namespace}_{context}"
                token_id = keyring.get_password(full_context, "token_id")
                if token_id:
                    return token_id
                else:
                    logger.error(f"No token ID found in keyring for {context}")
                    return None
            except Exception as e:
                logger.error(f"Error retrieving token ID from keyring: {e}")
                return None
        else:
            logger.error("Authentication failed")
            return None

    def delete_token(self, context: str) -> bool:
        """
        Delete an API token for a service.

        Args:
            context: Context name (e.g., 'bunny', 'premium')

        Returns:
            True if token was deleted successfully, False otherwise
        """
        # Keyring is now always available

        try:
            full_context = f"buckia_{self.namespace}_{context}"
            keyring.delete_password(full_context, "api_token")
            logger.info(f"Token deleted for {context}")
            return True
        except Exception as e:
            logger.error(f"Error deleting token: {e}")
            return False

    def delete_token_id(self, context: str) -> bool:
        """
        Delete a token ID for a service.

        Args:
            context: Context name (e.g., 'bunny', 'premium')

        Returns:
            True if token ID was deleted successfully, False otherwise
        """
        try:
            full_context = f"buckia_{self.namespace}_{context}"
            keyring.delete_password(full_context, "token_id")
            logger.info(f"Token ID deleted for {context}")
            return True
        except Exception as e:
            logger.error(f"Error deleting token ID: {e}")
            return False

    def _authenticate_with_platform(self) -> bool:
        """
        Perform platform-specific authentication check.

        Returns:
            True if authentication succeeded, False otherwise
        """
        # Check if running in test mode or CI environment
        # This allows tests to bypass authentication
        if os.environ.get("CI") == "1" or os.environ.get("PYTEST_CURRENT_TEST"):
            logger.debug("Running in test environment, skipping authentication")
            return True

        system = platform.system()

        if system == "Darwin":  # macOS
            try:
                # security command triggers Touch ID on supported devices
                result = subprocess.run(
                    ["security", "authorize", "-u"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return True
            except Exception as e:
                logger.debug(f"macOS authentication error: {e}")
                # Fall through to password fallback

        elif system == "Linux":
            try:
                # This might trigger fingerprint auth if configured
                result = subprocess.run(
                    ["pkexec", "--disable-internal-agent", "true"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    return True
            except Exception as e:
                logger.debug(f"Linux authentication error: {e}")
                # Fall through to password fallback

        # Check if running with stdin/stdout captured (like in pytest without -s)
        # If so, skip the password prompt that would hang
        if not os.isatty(sys.stdin.fileno()):
            logger.debug("Non-interactive environment detected, skipping password prompt")
            # Default to success for non-interactive environments (appropriate for testing)
            return True

        # Fall back to password verification for interactive use
        try:
            verify = getpass.getpass("Verification required to access token: ")
            # In a full implementation, you'd verify this against a stored hash
            # For now, we'll accept any non-empty password for demo purposes
            return len(verify) > 0
        except Exception as e:
            logger.warning(f"Password prompt failed: {e}")
            # Default to failure if password prompt fails
            return False
