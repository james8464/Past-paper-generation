import Combine
import Foundation

struct SettingsActionRequest: Identifiable, Equatable {
    enum Kind: Equatable {
        case hostedConsent(AIProvider)
        case error(String)
    }
    let id = UUID()
    let kind: Kind
}

@MainActor
final class SettingsActionPresentation: ObservableObject {
    private enum Phase {
        case inactive(SettingsActionRequest?)
        case idle
        case presented(SettingsActionRequest)
        case dismissing(SettingsActionRequest)
    }
    @Published private var phase = Phase.inactive(nil)
    private var deferredError: SettingsActionRequest?

    var request: SettingsActionRequest? {
        switch phase {
        case let .presented(request), let .dismissing(request): request
        case .idle, .inactive: nil
        }
    }
    var blocksCommands: Bool {
        if case .presented = phase { return true }
        return false
    }

    func activate() {
        guard case let .inactive(error) = phase else { return }
        phase = error.map(Phase.presented) ?? .idle
    }

    func deactivate() {
        let currentError = request.flatMap { request -> SettingsActionRequest? in
            if case .error = request.kind { return request }
            return nil
        }
        let retained: SettingsActionRequest?
        if case let .inactive(error) = phase { retained = error }
        else { retained = currentError ?? deferredError }
        deferredError = nil
        phase = .inactive(retained)
    }

    func requestConsent(for provider: AIProvider) {
        guard case .idle = phase else { return }
        phase = .presented(SettingsActionRequest(kind: .hostedConsent(provider)))
    }

    func reportError(_ message: String) {
        let error = SettingsActionRequest(kind: .error(message))
        switch phase {
        case let .inactive(retained): phase = .inactive(retained ?? error)
        case .idle: phase = .presented(error)
        case .presented, .dismissing:
            // Preserve the first waiting failure. All failures remain in the
            // coordinator's diagnostic entries rather than flooding alerts.
            if deferredError == nil { deferredError = error }
        }
    }

    func presentationDidDismiss(id: UUID) {
        guard let current = request, current.id == id else { return }
        phase = .dismissing(current)
    }

    func consume(id: UUID) -> SettingsActionRequest? {
        guard let current = request, current.id == id else { return nil }
        phase = deferredError.map(Phase.presented) ?? .idle
        deferredError = nil
        return current
    }

    func dismiss(id: UUID) { _ = consume(id: id) }
}
