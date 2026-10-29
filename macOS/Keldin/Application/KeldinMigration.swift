// Import earlier installations once, without deleting their files or overwriting Keldin data.

import CryptoKit
import Foundation

enum KeldinMigration {
    // Legacy spellings belong here so new storage and launch paths use Keldin throughout.
    static let legacyBundleID = "com.jamesdurup.PaperCreator"
    static let legacyAppFolders = ["Paper creator", "Paper Creator"]
    static let legacyKeychainService = "Paper creator"
    static let completionKey = "keldinIdentityMigrationVersion"
    static let artifactMappingsKey = "keldinImportedArtifactRoots"
    static let frenchFamilyImportFailedKey = "keldinFrenchFamilyImportFailed"
    private static let verifiedArtifactCopiesKey = "keldinVerifiedImportedArtifactCopies"
    private static let migrationVersion = 2

    static func needsImport(defaults: UserDefaults) -> Bool {
        defaults.integer(forKey: completionKey) < migrationVersion
    }

    static func environmentValue(_ name: String, environment: [String: String]) -> String? {
        environment[name] ?? environment[name.replacingOccurrences(of: "KELDIN_", with: "PAPER_CREATOR_")]
    }

    static func prepare(
        defaults: UserDefaults = .standard, fileManager: FileManager = .default,
        distributionMode: DistributionMode = .current,
        legacyDomainReader: (UserDefaults, String) -> [String: Any]? = { $0.persistentDomain(forName: $1) }
    ) -> [String] {
        guard needsImport(defaults: defaults) else { return [] }
        if distributionMode == .direct {
            importPreferences(legacyDomainReader(defaults, legacyBundleID) ?? [:], into: defaults)
        }
        let localHome = fileManager.homeDirectoryForCurrentUser
        let accountHome = fileManager.homeDirectory(forUser: NSUserName()) ?? localHome
        let support = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? localHome.appendingPathComponent("Library/Application Support", isDirectory: true)
        let destination = support.appendingPathComponent("Keldin", isDirectory: true)
        let supportRoots = [
            support,
            accountHome.appendingPathComponent("Library/Application Support", isDirectory: true),
            accountHome.appendingPathComponent("Library/Containers/\(legacyBundleID)/Data/Library/Application Support", isDirectory: true),
        ]
        var failures: [String] = []
        if defaults.bool(forKey: frenchFamilyImportFailedKey) {
            failures.append("Previous French practice history could not be imported. French generation remains blocked until the saved history is repaired.")
        }
        for root in supportRoots {
            for name in legacyAppFolders {
                let source = root.appendingPathComponent(name, isDirectory: true)
                guard fileManager.fileExists(atPath: source.path) else { continue }
                do {
                    try copyMissingTree(from: source, to: destination, fileManager: fileManager)
                    registerArtifactRoot(source, destination: destination, defaults: defaults)
                } catch {
                    failures.append(error.localizedDescription)
                }
            }
        }
        // An unreadable sandbox container can be selected explicitly in Output Settings.
        if failures.isEmpty { defaults.set(migrationVersion, forKey: completionKey) }
        return failures
    }

    static func importPreferences(_ values: [String: Any], into defaults: UserDefaults) {
        let keys = [
            AppStorageKey.aiProvider, AppStorageKey.hostedAIConsentAccepted,
            AppStorageKey.ollamaModel, AppStorageKey.openAIModel, AppStorageKey.anthropicModel,
            AppStorageKey.appleModel, AppStorageKey.preparedMLXModels, AppStorageKey.dryRun,
            AppStorageKey.notificationsEnabled, AppStorageKey.hasSeenWelcome,
            AppStorageKey.outputFolderPath, AppStorageKey.outputFolderBookmark,
            AppStorageKey.recentDocuments, AppStorageKey.expandedSubjectIDs, AppStorageKey.settingsPane,
            AppStorageKey.selectedBoardID, AppStorageKey.selectedPaperID, AppStorageKey.qualityInspectorVisible,
            AppStorageKey.favoriteBoardIDs, AppStorageKey.recentConfigurationIDs,
            AppStorageKey.historyRetentionLimit, AppStorageKey.navigationColumnVisibility,
            AppStorageKey.sidebarSelection, "interfaceLanguage",
        ]
        for key in keys where defaults.object(forKey: key) == nil {
            if let value = values[key] { defaults.set(value, forKey: key) }
        }
        let familyKey = AppStorageKey.frenchSavedFamilyIDs
        guard let importedValue = values[familyKey] else { return }
        guard let imported = importedValue as? [String],
              let current = (defaults.object(forKey: familyKey) ?? [String]()) as? [String] else {
            // Keep both original ledgers intact. Never treat an unreadable import as unused families.
            defaults.set(true, forKey: frenchFamilyImportFailedKey)
            return
        }
        defaults.set(Array(Set(current + imported)).sorted(), forKey: familyKey)
        defaults.removeObject(forKey: frenchFamilyImportFailedKey)
    }

    static func importData(
        from source: URL, defaults: UserDefaults = .standard, fileManager: FileManager = .default,
        distributionMode: DistributionMode = .current,
        legacyDomainReader: (UserDefaults, String) -> [String: Any]? = { $0.persistentDomain(forName: $1) }
    ) throws {
        let support = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? fileManager.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support")
        let destination = support.appendingPathComponent("Keldin")
        try copyMissingTree(from: source, to: destination, fileManager: fileManager)
        registerArtifactRoot(source, destination: destination, defaults: defaults)
        // A selected folder grants file access, not access to another preference
        // domain. Store builds import only the selected files.
        if distributionMode == .direct {
            importPreferences(legacyDomainReader(defaults, legacyBundleID) ?? [:], into: defaults)
        }
    }

