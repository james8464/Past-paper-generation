import Combine
import Foundation

struct ModelDownloadRequest: Equatable, Identifiable, Sendable {
    let id = UUID()
    let model: String
}

@MainActor
final class ModelDownloadPresentation: ObservableObject {
    private enum Phase {
        case idle
        case presented(ModelDownloadRequest)
        case dismissing(ModelDownloadRequest)
    }

    @Published private var phase = Phase.idle

    var request: ModelDownloadRequest? {
        switch phase {
        case .idle: nil
        case let .presented(request), let .dismissing(request): request
        }
    }

    var isPresented: Bool {
        if case .presented = phase { return true }
        return false
    }
    var blocksCommands: Bool { isPresented }

    func presentationDidDismiss(id: UUID) {
        guard let current = request, current.id == id else { return }
        // SwiftUI may dismiss before calling the selected button action.
        // Keep only that matching snapshot; invisible UI never blocks commands.
        phase = .dismissing(current)
    }

    func present(_ candidate: ModelDownloadRequest?) {
        guard !isPresented, let candidate else { return }
        phase = .presented(candidate)
    }

    func consume(id: UUID) -> ModelDownloadRequest? {
        guard let current = request, current.id == id else { return nil }
        phase = .idle
        return current
    }

    func dismiss(id: UUID) {
        _ = consume(id: id)
    }
}
