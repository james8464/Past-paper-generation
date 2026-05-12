@preconcurrency import Foundation

enum BackendClientError: LocalizedError {
    case backendMissing
    case pythonMissing
    case unreadableOutput(String)

    var errorDescription: String? {
        switch self {
        case .backendMissing:
            "Could not find app_backend.py."
        case .pythonMissing:
            "Could not find a Python interpreter."
        case let .unreadableOutput(line):
            "Backend returned unreadable output: \(line)"
        }
    }
}

final class BackendClient: @unchecked Sendable {
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
        process.arguments = [root.appendingPathComponent("app_backend.py").path] + arguments
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
                await onEvent(.error(message: stderr))
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
            process.arguments = [root.appendingPathComponent("app_backend.py").path] + arguments
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
                return events + [.error(message: errorText.trimmingCharacters(in: .whitespacesAndNewlines))]
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
        if let override = environment["PAPER_CREATOR_ROOT"] {
            let url = URL(fileURLWithPath: override)
            if fileManager.fileExists(atPath: url.appendingPathComponent("app_backend.py").path) {
                return url
            }
        }

        let sourceRoot = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        if fileManager.fileExists(atPath: sourceRoot.appendingPathComponent("app_backend.py").path) {
            return sourceRoot
        }

        var candidate = Bundle.main.bundleURL
        for _ in 0..<8 {
            if fileManager.fileExists(atPath: candidate.appendingPathComponent("app_backend.py").path) {
                return candidate
            }
            candidate.deleteLastPathComponent()
        }

        throw BackendClientError.backendMissing
    }

    private func pythonExecutable(root: URL) throws -> URL {
        let localPython = root.appendingPathComponent(".venv/bin/python")
        if fileManager.isExecutableFile(atPath: localPython.path) {
            return localPython
        }

        let userPython = URL(fileURLWithPath: "/usr/bin/python3")
        if fileManager.isExecutableFile(atPath: userPython.path) {
            return userPython
        }

        throw BackendClientError.pythonMissing
    }
}
