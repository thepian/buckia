"""
Factory for creating synchronization backends
"""

import importlib
import logging
from typing import Dict, Any, Optional
from .base import BaseSync
from ..config import BucketConfig


logger = logging.getLogger('buckia.factory')

def create_sync_backend(config: Dict[str, Any] | BucketConfig) -> Optional[BaseSync]:
    """
    Create appropriate synchronization backend based on provider
    
    Args:
        config: Configuration object with provider and other settings
        
    Returns:
        Instance of BaseSync subclass or None if provider not supported
    """
    provider = getattr(config, 'provider', '').lower()
    
    if not provider:
        logger.error("No provider specified in configuration")
        return None
        
    try:
        if provider == 'bunny':
            # Try to import BunnySync backend
            try:
                from .bunny import BunnySync
                return BunnySync(config)
            except ImportError:
                logger.error("Failed to import BunnySync backend")
                return None
                
        elif provider == 's3':
            # Try to import S3Sync backend
            try:
                from .s3 import S3Sync
                return S3Sync(config)
            except ImportError:
                logger.error("Failed to import S3Sync backend")
                return None
                
        elif provider == 'linode':
            # Try to import LinodeSync backend
            try:
                from .linode import LinodeSync
                return LinodeSync(config)
            except ImportError:
                logger.error("Failed to import LinodeSync backend")
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