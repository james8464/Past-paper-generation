import Foundation
import XCTest
@testable import Keldin

final class CoordinatorTests: XCTestCase {
    @MainActor
    func testOccitanieBackendStatusesFollowInterfaceLanguageAndKeepRawDiagnostics() {
        let preparation = "Préparation de l'extrait public d'Occitanie"
        let cancellation = "Création de l'activité annulée"
        for (language, preparing, cancelled, completed) in [
            ("en", "Preparing the Occitanie case study", "Occitanie case study cancelled.", "Occitanie case study created. Separate activity, without an exam mark."),
            ("fr", "Préparation de l’étude de cas Occitanie", "Création de l’activité annulée.", "Étude de cas Occitanie créée. Activité indépendante, sans note d’examen."),
        ] {
            let defaults = isolatedDefaults()
            defaults.set(language, forKey: "interfaceLanguage")
            let application = isolatedApplication(defaults: defaults)
            application.apply(.progress(stage: "occitanie_case_study", message: preparation, progress: 0.1))
            XCTAssertEqual(application.status, preparing)
            XCTAssertEqual(application.progressEntries.last?.message, preparation)
            application.apply(.progress(stage: "cancel", message: cancellation, progress: 0))
            XCTAssertEqual(application.status, cancelled)
            XCTAssertEqual(application.progressEntries.last?.message, cancellation)
            for completion in [
                "Activité Occitanie créée. Document indépendant, sans note d'examen.",
                "Activité Occitanie créée. Document indépendant, sans note d’examen.",
            ] {
                application.apply(.done(message: completion))
                XCTAssertEqual(application.status, completed)
                XCTAssertEqual(application.progressEntries.last?.message, completion)
            }
        }
    }
    @MainActor
    func testExplicitGenerationQualityRefusalsShowRecoveryCopyWithoutLosingDetails() throws {
        let english = "The model's work did not pass the paper quality checks. Try again or choose a stronger model in Settings. You can copy diagnostics from Tools."
        let french = "Le résultat du modèle ne passe pas les contrôles de qualité du sujet. Réessayez ou choisissez un modèle plus performant dans Réglages. Les détails peuvent être copiés depuis Outils."
        for firstLine in [
            "question 01 failed independent solution reconciliation: answer mismatch",
            "0/0/0 failed reference-demand review: context check failed",
            "question-2b failed second-pass assessment review: marking issue",
            "verified contract 15.1 failed assessment review: not approved",
            "question-1a independent answer disagrees with the keyed option",
            "AI could not produce a valid, second-pass reviewed item for question 01: rejected",
        ] {
            let raw = firstLine + "\nA private diagnostic report was saved to /private/test/model-diagnostic.json"
            XCTAssertEqual(GenerationPresentation.error(raw, code: "generation_failed", language: "en"), english)
            XCTAssertEqual(GenerationPresentation.error(raw, code: "generation_failed", language: "fr"), french)
            let defaults = isolatedDefaults()
            defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
            defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
            defaults.set("en", forKey: "interfaceLanguage")
            let backend = ControlledRunBackend()
            let model = isolatedApplication(defaults: defaults, backend: backend)
            model.setDryRun(true)
            model.generate()
            let request = try XCTUnwrap(backend.requests.first)
            request.onEvent(.error(message: raw, code: "generation_failed"))
            XCTAssertEqual(model.errorMessage, english)
            XCTAssertEqual(model.progressEntries.last?.message, raw)
            XCTAssertTrue(model.diagnosticSummary.contains(raw))
            request.onFinish(.success(1))
            XCTAssertEqual(model.generationCoordinator.status, raw)
            XCTAssertEqual(model.recentDocumentStore.records.first?.state, .failed)
        }
    }

    @MainActor
    func testQualityPresentationDoesNotHideOtherFailureTypes() {
        let quality = "question 01 failed independent solution reconciliation: mismatch"
        for code in ["output_error", "mlx_setup_required", "provider_error", "network_error", "cancelled"] {
            XCTAssertEqual(GenerationPresentation.error(quality, code: code, language: "fr"), quality)
        }
        XCTAssertEqual(GenerationPresentation.error(quality, language: "fr"), quality)
        for message in [
            "Could not write to /private/test/output: Permission denied",
            "Connection refused by the local provider",
            "Apple MLX support is not ready. Run the guided setup.",
            "Creation cancelled",
            "Ollama returned incomplete structured output.",
            "Unknown failure\nquestion 01 failed independent solution reconciliation: mismatch",
        ] {
            XCTAssertEqual(GenerationPresentation.error(message, code: "generation_failed", language: "fr"), message)
        }
    }

    @MainActor
    func testMLXBatchProgressUsesPlainLocalizedCopyAndKeepsDiagnostics() {
        for (stage, message, english, french) in [
            ("provider_batch", "Apple MLX is decoding two tasks together.",
             "Apple MLX is working on two tasks.", "Apple MLX traite deux tâches en parallèle."),
            ("provider_serial_fallback", "Apple MLX is using serial decoding for this model or prompt pair.",
             "Apple MLX is working on one task at a time for this model or these prompts.",
             "Apple MLX traite une tâche à la fois pour ce modèle ou ces consignes."),
        ] {
            XCTAssertEqual(GenerationPresentation.progress(message, language: "en"), english)
            XCTAssertEqual(GenerationPresentation.progress(message, language: "fr"), french)
            let model = isolatedApplication()
            model.apply(.progress(stage: stage, message: message, progress: 0.25))
            XCTAssertEqual(model.progressEntries.last?.message, message)
            XCTAssertEqual(model.progressEntries.last?.stage, stage)
            XCTAssertEqual(model.generationProgress, 0.25)
            let unknown = message + " Extra diagnostics."
            XCTAssertEqual(GenerationPresentation.progress(unknown, language: "fr"), unknown)
        }
    }

