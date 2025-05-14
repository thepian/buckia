# Swift Implementation for iOS/macOS

## Platform Requirements

- macOS 14+
- iOS 17+
- tvOS 17+
- Swift 5.9+

## Buckia Client

The `BuckiaClient` service is the main entry point for the Buckia library. It is used to interact with the Buckia Storage Bucket. The client is initialized with properties for the primary and fallback storage buckets.
To sync with a storage bucket, a token is needed. This requires the user to authenticate with an email/user-id and passkey. The token is stored in the Keychain and used for all requests to the storage bucket. The token is automatically refreshed when it expires. It is stored in the Keychain so it can be used with the web as well.

## Buckia folder structure

|- <user-id>
| | - backup.sqlite
| | - originals
| | - reworked
| | - inbound

The local file structure is managed by the Buckia library. The `user-id` folder is created when the user is created. This folder is used to store a local copy that can be sync'ed 1-to-1 with the user's folder in the Storage Bucket. The `backup.sqlite` file is a backup of the local SQLite database. It is used to restore the local database if needed. The `originals` folder holds the original recording files. The `reworked` folder holds the downscaled recordings for viewing. The `inbound` folder holds the incoming SQLite database diff files used to update the local database. This is used to send requests and shares between users.

The client App uses a local primary SQLite database(in App Support Folder) to store data and downscaled media thumbnails. New recordings are saved under `originals` and referenced in the database. When the App becomes inactive or goes to the background, the App calls the library to back up the database to the `backup.sqlite` in case changes have been made since the last backup. This will be done using APFS Copy-on-Write which is nearly instantanious. It should mean that there is no need to check if changes have been made since the last backup.

The local user folder can be configured to be stored under the App Support folder or the App Documents folder. If the folder isn't present, the other location is checked. If the folder is in the wrong location, it is moved to the correct location.

The `inbound` folder holds incremental changes to the local SQLite database. This is used to send requests and shares between users. These files are used to update the local database with changes from other users. The local DB has a table tracking past applied changes. The files are named using KSUIDs. This allows for quick sorting of files that have to be applied. The table definitions from the incoming DB file is used to adjust the local DB file. Additional tables are used to hold references to the changes.

## Buckia folder syncing

- List the filenames in `inbound` folder within the Storage Bucket. Download only IDs bigger than the last applied ID to the local `inbound` folder.
- Apply the changes to the local SQLite database. Drop applied files as needed to save space.
- Upload the `backup.sqlite` file to the Storage Bucket under the `user-id` folder.
- If enabled, upload new files in the `originals` folder to the Storage Bucket under the `user-id` folder.
- Upload new files in the `reworked` folder to the Storage Bucket under the `user-id` folder.

## Swift API Reference

### Provider Architecture

The Buckia Swift library is designed with a pluggable provider architecture that allows for different storage backends:

```swift
public protocol StorageProvider {
    /// Provider type identifier
    var providerType: StorageProviderType { get }
    
    /// Connect to the storage provider
    func connect() async throws -> Bool
    
    /// Test connection to the provider
    func testConnection() async throws -> ConnectionStatus
    
    /// Sync files between local and remote storage
    func sync(options: SyncOptions) async throws -> SyncResult
    
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

/// Supported storage provider types
public enum StorageProviderType: String, Codable {
    case bunny
    case b2
    case s3
    case local
    case custom
}
```

### BuckiaClient

The core Swift interface for interacting with Buckia storage:

```swift
public final class BuckiaClient {
    /// Creates a new Buckia client with the specified configuration
    public init(configuration: BuckiaConfiguration) async throws
    
    /// Tests the connection to the storage provider
    public func testConnection() async throws -> ConnectionStatus
    
    /// Performs a sync operation between local storage and remote storage
    public func sync(options: SyncOptions) async throws -> SyncResult
    
    /// Uploads a file to remote storage
    public func uploadFile(localURL: URL, remotePath: String?) async throws -> UploadResult
    
    /// Downloads a file from remote storage
    public func downloadFile(remotePath: String, localURL: URL) async throws -> DownloadResult
    
    /// Deletes a file from remote storage
    public func deleteFile(remotePath: String) async throws -> Bool
    
    /// Lists files in remote storage
    public func listFiles(path: String? = nil) async throws -> [RemoteFile]
    
    /// Gets a public URL for a remote file
    public func getPublicURL(remotePath: String) throws -> URL
}
```

### Configuration

```swift
public struct BuckiaConfiguration {
    /// Storage provider type (e.g., Bunny, B2)
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
}
```

### Authentication and Token Management

The Swift API supports multiple authentication methods including Okta integration and provider-specific token authentication:

