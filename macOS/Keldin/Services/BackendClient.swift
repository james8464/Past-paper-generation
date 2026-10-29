// Launch the backend helper and decode its streamed events.

@preconcurrency import Foundation

enum BackendClientError: LocalizedError {
    case backendMissing
    case pythonMissing
    case pythonVenvUnreadable(String)
    case shuttingDown

    var errorDescription: String? {
        switch self {
        case .backendMissing:
            "Keldin’s generation service is missing. Reinstall the app."
        case .pythonMissing:
            "Could not find a Python interpreter."
        case .shuttingDown:
            String(localized: "Keldin is closing. No new generation tasks can start.")
        case let .pythonVenvUnreadable(path):
            """
            The local Python environment is not readable: \(path). \
            Use the direct development build or choose a Python environment the app can access.
            """
        }
    }
}

protocol BackendRunning: Sendable {
    func run(
        arguments: [String],
        environment: [String: String],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process

    func collect(arguments: [String]) async throws -> [BackendEvent]
}

struct BackendEventLineBuffer {
    private var buffer = Data()

    mutating func append(_ data: Data) -> [String] {
        buffer.append(data)
        var lines: [String] = []
        while let newline = buffer.firstIndex(of: 0x0A) {
            lines.append(decode(buffer[..<newline]))
            buffer.removeSubrange(...newline)
        }
        return lines
    }

    mutating func finish() -> String {
        defer { buffer.removeAll(keepingCapacity: true) }
        return decode(buffer)
    }

    private func decode(_ data: Data) -> String {
        // A pipe read may split a character. Decode only complete lines; invalid
        // UTF-8 becomes an unreadable event, never silently discarded content.
        String(data: data, encoding: .utf8) ?? "\u{FFFD}"
    }
}

final class BackendClient: BackendRunning, @unchecked Sendable {
    private enum BackendFile {
        static let bundledExecutable = "Contents/Resources/KeldinBackend/KeldinBackend"
        static let bridgeScript = "bridge.py"
        static let localPython = ".venv/bin/python"
        static let localPythonConfig = ".venv/pyvenv.cfg"
        static let rootOverrideEnvironmentKey = "KELDIN_ROOT"
        static let bundleSearchDepth = 8
        static let pythonName = "python3"
        static let fallbackPythonDirectories = ["/usr/bin", "/opt/homebrew/bin", "/usr/local/bin"]
    }

    private let fileManager = FileManager.default
    private let bundleURL: URL
    private let distributionMode: DistributionMode
    private let developmentRoot: URL?
    private let lifecycle: BackendProcessLifecycle

    init(
        bundleURL: URL = Bundle.main.bundleURL,
        distributionMode: DistributionMode = .current,
        developmentRoot: URL? = nil,
        lifecycle: BackendProcessLifecycle = .shared
    ) {
        self.bundleURL = bundleURL
        self.distributionMode = distributionMode
        self.developmentRoot = developmentRoot
        self.lifecycle = lifecycle
    }

    func run(
        arguments: [String],
        environment: [String: String] = [:],
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @Sendable @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        let launch = try launchConfiguration(arguments: arguments)
        let process = Process()
        let pipe = Pipe()

        process.executableURL = launch.executable
        process.currentDirectoryURL = launch.workingDirectory
        process.arguments = launch.arguments
        process.environment = ProcessInfo.processInfo.environment.merging(environment) { _, newValue in newValue }
        let errorPipe = Pipe()
        process.standardOutput = pipe
        process.standardError = errorPipe

        try lifecycle.launch(process)

        Task.detached(priority: .userInitiated) {
            let errorTask = Task.detached {
                let data = errorPipe.fileHandleForReading.readDataToEndOfFile()
                return String(data: data, encoding: .utf8) ?? ""
            }

            let handle = pipe.fileHandleForReading
            var buffer = BackendEventLineBuffer()
            while true {
                let data = handle.availableData
                if data.isEmpty { break }
                for line in buffer.append(data) {
                    await Self.emitLine(line, onEvent: onEvent)
                }
            }
            await Self.emitLine(buffer.finish(), onEvent: onEvent)

            process.waitUntilExit()
            self.lifecycle.finished(process)
            let stderr = await errorTask.value.trimmingCharacters(in: .whitespacesAndNewlines)
            if process.terminationStatus != 0, !stderr.isEmpty {
                await onEvent(.error(message: Self.displayMessage(forBackendError: stderr)))
            }
            await onFinish(.success(process.terminationStatus))
        }

        return process
    }

