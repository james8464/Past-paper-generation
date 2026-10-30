import Combine
import Foundation
import Observation
import XCTest
@testable import Keldin

final class ModelDiscoveryOwnershipTests: XCTestCase {
    @MainActor
    func testDiscoveryOwnerStillInvalidatesObservationReaders() async {
        let application = isolatedApplication(backend: ControlledRunBackend())
        let invalidated = expectation(description: "Observation reader invalidated")
        withObservationTracking {
            _ = application.modelCoordinator.availableModels
        } onChange: {
            invalidated.fulfill()
        }
        application.modelCoordinator.receiveModels(["observed-model"])
        await fulfillment(of: [invalidated], timeout: 1)
        XCTAssertEqual(application.availableModels, ["observed-model"])
    }

    @MainActor
    func testBackendDiscoveryEventSendsOneLegacyNotificationForItsAtomicUpdate() {
        let application = isolatedApplication(backend: ControlledRunBackend())
        var notifications = 0
        let subscription = application.objectWillChange.sink { notifications += 1 }
        application.apply(.models(["installed-model"], message: nil))
        XCTAssertEqual(notifications, 1)
        XCTAssertEqual(application.availableModels, application.modelCoordinator.availableModels)
        XCTAssertEqual(application.hasLoadedOllamaModels, application.modelCoordinator.hasLoadedModels)
        XCTAssertNotNil(application.modelCoordinator.lastRefreshDate)
        subscription.cancel()
    }

    @MainActor
    func testDiscoveryOwnerUpdatesReachApplicationAndItsLegacyChangePublisher() {
        let application = isolatedApplication(backend: ControlledRunBackend())
        var snapshots: [[String]] = []
        let subscription = application.objectWillChange.sink {
            snapshots.append(application.availableModels)
        }
        XCTAssertFalse(application.hasLoadedOllamaModels)
        application.modelCoordinator.receiveModels(["installed-model"])
        XCTAssertEqual(application.availableModels, ["installed-model"])
        XCTAssertTrue(application.hasLoadedOllamaModels)
        XCTAssertEqual(snapshots.count, 1)
        XCTAssertEqual(snapshots.first, [])
        subscription.cancel()
    }

    @MainActor
    func testCompatibilitySettersDoNotInventACompletedDiscoveryOrChangeSelection() {
        let application = isolatedApplication(backend: ControlledRunBackend())
        let selected = application.selectedModel
        application.availableModels = ["manual-model"]
        XCTAssertEqual(application.modelCoordinator.availableModels, ["manual-model"])
        XCTAssertFalse(application.hasLoadedOllamaModels)
        XCTAssertNil(application.modelCoordinator.lastRefreshDate)
        application.hasLoadedOllamaModels = true
        XCTAssertTrue(application.modelCoordinator.hasLoadedModels)
        XCTAssertNil(application.modelCoordinator.lastRefreshDate)
        application.hasLoadedOllamaModels = false
        XCTAssertFalse(application.modelCoordinator.hasLoadedModels)
        XCTAssertEqual(application.availableModels, ["manual-model"])
        XCTAssertEqual(application.selectedModel, selected)
    }

    @MainActor
    func testEmptyDiscoveryAndStatusHaveOneOwnerInBothCallDirections() {
        let application = isolatedApplication(backend: ControlledRunBackend())
        application.modelCoordinator.receiveModels([])
        XCTAssertTrue(application.hasLoadedOllamaModels)
        let first = OllamaState(installed: true, running: false, message: "Owner update")
        application.modelCoordinator.receiveOllamaState(first)
        XCTAssertEqual(application.ollamaState, first)
        let replacement = OllamaState(installed: true, running: true, message: "Application update")
        application.ollamaState = replacement
        XCTAssertEqual(application.modelCoordinator.ollamaState, replacement)
    }

    @MainActor
    func testOptionsUseCurrentSelectionAndStableDeduplicationAfterOwnerRefresh() {
        let application = isolatedApplication(backend: ControlledRunBackend())
        let suggested = application.ollamaRecommendation.model
        application.selectedModel = "chosen-model"
        application.modelCoordinator.receiveModels(["z", "", "z", suggested, "chosen-model", "a"])
        XCTAssertEqual(application.ollamaModelOptions, ["chosen-model", suggested, "z", "a"])
        application.selectedModel = "a"
        XCTAssertEqual(application.ollamaModelOptions, ["a", suggested, "z", "chosen-model"])
        XCTAssertEqual(application.selectedModel, "a")
    }
}
