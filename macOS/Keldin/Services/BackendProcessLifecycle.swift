// Keep helper ownership tied to the app, including short catalogue requests.

import AppKit
import Darwin
import Synchronization

protocol BackendProcessControl: AnyObject, Sendable {
    var isRunning: Bool { get }
    func run() throws
    func terminate()
    func forceTerminate()
}

extension Process: BackendProcessControl {
    func forceTerminate() {
        // The registry retains this exact Process and checks ownership under its
        // launch gate. Never signal a group, daemon or process found by name.
        if isRunning, processIdentifier > 0 {
            _ = Darwin.kill(processIdentifier, SIGKILL)
        }
    }
}

final class BackendProcessLifecycle: Sendable {
    static let shared = BackendProcessLifecycle()

    private struct State {
        var shuttingDown = false
        var processes: [ObjectIdentifier: any BackendProcessControl] = [:]
    }
    private let state = Mutex(State())

    var activeCount: Int {
        state.withLock { state in
            state.processes = state.processes.filter { $0.value.isRunning }
            return state.processes.count
        }
    }

    func launch(_ process: any BackendProcessControl) throws {
        // Process.run is synchronous. Holding this gate through registration and
        // launch prevents Quit from overlooking an in-flight spawn.
        try state.withLock { state in
            guard !state.shuttingDown else { throw BackendClientError.shuttingDown }
            let id = ObjectIdentifier(process)
            state.processes[id] = process
            do {
                try process.run()
            } catch {
                state.processes.removeValue(forKey: id)
                throw error
            }
        }
    }

    func finished(_ process: any BackendProcessControl) {
        state.withLock { state in
            if !process.isRunning { state.processes.removeValue(forKey: ObjectIdentifier(process)) }
        }
    }

    @discardableResult
    func prepareForShutdown() -> Bool {
        state.withLock { state in
            state.shuttingDown = true
            state.processes = state.processes.filter { $0.value.isRunning }
            for process in state.processes.values { process.terminate() }
            return !state.processes.isEmpty
        }
    }

    func waitForShutdown(
        gracePolls: Int = 20,
        forcePolls: Int = 10,
        pause: @Sendable () async -> Void = { try? await Task.sleep(for: .milliseconds(100)) }
    ) async -> Bool {
        for _ in 0..<max(0, gracePolls) {
            if activeCount == 0 { return true }
            await pause()
        }
        state.withLock { state in
            state.processes = state.processes.filter { $0.value.isRunning }
            for process in state.processes.values { process.forceTerminate() }
        }
        for _ in 0..<max(0, forcePolls) {
            if activeCount == 0 { return true }
            await pause()
        }
        return activeCount == 0
    }

    func resumeAfterCancelledShutdown() {
        state.withLock { $0.shuttingDown = false }
    }
}

@MainActor
final class BackendTerminationDelegate: NSObject, NSApplicationDelegate {
    private let lifecycle: BackendProcessLifecycle
    private var awaitingShutdown = false

    override convenience init() {
        self.init(lifecycle: .shared)
    }

    init(lifecycle: BackendProcessLifecycle) {
        self.lifecycle = lifecycle
        super.init()
    }

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if awaitingShutdown { return .terminateLater }
        guard lifecycle.prepareForShutdown() else { return .terminateNow }
        awaitingShutdown = true
        Task {
            let stopped = await lifecycle.waitForShutdown()
            awaitingShutdown = false
            sender.reply(toApplicationShouldTerminate: stopped)
            if !stopped { lifecycle.resumeAfterCancelledShutdown() }
        }
        return .terminateLater
    }
}
