import Foundation
import Observation

enum GenerationJobState: String, Codable, Equatable {
    case pending
    case running
    case completed
    case cancelled
    case failed
    case interrupted
    case missingArtifacts = "missing-artifacts"
}

struct GenerationConfiguration: Codable, Equatable, Hashable {
    let boardID: String
    let paperID: String
    let provider: String
    let model: String
    let seed: Int?
    let dryRun: Bool
}

struct GenerationProvenance: Codable, Equatable {
    let appVersion: String
    let provider: String
    let model: String
}

struct QualificationSnapshot: Codable, Equatable {
    let engineeringValidated: Bool
    let visuallyCalibrated: Bool
    let empiricallyCalibrated: Bool
}

struct GenerationJobRecord: Codable, Equatable, Identifiable {
    static let currentSchemaVersion = 1

    let schemaVersion: Int
    let id: UUID
    let configuration: GenerationConfiguration
    let provenance: GenerationProvenance
    var state: GenerationJobState
    var artifacts: [GeneratedFile]
    let qualification: QualificationSnapshot
    let createdAt: Date
    var updatedAt: Date

    init(
        schemaVersion: Int = currentSchemaVersion,
        id: UUID = UUID(),
        configuration: GenerationConfiguration,
        provenance: GenerationProvenance,
        state: GenerationJobState,
        artifacts: [GeneratedFile],
        qualification: QualificationSnapshot,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.schemaVersion = schemaVersion
        self.id = id
        self.configuration = configuration
        self.provenance = provenance
        self.state = state
        self.artifacts = artifacts
        self.qualification = qualification
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    private enum CodingKeys: String, CodingKey {
        case schemaVersion
        case id
        case configuration
        case provenance
        case state
        case artifacts
        case qualification
        case createdAt
        case updatedAt
    }

    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try values.decodeIfPresent(Int.self, forKey: .schemaVersion) ?? 0
        id = try values.decode(UUID.self, forKey: .id)
        configuration = try values.decode(GenerationConfiguration.self, forKey: .configuration)
        provenance = try values.decode(GenerationProvenance.self, forKey: .provenance)
        state = try values.decode(GenerationJobState.self, forKey: .state)
        artifacts = try values.decode([GeneratedFile].self, forKey: .artifacts)
        qualification = try values.decode(QualificationSnapshot.self, forKey: .qualification)
        createdAt = try values.decode(Date.self, forKey: .createdAt)
        updatedAt = try values.decode(Date.self, forKey: .updatedAt)
    }

    var missingArtifactCount: Int {
        artifacts.lazy.filter { !$0.exists }.count
    }

    var provenanceSummary: String {
        let provider = AIProvider(backendID: configuration.provider)?.title
            ?? configuration.provider
        let seed = configuration.seed.map(String.init) ?? "Not recorded"
        return [
            "\(configuration.boardID) · Paper \(configuration.paperID)",
            "\(provider) · \(configuration.model) · Seed \(seed)",
            "App version: \(provenance.appVersion)",
            "Engineering: \(qualification.engineeringValidated ? "passed" : "pending")",
            "Visual: \(qualification.visuallyCalibrated ? "passed" : "pending")",
            "Empirical: \(qualification.empiricallyCalibrated ? "passed" : "pending")",
        ].joined(separator: "\n")
    }
}

enum RecentDocumentStoreError: LocalizedError {
    case unsupportedSchema(Int)

    var errorDescription: String? {
        switch self {
        case let .unsupportedSchema(version):
            "This history item uses unsupported schema version \(version)."
        }
    }
}

@MainActor
@Observable
final class RecentDocumentStore {
    private(set) var records: [GenerationJobRecord] = []
    private(set) var quarantinedRecordCount = 0
    var retentionLimit: Int {
        didSet { retentionLimit = max(1, retentionLimit) }
    }

    @ObservationIgnored private let directory: URL
    @ObservationIgnored private let fileManager: FileManager
    @ObservationIgnored private let clock: AppClock

    init(
        directory: URL,
        retentionLimit: Int,
        fileManager: FileManager = .default,
        clock: AppClock = SystemAppClock()
    ) {
        self.directory = directory
        self.retentionLimit = max(1, retentionLimit)
        self.fileManager = fileManager
        self.clock = clock
    }