    private static func registerArtifactRoot(_ source: URL, destination: URL, defaults: UserDefaults) {
        var mappings = defaults.dictionary(forKey: artifactMappingsKey) as? [String: String] ?? [:]
        mappings[source.standardizedFileURL.path] = destination.standardizedFileURL.path
        defaults.set(mappings, forKey: artifactMappingsKey)
    }

    static func relocatedArtifact(
        _ file: GeneratedFile, defaults: UserDefaults = .standard,
        readData: (URL) throws -> Data = { try Data(contentsOf: $0, options: .mappedIfSafe) }
    ) -> GeneratedFile {
        let path = file.url.standardizedFileURL.path
        let mappings = defaults.dictionary(forKey: artifactMappingsKey) as? [String: String] ?? [:]
        for source in mappings.keys.sorted(by: { $0.count > $1.count }) where path.hasPrefix(source + "/") {
            guard let destination = mappings[source] else { continue }
            let relative = String(path.dropFirst(source.count + 1))
            let url = URL(fileURLWithPath: destination).appendingPathComponent(relative)
            guard verifiedArtifactCopy(file, destination: url, defaults: defaults, readData: readData) else { continue }
            // Change only the history pointer. Assessment packages and PDF bytes keep their hashes.
            return GeneratedFile(id: file.id, role: file.role, url: url, createdAt: file.createdAt, subject: file.subject, paper: file.paper)
        }
        return file
    }

    private static func verifiedArtifactCopy(
        _ file: GeneratedFile, destination: URL, defaults: UserDefaults,
        readData: (URL) throws -> Data
    ) -> Bool {
        let key = file.id.uuidString
        var proofs = defaults.dictionary(forKey: verifiedArtifactCopiesKey) as? [String: [String: String]] ?? [:]
        func revokeProof() {
            guard proofs.removeValue(forKey: key) != nil else { return }
            defaults.set(proofs, forKey: verifiedArtifactCopiesKey)
        }
        guard let copied = try? regularArtifactData(at: destination, readData: readData) else {
            revokeProof()
            return false
        }
        let digest = SHA256.hash(data: copied).map { String(format: "%02x", $0) }.joined()
        let expected = [
            "source": file.url.standardizedFileURL.path,
            "destination": destination.standardizedFileURL.path,
            "sha256": digest,
        ]
        do {
            let original = try regularArtifactData(at: file.url, readData: readData)
            guard original == copied else {
                revokeProof()
                return false
            }
            // Only a byte-verified copy may outlive its original location.
            proofs[key] = expected
            defaults.set(proofs, forKey: verifiedArtifactCopiesKey)
            return true
        } catch let error as CocoaError where [.fileNoSuchFile, .fileReadNoSuchFile].contains(error.code) {
            guard proofs[key] == expected else {
                revokeProof()
                return false
            }
            return true
        } catch {
            // A present but unreadable original is not proof of a matching copy.
            revokeProof()
            return false
        }
    }

    private static func regularArtifactData(at url: URL, readData: (URL) throws -> Data) throws -> Data {
        // Inspect the current filesystem entry, including the link itself.
        let attributes = try FileManager.default.attributesOfItem(atPath: url.path)
        guard attributes[.type] as? FileAttributeType == .typeRegular else {
            throw CocoaError(.fileReadUnsupportedScheme)
        }
        return try readData(url)
    }

    static func copyMissingTree(from source: URL, to destination: URL, fileManager: FileManager = .default) throws {
        let sourceValues = try source.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
        guard sourceValues.isDirectory == true, sourceValues.isSymbolicLink != true else {
            throw CocoaError(.fileReadUnsupportedScheme)
        }
        let resolvedSource = source.resolvingSymlinksInPath().standardizedFileURL.path
        let resolvedDestination = destination.resolvingSymlinksInPath().standardizedFileURL.path
        guard resolvedDestination != resolvedSource,
              !resolvedDestination.hasPrefix(resolvedSource + "/") else {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        if let values = try? destination.resourceValues(forKeys: [.isSymbolicLinkKey]), values.isSymbolicLink == true {
            throw CocoaError(.fileWriteInvalidFileName)
        }
        try fileManager.createDirectory(at: destination, withIntermediateDirectories: true)
        for child in try fileManager.contentsOfDirectory(at: source, includingPropertiesForKeys: [.isDirectoryKey, .isSymbolicLinkKey]) {
            let target = destination.appendingPathComponent(child.lastPathComponent)
            let values = try child.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
            if values.isSymbolicLink == true {
                // Model snapshots use relative links to blob files. Copy the link itself.
                if !fileManager.fileExists(atPath: target.path),
                   (try? target.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink) != true {
                    try copyMissingItem(from: child, to: target, fileManager: fileManager)
                }
            } else if values.isDirectory == true {
                try copyMissingTree(from: child, to: target, fileManager: fileManager)
            } else if !fileManager.fileExists(atPath: target.path),
                      (try? target.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink) != true {
                try copyMissingItem(from: child, to: target, fileManager: fileManager)
            }
        }
    }

    private static func copyMissingItem(from source: URL, to destination: URL, fileManager: FileManager) throws {
        let temporary = destination.deletingLastPathComponent().appendingPathComponent(".keldin-import-\(UUID().uuidString)")
        defer { try? fileManager.removeItem(at: temporary) }
        try fileManager.copyItem(at: source, to: temporary)
        do {
            // Renaming a complete sibling copy keeps interrupted imports out of history.
            try fileManager.moveItem(at: temporary, to: destination)
        } catch {
            if !fileManager.fileExists(atPath: destination.path) { throw error }
        }
    }

}
