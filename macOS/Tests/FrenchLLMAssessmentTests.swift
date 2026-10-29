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
                         "print_policy": FrenchLLMAssessmentRequest.printPolicy],
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
        for artifact in artifacts.dropFirst() { try Data("fixture".utf8).write(to: artifact.url) }
        XCTAssertNoThrow(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts, configuration: configuration))
        for missing in artifacts.indices {
            XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(
                artifacts: artifacts.enumerated().filter { $0.offset != missing }.map(\.element), configuration: configuration))
        }
        var duplicateRoles = artifacts
        duplicateRoles[3] = GeneratedFile(role: "question_paper", url: artifacts[3].url)
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: duplicateRoles, configuration: configuration))
        XCTAssertThrowsError(try FrenchLLMAssessmentRequest.validatePublication(artifacts: artifacts + [artifacts[0]], configuration: configuration))
        for (key, value) in [("provider", "ollama" as Any), ("model", "other"), ("seed", 43), ("seed", true),
                             ("prompt_version", "fr-nsi-written-2027-v35"), ("print_policy", "old")] {
            var changed = publication
            var identity = try XCTUnwrap(changed["identity"] as? [String: Any])
            identity[key] = value
            changed["identity"] = identity
            XCTAssertThrowsError(try validate(changed), key)
        }
        publication["model_used"] = false
        XCTAssertThrowsError(try validate(publication))
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
