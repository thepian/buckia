"""
Security module for Buckia application.
Provides secure token management and authentication functionality.
"""

from .token_manager import TokenManager

__all__ = ["TokenManager"]


# Initialize default TokenManager with the buckia namespace
def get_token_manager():
    """Get a configured TokenManager instance for Buckia"""
    return TokenManager(namespace="buckia")
