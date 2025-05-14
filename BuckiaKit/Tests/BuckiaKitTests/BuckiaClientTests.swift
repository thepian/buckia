import XCTest
@testable import BuckiaKit

final class BuckiaClientTests: XCTestCase {
    
    // MARK: - Properties
    
    private var validConfig: BuckiaConfiguration!
    private var tempDirectory: URL!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create temp directory for tests
        tempDirectory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("BuckiaClientTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        
        // Create valid configuration for local provider (for tests)
        validConfig = BuckiaConfiguration(
            provider: .local,
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key"),
            folderStructure: FolderStructureConfiguration(
                userId: "test-user",
                baseLocation: .appSupport
            )
        )
    }
    
    override func tearDownWithError() throws {
        try super.tearDownWithError()
        
        // Clean up temp directory
        if let tempDirectory = tempDirectory, FileManager.default.fileExists(atPath: tempDirectory.path) {
            try FileManager.default.removeItem(at: tempDirectory)
        }
        
        validConfig = nil
        tempDirectory = nil
    }
    
    // MARK: - Tests
    
    func testInitWithValidConfiguration() async throws {
        // Test initialization with valid configuration
        let client = try await BuckiaClient(configuration: validConfig)
        
        XCTAssertEqual(client.config.provider, .local)
        XCTAssertEqual(client.config.bucketName, "test-bucket")
        XCTAssertEqual(client.config.authConfig.method, .apiKey)
    }
    
    func testInitWithInvalidProvider() async throws {
        // Create configuration with unsupported provider
        let invalidConfig = BuckiaConfiguration(
            provider: .b2,  // Not implemented yet
            bucketName: "test-bucket",
            authConfig: .apiKey("test-key")
        )
        
        // Expect an error during initialization
        do {
            _ = try await BuckiaClient(configuration: invalidConfig)
            XCTFail("Should throw an error for unimplemented provider")
        } catch let error as BuckiaError {
            XCTAssertEqual(String(describing: error).contains("not implemented"), true)
        }
    }
    
    func testTestConnection() async throws {
        // Initialize client
        let client = try await BuckiaClient(configuration: validConfig)
        
        // Test connection
        let status = try await client.testConnection()
        XCTAssertTrue(status.isConnected)
    }
    
    func testUpdateConfiguration() async throws {
        // Initialize client
        let client = try await BuckiaClient(configuration: validConfig)
        
        // Create updated configuration (same provider type)
        let updatedConfig = BuckiaConfiguration(
            provider: .local,
            bucketName: "updated-bucket",
            authConfig: .apiKey("updated-key")
        )
        
        // Update configuration
        try await client.updateConfiguration(updatedConfig)
        
        // Verify configuration was updated
        XCTAssertEqual(client.config.bucketName, "updated-bucket")
    }
    
    func testUpdateConfigurationWithDifferentProvider() async throws {
        // Initialize client
        let client = try await BuckiaClient(configuration: validConfig)
        
        // Create updated configuration with different provider type
        let updatedConfig = BuckiaConfiguration(
            provider: .bunny,  // Different provider
            bucketName: "updated-bucket",
            authConfig: .apiKey("updated-key")
        )
        
        // Expect an error when trying to change provider type
        do {
            try await client.updateConfiguration(updatedConfig)
            XCTFail("Should throw an error when changing provider type")
        } catch let error as BuckiaError {
            XCTAssertEqual(String(describing: error).contains("Cannot change provider"), true)
        }
    }
    
    func testBasicClientOperations() async throws {
        // Initialize client
        let client = try await BuckiaClient(configuration: validConfig)
        
        // Create a test file
        let testFileURL = tempDirectory.appendingPathComponent("test.txt")
        try "Test content".write(to: testFileURL, atomically: true, encoding: .utf8)
        
        // Test upload
        let uploadResult = try await client.uploadFile(localURL: testFileURL)
        XCTAssertTrue(uploadResult.success)
        
        // Test list files
        let files = try await client.listFiles()
        XCTAssertTrue(files.contains { $0.path.contains("test.txt") })
        
        // Test download
        let downloadURL = tempDirectory.appendingPathComponent("downloaded.txt")
        let downloadResult = try await client.downloadFile(remotePath: "test.txt", localURL: downloadURL)
        XCTAssertTrue(downloadResult.success)
        
        // Verify downloaded content
        let downloadedContent = try String(contentsOf: downloadURL, encoding: .utf8)
        XCTAssertEqual(downloadedContent, "Test content")
        
        // Test delete
        let deleteResult = try await client.deleteFile(remotePath: "test.txt")
        XCTAssertTrue(deleteResult)
        
        // Verify file was deleted
        let filesAfterDelete = try await client.listFiles()
        XCTAssertFalse(filesAfterDelete.contains { $0.path.contains("test.txt") })
        
        // Test cleanup
        await client.close()
    }
    
    func testClientAsyncSequence() async throws {
        // Initialize client
        let client = try await BuckiaClient(configuration: validConfig)
        
        // Use client with async/await syntax
        async let connectionStatus = client.testConnection()
        async let files = client.listFiles()
        
        // Wait for all operations to complete
        let (status, fileList) = try await (connectionStatus, files)
        
        XCTAssertTrue(status.isConnected)
        XCTAssertNotNil(fileList)
        
        // Test cleanup
        await client.close()
    }
}