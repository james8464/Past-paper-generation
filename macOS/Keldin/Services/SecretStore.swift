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
        var status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            status = SecItemAdd(query.merging(attributes) { _, new in new } as CFDictionary, nil)
        }
        // A denied write leaves the legacy credential available for another attempt.
        if status == errSecSuccess { SecItemDelete(legacyQuery as CFDictionary) }
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
