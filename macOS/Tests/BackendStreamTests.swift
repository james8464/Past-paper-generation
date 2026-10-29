import Foundation
import Combine
import XCTest
@testable import Keldin

final class BackendStreamTests: XCTestCase {
    @MainActor
    func testCollectionFailureReachesTheRefreshErrorPresentation() async throws {
        let application = isolatedApplication(backend: try fixtureClient("exit 7"))
        application.refreshOllama()
        let finished = expectation(description: "Refresh finishes")
        let subscription = application.$isRefreshingOllama.filter { !$0 }.prefix(1).sink { _ in finished.fulfill() }
        await fulfillment(of: [finished], timeout: 3)
        subscription.cancel()
        XCTAssertTrue(application.showError)
        XCTAssertTrue(application.errorMessage.contains("7"))
    }

    func testCollectionReportsMalformedJSONAndInvalidUTF8WithoutDroppingValidEvents() async throws {
        for body in [
            #"printf '%s\n' 'not JSON' '{"type":"done","message":"Valid event"}'"#,
            #"printf '\377\n'; printf '%s' '{"type":"done","message":"Valid event"}'"#,
        ] {
            let client = try fixtureClient(body)
            let events = try await client.collect(arguments: [])
            XCTAssertEqual(events.count, 2)
            guard case .error = events.first else { return XCTFail("Malformed output must be reported") }
            XCTAssertEqual(events.last, .done(message: "Valid event"))
        }
    }

    func testCollectionReportsNonzeroExitWithEmptyStderr() async throws {
        let events = try await fixtureClient("exit 7").collect(arguments: [])
        XCTAssertEqual(events.count, 1)
        guard case let .error(message, _) = events.first else { return XCTFail("Exit failure must be reported") }
        XCTAssertTrue(message.contains("7"))
    }

    func testCollectionPreservesExplicitErrorsAndUnicodeEOFEvents() async throws {
        let detail = #"{"type":"error","message":"Exact backend detail","code":"fixture"}"#
        let explicit = try await fixtureClient("printf '%s' '\(detail)'; exit 9").collect(arguments: [])
        XCTAssertEqual(explicit, [.error(message: "Exact backend detail", code: "fixture")])
        let valid = try await fixtureClient(#"printf '\n\r\n'; printf '%s\r\n' '{"type":"progress","stage":"fixture","message":"Créée ☀️","progress":0.5}'; printf '%s' '{"type":"done","message":"Terminée"}'"#).collect(arguments: [])
        XCTAssertEqual(valid, [.progress(stage: "fixture", message: "Créée ☀️", progress: 0.5), .done(message: "Terminée")])
        let stderr = try await fixtureClient("printf '%s' 'Exact diagnostic' >&2; exit 8").collect(arguments: [])
        XCTAssertEqual(stderr, [.error(message: "Exact diagnostic")])
    }

    func testImplicitDevelopmentRootWorksWithAnUnrelatedDeepBundle() throws {
        let environment = ProcessInfo.processInfo.environment
        try XCTSkipIf(KeldinMigration.environmentValue("KELDIN_ROOT", environment: environment) != nil, "This fixture requires no development-root override")
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        let deepBundle = (0..<12).reduce(root) { path, index in path.appendingPathComponent("level\(index)") }.appendingPathComponent("Missing.app")
        try FileManager.default.createDirectory(at: deepBundle, withIntermediateDirectories: true)
        let client = BackendClient(bundleURL: deepBundle, distributionMode: .direct)
        let launch = try client.launchConfiguration(arguments: ["ollama-status"])
        let repository = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        XCTAssertEqual(launch.workingDirectory.standardizedFileURL, repository.standardizedFileURL)
        XCTAssertEqual(launch.arguments, [repository.appendingPathComponent("bridge.py").path, "ollama-status"])
        XCTAssertThrowsError(try BackendClient(bundleURL: deepBundle, distributionMode: .appStore).launchConfiguration(arguments: []))
    }

    private func fixtureClient(_ body: String) throws -> BackendClient {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinBackendFixture-\(UUID().uuidString)")
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        let executable = root.appendingPathComponent("Contents/Resources/KeldinBackend/KeldinBackend")
        try FileManager.default.createDirectory(at: executable.deletingLastPathComponent(), withIntermediateDirectories: true)
        try ("#!/bin/sh\n" + body + "\n").write(to: executable, atomically: true, encoding: .utf8)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: executable.path)
        return BackendClient(bundleURL: root, distributionMode: .appStore)
    }

    func testFrenchEventSurvivesEveryPossibleByteSplit() throws {
        let line = #"{"type":"progress","stage":"render","message":"Épreuve créée à Noël ☀️","progress":0.5}"#
        let data = Data((line + "\n").utf8)
        for split in 0...data.count {
            var buffer = BackendEventLineBuffer()
            let lines = buffer.append(Data(data.prefix(split)))
                + buffer.append(Data(data.dropFirst(split)))
            XCTAssertEqual(lines, [line], "Byte split \(split)")
            XCTAssertEqual(buffer.finish(), "")
            if let received = lines.first {
                XCTAssertEqual(
                    try BackendEvent(jsonLine: received),
                    .progress(stage: "render", message: "Épreuve créée à Noël ☀️", progress: 0.5)
                )
            }
        }
    }

    func testSeveralLinesAndFinalUnterminatedEventKeepTheirOrder() {
        var buffer = BackendEventLineBuffer()
        XCTAssertEqual(buffer.append(Data("première\n\ndeuxième\nfin é".utf8)), ["première", "", "deuxième"])
        XCTAssertEqual(buffer.finish(), "fin é")
        XCTAssertEqual(buffer.finish(), "")
    }

    func testOneByteChunksPreserveUnicodeAndFinalLine() {
        var buffer = BackendEventLineBuffer()
        let source = "créée\n完了\n🌞"
        let lines = Data(source.utf8).flatMap { buffer.append(Data([$0])) }
        XCTAssertEqual(lines, ["créée", "完了"])
        XCTAssertEqual(buffer.finish(), "🌞")
    }

    func testInvalidUTF8IsRejectedInsteadOfDroppedOrRepairedInsideJSON() {
        var buffer = BackendEventLineBuffer()
        var data = Data(#"{"type":"done","message":""#.utf8)
        data.append(0xFF)
        data.append(contentsOf: Data("\"}\n".utf8))
        let lines = buffer.append(data)
        XCTAssertEqual(lines.count, 1)
        XCTAssertThrowsError(try BackendEvent(jsonLine: lines[0]))
        XCTAssertEqual(buffer.finish(), "")

        XCTAssertEqual(buffer.append(Data([0xFF])), [])
        XCTAssertThrowsError(try BackendEvent(jsonLine: buffer.finish()))
    }
}
