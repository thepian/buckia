import Foundation
import Logging

private let logger = Logger(label: "com.buckia.BuckiaClient")

/// Main client interface for interacting with Buckia storage services
public final class BuckiaClient {
    /// Configuration for the client
    public private(set) var config: BuckiaConfiguration
    
    /// Storage provider instance
    private var provider: StorageProvider
    
    /// Creates a new Buckia client with the specified configuration
    public init(configuration: BuckiaConfiguration) async throws {
        self.config = configuration
        
        // Create the appropriate storage provider based on the configuration
        switch configuration.provider {
        case .bunny:
            self.provider = try BunnyStorageProvider(config: configuration)
        case .b2:
            throw BuckiaError.configurationError("B2 provider not implemented yet")
        case .s3:
            throw BuckiaError.configurationError("S3 provider not implemented yet")
        case .local:
            self.provider = try LocalStorageProvider(config: configuration)
        case .custom:
            throw BuckiaError.configurationError("Custom provider requires explicit initialization")
        }
        
        // Connect to the provider
        if !(try await provider.connect()) {
            throw BuckiaError.connectionFailed("Failed to connect to provider: \(configuration.provider)")
        }
    }
    
    /// Creates a new Buckia client with a custom storage provider
    public init(configuration: BuckiaConfiguration, provider: StorageProvider) async throws {
        self.config = configuration
        self.provider = provider
        
        // Connect to the provider
        if !(try await provider.connect()) {
            throw BuckiaError.connectionFailed("Failed to connect to provider: \(provider.providerType)")
        }
    }
    
    /// Tests the connection to the storage provider
    public func testConnection() async throws -> ConnectionStatus {
        return try await provider.testConnection()
    }
    
    /// Performs a sync operation between local storage and remote storage
    public func sync(options: SyncOptions, progressHandler: SyncProgressHandler? = nil) async throws -> SyncResult {
        logger.info("Starting sync operation with options: \(options)")
        return try await provider.sync(options: options, progressHandler: progressHandler)
    }
    
    /// Uploads a file to remote storage
    public func uploadFile(localURL: URL, remotePath: String? = nil) async throws -> UploadResult {
        logger.info("Uploading file: \(localURL) to \(remotePath ?? "default path")")
        return try await provider.uploadFile(localURL: localURL, remotePath: remotePath)
    }
    
    /// Downloads a file from remote storage
    public func downloadFile(remotePath: String, localURL: URL) async throws -> DownloadResult {
        logger.info("Downloading file: \(remotePath) to \(localURL)")
        return try await provider.downloadFile(remotePath: remotePath, localURL: localURL)
    }
    
    /// Deletes a file from remote storage
    public func deleteFile(remotePath: String) async throws -> Bool {
        logger.info("Deleting file: \(remotePath)")
        return try await provider.deleteFile(remotePath: remotePath)
    }
    
    /// Lists files in remote storage
    public func listFiles(path: String? = nil) async throws -> [RemoteFile] {
        logger.info("Listing files in: \(path ?? "root")")
        return try await provider.listFiles(path: path)
    }
    
    /// Gets a public URL for a remote file
    public func getPublicURL(remotePath: String) throws -> URL {
        logger.info("Getting public URL for: \(remotePath)")
        return try provider.getPublicURL(remotePath: remotePath)
    }
    
    /// Updates the client configuration
    public func updateConfiguration(_ configuration: BuckiaConfiguration) async throws {
        // Only update if the provider type remains the same
        guard configuration.provider == config.provider else {
            throw BuckiaError.configurationError("Cannot change provider type after initialization")
        }
        
        self.config = configuration
        
        // Reconnect to apply new settings
        if !(try await provider.connect()) {
            throw BuckiaError.connectionFailed("Failed to reconnect with updated configuration")
        }
    }
    
    /// Closes the client and releases resources
    public func close() async {
        // Clean up any resources used by the client
    }
}