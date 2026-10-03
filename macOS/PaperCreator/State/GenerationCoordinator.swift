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
        activeJob = running
        status = "Starting"
        progress = 0
        progressEntries.removeAll()
        generatedFiles.removeAll()
        try history.save(running)
    }

    func receive(_ event: BackendEvent) {
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

    func complete(artifacts: [GeneratedFile]? = nil) throws {
        guard var job = activeJob else { return }
        if let artifacts { generatedFiles = artifacts }
        job.state = .completed
        job.artifacts = generatedFiles
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = 1
    }

    func cancel() throws {
        guard var job = activeJob else { return }
        job.state = .cancelled
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = nil
        status = "Cancelled"
    }

    func fail(message: String) throws {
        guard var job = activeJob else { return }
        job.state = .failed
        job.updatedAt = clock.now
        try history.save(job)
        activeJob = nil
        progress = nil
        status = message
    }
}
