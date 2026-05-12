import Charts
import SwiftUI

struct BenchmarkWorkspace: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                HStack(spacing: 14) {
                    Image(systemName: "speedometer")
                        .font(.system(size: 26, weight: .semibold))
                        .symbolRenderingMode(.hierarchical)
                        .foregroundStyle(.tint)
                        .frame(width: 52, height: 52)
                        .background(.tint.opacity(0.12), in: RoundedRectangle(cornerRadius: 8, style: .continuous))

                    VStack(alignment: .leading, spacing: 5) {
                        Text("Benchmark")
                            .font(.title.weight(.semibold))
                        Text("Measure generation-critical performance for this Mac.")
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    if appModel.isBenchmarkRunning {
                        Button(role: .cancel, action: appModel.cancelBenchmark) {
                            Label("Cancel", systemImage: "xmark.circle")
                        }
                        .controlSize(.large)
                    } else {
                        Button(action: appModel.startBenchmark) {
                            Label("Run \(Int(AppDefaults.benchmarkDurationSeconds)) Second Test", systemImage: "play.fill")
                        }
                        .disabled(appModel.isRunning)
                        .controlSize(.large)
                        .nativePrimaryActionStyle()
                    }
                }
                .nativePanel()

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
    }
}

private struct BenchmarkOverviewPanel: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Diagnostic", systemImage: "gauge.with.dots.needle.67percent")

            if appModel.isBenchmarkRunning {
                ProgressView(value: appModel.benchmarkProgress ?? 0) {
                    Text("Running CPU, memory, storage, PDF, network, power and Ollama checks")
                } currentValueLabel: {
                    Text((appModel.benchmarkProgress ?? 0).formatted(.percent.precision(.fractionLength(0))))
                }
                .progressViewStyle(.linear)
            } else if let verdict = appModel.benchmarkVerdict {
                BenchmarkVerdictSummary(verdict: verdict)
            } else {
                Text("Run the benchmark to calibrate ETA and check whether this Mac is ready for local generation.")
                    .foregroundStyle(.secondary)
            }
        }
        .nativePanel()
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
    @EnvironmentObject private var appModel: AppViewModel

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
        BenchmarkChart(title: "CPU Load", unit: "%", samples: appModel.benchmarkSamples, value: \.cpuLoad)
    }

    private var cpuThroughputChart: some View {
        BenchmarkChart(title: "CPU Throughput", unit: "MB/s", samples: appModel.benchmarkSamples, value: \.cpuThroughputMBs)
    }

    private var memoryChart: some View {
        BenchmarkChart(title: "Free Memory", unit: "GB", samples: appModel.benchmarkSamples, value: \.memoryAvailableGB)
    }

    private var memoryPressureChart: some View {
        BenchmarkChart(title: "Memory Pressure", unit: "%", samples: appModel.benchmarkSamples, value: \.memoryPressurePercent)
    }

    private var diskWriteChart: some View {
        BenchmarkChart(title: "Disk Write", unit: "MB/s", samples: appModel.benchmarkSamples, value: \.diskWriteMBs)
    }

    private var networkLatencyChart: some View {
        BenchmarkChart(title: "Network Latency", unit: "ms", samples: appModel.benchmarkSamples, value: \.networkLatencyDisplayMS)
    }

    private var pdfRenderChart: some View {
        BenchmarkChart(title: "PDF Render", unit: "pages/s", samples: appModel.benchmarkSamples, value: \.pdfPagesPerSecond)
    }

    private var thermalChart: some View {
        BenchmarkChart(title: "Thermal Limit", unit: "%", samples: appModel.benchmarkSamples, value: \.thermalSpeedLimitDisplayPercent)
    }
}

private struct BenchmarkChart: View {
    let title: String
    let unit: String
    let samples: [BenchmarkSample]
    let value: KeyPath<BenchmarkSample, Double>

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.headline)
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
        .nativePanel()
    }
}

private struct BenchmarkMetricGrid: View {
    @EnvironmentObject private var appModel: AppViewModel

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            PanelHeader(title: "Results", systemImage: "list.bullet.rectangle")

            if appModel.benchmarkMetrics.isEmpty {
                PanelEmptyState(title: "No Results", message: "Metric results appear as the diagnostic runs.", systemImage: "speedometer")
                    .frame(maxWidth: .infinity, minHeight: 130)
            } else {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 230), spacing: 12)], spacing: 12) {
                    ForEach(appModel.benchmarkMetrics) { metric in
                        BenchmarkMetricTile(metric: metric)
                    }
                }
            }
        }
        .nativePanel()
    }
}

private struct BenchmarkMetricTile: View {
    let metric: BenchmarkMetric

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Text(metric.name)
                    .font(.headline)
                Spacer()
                if let score = metric.score {
                    Text(score.formatted(.percent.precision(.fractionLength(0))))
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(score >= 0.7 ? .green : .orange)
                }
            }
            Text(metric.displayValue)
                .font(.title3.monospacedDigit().weight(.semibold))
            if let detail = metric.detail, !detail.isEmpty {
                Text(detail)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(12)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}
