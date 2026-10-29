// Track generation requests and their streamed progress or failure state.

import Foundation
import Observation

@MainActor
@Observable
final class GenerationCoordinator {
    private(set) var activeJob: GenerationJobRecord?
    private(set) var progress: Double?
    private(set) var status = "Ready"
    private(set) var progressEntries: [ProgressEntry] = []
    private(set) var generatedFiles: [GeneratedFile] = []

    @ObservationIgnored private let history: RecentDocumentStore
    @ObservationIgnored private let clock: AppClock

    init(
        history: RecentDocumentStore,
        clock: AppClock = SystemAppClock()
    ) {
        self.history = history
        self.clock = clock
    }

    func begin(_ job: GenerationJobRecord) throws {
        var running = job
        running.state = .running
        running.updatedAt = clock.now
        // Keep the current session until the new history record has been saved.
        try history.save(running)
        activeJob = running
        status = "Starting"
        progress = 0
        progressEntries.removeAll()
        generatedFiles.removeAll()
    }

    func receive(_ event: BackendEvent, expectedJobID: UUID) {
        guard activeJob?.id == expectedJobID else { return }
        switch event {
        case let .progress(stage, message, value):
            status = message
            progress = value ?? progress
            progressEntries.append(ProgressEntry(stage: stage, message: message))
        case let .file(role, path):
            let file = GeneratedFile(role: role, url: URL(fileURLWithPath: path))
            if !generatedFiles.contains(where: { $0.url == file.url }) {
                generatedFiles.insert(file, at: 0)
            }
        case let .done(message):
            status = message
            progress = 1
        default:
            break
        }
    }

    func complete(expectedJobID: UUID, artifacts: [GeneratedFile]? = nil, expectedFrenchPolicy: FrenchAssessmentRequest.PracticePolicy = .strict) throws {
        guard var job = activeJob, job.id == expectedJobID else { throw GenerationOwnershipError.jobChanged }
        if let artifacts { generatedFiles = artifacts }
        if job.configuration.assessmentID == FrenchAssessmentRequest.assessmentID,
           job.configuration.authoringVersion == "v36" {
            try FrenchLLMAssessmentRequest.validatePublication(artifacts: generatedFiles, configuration: job.configuration)
        }
        if job.configuration.assessmentID == FrenchAssessmentRequest.assessmentID,
           job.configuration.model == FrenchAssessmentRequest.modelID {
            guard let manifest = generatedFiles.first(where: { $0.role == "package_manifest" }) else {
                throw CocoaError(.fileReadNoSuchFile)
            }
            let seed = try FrenchAssessmentRequest.publishedSeed(from: manifest.url, expectedPolicy: expectedFrenchPolicy)
            let configuration = job.configuration
            job = GenerationJobRecord(
                schemaVersion: job.schemaVersion, id: job.id,
                configuration: GenerationConfiguration(
                    boardID: configuration.boardID, paperID: configuration.paperID,
                    provider: configuration.provider, model: configuration.model,
                    seed: seed, dryRun: configuration.dryRun,
                    educationSystem: configuration.educationSystem,
                    assessmentID: configuration.assessmentID,
                    documentLanguage: configuration.documentLanguage
                ),
                provenance: job.provenance, state: job.state, artifacts: job.artifacts,
                qualification: job.qualification, createdAt: job.createdAt, updatedAt: job.updatedAt
            )
        }
        job.state = .completed
        job.artifacts = generatedFiles
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = 1
    }

    func cancel(expectedJobID: UUID) throws {
        guard var job = activeJob, job.id == expectedJobID else { throw GenerationOwnershipError.jobChanged }
        job.state = .cancelled
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = nil
        status = "Cancelled"
    }

    func fail(message: String, expectedJobID: UUID) throws {
        guard var job = activeJob, job.id == expectedJobID else { throw GenerationOwnershipError.jobChanged }
        job.state = .failed
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = nil
        status = message
    }
}

enum GenerationOwnershipError: Error {
    case jobChanged
}
