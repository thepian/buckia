import Foundation

/// Options for generating access tokens
public struct AccessTokenOptions {
    /// User ID for user-specific tokens
    public var userId: String?
    
    /// Permissions for this token
    public var permissions: StoragePermissions
    
    /// Token expiration time
    public var expiry: TimeInterval
    
    /// Additional provider-specific options
    public var providerOptions: [String: Any]?
    
    /// Creates access token options
    public init(
        userId: String? = nil,
        permissions: StoragePermissions,
        expiry: TimeInterval,
        providerOptions: [String: Any]? = nil
    ) {
        self.userId = userId
        self.permissions = permissions
        self.expiry = expiry
        self.providerOptions = providerOptions
    }
}

/// Permissions for storage operations
public struct StoragePermissions: OptionSet, Codable {
    public let rawValue: Int
    
    public init(rawValue: Int) {
        self.rawValue = rawValue
    }
    
    public static let read = StoragePermissions(rawValue: 1 << 0)
    public static let write = StoragePermissions(rawValue: 1 << 1)
    public static let delete = StoragePermissions(rawValue: 1 << 2)
    public static let list = StoragePermissions(rawValue: 1 << 3)
    
    /// Full access (read, write, delete, list)
    public static let all: StoragePermissions = [.read, .write, .delete, .list]
    
    /// Read-only access (read, list)
    public static let readOnly: StoragePermissions = [.read, .list]
    
    /// Path restrictions for this permission set
    public var pathPrefix: String?
    
    /// Restrict permissions to a specific path prefix
    public func restrictToPath(_ path: String) -> StoragePermissions {
        var result = self
        result.pathPrefix = path
        return result
    }
    
    // Required for Codable conformance
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        rawValue = try container.decode(Int.self, forKey: .rawValue)
        pathPrefix = try container.decodeIfPresent(String.self, forKey: .pathPrefix)
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(rawValue, forKey: .rawValue)
        try container.encodeIfPresent(pathPrefix, forKey: .pathPrefix)
    }
    
    private enum CodingKeys: String, CodingKey {
        case rawValue
        case pathPrefix
    }
}

/// Metadata for a token
public struct TokenMetadata {
    /// User ID associated with the token
    public let userId: String?
    
    /// Permissions granted by the token
    public let permissions: StoragePermissions
    
    /// Expiration time of the token
    public let expiry: Date
    
    /// Additional metadata
    public let metadata: [String: Any]
    
    /// Creates token metadata
    public init(
        userId: String? = nil,
        permissions: StoragePermissions,
        expiry: Date,
        metadata: [String: Any] = [:]
    ) {
        self.userId = userId
        self.permissions = permissions
        self.expiry = expiry
        self.metadata = metadata
    }
}