import Foundation

/// Configuration for the Buckia client
public struct BuckiaConfiguration: Codable {
    /// Storage provider type
    public var provider: StorageProviderType
    
    /// Bucket or storage zone name
    public var bucketName: String
    
    /// Authentication configuration
    public var authConfig: AuthenticationConfiguration
    
    /// Maximum number of concurrent operations
    public var maxConcurrentOperations: Int
    
    /// Whether to delete orphaned files during sync
    public var deleteOrphanedFiles: Bool
    
    /// File patterns to include in sync operations
    public var includePatterns: [String]
    
    /// File patterns to exclude from sync operations
    public var excludePatterns: [String]
    
    /// Local folder structure configuration
    public var folderStructure: FolderStructureConfiguration
    
    /// Creates a configuration with the specified parameters
    public init(
        provider: StorageProviderType,
        bucketName: String,
        authConfig: AuthenticationConfiguration,
        maxConcurrentOperations: Int = 5,
        deleteOrphanedFiles: Bool = false,
        includePatterns: [String] = [],
        excludePatterns: [String] = [],
        folderStructure: FolderStructureConfiguration? = nil
    ) {
        self.provider = provider
        self.bucketName = bucketName
        self.authConfig = authConfig
        self.maxConcurrentOperations = maxConcurrentOperations
        self.deleteOrphanedFiles = deleteOrphanedFiles
        self.includePatterns = includePatterns
        self.excludePatterns = excludePatterns
        
        // If no folder structure is provided, create a default one with the bucket name as user ID
        self.folderStructure = folderStructure ?? FolderStructureConfiguration(userId: bucketName)
    }
    
    /// Creates a configuration from a JSON file
    public static func load(from url: URL) throws -> BuckiaConfiguration {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        return try decoder.decode(BuckiaConfiguration.self, from: data)
    }
    
    /// Saves this configuration to a JSON file
    public func save(to url: URL) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(self)
        try data.write(to: url)
    }
}

/// Configuration for the folder structure
public struct FolderStructureConfiguration: Codable {
    /// Base location for the user folder
    public var baseLocation: FolderBaseLocation
    
    /// User ID for the folder name
    public var userId: String
    
    /// Creates a folder structure configuration
    public init(userId: String, baseLocation: FolderBaseLocation = .appSupport) {
        self.userId = userId
        self.baseLocation = baseLocation
    }
    
    /// Gets the path to the user folder
    public var userFolderPath: URL {
        baseLocation.url.appendingPathComponent(userId, isDirectory: true)
    }
    
    /// Gets the path to the backup SQLite file
    public var backupDatabasePath: URL {
        userFolderPath.appendingPathComponent("backup.sqlite")
    }
    
    /// Gets the path to the originals folder
    public var originalsPath: URL {
        userFolderPath.appendingPathComponent("originals", isDirectory: true)
    }
    
    /// Gets the path to the reworked folder
    public var reworkedPath: URL {
        userFolderPath.appendingPathComponent("reworked", isDirectory: true)
    }
    
    /// Gets the path to the inbound folder
    public var inboundPath: URL {
        userFolderPath.appendingPathComponent("inbound", isDirectory: true)
    }
    
    /// Ensures the folder structure exists, creating it if necessary
    public func ensureFolderStructure() throws -> URL {
        let fileManager = FileManager.default
        
        // Check if the folder exists in the primary location
        if fileManager.fileExists(atPath: userFolderPath.path) {
            return userFolderPath
        }
        
        // Check if the folder exists in the alternate location
        let alternatePath = (baseLocation == .appSupport ? FolderBaseLocation.documents : FolderBaseLocation.appSupport).url
            .appendingPathComponent(userId, isDirectory: true)
        
        if fileManager.fileExists(atPath: alternatePath.path) {
            // Move the folder to the preferred location
            try fileManager.moveItem(at: alternatePath, to: userFolderPath)
            return userFolderPath
        }
        
        // Create the folder structure
        try fileManager.createDirectory(at: userFolderPath, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: originalsPath, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: reworkedPath, withIntermediateDirectories: true)
        try fileManager.createDirectory(at: inboundPath, withIntermediateDirectories: true)
        
        return userFolderPath
    }
}

/// Base locations for the user folder
public enum FolderBaseLocation: String, Codable {
    case appSupport
    case documents
    
    /// Gets the URL for the base location
    public var url: URL {
        switch self {
        case .appSupport:
            return FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        case .documents:
            return FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        }
    }
}