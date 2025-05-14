import XCTest
import SQLite
@testable import BuckiaKit

final class DatabaseManagerTests: XCTestCase {
    
    // MARK: - Properties
    
    private var tempDirectory: URL!
    private var folderStructure: FolderStructureConfiguration!
    private var databaseManager: DatabaseManager!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create temp directory for tests
        tempDirectory = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("DatabaseManagerTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: tempDirectory, withIntermediateDirectories: true)
        
        // Create test folder structure
        folderStructure = FolderStructureConfiguration(
            userId: "test-user",
            baseLocation: .appSupport
        )
        
        // Initialize database manager
        databaseManager = DatabaseManager(folderStructure: folderStructure)
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
    
    // MARK: - Tests
    
    func testOpenDatabase() throws {
        // Open the database
        let db = try databaseManager.openDatabase()
        
        // Verify connection is valid
        XCTAssertNoThrow(try db.execute("SELECT 1"))
        
        // Try to create a table
        XCTAssertNoThrow(try db.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id TEXT PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """))
        
        // Insert data
        XCTAssertNoThrow(try {
            let stmt = try db.prepare("""
                INSERT INTO test_table (id, name, value)
                VALUES (?, ?, ?)
            """)
            try stmt.run(UUID().uuidString, "Test Name", 42)
        }())
        
        // Query data
        let count = try db.scalar("SELECT COUNT(*) FROM test_table") as? Int64
        XCTAssertEqual(count, 1)
    }
    
    func testBackupAndRestoreDatabase() async throws {
        // Open database and create test data
        let db = try databaseManager.openDatabase()
        
        try db.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id TEXT PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        
        let testId = UUID().uuidString
        let insertStmt = try db.prepare("""
            INSERT INTO test_table (id, name, value)
            VALUES (?, ?, ?)
        """)
        try insertStmt.run(testId, "Backup Test", 100)
        
        // Create backup
        try await databaseManager.backupDatabase()
        
        // Verify backup file exists
        let backupPath = folderStructure.backupDatabasePath
        XCTAssertTrue(FileManager.default.fileExists(atPath: backupPath.path))
        
        // Modify original database
        let updateStmt = try db.prepare("""
            UPDATE test_table SET value = ? WHERE id = ?
        """)
        try updateStmt.run(200, testId)
        
        // Verify modification
        let updatedValue = try db.scalar("SELECT value FROM test_table WHERE id = ?", [testId]) as? Int64
        XCTAssertEqual(updatedValue, 200)
        
        // Restore from backup
        try await databaseManager.restoreFromBackup()
        
        // Reopen database
        try databaseManager.closeDatabase()
        let restoredDb = try databaseManager.openDatabase()
        
        // Verify restored value
        let restoredValue = try restoredDb.scalar("SELECT value FROM test_table WHERE id = ?", [testId]) as? Int64
        XCTAssertEqual(restoredValue, 100, "Value should be restored from backup")
    }
    
    func testCreateDatabaseDiff() async throws {
        // Create test changes
        let changes: [String: Any] = [
            "table/users/user1": [
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            ],
            "table/settings/theme": [
                "darkMode": true,
                "fontSize": 16
            ]
        ]
        
        // Create diff
        let diffPath = try await databaseManager.createDatabaseDiff(for: changes)
        
        // Verify diff file exists
        XCTAssertTrue(FileManager.default.fileExists(atPath: diffPath.path))
        
        // Open diff database and verify structure
        let diffDb = try Connection(diffPath.path)
        
        // Check metadata table exists
        let metadataCount = try diffDb.scalar("SELECT COUNT(*) FROM diff_metadata") as? Int64
        XCTAssertEqual(metadataCount, 1)
        
        // Check changes table exists and has correct row count
        let changesCount = try diffDb.scalar("SELECT COUNT(*) FROM changes") as? Int64
        XCTAssertEqual(changesCount, 2)
        
        // Check content of changes
        let paths = try diffDb.prepare("SELECT path FROM changes").map { row in
            row[0] as! String
        }
        XCTAssertTrue(paths.contains("table/users/user1"))
        XCTAssertTrue(paths.contains("table/settings/theme"))
    }
    
    func testProcessInboundChanges() async throws {
        // Open database and create test schema
        let db = try databaseManager.openDatabase()
        
        try db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                age INTEGER
            )
        """)
        
        try db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                dark_mode INTEGER,
                font_size INTEGER
            )
        """)
        
        // Create diff with changes
        let changes: [String: Any] = [
            "table/users/user1": [
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            ],
            "table/settings/theme": [
                "dark_mode": 1,
                "font_size": 16
            ]
        ]
        
        // Create and place diff in inbound folder
        let _ = try await databaseManager.createDatabaseDiff(for: changes)
        
        // Process inbound changes
        let appliedChanges = try await databaseManager.processInboundChanges()
        
        // Verify changes were applied
        XCTAssertEqual(appliedChanges.count, 1)
        XCTAssertEqual(appliedChanges[0].status, .applied)
        
        // Verify changes were applied to the database
        // This requires the actual implementation of updateRecord to work with our test schema
        // For a real test, you would check the database state here
    }
    
    // MARK: - Performance Tests
    
    func testBackupPerformance() throws {
        // Open database and create large test dataset
        let db = try databaseManager.openDatabase()
        
        try db.execute("""
            CREATE TABLE IF NOT EXISTS performance_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        
        // Insert 1000 records with some data
        try db.transaction {
            for i in 0..<1000 {
                let stmt = try db.prepare("""
                    INSERT INTO performance_test (id, data)
                    VALUES (?, ?)
                """)
                try stmt.run(i, String(repeating: "x", count: 1000))
            }
        }
        
        // Measure backup performance
        measure {
            let expectation = XCTestExpectation(description: "Backup completes")
            
            Task {
                do {
                    try await databaseManager.backupDatabase()
                    expectation.fulfill()
                } catch {
                    XCTFail("Backup failed: \(error)")
                }
            }
            
            wait(for: [expectation], timeout: 5.0)
        }
    }
}