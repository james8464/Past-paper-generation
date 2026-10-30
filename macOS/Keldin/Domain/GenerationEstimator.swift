// Estimate generation effort from the selected paper and runtime measurements.

import Foundation

private enum EstimateTuning {
    static let baselineSeconds = 210.0
    static let minimumSeconds = 20.0
    static let noBenchmarkConfidence = 0.58
    static let benchmarkConfidence = 0.76
    static let observedProgressThreshold = 0.08
    static let minimumProgress = 0.02
    static let maximumProgress = 0.995
    static let priorWeight = 0.35
    static let observedWeight = 0.65
    static let maximumConfidence = 0.92
    static let progressConfidenceBase = 0.65
    static let progressConfidenceRange = 0.25
    static let referenceModelBillions = 14.0
}

enum GenerationEstimator {
    static func initialEstimate(
        board: ExamBoardOption,
        paper: PaperOption,
        provider: AIProvider,
        model: String,
        dryRun: Bool,
        benchmark: BenchmarkVerdict?,
        recentRuns: [GenerationJobRecord] = [],
        localGenerationWorkers: Int = 1
    ) -> GenerationEstimate {
        let benchmark = benchmark.flatMap { verdict in
            verdict.validatedScore != nil ? verdict : nil
        }
        let paperFactor = paperComplexity(board: board, paper: paper)
        let providerFactor: (value: Double, factor: EstimateFactor)
        let modelFactor: (value: Double, factor: EstimateFactor)
        if !board.usesAI {
            providerFactor = (
                0.18,
                EstimateFactor(
                    title: "Generation mode",
                    detail: "Built-in constrained generation does not call an AI model.",
                    impact: 0.18
                )
            )
            modelFactor = (
                1.0,
                EstimateFactor(
                    title: "Model",
                    detail: "No model is used for this paper family.",
                    impact: 1.0
                )
            )
        } else if dryRun {
            providerFactor = (
                0.18,
                EstimateFactor(
                    title: "Generation mode",
                    detail: "Built-in draft mode avoids model calls.",
                    impact: 0.18
                )
            )
            modelFactor = (
                1.0,
                EstimateFactor(
                    title: "Model",
                    detail: "No model is used in preview mode.",
                    impact: 1.0
                )
            )
        } else {
            providerFactor = providerComplexity(provider)
            modelFactor = modelComplexity(model)
        }
        let deviceFactor = deviceComplexity()
        let benchmarkFactor = benchmark.map { benchmarkComplexity(score: $0.score) } ?? 1.0

        let total = EstimateTuning.baselineSeconds * paperFactor.value * providerFactor.value * modelFactor.value * deviceFactor.value * benchmarkFactor
        var factors = [
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

        let durations = recentRuns
            .filter {
                $0.state == .completed && $0.configuration.boardID == board.id
                    && $0.configuration.paperID == paper.id
                    && $0.configuration.provider == provider.backendID
                    && $0.configuration.model == model && $0.configuration.dryRun == dryRun
                    && $0.provenance.effectiveLocalGenerationWorkers == localGenerationWorkers
            }
            .sorted { $0.createdAt > $1.createdAt }
            .compactMap { run -> TimeInterval? in
                let duration = run.updatedAt.timeIntervalSince(run.createdAt)
                return duration.isFinite && (1...86_400).contains(duration) ? duration : nil
            }
            .prefix(5).sorted()
        let duration: TimeInterval
        if durations.isEmpty {
            duration = total
        } else {
            let middle = durations.count / 2
            duration = durations.count.isMultiple(of: 2)
                ? (durations[middle - 1] + durations[middle]) / 2 : durations[middle]
            factors.append(EstimateFactor(title: "Runtime history",
                detail: "Median of \(durations.count) matching completed runs.", impact: duration / max(total, 1)))
        }
        return GenerationEstimate(
            startedAt: Date(),
            totalSeconds: max(EstimateTuning.minimumSeconds, duration),
            remainingSeconds: max(EstimateTuning.minimumSeconds, duration),
            confidence: benchmark == nil ? EstimateTuning.noBenchmarkConfidence : EstimateTuning.benchmarkConfidence,
            factors: factors
        )
    }

    static func initialFrenchEstimate(
        configuration: GenerationConfiguration,
        recentRuns: [GenerationJobRecord],
        now: Date = Date()
    ) -> GenerationEstimate {
        // French exercise authoring, solving and review run sequentially. UK
        // parallel preferences and historical fixed catalogues are not timings
        // for this workflow. These are software runtimes, not learner timings.
        let durations = recentRuns.filter { run in
            let saved = run.configuration
            return configuration.assessmentID == FrenchAssessmentRequest.assessmentID
                && configuration.authoringVersion == "v36"
                && run.state == .completed && !saved.dryRun
                && saved.boardID == configuration.boardID
                && saved.paperID == configuration.paperID
                && saved.assessmentID == configuration.assessmentID
                && saved.authoringVersion == configuration.authoringVersion
                && saved.educationSystem == "fr-national" && saved.documentLanguage == "fr-FR"
                && saved.provider == configuration.provider && saved.model == configuration.model
                && run.provenance.provider == configuration.provider && run.provenance.model == configuration.model
                && run.provenance.effectiveLocalGenerationWorkers == 1
                && run.updatedAt <= now
        }
        .sorted { $0.createdAt > $1.createdAt }
        .compactMap { run -> TimeInterval? in
            let duration = run.updatedAt.timeIntervalSince(run.createdAt)
            return duration.isFinite && (1...86_400).contains(duration) ? duration : nil
        }
        .prefix(5).sorted()
        let duration: TimeInterval
        if durations.isEmpty {
            duration = 0
        } else {
            let middle = durations.count / 2
            duration = durations.count.isMultiple(of: 2)
                ? (durations[middle - 1] + durations[middle]) / 2 : durations[middle]
        }
        return GenerationEstimate(startedAt: now, totalSeconds: duration,
            remainingSeconds: duration,
            confidence: durations.isEmpty ? 0 : EstimateTuning.noBenchmarkConfidence,
            factors: [], elapsedSeconds: 0, hasDurationEstimate: !durations.isEmpty)
    }

    static func update(
        estimate: GenerationEstimate,
        progress: Double?,
        now: Date = Date()
    ) -> GenerationEstimate {
        let previousUpdate = estimate.lastUpdatedAt ?? estimate.startedAt
        guard now >= previousUpdate else { return estimate }
        let validProgress = progress.flatMap { $0.isFinite ? $0 : nil } ?? 0
        let currentProgress = max(estimate.lastObservedProgress ?? 0,
            min(max(validProgress, EstimateTuning.minimumProgress), EstimateTuning.maximumProgress))
        let changed = estimate.lastObservedProgress != currentProgress
        guard now != previousUpdate || changed else { return estimate }
        let elapsed = max(0, now.timeIntervalSince(estimate.startedAt))
        let interval = now.timeIntervalSince(previousUpdate)
        var updated = estimate
        if estimate.elapsedSeconds != nil { updated.elapsedSeconds = elapsed }
        if !estimate.hasDurationEstimate {
            updated.lastUpdatedAt = now
            updated.lastObservedProgress = currentProgress
            return updated
        }
        var targetRemaining = max(0, estimate.totalSeconds - elapsed)
        if currentProgress > EstimateTuning.observedProgressThreshold {
            let observedTotal = elapsed / currentProgress
            let blendedTotal = (estimate.totalSeconds * EstimateTuning.priorWeight) + (observedTotal * EstimateTuning.observedWeight)
            targetRemaining = max(0, blendedTotal - elapsed)
            if changed { updated.confidence = min(
                EstimateTuning.maximumConfidence,
                max(
                    estimate.confidence,
                    EstimateTuning.progressConfidenceBase + currentProgress * EstimateTuning.progressConfidenceRange
                )
            ) }
        }
        if estimate.remainingSeconds <= 0 && changed {
            // A fresh work observation can restore an expired estimate.
            updated.remainingSeconds = targetRemaining
        } else {
            let countdown = max(0, estimate.remainingSeconds - interval)
            let weight = 1 - exp(-interval / 15)
            let correction = (targetRemaining - countdown) * weight
            // Limit corrections to two seconds per elapsed second, rather
            // than snapping to a new ETA after a slow question completes.
            updated.remainingSeconds = max(0, countdown + min(2 * interval, max(-2 * interval, correction)))
        }
        updated.totalSeconds = elapsed + updated.remainingSeconds
        updated.lastUpdatedAt = now
        updated.lastObservedProgress = currentProgress
        return updated
    }

    private static func paperComplexity(board: ExamBoardOption, paper: PaperOption) -> (value: Double, factor: EstimateFactor) {
        let value: Double
        let detail: String
        if board.backendSubject?.hasPrefix("economics") == true {
            switch paper.id {
            case "3":
                value = 0.95
                detail = "Paper 3 has fewer large sections but longer integrated writing."
            default:
                value = 1.12
                detail = ["economics_aqa", "economics_ocr"].contains(board.backendSubject ?? "")
                    ? "Economics \(paper.title) creates a question paper and mark scheme."
                    : "Economics \(paper.title) creates question paper, source booklet, and mark scheme."
            }
        } else if ["computer_science", "computer_science_ocr"].contains(board.backendSubject ?? "") {
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
        case .apple:
            return (1.0, EstimateFactor(title: "AI provider", detail: "Local MLX speed depends on this Mac.", impact: 1.0))
        case .appleIntelligence:
            return (1.0, EstimateFactor(title: "AI provider", detail: "Apple Intelligence generation timing has not been measured.", impact: 1.0))
        case .openAI:
            return (0.72, EstimateFactor(title: "AI provider", detail: "Hosted OpenAI generation usually reduces local compute time.", impact: 0.72))
        case .anthropic:
            return (0.78, EstimateFactor(title: "AI provider", detail: "Hosted Anthropic generation usually reduces local compute time.", impact: 0.78))
        case .deepSeek:
            return (1.0, EstimateFactor(title: "AI provider", detail: "DeepSeek generation timing has not been measured.", impact: 1.0))
        }
    }

    private static func modelComplexity(_ model: String) -> (value: Double, factor: EstimateFactor) {
        let lowered = model.lowercased()
        let billions = modelBillions(lowered)
        let value: Double
        if lowered.contains("gpt") || lowered.contains("claude") {
            value = 0.9
        } else if let billions {
            value = min(2.7, max(0.58, sqrt(billions / EstimateTuning.referenceModelBillions)))
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
        guard let size = Double(model[range]), size.isFinite, size < Double(Int.max) else { return nil }
        return size
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
