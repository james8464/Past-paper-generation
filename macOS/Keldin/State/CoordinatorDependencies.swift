// Wrap the clock, workspace and credential store so tests can supply replacements

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
    func read(_ account: String) throws -> String
    func save(_ value: String, account: String) throws
}

struct KeychainSecretStore: SecretStoring {
    let keychain: any KeychainAccessing

    init(keychain: any KeychainAccessing = SystemKeychainAccess()) {
        self.keychain = keychain
    }

    func read(_ account: String) throws -> String {
        try SecretStore.read(account, keychain: keychain)
    }

    func save(_ value: String, account: String) throws {
        try SecretStore.save(value, account: account, keychain: keychain)
    }
}
