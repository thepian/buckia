"""
Unit tests for the TokenManager class
"""

import os
from unittest.mock import call, patch

from buckia.security.token_manager import TokenManager


def test_get_token_from_env_var():
    """Test retrieving a token from an environment variable"""
    # Create a test environment variable with the correct naming convention
    token_value = "test-api-key-1234567890"
    with patch.dict(os.environ, {"buckia_buckia_test_context": token_value}):
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Token should be retrieved from the environment variable
        retrieved_token = token_manager.get_token("test_context")
        assert retrieved_token == token_value


def test_get_token_from_uppercase_env_var():
    """Test retrieving a token from an uppercase environment variable"""
    # Create a test environment variable with uppercase naming
    token_value = "test-api-key-from-uppercase"
    with patch.dict(os.environ, {"BUCKIA_BUCKIA_TEST_CONTEXT": token_value}):
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Token should be retrieved from the uppercase environment variable
        retrieved_token = token_manager.get_token("test_context")
        assert retrieved_token == token_value


def test_get_token_tries_both_cases():
    """Test that get_token tries both lowercase and uppercase environment variables"""
    # Mock os.getenv to track calls
    with patch("os.getenv") as mock_getenv:
        # Set up mock to return None for first call, then a value for second call
        mock_getenv.side_effect = [None, "uppercase-token-value"]

        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Add mock for authentication to avoid actually trying keyring
        with patch.object(TokenManager, "_authenticate_with_platform", return_value=True):
            # Get token
            retrieved_token = token_manager.get_token("test_context")

            # Verify both lowercase and uppercase were tried
            assert mock_getenv.call_count == 2
            assert mock_getenv.call_args_list[0] == call("buckia_buckia_test_context")
            assert mock_getenv.call_args_list[1] == call("BUCKIA_BUCKIA_TEST_CONTEXT")

            # Verify the correct token was returned
            assert retrieved_token == "uppercase-token-value"


def test_get_token_from_keyring_fallback():
    """Test that keyring is used as a fallback when env var is not present"""
    # Create a mock for keyring.get_password
    with patch("keyring.get_password") as mock_get_password:
        mock_get_password.return_value = "keyring-token-value"

        # Mock the authentication to always succeed
        with patch.object(TokenManager, "_authenticate_with_platform", return_value=True):
            # Initialize token manager
            token_manager = TokenManager(namespace="buckia")

            # Ensure no environment variable is present
            with patch.dict(os.environ, {}, clear=True):
                # Token should be retrieved from keyring
                retrieved_token = token_manager.get_token("test_context")
                assert retrieved_token == "keyring-token-value"

                # Verify keyring was called with correct parameters
                mock_get_password.assert_called_once_with("buckia_buckia_test_context", "api_token")


def test_save_token_to_keyring():
    """Test saving a token to keyring"""
    # Create a mock for keyring.set_password
    with patch("keyring.set_password") as mock_set_password:
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Save a token
        result = token_manager.save_token("test_context", "test-token-value")

        # Verify the result is True and keyring was called with correct parameters
        assert result is True
        mock_set_password.assert_called_once_with(
            "buckia_buckia_test_context", "api_token", "test-token-value"
        )


def test_delete_token_from_keyring():
    """Test deleting a token from keyring"""
    # Create a mock for keyring.delete_password
    with patch("keyring.delete_password") as mock_delete_password:
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Delete a token
        result = token_manager.delete_token("test_context")

        # Verify the result is True and keyring was called with correct parameters
        assert result is True
        mock_delete_password.assert_called_once_with("buckia_buckia_test_context", "api_token")


def test_list_bucket_contexts():
    """Test listing available bucket contexts"""

    # Create a mock for keyring.get_password that returns a token for some contexts
    def mock_get_password_side_effect(service, username):
        # Return a token for 'bunny' and 's3' contexts
        if service in ["buckia_buckia_bunny", "buckia_buckia_s3"]:
            return "some-token"
        return None

    # Create a mock for keyring.get_password
    with patch("keyring.get_password") as mock_get_password:
        mock_get_password.side_effect = mock_get_password_side_effect

        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # List available contexts
        contexts = token_manager.list_bucket_contexts()

        # Verify the result includes 'bunny' and 's3'
        assert "bunny" in contexts
        assert "s3" in contexts
        assert "linode" not in contexts  # No token was returned for this context


def test_get_token_id_from_env_var():
    """Test retrieving a token ID from an environment variable"""
    # Create a test environment variable with the correct naming convention
    token_id_value = "test-token-id-1234567890"
    with patch.dict(os.environ, {"buckia_buckia_test_context_id": token_id_value}):
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Token ID should be retrieved from the environment variable
        retrieved_token_id = token_manager.get_token_id("test_context")
        assert retrieved_token_id == token_id_value