    func collect(arguments: [String]) async throws -> [BackendEvent] {
        try await Task.detached(priority: .userInitiated) {
            let launch = try self.launchConfiguration(arguments: arguments)
            let process = Process()
            let pipe = Pipe()
            let errorPipe = Pipe()

            process.executableURL = launch.executable
            process.currentDirectoryURL = launch.workingDirectory
            process.arguments = launch.arguments
            process.standardOutput = pipe
            process.standardError = errorPipe

            try self.lifecycle.launch(process)

            // Drain both pipes while the helper is running. Reading them one after
            // another can deadlock if the helper fills stderr before stdout closes.
            let outputTask = Task.detached {
                pipe.fileHandleForReading.readDataToEndOfFile()
            }
            let errorTask = Task.detached {
                errorPipe.fileHandleForReading.readDataToEndOfFile()
            }
            process.waitUntilExit()
            self.lifecycle.finished(process)
            let data = await outputTask.value
            let errorData = await errorTask.value

            var buffer = BackendEventLineBuffer()
            let lines = buffer.append(data) + [buffer.finish()]
            var events = lines.compactMap(Self.event)
            if process.terminationStatus != 0 {
                let stderr = String(data: errorData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                if !stderr.isEmpty {
                    events.append(.error(message: Self.displayMessage(forBackendError: stderr)))
                } else if !events.contains(where: { if case .error = $0 { return true }; return false }) {
                    events.append(.error(message: "The generation service stopped (exit code \(process.terminationStatus))."))
                }
            }
            return events
        }.value
    }

    struct LaunchConfiguration {
        let executable: URL
        let workingDirectory: URL
        let arguments: [String]
    }

    func launchConfiguration(arguments: [String]) throws -> LaunchConfiguration {
        let bundledExecutable = bundleURL.appendingPathComponent(BackendFile.bundledExecutable)
        if fileManager.isExecutableFile(atPath: bundledExecutable.path) {
            return LaunchConfiguration(
                executable: bundledExecutable,
                workingDirectory: bundledExecutable.deletingLastPathComponent(),
                arguments: arguments
            )
        }

        // Store builds must use their signed, bundled service. A local checkout
        // or environment override is only a development convenience.
        guard distributionMode == .direct else { throw BackendClientError.backendMissing }

        let root = try repositoryRoot()
        return LaunchConfiguration(
            executable: try pythonExecutable(root: root),
            workingDirectory: root,
            arguments: [root.appendingPathComponent(BackendFile.bridgeScript).path] + arguments
        )
    }

    @MainActor
    private static func emitLine(
        _ line: String,
        onEvent: @escaping @Sendable @MainActor (BackendEvent) -> Void
    ) {
        if let event = event(from: line) { onEvent(event) }
    }

    private static func event(from line: String) -> BackendEvent? {
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        return (try? BackendEvent(jsonLine: trimmed)) ?? .error(message: "Backend returned unreadable output.")
    }

    private func repositoryRoot() throws -> URL {
        if let developmentRoot {
            guard hasBackendScript(in: developmentRoot) else { throw BackendClientError.backendMissing }
            return developmentRoot
        }
        let environment = ProcessInfo.processInfo.environment
        if let override = KeldinMigration.environmentValue(BackendFile.rootOverrideEnvironmentKey, environment: environment) {
            let url = URL(fileURLWithPath: override)
            if hasBackendScript(in: url) {
                return url
            }
        }

        var sourceRoot = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        while sourceRoot.path != "/" {
            if hasBackendScript(in: sourceRoot) { return sourceRoot }
            sourceRoot.deleteLastPathComponent()
        }

        var candidate = bundleURL
        for _ in 0..<BackendFile.bundleSearchDepth {
            if hasBackendScript(in: candidate) {
                return candidate
            }
            candidate.deleteLastPathComponent()
        }

        throw BackendClientError.backendMissing
    }

    private func pythonExecutable(root: URL) throws -> URL {
        let localPython = root.appendingPathComponent(BackendFile.localPython)
        if fileManager.isExecutableFile(atPath: localPython.path) {
            let venvConfig = root.appendingPathComponent(BackendFile.localPythonConfig)
            if fileManager.fileExists(atPath: venvConfig.path),
               !fileManager.isReadableFile(atPath: venvConfig.path) {
                if let systemPython = executable(named: BackendFile.pythonName) {
                    return systemPython
                }
                throw BackendClientError.pythonVenvUnreadable(venvConfig.path)
            }
            return localPython
        }

        if let systemPython = executable(named: BackendFile.pythonName) {
            return systemPython
        }

        throw BackendClientError.pythonMissing
    }

    private func hasBackendScript(in root: URL) -> Bool {
        fileManager.fileExists(atPath: root.appendingPathComponent(BackendFile.bridgeScript).path)
    }

    private func executable(named name: String) -> URL? {
        let environmentPaths = ProcessInfo.processInfo.environment["PATH"]?
            .split(separator: ":")
            .map(String.init) ?? []
        let searchPaths = environmentPaths + BackendFile.fallbackPythonDirectories

        for directory in searchPaths {
            let candidate = URL(fileURLWithPath: directory).appendingPathComponent(name)
            if fileManager.isExecutableFile(atPath: candidate.path) {
                return candidate
            }
        }

        return nil
    }

    private static func displayMessage(forBackendError error: String) -> String {
        let trimmed = error.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.contains("init_import_site"),
           trimmed.contains("pyvenv.cfg"),
           trimmed.contains("Operation not permitted") {
            return "Python could not read the project virtual environment. In Xcode, use the Direct build settings, then run again."
        }

        let maximumLength = 1_200
        guard trimmed.count > maximumLength else { return trimmed }
        return String(trimmed.prefix(maximumLength)) + "\n..."
    }
}
