// Store current credentials under Keldin and import accessible legacy entries on demand.

import Foundation
import Security

enum SecretStoreOperation: Equatable { case read, write, clear }

enum SecretStoreError: Error, LocalizedError, Equatable {
    case status(operation: SecretStoreOperation, status: OSStatus)
    case invalidData
    case incompleteClear
    case unexpected(operation: SecretStoreOperation)

    func message(language: String) -> String {
        switch self {
        case .status(let operation, _), .unexpected(let operation):
            switch operation {
            case .read: InterfaceText.resolve("The API key couldn't be read from Keychain. Check Keychain access and try again.", language: language)
            case .write: InterfaceText.resolve("The API key couldn't be saved in Keychain. Check Keychain access and try again.", language: language)
            case .clear: InterfaceText.resolve("The API key couldn't be fully removed from Keychain. Retry to finish removing the saved entries.", language: language)
            }
        case .incompleteClear:
            InterfaceText.resolve("The API key couldn't be fully removed from Keychain. Retry to finish removing the saved entries.", language: language)
        case .invalidData:
            InterfaceText.resolve("The saved API key couldn't be read. Replace it in Settings.", language: language)
        }
    }

    var errorDescription: String? { message(language: "system") }
}

struct KeychainReadResult {
    let status: OSStatus
    let data: Data?
}

protocol KeychainAccessing {
    func copyMatching(_ query: [String: Any]) -> KeychainReadResult
    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus
    func add(_ attributes: [String: Any]) -> OSStatus
    func delete(_ query: [String: Any]) -> OSStatus
}

struct SystemKeychainAccess: KeychainAccessing {
    func copyMatching(_ query: [String: Any]) -> KeychainReadResult {
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        return KeychainReadResult(status: status, data: result as? Data)
    }

    func update(_ query: [String: Any], attributes: [String: Any]) -> OSStatus {
        SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
    }

    func add(_ attributes: [String: Any]) -> OSStatus {
        SecItemAdd(attributes as CFDictionary, nil)
    }

    func delete(_ query: [String: Any]) -> OSStatus {
        SecItemDelete(query as CFDictionary)
    }
}

enum SecretStore {
    static func read(_ account: String, keychain: any KeychainAccessing = SystemKeychainAccess()) throws -> String {
        // An empty current item records a clear that still needs cleanup. Never
        // treat it, an access denial, or malformed data as a missing credential.
        if let current = try value(account, service: "Keldin", keychain: keychain) {
            if current.isEmpty {
                // This marker follows an explicit clear, unlike an unreadable
                // key. Finish that request without consulting the legacy value.
                do { try save("", account: account, keychain: keychain) }
                catch { throw SecretStoreError.incompleteClear }
            }
            return current
        }
        guard let legacy = try value(account, service: KeldinMigration.legacyKeychainService, keychain: keychain) else { return "" }
        try writeCurrent(legacy, account: account, keychain: keychain)
        return legacy
    }

    static func save(_ value: String, account: String, keychain: any KeychainAccessing = SystemKeychainAccess()) throws {
        if value.isEmpty {
            // A partial deletion must not make the preserved legacy key reappear.
            // Keep this empty marker until both removal operations have succeeded.
            try writeCurrent("", account: account, keychain: keychain)
            for service in [KeldinMigration.legacyKeychainService, "Keldin"] {
                let status = keychain.delete(baseQuery(account, service: service))
                guard status == errSecSuccess || status == errSecItemNotFound else {
                    throw SecretStoreError.status(operation: .clear, status: status)
                }
            }
            return
        }
        try writeCurrent(value, account: account, keychain: keychain)
        // Retain the original credential so a recoverable older installation still works.
        // Only an explicit clear above removes both copies.
    }

    private static func writeCurrent(_ value: String, account: String, keychain: any KeychainAccessing) throws {
        let query = baseQuery(account, service: "Keldin")
        let data = Data(value.utf8)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        ]
        var status = keychain.update(query, attributes: attributes)
        if status == errSecItemNotFound {
            status = keychain.add(query.merging(attributes) { _, new in new })
            if status == errSecDuplicateItem {
                // Another writer created the item after the initial lookup.
                status = keychain.update(query, attributes: attributes)
            }
        }
        guard status == errSecSuccess else {
            throw SecretStoreError.status(operation: .write, status: status)
        }
    }

    private static func value(_ account: String, service: String, keychain: any KeychainAccessing) throws -> String? {
        var query = baseQuery(account, service: service)
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        query[kSecReturnData as String] = true
        let result = keychain.copyMatching(query)
        if result.status == errSecItemNotFound { return nil }
        guard result.status == errSecSuccess else {
            throw SecretStoreError.status(operation: .read, status: result.status)
        }
        guard let data = result.data, let value = String(data: data, encoding: .utf8) else {
            throw SecretStoreError.invalidData
        }
        return value
    }

    private static func baseQuery(_ account: String, service: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
    }
}
