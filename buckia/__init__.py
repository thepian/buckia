"""
Buckia - A multi-platform, multi-backend storage bucket synchronization library
"""

__version__ = "0.5.0"

from .client import BuckiaClient
from .config import BucketConfig, BuckiaConfig

__all__ = ["BuckiaClient", "BucketConfig", "BuckiaConfig"]
