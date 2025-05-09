"""
Quick test to verify B2 backend can be initialized
"""

from buckia.config import BucketConfig
from buckia.sync.b2 import B2Sync


def test_b2_backend_init() -> None:
    """Test that we can initialize the B2 backend"""
    # Create a minimal config
    config = BucketConfig(provider="b2", bucket_name="buckia-test", token_context="demo")

    # Create the backend
    backend = B2Sync(config)

    # Verify the backend has the necessary attributes
    assert hasattr(backend, "connect")
    assert hasattr(backend, "test_connection")
    assert hasattr(backend, "list_remote_files")
    assert hasattr(backend, "upload_file")
    assert hasattr(backend, "download_file")
    assert hasattr(backend, "delete_file")
    assert hasattr(backend, "get_public_url")
