// swift-tools-version: 6.0
import PackageDescription

let package = Package(
  name: "KeldinAppleIntelligence",
  platforms: [.macOS(.v15)],
  products: [.executable(name: "KeldinAppleIntelligence", targets: ["KeldinAppleIntelligence"])],
  targets: [
    .executableTarget(name: "KeldinAppleIntelligence"),
    .testTarget(name: "KeldinAppleIntelligenceTests", dependencies: ["KeldinAppleIntelligence"]),
  ]
)