```swift
public struct AuthenticationConfiguration {
    /// Authentication method
    public var method: AuthenticationMethod
    
    /// Authentication credentials
    public var credentials: [String: String]?
    
    /// Token context name
    public var tokenContext: String?
    
    /// Creates an authentication configuration with API key
    public static func apiKey(_ key: String, context: String? = nil) -> AuthenticationConfiguration
    
    /// Creates an authentication configuration with Okta
    public static func okta(domain: String, clientId: String) -> AuthenticationConfiguration
    
    /// Creates provider-specific authentication
    public static func providerSpecific(type: StorageProviderType, credentials: [String: String]) -> AuthenticationConfiguration
}

public enum AuthenticationMethod: String, Codable {
    case apiKey
    case okta
    case oauth
    case awsSignature
    case token
    case none
}

public final class TokenManager {
    /// Shared instance of the token manager
    public static let shared = TokenManager()
    
    /// Saves a token for the specified context
    public func saveToken(_ token: String, for context: String) throws
    
    /// Retrieves a token for the specified context
    public func getToken(for context: String) throws -> String?
    
    /// Deletes a token for the specified context
    public func deleteToken(for context: String) throws
    
    /// Generates a Bunny CDN token for secure URL access
    public func generateBunnyToken(for path: String, 
                                  expiry: TimeInterval,
                                  ip: String? = nil,
                                  countries: [String]? = nil,
                                  referrers: [String]? = nil) throws -> String
                                  
    /// Generates a user-specific storage token for bucket synchronization
    public func generateUserStorageToken(userId: String,
                                       permissions: StoragePermissions,
                                       expiry: TimeInterval,
                                       provider: StorageProviderType) throws -> String
}

/// Provider-specific token factory to support multiple storage backends
public protocol TokenFactory {
    /// Generate access tokens appropriate for the specific provider
    func generateToken(options: AccessTokenOptions) throws -> String
    
    /// Validate a token for this provider
    func validateToken(_ token: String) throws -> Bool
    
    /// Parse a token to extract its permissions and metadata
    func parseToken(_ token: String) throws -> TokenMetadata
}

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
}
```

### Database Management

```swift
public final class DatabaseManager {
    /// Creates a new database manager for the specified folder structure
    public init(folderStructure: FolderStructureConfiguration)
    
    /// Backs up the primary database to the backup file
    /// Uses APFS Copy-on-Write when available for instant backups
    public func backupDatabase() async throws
    
    /// Processes new database diff files in the inbound folder
    public func processInboundChanges() async throws -> [AppliedChange]
    
    /// Creates a database diff for sharing with other users
    public func createDatabaseDiff(for changes: [String: Any]) async throws -> URL
}
```

### SwiftUI Integration

The Buckia API provides SwiftUI integration for seamless use in modern iOS/macOS apps:

```swift
/// Property wrapper to provide a Buckia client through the SwiftUI environment
@propertyWrapper
public struct BuckiaClient: DynamicProperty {
    /// Creates a Buckia client property wrapper with the specified configuration
    public init(configuration: BuckiaConfiguration)
    
    /// The wrapped value
    public var wrappedValue: BuckiaClient { get }
}

/// Environment values for Buckia
public extension EnvironmentValues {
    /// The Buckia client for the current environment
    var buckiaClient: BuckiaClient { get set }
    
    /// The current sync progress
    var syncProgress: SyncProgress? { get }
}
```

### Storage Permissions

The API includes a dedicated type for managing permissions on user-specific tokens:

```swift
public struct StoragePermissions: OptionSet {
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
    public func restrictToPath(_ path: String) -> StoragePermissions
}
```

### Usage Examples

#### Basic Client Setup and Sync

```swift
// Create a configuration
let config = BuckiaConfiguration(
    provider: .bunny,
    bucketName: "my-storage-zone",
    authConfig: .apiKey("your-api-key", context: "bunny")
)

// Initialize the client
do {
    let client = try await BuckiaClient(configuration: config)
    let connectionStatus = try await client.testConnection()
    
    // Sync files
    let options = SyncOptions(localPath: URL.documentsDirectory.appending(path: "UserData"))
    let result = try await client.sync(options: options)
    
    print("Files uploaded: \(result.filesUploaded)")
    print("Files downloaded: \(result.filesDownloaded)")
} catch {
    print("Error: \(error)")
}
```

## Provider-Specific Token Management

### Bunny.net Authentication and Token Management

Bunny.net offers different authentication mechanisms depending on which service you're accessing:

#### Authentication Methods

Bunny.net supports several authentication approaches:

1. **API Keys** - For general API access to storage zones and CDN management
2. **CDN Tokens** - For securing access to CDN content with fine-grained control
3. **Storage Access Keys** - For authenticating access to storage zones

