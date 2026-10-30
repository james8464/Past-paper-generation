import Foundation
import Darwin

/// Availability is an OS capability check, not a paper-quality result.
struct AppleIntelligenceAvailability: Sendable {
    static let model = "apple-system-on-device"
    static let unchecked = Self(checked: false, available: false, contextSize: 0, frenchSupported: false)
    let checked: Bool
    let available: Bool
    let contextSize: Int
    let frenchSupported: Bool

    static func helperURL(bundleURL: URL = Bundle.main.bundleURL, distributionMode: DistributionMode = .current) -> URL {
        if distributionMode == .direct,
           let path = ProcessInfo.processInfo.environment["KELDIN_APPLE_INTELLIGENCE_HELPER"],
           path.hasPrefix("/") {
            return URL(fileURLWithPath: path)
        }
        return bundleURL.appendingPathComponent("Contents/Helpers/KeldinAppleIntelligence")
    }

    static func check(helper: URL) async -> Self {
        await Task.detached(priority: .utility) {
            let process = Process()
            let input = Pipe()
            let output = Pipe()
            process.executableURL = helper
            process.standardInput = input
            process.standardOutput = output
            process.standardError = FileHandle.nullDevice
            let credentialNames: Set<String> = ["KELDIN_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]
            process.environment = ProcessInfo.processInfo.environment.filter { !credentialNames.contains($0.key) }
            defer { stop(process) }
            let requestID = UUID().uuidString
            do {
                guard helper.lastPathComponent == "KeldinAppleIntelligence",
                      FileManager.default.isExecutableFile(atPath: helper.path) else {
                    throw CocoaError(.fileNoSuchFile)
                }
                let request = try JSONSerialization.data(withJSONObject: [
                    "protocol_version": 1, "request_id": requestID,
                    "operation": "availability", "locale": "fr_FR",
                ])
                try process.run()
                try input.fileHandleForWriting.write(contentsOf: request + Data([0x0A]))
                try input.fileHandleForWriting.close()
                let deadline = Date().addingTimeInterval(10)
                while process.isRunning && Date() < deadline { try await Task.sleep(for: .milliseconds(20)) }
                guard !process.isRunning else { throw CocoaError(.fileReadUnknown) }
                // Availability does not start an inference task. Its small reply
                // is bounded by the signed helper's protocol implementation.
                guard process.terminationStatus == 0 else { throw CocoaError(.fileReadUnknown) }
                let data = output.fileHandleForReading.readDataToEndOfFile()
                return try decode(data, requestID: requestID)
            } catch {
                return Self(checked: true, available: false, contextSize: 0, frenchSupported: false)
            }
        }.value
    }

    private static func stop(_ process: Process) {
        guard process.processIdentifier > 0 else { return }
        if process.isRunning { process.terminate() }
        let deadline = Date().addingTimeInterval(1)
        while process.isRunning && Date() < deadline { usleep(20_000) }
        if process.isRunning { kill(process.processIdentifier, SIGKILL) }
        process.waitUntilExit()
    }

    static func decode(_ data: Data, requestID: String) throws -> Self {
        guard data.count <= 1_048_576 else { throw CocoaError(.fileReadCorruptFile) }
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let reply = try decoder.decode(Reply.self, from: data)
        guard reply.protocolVersion == 1, reply.requestId == requestID,
              reply.provider == "apple_intelligence", reply.model == model,
              reply.status == "available", !reply.osVersion.isEmpty,
              (0 ... 65536).contains(reply.contextSize),
              !reply.available || reply.contextSize > 0 else { throw CocoaError(.fileReadCorruptFile) }
        return Self(checked: true, available: reply.available, contextSize: reply.contextSize, frenchSupported: reply.frenchSupported)
    }

    private struct Reply: Decodable {
        let protocolVersion: Int
        let requestId: String
        let provider: String
        let model: String
        let status: String
        let osVersion: String
        let contextSize: Int
        let available: Bool
        let frenchSupported: Bool
    }
}
