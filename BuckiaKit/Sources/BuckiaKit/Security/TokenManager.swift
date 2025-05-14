import Foundation
import KeychainAccess
import Logging

private let logger = Logger(label: "com.buckia.TokenManager")

/// Manages API tokens and token IDs with secure storage.
public final class TokenManager {
    
    /// Shared instance of the token manager
    public static let shared = TokenManager()
    
    /// Keychain for token storage
    private let keychain: Keychain
    
    /// Token factory registry
    private var tokenFactories: [StorageProviderType: TokenFactory] = [:]
    
    /// Initialize token manager with default keychain
    public init() {
        self.keychain = Keychain(service: "com.buckia.tokens")
            .accessibility(.afterFirstUnlock)
    }
    
    /// Initialize token manager with custom keychain
    public init(keychain: Keychain) {
        self.keychain = keychain
    }
    
    /// Register a token factory for a provider type
    public func registerTokenFactory(_ factory: TokenFactory, for providerType: StorageProviderType) {
        tokenFactories[providerType] = factory
    }
    
    /// Saves a token for the specified context
    public func saveToken(_ token: String, for context: String) throws {
        do {
            try keychain.set(token, key: "token_\(context)")
            logger.info("Token saved for context: \(context)")
        } catch {
            logger.error("Failed to save token: \(error)")
            throw BuckiaError.tokenError("Failed to save token: \(error)")
        }
    }
    
    /// Saves a token with metadata for the specified context
    public func saveToken(_ token: String, for context: String, metadata: [String: Any]) throws {
        try saveToken(token, for: context)
        
        // Save metadata as JSON
        if !metadata.isEmpty {
            do {
                let metadataData = try JSONSerialization.data(withJSONObject: metadata)
                try keychain.set(metadataData, key: "meta_\(context)")
                logger.info("Token metadata saved for context: \(context)")
            } catch {
                logger.error("Failed to save token metadata: \(error)")
                throw BuckiaError.tokenError("Failed to save token metadata: \(error)")
            }
        }
    }
    
    /// Retrieves a token for the specified context
    public func getToken(for context: String) throws -> String? {
        do {
            let token = try keychain.getString("token_\(context)")
            
            // Check if token has metadata with expiration
            if let metadata = try getTokenMetadata(for: context),
               let expiryTimestamp = metadata["expires"] as? TimeInterval {
                
                let expiryDate = Date(timeIntervalSince1970: expiryTimestamp)
                if expiryDate < Date() {
                    logger.warning("Token for context \(context) has expired")
                    return nil
                }
            }
            
            return token
        } catch {
            logger.error("Failed to retrieve token: \(error)")
            throw BuckiaError.tokenError("Failed to retrieve token: \(error)")
        }
    }
    
    /// Retrieves token metadata for the specified context
    public func getTokenMetadata(for context: String) throws -> [String: Any]? {
        do {
            guard let metadataData = try keychain.getData("meta_\(context)") else {
                return nil
            }
            
            let metadata = try JSONSerialization.jsonObject(with: metadataData)
            return metadata as? [String: Any]
        } catch {
            logger.error("Failed to retrieve token metadata: \(error)")
            throw BuckiaError.tokenError("Failed to retrieve token metadata: \(error)")
        }
    }
    
    /// Deletes a token for the specified context
    public func deleteToken(for context: String) throws {
        do {
            try keychain.remove("token_\(context)")
            try? keychain.remove("meta_\(context)")
            logger.info("Token deleted for context: \(context)")
        } catch {
            logger.error("Failed to delete token: \(error)")
            throw BuckiaError.tokenError("Failed to delete token: \(error)")
        }
    }
    
    /// Lists all available bucket contexts
    public func listBucketContexts() throws -> [String] {
        // This is a simplified implementation since KeychainAccess
        // doesn't provide a way to list all keys
        // In a real implementation, you would keep track of saved contexts
        return []
    }
    
    /// Generates a user-specific storage token for bucket synchronization
    public func generateUserStorageToken(
        userId: String,
        permissions: StoragePermissions,
        expiry: TimeInterval,
        provider: StorageProviderType
    ) throws -> String {
        guard let factory = tokenFactories[provider] else {
            throw BuckiaError.tokenError("No token factory registered for provider: \(provider)")
        }
        
        let options = AccessTokenOptions(
            userId: userId,
            permissions: permissions,
            expiry: expiry
        )
        
        return try factory.generateToken(options: options)
    }
}