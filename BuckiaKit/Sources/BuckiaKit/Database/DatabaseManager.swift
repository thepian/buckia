import Foundation
import SQLite
import Logging

private let logger = Logger(label: "com.buckia.DatabaseManager")

/// Manages SQLite database operations, backups, and synchronization
public final class DatabaseManager {
    /// Folder structure configuration
    private let folderStructure: FolderStructureConfiguration
    
    /// Primary database connection
    private var database: Connection?
    
    /// Creates a new database manager for the specified folder structure
    public init(folderStructure: FolderStructureConfiguration) {
        self.folderStructure = folderStructure
    }
    
    /// Opens the primary database connection
    public func openDatabase() throws -> Connection {
        if let database = database {
            return database
        }
        
        // Ensure folders exist
        let _ = try folderStructure.ensureFolderStructure()
        
        // Primary database path is in App Support
        let primaryDbPath = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("BuckiaDatabase.sqlite")
        
        // Open connection
        do {
            let db = try Connection(primaryDbPath.path)
            self.database = db
            return db
        } catch {
            logger.error("Failed to open database: \(error)")
            throw BuckiaError.databaseError("Failed to open database: \(error)")
        }
    }
    
    /// Backs up the primary database to the backup file
    /// Uses APFS Copy-on-Write when available for instant backups
    public func backupDatabase() async throws {
        // Ensure database is closed for clean backup
        try closeDatabase()
        
        // Primary database path
        let primaryDbPath = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("BuckiaDatabase.sqlite")
        
        // Backup database path
        let backupDbPath = folderStructure.backupDatabasePath
        
        // Ensure backup directory exists
        try FileManager.default.createDirectory(at: backupDbPath.deletingLastPathComponent(), withIntermediateDirectories: true)
        
        // Use APFS cloning when available (macOS)
        #if os(macOS)
        if #available(macOS 10.15, *) {
            let fileManager = FileManager.default
            
            // Check if source file exists
            guard fileManager.fileExists(atPath: primaryDbPath.path) else {
                throw BuckiaError.fileOperationFailed("Primary database does not exist")
            }
            
            // Remove existing backup if it exists
            if fileManager.fileExists(atPath: backupDbPath.path) {
                try fileManager.removeItem(at: backupDbPath)
            }
            
            // On macOS, use standard copy (filesystem will use CoW if available)
            try fileManager.copyItem(at: primaryDbPath, to: backupDbPath)
            
            logger.info("Database backed up using APFS")
            return
        }
        #endif
        