    func load() throws {
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        let urls = try fileManager.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: nil
        ).filter { $0.pathExtension == "json" }
        var loaded: [GenerationJobRecord] = []
        quarantinedRecordCount = 0
        for url in urls {
            do {
                var record = try JSONDecoder.paperCreator.decode(
                    GenerationJobRecord.self,
                    from: Data(contentsOf: url)
                )
                if record.schemaVersion == 0 {
                    record = GenerationJobRecord(
                        id: record.id,
                        configuration: record.configuration,
                        provenance: record.provenance,
                        state: record.state,
                        artifacts: record.artifacts,
                        qualification: record.qualification,
                        createdAt: record.createdAt,
                        updatedAt: record.updatedAt
                    )
                    try write(record)
                } else if record.schemaVersion != GenerationJobRecord.currentSchemaVersion {
                    throw RecentDocumentStoreError.unsupportedSchema(record.schemaVersion)
                }
                if record.state == .running {
                    record.state = .interrupted
                    record.updatedAt = clock.now
                    try write(record)
                } else if record.state == .completed, record.missingArtifactCount > 0 {
                    record.state = .missingArtifacts
                    record.updatedAt = clock.now
                    try write(record)
                }
                loaded.append(record)
            } catch {
                try quarantine(url)
            }
        }
        records = loaded.sorted(by: Self.newestFirst)
        try enforceRetention()
    }

    func save(_ record: GenerationJobRecord) throws {
        var record = record
        record.updatedAt = max(record.updatedAt, record.createdAt)
        try fileManager.createDirectory(at: directory, withIntermediateDirectories: true)
        try write(record)
        records.removeAll { $0.id == record.id }
        records.append(record)
        records.sort(by: Self.newestFirst)
        try enforceRetention()
    }

    func remove(_ record: GenerationJobRecord) throws {
        try? fileManager.removeItem(at: fileURL(for: record.id))
        records.removeAll { $0.id == record.id }
    }

    func duplicateConfiguration(
        of record: GenerationJobRecord,
        newSeed: Int? = nil
    ) -> GenerationJobRecord {
        let configuration = GenerationConfiguration(
            boardID: record.configuration.boardID,
            paperID: record.configuration.paperID,
            provider: record.configuration.provider,
            model: record.configuration.model,
            seed: newSeed ?? record.configuration.seed,
            dryRun: record.configuration.dryRun
        )
        return GenerationJobRecord(
            configuration: configuration,
            provenance: record.provenance,
            state: .pending,
            artifacts: [],
            qualification: record.qualification,
            createdAt: clock.now,
            updatedAt: clock.now
        )
    }

    private func write(_ record: GenerationJobRecord) throws {
        let data = try JSONEncoder.paperCreator.encode(record)
        try data.write(to: fileURL(for: record.id), options: [.atomic])
    }

    private func enforceRetention() throws {
        guard records.count > retentionLimit else { return }
        for record in records.dropFirst(retentionLimit) {
            try? fileManager.removeItem(at: fileURL(for: record.id))
        }
        records = Array(records.prefix(retentionLimit))
    }

    private func quarantine(_ url: URL) throws {
        let quarantineDirectory = directory.appendingPathComponent(
            "Quarantine",
            isDirectory: true
        )
        try fileManager.createDirectory(
            at: quarantineDirectory,
            withIntermediateDirectories: true
        )
        let destination = quarantineDirectory.appendingPathComponent(
            "\(url.deletingPathExtension().lastPathComponent)-\(UUID().uuidString).json"
        )
        try fileManager.moveItem(at: url, to: destination)
        quarantinedRecordCount += 1
    }

    private func fileURL(for id: UUID) -> URL {
        directory.appendingPathComponent("\(id.uuidString).json")
    }

    private static func newestFirst(
        _ lhs: GenerationJobRecord,
        _ rhs: GenerationJobRecord
    ) -> Bool {
        if lhs.createdAt == rhs.createdAt {
            return lhs.id.uuidString < rhs.id.uuidString
        }
        return lhs.createdAt > rhs.createdAt
    }
}

private extension JSONEncoder {
    static var paperCreator: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return encoder
    }
}

private extension JSONDecoder {
    static var paperCreator: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}