    @MainActor
    func testAcceptedParallelProgressUsesTheSelectedLanguage() {
        for (kind, english, french) in [
            ("items", "Items checked: 2 of 17", "Éléments vérifiés : 2 sur 17"),
            ("questions", "Questions checked: 2 of 17", "Questions vérifiées : 2 sur 17"),
        ] {
            let message = "Accepted 2 of 17 AI \(kind)"
            XCTAssertEqual(GenerationPresentation.progress(message, language: "en"), english)
            XCTAssertEqual(GenerationPresentation.progress(message, language: "fr"), french)
        }
        for malformed in ["Accepted 3 of 2 AI items", "Accepted 1 of 0 AI questions",
                          "Accepted -1 of 2 AI items", "Accepted two of 17 AI questions",
                          "Accepted 2 of 17 AI questions: extra", "Accepted 2 of 17 AI questions\n"] {
            XCTAssertEqual(GenerationPresentation.progress(malformed, language: "fr"), malformed)
        }
        let model = isolatedApplication()
        let message = "Accepted 2 of 17 AI questions"
        model.apply(.progress(stage: "checkpoint", message: message, progress: 0.3))
        XCTAssertEqual(model.progressEntries.last?.message, message)
        XCTAssertEqual(model.generationProgress, 0.3)
    }

    @MainActor
    func testDifficultyReviewProgressUsesPlainSelectedLanguageCopy() {
        for prefix in ["Calibrating difficulty", "Checking reference demand"] {
            let message = "\(prefix) 2/17: 1b"
            XCTAssertEqual(GenerationPresentation.progress(message, language: "en"), "Reviewing question 2 of 17")
            XCTAssertEqual(GenerationPresentation.progress(message, language: "fr"), "Vérification de la question 2 sur 17")
        }
        let malformed = "Calibrating difficulty 0/17: 1b"
        XCTAssertEqual(GenerationPresentation.progress(malformed, language: "fr"), malformed)
    }

    @MainActor
    func testQualityFailureShowsRecoveryAdviceAndKeepsOriginalActivity() {
        let model = isolatedApplication()
        let diagnostic = "AI could not produce a valid, second-pass reviewed item for question 05: context check failed"
        model.apply(.error(message: diagnostic, code: "generation_failed"))
        XCTAssertEqual(model.errorMessage, String(localized: "The model's work did not pass the paper quality checks. Try again or choose a stronger model in Settings. You can copy diagnostics from Tools."))
        XCTAssertEqual(model.progressEntries.last?.message, diagnostic)
        XCTAssertTrue(model.diagnosticSummary.contains(diagnostic))

        model.apply(.error(message: "Cannot write to the selected folder", code: "output_error"))
        XCTAssertEqual(model.errorMessage, "Cannot write to the selected folder")
    }

    @MainActor
    func testRefinementStatusKeepsQuestionNumberAndDetailedActivity() {
        let model = isolatedApplication()
        let diagnostic = "Refining AI item 03.2 after an automated quality check: Counter({'AO1': 2})"
        model.apply(.progress(stage: "generation", message: diagnostic, progress: 0.25))
        XCTAssertEqual(model.status, String(localized: "Rechecking question \("03.2")"))
        XCTAssertEqual(model.progressEntries.last?.message, diagnostic)
        XCTAssertEqual(model.generationProgress, 0.25)

        model.apply(.progress(stage: "generation", message: "Writing PDFs", progress: 0.9))
        XCTAssertEqual(model.status, "Writing PDFs")
    }

    @MainActor
    func testGenerationMessagesHonorTheChosenFrenchInterfaceLanguage() {
        let defaults = isolatedDefaults()
        defaults.set("fr", forKey: "interfaceLanguage")
        let model = isolatedApplication(defaults: defaults)
        model.apply(.progress(stage: "generation", message: "Refining AI item 01 after an automated quality check: context check failed", progress: 0.1))
        XCTAssertEqual(model.status, "Nouvelle vérification de la question 01")
        model.apply(.done(message: "Sujet d'entraînement créé. Barème indicatif, difficulté et durée non calibrées."))
        XCTAssertEqual(model.status, "Sujet d’entraînement créé. Barème indicatif, difficulté et durée non calibrées.")
        model.apply(.error(message: "AI could not produce a valid, second-pass reviewed item for question 01: rejected", code: "generation_failed"))
        XCTAssertTrue(model.errorMessage.hasPrefix("Le résultat du modèle ne passe pas les contrôles"))
        XCTAssertEqual(model.status, "Erreur")
    }

    @MainActor
    func testFrenchCompletionAndExhaustionHonorEnglishInterfaceLanguage() {
        let defaults = isolatedDefaults()
        defaults.set("en", forKey: "interfaceLanguage")
        let model = isolatedApplication(defaults: defaults)
        model.apply(.done(message: "Sujet d'entraînement créé. Barème indicatif, difficulté et durée non calibrées."))
        XCTAssertEqual(model.status, "Practice paper created. Marking guidance is indicative; difficulty and timing are uncalibrated.")
        model.apply(.error(message: "Les quatre familles disponibles sont trop proches des sujets précédents. Aucun nouveau sujet n'a été créé.", code: "french_generation_failed"))
        XCTAssertEqual(model.errorMessage, "None of the four paper families is sufficiently different from your saved papers. No new paper was created.")
        XCTAssertEqual(model.status, "Error")
    }

    @MainActor
    func testFiveFamilyRefusalHasEnglishAndFrenchCopy() {
        let message = "Les cinq familles disponibles sont trop proches des sujets précédents. Aucun nouveau sujet n'a été créé."
        XCTAssertEqual(GenerationPresentation.error(message, language: "en"), "None of the five paper families is sufficiently different from your saved papers. No new paper was created.")
        XCTAssertEqual(GenerationPresentation.error(message, language: "fr"), "Aucune des cinq familles n’est suffisamment différente de vos sujets enregistrés. Aucun nouveau sujet n’a été créé.")
    }

