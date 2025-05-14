import Foundation

/// Errors that can occur in the Buckia library
public enum BuckiaError: Error, CustomStringConvertible, LocalizedError {
    /// Authentication failed
    case authenticationFailed(String)
    
    /// Connection to the storage provider failed
    case connectionFailed(String)
    
    /// File operation failed
    case fileOperationFailed(String)
    
    /// Synchronization failed
    case syncFailed(String)
    
    /// Configuration error
    case configurationError(String)
    
    /// Token management error
    case tokenError(String)
    
    /// Database error
    case databaseError(String)
    
    /// Network error
    case networkError(String)
    
    /// Validation error
    case validationError(String)
    
    /// Unknown error
    case unknown(String)
    
    public var description: String {
        switch self {
        case .authenticationFailed(let message):
            return "Authentication failed: \(message)"
        case .connectionFailed(let message):
            return "Connection failed: \(message)"
        case .fileOperationFailed(let message):
            return "File operation failed: \(message)"
        case .syncFailed(let message):
            return "Sync failed: \(message)"
        case .configurationError(let message):
            return "Configuration error: \(message)"
        case .tokenError(let message):
            return "Token error: \(message)"
        case .databaseError(let message):
            return "Database error: \(message)"
        case .networkError(let message):
            return "Network error: \(message)"
        case .validationError(let message):
            return "Validation error: \(message)"
        case .unknown(let message):
            return "Unknown error: \(message)"
        }
    }
    
    public var errorDescription: String? {
        description
    }
}