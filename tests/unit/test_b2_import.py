"""
Unit tests for B2 SDK import and basic functionality
"""

import sys

import pytest


def test_b2sdk_import():
    """Test if b2sdk module can be imported successfully"""
    try:
        import b2sdk

        assert "b2sdk" in sys.modules

        # Get version information
        print(f"Successfully imported b2sdk version: {b2sdk.__version__}")

        # Import API class from v2
        from b2sdk.v2.api import B2Api

        assert hasattr(B2Api, "authorize_account")

        # Import account info from internal structure
        from b2sdk._internal.account_info.in_memory import InMemoryAccountInfo

        assert hasattr(InMemoryAccountInfo, "get_account_id")

        # Import download destination from v1
        from b2sdk.v1.download_dest import DownloadDestLocalFile

        assert hasattr(DownloadDestLocalFile, "__init__")

        # Check for exception classes
        try:
            # Try internal structure
            from b2sdk._internal.exception import B2Error, FileNotPresent

            assert issubclass(B2Error, Exception)
            assert issubclass(FileNotPresent, B2Error)
        except ImportError:
            # Try other locations
            try:
                from b2sdk.exception import B2Error, FileNotPresent

                assert issubclass(B2Error, Exception)
                assert issubclass(FileNotPresent, B2Error)
            except ImportError:
                try:
                    from b2sdk.v2.exception import B2Error, FileNotPresent

                    assert issubclass(B2Error, Exception)
                    assert issubclass(FileNotPresent, B2Error)
                except ImportError:
                    pytest.fail(
                        "Could not import B2Error and FileNotPresent from any known location"
                    )

        # Test creating API and account info objects
        info = InMemoryAccountInfo()
        api = B2Api(info)
        assert hasattr(api, "authorize_account")

    except ImportError as e:
        pytest.fail(f"Failed to import b2sdk: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error while testing b2sdk: {e}")


def test_b2_sync_import():
    """Test importing our B2Sync implementation"""
    try:
        from buckia.sync.b2 import B2Sync

        # Check that B2Sync has the required attributes
        assert hasattr(B2Sync, "connect")
        assert hasattr(B2Sync, "test_connection")
        assert hasattr(B2Sync, "list_remote_files")
        assert hasattr(B2Sync, "upload_file")
        assert hasattr(B2Sync, "download_file")
        assert hasattr(B2Sync, "delete_file")
        assert hasattr(B2Sync, "get_public_url")

    except ImportError as e:
        pytest.fail(f"Failed to import B2Sync: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error while testing B2Sync import: {e}")
