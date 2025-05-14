// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "BuckiaKit",
    platforms: [
        .macOS(.v14),
        .iOS(.v17),
        .tvOS(.v17)
    ],
    products: [
        .library(
            name: "BuckiaKit",
            targets: ["BuckiaKit"]),
    ],
    dependencies: [
        .package(url: "https://github.com/stephencelis/SQLite.swift.git", from: "0.14.1"),
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
        .package(url: "https://github.com/okta/okta-auth-swift", from: "2.4.6"),
        .package(url: "https://github.com/apple/swift-log.git", from: "1.5.3")
    ],
    targets: [
        .target(
            name: "BuckiaKit",
            dependencies: [
                .product(name: "SQLite", package: "SQLite.swift"),
                .product(name: "KeychainAccess", package: "KeychainAccess"),
                .product(name: "OktaAuthNative", package: "okta-auth-swift"),
                .product(name: "Logging", package: "swift-log")
            ]
        ),
        .testTarget(
            name: "BuckiaKitTests",
            dependencies: ["BuckiaKit"],
            path: "Tests/BuckiaKitTests"),
    ]
)