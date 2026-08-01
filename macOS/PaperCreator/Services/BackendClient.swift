@preconcurrency import Foundation

enum BackendClientError: LocalizedError {
    case backendMissing
    case pythonMissing
    case pythonVenvUnreadable(String)

    var errorDescription: String? {
        switch self {
        case .backendMissing:
            "Paper creator’s generation service is missing. Reinstall the app."
        case .pythonMissing:
            "Could not find a Python interpreter."
        case let .pythonVenvUnreadable(path):
            """
            The local Python environment is not readable: \(path). \
            Use the direct development build or choose a Python environment the app can access.
            """
        }
    }
}

final class BackendClient: @unchecked Sendable {
    private enum BackendFile {
        static let bundledExecutable = "Contents/Resources/PaperCreatorBackend/PaperCreatorBackend"
        static let bridgeScript = "bridge.py"
        static let localPython = ".venv/bin/python"
        static let localPythonConfig = ".venv/pyvenv.cfg"
        static let rootOverrideEnvironmentKey = "PAPER_CREATOR_ROOT"
        static let bundleSearchDepth = 8
        static let pythonName = "python3"
        static let fallbackPythonDirectories = ["/usr/bin", "/opt/homebrew/bin", "/usr/local/bin"]
    }

    private let fileManager = FileManager.default

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

        try process.run()

        Task.detached(priority: .userInitiated) {
            let errorTask = Task.detached {
                let data = errorPipe.fileHandleForReading.readDataToEndOfFile()
                return String(data: data, encoding: .utf8) ?? ""
            }

            let handle = pipe.fileHandleForReading
            var buffer = ""
            while true {
                let data = handle.availableData
                if data.isEmpty { break }
                buffer += String(data: data, encoding: .utf8) ?? ""

                while let newline = buffer.firstIndex(of: "\n") {
                    let line = String(buffer[..<newline])
                    buffer.removeSubrange(...newline)
                    await Self.emitLine(line, onEvent: onEvent)
                }
            }
            await Self.emitLine(buffer, onEvent: onEvent)

            process.waitUntilExit()
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

            try process.run()

            // Drain both pipes while the helper is running. Reading them one after
            // another can deadlock if the helper fills stderr before stdout closes.
            let outputTask = Task.detached {
                pipe.fileHandleForReading.readDataToEndOfFile()
            }
            let errorTask = Task.detached {
                errorPipe.fileHandleForReading.readDataToEndOfFile()
            }
            process.waitUntilExit()
            let data = await outputTask.value
            let errorData = await errorTask.value

            let output = String(data: data, encoding: .utf8) ?? ""
            let events = output
                .split(separator: "\n")
                .compactMap { try? BackendEvent(jsonLine: String($0)) }
            if process.terminationStatus != 0,
               let errorText = String(data: errorData, encoding: .utf8),
               !errorText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                return events + [.error(message: Self.displayMessage(forBackendError: errorText))]
            }
            return events
        }.value
    }

    private struct LaunchConfiguration {
        let executable: URL
        let workingDirectory: URL
        let arguments: [String]
    }

    private func launchConfiguration(arguments: [String]) throws -> LaunchConfiguration {
        let bundledExecutable = Bundle.main.bundleURL.appendingPathComponent(BackendFile.bundledExecutable)
        if fileManager.isExecutableFile(atPath: bundledExecutable.path) {
            return LaunchConfiguration(
                executable: bundledExecutable,
                workingDirectory: bundledExecutable.deletingLastPathComponent(),
                arguments: arguments
            )
        }

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
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        if let event = try? BackendEvent(jsonLine: trimmed) {
            onEvent(event)
        } else {
            onEvent(.error(message: "Backend returned unreadable output."))
        }
    }

    private func repositoryRoot() throws -> URL {
        let environment = ProcessInfo.processInfo.environment
        if let override = environment[BackendFile.rootOverrideEnvironmentKey] {
            let url = URL(fileURLWithPath: override)
            if hasBackendScript(in: url) {
                return url
            }
        }

        let sourceRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        if hasBackendScript(in: sourceRoot) {
            return sourceRoot
        }

        var candidate = Bundle.main.bundleURL
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
