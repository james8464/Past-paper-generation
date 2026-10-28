// Store current credentials under Keldin and import accessible legacy entries on demand.

import Foundation
import Security

enum SecretStore {
    static func read(_ account: String) -> String {
        if let current = value(account, service: "Keldin") { return current }
        guard let legacy = value(account, service: KeldinMigration.legacyKeychainService) else { return "" }
        save(legacy, account: account)
        return legacy
    }

    static func save(_ value: String, account: String) {
        let query = baseQuery(account, service: "Keldin")
        let legacyQuery = baseQuery(account, service: KeldinMigration.legacyKeychainService)
        if value.isEmpty {
            SecItemDelete(query as CFDictionary)
            // Clearing a key must not restore it from the old service on the next read.
            SecItemDelete(legacyQuery as CFDictionary)
            return
        }
        let data = Data(value.utf8)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        ]
        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            _ = SecItemAdd(query.merging(attributes) { _, new in new } as CFDictionary, nil)
        }
        // Retain the original credential so a recoverable older installation still works.
        // Explicitly clearing a key above removes both copies to prevent resurrection.
    }

    private static func value(_ account: String, service: String) -> String? {
        var query = baseQuery(account, service: service)
        query[kSecMatchLimit as String] = kSecMatchLimitOne
        query[kSecReturnData as String] = true
        var result: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func baseQuery(_ account: String, service: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
    }
}
