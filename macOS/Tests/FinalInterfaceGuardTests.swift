import XCTest
@testable import Keldin

final class FinalInterfaceGuardTests: XCTestCase {
    func testMainOwnedPresentationAllowsRecoveryFromAnotherScene() {
        XCTAssertTrue(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: true, mainSceneIsFocused: false))
        XCTAssertFalse(KeldinCreationContext.allowsNavigation(from: .board, applicationModal: true, mainSceneIsFocused: true))
        XCTAssertFalse(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: false, mainSceneIsFocused: false, settingsModal: true))
    }

    @MainActor
    func testSettingsActionLifetimeRetainsErrorsButCancelsConsentOnClose() throws {
        let owner = SettingsActionPresentation()
        owner.reportError("Retained original error")
        XCTAssertFalse(owner.blocksCommands)
        XCTAssertNil(owner.request)
        owner.activate()
        let error = try XCTUnwrap(owner.request)
        XCTAssertEqual(error.kind, .error("Retained original error"))
        XCTAssertEqual(owner.consume(id: error.id), error)
        owner.requestConsent(for: .openAI)
        let consent = try XCTUnwrap(owner.request)
        owner.presentationDidDismiss(id: consent.id)
        XCTAssertFalse(owner.blocksCommands)
        XCTAssertEqual(owner.consume(id: consent.id), consent)
        XCTAssertNil(owner.consume(id: consent.id))
        owner.requestConsent(for: .anthropic)
        let newer = try XCTUnwrap(owner.request)
        owner.dismiss(id: consent.id)
        XCTAssertEqual(owner.request, newer)
        owner.reportError("Deferred error")
        owner.deactivate()
        XCTAssertFalse(owner.blocksCommands)
        XCTAssertNil(owner.consume(id: newer.id))
        owner.activate()
        XCTAssertEqual(owner.request?.kind, .error("Deferred error"))
        owner.deactivate()
        owner.activate()
        XCTAssertEqual(owner.request?.kind, .error("Deferred error"))
    }

    @MainActor
    func testDownloadApprovalHandlesBothDismissalOrdersWithoutInvisibleCommandBlocking() {
        for dismissFirst in [false, true] {
            let presentation = ModelDownloadPresentation()
            let request = ModelDownloadRequest(model: "fixture/captured")
            presentation.present(request)
            if dismissFirst {
                presentation.presentationDidDismiss(id: request.id)
                XCTAssertFalse(presentation.blocksCommands)
                XCTAssertFalse(presentation.isPresented)
            }
            XCTAssertEqual(presentation.consume(id: request.id), request)
            if !dismissFirst { presentation.presentationDidDismiss(id: request.id) }
            XCTAssertNil(presentation.request)
            XCTAssertFalse(presentation.blocksCommands)
            XCTAssertNil(presentation.consume(id: request.id))

            presentation.present(request)
            presentation.presentationDidDismiss(id: request.id)
            let replacement = ModelDownloadRequest(model: "fixture/replacement")
            presentation.present(replacement)
            presentation.presentationDidDismiss(id: request.id)
            XCTAssertNil(presentation.consume(id: request.id))
            XCTAssertEqual(presentation.request, replacement)
            XCTAssertTrue(presentation.blocksCommands)
            presentation.dismiss(id: replacement.id)
            XCTAssertNil(presentation.consume(id: replacement.id))
            XCTAssertFalse(presentation.blocksCommands)
        }
    }

    @MainActor
    func testDownloadPresentationOwnsOnlyItsSceneAndConsumesTheExactRequestOnce() throws {
        let settings = ModelDownloadPresentation()
        let otherScene = ModelDownloadPresentation()
        let first = ModelDownloadRequest(model: "fixture/first")
        let newer = ModelDownloadRequest(model: "fixture/newer")
        settings.present(first)
        otherScene.present(newer)
        XCTAssertFalse(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: settings.isPresented))
        settings.present(newer)
        XCTAssertEqual(settings.request, first)
        XCTAssertNil(settings.consume(id: newer.id))
        XCTAssertEqual(settings.request, first)
        XCTAssertEqual(settings.consume(id: first.id), first)
        XCTAssertNil(settings.consume(id: first.id))
        XCTAssertTrue(KeldinCreationContext.allowsNavigation(from: nil, applicationModal: settings.isPresented))
        XCTAssertEqual(otherScene.request, newer)

        settings.present(newer)
        settings.dismiss(id: first.id)
        XCTAssertEqual(settings.request, newer)
        settings.dismiss(id: newer.id)
        XCTAssertFalse(settings.isPresented)
        XCTAssertEqual(otherScene.request, newer)
        otherScene.dismiss(id: newer.id)
        XCTAssertFalse(otherScene.isPresented)
        settings.present(nil)
        XCTAssertFalse(settings.isPresented)
    }

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
            \.showMLXSetupConfirmation,
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
