import Foundation

/// Supported storage provider types
public enum StorageProviderType: String, Codable {
    case bunny
    case b2
    case s3
    case local
    case custom
}

/// Status of a connection to a storage provider
public struct ConnectionStatus {
    /// Whether the connection is established
    public let isConnected: Bool
    
    /// Additional status information
    public let details: [String: Bool]
    
    /// Any error that occurred during connection
    public let error: Error?
    
    /// Creates a connection status
    public init(isConnected: Bool, details: [String: Bool] = [:], error: Error? = nil) {
        self.isConnected = isConnected
        self.details = details
        self.error = error
    }
}

/// Result of a sync operation
public struct SyncResult {
    /// Number of files uploaded
    public let filesUploaded: Int
    
    /// Number of files downloaded
    public let filesDownloaded: Int
    
    /// Number of files deleted
    public let filesDeleted: Int
    
    /// Number of files skipped (already in sync)
    public let filesSkipped: Int
    
    /// Total number of bytes transferred
    public let bytesTransferred: Int64
    
    /// Elapsed time in seconds
    public let elapsedTime: TimeInterval
    
    /// Files that failed to sync
    public let failures: [FailedFile]
    
    /// Creates a sync result
    public init(
        filesUploaded: Int = 0,
        filesDownloaded: Int = 0,
        filesDeleted: Int = 0,
        filesSkipped: Int = 0,
        bytesTransferred: Int64 = 0,
        elapsedTime: TimeInterval = 0,
        failures: [FailedFile] = []
    ) {
        self.filesUploaded = filesUploaded
        self.filesDownloaded = filesDownloaded
        self.filesDeleted = filesDeleted
        self.filesSkipped = filesSkipped
        self.bytesTransferred = bytesTransferred
        self.elapsedTime = elapsedTime
        self.failures = failures
    }
}

/// File that failed to sync
public struct FailedFile {
    /// Path to the file
    public let path: String
    
    /// Operation that failed
    public let operation: SyncOperation
    
    /// Error that occurred
    public let error: Error
    
    /// Creates a failed file
    public init(path: String, operation: SyncOperation, error: Error) {
        self.path = path
        self.operation = operation
        self.error = error
    }
}

/// Type of sync operation
public enum SyncOperation: String {
    case upload
    case download
    case delete
}

/// Result of an upload operation
public struct UploadResult {
    /// Whether the upload was successful
    public let success: Bool
    
    /// URL of the uploaded file
    public let url: URL?
    
    /// Error that occurred during upload
    public let error: Error?
    
    /// Creates an upload result
    public init(success: Bool, url: URL? = nil, error: Error? = nil) {
        self.success = success
        self.url = url
        self.error = error
    }
}

/// Result of a download operation
public struct DownloadResult {
    /// Whether the download was successful
    public let success: Bool
    
    /// Local URL of the downloaded file
    public let localURL: URL?
    
    /// Error that occurred during download
    public let error: Error?
    
    /// Creates a download result
    public init(success: Bool, localURL: URL? = nil, error: Error? = nil) {
        self.success = success
        self.localURL = localURL
        self.error = error
    }
}

/// Information about a remote file
public struct RemoteFile {
    /// Path to the file
    public let path: String
    
    /// Size of the file in bytes
    public let size: Int64
    
    /// Last modified time
    public let lastModified: Date
    
    /// MIME type of the file
    public let contentType: String?
    
    /// Additional metadata
    public let metadata: [String: String]
    
    /// Creates a remote file
    public init(
        path: String,
        size: Int64,
        lastModified: Date,
        contentType: String? = nil,
        metadata: [String: String] = [:]
    ) {
        self.path = path
        self.size = size
        self.lastModified = lastModified
        self.contentType = contentType
        self.metadata = metadata
    }
}

/// Options for a sync operation
public struct SyncOptions {
    /// Local directory path to sync
    public var localPath: URL
    
    /// Maximum number of concurrent operations (overrides client configuration)
    public var maxConcurrentOperations: Int?
    
    /// Whether to delete files on remote that don't exist locally
    public var deleteOrphanedFiles: Bool?
    
    /// Regex pattern for files to include
    public var includePattern: String?
    
    /// Regex pattern for files to exclude
    public var excludePattern: String?
    
    /// If true, only report what would be done without making changes
    public var dryRun: Bool
    
    /// Specific paths to sync (relative to localPath)
    public var syncPaths: [String]?
    
    /// Creates sync options with the specified local path
    public init(
        localPath: URL,
        maxConcurrentOperations: Int? = nil,
        deleteOrphanedFiles: Bool? = nil,
        includePattern: String? = nil,
        excludePattern: String? = nil,
        dryRun: Bool = false,
        syncPaths: [String]? = nil
    ) {
        self.localPath = localPath
        self.maxConcurrentOperations = maxConcurrentOperations
        self.deleteOrphanedFiles = deleteOrphanedFiles
        self.includePattern = includePattern
        self.excludePattern = excludePattern
        self.dryRun = dryRun
        self.syncPaths = syncPaths
    }
}

/// Handler for receiving sync progress updates
public typealias SyncProgressHandler = (SyncProgress) -> Void

/// Progress of a sync operation
public struct SyncProgress {
    /// Current operation type
    public let operation: SyncOperation
    
    /// Total number of files to process
    public let totalFiles: Int
    
    /// Number of files processed so far
    public let processedFiles: Int
    
    /// Current file being processed
    public let currentFile: String?
    
    /// Percentage complete (0-100)
    public let percentComplete: Double
    
    /// Creates a sync progress
    public init(
        operation: SyncOperation,
        totalFiles: Int,
        processedFiles: Int,
        currentFile: String? = nil
    ) {
        self.operation = operation
        self.totalFiles = totalFiles
        self.processedFiles = processedFiles
        self.currentFile = currentFile
        self.percentComplete = totalFiles > 0 ? Double(processedFiles) * 100.0 / Double(totalFiles) : 0
    }
}

/// Protocol for interacting with a storage provider
public protocol StorageProvider {
    /// Provider type identifier
    var providerType: StorageProviderType { get }
    
    /// Connect to the storage provider
    func connect() async throws -> Bool
    
    /// Test connection to the provider
    func testConnection() async throws -> ConnectionStatus
    
    /// Sync files between local and remote storage
    func sync(options: SyncOptions, progressHandler: SyncProgressHandler?) async throws -> SyncResult
    
    /// Upload a file to remote storage
    func uploadFile(localURL: URL, remotePath: String?) async throws -> UploadResult
    
    /// Download a file from remote storage
    func downloadFile(remotePath: String, localURL: URL) async throws -> DownloadResult
    
    /// Delete a file from remote storage
    func deleteFile(remotePath: String) async throws -> Bool
    
    /// List files in remote storage
    func listFiles(path: String?) async throws -> [RemoteFile]
    
    /// Get a public URL for a file
    func getPublicURL(remotePath: String) throws -> URL
    
    /// Generate tokens for access control (if supported)
    func generateAccessToken(options: AccessTokenOptions) throws -> String?
}