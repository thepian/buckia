import Foundation

/// Factory for creating provider-specific tokens
public protocol TokenFactory {
    /// Generate access tokens appropriate for the specific provider
    func generateToken(options: AccessTokenOptions) throws -> String
    
    /// Validate a token for this provider
    func validateToken(_ token: String) throws -> Bool
    
    /// Parse a token to extract its permissions and metadata
    func parseToken(_ token: String) throws -> TokenMetadata
}

/// Authentication methods supported by providers
public enum AuthenticationMethod: String, Codable {
    case apiKey
    case okta
    case oauth
    case awsSignature
    case token
    case none
}

/// Configuration for authentication
public struct AuthenticationConfiguration: Codable {
    /// Authentication method
    public var method: AuthenticationMethod
    
    /// Authentication credentials - storing as simple string dictionary for serialization
    public var credentials: [String: String]?
    
    /// Token context name
    public var tokenContext: String?
    
    /// Creates an authentication configuration
    public init(
        method: AuthenticationMethod,
        credentials: [String: String]? = nil,
        tokenContext: String? = nil
    ) {
        self.method = method
        self.credentials = credentials
        self.tokenContext = tokenContext
    }
    
    // Custom Codable implementation
    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        method = try container.decode(AuthenticationMethod.self, forKey: .method)
        credentials = try container.decodeIfPresent([String: String].self, forKey: .credentials)
        tokenContext = try container.decodeIfPresent(String.self, forKey: .tokenContext)
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(method, forKey: .method)
        try container.encodeIfPresent(credentials, forKey: .credentials)
        try container.encodeIfPresent(tokenContext, forKey: .tokenContext)
    }
    
    private enum CodingKeys: String, CodingKey {
        case method
        case credentials
        case tokenContext
    }
    
    /// Creates an authentication configuration with API key
    public static func apiKey(_ key: String, context: String? = nil) -> AuthenticationConfiguration {
        AuthenticationConfiguration(
            method: .apiKey,
            credentials: ["api_key": key],
            tokenContext: context
        )
    }
    
    /// Creates an authentication configuration with Okta
    public static func okta(domain: String, clientId: String) -> AuthenticationConfiguration {
        AuthenticationConfiguration(
            method: .okta,
            credentials: [
                "domain": domain,
                "client_id": clientId
            ]
        )
    }
    
    /// Creates provider-specific authentication
    public static func providerSpecific(
        type: StorageProviderType,
        credentials: [String: String]
    ) -> AuthenticationConfiguration {
        AuthenticationConfiguration(
            method: .apiKey,
            credentials: credentials,
            tokenContext: type.rawValue
        )
    }
}