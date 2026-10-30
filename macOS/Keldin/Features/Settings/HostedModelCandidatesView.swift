import SwiftUI

struct HostedModelCandidatesView: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    let provider: AIProvider
    @Binding var model: String

    var body: some View {
        DisclosureGroup("Vendor model candidates") {
            Text("These are vendor model candidates, not paper-quality approvals from Keldin. Hosted generation requires your own API credits.")
                .font(.caption)
                .foregroundStyle(.secondary)
            ForEach(HostedModelCandidate.forProvider(provider)) { candidate in
                LabeledContent {
                    Button { model = candidate.model } label: { Text(verbatim: candidate.model) }
                        .disabled(application.isRunning)
                } label: { Text(candidate.role) }
            }
        }
    }
}
