import CryptoKit
import Foundation
import XCTest
@testable import Keldin

final class UKArtifactPublisherTests: XCTestCase {
    @MainActor
    func testFrenchAndUKCompletionExportDocumentsButRetainPrivateManifests() throws {
        for french in [false, true] {
            let backend = ControlledRunBackend()
            let defaults = isolatedDefaults()
            defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
            defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
            let application = isolatedApplication(defaults: defaults, backend: backend)
            application.selectBoard(try XCTUnwrap(ExamCatalog.readyBoards.first { $0.usesAI }))
            application.setDryRun(true)
            let output = directory.appendingPathComponent(french ? "french-exports" : "uk-exports")
            application.outputFolder = output
            if french { application.generateFrenchPaper(largePrint: false) }
            else { application.generate() }
            let run = try XCTUnwrap(backend.requests.first)
            let outputIndex = try XCTUnwrap(run.arguments.firstIndex(of: "--output"))
            let working = URL(fileURLWithPath: run.arguments[outputIndex + 1])
            let source = french ? working.appendingPathComponent("nsi-fixture") : working
            try manager.createDirectory(at: source, withIntermediateDirectories: true)
            let seedIndex = try XCTUnwrap(run.arguments.firstIndex(of: "--seed"))
            let seed = try XCTUnwrap(Int(run.arguments[seedIndex + 1]))
            let manifest = source.appendingPathComponent("manifest.json")
            let metadata: [String: Any] = [
                "schema_version": 1, "assessment": FrenchAssessmentRequest.assessmentID,
                "status": "unreviewed_draft", "generation_origin": "application_owned", "model_used": false,
                "teacher_review": "not_run", "empirical_calibration": "not_run",
                "practice_policy": "repeat-practice-v1", "cross_history_comparison": "not_performed",
                "identity": ["provider": "application-owned", "model": FrenchAssessmentRequest.modelID,
                    "prompt_version": "fr-nsi-written-2027-v35", "print_policy": "fr-nsi-v35-internal-review-v1", "seed": seed],
            ]
            let bytes = try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys])
            try bytes.write(to: manifest)
            for role in ["question_paper", "mark_scheme"] {
                let pdf = source.appendingPathComponent(role + ".pdf")
                try Data((role + " fixture").utf8).write(to: pdf)
                run.onEvent(.file(role: role, path: pdf.path))
            }
            run.onEvent(.file(role: "package_manifest", path: manifest.path))
            run.onFinish(.success(0))

