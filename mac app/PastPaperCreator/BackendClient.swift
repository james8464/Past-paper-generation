@preconcurrency import Foundation

enum BackendClientError: LocalizedError {
    case backendMissing
    case pythonMissing
    case pythonVenvUnreadable(String)

    var errorDescription: String? {
        switch self {
        case .backendMissing:
            "Could not find app_backend.py."
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
        static let bridgeScript = "app_backend.py"
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
        onEvent: @escaping @MainActor (BackendEvent) -> Void,
        onFinish: @escaping @MainActor (Result<Int32, Error>) -> Void
    ) throws -> Process {
        let root = try repositoryRoot()
        let process = Process()
        let pipe = Pipe()

        process.executableURL = try pythonExecutable(root: root)
        process.currentDirectoryURL = root
        process.arguments = [root.appendingPathComponent(BackendFile.bridgeScript).path] + arguments
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
            let root = try self.repositoryRoot()
            let process = Process()
            let pipe = Pipe()
            let errorPipe = Pipe()

            process.executableURL = try self.pythonExecutable(root: root)
            process.currentDirectoryURL = root
            process.arguments = [root.appendingPathComponent(BackendFile.bridgeScript).path] + arguments
            process.standardOutput = pipe
            process.standardError = errorPipe

            try process.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
            process.waitUntilExit()

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

    @MainActor
    private static func emitLine(
        _ line: String,
        onEvent: @escaping @MainActor (BackendEvent) -> Void
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