    @MainActor
    func testFrenchSavedFamiliesSurviveOutputFolderChangesAndMissingFiles() throws {
        func record(model: String, seed: Int?, state: GenerationJobState = .completed, dryRun: Bool = false) -> GenerationJobRecord {
            GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: "fr-national-nsi", paperID: "written-2027", provider: "application-owned", model: model, seed: seed, dryRun: dryRun, assessmentID: FrenchAssessmentRequest.assessmentID),
                provenance: GenerationProvenance(appVersion: "test", provider: "application-owned", model: model),
                state: state, artifacts: [], qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
            )
        }
        let jobs = (0..<5).map { record(model: "app-owned-v35", seed: $0, state: $0 == 4 ? .missingArtifacts : .completed) }
        XCTAssertEqual(try FrenchAssessmentRequest.savedFamilies(in: jobs), [0,1,2,3,4])
        XCTAssertEqual(try FrenchAssessmentRequest.savedFamilies(in: [record(model: "app-owned-v34", seed: 7), record(model: "app-owned-v35", seed: -1)]), [3,4])
        XCTAssertEqual(try FrenchAssessmentRequest.savedFamilies(in: [record(model: "app-owned-v35", seed: 2, state: .failed), record(model: "app-owned-v35", seed: 2, dryRun: true)]), [])
        XCTAssertThrowsError(try FrenchAssessmentRequest.savedFamilies(in: [record(model: "app-owned-v35", seed: nil)]))
        let request = FrenchAssessmentRequest(referenceIndex: URL(fileURLWithPath: "/references.sqlite"), output: URL(fileURLWithPath: "/new-folder"), seed: 270100, largePrint: false, excludedFamilies: [0,1,2,3,4])
        XCTAssertEqual(Array(request.arguments.suffix(10)), ["--exclude-family","0","--exclude-family","1","--exclude-family","2","--exclude-family","3","--exclude-family","4"])
        let defaults = isolatedDefaults()
        defaults.set("fr", forKey: "interfaceLanguage")
        let backend = ControlledRunBackend()
        let application = isolatedApplication(defaults: defaults, backend: backend)
        for job in jobs { try application.recentDocumentStore.save(job) }
        XCTAssertEqual(try application.savedFrenchFamilies(), [0,1,2,3,4])
        for job in jobs { try application.recentDocumentStore.remove(job) }
        XCTAssertEqual(try application.savedFrenchFamilies(), [0,1,2,3,4])
        application.outputFolder = temporaryDirectory.appendingPathComponent("another-output")
        application.generateFrenchFixture(largePrint: false)
        XCTAssertTrue(application.isRunning)
        XCTAssertFalse(application.showError)
        XCTAssertEqual(backend.requests.count, 1)
        XCTAssertTrue(backend.requests[0].arguments.contains("v36"))
        XCTAssertFalse(backend.requests[0].arguments.contains("--repeat-practice"))
        XCTAssertEqual(application.recentDocumentStore.records.count, 1)
        XCTAssertFalse(FileManager.default.fileExists(atPath: application.outputFolder.path))
        application.cancelGeneration()
        defaults.set(["unknown-family"], forKey: AppStorageKey.frenchSavedFamilyIDs)
        XCTAssertThrowsError(try application.savedFrenchFamilies())
    }

    @MainActor
    func testSixthFrenchRequestStartsWithoutClearingHistoryOrChangingRequestedSeed() throws {
        let backend = ControlledRunBackend()
        let application = isolatedApplication(backend: backend)
        for seed in 0 ..< 5 {
            let record = GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: "fr-national-nsi", paperID: "written-2027", provider: "application-owned", model: FrenchAssessmentRequest.modelID, seed: seed, dryRun: false, assessmentID: FrenchAssessmentRequest.assessmentID),
                provenance: GenerationProvenance(appVersion: "fixture", provider: "application-owned", model: FrenchAssessmentRequest.modelID),
                state: .completed, artifacts: [], qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
            )
            try application.recentDocumentStore.save(record)
        }
        let prior = application.recentDocumentStore.records
        application.generateFrenchFixture(largePrint: true)

        let request = try XCTUnwrap(backend.requests.first)
        let seedIndex = try XCTUnwrap(request.arguments.firstIndex(of: "--seed"))
        let requestedSeed = try XCTUnwrap(Int(request.arguments[seedIndex + 1]))
        XCTAssertTrue(application.isRunning)
        XCTAssertEqual(application.pendingGenerationSeed, requestedSeed)
        XCTAssertEqual(application.generationCoordinator.activeJob?.configuration.seed, requestedSeed)
        XCTAssertFalse(request.arguments.contains("--repeat-practice"))
        XCTAssertTrue(request.arguments.contains("--large-print"))
        XCTAssertFalse(request.arguments.contains("--exclude-family"))
        XCTAssertTrue(request.arguments.contains("--model"))
        XCTAssertEqual(application.recentDocumentStore.records.filter { $0.state == .completed }, prior)
        XCTAssertEqual(try application.savedFrenchFamilies(), [0, 1, 2, 3, 4])
        application.cancelGeneration()
    }

    @MainActor
    func testFrenchPreparationProgressUsesTheSelectedLanguage() {
        let message = "Construction des exercices vérifiés, sans appel à un modèle."
        XCTAssertEqual(GenerationPresentation.progress(message, language: "en"), "Preparing the practice paper.")
        XCTAssertEqual(GenerationPresentation.progress(message, language: "fr"), "Préparation du sujet d’entraînement.")
    }

    private var temporaryDirectory: URL!

    private static func fixtureRoot() -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("KeldinCoordinatorTests-\(UUID().uuidString)")
    }

    private static func catalogSuiteName() -> String {
        "KeldinCatalogTests-\(UUID().uuidString)"
    }

    func testFixtureRootsAndPreferenceDomainsAreUniqueAcrossConstructions() {
        let firstRoot = Self.fixtureRoot()
        let secondRoot = Self.fixtureRoot()
        XCTAssertNotEqual(firstRoot, secondRoot)
        XCTAssertEqual(firstRoot.deletingLastPathComponent(), FileManager.default.temporaryDirectory)
        XCTAssertNotEqual(Self.catalogSuiteName(), Self.catalogSuiteName())
    }

    override func setUpWithError() throws {
        temporaryDirectory = Self.fixtureRoot()
        try FileManager.default.createDirectory(
            at: temporaryDirectory,
            withIntermediateDirectories: true
        )
    }

    override func tearDownWithError() throws {
        if let temporaryDirectory {
            try? FileManager.default.removeItem(at: temporaryDirectory)
        }
    }

    private func qualityReport() throws -> GenerationQualityReport {
        let url = temporaryDirectory.appendingPathComponent("quality.json")
        let manifest = #"{"request":{"subject":"economics_aqa","paper":"1","seed":42,"preview_mode":false},"evidence":{"assessment_validation":{"form_id":"form","item_count":1,"fingerprints_verified":true,"authoring_provenance":{"schema_version":1,"items":1,"counts":{"reviewed-fixed":1},"reviewed_fixed_items":1,"ai_authored_items":0,"ai_authored_stem_items":0,"unreviewed_or_builtin_items":0,"unknown_items":0},"reference_demand":{"passed":true,"items_checked":1,"failed_checks":[],"item_review_evidence":{"reviewed_items":1,"approved_items":1,"coverage":1.0,"reasoning_range_fit":1,"context_fit":1,"shortcut_resistant":1}}},"novelty_validation":{"passed":true,"historic_comparisons":1}},"outputs":{}}"#
        try Data(manifest.utf8).write(to: url)
        return try XCTUnwrap(GenerationQualityReport.load(from: url))
    }

    @MainActor
    func testHistoryPersistsVersionedJobAndRestoresAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        let record = GenerationJobRecord.fixture(state: .completed)
        try original.save(record)

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records, [record])
        XCTAssertEqual(relaunched.records.first?.schemaVersion, GenerationJobRecord.currentSchemaVersion)
    }

    @MainActor
    func testCompletionRecordsExportedArtifactLocations() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        let coordinator = GenerationCoordinator(history: store)
        let record = GenerationJobRecord.fixture(state: .pending)
        try coordinator.begin(record)
        coordinator.receive(.file(role: "question_paper", path: "/private/working/sujet.pdf"), expectedJobID: record.id)
        let exported = GeneratedFile(role: "question_paper", url: temporaryDirectory.appendingPathComponent("sujet.pdf"))
        try Data("PDF fixture".utf8).write(to: exported.url)
        try coordinator.complete(expectedJobID: record.id, artifacts: [exported])
        XCTAssertEqual(store.records.first?.artifacts.map(\.url), [exported.url])
    }

    @MainActor
    func testFrenchCompletionRecordsThePublishedSeed() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        let coordinator = GenerationCoordinator(history: store)
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: "fr-national-nsi", paperID: "written-2027",
                provider: "application-owned", model: "app-owned-v35", seed: 270100,
                dryRun: false, educationSystem: "fr-national",
                assessmentID: FrenchAssessmentRequest.assessmentID, documentLanguage: "fr-FR"
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "application-owned", model: "app-owned-v35"),
            state: .pending, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let manifest = temporaryDirectory.appendingPathComponent("manifest.json")
        try coordinator.begin(record)
        XCTAssertThrowsError(try coordinator.complete(expectedJobID: record.id))
        XCTAssertEqual(store.records.first?.state, .running)
        let payload = #"{"schema_version":1,"assessment":"fr-bac-general-nsi-written-2027","status":"unreviewed_draft","generation_origin":"application_owned","model_used":false,"teacher_review":"not_run","empirical_calibration":"not_run","identity":{"provider":"application-owned","model":"app-owned-v35","seed":270101,"prompt_version":"fr-nsi-written-2027-v35","print_policy":"fr-nsi-v35-internal-review-v1"}}"#
        try Data(payload.utf8).write(to: manifest)
        let original = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(payload.utf8)) as? [String: Any])
        for (key, value) in ["seed": true, "print_policy": "approved", "model": "app-owned-v32"] as [String: Any] {
            var changed = original
            var identity = try XCTUnwrap(changed["identity"] as? [String: Any])
            identity[key] = value
            changed["identity"] = identity
            try JSONSerialization.data(withJSONObject: changed).write(to: manifest)
            XCTAssertThrowsError(try FrenchAssessmentRequest.publishedSeed(from: manifest))
        }
        for (key, value) in ["teacher_review": "passed", "empirical_calibration": "passed", "status": "approved"] {
            var changed = original
            changed[key] = value
            try JSONSerialization.data(withJSONObject: changed).write(to: manifest)
            XCTAssertThrowsError(try FrenchAssessmentRequest.publishedSeed(from: manifest))
        }
        try Data(payload.utf8).write(to: manifest)
        let file = GeneratedFile(role: "package_manifest", url: manifest)
        XCTAssertThrowsError(try coordinator.complete(expectedJobID: record.id, artifacts: [file], expectedFrenchPolicy: .repeatPractice))
        try coordinator.complete(expectedJobID: record.id, artifacts: [file])
        XCTAssertEqual(store.records.first?.id, record.id)
        XCTAssertEqual(store.records.first?.configuration.seed, 270101)
        XCTAssertEqual(store.records.first?.configuration.model, "app-owned-v35")
        XCTAssertEqual(store.records.first?.qualification, record.qualification)
        XCTAssertEqual(store.records.first?.state, .completed)
        var repeated = original
        repeated["practice_policy"] = "repeat-practice-v1"
        repeated["cross_history_comparison"] = "not_performed"
        try JSONSerialization.data(withJSONObject: repeated).write(to: manifest)
        XCTAssertEqual(try FrenchAssessmentRequest.publishedSeed(from: manifest, expectedPolicy: .repeatPractice), 270101)
        XCTAssertThrowsError(try FrenchAssessmentRequest.publishedSeed(from: manifest))
        repeated["practice_policy"] = "unknown-version"
        try JSONSerialization.data(withJSONObject: repeated).write(to: manifest)
        XCTAssertThrowsError(try FrenchAssessmentRequest.publishedSeed(from: manifest, expectedPolicy: .repeatPractice))
    }

    @MainActor
    func testRunningJobBecomesInterruptedAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try original.save(.fixture(state: .running))

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records.first?.state, .interrupted)
    }

    @MainActor
    func testSchemaZeroHistoryMigratesWithoutLosingConfiguration() throws {
        let record = GenerationJobRecord.fixture(state: .completed)
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(record)
        var payload = try XCTUnwrap(
            JSONSerialization.jsonObject(with: data) as? [String: Any]
        )
        payload.removeValue(forKey: "schemaVersion")
        let legacyData = try JSONSerialization.data(withJSONObject: payload)
        try legacyData.write(
            to: temporaryDirectory.appendingPathComponent("\(record.id.uuidString).json")
        )

        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.load()

        XCTAssertEqual(store.records.first?.schemaVersion, 1)
        XCTAssertEqual(store.records.first?.configuration, record.configuration)
        XCTAssertEqual(store.quarantinedRecordCount, 0)
    }

    @MainActor
    func testCancelledJobRemainsCancelledAfterRelaunch() throws {
        let original = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try original.save(.fixture(state: .cancelled))

        let relaunched = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try relaunched.load()

        XCTAssertEqual(relaunched.records.first?.state, .cancelled)
    }

    @MainActor
    func testCorruptHistoryIsQuarantinedWithoutDiscardingValidJobs() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.save(.fixture(state: .completed))
        try Data("not json".utf8).write(to: temporaryDirectory.appendingPathComponent("broken.json"))

        try store.load()

        XCTAssertEqual(store.records.count, 1)
        XCTAssertEqual(store.quarantinedRecordCount, 1)
        let quarantine = temporaryDirectory.appendingPathComponent("Quarantine", isDirectory: true)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: quarantine.path).count, 1)
    }

    @MainActor
    func testCompletedJobWithMissingArtifactIsMarkedActionably() throws {
        let missing = GeneratedFile(
            role: "question_paper",
            url: temporaryDirectory.appendingPathComponent("missing.pdf")
        )
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 10)
        try store.save(.fixture(state: .completed, artifacts: [missing]))

        try store.load()

        XCTAssertEqual(store.records.first?.state, .missingArtifacts)
        XCTAssertEqual(store.records.first?.missingArtifactCount, 1)
    }

    @MainActor
    func testRetentionIsBoundedAndDuplicateConfigurationGetsNewIdentity() throws {
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 2)
        let first = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 1)
        )
        let second = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 2)
        )
        let third = GenerationJobRecord.fixture(
            state: .completed,
            createdAt: Date(timeIntervalSince1970: 3)
        )
        try store.save(first)
        try store.save(second)
        try store.save(third)

        XCTAssertEqual(store.records.map(\.id), [third.id, second.id])
        let duplicate = store.duplicateConfiguration(of: third, newSeed: 99)
        XCTAssertNotEqual(duplicate.id, third.id)
        XCTAssertEqual(duplicate.configuration.seed, 99)
        XCTAssertEqual(duplicate.state, .pending)
        XCTAssertTrue(duplicate.artifacts.isEmpty)
    }

    @MainActor
    func testModelCoordinatorExpiresStaleModelList() {
        let clock = TestClock(now: Date(timeIntervalSince1970: 1_000))
        let coordinator = ModelCoordinator(clock: clock, staleAfter: 60)
        coordinator.receiveModels(["gemma4:12b"], at: clock.now)
        XCTAssertFalse(coordinator.isModelListStale)

        clock.now = Date(timeIntervalSince1970: 1_061)
        XCTAssertTrue(coordinator.isModelListStale)
    }

    @MainActor
    func testCatalogStoreFiltersAndPersistsFavouritesAndRecentConfigurations() throws {
        let suite = Self.catalogSuiteName()
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        store.searchText = "computer"

        XCTAssertTrue(store.filteredSubjects.allSatisfy { subject in
            subject.title.localizedCaseInsensitiveContains("computer")
                || subject.boards.contains {
                    $0.title.localizedCaseInsensitiveContains("computer")
                        || $0.subjectTitle.localizedCaseInsensitiveContains("computer")
                }
        })
        let board = try XCTUnwrap(ExamCatalog.readyBoards.first)
        store.toggleFavourite(board.id)
        store.recordRecentConfiguration(boardID: board.id, paperID: board.papers[0].id)

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.favoriteIDs, [board.id])
        XCTAssertEqual(restored.recentConfigurationIDs.first, "\(board.id)::\(board.papers[0].id)")
    }

    @MainActor
    func testSidebarDefaultsToAvailableBoardsButSearchRevealsPlannedBoards() throws {
        let suite = "KeldinSidebarFocusTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)

        XCTAssertFalse(store.filteredSubjects.isEmpty)
        XCTAssertTrue(store.filteredSubjects.allSatisfy { subject in
            !subject.boards.isEmpty && subject.boards.allSatisfy(\.isReady)
        })

        store.searchText = "Biology"
        XCTAssertTrue(store.filteredSubjects.contains { subject in
            subject.title == "Biology"
                && subject.boards.contains { $0.status == .placeholder }
        })

        let plannedBoard = try XCTUnwrap(ExamCatalog.board(id: "biology-aqa"))
        XCTAssertTrue(store.selectBoard(plannedBoard, isLocked: false))
        store.searchText = ""
        XCTAssertTrue(store.filteredSubjects.contains { subject in
            subject.boards.contains { $0.id == plannedBoard.id }
        })
        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.sidebarSelection, .board(plannedBoard.id))
        XCTAssertTrue(restored.filteredSubjects.contains { subject in
            subject.boards.contains { $0.id == plannedBoard.id }
        })
    }

    func testSidebarSearchExpandsMatchingSubjectWithoutChangingSavedDisclosureState() {
        XCTAssertFalse(SidebarExpansionPolicy.isExpanded(
            subjectID: "biology", savedExpandedIDs: [], searchText: " "
        ))
        XCTAssertTrue(SidebarExpansionPolicy.isExpanded(
            subjectID: "biology", savedExpandedIDs: [], searchText: "biology"
        ))
        XCTAssertTrue(SidebarExpansionPolicy.isExpanded(
            subjectID: "biology", savedExpandedIDs: ["biology"], searchText: ""
        ))
    }

    @MainActor
    func testCatalogStoreOwnsAndRestoresValidSelection() throws {
        let suite = "KeldinCatalogSelectionTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let board = try XCTUnwrap(ExamCatalog.readyBoards.last)
        let paper = try XCTUnwrap(board.papers.last)

        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertTrue(store.selectBoard(board, isLocked: false))
        XCTAssertTrue(store.selectPaperID(paper.id, isLocked: false))

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.selectedBoardID, board.id)
        XCTAssertEqual(restored.selectedPaperID, paper.id)
        XCTAssertEqual(restored.sidebarSelection, .board(board.id))
        XCTAssertFalse(restored.selectPaperID("not-a-paper", isLocked: false))
    }

    @MainActor
    func testCatalogStoreRestoresNonBoardNavigationDestination() throws {
        let suite = "KeldinCatalogNavigationTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }

        let store = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        store.show(.history)

        let restored = CatalogStore(subjects: ExamCatalog.subjects, defaults: defaults)
        XCTAssertEqual(restored.sidebarSelection, .history)
    }

    @MainActor
    func testSettingsStorePersistsPreferencesAndDelegatesSecrets() throws {
        let suite = "KeldinSettingsTests-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let secrets = MemorySecrets()
        let settings = SettingsStore(defaults: defaults, secrets: secrets)
        settings.provider = .apple
        settings.appleModel = "mlx-community/test"
        settings.historyRetentionLimit = 0
        settings.openAIAPIKey = "private-test-value"
        settings.save()

        let restored = SettingsStore(defaults: defaults, secrets: secrets)
        XCTAssertEqual(restored.provider, .apple)
        XCTAssertEqual(restored.appleModel, "mlx-community/test")
        XCTAssertEqual(restored.historyRetentionLimit, 1)
        XCTAssertEqual(restored.openAIAPIKey, "private-test-value")
    }

    @MainActor
    func testApplicationPreferencesStayWithinTheirInjectedSuite() {
        let firstDefaults = isolatedDefaults()
        let secondDefaults = isolatedDefaults()
        firstDefaults.set(true, forKey: AppStorageKey.dryRun)
        let first = isolatedApplication(defaults: firstDefaults)
        let second = isolatedApplication(defaults: secondDefaults)

        XCTAssertTrue(first.dryRun)
        XCTAssertFalse(second.dryRun)
        second.setDryRun(true)
        first.setDryRun(false)
        XCTAssertFalse(firstDefaults.bool(forKey: AppStorageKey.dryRun))
        XCTAssertTrue(secondDefaults.bool(forKey: AppStorageKey.dryRun))
        first.openAIAPIKey = "isolated-test-key"
        first.settingsStore.openAIAPIKey = first.openAIAPIKey
        first.settingsStore.save()
        XCTAssertTrue(second.settingsStore.openAIAPIKey.isEmpty)
    }

    @MainActor
    func testApplicationCoordinatorOwnsFocusedCoordinators() {
        let model = isolatedApplication()

        XCTAssertEqual(model.settingsStore.provider, model.aiProvider)
        XCTAssertEqual(model.catalogStore.subjects, ExamCatalog.subjects)
        XCTAssertTrue(model.modelCoordinator.isModelListStale)
        XCTAssertFalse(model.benchmarkCoordinator.isRunning)
        XCTAssertGreaterThan(model.recentDocumentStore.retentionLimit, 0)
        XCTAssertNil(model.generationCoordinator.activeJob)
    }

    @MainActor
    func testSavedReportClearsOnlyForAcceptedTargetChanges() throws {
        let model = isolatedApplication(backend: ControlledRunBackend())
        let board = try XCTUnwrap(
            ExamCatalog.readyBoards.first { $0.papers.count > 1 }
        )
        model.selectBoard(board)
        let original = model.selectedPaperID
        let changed = try XCTUnwrap(board.papers.first { $0.id != original })
        let report = try qualityReport()

        model.lastQualityReport = report
        model.selectPaperID(original)
        XCTAssertEqual(model.lastQualityReport, report)
        model.selectPaperID("not-a-paper")
        XCTAssertEqual(model.lastQualityReport, report)
        model.prepareFrenchReferences()
        model.lastQualityReport = report
        model.selectPaperID(changed.id)
        XCTAssertEqual(model.lastQualityReport, report)
        model.cancelGeneration()
        model.selectPaperID(changed.id)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testModeToggleAndArtifactOnlyRelaunchDoNotInventOrChangeSavedFacts() throws {
        let model = isolatedApplication()
        let report = try qualityReport()
        model.lastQualityReport = report

        model.setDryRun(!model.dryRun)

        XCTAssertEqual(model.lastQualityReport, report)
        XCTAssertEqual(model.lastQualityReport?.savedMode, .live)
        XCTAssertEqual(
            model.qualityDiagnosticLines,
            GenerationQualityPolicy.presentation(for: report).diagnosticLines
        )
        XCTAssertNil(isolatedApplication().lastQualityReport)
    }

    @MainActor
    func testAssessmentKindChangeClearsSavedReportOnAcceptedNewTarget() throws {
        let model = isolatedApplication()
        let board = try XCTUnwrap(
            ExamCatalog.readyBoards.first {
                !$0.fullPapers.isEmpty && !$0.questionBanks.isEmpty
            }
        )
        model.selectBoard(board)
        model.lastQualityReport = try qualityReport()

        model.selectAssessmentKind(.questionBank)

        XCTAssertEqual(model.selectedPaper.assessmentKind, .questionBank)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testDuplicateConfigurationRestoresSelectionsAndSeed() throws {
        let model = isolatedApplication()
        let record = GenerationJobRecord.fixture(state: .completed)

        model.duplicateConfiguration(record)

        XCTAssertEqual(model.selectedBoardID, record.configuration.boardID)
        XCTAssertEqual(model.selectedPaperID, record.configuration.paperID)
        XCTAssertEqual(model.aiProvider.backendID, record.configuration.provider)
        XCTAssertEqual(model.pendingGenerationSeed, record.configuration.seed)
        XCTAssertEqual(model.sidebarSelection, .board(record.configuration.boardID))
    }

    @MainActor
    func testReportedBackendFailureFinalizesHistoryAndReleasesSeed() throws {
        let backend = ControlledRunBackend()
        let defaults = isolatedDefaults()
        defaults.set(true, forKey: AppStorageKey.hasSeenWelcome)
        defaults.set(false, forKey: AppStorageKey.notificationsEnabled)
        let model = isolatedApplication(defaults: defaults, backend: backend)
        let record = GenerationJobRecord.fixture(state: .pending)
        model.duplicateConfiguration(record)
        model.setDryRun(true)
        model.generate()
        let job = try XCTUnwrap(model.generationCoordinator.activeJob)
        let run = try XCTUnwrap(backend.requests.first)
        run.onEvent(.error(message: "Checkpoint identity changed", code: "french_generation_failed"))
        run.onFinish(.success(1))
        XCTAssertNil(model.pendingGenerationSeed)
        XCTAssertNil(model.generationCoordinator.activeJob)
        XCTAssertEqual(model.recentDocumentStore.records.first(where: { $0.id == job.id })?.state, .failed)
    }

    @MainActor
    func testFrenchHistoryPreservesContextWithoutUKBoardLookup() throws {
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: "fr-national-nsi", paperID: "written-2027", provider: "ollama",
                model: "fixture", seed: 55, dryRun: false, educationSystem: "fr-national",
                assessmentID: FrenchAssessmentRequest.assessmentID, documentLanguage: "fr-FR"
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let store = RecentDocumentStore(directory: temporaryDirectory, retentionLimit: 2)
        XCTAssertEqual(store.duplicateConfiguration(of: record).configuration, record.configuration)
        let model = isolatedApplication()
        model.duplicateConfiguration(record)
        XCTAssertEqual(model.sidebarSelection, .frenchBaccalaureat)
        XCTAssertEqual(model.pendingGenerationSeed, 55)
        XCTAssertEqual(model.selectedModel, "fixture")
    }

    @MainActor
    func testAppOwnedFrenchHistoryRestoresSeedWithoutChangingUKModel() {
        let record = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: "fr-national-nsi", paperID: "written-2027", provider: "application-owned",
                model: "app-owned-v32", seed: 270101, dryRun: false, educationSystem: "fr-national",
                assessmentID: FrenchAssessmentRequest.assessmentID, documentLanguage: "fr-FR"
            ),
            provenance: GenerationProvenance(appVersion: "test", provider: "application-owned", model: "app-owned-v32"),
            state: .completed, artifacts: [],
            qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
        )
        let model = isolatedApplication()
        model.selectedModel = "uk-model"
        model.duplicateConfiguration(record)
        XCTAssertEqual(model.sidebarSelection, .frenchBaccalaureat)
        XCTAssertEqual(model.pendingGenerationSeed, 270101)
        XCTAssertEqual(model.selectedModel, "uk-model")
    }

    @MainActor
    func testInvalidConfigurationDoesNotClearSavedReportOrChangeTarget() throws {
        let model = isolatedApplication()
        let report = try qualityReport()
        model.lastQualityReport = report
        let originalBoard = model.selectedBoardID
        let originalPaper = model.selectedPaperID
        let differentBoard = try XCTUnwrap(
            ExamCatalog.readyBoards.first { $0.id != originalBoard }
        )
        let fixture = GenerationJobRecord.fixture(state: .completed)
        let invalid = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: differentBoard.id,
                paperID: "not-a-paper",
                provider: fixture.configuration.provider,
                model: fixture.configuration.model,
                seed: fixture.configuration.seed,
                dryRun: fixture.configuration.dryRun
            ),
            provenance: fixture.provenance,
            state: fixture.state,
            artifacts: fixture.artifacts,
            qualification: fixture.qualification
        )

        model.duplicateConfiguration(invalid)

        XCTAssertEqual(model.selectedBoardID, originalBoard)
        XCTAssertEqual(model.selectedPaperID, originalPaper)
        XCTAssertEqual(model.lastQualityReport, report)
    }

    @MainActor
    func testApplyingHistoryConfigurationUsesAcceptedTargetChangePolicy() throws {
        let model = isolatedApplication()
        let fixture = GenerationJobRecord.fixture(state: .completed)
        let board = try XCTUnwrap(ExamCatalog.board(id: fixture.configuration.boardID))
        model.selectBoard(board)
        model.selectPaperID(fixture.configuration.paperID)
        let report = try qualityReport()
        model.lastQualityReport = report

        model.duplicateConfiguration(fixture)
        XCTAssertEqual(model.lastQualityReport, report)

        let otherPaper = try XCTUnwrap(
            board.papers.first { $0.id != fixture.configuration.paperID }
        )
        let changed = GenerationJobRecord(
            configuration: GenerationConfiguration(
                boardID: board.id,
                paperID: otherPaper.id,
                provider: fixture.configuration.provider,
                model: fixture.configuration.model,
                seed: fixture.configuration.seed,
                dryRun: fixture.configuration.dryRun
            ),
            provenance: fixture.provenance,
            state: fixture.state,
            artifacts: fixture.artifacts,
            qualification: fixture.qualification
        )
        model.duplicateConfiguration(changed)

        XCTAssertEqual(model.selectedPaperID, otherPaper.id)
        XCTAssertNil(model.lastQualityReport)
    }

    @MainActor
    func testCreateAgainUsesDifferentSeedAndPreviewOpensDocuments() throws {
        let model = isolatedApplication()
        let record = GenerationJobRecord.fixture(state: .completed)
        let file = GeneratedFile(
            role: "question_paper",
            url: temporaryDirectory.appendingPathComponent("paper.pdf")
        )

        model.createAgainWithNewSeed(record)
        model.previewGeneratedFile(file)

        XCTAssertNotEqual(model.pendingGenerationSeed, record.configuration.seed)
        XCTAssertEqual(model.previewedFileID, file.id)
        XCTAssertEqual(model.sidebarSelection, .documents)
    }

    @MainActor
    func testRolePreviewUsesNewestDocumentAndRefreshesReplacedFiles() throws {
        let model = isolatedApplication()
        let oldURL = temporaryDirectory.appendingPathComponent("old.pdf")
        let newURL = temporaryDirectory.appendingPathComponent("new.pdf")
        model.apply(.file(role: "question_paper", path: oldURL.path))
        model.apply(.file(role: "question_paper", path: newURL.path))
        let firstVersion = try XCTUnwrap(model.generatedFiles.first)
        model.previewGeneratedFile(role: "question_paper")
        XCTAssertEqual(model.previewedFileID, firstVersion.id)

        model.apply(.file(role: "question_paper", path: newURL.path))
        let replacement = try XCTUnwrap(model.generatedFiles.first)
        XCTAssertNotEqual(replacement.id, firstVersion.id)
        XCTAssertEqual(model.generatedFiles.filter { $0.url == newURL }.count, 1)
        model.previewGeneratedFile(role: "question_paper")
        XCTAssertEqual(model.previewedFileID, replacement.id)
    }

    @MainActor
    func testRestoredDocumentLibraryDeduplicatesReplacedPaths() throws {
        let defaults = isolatedDefaults()
        let url = temporaryDirectory.appendingPathComponent("paper.pdf")
        let newest = GeneratedFile(role: "question_paper", url: url)
        let older = GeneratedFile(role: "question_paper", url: url)
        defaults.set(try JSONEncoder().encode([newest, older]), forKey: AppStorageKey.recentDocuments)
        let model = isolatedApplication(defaults: defaults)
        XCTAssertEqual(model.generatedFiles.map(\.id), [newest.id])
    }

    @MainActor
    func testGenerationArtifactsExcludeEarlierLibraryDocuments() {
        let model = isolatedApplication()
        model.apply(.file(role: "question_paper", path: temporaryDirectory.appendingPathComponent("old.pdf").path))
        model.beginDocumentCollection()
        model.apply(.file(role: "question_paper", path: temporaryDirectory.appendingPathComponent("new.pdf").path))
        XCTAssertEqual(model.generatedFiles.count, 2)
        XCTAssertEqual(model.currentGenerationFiles.map { $0.url.lastPathComponent }, ["new.pdf"])
    }

    func testDocumentProvenanceRejectsAmbiguousOrReusedPaths() {
        let file = GeneratedFile(role: "question_paper", url: temporaryDirectory.appendingPathComponent("paper.pdf"))
        let first = GenerationJobRecord.fixture(state: .completed, artifacts: [file])
        let duplicate = GenerationJobRecord.fixture(state: .completed, artifacts: [file])
        XCTAssertNil(PDFDocumentActions.provenanceRecord(for: file, records: [first, duplicate]))
        XCTAssertEqual(PDFDocumentActions.provenanceRecord(for: file, records: [first])?.id, first.id)
        let replacement = GeneratedFile(role: "question_paper", url: file.url)
        XCTAssertNil(PDFDocumentActions.provenanceRecord(for: replacement, records: [first]))
    }

    func testCopiedProvenanceIdentifiesConfigurationAndQualification() {
        let record = GenerationJobRecord.fixture(state: .completed)

        let summary = record.provenanceSummary

        XCTAssertTrue(summary.contains("economics-aqa · Paper 1"))
        XCTAssertTrue(summary.contains("Ollama · gemma4:12b · Seed 42"))
        XCTAssertTrue(summary.contains("Engineering: passed"))
        XCTAssertTrue(summary.contains("Visual: pending"))
        XCTAssertTrue(summary.contains("Empirical: pending"))
    }
}

private extension GenerationJobRecord {
    static func fixture(
        state: GenerationJobState,
        createdAt: Date = Date(timeIntervalSince1970: 10),
        artifacts: [GeneratedFile] = []
    ) -> GenerationJobRecord {
        GenerationJobRecord(
            id: UUID(),
            configuration: GenerationConfiguration(
                boardID: "economics-aqa",
                paperID: "1",
                provider: "ollama",
                model: "gemma4:12b",
                seed: 42,
                dryRun: false
            ),
            provenance: GenerationProvenance(
                appVersion: "test",
                provider: "ollama",
                model: "gemma4:12b"
            ),
            state: state,
            artifacts: artifacts,
            qualification: QualificationSnapshot(
                engineeringValidated: true,
                visuallyCalibrated: false,
                empiricallyCalibrated: false
            ),
            createdAt: createdAt,
            updatedAt: createdAt
        )
    }
}

private final class TestClock: AppClock {
    var now: Date

    init(now: Date) {
        self.now = now
    }
}

private final class MemorySecrets: SecretStoring {
    private var values: [String: String] = [:]

    func read(_ account: String) -> String {
        values[account] ?? ""
    }

    func save(_ value: String, account: String) {
        values[account] = value
    }
}
