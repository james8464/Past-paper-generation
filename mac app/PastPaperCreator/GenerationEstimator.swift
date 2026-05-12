import Foundation

enum GenerationEstimator {
    static func initialEstimate(
        board: ExamBoardOption,
        paper: PaperOption,
        provider: AIProvider,
        model: String,
        dryRun: Bool,
        benchmark: BenchmarkVerdict?
    ) -> GenerationEstimate {
        let paperFactor = paperComplexity(board: board, paper: paper)
        let providerFactor = dryRun
            ? (value: 0.18, factor: EstimateFactor(title: "AI provider", detail: "Built-in draft mode avoids model calls.", impact: 0.18))
            : providerComplexity(provider)
        let modelFactor = modelComplexity(model)
        let deviceFactor = deviceComplexity()
        let benchmarkFactor = benchmark.map { benchmarkComplexity(score: $0.score) } ?? 1.0

        let total = 210 * paperFactor.value * providerFactor.value * modelFactor.value * deviceFactor.value * benchmarkFactor
        let factors = [
            paperFactor.factor,
            providerFactor.factor,
            modelFactor.factor,
            deviceFactor.factor,
            EstimateFactor(
                title: "Benchmark",
                detail: benchmark == nil ? "No recent benchmark; using device defaults." : "Last benchmark score \(Int((benchmark?.score ?? 0) * 100))%.",
                impact: benchmarkFactor
            ),
        ]

        return GenerationEstimate(
            startedAt: Date(),
            totalSeconds: max(20, total),
            remainingSeconds: max(20, total),
            confidence: benchmark == nil ? 0.58 : 0.76,
            factors: factors
        )
    }

    static func update(
        estimate: GenerationEstimate,
        progress: Double?,
        now: Date = Date()
    ) -> GenerationEstimate {
        var updated = estimate
        let elapsed = now.timeIntervalSince(estimate.startedAt)
        let currentProgress = min(max(progress ?? 0, 0.02), 0.995)
        let scheduleRemaining = max(0, estimate.totalSeconds - elapsed)

        if currentProgress > 0.08 {
            let observedTotal = elapsed / currentProgress
            let blendedTotal = (estimate.totalSeconds * 0.35) + (observedTotal * 0.65)
            updated.totalSeconds = max(elapsed, blendedTotal)
            updated.remainingSeconds = max(0, updated.totalSeconds - elapsed)
            updated.confidence = min(0.92, max(estimate.confidence, 0.65 + currentProgress * 0.25))
        } else {
            updated.remainingSeconds = scheduleRemaining
        }
        return updated
    }

    private static func paperComplexity(board: ExamBoardOption, paper: PaperOption) -> (value: Double, factor: EstimateFactor) {
        let value: Double
        let detail: String
        if board.backendSubject == "economics" {
            switch paper.id {
            case "3":
                value = 0.95
                detail = "Paper 3 has fewer large sections but longer integrated writing."
            default:
                value = 1.12
                detail = "Economics \(paper.title) creates question paper, source booklet, and mark scheme."
            }
        } else if board.backendSubject == "computer_science" {
            value = 1.02
            detail = "Computer Science Paper 2 is self-contained but has more technical subparts."
        } else {
            value = 1.0
            detail = "Default paper profile."
        }
        return (value, EstimateFactor(title: "Paper length", detail: detail, impact: value))
    }

    private static func providerComplexity(_ provider: AIProvider) -> (value: Double, factor: EstimateFactor) {
        switch provider {
        case .ollama:
            return (1.0, EstimateFactor(title: "AI provider", detail: "Local Ollama speed depends on this Mac.", impact: 1.0))
        case .openAI:
            return (0.72, EstimateFactor(title: "AI provider", detail: "Hosted OpenAI generation usually reduces local compute time.", impact: 0.72))
        case .anthropic:
            return (0.78, EstimateFactor(title: "AI provider", detail: "Hosted Anthropic generation usually reduces local compute time.", impact: 0.78))
        }
    }

    private static func modelComplexity(_ model: String) -> (value: Double, factor: EstimateFactor) {
        let lowered = model.lowercased()
        let billions = modelBillions(lowered)
        let value: Double
        if lowered.contains("gpt") || lowered.contains("claude") {
            value = 0.9
        } else if let billions {
            value = min(2.7, max(0.58, sqrt(billions / 14.0)))
        } else {
            value = 1.0
        }

        let detail: String
        if let billions {
            detail = "\(Int(billions))B-class local model."
        } else {
            detail = "Unknown model size; using neutral estimate."
        }
        return (value, EstimateFactor(title: "Model", detail: detail, impact: value))
    }

    private static func deviceComplexity() -> (value: Double, factor: EstimateFactor) {
        let processInfo = ProcessInfo.processInfo
        let cores = max(1, processInfo.activeProcessorCount)
        let memoryGB = Double(processInfo.physicalMemory) / 1_073_741_824
        var value = 1.0

        if cores < 8 { value *= 1.18 }
        if cores >= 12 { value *= 0.88 }
        if memoryGB < 12 { value *= 1.18 }
        if memoryGB >= 24 { value *= 0.92 }

        switch processInfo.thermalState {
        case .serious:
            value *= 1.2
        case .critical:
            value *= 1.45
        default:
            break
        }

        let detail = "\(cores) active CPU cores, \(Int(memoryGB.rounded())) GB memory, thermal state \(thermalTitle(processInfo.thermalState))."
        return (value, EstimateFactor(title: "Mac performance", detail: detail, impact: value))
    }

    private static func benchmarkComplexity(score: Double) -> Double {
        let clamped = min(max(score, 0.2), 1.0)
        return 1.25 - (clamped * 0.45)
    }

    private static func modelBillions(_ model: String) -> Double? {
        let pattern = #"(\d+(?:\.\d+)?)\s*b"#
        guard let regex = try? NSRegularExpression(pattern: pattern),
              let match = regex.firstMatch(in: model, range: NSRange(model.startIndex..., in: model)),
              let range = Range(match.range(at: 1), in: model) else {
            return nil
        }
        return Double(model[range])
    }

    private static func thermalTitle(_ state: ProcessInfo.ThermalState) -> String {
        switch state {
        case .nominal: "nominal"
        case .fair: "fair"
        case .serious: "serious"
        case .critical: "critical"
        @unknown default: "unknown"
        }
    }
}
