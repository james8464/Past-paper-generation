import Charts
import SwiftUI

struct BenchmarkWorkspace: View {
    @Environment(BenchmarkCoordinator.self) private var benchmark
    @Environment(GenerationCoordinator.self) private var generation

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                BenchmarkOverviewPanel()
                BenchmarkLiveCharts()
                BenchmarkMetricGrid()
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 24)
            .frame(maxWidth: 1160)
            .frame(maxWidth: .infinity)
        }
        .background(.background)
        .navigationTitle("Benchmark")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                if benchmark.isRunning {
                    Button(role: .cancel, action: benchmark.cancel) {
                        Label("Cancel", systemImage: "xmark.circle")
                    }
                } else {
                    Button {
                        benchmark.start(generationIsRunning: generation.activeJob != nil)
                    } label: {
                        Label(
                            "Run \(Int(AppDefaults.benchmarkDurationSeconds)) Second Test",
                            systemImage: "play.fill"
                        )
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(generation.activeJob != nil)
                }
            }
        }
    }
}

private struct BenchmarkOverviewPanel: View {
    @Environment(BenchmarkCoordinator.self) private var benchmark

    var body: some View {
        GroupBox {
            if benchmark.isRunning {
                ProgressView(value: benchmark.progress ?? 0) {
                    Text("Running CPU, memory, storage, PDF, network, power and Ollama checks")
                } currentValueLabel: {
                    Text((benchmark.progress ?? 0).formatted(.percent.precision(.fractionLength(0))))
                }
                .accessibilityLabel("Benchmark progress")
                .accessibilityValue(
                    (benchmark.progress ?? 0).formatted(
                        .percent.precision(.fractionLength(0))
                    )
                )
                .accessibilityAddTraits(.updatesFrequently)
                .progressViewStyle(.linear)
            } else if let verdict = benchmark.verdict {
                BenchmarkVerdictSummary(verdict: verdict)
            } else {
                Text("Run the benchmark to calibrate ETA and check whether this Mac is ready for local generation.")
                    .foregroundStyle(.secondary)
            }
        } label: {
            Label("Diagnostic", systemImage: "gauge.with.dots.needle.67percent")
        }
    }
}

private struct BenchmarkVerdictSummary: View {
    let verdict: BenchmarkVerdict

    var body: some View {
        ViewThatFits(in: .horizontal) {
            HStack(alignment: .center, spacing: 16) {
                scoreGauge
                verdictText
                Spacer()
            }

            VStack(alignment: .leading, spacing: 12) {
                scoreGauge
                verdictText
            }
        }
    }

    private var scoreGauge: some View {
        Gauge(value: verdict.score, in: 0...1) {
            Text("Score")
        } currentValueLabel: {
            Text(verdict.score.formatted(.percent.precision(.fractionLength(0))))
                .font(.headline.monospacedDigit())
        }
        .gaugeStyle(.accessoryCircularCapacity)
        .tint(verdict.score >= 0.72 ? .green : .orange)
        .frame(width: 82, height: 82)
        .accessibilityLabel("Benchmark score")
    }

    private var verdictText: some View {
        VStack(alignment: .leading, spacing: 4) {
            Label(verdict.verdict, systemImage: verdict.score >= 0.72 ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                .font(.headline)
                .symbolRenderingMode(.hierarchical)
                .foregroundStyle(verdict.score >= 0.72 ? .green : .orange)
            Text(verdict.detail)
                .foregroundStyle(.secondary)
        }
    }
}

private struct BenchmarkLiveCharts: View {
    @Environment(BenchmarkCoordinator.self) private var benchmark

    var body: some View {
        ViewThatFits(in: .horizontal) {
                Grid(alignment: .topLeading, horizontalSpacing: 18, verticalSpacing: 18) {
                    GridRow {
                        cpuChart
                        cpuThroughputChart
                    }
                    GridRow {
                        memoryChart
                        memoryPressureChart
                    }
                    GridRow {
                        diskWriteChart
                        networkLatencyChart
                    }
                    GridRow {
                        pdfRenderChart
                        thermalChart
                    }
                }

            VStack(spacing: 18) {
                cpuChart
                cpuThroughputChart
                memoryChart
                memoryPressureChart
                diskWriteChart
                networkLatencyChart
                pdfRenderChart
                thermalChart
            }
        }
    }