        // Fallback for non-APFS or older systems
        do {
            try FileManager.default.copyItem(at: primaryDbPath, to: backupDbPath)
            logger.info("Database backed up using standard file copy")
        } catch {
            logger.error("Failed to backup database: \(error)")
            throw BuckiaError.fileOperationFailed("Failed to backup database: \(error)")
        }
    }
    
    /// Restores the database from the backup file
    public func restoreFromBackup() async throws {
        // Ensure database is closed for clean restore
        try closeDatabase()
        
        // Primary database path
        let primaryDbPath = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("BuckiaDatabase.sqlite")
        
        // Backup database path
        let backupDbPath = folderStructure.backupDatabasePath
        
        guard FileManager.default.fileExists(atPath: backupDbPath.path) else {
            throw BuckiaError.fileOperationFailed("Backup database does not exist")
        }
        
        // Remove existing database
        if FileManager.default.fileExists(atPath: primaryDbPath.path) {
            try FileManager.default.removeItem(at: primaryDbPath)
        }
        
        // Copy backup to primary database
        try FileManager.default.copyItem(at: backupDbPath, to: primaryDbPath)
        
        logger.info("Database restored from backup")
    }
    
    /// Processes new database diff files in the inbound folder
    public func processInboundChanges() async throws -> [AppliedChange] {
        // Get list of diff files
        let inboundPath = folderStructure.inboundPath
        let fileManager = FileManager.default
        
        guard fileManager.fileExists(atPath: inboundPath.path) else {
            throw BuckiaError.fileOperationFailed("Inbound directory does not exist")
        }
        
        let diffFiles = try fileManager.contentsOfDirectory(at: inboundPath, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "sqlite" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        
        var appliedChanges: [AppliedChange] = []
        
        // Process each diff file
        for diffFile in diffFiles {
            do {
                let change = try await applyDiffFile(diffFile)
                appliedChanges.append(change)
                
                // Optional: Delete applied diff file
                try fileManager.removeItem(at: diffFile)
            } catch {
                logger.error("Failed to apply diff file \(diffFile.lastPathComponent): \(error)")
                // Continue with next file
            }
        }
        
        return appliedChanges
    }
    
    /// Creates a database diff for sharing with other users
    public func createDatabaseDiff(for changes: [String: Any]) async throws -> URL {
        // Create a new temp database for the diff
        let diffId = UUID().uuidString
        let diffPath = folderStructure.inboundPath.appendingPathComponent("\(diffId).sqlite")
        
        // Create directory if needed
        try FileManager.default.createDirectory(at: diffPath.deletingLastPathComponent(), withIntermediateDirectories: true)
        
        // Create connection to diff database
        let diffDb = try Connection(diffPath.path)
        
        // Create diff metadata table
        try diffDb.execute("""
            CREATE TABLE diff_metadata (
                id TEXT PRIMARY KEY,
                created_at INTEGER,
                type TEXT,
                user_id TEXT
            )
        """)
        
        // Insert metadata
        let stmt = try diffDb.prepare("""
            INSERT INTO diff_metadata (id, created_at, type, user_id)
            VALUES (?, ?, ?, ?)
        """)
        try stmt.run(diffId, Date().timeIntervalSince1970, "changes", folderStructure.userId)
        
        // Create changes table
        try diffDb.execute("""
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
            
            let stmt = try diffDb.prepare("""
                INSERT INTO changes (id, path, value, type)
                VALUES (?, ?, ?, ?)
            """)
            try stmt.run(changeId, path, valueJson, "update")
        }
        
        return diffPath
    }
    
    /// Apply a single diff file
    private func applyDiffFile(_ diffPath: URL) async throws -> AppliedChange {
        guard let primaryDb = try? openDatabase() else {
            throw BuckiaError.databaseError("Cannot open primary database")
        }
        
        // Open diff database
        let diffDb = try Connection(diffPath.path)
        
        // Get diff metadata
        let metadata = try diffDb.prepare("SELECT id, created_at, type, user_id FROM diff_metadata LIMIT 1").map { row -> [String: Any] in
            return [
                "id": row[0] as! String,
                "created_at": row[1] as! Double,
                "type": row[2] as! String,
                "user_id": row[3] as! String
            ]
        }.first ?? [:]
        
        guard !metadata.isEmpty else {
            throw BuckiaError.databaseError("Invalid diff file: missing metadata")
        }
        
        // Start transaction
        try primaryDb.execute("BEGIN TRANSACTION")
        
        do {
            // Create applied_changes table if not exists
            try primaryDb.execute("""
                CREATE TABLE IF NOT EXISTS applied_changes (
                    id TEXT PRIMARY KEY,
                    diff_id TEXT,
                    applied_at INTEGER,
                    user_id TEXT
                )
            """)
            
            // Check if diff already applied
            let diffId = metadata["id"] as! String
            let alreadyApplied = try primaryDb.scalar("SELECT COUNT(*) FROM applied_changes WHERE diff_id = ?", [diffId]) as? Int64 ?? 0 > 0
            
            if alreadyApplied {
                try primaryDb.execute("ROLLBACK")
                return AppliedChange(
                    diffId: diffId,
                    userId: metadata["user_id"] as! String,
                    appliedAt: Date(),
                    changeCount: 0,
                    status: .alreadyApplied
                )
            }
            
            // Get changes
            let changes = try diffDb.prepare("SELECT id, path, value, type FROM changes").map { row -> [String: Any] in
                return [
                    "id": row[0] as! String,
                    "path": row[1] as! String,
                    "value": row[2] as! String,
                    "type": row[3] as! String
                ]
            }
            
            // Apply each change
            var appliedCount = 0
            
            for change in changes {
                let path = change["path"] as! String
                let valueJson = change["value"] as! String
                let type = change["type"] as! String
                
                // Parse JSON value
                let value = try JSONSerialization.jsonObject(with: Data(valueJson.utf8))
                
                // Apply change based on path and type
                switch type {
                case "update":
                    // Implementation depends on the specific structure of your database
                    // This is a simplified example
                    if path.starts(with: "table/") {
                        let components = path.components(separatedBy: "/")
                        let tableName = components[1]
                        let recordId = components[2]
                        
                        if let valueDict = value as? [String: Any] {
                            // Update record
                            // This is simplified - actual implementation would depend on schema
                            try updateRecord(in: primaryDb, tableName: tableName, recordId: recordId, values: valueDict)
                            appliedCount += 1
                        }
                    }
                    
                case "insert", "delete":
                    // Implementation for other change types
                    // ...
                    appliedCount += 1
                    
                default:
                    logger.warning("Unknown change type: \(type)")
                }
            }
            
            // Record that we applied this diff
            let stmt = try primaryDb.prepare("""
                INSERT INTO applied_changes (id, diff_id, applied_at, user_id)
                VALUES (?, ?, ?, ?)
            """)
            try stmt.run(UUID().uuidString, diffId, Date().timeIntervalSince1970, metadata["user_id"] as! String)
            
            // Commit transaction
            try primaryDb.execute("COMMIT")
            
            return AppliedChange(
                diffId: diffId,
                userId: metadata["user_id"] as! String,
                appliedAt: Date(),
                changeCount: appliedCount,
                status: .applied
            )
        } catch {
            // Rollback on error
            try primaryDb.execute("ROLLBACK")
            throw BuckiaError.databaseError("Failed to apply diff: \(error)")
        }
    }
    
    /// Update a record in the database
    private func updateRecord(in db: Connection, tableName: String, recordId: String, values: [String: Any]) throws {
        // This is a simplified implementation that uses string interpolation
        // In a real app, you would use proper parameter binding and handle different column types
        
        // Create column assignments
        var assignments: [String] = []
        
        // Build value assignments with proper escaping
        for (column, value) in values {
            switch value {
            case let stringValue as String:
                assignments.append("\(column) = '\(stringValue.replacingOccurrences(of: "'", with: "''"))'")
            case let intValue as Int:
                assignments.append("\(column) = \(intValue)")
            case let doubleValue as Double:
                assignments.append("\(column) = \(doubleValue)")
            case let boolValue as Bool:
                assignments.append("\(column) = \(boolValue ? 1 : 0)")
            default:
                // Skip unsupported types
                logger.warning("Skipping unsupported value type for column \(column)")
            }
        }
        
        // Build update query with interpolated values
        // Note: In a real implementation, you would use proper binding for security
        let updateSQL = """
            UPDATE \(tableName)
            SET \(assignments.joined(separator: ", "))
            WHERE id = '\(recordId.replacingOccurrences(of: "'", with: "''"))'
        """
        
        // Execute the statement
        try db.execute(updateSQL)
    }
    
    /// Closes the database connection
    public func closeDatabase() throws {
        database = nil
    }
}

/// Status of an applied database change
public enum AppliedChangeStatus {
    case applied
    case alreadyApplied
    case failed
}

/// Result of applying a database change
public struct AppliedChange {
    /// ID of the diff that was applied
    public let diffId: String
    
    /// User ID that created the diff
    public let userId: String
    
    /// When the diff was applied
    public let appliedAt: Date
    
    /// Number of changes applied
    public let changeCount: Int
    
    /// Status of the application
    public let status: AppliedChangeStatus
}