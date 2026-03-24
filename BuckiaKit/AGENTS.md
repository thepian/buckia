### Swift Package Development (BuckiaKit)

#### Prerequisites
- Xcode 15+ or Swift 5.9+ command line tools
- macOS 14+

#### Building BuckiaKit
```bash
# Navigate to the BuckiaKit directory
cd /Volumes/Projects/Evidently/buckia/BuckiaKit

# Build the package
swift build

# Build in release mode
swift build -c release
```

#### Running Tests
```bash
# Run all tests
swift test

# Run specific test
swift test --filter BuckiaKitTests.BuckiaClientTests

# Run tests with verbose output
swift test --verbose

# Run tests with code coverage
swift test --enable-code-coverage
```

#### Generating Xcode Project
```bash
# Generate an Xcode project for development
swift package generate-xcodeproj

# Open the generated project
open BuckiaKit.xcodeproj
```

#### Package Documentation
```bash
# Generate documentation (requires DocC plugin)
swift package --allow-writing-to-directory ./docs \
    generate-documentation --target BuckiaKit \
    --output-path ./docs \
    --transform-for-static-hosting \
    --hosting-base-path BuckiaKit
```

#### Integration with iOS/macOS Projects
```bash
# For Swift Package Manager integration, add to Package.swift:
dependencies: [
    .package(url: "/path/to/BuckiaKit", from: "0.1.0")
]

# For Xcode projects, add through File > Add Packages...
# using the local path: /Volumes/Projects/Evidently/buckia/BuckiaKit
```


### Swift Code Style

- Follow Swift API Design Guidelines (https://swift.org/documentation/api-design-guidelines/)
- Use Swift 5.9+ features including async/await concurrency
- Use Swift's native error handling (throwing functions) 
- Prefer structs over classes for value semantics where appropriate
- Use Swift's strong type system and avoid force unwrapping of optionals
- Property and method naming:
  - Methods that perform actions should use verbs (e.g., `download()`, `sync()`)
  - Properties and methods that return values should use nouns (e.g., `configuration`, `tokens`)
  - Boolean properties should read as assertions (e.g., `isConnected`, `hasToken`)
- Use Swift's access control appropriately:
  - `public` for API interfaces
  - `internal` for implementation details (default)
  - `private` for helpers only used within a single type
  - `fileprivate` when needed for extensions within the same file
- Document all public interfaces with doc comments (/// or /** */)
- Use Swift Package Manager for dependency management
- Organize code with extensions to enhance readability


