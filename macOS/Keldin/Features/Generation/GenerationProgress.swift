// Keep real generation feedback and cancellation visible outside locked settings.

import SwiftUI

struct GenerationProgress: View {
    @Environment(\.locale) private var locale
    @EnvironmentObject private var application: ApplicationCoordinator

    var body: some View {
        HStack(alignment: .center, spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                if let progress = application.generationProgress {
                    ProgressView(value: progress) {
                        Text(application.status)
                    } currentValueLabel: {
                        Text(progress.formatted(.percent.precision(.fractionLength(0))))
                    }
                } else {
                    ProgressView(application.status)
                }
                if let estimate = application.generationEstimate {
                    Text(GenerationPresentation.estimatedTime(estimate, locale: locale))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityElement(children: .combine)
            .accessibilityLabel("Paper creation progress")
            .accessibilityValue(accessibilityValue)
            .accessibilityAddTraits(.updatesFrequently)

            Button("Cancel", role: .cancel, action: application.cancelGeneration)
        }
    }

    private var accessibilityValue: String {
        var parts = [application.status]
        if let progress = application.generationProgress {
            parts.append(progress.formatted(.percent.precision(.fractionLength(0))))
        }
        if let estimate = application.generationEstimate {
            parts.append(GenerationPresentation.estimatedTime(estimate, locale: locale))
        }
        return parts.joined(separator: ", ")
    }
}
