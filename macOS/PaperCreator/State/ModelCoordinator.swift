import Foundation
import Observation

@MainActor
@Observable
final class ModelCoordinator {
    var provider: AIProvider = .ollama
    var selectedModel = AppDefaults.ollamaModel
    private(set) var availableModels: [String] = []
    private(set) var lastRefreshDate: Date?
    private(set) var ollamaState = OllamaState()
    var isRefreshing = false

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

    var modelOptions: [String] {
        var seen: Set<String> = []
        return ([selectedModel, recommendation.model] + availableModels)
            .filter { !$0.isEmpty && seen.insert($0).inserted }
    }

    func receiveModels(_ models: [String], at date: Date? = nil) {
        availableModels = models
        lastRefreshDate = date ?? clock.now
    }

    func receiveOllamaState(_ state: OllamaState) {
        ollamaState = state
    }
}
