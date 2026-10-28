import Foundation
import XCTest
@testable import Keldin

final class NativeInterfaceAuditTests: XCTestCase {
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
