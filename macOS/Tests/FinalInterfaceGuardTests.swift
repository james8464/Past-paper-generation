import XCTest
@testable import Keldin

final class FinalInterfaceGuardTests: XCTestCase {
    func testLocalModalContextBlocksCreationAndNavigationThenRestoresItsPrintChoice() {
        for original in [KeldinCreationContext.board, .french(largePrint: false), .french(largePrint: true)] {
            let modal = original.presentingModal(true)
            XCTAssertFalse(modal.canCreate(boardCanGenerate: true, hasFrenchReferences: true, isBusy: false))
            XCTAssertFalse(KeldinCreationContext.allowsNavigation(from: modal, applicationModal: false))
            let restored = original.presentingModal(false)
            XCTAssertEqual(restored, original)
            XCTAssertEqual(restored.frenchLargePrint, original.frenchLargePrint)
            XCTAssertTrue(KeldinCreationContext.allowsNavigation(from: restored, applicationModal: false))
        }
        XCTAssertTrue(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: false))
        XCTAssertFalse(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: true))
    }

    @MainActor
    func testEveryExistingGlobalPresentationBlocksCommandsWithoutMirroredState() {
        let application = isolatedApplication()
        application.showWelcome = false
        let flags: [ReferenceWritableKeyPath<ApplicationCoordinator, Bool>] = [
            \.showWelcome, \.showHelp, \.showError, \.showHostedAIConsent,
            \.showMLXSetupConfirmation, \.showPullConfirmation,
        ]
        XCTAssertFalse(application.hasCommandBlockingPresentation)
        for flag in flags {
            application[keyPath: flag] = true
            XCTAssertTrue(application.hasCommandBlockingPresentation)
            application[keyPath: flag] = false
            XCTAssertFalse(application.hasCommandBlockingPresentation)
        }
    }

    func testNotificationCopyUsesSelectedFrenchAndKeepsRawDetails() {
        let detail = "Backend code E42 /private/fixture.sql: échec"
        let cases: [(WorkNotification, String, String)] = [
            (.paperStarted(subject: "NSI", paper: "Sujet"), "Création du sujet", "NSI · Sujet"),
            (.paperReady(folder: "Dossier"), "Votre sujet est prêt", "Le sujet et le corrigé se trouvent dans Dossier."),
            (.paperFailed(detail: detail), "Impossible de créer le sujet", detail),
            (.modelStarted(model: "fixture/model"), "Téléchargement du modèle", "Ollama télécharge fixture/model."),
            (.modelReady(model: "fixture/model"), "Modèle prêt", "fixture/model est disponible dans Ollama."),
            (.modelFailed(detail: detail), "Impossible de télécharger le modèle", detail),
            (.mlxStarted, "Configuration d’Apple MLX", "Keldin prépare le modèle local sélectionné."),
            (.mlxReady, "Apple MLX est prêt", "Le modèle sélectionné est prêt pour la création locale."),
            (.mlxFailed(detail: detail), "La configuration d’Apple MLX nécessite votre attention", detail),
        ]
        for (event, title, body) in cases {
            XCTAssertEqual(event.content(language: "fr"), WorkNotificationContent(title: title, body: body))
        }
        XCTAssertEqual(WorkNotification.paperReady(folder: "Test").content(language: "en"), WorkNotificationContent(title: "Your paper is ready", body: "The paper and mark scheme are in Test."))
        for event in [WorkNotification.paperFailed(detail: detail), .modelFailed(detail: detail), .mlxFailed(detail: detail)] {
            XCTAssertEqual(event.content(language: "en").body, detail)
            XCTAssertEqual(event.content(language: "fr").body, detail)
        }
    }

    func testAllNotificationEventsRetainTheirEnglishCopy() {
        let cases: [(WorkNotification, String, String)] = [
            (.paperStarted(subject: "Accounting", paper: "Paper 1"), "Creating your paper", "Accounting · Paper 1"),
            (.paperReady(folder: "Test"), "Your paper is ready", "The paper and mark scheme are in Test."),
            (.paperFailed(detail: "Exact failure"), "Couldn’t create the paper", "Exact failure"),
            (.modelStarted(model: "fixture/model"), "Downloading model", "Ollama is downloading fixture/model."),
            (.modelReady(model: "fixture/model"), "Model ready", "fixture/model is available in Ollama."),
            (.modelFailed(detail: "Exact failure"), "Couldn’t download the model", "Exact failure"),
            (.mlxStarted, "Setting up Apple MLX", "Keldin is preparing the selected local model."),
            (.mlxReady, "Apple MLX ready", "The selected model is ready for local generation."),
            (.mlxFailed(detail: "Exact failure"), "Apple MLX setup needs attention", "Exact failure"),
        ]
        for (event, title, body) in cases {
            XCTAssertEqual(event.content(language: "en"), WorkNotificationContent(title: title, body: body))
        }
    }
}
