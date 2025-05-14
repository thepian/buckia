import Foundation
import CryptoKit
import Logging

private let logger = Logger(label: "com.buckia.BunnyTokenFactory")

/// Factory for generating Bunny.net specific tokens
public class BunnyTokenFactory: TokenFactory {
    /// Storage zone name
    private let storageZoneName: String
    
    /// Security key for token generation
    private let securityKey: String
    
    /// Initialize with storage zone details and security key
    public init(storageZoneName: String, securityKey: String) {
        self.storageZoneName = storageZoneName
        self.securityKey = securityKey
    }
    
    /// Generate a token for the specified options
    public func generateToken(options: AccessTokenOptions) throws -> String {
        // For Bunny.net, we'll use either CDN token or Storage token based on the options
        if let userId = options.userId {
            return try generateStorageToken(
                userId: userId,
                permissions: options.permissions,
                expiry: options.expiry
            )
        } else if let path = options.providerOptions?["path"] as? String {
            return try generateCDNToken(
                path: path,
                expiry: options.expiry,
                ip: options.providerOptions?["ip"] as? String,
                countries: options.providerOptions?["countries"] as? [String],
                countriesBlocked: options.providerOptions?["countriesBlocked"] as? [String],
                referrers: options.providerOptions?["referrers"] as? [String],
                speedLimit: options.providerOptions?["speedLimit"] as? Int
            )
        } else {
            throw BuckiaError.tokenError("Invalid options for Bunny.net token generation")
        }
    }
    
    /// Validate a Bunny.net token
    public func validateToken(_ token: String) throws -> Bool {
        // In a real implementation, we would validate the token structure
        // For now, we just return true if the token is not empty
        return !token.isEmpty
    }
    
    /// Parse a Bunny.net token to extract metadata
    public func parseToken(_ token: String) throws -> TokenMetadata {
        // This is a simplified implementation
        // In a real implementation, we would decode the token to extract the metadata
        throw BuckiaError.tokenError("Token parsing not implemented for Bunny.net")
    }
    
    /// Generate Bunny.net CDN token for protecting URLs
    /// Algorithm: Base64Encode(SHA256_RAW(token_security_key + signed_url + expiration + optional_parameters))
    public func generateCDNToken(
        path: String,
        expiry: TimeInterval,
        ip: String? = nil,
        countries: [String]? = nil,
        countriesBlocked: [String]? = nil,
        referrers: [String]? = nil,
        speedLimit: Int? = nil
    ) throws -> String {
        // Calculate expiration timestamp
        let expiryTimestamp = Int(Date().timeIntervalSince1970 + expiry)
        
        // Build the base string for hashing
        var baseString = securityKey + path + String(expiryTimestamp)
        
        // Add optional IP restriction
        if let ip = ip {
            baseString += ip
        }
        
        // Prepare query parameters (these must be sorted alphabetically)
        var queryParams: [String: String] = [:]
        
        // Add countries if specified
        if let countries = countries, !countries.isEmpty {
            queryParams["token_countries"] = countries.joined(separator: ",")
        }
        
        // Add blocked countries if specified
        if let countriesBlocked = countriesBlocked, !countriesBlocked.isEmpty {
            queryParams["token_countries_blocked"] = countriesBlocked.joined(separator: ",")
        }
        
        // Add referrers if specified
        if let referrers = referrers, !referrers.isEmpty {
            queryParams["token_referrers"] = referrers.joined(separator: ",")
        }
        
        // Add speed limit if specified
        if let speedLimit = speedLimit {
            queryParams["limit"] = String(speedLimit)
        }
        
        // Add query parameters to the base string (sorted alphabetically by key)
        if !queryParams.isEmpty {
            let sortedParams = queryParams.sorted(by: { $0.key < $1.key })
            let queryString = sortedParams.map { "\($0.key)=\($0.value)" }.joined(separator: "&")
            baseString += queryString
        }
        
        // Generate SHA256 hash
        guard let baseData = baseString.data(using: .utf8) else {
            throw BuckiaError.tokenError("Failed to convert string to data")
        }
        
        let hash = SHA256.hash(data: baseData)
        let hashData = Data(hash)
        
        // Base64 encode the hash
        var base64String = hashData.base64EncodedString()
        
        // Replace characters according to Bunny.net requirements
        base64String = base64String.replacingOccurrences(of: "\n", with: "")
        base64String = base64String.replacingOccurrences(of: "+", with: "-")
        base64String = base64String.replacingOccurrences(of: "/", with: "_")
        base64String = base64String.replacingOccurrences(of: "=", with: "")
        
        // Build final token with parameters
        var tokenParams = ["token": base64String, "expires": String(expiryTimestamp)]
        
        // Add other parameters
        tokenParams.merge(queryParams) { current, _ in current }
        
        // Construct query string version of the token
        let fullToken = tokenParams.map { "\($0.key)=\($0.value)" }.joined(separator: "&")
        
        return fullToken
    }
    
    /// Generate Bunny.net Storage API access token using the AccessKey
    public func generateStorageToken(
        userId: String,
        permissions: StoragePermissions,
        expiry: TimeInterval
    ) throws -> String {
        // Convert permissions to a format Bunny.net understands
        var permissionString = ""
        if permissions.contains(.read) { permissionString += "r" }
        if permissions.contains(.write) { permissionString += "w" }
        if permissions.contains(.delete) { permissionString += "d" }
        if permissions.contains(.list) { permissionString += "l" }
        
        // Calculate expiration timestamp
        let expiryTimestamp = Int(Date().timeIntervalSince1970 + expiry)
        
        // Create the token payload
        let payload: [String: Any] = [
            "storage_zone": storageZoneName,
            "user_id": userId,
            "permissions": permissionString,
            "path_prefix": permissions.pathPrefix ?? "/\(userId)/",
            "exp": expiryTimestamp
        ]
        
        // In a real implementation, we would sign this payload with the security key
        // For now, we'll just encode it as JSON and base64
        guard let payloadData = try? JSONSerialization.data(withJSONObject: payload) else {
            throw BuckiaError.tokenError("Failed to serialize token payload")
        }
        
        let base64Payload = payloadData.base64EncodedString()
        
        // In a real implementation, this would be a properly signed JWT
        // For simplicity, we'll prepend a header indicating this is a Bunny storage token
        return "bny_st_\(base64Payload)"
    }
}