            XCTAssertFalse(application.showError, application.errorMessage)
            XCTAssertEqual(application.recentDocumentStore.records.first?.state, .completed)
            let retained = try XCTUnwrap(application.currentGenerationFiles.first { $0.role == "package_manifest" })
            XCTAssertEqual(retained.url, manifest)
            XCTAssertEqual(try Data(contentsOf: retained.url), bytes)
            let folders = try manager.contentsOfDirectory(at: output, includingPropertiesForKeys: nil)
            XCTAssertEqual(folders.count, 1)
            XCTAssertEqual(Set(try manager.contentsOfDirectory(atPath: folders[0].path)), ["question_paper.pdf", "mark_scheme.pdf"])
            for file in application.currentGenerationFiles where file.role != "package_manifest" {
                XCTAssertEqual(file.url.deletingLastPathComponent().resolvingSymlinksInPath(), folders[0].resolvingSymlinksInPath())
                XCTAssertEqual(try Data(contentsOf: file.url), try Data(contentsOf: source.appendingPathComponent(file.url.lastPathComponent)))
            }
        }
    }

    func testUserPublicationKeepsJSONPrivateAndCopiesOnlyUsableDocuments() throws {
        let files = try fixtureFiles()
        let sourceBefore = try snapshot(sourceFolder)
        let output = directory.appendingPathComponent("documents", isDirectory: true)

        let published = try UKArtifactPublisher().publishUserDocuments(files, to: output)

        XCTAssertEqual(Set(published.map(\.role)), ["question_paper", "mark_scheme"])
        XCTAssertEqual(try snapshot(sourceFolder), sourceBefore)
        let destination = try XCTUnwrap(published.first?.url.deletingLastPathComponent())
        XCTAssertEqual(Set(try manager.contentsOfDirectory(atPath: destination.path)), ["question.pdf", "mark-scheme.pdf"])
        for file in published {
            XCTAssertEqual(try Data(contentsOf: file.url), sourceBefore[file.url.lastPathComponent])
        }
    }

    private var directory: URL!
    private let manager = FileManager.default

    override func setUpWithError() throws {
        directory = manager.temporaryDirectory.appendingPathComponent("KeldinUKPublication-\(UUID().uuidString)")
        try manager.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        if let directory { try manager.removeItem(at: directory) }
    }

    func testSecondCopyFailurePreservesEveryExistingDestinationAndSource() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let before = try snapshot(output)
        let sourceBefore = try snapshot(sourceFolder)
        var copies = 0
        let publisher = UKArtifactPublisher(copyFile: { source, destination in
            copies += 1
            if copies == 2 { throw CocoaError(.fileWriteNoPermission) }
            try Data(contentsOf: source).write(to: destination, options: .atomic)
        })

        XCTAssertThrowsError(try publisher.publish(files, to: output))

        XCTAssertEqual(copies, 2)
        XCTAssertEqual(try snapshot(output), before)
        XCTAssertEqual(try snapshot(sourceFolder), sourceBefore)
        XCTAssertFalse(try manager.contentsOfDirectory(atPath: output.path).contains { $0.hasPrefix(".keldin-export-") })
    }

    func testCommitFailurePreservesExistingDestinationAndCleansOnlyItsStaging() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let before = try snapshot(output)
        let publisher = UKArtifactPublisher(commitDirectory: { _, _ in
            throw CocoaError(.fileWriteNoPermission)
        })

        XCTAssertThrowsError(try publisher.publish(files, to: output))

        XCTAssertEqual(try snapshot(output), before)
        XCTAssertFalse(try manager.contentsOfDirectory(atPath: output.path).contains { $0.hasPrefix(".keldin-export-") })
    }

    func testSuccessPublishesOneNewFolderWithEqualBytesAndRelativeManifestTargets() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let before = try snapshot(output)
        let published = try UKArtifactPublisher().publish(files, to: output)
        let jobFolder = try XCTUnwrap(published.first?.url.deletingLastPathComponent())

        XCTAssertNotEqual(jobFolder, output)
        XCTAssertEqual(jobFolder.deletingLastPathComponent(), output)
        XCTAssertEqual(Set(published.map { $0.url.deletingLastPathComponent() }), Set([jobFolder]))
        XCTAssertEqual(published.map(\.id), files.map(\.id))
        XCTAssertEqual(published.map(\.role), files.map(\.role))
        XCTAssertEqual(published.map(\.createdAt), files.map(\.createdAt))
        for (original, result) in zip(files, published) {
            XCTAssertEqual(try Data(contentsOf: result.url), try Data(contentsOf: original.url))
            XCTAssertEqual(result.subject, original.subject)
            XCTAssertEqual(result.paper, original.paper)
            XCTAssertEqual(result.url.lastPathComponent, original.url.lastPathComponent)
        }
        for (name, bytes) in before {
            XCTAssertEqual(try Data(contentsOf: output.appendingPathComponent(name)), bytes)
        }
        let manifest = try XCTUnwrap(published.first { $0.role == "package_manifest" })
        let document = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: manifest.url)) as? [String: Any])
        let outputs = try XCTUnwrap(document["outputs"] as? [String: [String: Any]])
        for metadata in outputs.values {
            let filename = try XCTUnwrap(metadata["filename"] as? String)
            let bytes = try Data(contentsOf: jobFolder.appendingPathComponent(filename))
            XCTAssertEqual(metadata["sha256"] as? String, hash(bytes))
            XCTAssertEqual(metadata["bytes"] as? Int, bytes.count)
        }
    }

    func testRepeatedRunsNeverReplaceEarlierPublishedArtifacts() throws {
        let files = try fixtureFiles()
        let output = directory.appendingPathComponent("published", isDirectory: true)
        let first = try UKArtifactPublisher().publish(files, to: output)
        let firstBefore = try snapshot(first[0].url.deletingLastPathComponent())
        let revision = Data("second question revision".utf8)
        try revision.write(to: files[0].url)
        let manifest = try XCTUnwrap(files.first { $0.role == "package_manifest" })
        var document = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: manifest.url)) as? [String: Any])
        var outputs = try XCTUnwrap(document["outputs"] as? [String: [String: Any]])
        outputs["question_paper"] = ["filename": files[0].url.lastPathComponent, "bytes": revision.count, "sha256": hash(revision)]
        document["outputs"] = outputs
        try JSONSerialization.data(withJSONObject: document, options: [.sortedKeys]).write(to: manifest.url)
        let second = try UKArtifactPublisher().publish(files, to: output)

        XCTAssertNotEqual(first[0].url.deletingLastPathComponent(), second[0].url.deletingLastPathComponent())
        XCTAssertEqual(try snapshot(first[0].url.deletingLastPathComponent()), firstBefore)
        XCTAssertEqual(try Data(contentsOf: second[0].url), try Data(contentsOf: files[0].url))
    }

    func testDuplicateBasenamesAndSymlinkSourcesRefuseWithoutPublishing() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let before = try snapshot(output)
        XCTAssertThrowsError(try UKArtifactPublisher().publish([files[0], files[0]], to: output))
        let link = sourceFolder.appendingPathComponent("linked.pdf")
        try manager.createSymbolicLink(at: link, withDestinationURL: files[0].url)
        XCTAssertThrowsError(try UKArtifactPublisher().publish([GeneratedFile(role: "question_paper", url: link)], to: output))
        XCTAssertEqual(try snapshot(output), before)
    }

    @MainActor
    func testPublicationFailureDoesNotChangeCollectedURLsOrActiveJobHistory() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let application = isolatedApplication()
        let job = pendingJob()
        try application.generationCoordinator.begin(job)
        application.beginDocumentCollection()
        for file in files { application.apply(.file(role: file.role, path: file.url.path)) }
        let urls = application.generatedFiles.map(\.url)
        let records = application.recentDocumentStore.records
        var copies = 0
        let publisher = UKArtifactPublisher(copyFile: { source, destination in
            copies += 1
            if copies == 2 { throw CocoaError(.fileWriteNoPermission) }
            try Data(contentsOf: source).write(to: destination, options: .atomic)
        })

        XCTAssertThrowsError(try application.publishUKGeneratedFiles(from: sourceFolder, to: output, publisher: publisher))

        XCTAssertEqual(application.generatedFiles.map(\.url), urls)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, job.id)
        XCTAssertEqual(application.generationCoordinator.activeJob?.state, .running)
        XCTAssertEqual(application.recentDocumentStore.records, records)
    }

    @MainActor
    func testURLsAndCompletedHistoryChangeOnlyAfterDirectoryCommit() throws {
        let files = try fixtureFiles()
        let output = directory.appendingPathComponent("published", isDirectory: true)
        let application = isolatedApplication()
        let job = pendingJob()
        try application.generationCoordinator.begin(job)
        application.beginDocumentCollection()
        for file in files { application.apply(.file(role: file.role, path: file.url.path)) }
        let urls = application.generatedFiles.map(\.url)
        var committed = false
        let publisher = UKArtifactPublisher(commitDirectory: { [self] source, destination in
            XCTAssertEqual(application.generatedFiles.map(\.url), urls)
            XCTAssertEqual(application.recentDocumentStore.records.first?.state, .running)
            try manager.moveItem(at: source, to: destination)
            committed = true
        })

        try application.publishUKGeneratedFiles(from: sourceFolder, to: output, publisher: publisher)

        XCTAssertTrue(committed)
        XCTAssertNotEqual(application.generatedFiles.map(\.url), urls)
        try application.generationCoordinator.complete(expectedJobID: job.id, artifacts: application.currentGenerationFiles)
        XCTAssertNil(application.generationCoordinator.activeJob)
        XCTAssertEqual(application.recentDocumentStore.records.first?.state, .completed)
        XCTAssertEqual(application.recentDocumentStore.records.first?.artifacts.map(\.url), application.currentGenerationFiles.map(\.url))
    }

    @MainActor
    func testMixedCurrentJobPathsRefuseWithoutChangingUnrelatedOlderDocuments() throws {
        let files = try fixtureFiles()
        let output = try outputWithExistingFiles(files)
        let before = try snapshot(output)
        let outside = directory.appendingPathComponent("outside", isDirectory: true)
        try manager.createDirectory(at: outside, withIntermediateDirectories: true)
        let older = outside.appendingPathComponent("older.pdf")
        let unexpected = outside.appendingPathComponent("unexpected.pdf")
        try Data("retained older document".utf8).write(to: older)
        try Data("unexpected current document".utf8).write(to: unexpected)
        let application = isolatedApplication()
        application.apply(.file(role: "question_paper", path: older.path))
        let job = pendingJob()
        try application.generationCoordinator.begin(job)
        application.beginDocumentCollection()
        for file in files { application.apply(.file(role: file.role, path: file.url.path)) }
        application.apply(.file(role: "source_booklet", path: unexpected.path))
        let documents = application.generatedFiles
        let records = application.recentDocumentStore.records
        var copied = false
        let publisher = UKArtifactPublisher(copyFile: { _, _ in copied = true })

        XCTAssertThrowsError(try application.publishUKGeneratedFiles(from: sourceFolder, to: output, publisher: publisher))

        XCTAssertFalse(copied)
        XCTAssertEqual(application.generatedFiles, documents)
        XCTAssertEqual(application.generationCoordinator.activeJob?.id, job.id)
        XCTAssertEqual(application.recentDocumentStore.records, records)
        XCTAssertEqual(try snapshot(output), before)
        XCTAssertEqual(try Data(contentsOf: older), Data("retained older document".utf8))
        XCTAssertEqual(try Data(contentsOf: unexpected), Data("unexpected current document".utf8))
    }

    private var sourceFolder: URL { directory.appendingPathComponent("working", isDirectory: true) }

    private func fixtureFiles() throws -> [GeneratedFile] {
        try manager.createDirectory(at: sourceFolder, withIntermediateDirectories: true)
        let payloads = [
            ("question_paper", "question.pdf", Data("opaque question PDF fixture bytes".utf8)),
            ("mark_scheme", "mark-scheme.pdf", Data("opaque correction PDF fixture bytes".utf8)),
            ("assessment_package", "assessment.json", Data("{\"schema_version\":1}".utf8)),
        ]
        var outputs: [String: [String: Any]] = [:]
        var files: [GeneratedFile] = []
        for (role, name, bytes) in payloads {
            let url = sourceFolder.appendingPathComponent(name)
            try bytes.write(to: url)
            files.append(GeneratedFile(role: role, url: url, subject: "Accounting", paper: "Paper 1"))
            outputs[role] = ["filename": name, "bytes": bytes.count, "sha256": hash(bytes)]
        }
        let manifest = sourceFolder.appendingPathComponent("accounting-paper-1-package.json")
        try JSONSerialization.data(withJSONObject: ["outputs": outputs], options: [.sortedKeys]).write(to: manifest)
        files.append(GeneratedFile(role: "package_manifest", url: manifest, subject: "Accounting", paper: "Paper 1"))
        return files
    }

    private func outputWithExistingFiles(_ files: [GeneratedFile]) throws -> URL {
        let output = directory.appendingPathComponent("published", isDirectory: true)
        try manager.createDirectory(at: output, withIntermediateDirectories: true)
        for file in files {
            try Data("previous \(file.role)".utf8).write(to: output.appendingPathComponent(file.url.lastPathComponent))
        }
        try Data("unrelated retained file".utf8).write(to: output.appendingPathComponent(".unrelated-export"))
        return output
    }

    private func snapshot(_ folder: URL) throws -> [String: Data] {
        try Dictionary(uniqueKeysWithValues: manager.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil).map {
            ($0.lastPathComponent, try Data(contentsOf: $0))
        })
    }

    private func hash(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    @MainActor
    private func pendingJob() -> GenerationJobRecord {
        GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "aqa-accounting", paperID: "paper_1", provider: "test", model: "fixture", seed: 1, dryRun: false),
            provenance: GenerationProvenance(appVersion: "test", provider: "test", model: "fixture"),
            state: .pending, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
    }
}
