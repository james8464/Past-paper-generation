// Persist job history and resolve the document artifacts attached to each job.

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
    var educationSystem: String? = nil
    var assessmentID: String? = nil
    var documentLanguage: String? = nil
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
    @ObservationIgnored private let defaults: UserDefaults
    @ObservationIgnored private let recordWriter: (Data, URL) throws -> Void

    init(
        directory: URL,
        retentionLimit: Int,
        fileManager: FileManager = .default,
        clock: AppClock = SystemAppClock(),
        defaults: UserDefaults = .standard,
        recordWriter: @escaping (Data, URL) throws -> Void = { data, url in
            try data.write(to: url, options: [.atomic])
        }
    ) {
        self.directory = directory
        self.retentionLimit = max(1, retentionLimit)
        self.fileManager = fileManager
        self.clock = clock
        self.defaults = defaults
        self.recordWriter = recordWriter
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
            // Access failures do not make a record corrupt. Keep reads and
            // migration writes outside the structural-validation catch.
            let data = try Data(contentsOf: url)
            var record: GenerationJobRecord
            do {
                record = try JSONDecoder.keldin.decode(GenerationJobRecord.self, from: data)
                if record.schemaVersion != 0,
                   record.schemaVersion != GenerationJobRecord.currentSchemaVersion {
                    throw RecentDocumentStoreError.unsupportedSchema(record.schemaVersion)
                }
            } catch is DecodingError {
                try quarantine(url)
                continue
            } catch RecentDocumentStoreError.unsupportedSchema(_) {
                try quarantine(url)
                continue
            }
            let relocated = record.artifacts.map { KeldinMigration.relocatedArtifact($0, defaults: defaults) }
            var needsWrite = relocated != record.artifacts
            record.artifacts = relocated
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
                needsWrite = true
            }
            if record.state == .running {
                record.state = .interrupted
                record.updatedAt = clock.now
                needsWrite = true
            } else if record.state == .completed, record.missingArtifactCount > 0 {
                record.state = .missingArtifacts
                record.updatedAt = clock.now
                needsWrite = true
            }
            if needsWrite { try write(record) }
            loaded.append(record)
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
            dryRun: record.configuration.dryRun,
            educationSystem: record.configuration.educationSystem,
            assessmentID: record.configuration.assessmentID,
            documentLanguage: record.configuration.documentLanguage
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
        let data = try JSONEncoder.keldin.encode(record)
        try recordWriter(data, fileURL(for: record.id))
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
    static var keldin: JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        return encoder
    }
}

private extension JSONDecoder {
    static var keldin: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }
}
