import AppKit
import Foundation

protocol AppClock {
    var now: Date { get }
}

struct SystemAppClock: AppClock {
    var now: Date { Date() }
}

protocol WorkspaceOpening {
    @MainActor
    func open(_ url: URL)

    @MainActor
    func reveal(_ url: URL)
}

struct SystemWorkspaceOpener: WorkspaceOpening {
    @MainActor
    func open(_ url: URL) {
        NSWorkspace.shared.open(url)
    }

    @MainActor
    func reveal(_ url: URL) {
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
}

protocol SecretStoring {
    func read(_ account: String) -> String
    func save(_ value: String, account: String)
}

struct KeychainSecretStore: SecretStoring {
    func read(_ account: String) -> String {
        SecretStore.read(account)
    }

    func save(_ value: String, account: String) {
        SecretStore.save(value, account: account)
    }
}
