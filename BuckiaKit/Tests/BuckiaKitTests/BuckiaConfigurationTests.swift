import XCTest
@testable import BuckiaKit

final class BuckiaConfigurationTests: XCTestCase {
    
    // MARK: - Properties
    
    private var tempDirectory: URL!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create temp directory for tests
        tempDirectory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("BuckiaConfigTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
    }
    
    override func tearDownWithError() throws {
        try super.tearDownWithError()
        
        // Clean up temp directory
        if let tempDirectory = tempDirectory, FileManager.default.fileExists(atPath: tempDirectory.path) {
            try FileManager.default.removeItem(at: tempDirectory)
        }
        
        tempDirectory = nil
    }
    
    // MARK: - Tests
    
    func testCreateConfigurationWithCode() {
        // Create configuration with all properties specified
        let config = BuckiaConfiguration(
            provider: .bunny,
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key"),
            maxConcurrentOperations: 10,
            deleteOrphanedFiles: true,
            includePatterns: ["*.jpg", "*.png"],
            excludePatterns: ["*.tmp"],
            folderStructure: FolderStructureConfiguration(
                userId: "test-user",
                baseLocation: .documents
            )
        )
        
        // Verify all properties
        XCTAssertEqual(config.provider, .bunny)
        XCTAssertEqual(config.bucketName, "test-bucket")
        XCTAssertEqual(config.authConfig.method, .apiKey)
        XCTAssertEqual(config.authConfig.credentials?["api_key"], "test-key")
        XCTAssertEqual(config.maxConcurrentOperations, 10)
        XCTAssertEqual(config.deleteOrphanedFiles, true)
        XCTAssertEqual(config.includePatterns, ["*.jpg", "*.png"])
        XCTAssertEqual(config.excludePatterns, ["*.tmp"])
        XCTAssertEqual(config.folderStructure.userId, "test-user")
        XCTAssertEqual(config.folderStructure.baseLocation, .documents)
    }
    
    func testCreateConfigurationWithDefaults() {
        // Create configuration with minimal properties (using defaults)
        let config = BuckiaConfiguration(
            provider: .local,
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key")
        )
        
        // Verify default values
        XCTAssertEqual(config.provider, .local)
        XCTAssertEqual(config.bucketName, "test-bucket")
        XCTAssertEqual(config.maxConcurrentOperations, 5) // Default value
        XCTAssertEqual(config.deleteOrphanedFiles, false) // Default value
        XCTAssertEqual(config.includePatterns, []) // Default value
        XCTAssertEqual(config.excludePatterns, []) // Default value
        XCTAssertEqual(config.folderStructure.userId, "test-bucket") // Default to bucket name
        XCTAssertEqual(config.folderStructure.baseLocation, .appSupport) // Default value
    }
    
    func testConfigurationSerialization() throws {
        // Create configuration to serialize
        let config = BuckiaConfiguration(
            provider: .bunny,
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key"),
            maxConcurrentOperations: 10,
            deleteOrphanedFiles: true,
            includePatterns: ["*.jpg", "*.png"],
            excludePatterns: ["*.tmp"],
            folderStructure: FolderStructureConfiguration(
                userId: "test-user",
                baseLocation: .documents
            )
        )
        
        // Serialize to JSON
        let tempURL = tempDirectory.appendingPathComponent("config.json")
        try config.save(to: tempURL)
        
        // Verify file exists
        XCTAssertTrue(FileManager.default.fileExists(atPath: tempURL.path))
        
        // Deserialize from JSON
        let loadedConfig = try BuckiaConfiguration.load(from: tempURL)
        
        // Verify all properties match
        XCTAssertEqual(loadedConfig.provider, config.provider)
        XCTAssertEqual(loadedConfig.bucketName, config.bucketName)
        XCTAssertEqual(loadedConfig.authConfig.method, config.authConfig.method)
        XCTAssertEqual(loadedConfig.authConfig.credentials?["api_key"], config.authConfig.credentials?["api_key"])
        XCTAssertEqual(loadedConfig.maxConcurrentOperations, config.maxConcurrentOperations)
        XCTAssertEqual(loadedConfig.deleteOrphanedFiles, config.deleteOrphanedFiles)
        XCTAssertEqual(loadedConfig.includePatterns, config.includePatterns)
        XCTAssertEqual(loadedConfig.excludePatterns, config.excludePatterns)
        XCTAssertEqual(loadedConfig.folderStructure.userId, config.folderStructure.userId)
        XCTAssertEqual(loadedConfig.folderStructure.baseLocation, config.folderStructure.baseLocation)
    }
    
    func testDifferentAuthenticationMethods() {
        // Test API Key authentication
        let apiKeyConfig = BuckiaConfiguration(
            provider: .bunny,
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key", context: "bunny")
        )
        XCTAssertEqual(apiKeyConfig.authConfig.method, .apiKey)
        XCTAssertEqual(apiKeyConfig.authConfig.credentials?["api_key"], "test-key")
        XCTAssertEqual(apiKeyConfig.authConfig.tokenContext, "bunny")
        
        // Test Okta authentication
        let oktaConfig = BuckiaConfiguration(
            provider: .bunny,
            bucketName: "test-bucket",
            authConfig: .okta(domain: "example.okta.com", clientId: "client123")
        )
        XCTAssertEqual(oktaConfig.authConfig.method, .okta)
        XCTAssertEqual(oktaConfig.authConfig.credentials?["domain"], "example.okta.com")
        XCTAssertEqual(oktaConfig.authConfig.credentials?["client_id"], "client123")
        
        // Test provider-specific authentication
        let providerSpecificConfig = BuckiaConfiguration(
            provider: .bunny,
            bucketName: "test-bucket",
            authConfig: .providerSpecific(type: .bunny, credentials: [
                "api_key": "test-key",
                "storage_zone": "test-zone"
            ])
        )
        XCTAssertEqual(providerSpecificConfig.authConfig.method, .apiKey)
        XCTAssertEqual(providerSpecificConfig.authConfig.credentials?["api_key"], "test-key")
        XCTAssertEqual(providerSpecificConfig.authConfig.credentials?["storage_zone"], "test-zone")
        XCTAssertEqual(providerSpecificConfig.authConfig.tokenContext, "bunny")
    }
    
    func testFolderStructure() {
        // Create folder structure
        let folderStructure = FolderStructureConfiguration(
            userId: "test-user",
            baseLocation: .documents
        )
        
        // Verify paths
        XCTAssertTrue(folderStructure.userFolderPath.path.contains("test-user"))
        XCTAssertTrue(folderStructure.backupDatabasePath.path.contains("backup.sqlite"))
        XCTAssertTrue(folderStructure.originalsPath.path.contains("originals"))
        XCTAssertTrue(folderStructure.reworkedPath.path.contains("reworked"))
        XCTAssertTrue(folderStructure.inboundPath.path.contains("inbound"))
        
        // Test base location
        XCTAssertEqual(folderStructure.baseLocation, .documents)
        
        // Test app support base location
        let appSupportFolderStructure = FolderStructureConfiguration(
            userId: "test-user",
            baseLocation: .appSupport
        )
        XCTAssertEqual(appSupportFolderStructure.baseLocation, .appSupport)
    }
}