// Track model discovery, downloads and local runtime setup.

import Foundation
import Observation

@MainActor
@Observable
final class ModelCoordinator {
    var provider: AIProvider = .ollama
    private(set) var availableModels: [String] = []
    private(set) var hasLoadedModels = false
    private(set) var lastRefreshDate: Date?
    private(set) var ollamaState = OllamaState()

    // Legacy EnvironmentObject views need the same pre-mutation invalidation
    // as views reading this observable owner directly.
    @ObservationIgnored var onDiscoveryChange: (@MainActor () -> Void)?

    @ObservationIgnored private let clock: AppClock
    @ObservationIgnored private let staleAfter: TimeInterval

    init(
        clock: AppClock = SystemAppClock(),
        staleAfter: TimeInterval = 5 * 60
    ) {
        self.clock = clock
        self.staleAfter = staleAfter
    }

    var isModelListStale: Bool {
        guard let lastRefreshDate else { return true }
        return clock.now.timeIntervalSince(lastRefreshDate) > staleAfter
    }

    var recommendation: OllamaModelRecommendation {
        OllamaModelGuide.currentRecommendation
    }

    func modelOptions(selectedModel: String) -> [String] {
        var seen: Set<String> = []
        return ([selectedModel, recommendation.model] + availableModels)
            .filter { !$0.isEmpty && seen.insert($0).inserted }
    }

    func receiveModels(_ models: [String], at date: Date? = nil) {
        onDiscoveryChange?()
        availableModels = models
        lastRefreshDate = date ?? clock.now
        hasLoadedModels = true
    }

    func setAvailableModels(_ models: [String]) {
        onDiscoveryChange?()
        availableModels = models
    }

    func setHasLoadedModels(_ loaded: Bool) {
        onDiscoveryChange?()
        hasLoadedModels = loaded
    }

    func receiveOllamaState(_ state: OllamaState) {
        onDiscoveryChange?()
        ollamaState = state
    }
}