According to the [Bunny.net documentation](https://docs.bunny.net/docs/cdn-token-authentication):

> "Bunny CDN provides a powerful token authentication system to strictly control who, where and for how long can access your content."

> "If enabled, token authentication will block all requests to your URLs unless a valid token is passed with the request. The token is then compared on our server and we check if both values match."

#### CDN Token Implementation

The CDN token authentication system provides strict control over content access using signed URLs. As the Bunny.net documentation explains:

> "The token is a Base64 encoded SHA256 hash based on the URL, expiration time and other parameters."

> "The signing process consists of the following parameters that need to be added to the URL: token (required), expires (required), token_path (optional), token_countries (optional), token_countries_blocked (optional), limit (optional)"

The Swift implementation follows this specification:

```swift
// Bunny.net specific token factory
public class BunnyTokenFactory: TokenFactory {
    /// Initialize with storage zone details and security key
    public init(storageZoneName: String, securityKey: String)
    
    /// Generate Bunny.net CDN token for protecting URLs
    /// Algorithm: Base64Encode(SHA256_RAW(token_security_key + signed_url + expiration + optional_parameters))
    public func generateCDNToken(path: String, 
                               expiry: TimeInterval,
                               ip: String? = nil,
                               countries: [String]? = nil,
                               countriesBlocked: [String]? = nil,
                               referrers: [String]? = nil,
                               speedLimit: Int? = nil) throws -> String
    
    /// Generate Bunny.net Storage API access token using the AccessKey
    public func generateStorageToken(userId: String,
                                   permissions: StoragePermissions,
                                   expiry: TimeInterval) throws -> String
}
```

#### Storage API Authentication

For the Storage API, Bunny.net requires an API key to be passed in the `AccessKey` header. According to the Bunny.net API documentation:

> "The API requests are authenticated using the **AccessKey** header. You can find it in your Video Library details page in the bunny.net dashboard."

The Swift implementation handles this authentication automatically:

```swift
public class BunnyStorageProvider: StorageProvider {
    /// Connect to the Bunny.net storage using the API key
    public func connect() async throws -> Bool {
        // Set the AccessKey header for all requests
        self.httpClient.defaultHeaders = [
            "AccessKey": self.apiKey,
            "Content-Type": "application/json"
        ]
        
        return try await testConnection().isConnected
    }
}
```

#### User Authentication Flow

When implementing user authentication with Bunny.net in your Swift application, the typical flow is:

1. **Initial Setup**: Application authenticates with Bunny.net using a master API key
2. **User Authentication**: User authenticates with your application (typically via Okta)
3. **Token Generation**: Your app generates a user-specific token with limited permissions
4. **Token Storage**: The token is securely stored in the keychain with an expiration
5. **Automatic Renewal**: The token is automatically refreshed before expiration

### Managing User-Specific Tokens

Each provider implementation follows these best practices for user token management:

1. **Token Generation**: Create tokens with the minimum permissions required
2. **Path Restrictions**: Limit access to user-specific paths (see `token_path` parameter)
3. **Short Expiration**: Use short-lived tokens that must be refreshed (via `expires` parameter)
4. **Token Rotation**: Support token rotation for security
5. **Secure Storage**: Store tokens securely in the keychain

#### Creating User-Specific Tokens for Syncing

```swift
// Generate a user-specific token for sync access
func createUserSyncToken(for userId: String, provider: StorageProviderType) async throws -> String {
    // Create permissions with path restrictions
    var permissions = StoragePermissions.readOnly
    permissions = permissions.restrictToPath("\(userId)/")
    
    // Add write permission only for inbound folder
    var inboundPermissions = StoragePermissions.write
    inboundPermissions = inboundPermissions.restrictToPath("\(userId)/inbound/")
    
    // Combine permissions
    let syncPermissions: StoragePermissions = [permissions, inboundPermissions]
    
    // Generate token that expires in 24 hours
    let expiry = TimeInterval(24 * 60 * 60)
    
    // Use the appropriate token manager based on the provider
    switch provider {
    case .bunny:
        // Bunny.net specific implementation
        let factory = BunnyTokenFactory(
            storageZoneName: "my-storage-zone",
            securityKey: try TokenManager.shared.getToken(for: "bunny-master-key")!
        )
        return try factory.generateStorageToken(
            userId: userId,
            permissions: syncPermissions,
            expiry: expiry
        )
        
    case .b2:
        // Backblaze B2 specific implementation
        // Uses a different token generation mechanism
        let factory = B2TokenFactory(
            applicationKeyId: try TokenManager.shared.getToken(for: "b2-key-id")!,
            applicationKey: try TokenManager.shared.getToken(for: "b2-app-key")!
        )
        return try factory.generateToken(options: AccessTokenOptions(
            userId: userId,
            permissions: syncPermissions,
            expiry: expiry,
            providerOptions: ["bucketName": "my-bucket"]
        ))
        
    default:
        // Generic implementation for other providers
        return try TokenManager.shared.generateUserStorageToken(
            userId: userId,
            permissions: syncPermissions,
            expiry: expiry,
            provider: provider
        )
    }
}

// Example of using the token for a specific user
let userId = "user123"
let syncToken = try await createUserSyncToken(for: userId, provider: .bunny)

// Configure client with user-specific token
let userConfig = BuckiaConfiguration(
    provider: .bunny,
    bucketName: "my-storage-zone",
    authConfig: .apiKey(syncToken, context: "user-\(userId)")
)

// For additional security, you can store the token with expiration metadata
try TokenManager.shared.saveToken(
    syncToken,
    for: "user-\(userId)",
    metadata: ["expires": Date().addingTimeInterval(24 * 60 * 60).timeIntervalSince1970]
)

let userClient = try await BuckiaClient(configuration: userConfig)
