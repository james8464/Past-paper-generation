import Foundation
import XCTest
@testable import Keldin

final class BackendLifecycleClientTests: XCTestCase {
    @MainActor
    func testOwnedHelperIgnoringGracefulTerminationIsKilledWithinBound() async throws {
        let lifecycle = BackendProcessLifecycle()
        let client = try fixtureClient(
            #"trap '' TERM; printf '%s\n' '{"type":"done","message":"Ready"}'; exec /bin/sleep 30"#,
            lifecycle: lifecycle
        )
        let ready = expectation(description: "Fixture installs ignored TERM handler")
        let finished = expectation(description: "Stubborn owned helper exits")
        let process = try client.run(arguments: [], onEvent: { event in
            if event == .done(message: "Ready") { ready.fulfill() }
        }, onFinish: { _ in finished.fulfill() })
        await fulfillment(of: [ready], timeout: 3)
        XCTAssertTrue(lifecycle.prepareForShutdown())
        let stopped = await lifecycle.waitForShutdown(gracePolls: 1)
        XCTAssertTrue(stopped)
        await fulfillment(of: [finished], timeout: 3)
        XCTAssertEqual(process.terminationReason, .uncaughtSignal)
        XCTAssertEqual(process.terminationStatus, SIGKILL)
        XCTAssertEqual(lifecycle.activeCount, 0)
    }

    @MainActor
    func testStreamingHelperIsOwnedUntilExitAndStopsOnShutdown() async throws {
        let lifecycle = BackendProcessLifecycle()
        let client = try fixtureClient("exec /bin/sleep 30", lifecycle: lifecycle)
        let finished = expectation(description: "Owned helper exits")
        let process = try client.run(arguments: [], onEvent: { _ in }, onFinish: { _ in finished.fulfill() })
        XCTAssertEqual(lifecycle.activeCount, 1)
        XCTAssertTrue(lifecycle.prepareForShutdown())
        let stopped = await lifecycle.waitForShutdown()
        XCTAssertTrue(stopped)
        await fulfillment(of: [finished], timeout: 3)
        XCTAssertFalse(process.isRunning)
        XCTAssertEqual(lifecycle.activeCount, 0)
    }

    func testCollectionCompletionCleansOwnershipAndBothLaunchPathsRefuseAfterQuit() async throws {
        let lifecycle = BackendProcessLifecycle()
        let client = try fixtureClient(
            #"printf '%s\n' '{"type":"done","message":"Fixture complete"}'"#,
            lifecycle: lifecycle
        )
        let events = try await client.collect(arguments: [])
        XCTAssertEqual(events, [.done(message: "Fixture complete")])
        XCTAssertEqual(lifecycle.activeCount, 0)
        XCTAssertFalse(lifecycle.prepareForShutdown())
        XCTAssertThrowsError(try client.run(arguments: [], onEvent: { _ in }, onFinish: { _ in }))
        do {
            _ = try await client.collect(arguments: [])
            XCTFail("Collection must not launch after Quit")
        } catch BackendClientError.shuttingDown {
            // Both entry points use the same closed launch gate.
        }
    }

    private func fixtureClient(_ body: String, lifecycle: BackendProcessLifecycle) throws -> BackendClient {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinLifecycleFixture-\(UUID().uuidString)")
        addTeardownBlock { try? FileManager.default.removeItem(at: root) }
        let helper = root.appendingPathComponent("Contents/Resources/KeldinBackend/KeldinBackend")
        try FileManager.default.createDirectory(at: helper.deletingLastPathComponent(), withIntermediateDirectories: true)
        try ("#!/bin/sh\n" + body + "\n").write(to: helper, atomically: true, encoding: .utf8)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: helper.path)
        return BackendClient(bundleURL: root, distributionMode: .appStore, lifecycle: lifecycle)
    }
}
