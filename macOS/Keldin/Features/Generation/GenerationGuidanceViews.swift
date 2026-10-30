import SwiftUI

struct ModelQualityAdviceView: View {
    @Environment(\.locale) private var locale
    let provider: AIProvider
    let model: String

    var body: some View {
        let advice = ModelQualityAdvice.forModel(provider: provider, model: model)
        VStack(alignment: .leading, spacing: 4) {
            Label {
                Text(InterfaceText.localizedResource(advice.title, locale: locale))
            } icon: {
                Image(systemName: "exclamationmark.triangle").accessibilityHidden(true)
            }
            Text(InterfaceText.localizedResource(advice.detail, locale: locale))
                .font(.caption)
        }
        .foregroundStyle(.primary)
        .fixedSize(horizontal: false, vertical: true)
        .accessibilityElement(children: .combine)
    }
}

struct PaperQualitySummarySection: View {
    let report: GenerationQualityReport?
    var frenchReport: FrenchDraftQualityReport? = nil

    var body: some View {
        if let frenchReport { FrenchDraftQualitySummarySection(report: frenchReport) }
        else { standardSummary }
    }

    private var standardSummary: some View {
        let summary = GenerationIssueSummary(report: report)
        return Section("Last result checks") {
            Text("\(summary.issues.count) issues · \(summary.warnings.count) warnings · \(summary.notChecked.count) not checked")
                .font(.callout)
            DisclosureGroup("Show check details") {
                QualityCheckGroup(title: "Reported issues", notices: summary.issues,
                                  empty: "No failed checks are reported in this record.")
                ForEach(summary.failureDetails, id: \.self) { Text(verbatim: $0).font(.caption) }
                QualityCheckGroup(title: "Warnings", notices: summary.warnings,
                                  empty: "No warnings are recorded.")
                ForEach(summary.warningDetails, id: \.self) { Text(verbatim: $0).font(.caption) }
                QualityCheckGroup(title: "Not checked", notices: summary.notChecked,
                                  empty: "No additional unchecked areas are identified in this record.")
            }
        }
        .foregroundStyle(.primary)
    }
}

private struct FrenchDraftQualitySummarySection: View {
    @Environment(\.locale) private var locale
    let report: FrenchDraftQualityReport

    var body: some View {
        Section("Last result checks") {
            Text("Model review is not proof. Executable contract checks do not certify the printed answers.")
                .font(.callout)
            Text("Model-reviewed questions: \(report.modelReviewedQuestions) of \(report.questionCount)")
            Text("Executable contracts checked: \(report.executableContracts) of \(report.questionCount)")
            Text("Printed-answer correctness, difficulty and completion time are not certified.")
                .font(.caption)
            DisclosureGroup("Show check details") {
                findings("Reported issues", report.issues)
                findings("Warnings", report.warnings)
                findings("Not checked", report.notChecked)
            }
        }
        .foregroundStyle(.primary)
    }

    private func findings(_ title: LocalizedStringResource, _ entries: [FrenchDraftQualityReport.Finding]) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.headline)
            if entries.isEmpty { Text("No entries in this part of the record. This is not an all-clear.").font(.caption) }
            ForEach(entries) { entry in
                Text(InterfaceText.localizedResource(entry.locationResource, locale: locale)).font(.caption.weight(.semibold))
                if !entry.detail.isEmpty { Text(verbatim: entry.detail).font(.caption) }
            }
        }
    }
}

private struct QualityCheckGroup: View {
    @Environment(\.locale) private var locale
    let title: LocalizedStringResource
    let notices: [QualityCheckNotice]
    let empty: LocalizedStringResource

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(InterfaceText.localizedResource(title, locale: locale)).font(.headline)
            if notices.isEmpty {
                Text(InterfaceText.localizedResource(empty, locale: locale)).font(.caption)
            } else {
                ForEach(notices) { notice in
                    Text(InterfaceText.localizedResource(notice.message, locale: locale)).font(.caption)
                }
            }
        }
        .fixedSize(horizontal: false, vertical: true)
    }
}
