import Foundation

/// Keep the PDFs, assessment and their relative-path manifest together.
enum AssessmentBundleExporter {
    static func export(source: URL, to output: URL) throws -> URL {
        let manager = FileManager.default
        let files = try manager.contentsOfDirectory(
            at: source, includingPropertiesForKeys: [.isRegularFileKey, .isSymbolicLinkKey]
        )
        guard files.contains(where: { $0.lastPathComponent == "manifest.json" }),
              try files.allSatisfy({
                  let values = try $0.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
                  return values.isRegularFile == true && values.isSymbolicLink != true
              }) else {
            throw CocoaError(.fileReadCorruptFile)
        }
        try manager.createDirectory(at: output, withIntermediateDirectories: true)
        let destination = output.appendingPathComponent(source.lastPathComponent, isDirectory: true)
        guard !manager.fileExists(atPath: destination.path) else {
            throw CocoaError(.fileWriteFileExists)
        }
        let staging = output.appendingPathComponent(".nsi-export-\(UUID().uuidString)", isDirectory: true)
        defer { try? manager.removeItem(at: staging) }
        try manager.copyItem(at: source, to: staging)
        try manager.moveItem(at: staging, to: destination)
        return destination
    }
}
