import AppKit
import PDFKit
import TipKit
import XCTest
@testable import Keldin

final class KeldinTests: XCTestCase {
    func testMLXDownloadMetadataEventRequiresTypedNonnegativeSizeAndCacheState() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"mlx_download_info","model":"owner/model","download_bytes":2048,"cached":false,"revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}"#)
        XCTAssertEqual(event, .mlxDownloadInfo(MLXDownloadInfo(model: "owner/model", downloadBytes: 2048, cached: false, revision: String(repeating: "a", count: 40))))
        for body in [#""download_bytes":-1,"cached":false"#, #""download_bytes":true,"cached":false"#, #""download_bytes":1"#, #""download_bytes":1,"cached":"false"#] {
            XCTAssertThrowsError(try BackendEvent(jsonLine: "{\"type\":\"mlx_download_info\",\"model\":\"owner/model\",\"revision\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\(body)}"))
        }
        for revision in [nil, "main", "abc", String(repeating: "A", count: 40), String(repeating: "a", count: 65), String(repeating: "a", count: 40) + "\n"] {
            XCTAssertFalse(MLXDownloadInfo(model: "owner/model", downloadBytes: 2048, cached: false, revision: revision).isValid)
        }
        XCTAssertTrue(MLXDownloadInfo(model: "/fixture/local-model", downloadBytes: 0, cached: true, revision: nil).isValid)
    }
    func testStoreMLXModelsUseManagedRepositoryIDsWithoutRestrictingDirectPaths() {
        for model in ["mlx-community/Qwen2.5-3B-Instruct-4bit", " owner/model.v1 "] {
            XCTAssertNil(MLXModelAccessPolicy.issue(model: model, distributionMode: .appStore))
        }
        for model in ["/Users/test/model", "~/models/model", "./models/model", "../model", "file:///model", "owner/model/subfolder", "local-model", "owner/.."] {
            XCTAssertNotNil(MLXModelAccessPolicy.issue(model: model, distributionMode: .appStore), model)
            XCTAssertNil(MLXModelAccessPolicy.issue(model: model, distributionMode: .direct), model)
        }
    }
    func testOllamaAvailabilityStatusUsesFrenchTranslation() {
        let expected = [
            "Not checked": "Non vérifié",
            "Ollama is available.": "Ollama est disponible.",
            "Ollama is not installed.": "Ollama n’est pas installé.",
            "Ollama is installed but not responding.": "Ollama est installé mais ne répond pas.",
        ]
        for (message, translation) in expected {
            let state = OllamaState(message: message)
            XCTAssertEqual(InterfaceText.resolve(state.messageResource, language: "fr"), translation)
            XCTAssertEqual(state.message, message)
        }
    }

    func testInterfaceTextUsesChosenLanguageOutsideTheViewTree() {
        XCTAssertEqual(InterfaceText.resolve("Create Paper", language: "fr"), "Créer un sujet")
        XCTAssertEqual(InterfaceText.resolve("Create Paper", language: "en"), "Create Paper")
        let original: LocalizedStringResource = "Create Paper"
        let french = InterfaceText.localizedResource(original, locale: Locale(identifier: "fr"))
        XCTAssertEqual(String(localized: french), "Créer un sujet")
        XCTAssertEqual(french.key, original.key)
        XCTAssertEqual(original.locale, Locale.current)
        XCTAssertEqual(
            InterfaceText.resolve(HelpTopic.frenchBaccalaureat.titleResource, language: "fr"),
            "Baccalauréat français · NSI"
        )
    }

    func testCreationContextKeepsFrenchIndependentOfUKModelReadiness() {
        let normal = KeldinCreationContext.french(largePrint: false)
        let enlarged = KeldinCreationContext.french(largePrint: true)
        XCTAssertEqual(normal.frenchLargePrint, false)
        XCTAssertEqual(enlarged.frenchLargePrint, true)
        XCTAssertNil(KeldinCreationContext.board.frenchLargePrint)
        for context in [normal, enlarged] {
            XCTAssertTrue(context.canCreate(boardCanGenerate: false, hasFrenchReferences: true, isBusy: false))
            XCTAssertFalse(context.canCreate(boardCanGenerate: true, hasFrenchReferences: false, isBusy: false))
            XCTAssertFalse(context.canCreate(boardCanGenerate: true, hasFrenchReferences: true, isBusy: true))
        }
        XCTAssertFalse(KeldinCreationContext.board.canCreate(boardCanGenerate: false, hasFrenchReferences: true, isBusy: false))
        XCTAssertTrue(KeldinCreationContext.board.canCreate(boardCanGenerate: true, hasFrenchReferences: false, isBusy: false))
    }

    func testKeldinTipContainerKeepsTheExistingTipIdentities() {
        XCTAssertEqual(KeldinCreationTips.modelRecommendation.id, "ModelRecommendationTip")
        XCTAssertEqual(KeldinCreationTips.preview.id, "PreviewTip")
        XCTAssertEqual(KeldinCreationTips.quality.id, "QualityTip")
    }

    @MainActor
    func testDocumentCommandsFollowSelectionAndMissingFiles() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let first = GeneratedFile(role: "question_paper", url: directory.appendingPathComponent("subject.pdf"))
        let second = GeneratedFile(role: "mark_scheme", url: directory.appendingPathComponent("correction.pdf"))
        let document = PDFDocument()
        document.insert(PDFPage(), at: 0)
        XCTAssertTrue(document.write(to: first.url))
        XCTAssertTrue(document.write(to: second.url))
        let actions = DocumentActionController()
        XCTAssertFalse(actions.canAccessDocument)
        actions.update(file: first, provenance: nil)
        XCTAssertTrue(actions.canAccessDocument)
        XCTAssertEqual(actions.selectedFile, first)
        actions.update(file: second, provenance: nil)
        XCTAssertEqual(actions.selectedFile, second)
        try FileManager.default.removeItem(at: second.url)
        XCTAssertFalse(actions.canAccessDocument)
        actions.update(file: nil, provenance: nil)
        XCTAssertNil(actions.selectedFile)
        XCTAssertNil(actions.provenance)
    }

    func testCancelledReviewSelectionKeepsItsFormOpen() {
        XCTAssertFalse(FrenchReviewSubmissionOutcome.cancelled.closesReviewForm)
        XCTAssertTrue(FrenchReviewSubmissionOutcome.submitted.closesReviewForm)
        XCTAssertTrue(FrenchReviewSubmissionOutcome.rejected.closesReviewForm)
    }

    func testPDFExportToItsOwnPathPreservesTheSource() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("paper.pdf")
        let original = Data("original PDF bytes".utf8)
        try original.write(to: source)
        try PDFDocumentActions.export(from: source, to: source)
        XCTAssertEqual(try Data(contentsOf: source), original)

        let destination = root.appendingPathComponent("export.pdf")
        try Data("previous export".utf8).write(to: destination)
        try PDFDocumentActions.export(from: source, to: destination)
        XCTAssertEqual(try Data(contentsOf: destination), original)
        XCTAssertThrowsError(try PDFDocumentActions.export(from: root.appendingPathComponent("missing.pdf"), to: destination))
        XCTAssertEqual(try Data(contentsOf: destination), original)
    }

    @MainActor
    func testPDFPrintOperationIncludesEveryPage() throws {
        let source = FileManager.default.temporaryDirectory.appendingPathComponent("\(UUID().uuidString).pdf")
        defer { try? FileManager.default.removeItem(at: source) }
        let document = PDFDocument()
        for index in 0..<3 { document.insert(PDFPage(), at: index) }
        XCTAssertTrue(document.write(to: source))
        let operation = try XCTUnwrap(PDFDocumentActions.printOperation(for: source))
        var range = NSRange()
        XCTAssertTrue(try XCTUnwrap(operation.view).knowsPageRange(&range))
        XCTAssertEqual(range.length, 3)
    }

    func testAppLaunchPolicySuppressesWindowsOnlyDuringUnitTests() {
        XCTAssertFalse(
            AppLaunchPolicy.presentsMainWindow(
                environment: ["XCTestConfigurationFilePath": "/tmp/tests.xctestconfiguration"]
            )
        )
        XCTAssertTrue(AppLaunchPolicy.presentsMainWindow(environment: [:]))
    }

    func testFrenchBundleExportPreservesManifestAndRejectsOverwrite() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let source = root.appendingPathComponent("working/nsi-2027-fixture")
        let output = root.appendingPathComponent("selected")
        try FileManager.default.createDirectory(at: source, withIntermediateDirectories: true)
        for name in ["sujet.pdf", "corrige.pdf", "assessment.json", "manifest.json"] {
            try Data(name.utf8).write(to: source.appendingPathComponent(name))
        }
        let result = try AssessmentBundleExporter.export(source: source, to: output)
        XCTAssertEqual(result.lastPathComponent, source.lastPathComponent)
        for name in ["sujet.pdf", "corrige.pdf", "assessment.json", "manifest.json"] {
            XCTAssertEqual(try Data(contentsOf: result.appendingPathComponent(name)), Data(name.utf8))
        }
        XCTAssertThrowsError(try AssessmentBundleExporter.export(source: source, to: output))
        XCTAssertTrue(FileManager.default.fileExists(atPath: source.path))
    }

    func testFrenchRequestKeepsCurriculumSeparateFromUILanguage() {
        let arguments = FrenchAssessmentRequest(
            referenceIndex: URL(fileURLWithPath: "/tmp/references.sqlite"),
            output: URL(fileURLWithPath: "/tmp/papers"),
            seed: 42, largePrint: true
        ).arguments
        XCTAssertEqual(arguments.first, "generate-assessment")
        XCTAssertTrue(arguments.contains("fr-bac-general-nsi-written-2027"))
        XCTAssertTrue(arguments.contains("--large-print"))
        XCTAssertFalse(arguments.contains("--subject"))
        XCTAssertFalse(arguments.contains("--allow-remote"))
        XCTAssertTrue(arguments.contains("application-owned"))
        XCTAssertFalse(arguments.contains("--model"))
        XCTAssertFalse(arguments.contains("--ollama-url"))
    }

    @MainActor
    func testTestHostStartupUsesPrivatePreferencesAndSecrets() {
        let environment = ["XCTestConfigurationFilePath": "fixture.xctestconfiguration"]
        let first = AppLaunchPolicy.makeApplication(environment: environment)
        let second = AppLaunchPolicy.makeApplication(environment: environment)
        first.setDryRun(true)
        first.settingsStore.openAIAPIKey = "test-host-only"
        first.settingsStore.save()
        XCTAssertTrue(first.dryRun)
        XCTAssertFalse(second.dryRun)
        XCTAssertTrue(second.settingsStore.openAIAPIKey.isEmpty)
        XCTAssertTrue(first.generatedFiles.isEmpty)
        XCTAssertTrue(second.generatedFiles.isEmpty)
    }

    func testFrenchTeacherReviewRequestCarriesTheCompleteRubric() throws {
        let scores = Dictionary(
            uniqueKeysWithValues: FrenchReviewRequest.rubricKeys.map { ($0, 3) }
        )
        let request = FrenchReviewRequest(
            manifest: URL(fileURLWithPath: "/tmp/nsi/manifest.json"),
            reviewer: "Mme Martin",
            decision: .revise,
            scores: scores,
            notes: "Revoir la question 2."
        )

        XCTAssertTrue(request.isComplete)
        XCTAssertEqual(request.arguments.first, "review-french-assessment")
        XCTAssertTrue(request.arguments.contains("/tmp/nsi/manifest.json"))
        let scoresIndex = try XCTUnwrap(request.arguments.firstIndex(of: "--scores-json"))
        let encoded = try XCTUnwrap(
            request.arguments[scoresIndex + 1].data(using: .utf8)
        )
        let decoded = try XCTUnwrap(
            JSONSerialization.jsonObject(with: encoded) as? [String: Int]
        )
        XCTAssertEqual(decoded, scores)
    }

    func testQualificationReadinessKeepsThreeEvidenceLevelsIndependent() {
        let readiness = QualificationReadiness(
            engineeringValidated: true,
            visuallyCalibrated: true,
            empiricallyCalibrated: false
        )

        XCTAssertTrue(readiness.engineeringValidated)
        XCTAssertTrue(readiness.visuallyCalibrated)
        XCTAssertFalse(readiness.empiricallyCalibrated)
        XCTAssertEqual(readiness.highestLevelTitle, "Visually calibrated")
    }

    func testLegacyRegistryGatesMigrateWithoutFalseEmpiricalCalibration() throws {
        let catalog = Data(
            #"{"qualification":"A-Level","subjects":[{"id":"economics","title":"Economics","system_image":"chart.line.uptrend.xyaxis","boards":[{"id":"aqa","title":"AQA"}]}]}"#.utf8
        )
        let registry = Data(
            #"{"schema_version":2,"qualification":"a-level","families":[{"app_subject":"economics","app_board":"aqa","backend_subject":"economics_aqa","resource_path":"economics/aqa","content_mode":"ai-assisted","supported_providers":["ollama"],"advertised":true,"papers":[{"id":"1","title":"Paper 1","detail":"Markets","gates":{"release":true,"visual":true,"difficulty":false}}]}]}"#.utf8
        )

        let subjects = try CatalogLoader.load(catalogData: catalog, registryData: registry)
        let readiness = try XCTUnwrap(subjects.first?.boards.first?.papers.first?.readiness)

        XCTAssertTrue(readiness.engineeringValidated)
        XCTAssertTrue(readiness.visuallyCalibrated)
        XCTAssertFalse(readiness.empiricallyCalibrated)
    }

    func testCatalogExposesQuestionBanksAsASeparateAssessmentKind() throws {
        let subjects = try CatalogLoader.load(bundle: .main)
        let board = try XCTUnwrap(
            subjects.flatMap(\.boards).first { $0.id == "computer-science-aqa" }
        )
        let dataStructures = try XCTUnwrap(
            board.papers.first { $0.id == "bank-4.2" }
        )

        XCTAssertEqual(dataStructures.assessmentKind, .questionBank)
        XCTAssertEqual(dataStructures.topicID, "4.2")
        XCTAssertEqual(board.fullPapers.map(\.id), ["1", "2"])
        XCTAssertEqual(
            board.questionBanks.map(\.id),
            ["bank-4.2", "bank-4.10", "bank-4.12"]
        )
    }

    func testBackendHandshakeDecodesProtocolCapabilities() throws {
        let event = try BackendEvent(
            jsonLine: #"{"protocol":2,"type":"hello","event_id":1,"timestamp":"2026-07-29T12:00:00Z","job_id":"job","backend_version":"2.0.0","capabilities":["manifest"]}"#
        )
        XCTAssertEqual(
            event,
            .hello(
                protocolVersion: 2,
                backendVersion: "2.0.0",
                capabilities: ["manifest"]
            )
        )
    }

    func testBackendProgressEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"progress","stage":"render","message":"Rendering question paper","progress":0.88}"#)
        XCTAssertEqual(event, .progress(stage: "render", message: "Rendering question paper", progress: 0.88))
    }

    func testBackendMLXCacheMissPreservesRecoveryCode() throws {
        let event = try BackendEvent(
            jsonLine: #"{"type":"error","message":"Approve setup again.","code":"mlx_setup_required"}"#
        )
        XCTAssertEqual(
            event,
            .error(message: "Approve setup again.", code: "mlx_setup_required")
        )
    }

    func testBackendFileEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"file","role":"mark_scheme","path":"/tmp/ms.pdf"}"#)
        XCTAssertEqual(event, .file(role: "mark_scheme", path: "/tmp/ms.pdf"))
    }

    func testBackendClientLaunchesBridge() async throws {
        let events = try await BackendClient().collect(arguments: ["ollama-status"])
        XCTAssertTrue(events.contains { event in
            if case .ollamaStatus = event {
                return true
            }
            return false
        })
    }

    func testStoreBackendCannotFallBackToDevelopmentPython() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let bridge = root.appendingPathComponent("bridge.py")
        try Data("# Development fixture; must never execute in a store build.\n".utf8).write(to: bridge)
        let missingBundle = root.appendingPathComponent("Missing.app")

        let direct = BackendClient(bundleURL: missingBundle, distributionMode: .direct, developmentRoot: root)
        let launch = try direct.launchConfiguration(arguments: ["ollama-status"])
        XCTAssertEqual(launch.workingDirectory, root)
        XCTAssertEqual(launch.arguments, [bridge.path, "ollama-status"])

        let store = BackendClient(bundleURL: missingBundle, distributionMode: .appStore, developmentRoot: root)
        XCTAssertThrowsError(try store.launchConfiguration(arguments: ["ollama-status"])) { error in
            guard case BackendClientError.backendMissing = error else {
                return XCTFail("Expected a missing bundled service, got \(error)")
            }
        }
    }

    func testBothDistributionModesPreferTheirBundledBackend() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let bundle = root.appendingPathComponent("Keldin.app")
        let executable = bundle.appendingPathComponent("Contents/Resources/KeldinBackend/KeldinBackend")
        try FileManager.default.createDirectory(at: executable.deletingLastPathComponent(), withIntermediateDirectories: true)
        try Data("# Selection fixture; this test never starts a process.\n".utf8).write(to: executable)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: executable.path)

        for mode in [DistributionMode.direct, .appStore] {
            let client = BackendClient(bundleURL: bundle, distributionMode: mode, developmentRoot: root)
            let launch = try client.launchConfiguration(arguments: ["mlx-status"])
            XCTAssertEqual(launch.executable, executable)
            XCTAssertEqual(launch.workingDirectory, executable.deletingLastPathComponent())
            XCTAssertEqual(launch.arguments, ["mlx-status"])
        }
    }

    func testBuiltAppContainsStandaloneBackend() throws {
        let bundle = Bundle(for: ApplicationCoordinator.self).bundleURL
        let executable = bundle
            .appendingPathComponent("Contents/Resources/KeldinBackend/KeldinBackend")
        XCTAssertTrue(FileManager.default.isExecutableFile(atPath: executable.path))
        let calibrationSchema = bundle.appendingPathComponent(
            "Contents/Resources/KeldinBackend/_internal/Resources/empirical-calibration.schema.json"
        )
        XCTAssertTrue(FileManager.default.fileExists(atPath: calibrationSchema.path))
        let calibrationPolicy = bundle.appendingPathComponent(
            "Contents/Resources/KeldinBackend/_internal/Resources/empirical-calibration-policy.json"
        )
        XCTAssertTrue(FileManager.default.fileExists(atPath: calibrationPolicy.path))
        let demandProfiles = bundle.appendingPathComponent(
            "Contents/Resources/KeldinBackend/_internal/Resources/reference-demand-profiles.json"
        )
        XCTAssertTrue(FileManager.default.fileExists(atPath: demandProfiles.path))
    }

    func testGenerationQualityReportDecodesReferenceDemandEvidence() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("json")
        defer { try? FileManager.default.removeItem(at: url) }
        let manifest = #"{"evidence":{"assessment_validation":{"item_count":12,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":12,"source_document_count":4,"extraction_coverage":0.94,"item_review_evidence":{"reviewed_items":12,"coverage":1.0,"reasoning_range_fit":12,"context_fit":12,"shortcut_resistant":11},"gated_distances":{"mark_band_distribution":0.12,"command_family_distribution":0.31,"mark_weighted_demand_distribution":0.08}}},"novelty_validation":{"historic_comparisons":20,"nearest_match":{"similarity":0.14}}},"outputs":{"question_paper":{"pdf_validation":{}}}}"#
        try Data(manifest.utf8).write(to: url)

        let report = try XCTUnwrap(GenerationQualityReport.load(from: url))

        XCTAssertTrue(report.referenceDemandPassed == true)
        XCTAssertEqual(report.referenceDemandItems, 12)
        XCTAssertEqual(report.referenceDemandDocuments, 4)
        XCTAssertEqual(report.referenceDemandMaxDistance, 0.31)
        XCTAssertEqual(report.referenceDemandExtractionCoverage, 0.94)
        XCTAssertEqual(report.difficultyReviewedItems, 12)
        XCTAssertEqual(report.difficultyReasoningFitItems, 12)
        XCTAssertEqual(report.difficultyContextFitItems, 12)
        XCTAssertEqual(report.difficultyShortcutFitItems, 11)
    }

    func testPreviewQualityPolicyKeepsAggregateFitSeparateFromItemReview() throws {
        let report = try loadQualityReport(
            #"{"job_id":"job-7","generator":{"id":"economics-aqa","version":"1.2.3"},"request":{"subject":"economics_aqa","paper":"1","seed":42,"preview_mode":true},"evidence":{"qualification_levels":{"engineering_validated":true,"visually_calibrated":false,"empirically_calibrated":false},"assessment_validation":{"form_id":"form-42","item_count":12,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":12,"counts":{"built-in":12},"reviewed_fixed_items":0,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":12,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":12,"source_document_count":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":0,"approved_items":0,"coverage":0.0,"reasoning_range_fit":0,"context_fit":0,"shortcut_resistant":0}}},"novelty_validation":{"passed":true,"historic_comparisons":0,"preview_skipped_history":true}},"outputs":{}}"#
        )
        let presentation = GenerationQualityPolicy.presentation(for: report)

        XCTAssertEqual(report.identity.subject, "economics_aqa")
        XCTAssertEqual(report.identity.paper, "1")
        XCTAssertEqual(report.identity.seed, 42)
        XCTAssertEqual(report.identity.jobID, "job-7")
        XCTAssertEqual(report.identity.generatorID, "economics-aqa")
        XCTAssertEqual(report.identity.formID, "form-42")
        XCTAssertEqual(report.savedMode, .preview)
        XCTAssertTrue(presentation.diagnosticLines.contains("Saved job: job-7"))
        XCTAssertEqual(presentation.originalityState, .preview)
        XCTAssertEqual(presentation.referenceDemandState, .preview)
        XCTAssertTrue(presentation.referenceDemandDetail.contains("0 of 12"))
        XCTAssertEqual(presentation.pathEvidenceState, .unknown)
        let french = GenerationQualityPolicy.presentation(for: report, locale: Locale(identifier: "fr"))
        XCTAssertEqual(french.originalityState, .preview)
        XCTAssertTrue(french.originalityDetail.hasPrefix("L’aperçu n’est pas comparé"))
        XCTAssertTrue(french.referenceDemandDetail.hasPrefix("La correspondance du profil global ne concerne que l’aperçu."))
        XCTAssertTrue(french.referenceDemandDetail.contains("0 éléments sur 12"))
    }

    func testSparseBankEvidenceNeverBecomesPassedInInspectorOrDiagnostics() throws {
        for preview in [true, false] {
            let report = try loadQualityReport("""
            {"request":{"subject":"computer_science","paper":"bank-4.2","preview_mode":\(preview)},"evidence":{"assessment_validation":{"item_count":1,"reference_demand":{"passed":true,"evidence_state":"insufficient","build_eligible":true,"items_checked":1,"topic_evidence":{"coverage":{"matched_items":0},"gaps":["Missing programme context"]}},"path_evidence":{"passed":true,"evidence_state":"insufficient","path_count":1,"candidate_mark_range":[30,30],"printed_marks":30}},"novelty_validation":{}},"outputs":{}}
            """)
            let presentation = GenerationQualityPolicy.presentation(for: report)
            XCTAssertEqual(presentation.referenceDemandState.title, "Insufficient")
            XCTAssertEqual(presentation.pathEvidenceState.title, "Insufficient")
            XCTAssertTrue(presentation.referenceDemandDetail.contains("Missing programme context"))
            XCTAssertTrue(presentation.diagnosticLines.joined(separator: " ").contains("insufficient"))
            XCTAssertFalse(presentation.pathEvidenceDetail.contains("passed"))
        }
    }

    func testLiveQualityPolicyDistinguishesFixedAndMixedProvenance() throws {
        let fixed = try loadQualityReport(
            #"{"generator":{"id":"edexcel","version":"1"},"request":{"subject":"economics_edexcel_a","paper":"3","seed":51,"preview_mode":false},"evidence":{"qualification_levels":{"engineering_validated":true,"visually_calibrated":true,"empirically_calibrated":false},"assessment_validation":{"form_id":"fixed","item_count":4,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":4,"counts":{"reviewed-deterministic-contract":4},"reviewed_fixed_items":4,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":4,"source_document_count":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let mixed = try loadQualityReport(
            #"{"request":{"subject":"economics_edexcel_a","paper":"3","seed":51,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"mixed","item_count":4,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":4,"counts":{"ai-authored-stem-reviewed-contract":1,"reviewed-deterministic-contract":3},"reviewed_fixed_items":3,"ai_authored_items":0,"ai_authored_stem_items":1,"unreviewed_or_builtin_items":0,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )

        XCTAssertEqual(fixed.authoringProvenance.kind, .reviewedFixedOnly)
        XCTAssertEqual(mixed.authoringProvenance.kind, .mixed)
        XCTAssertFalse(
            GenerationQualityPolicy.presentation(for: fixed).originalityDetail
                .contains("newly AI-authored")
        )
        XCTAssertTrue(
            GenerationQualityPolicy.presentation(for: mixed).originalityDetail
                .contains("1 stem")
        )
        XCTAssertEqual(
            GenerationQualityPolicy.presentation(for: mixed).referenceDemandState,
            .passed
        )
        let french = GenerationQualityPolicy.presentation(for: mixed, locale: Locale(identifier: "fr"))
        XCTAssertEqual(french.referenceDemandState, .passed)
        XCTAssertTrue(french.originalityDetail.hasPrefix("Les contrôles de similarité du dossier enregistré sont validés."))
        XCTAssertTrue(french.originalityDetail.contains("La provenance mixte"))
        XCTAssertTrue(french.referenceDemandDetail.contains("4 éléments sur 4"))
    }

    func testRepeatPracticeEvidenceDoesNotBecomePassedOriginality() throws {
        for overlap in [true, false] {
            for withinPaper in [true, false] {
                let report = try loadQualityReport("""
                {"request":{"preview_mode":false},"evidence":{"assessment_validation":{"item_count":1,"authoring_provenance":{"schema_version":1,"items":1,"reviewed_fixed_items":1,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0}},"novelty_validation":{"passed":\(!overlap),"cross_generation_policy":"repeat-practice-v1","within_paper_passed":\(withinPaper),"historical_overlap":\(overlap)}},"outputs":{}}
                """)
                let presentation = GenerationQualityPolicy.presentation(for: report, locale: Locale(identifier: "en"))
                XCTAssertEqual(report.historicalOverlap, overlap)
                XCTAssertEqual(report.withinPaperPassed, withinPaper)
                XCTAssertEqual(presentation.originalityState, .unknown)
                XCTAssertEqual(presentation.originalityDetail, withinPaper
                    ? "Repeat practice allows overlap with earlier papers. Questions within this paper were checked for duplicates."
                    : "Repeat practice allows overlap with earlier papers. Duplicate checks within this paper are incomplete.")
            }
        }
    }

    func testKnownStrictPolicyRetainsItsExistingSimilarityInterpretation() throws {
        let report = try loadQualityReport(#"{"request":{"preview_mode":false},"evidence":{"assessment_validation":{"item_count":1,"authoring_provenance":{"schema_version":1,"items":1,"reviewed_fixed_items":1,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0}},"novelty_validation":{"passed":true,"cross_generation_policy":"strict-cross-generation-v1","within_paper_passed":true,"historical_overlap":false}},"outputs":{}}"#)
        XCTAssertEqual(GenerationQualityPolicy.presentation(for: report).originalityState, .passed)
    }

    func testLiveSimilarityPassDoesNotBecomeOriginalityPassWithoutReviewedProvenance() throws {
        let unknown = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":9,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"unknown-provenance","item_count":1,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":1,"failed_checks":[],"item_review_evidence":{"reviewed_items":1,"approved_items":1,"coverage":1.0,"reasoning_range_fit":1,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let unreviewed = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":9,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"unreviewed-provenance","item_count":1,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":1,"counts":{"built-in":1},"reviewed_fixed_items":0,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":1,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":1,"failed_checks":[],"item_review_evidence":{"reviewed_items":1,"approved_items":1,"coverage":1.0,"reasoning_range_fit":1,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )

        for report in [unknown, unreviewed] {
            let presentation = GenerationQualityPolicy.presentation(for: report)
            XCTAssertEqual(presentation.originalityState, .unknown)
            XCTAssertTrue(presentation.originalityDetail.contains("similarity checks passed"))
            XCTAssertTrue(
                presentation.originalityDetail.contains("unknown")
                    || presentation.originalityDetail.contains("not reviewed originality")
            )
            XCTAssertTrue(
                presentation.diagnosticLines.contains(
                    "Originality (Unknown): \(presentation.originalityDetail)"
                )
            )
        }
    }

    func testLegacyManifestDoesNotInventModeCoverageOrPathEvidence() throws {
        let report = try loadQualityReport(
            #"{"job_id":"","generator":{"id":"","version":""},"evidence":{"assessment_validation":{"item_count":4,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4}},"novelty_validation":{"historic_comparisons":0}},"outputs":{}}"#
        )
        let presentation = GenerationQualityPolicy.presentation(for: report)

        XCTAssertEqual(report.savedMode, .unknown)
        XCTAssertNil(report.difficultyReviewCoverage)
        XCTAssertEqual(report.authoringProvenance.kind, .unknown)
        XCTAssertNil(report.identity.jobID)
        XCTAssertNil(report.identity.generatorID)
        XCTAssertNil(report.identity.generatorVersion)
        XCTAssertEqual(presentation.referenceDemandState, .unknown)
        XCTAssertEqual(presentation.pathEvidenceState, .unknown)
        XCTAssertTrue(
            presentation.diagnosticLines.contains {
                $0.contains("Saved mode: Unknown")
            }
        )
    }

    func testMalformedSavedReviewCountsCannotProduceAPass() throws {
        let malformed = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"bad-counts","item_count":4,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":-1,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let mismatched = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"bad-total","item_count":3,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let malformedFailures = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"bad-failures","item_count":4,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4,"failed_checks":{"unexpected":true},"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let malformedProvenance = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"bad-provenance","item_count":4,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":1,"counts":{"reviewed-fixed":1},"reviewed_fixed_items":1,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":4,"context_fit":4,"shortcut_resistant":4}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )

        XCTAssertEqual(GenerationQualityPolicy.presentation(for: malformed).referenceDemandState, .unknown)
        XCTAssertEqual(GenerationQualityPolicy.presentation(for: mismatched).referenceDemandState, .unknown)
        XCTAssertEqual(GenerationQualityPolicy.presentation(for: malformedFailures).referenceDemandState, .unknown)
        XCTAssertEqual(malformedProvenance.authoringProvenance.kind, .unknown)
    }

    func testMissingOrContradictoryFitCountersCannotPassReferenceDemand() throws {
        let missing = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"missing-fits","item_count":4,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let zero = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":7,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"zero-fits","item_count":4,"fingerprints_verified":true,"reference_demand":{"passed":true,"items_checked":4,"failed_checks":[],"item_review_evidence":{"reviewed_items":4,"approved_items":4,"coverage":1.0,"reasoning_range_fit":0,"context_fit":0,"shortcut_resistant":0}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )

        XCTAssertNil(missing.difficultyReasoningFitItems)
        XCTAssertNil(missing.difficultyContextFitItems)
        XCTAssertNil(missing.difficultyShortcutFitItems)
        XCTAssertEqual(
            GenerationQualityPolicy.presentation(for: missing).referenceDemandState,
            .unknown
        )
        XCTAssertEqual(zero.difficultyReasoningFitItems, 0)
        XCTAssertEqual(zero.difficultyContextFitItems, 0)
        XCTAssertEqual(zero.difficultyShortcutFitItems, 0)
        XCTAssertNotEqual(
            GenerationQualityPolicy.presentation(for: zero).referenceDemandState,
            .passed
        )
    }

    func testPartialReviewAndRecordedCandidatePathRemainSeparateStates() throws {
        let partial = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":8,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"partial","item_count":4,"fingerprints_verified":true,"path_evidence":{"passed":false},"reference_demand":{"passed":false,"items_checked":4,"failed_checks":["item_difficulty_review"],"item_review_evidence":{"reviewed_items":2,"approved_items":1,"coverage":0.5,"reasoning_range_fit":2,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )
        let completePath = try loadQualityReport(
            #"{"request":{"subject":"economics_aqa","paper":"1","seed":8,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"complete","item_count":1,"fingerprints_verified":true,"path_evidence":{"passed":true},"reference_demand":{"passed":true,"items_checked":1,"failed_checks":[],"item_review_evidence":{"reviewed_items":1,"approved_items":1,"coverage":1.0,"reasoning_range_fit":1,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":10}},"outputs":{}}"#
        )

        let partialPresentation = GenerationQualityPolicy.presentation(for: partial)
        XCTAssertEqual(partialPresentation.referenceDemandState, .pending)
        XCTAssertEqual(partialPresentation.pathEvidenceState, .pending)
        XCTAssertEqual(
            GenerationQualityPolicy.presentation(for: completePath).pathEvidenceState,
            .passed
        )
    }

    private func loadQualityReport(_ manifest: String) throws -> GenerationQualityReport {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("json")
        defer { try? FileManager.default.removeItem(at: url) }
        try Data(manifest.utf8).write(to: url)
        return try XCTUnwrap(GenerationQualityReport.load(from: url))
    }

    func testBenchmarkSampleEventDecodes() throws {
        let event = try BackendEvent(jsonLine: #"{"type":"benchmark_sample","elapsed":2,"cpu_load":18.5,"cpu_mb_s":720,"memory_available_gb":9.25,"memory_pressure_percent":42,"swap_used_gb":0.5,"disk_write_mb_s":420,"disk_read_mb_s":900,"disk_free_gb":128,"small_file_ms":3.2,"network_latency_ms":42,"network_download_mb_s":34,"ollama_latency_ms":12,"thermal_speed_limit_percent":100,"pdf_pages_per_s":22}"#)
        if case let .benchmarkSample(sample) = event {
            XCTAssertEqual(sample.elapsed, 2)
            XCTAssertEqual(sample.cpuLoad, 18.5)
            XCTAssertEqual(sample.cpuThroughputMBs, 720)
            XCTAssertEqual(sample.memoryAvailableGB, 9.25)
            XCTAssertEqual(sample.memoryPressurePercent, 42)
            XCTAssertEqual(sample.swapUsedGB, 0.5)
            XCTAssertEqual(sample.diskWriteMBs, 420)
            XCTAssertEqual(sample.diskReadMBs, 900)
            XCTAssertEqual(sample.diskFreeGB, 128)
            XCTAssertEqual(sample.smallFileMS, 3.2)
            XCTAssertEqual(sample.networkLatencyMS, 42)
            XCTAssertEqual(sample.networkDownloadMBs, 34)
            XCTAssertEqual(sample.ollamaLatencyMS, 12)
            XCTAssertEqual(sample.thermalSpeedLimitPercent, 100)
            XCTAssertEqual(sample.pdfPagesPerSecond, 22)
        } else {
            XCTFail("Expected benchmark sample")
        }
    }

    func testGenerationEstimateUsesModelSize() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let paper = try XCTUnwrap(economics.papers.first)
        let small = GenerationEstimator.initialEstimate(
            board: economics,
            paper: paper,
            provider: .ollama,
            model: "qwen2.5:7b",
            dryRun: false,
            benchmark: nil
        )
        let large = GenerationEstimator.initialEstimate(
            board: economics,
            paper: paper,
            provider: .ollama,
            model: "qwen2.5:32b",
            dryRun: false,
            benchmark: nil
        )
        XCTAssertGreaterThan(large.totalSeconds, small.totalSeconds)
    }

    // Run this regression alone in a controlled test process before the bounds
    // fix: the former Int conversion terminates the process for these inputs.
    func testGenerationEstimateIgnoresUnrepresentableModelSizeHints() throws {
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first(where: { $0.usesAI }))
        let paper = try XCTUnwrap(board.papers.first)
        for model in ["fixture/999999999999999999999999999999b", "fixture/" + String(repeating: "9", count: 400) + "b"] {
            let estimate = GenerationEstimator.initialEstimate(
                board: board, paper: paper, provider: .apple, model: model,
                dryRun: false, benchmark: nil
            )
            XCTAssertTrue(estimate.totalSeconds.isFinite)
            XCTAssertGreaterThan(estimate.totalSeconds, 0)
            let modelFactor = try XCTUnwrap(estimate.factors.first(where: { $0.title == "Model" }))
            XCTAssertEqual(modelFactor.impact, 1)
            XCTAssertEqual(modelFactor.detail, "Unknown model size; using neutral estimate.")
        }
    }

    func testGenerationEstimateIgnoresInvalidBenchmarkScores() throws {
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first(where: { $0.usesAI }))
        let paper = try XCTUnwrap(board.papers.first)
        for score in [Double.nan, .infinity, -.infinity, Double.greatestFiniteMagnitude, -1, 2] {
            let estimate = GenerationEstimator.initialEstimate(
                board: board, paper: paper, provider: .apple, model: "fixture/model-3b",
                dryRun: false, benchmark: BenchmarkVerdict(score: score, verdict: "fixture", detail: "fixture")
            )
            XCTAssertTrue(estimate.totalSeconds.isFinite)
            XCTAssertEqual(estimate.confidence, 0.58)
            let factor = try XCTUnwrap(estimate.factors.first(where: { $0.title == "Benchmark" }))
            XCTAssertEqual(factor.impact, 1)
            XCTAssertEqual(factor.detail, "No recent benchmark; using device defaults.")
        }
    }

    @MainActor
    func testBenchmarkRejectsInvalidScoresAtTheEventAndOwnerBoundaries() throws {
        for scoreField in ["", ",\"score\":1e100", ",\"score\":-0.1", ",\"score\":1.1"] {
            let event = try BackendEvent(jsonLine: "{\"type\":\"benchmark_done\",\"verdict\":\"fixture\"\(scoreField)}")
            if case let .error(message, code) = event {
                XCTAssertEqual(code, "invalid_benchmark_score")
                XCTAssertEqual(message, "The benchmark returned an invalid score.")
            } else {
                XCTFail("Expected invalid benchmark score error for \(scoreField)")
            }
        }
        for score in [Double.nan, .infinity, -.infinity, Double.greatestFiniteMagnitude, -1, 2] {
            let benchmark = BenchmarkCoordinator()
            benchmark.receive(.benchmarkDone(BenchmarkVerdict(score: 1, verdict: "prior", detail: "fixture")))
            benchmark.receive(.benchmarkDone(BenchmarkVerdict(score: score, verdict: "invalid", detail: "fixture")))
            XCTAssertNil(benchmark.verdict)
            XCTAssertEqual(benchmark.errorMessage, "The benchmark returned an invalid score.")
        }
    }

    @MainActor
    func testBenchmarkAcceptsScoreBoundaryValuesWithoutChangingFacts() throws {
        for score in [0.0, 1.0] {
            let event = try BackendEvent(jsonLine: "{\"type\":\"benchmark_done\",\"verdict\":\"fixture\",\"detail\":\"original detail\",\"score\":\(score)}")
            let benchmark = BenchmarkCoordinator()
            benchmark.receive(event)
            XCTAssertEqual(benchmark.verdict, BenchmarkVerdict(score: score, verdict: "fixture", detail: "original detail"))
            XCTAssertNil(benchmark.errorMessage)
        }
    }

    func testExpiredGenerationEstimateDoesNotPromiseZeroSeconds() {
        let start = Date(timeIntervalSince1970: 1_000)
        let estimate = GenerationEstimate(
            startedAt: start, totalSeconds: 60, remainingSeconds: 60,
            confidence: 0.5, factors: []
        )
        let delayed = GenerationEstimator.update(
            estimate: estimate, progress: 0.02, now: start.addingTimeInterval(120)
        )
        XCTAssertEqual(delayed.remainingText, String(localized: "Taking longer than estimated"))
        let resumed = GenerationEstimator.update(
            estimate: delayed, progress: 0.5, now: start.addingTimeInterval(120)
        )
        XCTAssertGreaterThan(resumed.remainingSeconds, 0)
        XCTAssertNotEqual(resumed.remainingText, delayed.remainingText)
    }

    func testPositiveGenerationEstimateNeverRoundsDownToZeroSeconds() {
        let estimate = GenerationEstimate(
            startedAt: Date(), totalSeconds: 10, remainingSeconds: 0.2,
            confidence: 0.5, factors: []
        )
        XCTAssertEqual(estimate.remainingText, "1s")
    }

    func testOllamaGuideSelectsAMemoryAppropriateModel() throws {
        let guide = try OllamaModelGuide.load(bundle: .main)
        let eightGB = guide.recommendation(physicalMemoryBytes: 8 * 1_073_741_824)
        let sixteenGB = guide.recommendation(physicalMemoryBytes: 16 * 1_073_741_824)

        XCTAssertEqual(eightGB.model, "qwen2.5:7b")
        XCTAssertEqual(sixteenGB.model, "gemma4:12b")
        XCTAssertEqual(sixteenGB.contextWindow, "256K")
        XCTAssertEqual(sixteenGB.appContextWindow, "16K")
        XCTAssertEqual(
            AppDefaults.ollamaModel,
            OllamaModelGuide.currentRecommendation.model
        )
        XCTAssertTrue(guide.otherModelWarning.localizedCaseInsensitiveContains("results may vary"))
        XCTAssertTrue(guide.sources.allSatisfy { $0.scheme == "https" })
    }

    func testTutorialScreenshotsAreBundled() {
        XCTAssertNotNil(NSImage(named: NSImage.Name("TutorialWorkspace")))
        XCTAssertNotNil(NSImage(named: NSImage.Name("TutorialModelSettings")))
        XCTAssertNotNil(NSImage(named: NSImage.Name("TutorialFrenchNSI")))
    }

    func testModelGuidanceUsesSelectedLanguageAndStatesReviewLimits() throws {
        let guide = try OllamaModelGuide.load(bundle: .main)
        let large = guide.recommendation(physicalMemoryBytes: 16 * 1_073_741_824)
        let small = guide.recommendation(physicalMemoryBytes: 8 * 1_073_741_824)
        XCTAssertFalse(large.validatedForFullMatrix)
        XCTAssertFalse(small.validatedForFullMatrix)
        let french = Locale(identifier: "fr")
        let detail = InterfaceText.resolve(large.detailResource, language: "fr")
        XCTAssertTrue(detail.contains("mémoire unifiée"))
        XCTAssertFalse(detail.contains("For Macs"))
        let download = String(localized: large.downloadResource(locale: french))
        XCTAssertTrue(download.contains("Environ"))
        XCTAssertTrue(download.contains("Go"))
        XCTAssertTrue(download.contains(","))
        XCTAssertFalse(download.contains("GB download"))
        let shortDownload = String(localized: large.downloadResource(locale: french, includeContext: false))
        XCTAssertTrue(shortDownload.contains(","))
        XCTAssertTrue(shortDownload.contains("Go"))
        XCTAssertFalse(shortDownload.contains("contexte"))
        for provider in AIProvider.allCases {
            let subtitle = InterfaceText.resolve(provider.subtitleResource, language: "fr")
            XCTAssertFalse(subtitle.isEmpty)
            XCTAssertNotEqual(subtitle, provider.subtitle)
        }
        let warning = InterfaceText.resolve(guide.otherModelWarningResource, language: "fr")
        XCTAssertTrue(warning.contains("pas encore passé un contrôle de qualité complet"))
        let fallback = OllamaModelGuideDocument.fallback.recommendation(physicalMemoryBytes: 16 * 1_073_741_824)
        XCTAssertEqual(fallback.detail, large.detail)
        XCTAssertEqual(fallback.downloadSizeGB, large.downloadSizeGB)
    }

    func testFrenchNSIWorkflowHasFrenchLocalisation() {
        let resourceURL = try? XCTUnwrap(Bundle.main.url(forResource: "fr", withExtension: "lproj"))
        let frenchBundle = resourceURL.flatMap(Bundle.init(url:))
        XCTAssertNotNil(frenchBundle)
        XCTAssertEqual(
            frenchBundle?.localizedString(forKey: "Record a teacher review…", value: nil, table: nil),
            "Enregistrer l’avis d’un enseignant…"
        )
        XCTAssertEqual(
            frenchBundle?.localizedString(forKey: "Create an unreviewed draft", value: nil, table: nil),
            "Créer un sujet non relu"
        )
        XCTAssertEqual(
            frenchBundle?.localizedString(forKey: "Delete downloaded French references", value: nil, table: nil),
            "Supprimer les références françaises téléchargées"
        )
        for (key, expected) in [
            ("%@ (recommended)", "%@ (recommandé)"),
            ("%lld to %lld", "%lld à %lld"),
            ("Print…", "Imprimer…"),
            ("Save review…", "Enregistrer la relecture…"),
        ] {
            XCTAssertEqual(frenchBundle?.localizedString(forKey: key, value: nil, table: nil), expected)
        }
    }

    func testFrenchReviewUsesEnvironmentLocalisableKeys() {
        XCTAssertEqual(FrenchReviewDecision.approved.localizationKey, "Approved for classroom practice")
        XCTAssertEqual(FrenchReviewDecision.revise.localizationKey, "Revisions required")
        XCTAssertEqual(FrenchReviewRubric.localizationKey(for: "correctness"), "Correctness")
        XCTAssertEqual(FrenchReviewRubric.localizationKey(for: "language"), "Quality of French")
    }

    func testDisplayPathAbbreviatesOnlyTheHomeFolder() {
        let home = FileManager.default.homeDirectoryForCurrentUser
        XCTAssertEqual(AppDefaults.displayPath(home), "~")
        XCTAssertEqual(
            AppDefaults.displayPath(home.appendingPathComponent("Downloads")),
            "~/Downloads"
        )
        XCTAssertEqual(
            AppDefaults.displayPath(URL(fileURLWithPath: "/Users/Shared/Papers")),
            "/Users/Shared/Papers"
        )
    }

    func testAppStoreModeDisablesOllamaManagement() {
        XCTAssertFalse(DistributionMode.appStore.canManageOllama)
        XCTAssertTrue(DistributionMode.direct.canManageOllama)
    }

    func testAppStoreWorkspaceIsPrivateAndNotDownloads() {
        let path = AppDefaults.appStoreWorkingFolder().path
        XCTAssertTrue(path.contains("/Library/Containers/"))
        XCTAssertTrue(path.hasSuffix("/Data/Library/Application Support/Keldin/Generated papers"))
        XCTAssertFalse(path.contains("/Data/Downloads"))
    }

    @MainActor
    func testPreviewModePreferencePersists() {
        let defaults = isolatedDefaults()
        let previous = defaults.object(forKey: AppStorageKey.dryRun)
        defer {
            if let previous {
                defaults.set(previous, forKey: AppStorageKey.dryRun)
            } else {
                defaults.removeObject(forKey: AppStorageKey.dryRun)
            }
        }

        defaults.set(true, forKey: AppStorageKey.dryRun)
        let application = isolatedApplication(defaults: defaults)
        XCTAssertTrue(application.dryRun)

        application.setDryRun(false)
        XCTAssertFalse(defaults.bool(forKey: AppStorageKey.dryRun))
    }

    func testHostedProvidersAreMarkedOffDevice() {
        XCTAssertFalse(AIProvider.ollama.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.openAI.sendsPromptsOffDevice)
        XCTAssertTrue(AIProvider.anthropic.sendsPromptsOffDevice)
    }

    func testAppleMLXSetupPolicyRequestsConsentOnlyForUnpreparedLiveModels() {
        let model = "mlx-community/test-model"

        XCTAssertTrue(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: false
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [model],
                usesAI: true,
                dryRun: false
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .apple,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: true
            )
        )
        XCTAssertFalse(
            MLXSetupPolicy.requiresSetup(
                provider: .ollama,
                model: model,
                preparedModels: [],
                usesAI: true,
                dryRun: false
            )
        )
    }

    func testCancelledMLXCacheRecoveryDoesNotLeakIntoSuccessfulRetry() {
        var recovery = MLXRecoveryState()

        recovery.beginGeneration()
        recovery.requestSetup()
        recovery.cancel()
        recovery.beginGeneration()

        XCTAssertFalse(recovery.consumeSetupRequest())
    }

    func testReviewLinksAreValidHTTPSURLs() {
        XCTAssertEqual(AppLinks.privacyPolicy.scheme, "https")
        XCTAssertEqual(AppLinks.projectHelp.scheme, "https")
        XCTAssertTrue(AppLinks.privacyPolicy.absoluteString.contains("#privacy"))
        XCTAssertEqual(
            AppLinks.projectHelp.absoluteString,
            "https://github.com/james8464/Past-paper-generation"
        )
    }

    func testCatalogReadyBoardsUseCorrectResourceFolders() throws {
        let economics = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        XCTAssertTrue(economics.isReady)
        XCTAssertEqual(economics.resourcePath, "economics/edexcel-a")
        XCTAssertEqual(economics.backendSubject, "economics")
        XCTAssertEqual(economics.papers.map(\.id), ["1", "2", "3"])

        let aqaEconomics = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))
        XCTAssertTrue(aqaEconomics.isReady)
        XCTAssertEqual(aqaEconomics.resourcePath, "economics/aqa")
        XCTAssertEqual(aqaEconomics.backendSubject, "economics_aqa")
        XCTAssertEqual(aqaEconomics.papers.map(\.id), ["1", "2", "3"])

        let ocrEconomics = try XCTUnwrap(ExamCatalog.board(id: "economics-ocr"))
        XCTAssertTrue(ocrEconomics.isReady)
        XCTAssertEqual(ocrEconomics.resourcePath, "economics/ocr")
        XCTAssertEqual(ocrEconomics.backendSubject, "economics_ocr")
        XCTAssertEqual(ocrEconomics.papers.map(\.id), ["1", "2", "3"])

        let computerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-aqa"))
        XCTAssertTrue(computerScience.isReady)
        XCTAssertEqual(computerScience.resourcePath, "computer-science/aqa")
        XCTAssertEqual(computerScience.backendSubject, "computer_science")
        XCTAssertEqual(
            computerScience.papers.map(\.id),
            ["1", "2", "bank-4.2", "bank-4.10", "bank-4.12"]
        )

        let ocrComputerScience = try XCTUnwrap(ExamCatalog.board(id: "computer-science-ocr"))
        XCTAssertTrue(ocrComputerScience.isReady)
        XCTAssertEqual(ocrComputerScience.resourcePath, "computer-science/ocr")
        XCTAssertEqual(ocrComputerScience.backendSubject, "computer_science_ocr")
        XCTAssertEqual(ocrComputerScience.papers.map(\.id), ["1", "2"])

        let aqaBusiness = try XCTUnwrap(ExamCatalog.board(id: "business-aqa"))
        XCTAssertTrue(aqaBusiness.isReady)
        XCTAssertEqual(aqaBusiness.resourcePath, "business/aqa")
        XCTAssertEqual(aqaBusiness.backendSubject, "business_aqa")
        XCTAssertEqual(aqaBusiness.papers.map(\.id), ["1", "2", "3"])

        let aqaAccounting = try XCTUnwrap(ExamCatalog.board(id: "accounting-aqa"))
        XCTAssertTrue(aqaAccounting.isReady)
        XCTAssertEqual(aqaAccounting.resourcePath, "accounting/aqa")
        XCTAssertEqual(aqaAccounting.backendSubject, "accounting_aqa")
        XCTAssertEqual(aqaAccounting.papers.map(\.id), ["1", "2"])

        let plannedBiology = try XCTUnwrap(ExamCatalog.board(id: "biology-aqa"))
        XCTAssertFalse(plannedBiology.isReady)
        XCTAssertEqual(plannedBiology.status, .placeholder)
        XCTAssertNil(plannedBiology.backendSubject)
        XCTAssertTrue(plannedBiology.papers.isEmpty)

        let plannedCambridge = try XCTUnwrap(
            ExamCatalog.board(id: "computer-science-cambridge-international")
        )
        XCTAssertFalse(plannedCambridge.isReady)
        XCTAssertNil(plannedCambridge.backendSubject)
    }

    func testBundledCatalogLoadsFromCanonicalResources() throws {
        let subjects = try CatalogLoader.load(bundle: .main)
        XCTAssertEqual(subjects.count, 8)
        XCTAssertEqual(subjects.flatMap(\.boards).count, 23)
        XCTAssertEqual(subjects.flatMap(\.boards).filter(\.isReady).count, 7)
        XCTAssertEqual(
            subjects.flatMap(\.boards).filter { !$0.isReady }.count,
            16
        )
    }

    func testCatalogExposesAIForEveryGenerator() throws {
        let edexcel = try XCTUnwrap(ExamCatalog.board(id: "economics-edexcel-a"))
        let aqa = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))

        XCTAssertTrue(edexcel.usesAI)
        XCTAssertEqual(Set(edexcel.supportedProviders), Set(AIProvider.allCases))
        XCTAssertTrue(aqa.usesAI)
        XCTAssertEqual(Set(aqa.supportedProviders), Set(AIProvider.allCases))
        XCTAssertTrue(aqa.papers.allSatisfy { !$0.readiness.empiricallyCalibrated })
    }

    @MainActor
    func testAIGeneratorRequiresOllamaCheck() throws {
        let defaults = isolatedDefaults()
        let previousWelcome = defaults.object(forKey: AppStorageKey.hasSeenWelcome)
        defer {
            if let previousWelcome {
                defaults.set(previousWelcome, forKey: AppStorageKey.hasSeenWelcome)
            } else {
                defaults.removeObject(forKey: AppStorageKey.hasSeenWelcome)
            }
        }
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        let application = isolatedApplication(defaults: defaults)
        let board = try XCTUnwrap(ExamCatalog.board(id: "economics-aqa"))
        application.selectBoard(board)
        application.aiProvider = .ollama
        application.selectedModel = AppDefaults.ollamaModel
        application.ollamaState = OllamaState()
        application.setDryRun(false)
        XCTAssertEqual(application.generationBlocker, "Check Ollama before generating.")
    }

    func testRecentDocumentMetadataRoundTrips() throws {
        let document = GeneratedFile(
            role: "question_paper",
            url: URL(fileURLWithPath: "/tmp/practice.pdf"),
            subject: "Economics AQA",
            paper: "Paper 1"
        )
        let data = try JSONEncoder().encode([document])
        let restored = try JSONDecoder().decode([GeneratedFile].self, from: data)
        XCTAssertEqual(restored, [document])
    }
}
