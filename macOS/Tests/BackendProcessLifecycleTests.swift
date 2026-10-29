import Foundation
import Synchronization
import XCTest
@testable import Keldin

final class BackendProcessLifecycleTests: XCTestCase {
    func testNormalCompletionAndFailedLaunchReleaseOwnership() throws {
        let lifecycle = BackendProcessLifecycle()
        let process = LifecycleProcess()
        try lifecycle.launch(process)
        XCTAssertEqual(lifecycle.activeCount, 1)
        lifecycle.finished(process)
        XCTAssertEqual(lifecycle.activeCount, 1, "A premature callback cannot forget a live helper")
        process.finish()
        lifecycle.finished(process)
        XCTAssertEqual(lifecycle.activeCount, 0)
        XCTAssertThrowsError(try lifecycle.launch(LifecycleProcess(failsLaunch: true)))
        XCTAssertEqual(lifecycle.activeCount, 0)
    }

    func testShutdownRefusesLateLaunchesAndAllowsGracefulExit() async throws {
        let lifecycle = BackendProcessLifecycle()
        let process = LifecycleProcess(exitsOnTerminate: true)
        try lifecycle.launch(process)
        XCTAssertTrue(lifecycle.prepareForShutdown())
        let late = LifecycleProcess()
        XCTAssertThrowsError(try lifecycle.launch(late))
        XCTAssertEqual(late.starts, 0)
        let stopped = await lifecycle.waitForShutdown(gracePolls: 1, forcePolls: 1, pause: {})
        XCTAssertTrue(stopped)
        XCTAssertEqual(process.terminations, 1)
        XCTAssertEqual(process.forcedTerminations, 0)
        XCTAssertEqual(lifecycle.activeCount, 0)
    }

    func testTimeoutEscalatesOnlyStillOwnedProcesses() async throws {
        let lifecycle = BackendProcessLifecycle()
        let stubborn = LifecycleProcess()
        let completed = LifecycleProcess()
        try lifecycle.launch(stubborn)
        try lifecycle.launch(completed)
        completed.finish()
        lifecycle.finished(completed)
        XCTAssertTrue(lifecycle.prepareForShutdown())
        let stopped = await lifecycle.waitForShutdown(gracePolls: 2, forcePolls: 1, pause: {})
        XCTAssertTrue(stopped)
        XCTAssertEqual(stubborn.terminations, 1)
        XCTAssertEqual(stubborn.forcedTerminations, 1)
        XCTAssertEqual(completed.terminations, 0)
        XCTAssertEqual(completed.forcedTerminations, 0)
    }

    func testCancelledQuitReopensLaunchesWithoutLosingUnstoppedOwnership() async throws {
        let lifecycle = BackendProcessLifecycle()
        let stubborn = LifecycleProcess(ignoresForce: true)
        try lifecycle.launch(stubborn)
        XCTAssertTrue(lifecycle.prepareForShutdown())
        let stopped = await lifecycle.waitForShutdown(gracePolls: 0, forcePolls: 0, pause: {})
        XCTAssertFalse(stopped)
        lifecycle.resumeAfterCancelledShutdown()
        let next = LifecycleProcess()
        try lifecycle.launch(next)
        XCTAssertEqual(lifecycle.activeCount, 2)
        stubborn.finish()
        next.finish()
        lifecycle.finished(stubborn)
        lifecycle.finished(next)
    }

    func testEmptyShutdownStillClosesLaunchGate() {
        let lifecycle = BackendProcessLifecycle()
        XCTAssertFalse(lifecycle.prepareForShutdown())
        XCTAssertThrowsError(try lifecycle.launch(LifecycleProcess()))
    }

    func testQuitCannotOverlookLaunchInProgress() {
        let lifecycle = BackendProcessLifecycle()
        let process = BlockingLaunchProcess()
        let launched = expectation(description: "Launch finishes")
        let shutdown = expectation(description: "Quit closes launch gate")
        DispatchQueue.global().async {
            do { try lifecycle.launch(process) } catch { XCTFail("Unexpected launch failure: \(error)") }
            launched.fulfill()
        }
        XCTAssertEqual(process.started.wait(timeout: .now() + 2), .success)
        DispatchQueue.global().async {
            XCTAssertTrue(lifecycle.prepareForShutdown())
            shutdown.fulfill()
        }
        process.release.signal()
        wait(for: [launched, shutdown], timeout: 3)
        XCTAssertEqual(process.child.terminations, 1)
        XCTAssertThrowsError(try lifecycle.launch(LifecycleProcess()))
        process.child.finish()
        lifecycle.finished(process)
    }
}

private final class BlockingLaunchProcess: BackendProcessControl, Sendable {
    let started = DispatchSemaphore(value: 0)
    let release = DispatchSemaphore(value: 0)
    let child = LifecycleProcess()
    var isRunning: Bool { child.isRunning }
    func run() throws {
        started.signal()
        // This synchronous fake spawn blocks a worker, never an async executor.
        guard release.wait(timeout: .now() + 3) == .success else { throw CocoaError(.userCancelled) }
        try child.run()
    }
    func terminate() { child.terminate() }
    func forceTerminate() { child.forceTerminate() }
}

private final class LifecycleProcess: BackendProcessControl, Sendable {
    private struct State {
        var running = false
        var starts = 0
        var terminations = 0
        var forcedTerminations = 0
    }
    private let state = Mutex(State())
    private let exitsOnTerminate: Bool
    private let ignoresForce: Bool
    private let failsLaunch: Bool

    init(exitsOnTerminate: Bool = false, ignoresForce: Bool = false, failsLaunch: Bool = false) {
        self.exitsOnTerminate = exitsOnTerminate
        self.ignoresForce = ignoresForce
        self.failsLaunch = failsLaunch
    }

    var isRunning: Bool { state.withLock { $0.running } }
    var starts: Int { state.withLock { $0.starts } }
    var terminations: Int { state.withLock { $0.terminations } }
    var forcedTerminations: Int { state.withLock { $0.forcedTerminations } }
    func run() throws {
        if failsLaunch { throw CocoaError(.executableNotLoadable) }
        state.withLock { $0.starts += 1; $0.running = true }
    }
    func terminate() {
        state.withLock {
            $0.terminations += 1
            if exitsOnTerminate { $0.running = false }
        }
    }
    func forceTerminate() {
        state.withLock {
            $0.forcedTerminations += 1
            if !ignoresForce { $0.running = false }
        }
    }
    func finish() { state.withLock { $0.running = false } }
}
