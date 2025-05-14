# BuckiaKit Test Plan

This document outlines the comprehensive test strategy for the BuckiaKit Swift package.

## Test Categories

### 1. Core Client Tests

**BuckiaClientTests**
- Test initialization with valid configuration
- Test initialization with invalid configuration (should throw errors)
- Test connection to storage provider
- Test client context switching/updating configuration
- Test client lifecycle (init, use, close)

**BuckiaConfigurationTests**
- Test creating configuration from various sources (code, JSON)
- Test configuration serialization/deserialization
- Test valid and invalid configurations
- Test default values handling

### 2. Storage Provider Tests

**StorageProviderTests**
- Test provider factory pattern (getting correct provider types)
- Test provider registration mechanism
- Test provider connection handling

**BunnyStorageProviderTests**
- Test connection to Bunny.net
- Test path handling and URL construction
- Test error handling with invalid credentials
- Test API response parsing

**LocalStorageProviderTests**
- Test local file operations
- Test path resolution
- Test error handling with invalid paths
- Test APFS integration (if applicable)

### 3. File Operations Tests

**SyncOperationsTests**
- Test file synchronization between local and remote
- Test incremental sync behavior
- Test conflict resolution
- Test progress reporting
- Test cancellation

**FileOperationsTests**
- Test uploading files
- Test downloading files
- Test listing remote files
- Test deleting files
- Test handling large files

### 4. Token Management and Authentication Tests

**TokenManagerTests**
- Test token storage in keychain
- Test token retrieval
- Test token rotation
- Test metadata handling
- Test token expiration

**AuthenticationTests**
- Test different authentication methods (API key, Okta)
- Test credential management
- Test authentication error handling
- Test authentication renewal

**BunnyTokenFactoryTests**
- Test CDN token generation
- Test token validation
- Test various token parameters (IP restriction, country codes, etc.)
- Test token format compliance with Bunny.net specs

### 5. Permission and Access Control Tests

**StoragePermissionsTests**
- Test permission creation and manipulation
- Test permission serialization
- Test path restriction functionality
- Test permission combination

**UserSpecificTokenTests**
- Test generating tokens for specific users
- Test token scoping to user paths
- Test permission granularity

### 6. Database Management Tests

**DatabaseManagerTests**
- Test SQLite database handling
- Test backup operations
- Test APFS Copy-on-Write functionality
- Test database diffing for sharing

**InboundChangesTests**
- Test processing inbound changes
- Test change application
- Test conflict resolution
- Test incremental updates

### 7. Error Handling Tests

**ErrorHandlingTests**
- Test all error types
- Test error propagation
- Test recovery from errors
- Test error reporting

### 8. Integration Tests

**EndToEndSyncTests**
- Test complete sync workflow
- Test real-world usage scenarios
- Test performance with various file sizes/counts
- Test reliability with network interruptions

**MultiproviderTests**
- Test switching between providers
- Test consistent behavior across providers
- Test migration between providers

### 9. SwiftUI Integration Tests

**EnvironmentIntegrationTests**
- Test @Environment property wrapper
- Test environment value propagation
- Test SwiftUI binding

**ProgressReportingTests**
- Test progress updates in SwiftUI
- Test cancellation
- Test error presentation

## Test Data and Mocks

- Create mock storage providers for testing
- Create test fixtures (files of various types/sizes)
- Set up mock authentication services
- Create sample databases for testing diffing

## Test Implementation Strategy

1. **Unit Tests**: Focus on individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Ensure performance meets requirements
5. **Regression Tests**: Prevent regressions in functionality

## Test Environment

- Test on multiple platforms (macOS, iOS, tvOS)
- Test with different Swift versions (5.9+)
- Test with different network conditions
- Test with different storage providers

## Test Execution

- Run tests automatically on every build
- Run tests before every commit
- Run more comprehensive tests before release

## Test Coverage Goals

- Aim for 90%+ code coverage
- Ensure all public API methods are tested
- Ensure all error paths are tested
- Ensure all configuration options are tested