import CryptoKit
import Foundation
import XCTest
@testable import Keldin

final class FrenchLLMAssessmentTests: XCTestCase {
    func testRequestUsesSelectedProviderAndModelWithoutCatalogueFallbackOrSecrets() {
        for provider in AIProvider.allCases {
            let request = FrenchLLMAssessmentRequest(referenceIndex: URL(fileURLWithPath: "/refs.sqlite"),
                output: URL(fileURLWithPath: "/private/job"), seed: 42, largePrint: true,
                provider: provider, model: "chosen-model")
            XCTAssertTrue(request.arguments.contains(provider.backendID))
            XCTAssertTrue(request.arguments.contains("chosen-model"))
            XCTAssertTrue(request.arguments.contains("v36"))
            XCTAssertTrue(request.arguments.contains("--large-print"))
            for legacy in ["application-owned", "--repeat-practice", "--exclude-family", "--api-key"] {
                XCTAssertFalse(request.arguments.contains(legacy))
            }
        }
    }

    func testPublicationRequiresActualModelProviderSeedAndExplicitReviewLimits() throws {
        let configuration = GenerationConfiguration(boardID: "fr-national-nsi", paperID: "written-2027",
            provider: "apple", model: "chosen-model", seed: 42, dryRun: false,
            assessmentID: FrenchAssessmentRequest.assessmentID, authoringVersion: "v36")
        var publication: [String: Any] = [
            "schema_version": 1, "assessment": FrenchAssessmentRequest.assessmentID,
            "status": "unreviewed_draft", "generation_origin": "model_authored", "model_used": true,
            "teacher_review": "not_run", "empirical_calibration": "not_run",
            "identity": ["provider": "apple", "model": "chosen-model", "seed": 42,
                         "prompt_version": FrenchLLMAssessmentRequest.promptVersion,
                         "print_policy": FrenchLLMAssessmentRequest.printPolicy,
                         "sql_source_policy": FrenchLLMAssessmentRequest.sqlSourcePolicy],
        ]
        let file = FileManager.default.temporaryDirectory.appendingPathComponent("FrenchLLM-\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: file) }
        func validate(_ payload: [String: Any]) throws {
            try JSONSerialization.data(withJSONObject: payload).write(to: file)
            try FrenchLLMAssessmentRequest.validatePublication(at: file, configuration: configuration)
        }
        XCTAssertNoThrow(try validate(publication))
        let artifacts = [GeneratedFile(role: "package_manifest", url: file)] + ["assessment_package", "question_paper", "mark_scheme"].map {
            GeneratedFile(role: $0, url: FileManager.default.temporaryDirectory.appendingPathComponent("FrenchLLM-\(UUID().uuidString)-\($0)"))
        }
        defer { for artifact in artifacts.dropFirst() { try? FileManager.default.removeItem(at: artifact.url) } }
        var records: [String: [String: String]] = [:]
        for artifact in artifacts.dropFirst() {
            let data = artifact.role == "assessment_package"
                ? try JSONSerialization.data(withJSONObject: ["identity": try XCTUnwrap(publication["identity"])])
                : Data("%PDF-1.7\nfixture \(artifact.role)".utf8)
            try data.write(to: artifact.url)
            records[artifact.role] = ["file": artifact.url.lastPathComponent, "sha256": digest(data)]
        }
        publication["artifacts"] = records
        try validate(publication)
        XCTAssertNoThrow(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
        for artifact in artifacts.dropFirst() {
            let original = try Data(contentsOf: artifact.url)
            try (original + Data("changed".utf8)).write(to: artifact.url)
            XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
            try original.write(to: artifact.url)
        }
        for name in ["wrong.pdf", "../sujet.pdf", "/tmp/sujet.pdf", "..\\sujet.pdf"] {
            var changedRecords = records
            changedRecords["question_paper"]?["file"] = name
            var changedPublication = publication
            changedPublication["artifacts"] = changedRecords
            try validate(changedPublication)
            XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
        }
        try validate(publication)
        let packageFile = try XCTUnwrap(artifacts.first { $0.role == "assessment_package" })
        let originalPackage = try Data(contentsOf: packageFile.url)
        var wrongIdentity = try XCTUnwrap(publication["identity"] as? [String: Any])
        wrongIdentity["seed"] = 43
        let wrongPackage = try JSONSerialization.data(withJSONObject: ["identity": wrongIdentity])
        try wrongPackage.write(to: packageFile.url)
        var wrongRecords = records
        wrongRecords["assessment_package"]?["sha256"] = digest(wrongPackage)
        var wrongPublication = publication
        wrongPublication["artifacts"] = wrongRecords
        try validate(wrongPublication)
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
        let malformedPackage = Data("not JSON".utf8)
        try malformedPackage.write(to: packageFile.url)
        wrongRecords["assessment_package"]?["sha256"] = digest(malformedPackage)
        wrongPublication["artifacts"] = wrongRecords
        try validate(wrongPublication)
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
        try originalPackage.write(to: packageFile.url)
        try validate(publication)
        for missing in artifacts.indices {
            XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(
                artifacts: artifacts.enumerated().filter { $0.offset != missing }.map(\.element), configuration: configuration))
        }
        var duplicateRoles = artifacts
        duplicateRoles[3] = GeneratedFile(role: "question_paper", url: artifacts[3].url)
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: duplicateRoles, configuration: configuration))
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts + [artifacts[0]], configuration: configuration))
        for (key, value) in [("provider", "ollama" as Any), ("model", "other"), ("seed", 43), ("seed", true),
                             ("prompt_version", "fr-nsi-written-2027-v35"), ("print_policy", "old"),
                             ("sql_source_policy", "old"), ("sql_source_policy", true), ("sql_source_policy", 1)] {
            var changed = publication
            var identity = try XCTUnwrap(changed["identity"] as? [String: Any])
            identity[key] = value
            changed["identity"] = identity
            XCTAssertThrowsError(try validate(changed), key)
        }
        var missingPolicy = publication
        var missingIdentity = try XCTUnwrap(missingPolicy["identity"] as? [String: Any])
        missingIdentity.removeValue(forKey: "sql_source_policy")
        missingPolicy["identity"] = missingIdentity
        XCTAssertThrowsError(try validate(missingPolicy))
        publication["model_used"] = false
        XCTAssertThrowsError(try validate(publication))
    }

    private func digest(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }

    @MainActor
    func testDuplicateFrenchFileEventCannotBeHiddenByDocumentDeduplication() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .ollama
        app.generateFrenchFixture(largePrint: false)
        let generation = try XCTUnwrap(backend.requests.last)
        generation.onEvent(.file(role: "question_paper", path: "/private/duplicate/sujet.pdf"))
        generation.onEvent(.file(role: "question_paper", path: "/private/duplicate/sujet.pdf"))
        generation.onFinish(.success(0))
        XCTAssertTrue(app.showError)
        XCTAssertEqual(app.recentDocumentStore.records.first?.state, .failed)
        XCTAssertFalse(app.recentDocumentStore.records.contains { $0.state == .completed })
    }

    @MainActor
    func testFrenchHostedConsentKeepsFrenchEnlargedRequestAndKeyOutOfArguments() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .openAI
        app.openAIModel = "chosen-model"
        app.openAIAPIKey = "fixture-secret"
        app.generateFrenchPaper(largePrint: true)
        XCTAssertTrue(app.showHostedAIConsent)
        XCTAssertTrue(backend.requests.isEmpty)
        app.acceptHostedAIConsent()
        let generation = try XCTUnwrap(backend.requests.last)
        XCTAssertEqual(generation.arguments.first, "generate-assessment")
        XCTAssertTrue(generation.arguments.contains("--large-print"))
        XCTAssertTrue(generation.arguments.contains("chosen-model"))
        XCTAssertEqual(generation.environment["KELDIN_API_KEY"], "fixture-secret")
        XCTAssertFalse(generation.arguments.contains("fixture-secret"))
        app.cancelGeneration()
    }

    @MainActor
    func testFrenchModelReadinessCannotUseUKLayoutPreviewToBypassOllama() {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .ollama
        app.setDryRun(true)
        app.generateFrenchPaper(largePrint: false)
        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertTrue(app.showError)
        XCTAssertNil(app.generationCoordinator.activeJob)
    }

    @MainActor
    func testFrenchApplePreparationResumesFrenchEnlargedDraftRatherThanUKSelection() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let app = isolatedApplication(defaults: defaults, backend: backend)
        app.aiProvider = .apple
        app.appleModel = "fixture/model"
        app.generateFrenchPaper(largePrint: true)
        let metadata = try XCTUnwrap(backend.requests.last)
        XCTAssertEqual(metadata.arguments.first, "mlx-download-info")
        metadata.onEvent(.mlxDownloadInfo(MLXDownloadInfo(model: "fixture/model", downloadBytes: 0,
            cached: true, revision: String(repeating: "a", count: 40))))
        metadata.onFinish(.success(0))
        app.confirmMLXSetup()
        let setup = try XCTUnwrap(backend.requests.last)
        XCTAssertEqual(setup.arguments.first, "setup-mlx")
        setup.onFinish(.success(0))
        let generation = try XCTUnwrap(backend.requests.last)
        XCTAssertEqual(generation.arguments.first, "generate-assessment")
        XCTAssertTrue(generation.arguments.contains("--large-print"))
        XCTAssertTrue(generation.arguments.contains("apple"))
        XCTAssertEqual(app.generationCoordinator.activeJob?.configuration.authoringVersion, "v36")
        app.cancelGeneration()
    }
}
