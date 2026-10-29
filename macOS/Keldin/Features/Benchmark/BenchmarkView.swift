// Show benchmark progress and the measurements reported by the backend.

import Charts
import SwiftUI

enum BenchmarkAccessibility {
    static func chartSummary(
        title: String,
        unit: String,
        values: [Double], locale: Locale = .current
    ) -> String {
        let displayUnit = NativeInterfaceCopy.benchmarkUnit(unit, locale: locale)
        guard let latest = values.last,
              let minimum = values.min(),
              let maximum = values.max() else {
            return String(
                format: String(localized: InterfaceText.localizedResource("%@. No samples.", locale: locale)),
                locale: locale,
                title
            )
        }
        let value: (Double) -> String = {
            $0.formatted(.number.precision(.fractionLength(0...1)).locale(locale))
        }
        return String(
            format: String(localized: InterfaceText.localizedResource("%@. %lld samples. Latest %@ %@. Range %@ to %@ %@.", locale: locale)),
            locale: locale,
            title,
            Int64(values.count),
            value(latest),
            displayUnit,
            value(minimum),
            value(maximum),
            displayUnit
        )
    }
}

struct BenchmarkWorkspace: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    @Environment(BenchmarkCoordinator.self) private var benchmark

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
                    Button(role: .cancel, action: application.cancelBenchmark) {
                        Label("Cancel", systemImage: "xmark.circle")
                    }
                } else {
                    Button(action: application.startBenchmark) {
                        Label(
                            "Run \(Int(AppDefaults.benchmarkDurationSeconds)) Second Test",
                            systemImage: "play.fill"
                        )
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(application.isRunning)
                }
            }
        }
    }
}

private struct BenchmarkOverviewPanel: View {
    @Environment(\.locale) private var locale
    @EnvironmentObject private var application: ApplicationCoordinator
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
            } else if let error = benchmark.errorMessage {
                VStack(alignment: .leading, spacing: 10) {
                    Label("The benchmark couldn't finish", systemImage: "exclamationmark.triangle")
                    Text("Try again, or copy diagnostics from Tools if the problem continues.")
                    Text(NativeInterfaceCopy.benchmarkText(error, locale: locale)).font(.caption).foregroundStyle(.secondary)
                    Button("Try Again", action: application.startBenchmark)
                        .disabled(application.isRunning)
                }
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
    @Environment(\.locale) private var locale
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
            Text(verdict.score.formatted(.percent.precision(.fractionLength(0)).locale(locale)))
                .font(.headline.monospacedDigit())
        }
        .gaugeStyle(.accessoryCircularCapacity)
        .tint(verdict.score >= 0.72 ? .green : .orange)
        .frame(width: 82, height: 82)
        .accessibilityLabel("Benchmark score")
    }

    private var verdictText: some View {
        VStack(alignment: .leading, spacing: 4) {
            Label {
                Text(NativeInterfaceCopy.benchmarkText(verdict.verdict, locale: locale)).foregroundStyle(.primary)
            } icon: {
                Image(systemName: verdict.score >= 0.72 ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                    .foregroundStyle(verdict.score >= 0.72 ? .green : .orange)
            }
                .font(.headline)
                .symbolRenderingMode(.hierarchical)
            Text(NativeInterfaceCopy.benchmarkText(verdict.detail, locale: locale))
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
    @Environment(\.locale) private var locale
    let title: LocalizedStringResource
    let unit: String
    let samples: [BenchmarkSample]
    let value: KeyPath<BenchmarkSample, Double>

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Spacer()
                    if let latest = samples.last {
                        Text(latest[keyPath: value].formatted(.number.precision(.fractionLength(0...1)).locale(locale)) + " \(NativeInterfaceCopy.benchmarkUnit(unit, locale: locale))")
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
                    .chartYAxisLabel(NativeInterfaceCopy.benchmarkUnit(unit, locale: locale))
                    .frame(height: 150)
                }
            }
        } label: {
            Label { Text(InterfaceText.localizedResource(title, locale: locale)) } icon: { Image(systemName: "chart.xyaxis.line") }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilitySummary)
        .accessibilityHint(
            "A time-series chart summarised by its latest, minimum and maximum values."
        )
    }

    private var accessibilitySummary: String {
        BenchmarkAccessibility.chartSummary(
            title: String(localized: InterfaceText.localizedResource(title, locale: locale)),
            unit: unit,
            values: samples.map { $0[keyPath: value] }, locale: locale
        )
    }
}

private struct BenchmarkMetricGrid: View {
    @Environment(\.locale) private var locale
    @Environment(BenchmarkCoordinator.self) private var benchmark

    var body: some View {
        GroupBox {
            if benchmark.metrics.isEmpty {
                PanelEmptyState(title: "No Results", message: "Metric results appear as the diagnostic runs.", systemImage: "speedometer")
                    .frame(maxWidth: .infinity, minHeight: 130)
            } else {
                Table(benchmark.metrics) {
                    TableColumn("Metric") { metric in
                        Text(NativeInterfaceCopy.benchmarkText(metric.name, locale: locale))
                    }
                    TableColumn("Value") { metric in
                        Text(metric.displayValue(locale: locale))
                            .monospacedDigit()
                    }
                    TableColumn("Score") { metric in
                        if let score = metric.score {
                            Text(score.formatted(.percent.precision(.fractionLength(0)).locale(locale)))
                                .monospacedDigit()
                        } else {
                            Text("Not available")
                                .foregroundStyle(.secondary)
                        }
                    }
                    TableColumn("Detail") { metric in
                        Text(NativeInterfaceCopy.benchmarkText(metric.detail ?? "", locale: locale))
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
