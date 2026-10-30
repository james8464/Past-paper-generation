import CryptoKit
import Foundation

struct UKArtifactPublisher {
    private let copyFile: (URL, URL) throws -> Void
    private let commitDirectory: (URL, URL) throws -> Void

    init(
        copyFile: @escaping (URL, URL) throws -> Void = { source, destination in
            try FileManager.default.copyItem(at: source, to: destination)
        },
        commitDirectory: @escaping (URL, URL) throws -> Void = { source, destination in
            try FileManager.default.moveItem(at: source, to: destination)
        }
    ) {
        self.copyFile = copyFile
        self.commitDirectory = commitDirectory
    }

    func publishUserDocuments(_ files: [GeneratedFile], to output: URL) throws -> [GeneratedFile] {
        let roles: Set<String> = [
            "question_paper", "mark_scheme", "source_booklet", "preliminary_material",
            "electronic_answer_document", "skeleton_program", "data_file",
        ]
        let documents = files.filter {
            roles.contains($0.role) && $0.url.pathExtension.lowercased() != "json"
        }
        return try publish(documents, to: output)
    }

    func publish(_ files: [GeneratedFile], to output: URL) throws -> [GeneratedFile] {
        guard !files.isEmpty else { return [] }
        let manager = FileManager.default
        guard Set(files.map(\.id)).count == files.count,
              Set(files.map { $0.url.lastPathComponent }).count == files.count else {
            throw CocoaError(.fileReadInvalidFileName)
        }
        for file in files {
            guard file.url.isFileURL else { throw CocoaError(.fileReadInvalidFileName) }
            let values = try file.url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
            guard values.isRegularFile == true, values.isSymbolicLink != true else {
                throw CocoaError(.fileReadCorruptFile)
            }
        }

        try manager.createDirectory(at: output, withIntermediateDirectories: true)
        let transaction = UUID().uuidString
        let staging = output.appendingPathComponent(".keldin-export-\(transaction)", isDirectory: true)
        let destination = output.appendingPathComponent("Keldin-\(transaction)", isDirectory: true)
        guard !manager.fileExists(atPath: destination.path) else {
            throw CocoaError(.fileWriteFileExists)
        }
        try manager.createDirectory(at: staging, withIntermediateDirectories: false)
        defer { try? manager.removeItem(at: staging) }
        for file in files {
            let sourceHash = try fileHash(file.url)
            let copy = staging.appendingPathComponent(file.url.lastPathComponent)
            try copyFile(file.url, copy)
            let values = try copy.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
            guard values.isRegularFile == true, values.isSymbolicLink != true,
                  try fileHash(copy) == sourceHash else {
                throw CocoaError(.fileReadCorruptFile)
            }
        }
        // Both directories share their parent and volume. Publish the whole run
        // with one rename; existing papers and relative manifest paths stay intact.
        try commitDirectory(staging, destination)
        return files.map { relocated($0, to: destination.appendingPathComponent($0.url.lastPathComponent)) }
    }

    private func fileHash(_ url: URL) throws -> SHA256.Digest {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        var hash = SHA256()
        var chunk = try handle.read(upToCount: 1_048_576) ?? Data()
        while !chunk.isEmpty {
            hash.update(data: chunk)
            chunk = try handle.read(upToCount: 1_048_576) ?? Data()
        }
        return hash.finalize()
    }

    private func relocated(_ file: GeneratedFile, to destination: URL) -> GeneratedFile {
        GeneratedFile(
            id: file.id, role: file.role, url: destination,
            createdAt: file.createdAt, subject: file.subject, paper: file.paper
        )
    }
}