def test_get_token_id_from_uppercase_env_var():
    """Test retrieving a token ID from an uppercase environment variable"""
    # Create a test environment variable with uppercase naming
    token_id_value = "test-token-id-from-uppercase"
    with patch.dict(os.environ, {"BUCKIA_BUCKIA_TEST_CONTEXT_ID": token_id_value}):
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Token ID should be retrieved from the uppercase environment variable
        retrieved_token_id = token_manager.get_token_id("test_context")
        assert retrieved_token_id == token_id_value


def test_get_token_id_from_keyring_fallback():
    """Test that keyring is used as a fallback when env var is not present for token ID"""
    # Create a mock for keyring.get_password
    with patch("keyring.get_password") as mock_get_password:
        mock_get_password.return_value = "keyring-token-id-value"

        # Mock the authentication to always succeed
        with patch.object(TokenManager, "_authenticate_with_platform", return_value=True):
            # Initialize token manager
            token_manager = TokenManager(namespace="buckia")

            # Ensure no environment variable is present
            with patch.dict(os.environ, {}, clear=True):
                # Token ID should be retrieved from keyring
                retrieved_token_id = token_manager.get_token_id("test_context")
                assert retrieved_token_id == "keyring-token-id-value"

                # Verify keyring was called with correct parameters
                mock_get_password.assert_called_once_with("buckia_buckia_test_context", "token_id")


def test_save_token_id_to_keyring():
    """Test saving a token ID to keyring"""
    # Create a mock for keyring.set_password
    with patch("keyring.set_password") as mock_set_password:
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Save a token ID
        result = token_manager.save_token_id("test_context", "test-token-id-value")

        # Verify the result is True and keyring was called with correct parameters
        assert result is True
        mock_set_password.assert_called_once_with(
            "buckia_buckia_test_context", "token_id", "test-token-id-value"
        )


def test_delete_token_id_from_keyring():
    """Test deleting a token ID from keyring"""
    # Create a mock for keyring.delete_password
    with patch("keyring.delete_password") as mock_delete_password:
        # Initialize token manager
        token_manager = TokenManager(namespace="buckia")

        # Delete a token ID
        result = token_manager.delete_token_id("test_context")

        # Verify the result is True and keyring was called with correct parameters
        assert result is True
        mock_delete_password.assert_called_once_with("buckia_buckia_test_context", "token_id")


def test_get_token_with_id():
    """Test retrieving both token and token ID at once"""
    # Create mocks for get_token and get_token_id
    with patch.object(TokenManager, "get_token", return_value="test-token-value") as mock_get_token:
        with patch.object(
            TokenManager, "get_token_id", return_value="test-token-id-value"
        ) as mock_get_token_id:
            # Initialize token manager
            token_manager = TokenManager(namespace="buckia")

            # Get both token and token ID
            token, token_id = token_manager.get_token_with_id("test_context")

            # Verify both values were returned correctly
            assert token == "test-token-value"
            assert token_id == "test-token-id-value"

            # Verify the individual methods were called with the right context
            mock_get_token.assert_called_once_with("buckia_buckia_test_context")
            mock_get_token_id.assert_called_once_with("buckia_buckia_test_context")


def test_save_token_with_id():
    """Test saving both token and token ID at once"""
    # Create mocks for save_token and save_token_id
    with patch.object(TokenManager, "save_token", return_value=True) as mock_save_token:
        with patch.object(TokenManager, "save_token_id", return_value=True) as mock_save_token_id:
            # Initialize token manager
            token_manager = TokenManager(namespace="buckia")

            # Save both token and token ID
            result = token_manager.save_token_with_id(
                "test_context", "test-token-value", "test-token-id-value"
            )

            # Verify the result is True
            assert result is True

            # Verify both individual methods were called with the right parameters
            mock_save_token.assert_called_once_with(
                "buckia_buckia_test_context", "test-token-value"
            )
            mock_save_token_id.assert_called_once_with(
                "buckia_buckia_test_context", "test-token-id-value"
            )


def test_save_token_with_id_partial_failure():
    """Test save_token_with_id returns False if either save operation fails"""
    # Create mocks for save_token and save_token_id
    with patch.object(TokenManager, "save_token", return_value=True) as mock_save_token:
        with patch.object(TokenManager, "save_token_id", return_value=False) as mock_save_token_id:
            # Initialize token manager
            token_manager = TokenManager(namespace="buckia")

            # Save both token and token ID
            result = token_manager.save_token_with_id(
                "test_context", "test-token-value", "test-token-id-value"
            )

            # Verify the result is False (because save_token_id returned False)
            assert result is False

            # Verify both individual methods were still called
            mock_save_token.assert_called_once()
            mock_save_token_id.assert_called_once()
