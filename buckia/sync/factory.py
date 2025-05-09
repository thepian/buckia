"""
Factory for creating synchronization backends
"""

import importlib
import logging
from typing import Any

from ..config import BucketConfig
from .base import BaseSync

logger = logging.getLogger("buckia.factory")


def create_sync_backend(
    config: dict[str, Any] | BucketConfig,
) -> BaseSync | None:
    """
    Create appropriate synchronization backend based on provider

    Args:
        config: Configuration object with provider and other settings

    Returns:
        Instance of BaseSync subclass or None if provider not supported
    """
    provider = getattr(config, "provider", "").lower()

    if not provider:
        logger.error("No provider specified in configuration")
        return None

    try:
        if provider == "bunny":
            # Try to import BunnySync backend
            try:
                from .bunny import BunnySync  # type: ignore

                return BunnySync(config)
            except ImportError:
                logger.error("Failed to import BunnySync backend")
                return None

        elif provider == "s3":
            # Try to import S3Sync backend
            try:
                from .s3 import S3Sync  # type: ignore

                return S3Sync(config)
            except ImportError:
                logger.error("Failed to import S3Sync backend")
                return None

        elif provider == "linode":
            # Try to import LinodeSync backend
            try:
                from .linode import LinodeSync  # type: ignore

                return LinodeSync(config)
            except ImportError:
                logger.error("Failed to import LinodeSync backend")
                return None

        elif provider == "b2":
            # Try to import B2Sync backend
            try:
                from .b2 import B2Sync  # type: ignore

                return B2Sync(config)
            except ImportError as e:
                logger.error(f"Failed to import B2Sync backend, {e}")
                return None

        else:
            # Try dynamic import for custom backends
            try:
                module_name = f".{provider}"
                module = importlib.import_module(module_name, package="buckia.sync")
                class_name = f"{provider.capitalize()}Sync"
                backend_class = getattr(module, class_name)
                return backend_class(config)
            except (ImportError, AttributeError) as e:
                logger.error(f"Provider not supported: {provider} - {str(e)}")
                return None

    except Exception as e:
        logger.error(f"Error creating sync backend for provider {provider}: {str(e)}")
        return None


get_sync_backend = create_sync_backend
