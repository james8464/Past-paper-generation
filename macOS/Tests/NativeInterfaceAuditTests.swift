import Foundation
import XCTest
@testable import Keldin

final class NativeInterfaceAuditTests: XCTestCase {
    func testQualitySheetChromeUsesSelectedLanguageAndSystemLocale() {
        let labels: [(LocalizedStringResource, String, String)] = [
            ("Quality review", "Quality review", "Contrôle de qualité"),
            ("Quality", "Quality", "Qualité"),
            ("Close", "Close", "Fermer"),
        ]
        for (resource, english, french) in labels {
            XCTAssertEqual(InterfaceText.resolve(resource, language: "en"), english)
            XCTAssertEqual(InterfaceText.resolve(resource, language: "fr"), french)
            XCTAssertEqual(InterfaceText.resolve(resource, language: "system"), String(localized: resource))
        }
    }

    @MainActor
    func testRemovedRecentsStayHiddenAcrossRestartAndDuplicateHistory() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinRecentVisibility-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: root) }
        let history = root.appendingPathComponent("history")
        let defaults = UserDefaults(suiteName: "RecentVisibility-\(UUID().uuidString)")!
        let pdf = root.appendingPathComponent("paper.pdf")
        let bytes = Data("preserved source artifact".utf8)
        try bytes.write(to: pdf)
        let first = GeneratedFile(role: "question_paper", url: pdf)
        let duplicate = GeneratedFile(role: "question_paper", url: pdf)
        func app() -> ApplicationCoordinator {
            ApplicationCoordinator(defaults: defaults, secrets: AuditSecrets(), historyDirectory: history)
        }
        let original = app()
        for file in [first, duplicate] { try original.recentDocumentStore.save(record(file)) }
        let populated = app()
        let visible = try XCTUnwrap(populated.generatedFiles.first)
        let records = populated.recentDocumentStore.records
        let equivalentPath = GeneratedFile(role: "question_paper", url: root.appendingPathComponent("sub/../paper.pdf"))
        populated.generatedFiles = [first, duplicate, equivalentPath]
        populated.removeGeneratedFile(visible)

        XCTAssertTrue(populated.generatedFiles.isEmpty)
        XCTAssertTrue(app().generatedFiles.isEmpty)
        XCTAssertEqual(try Data(contentsOf: pdf), bytes)
        XCTAssertEqual(app().recentDocumentStore.records, records)

        let revived = app()
        revived.apply(.file(role: "question_paper", path: pdf.path))
        XCTAssertEqual(revived.generatedFiles.map(\.url), [pdf])
        XCTAssertEqual(app().generatedFiles.map(\.url), [pdf])
    }

    func testFiniteStateLabelsAndQualityDetailsUseChosenFrench() {
        XCTAssertEqual(InterfaceText.resolve(GenerationJobState.completed.titleResource, language: "fr"), "Terminé")
        XCTAssertEqual(InterfaceText.resolve(GenerationJobState.interrupted.titleResource, language: "fr"), "Interrompu")
        XCTAssertEqual(InterfaceText.resolve(GenerationQualityState.atCreation.titleResource, language: "fr"), "À la création")
        let presentation = GenerationQualityPolicy.presentation(for: nil, locale: Locale(identifier: "fr"))
        XCTAssertEqual(presentation.originalityDetail, "Les éléments de contrôle de l’originalité sont créés avec le dossier enregistré.")
        XCTAssertEqual(presentation.pathEvidenceDetail, "Les éléments de contrôle des parcours ne sont pas disponibles.")
        XCTAssertEqual(InterfaceText.resolve(NativeInterfaceCopy.creationTitle(for: .fullPaper), language: "fr"), "Créer un sujet")
        XCTAssertEqual(InterfaceText.resolve(GeneratedFile(role: "mark_scheme", url: URL(fileURLWithPath: "/unused.pdf")).titleResource, language: "fr"), "Corrigé")
        XCTAssertEqual(InterfaceText.resolve("No papers yet", language: "fr"), "Aucun sujet pour le moment")
    }

    func testReferenceLayoutReviewDoesNotClaimGeneratedPDFVerification() {
        let reviewed = GenerationPresentation.referenceLayout(
            savedReviewed: nil, hasSavedReport: false, currentReviewed: true,
            locale: Locale(identifier: "en")
        )
        XCTAssertEqual(reviewed.state, .passed)
        XCTAssertEqual(reviewed.status, "Reference reviewed")
        XCTAssertEqual(reviewed.detail, "The reference layout has been reviewed. This does not verify the generated PDF.")

        let pending = GenerationPresentation.referenceLayout(
            savedReviewed: true, hasSavedReport: false, currentReviewed: false,
            locale: Locale(identifier: "en")
        )
        XCTAssertEqual(pending.state, .pending)
        XCTAssertEqual(pending.status, "Not reviewed")
        XCTAssertEqual(pending.detail, "The reference layout has not been reviewed.")
    }

    func testReferenceLayoutUsesSavedEvidenceBeforeCurrentReadiness() {
        let cases: [(Bool?, Bool, GenerationQualityState, String)] = [
            (true, false, .passed, "Reference reviewed"),
            (false, true, .pending, "Not reviewed"),
            (nil, true, .unknown, "Unknown"),
            (nil, false, .unknown, "Unknown"),
        ]
        for (saved, current, expectedState, expectedStatus) in cases {
            let result = GenerationPresentation.referenceLayout(
                savedReviewed: saved, hasSavedReport: true, currentReviewed: current,
                locale: Locale(identifier: "en")
            )
            XCTAssertEqual(result.state, expectedState)
            XCTAssertEqual(result.status, expectedStatus)
            if saved == nil {
                XCTAssertEqual(result.detail, "This evidence is not recorded in the saved package.")
            }
        }
    }

    func testReferenceLayoutUsesChosenFrenchWithoutChangingReviewState() {
        XCTAssertEqual(InterfaceText.resolve("Reference layout", language: "fr"), "Présentation de référence")
        let result = GenerationPresentation.referenceLayout(
            savedReviewed: true, hasSavedReport: true, currentReviewed: false,
            locale: Locale(identifier: "fr")
        )
        XCTAssertEqual(result.state, .passed)
        XCTAssertEqual(result.status, "Référence examinée")
        XCTAssertEqual(result.detail, "La mise en page de référence a été examinée. Cela ne vérifie pas le PDF généré.")
        let pending = GenerationPresentation.referenceLayout(
            savedReviewed: nil, hasSavedReport: false, currentReviewed: false,
            locale: Locale(identifier: "fr")
        )
        XCTAssertEqual(pending.state, .pending)
        XCTAssertEqual(pending.status, "Non examinée")
        XCTAssertEqual(pending.detail, "La mise en page de référence n'a pas été examinée.")
    }

    func testHelpDescribesCurrentProvidersAndPrivateValidationRecords() throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        let source = try String(contentsOf: root.appendingPathComponent("Keldin/Features/Onboarding/WelcomeHelpViews.swift"), encoding: .utf8)
        let providerCopy: LocalizedStringResource = "Choose Apple Intelligence on a compatible Mac, an installed Ollama model, or a hosted provider in Settings. Read the model's quality warnings before generating."
        let outputCopy: LocalizedStringResource = "PDFs and any supporting files go to your chosen folder after validation. Technical validation records stay in Keldin's private storage."
        XCTAssertTrue(source.contains(InterfaceText.resolve(providerCopy, language: "en")))
        XCTAssertTrue(source.contains(InterfaceText.resolve(outputCopy, language: "en")))
        XCTAssertFalse(source.contains("For local generation, install Ollama and use the model recommended for this Mac."))
        XCTAssertFalse(source.contains("assessment evidence, and package manifest are published together"))
        XCTAssertEqual(InterfaceText.resolve(providerCopy, language: "fr"), "Dans Réglages, choisissez Apple Intelligence sur un Mac compatible, un modèle Ollama installé ou un fournisseur hébergé. Lisez les avertissements sur la qualité du modèle avant de créer un sujet.")
        XCTAssertEqual(InterfaceText.resolve(outputCopy, language: "fr"), "Les PDF et les fichiers d'accompagnement sont enregistrés dans le dossier choisi après validation. Les rapports techniques de validation restent dans l'espace privé de Keldin.")
    }

    @MainActor
    func testWorkspaceBlockerUsesSelectedFrenchWithoutChangingItsDecision() {
        let defaults = UserDefaults(suiteName: "WorkspaceLocale-\(UUID().uuidString)")!
        defaults.set("fr", forKey: "interfaceLanguage")
        let history = FileManager.default.temporaryDirectory.appendingPathComponent("WorkspaceLocale-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: history) }
        let app = ApplicationCoordinator(defaults: defaults, secrets: AuditSecrets(), historyDirectory: history)
        app.showWelcome = true
        XCTAssertFalse(app.canGenerate)
        XCTAssertEqual(app.generationBlocker, "Terminez le guide de bienvenue avant de créer un sujet.")
    }

    func testBenchmarkAccessibilityUsesTheChosenLocale() {
        let french = BenchmarkAccessibility.chartSummary(title: "Charge CPU", unit: "%", values: [], locale: Locale(identifier: "fr"))
        XCTAssertEqual(french, "Charge CPU. Aucun échantillon.")
        let english = BenchmarkAccessibility.chartSummary(title: "CPU Load", unit: "%", values: [], locale: Locale(identifier: "en"))
        XCTAssertEqual(english, "CPU Load. No samples.")
        let values = BenchmarkAccessibility.chartSummary(title: "Charge CPU", unit: "%", values: [1.5, 2.5], locale: Locale(identifier: "fr"))
        XCTAssertTrue(values.contains("2 échantillons"))
        XCTAssertTrue(values.contains("2,5"))
    }

    func testBenchmarkToolbarUsesTheApplicationBoundaryAndDisplaysFailures() throws {
        let root = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
        let source = try String(contentsOf: root.appendingPathComponent("Keldin/Features/Benchmark/BenchmarkView.swift"), encoding: .utf8)
        XCTAssertFalse(source.contains("benchmark.start(generationIsRunning:"))
        XCTAssertTrue(source.contains("application.startBenchmark"))
        XCTAssertTrue(source.contains("application.cancelBenchmark"))
        XCTAssertTrue(source.contains("benchmark.errorMessage"))
    }

    private func record(_ file: GeneratedFile) -> GenerationJobRecord {
        GenerationJobRecord(configuration: GenerationConfiguration(boardID: "economics-aqa", paperID: "1", provider: "ollama", model: "fixture", seed: 1, dryRun: false), provenance: GenerationProvenance(appVersion: "test", provider: "ollama", model: "fixture"), state: .completed, artifacts: [file], qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false))
    }
}

private final class AuditSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
