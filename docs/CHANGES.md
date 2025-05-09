# Changes to Buckia

## Added Backblaze B2 Storage Provider Support

Buckia now supports Backblaze B2 as a storage provider. This implementation includes:

1. **Complete B2 Backend Implementation**
   - File upload and download operations
   - Directory synchronization
   - Public URL generation for shared files
   - Comprehensive error handling

2. **Integration Tests**
   - Tests configured to use "buckia-test" bucket (ID: 81cffb4f05c7c201966b0b12)
   - Token-based authentication using the "demo" token context
   - Tests for file operations, listing, and synchronization

3. **Documentation Updates**
   - Updated README with B2 information
   - Installation instructions for B2 dependency
   - Provider capabilities documentation

4. **Dependency Management**
   - Added optional b2sdk dependency
   - Installable via `pip install "buckia[b2]"`

## Changes to Buckia Configuration System

## Added Multi-Bucket Configuration Support

The Buckia library now supports managing multiple bucket configurations through the new `BuckiaConfig` class. This enhancement allows users to define multiple configurations in a single file and easily switch between them.

### Key Changes

1. **New `BuckiaConfig` Class**

   - Acts as a container for multiple `BucketConfig` instances
   - Supports dictionary-like access for bucket configurations
   - Includes methods for file loading and saving

2. **Updated Configuration File Format**

   - Now supports multiple named bucket configurations
   - Each configuration is identified by a key (e.g., "default", "production")
   - Maintains backward compatibility with single-bucket configuration files

3. **Enhanced Client Initialization**

   - `BuckiaClient` now accepts `BuckiaConfig` objects
   - Added `bucket_name` parameter to select specific configurations
   - Uses "default" bucket automatically when available

4. **Improved Test Configuration**
   - Updated test fixtures to handle multi-bucket configurations
   - Added `buckia_config` fixture for easier testing
   - Updated `test_config.yaml` with multi-bucket format

### Backward Compatibility

- Existing single-bucket configuration files continue to work
- `BucketConfig.from_file()` automatically detects multi-bucket files and selects the appropriate configuration
- The client intelligently works with both old and new configuration formats

### Documentation Updates

- Added comprehensive documentation in `BUCKIA_CONFIG.md`
- Included examples of file format and usage patterns
- Added unit tests for all new functionality

## Migration Guide

To migrate from a single-bucket to a multi-bucket configuration:

1. Wrap your existing configuration in a "default" section
2. Add additional named configurations as needed
3. When creating a client, specify the bucket name if needed

Example:

```python
# Old approach (still supported)
client = BuckiaClient("path/to/config.yaml")

# New approach with specific bucket
config = BuckiaConfig.from_file("path/to/multi_config.yaml")
client = BuckiaClient(config, bucket_name="production")
```

## Testing

Unit tests have been added to cover:

- Dictionary-like access and iteration
- Loading multi-bucket configurations from files
- Saving configurations to files
- Error handling for invalid configurations

Integration tests have been updated to work with the new configuration format while maintaining compatibility with existing tests.
