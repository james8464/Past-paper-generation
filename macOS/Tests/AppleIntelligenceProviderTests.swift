import Foundation
import XCTest
@testable import Keldin

final class AppleIntelligenceProviderTests: XCTestCase {
    func testProviderIdentityDoesNotMigrateSavedMLXSettings() {
        XCTAssertEqual(AIProvider(backendID: "apple"), .apple)
        XCTAssertEqual(AIProvider(rawValue: "apple"), .apple)
        XCTAssertEqual(AIProvider(backendID: "apple_intelligence"), .appleIntelligence)
        XCTAssertEqual(AIProvider.appleIntelligence.backendID, "apple_intelligence")
        XCTAssertFalse(AIProvider.appleIntelligence.sendsPromptsOffDevice)
        XCTAssertEqual(AppleIntelligenceAvailability.model, "apple-system-on-device")
    }

    func testAvailabilityRequiresExactSystemIdentityAndMatchingRequest() throws {
        var reply: [String: Any] = ["protocol_version":1, "request_id":"owned", "provider":"apple_intelligence",
            "model":"apple-system-on-device", "status":"available", "os_version":"26.4",
            "available":true, "context_size":8192, "french_supported":true]
        func decode(_ value: [String: Any]) throws -> AppleIntelligenceAvailability {
            try AppleIntelligenceAvailability.decode(JSONSerialization.data(withJSONObject: value), requestID: "owned")
        }
        let status = try decode(reply)
        XCTAssertTrue(status.checked && status.available && status.frenchSupported)
        XCTAssertEqual(status.contextSize, 8192)
        for (key, value) in [("provider", "apple" as Any), ("model", "mlx-community/model"),
                             ("request_id", "other"), ("protocol_version", true), ("available", 1),
                             ("context_size", 0), ("status", "ok")] {
            var invalid = reply
            invalid[key] = value
            XCTAssertThrowsError(try decode(invalid), key)
        }
        reply["available"] = false
        reply["context_size"] = 0
        XCTAssertFalse(try decode(reply).available)
    }

    @MainActor
    func testSystemModelDoesNotNeedAKeyOrMLXSetupButNeedsAvailability() {
        let backend = ControlledRunBackend()
        let app = isolatedApplication(backend: backend)
        app.showWelcome = false
        app.aiProvider = .appleIntelligence
        app.dryRun = false
        XCTAssertEqual(app.activeModelName, "apple-system-on-device")
        XCTAssertNotNil(app.generationBlockerResource)
        app.appleIntelligenceAvailability = AppleIntelligenceAvailability(checked: true, available: true, contextSize: 8192, frenchSupported: true)
        XCTAssertNil(app.generationBlockerResource)
        XCTAssertFalse(app.showHostedAIConsent)
        XCTAssertFalse(app.showMLXSetupConfirmation)
        XCTAssertTrue(backend.requests.isEmpty)
        app.appleIntelligenceAvailability = AppleIntelligenceAvailability(checked: true, available: false, contextSize: 0, frenchSupported: false)
        XCTAssertNotNil(app.generationBlockerResource)
    }

    func testStoreAvailabilityCannotUseExternalHelperOverride() {
        let bundle = URL(fileURLWithPath: "/Applications/Keldin.app")
        XCTAssertEqual(AppleIntelligenceAvailability.helperURL(bundleURL: bundle, distributionMode: .appStore).path,
                       "/Applications/Keldin.app/Contents/Helpers/KeldinAppleIntelligence")
    }

    @MainActor
    func testFrenchFullPaperToolbarAndDirectActionRemainUnsupported() {
        let backend = ControlledRunBackend()
        let app = isolatedApplication(backend: backend)
        app.showWelcome = false
        app.aiProvider = .appleIntelligence
        app.appleIntelligenceAvailability = AppleIntelligenceAvailability(checked: true, available: true, contextSize: 8192, frenchSupported: true)
        let blocker = app.frenchGenerationBlockerResource.map { InterfaceText.resolve($0, language: "en") }
        XCTAssertTrue(blocker?.contains("Choose another provider") == true)
        XCTAssertFalse(KeldinCreationContext.french(largePrint: false).canCreate(boardCanGenerate: true,
            hasFrenchReferences: app.frenchGenerationBlockerResource == nil, isBusy: false))
        app.generateFrenchPaper(largePrint: false)
        XCTAssertTrue(backend.requests.isEmpty)
        XCTAssertFalse(app.isRunning)
    }

    @MainActor
    func testRestoredSystemProviderStartsAvailabilityCheckWithoutOpeningSettings() async {
        let defaults = isolatedDefaults()
        defaults.set(AIProvider.appleIntelligence.rawValue, forKey: AppStorageKey.aiProvider)
        defaults.set("retained-mlx-model", forKey: AppStorageKey.appleModel)
        let counter = AvailabilityCounter()
        let history = FileManager.default.temporaryDirectory.appendingPathComponent("AppleIntelligenceHistory-\(UUID().uuidString)")
        addTeardownBlock {
            if FileManager.default.fileExists(atPath: history.path) { try FileManager.default.removeItem(at: history) }
        }
        let app = ApplicationCoordinator(defaults: defaults, secrets: EmptyAppleSecrets(),
            historyDirectory: history, backend: ControlledRunBackend(), appleIntelligenceChecker: { _ in
                await counter.record()
                return AppleIntelligenceAvailability(checked: true, available: true, contextSize: 8192, frenchSupported: true)
            })
        XCTAssertTrue(app.isRefreshingAppleIntelligence)
        await app.refreshAppleIntelligenceAvailability()?.value
        let count = await counter.calls
        XCTAssertEqual(count, 1)
        XCTAssertTrue(app.appleIntelligenceAvailability.available)
        XCTAssertEqual(app.appleModel, "retained-mlx-model")
        XCTAssertEqual(app.activeModelName, "apple-system-on-device")
    }
}

private actor AvailabilityCounter {
    var calls = 0
    func record() { calls += 1 }
}

private final class EmptyAppleSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
