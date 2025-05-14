import XCTest
import SQLite
@testable import BuckiaKit

final class InboundChangesTests: XCTestCase {
    
    // MARK: - Properties
    
    private var tempDirectory: URL!
    private var folderStructure: FolderStructureConfiguration!
    private var databaseManager: DatabaseManager!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create temp directory for tests
        tempDirectory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("InboundChangesTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        
        // Create test folder structure
        folderStructure = FolderStructureConfiguration(
            userId: "test-user",
            baseLocation: .appSupport
        )
        
        // Initialize database manager
        databaseManager = DatabaseManager(folderStructure: folderStructure)
        
        // Set up test database
        let db = try databaseManager.openDatabase()
        
        // Create test tables
        try db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                content TEXT,
                timestamp INTEGER,
                sender_id TEXT,
                read INTEGER DEFAULT 0
            )
        """)
        
        try db.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT
            )
        """)
        
        // Create applied_changes table
        try db.execute("""
            CREATE TABLE IF NOT EXISTS applied_changes (
                id TEXT PRIMARY KEY,
                diff_id TEXT,
                applied_at INTEGER,
                user_id TEXT
            )
        """)
    }
    
    override func tearDownWithError() throws {
        try super.tearDownWithError()
        
        // Close database
        try databaseManager.closeDatabase()
        databaseManager = nil
        
        // Clean up temp directory
        if let tempDirectory = tempDirectory, FileManager.default.fileExists(atPath: tempDirectory.path) {
            try FileManager.default.removeItem(at: tempDirectory)
        }
        
        tempDirectory = nil
        folderStructure = nil
    }
    
    // MARK: - Helper Methods
    
    private func createInboundDiffFile(changes: [String: Any]) throws -> URL {
        // Ensure inbound directory exists
        let inboundPath = folderStructure.inboundPath
        try FileManager.default.createDirectory(at: inboundPath, withIntermediateDirectories: true)
        
        // Create a diff file with a predictable name
        let diffId = UUID().uuidString
        let diffPath = inboundPath.appendingPathComponent("\(diffId).sqlite")
        
        // Create database
        let db = try Connection(diffPath.path)
        
        // Create metadata table
        try db.execute("""
            CREATE TABLE diff_metadata (
                id TEXT PRIMARY KEY,
                created_at INTEGER,
                type TEXT,
                user_id TEXT
            )
        """)
        
        // Insert metadata
        let metadataStmt = try db.prepare("""
            INSERT INTO diff_metadata (id, created_at, type, user_id)
            VALUES (?, ?, ?, ?)
        """)
        try metadataStmt.run(diffId, Date().timeIntervalSince1970, "changes", "sender-user")
        
        // Create changes table
        try db.execute("""
            CREATE TABLE changes (
                id TEXT PRIMARY KEY,
                path TEXT,
                value TEXT,
                type TEXT
            )
        """)
        
        // Insert changes
        for (path, value) in changes {
            let changeId = UUID().uuidString
            let valueJson = try String(data: JSONSerialization.data(withJSONObject: value), encoding: .utf8)!
            
            let changeStmt = try db.prepare("""
                INSERT INTO changes (id, path, value, type)
                VALUES (?, ?, ?, ?)
            """)
            try changeStmt.run(changeId, path, valueJson, "update")
        }
        
        return diffPath
    }
    
    // MARK: - Tests
    
    func testProcessMultipleInboundFiles() async throws {
        // Create first diff file with message changes
        let messageChanges: [String: Any] = [
            "table/messages/msg1": [
                "content": "Hello from user1",
                "timestamp": Date().timeIntervalSince1970,
                "sender_id": "user1",
                "read": 0
            ],
            "table/messages/msg2": [
                "content": "How are you?",
                "timestamp": Date().timeIntervalSince1970 + 60,
                "sender_id": "user1",
                "read": 0
            ]
        ]
        
        let _ = try createInboundDiffFile(changes: messageChanges)
        
        // Create second diff file with contact changes
        let contactChanges: [String: Any] = [
            "table/contacts/contact1": [
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-1234"
            ]
        ]
        
        let _ = try createInboundDiffFile(changes: contactChanges)
        
        // Process inbound changes
        let appliedChanges = try await databaseManager.processInboundChanges()
        
        // Verify multiple changes were processed
        XCTAssertEqual(appliedChanges.count, 2)
        
        // Verify all changes were applied
        for change in appliedChanges {
            XCTAssertEqual(change.status, .applied)
            XCTAssertEqual(change.userId, "sender-user")
        }
    }
    
    func testIdempotentProcessing() async throws {
        // Create a diff file
        let changes: [String: Any] = [
            "table/messages/msg1": [
                "content": "Hello there",
                "timestamp": Date().timeIntervalSince1970,
                "sender_id": "user1",
                "read": 0
            ]
        ]
        
        let diffPath = try createInboundDiffFile(changes: changes)
        
        // Process changes first time
        var appliedChanges = try await databaseManager.processInboundChanges()
        XCTAssertEqual(appliedChanges.count, 1)
        XCTAssertEqual(appliedChanges[0].status, .applied)
        
        // Recreate the same diff file with same ID
        let diffInfo = try Connection(diffPath.path).prepare("SELECT id FROM diff_metadata LIMIT 1").map { row in
            row[0] as! String
        }.first!
        
        // Create a new copy of the same diff
        let newDiffPath = folderStructure.inboundPath.appendingPathComponent("\(diffInfo)-copy.sqlite")
        try FileManager.default.copyItem(at: diffPath, to: newDiffPath)
        
        // Process changes second time
        appliedChanges = try await databaseManager.processInboundChanges()
        
        // Should be flagged as already applied (idempotent)
        XCTAssertEqual(appliedChanges.count, 1)
        XCTAssertEqual(appliedChanges[0].status, .alreadyApplied)
    }
    
    func testPartialProcessing() async throws {
        // Create a valid diff file
        let validChanges: [String: Any] = [
            "table/messages/msg1": [
                "content": "Valid message",
                "timestamp": Date().timeIntervalSince1970,
                "sender_id": "user1",
                "read": 0
            ]
        ]
        
        let _ = try createInboundDiffFile(changes: validChanges)
        
        // Create an invalid diff file (missing metadata)
        let invalidDiffPath = folderStructure.inboundPath.appendingPathComponent("invalid.sqlite")
        let invalidDb = try Connection(invalidDiffPath.path)
        
        // Only create changes table without metadata
        try invalidDb.execute("""
            CREATE TABLE changes (
                id TEXT PRIMARY KEY,
                path TEXT,
                value TEXT,
                type TEXT
            )
        """)
        
        // Process should succeed for valid file but skip invalid
        let appliedChanges = try await databaseManager.processInboundChanges()
        
        // Only the valid diff should be processed
        XCTAssertEqual(appliedChanges.count, 1)
    }
    
    func testParallelProcessing() async throws {
        // Create 5 different diff files
        for i in 1...5 {
            let changes: [String: Any] = [
                "table/messages/msg\(i)": [
                    "content": "Message \(i)",
                    "timestamp": Date().timeIntervalSince1970 + Double(i),
                    "sender_id": "user\(i)",
                    "read": 0
                ]
            ]
            
            let _ = try createInboundDiffFile(changes: changes)
        }
        
        // Process changes in parallel
        let task1 = Task {
            try await databaseManager.processInboundChanges()
        }
        
        let task2 = Task {
            try await databaseManager.processInboundChanges()
        }
        
        // Get results
        let result1 = try await task1.value
        let result2 = try await task2.value
        
        // Combined, we should have processed all 5 diffs
        // Some may be in result1, others in result2
        XCTAssertEqual(result1.count + result2.count, 5)
        
        // All should be applied or already applied
        for change in result1 + result2 {
            XCTAssertTrue(change.status == .applied || change.status == .alreadyApplied)
        }
    }
}