    private var cpuChart: some View {
        BenchmarkChart(title: "CPU Load", unit: "%", samples: benchmark.samples, value: \.cpuLoad)
    }

    private var cpuThroughputChart: some View {
        BenchmarkChart(title: "CPU Throughput", unit: "MB/s", samples: benchmark.samples, value: \.cpuThroughputMBs)
    }

    private var memoryChart: some View {
        BenchmarkChart(title: "Free Memory", unit: "GB", samples: benchmark.samples, value: \.memoryAvailableGB)
    }

    private var memoryPressureChart: some View {
        BenchmarkChart(title: "Memory Pressure", unit: "%", samples: benchmark.samples, value: \.memoryPressurePercent)
    }

    private var diskWriteChart: some View {
        BenchmarkChart(title: "Disk Write", unit: "MB/s", samples: benchmark.samples, value: \.diskWriteMBs)
    }

    private var networkLatencyChart: some View {
        BenchmarkChart(title: "Network Latency", unit: "ms", samples: benchmark.samples, value: \.networkLatencyDisplayMS)
    }

    private var pdfRenderChart: some View {
        BenchmarkChart(title: "PDF Render", unit: "pages/s", samples: benchmark.samples, value: \.pdfPagesPerSecond)
    }

    private var thermalChart: some View {
        BenchmarkChart(title: "Thermal Limit", unit: "%", samples: benchmark.samples, value: \.thermalSpeedLimitDisplayPercent)
    }
}

private struct BenchmarkChart: View {
    let title: String
    let unit: String
    let samples: [BenchmarkSample]
    let value: KeyPath<BenchmarkSample, Double>

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Spacer()
                    if let latest = samples.last {
                        Text(latest[keyPath: value].formatted(.number.precision(.fractionLength(0...1))) + " \(unit)")
                            .foregroundStyle(.secondary)
                            .monospacedDigit()
                    }
                }

                if samples.isEmpty {
                    PanelEmptyState(title: "No Samples", message: "Start the benchmark to populate this chart.", systemImage: "chart.xyaxis.line")
                        .frame(height: 150)
                } else {
                    Chart(samples) { sample in
                        LineMark(
                            x: .value("Seconds", sample.elapsed),
                            y: .value(unit, sample[keyPath: value])
                        )
                        .interpolationMethod(.catmullRom)
                        .foregroundStyle(.tint)
                        AreaMark(
                            x: .value("Seconds", sample.elapsed),
                            y: .value(unit, sample[keyPath: value])
                        )
                        .interpolationMethod(.catmullRom)
                        .foregroundStyle(.tint.opacity(0.12))
                    }
                    .chartXAxisLabel("seconds")
                    .chartYAxisLabel(unit)
                    .frame(height: 150)
                }
            }
        } label: {
            Label(title, systemImage: "chart.xyaxis.line")
        }
    }
}

private struct BenchmarkMetricGrid: View {
    @Environment(BenchmarkCoordinator.self) private var benchmark

    var body: some View {
        GroupBox {
            if benchmark.metrics.isEmpty {
                PanelEmptyState(title: "No Results", message: "Metric results appear as the diagnostic runs.", systemImage: "speedometer")
                    .frame(maxWidth: .infinity, minHeight: 130)
            } else {
                Table(benchmark.metrics) {
                    TableColumn("Metric") { metric in
                        Text(metric.name)
                    }
                    TableColumn("Value") { metric in
                        Text(metric.displayValue)
                            .monospacedDigit()
                    }
                    TableColumn("Score") { metric in
                        if let score = metric.score {
                            Text(score.formatted(.percent.precision(.fractionLength(0))))
                                .monospacedDigit()
                        } else {
                            Text("—")
                                .foregroundStyle(.secondary)
                        }
                    }
                    TableColumn("Detail") { metric in
                        Text(metric.detail ?? "")
                            .foregroundStyle(.secondary)
                    }
                }
                .frame(minHeight: 230)
            }
        } label: {
            Label("Results", systemImage: "list.bullet.rectangle")
        }
    }
}
