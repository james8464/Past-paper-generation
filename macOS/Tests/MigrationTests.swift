// Exercise file and preference imports with isolated data, never a user's installed app.

import Foundation
import XCTest
@testable import Keldin

final class MigrationTests: XCTestCase {
    func testArtifactCollisionNeverSubstitutesDifferentDestinationBytes() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationCollision-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let original = Data("original assessment".utf8)
        let current = Data("different current assessment".utf8)
        try original.write(to: source)
        try current.write(to: destination)
        try KeldinMigration.copyMissingTree(from: old, to: new)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)

        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)
        XCTAssertEqual(try Data(contentsOf: source), original)
        XCTAssertEqual(try Data(contentsOf: destination), current)
    }

    func testMissingOriginalRequiresVerifiedCopyAndRejectsLaterDestinationChanges() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationProof-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let bytes = Data("verified original assessment".utf8)
        try bytes.write(to: destination)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)

        try bytes.write(to: source)
        let verified = KeldinMigration.relocatedArtifact(artifact, defaults: defaults)
        XCTAssertEqual(verified.url, destination)
        XCTAssertEqual(verified.id, artifact.id)
        try FileManager.default.removeItem(at: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), verified)

        try Data("replacement assessment".utf8).write(to: destination)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact)
    }

    func testObservedSourceConflictRevokesProofBeforeTheOriginalDisappears() throws {
        for failure in ["changed bytes", "read denied", "symbolic link"] {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationRevocation-\(UUID().uuidString)")
            defer { try? FileManager.default.removeItem(at: root) }
            let old = root.appendingPathComponent("old")
            let new = root.appendingPathComponent("new")
            try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
            try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
            let source = old.appendingPathComponent("paper.pdf")
            let destination = new.appendingPathComponent("paper.pdf")
            let bytes = Data("assessment A".utf8)
            try bytes.write(to: source)
            try bytes.write(to: destination)
            let defaults = isolatedDefaults()
            defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
            let artifact = GeneratedFile(role: "question_paper", url: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)

            if failure == "changed bytes" {
                try Data("assessment B".utf8).write(to: source)
            } else if failure == "symbolic link" {
                try FileManager.default.removeItem(at: source)
                try FileManager.default.createSymbolicLink(atPath: source.path, withDestinationPath: destination.path)
            }
            let refused = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
                if failure == "read denied", url == source { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            })
            XCTAssertEqual(refused, artifact, failure)

            try FileManager.default.removeItem(at: source)

            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact, failure)
            XCTAssertEqual(try Data(contentsOf: destination), bytes)
            try bytes.write(to: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
            try FileManager.default.removeItem(at: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
        }
    }

    func testRejectedDestinationRevokesProofBeforeTheOriginalDisappears() throws {
        for failure in ["read denied", "symbolic link"] {
            let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationDestination-\(UUID().uuidString)")
            defer { try? FileManager.default.removeItem(at: root) }
            let old = root.appendingPathComponent("old")
            let new = root.appendingPathComponent("new")
            try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
            try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
            let source = old.appendingPathComponent("paper.pdf")
            let destination = new.appendingPathComponent("paper.pdf")
            let bytes = Data("assessment A".utf8)
            try bytes.write(to: source)
            try bytes.write(to: destination)
            let defaults = isolatedDefaults()
            defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
            let artifact = GeneratedFile(role: "question_paper", url: source)
            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)
            if failure == "symbolic link" {
                try FileManager.default.removeItem(at: destination)
                try FileManager.default.createSymbolicLink(atPath: destination.path, withDestinationPath: source.path)
            }

            let refused = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
                if failure == "read denied", url == destination { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            })
            XCTAssertEqual(refused, artifact, failure)
            try FileManager.default.removeItem(at: source)
            if failure == "symbolic link" { try FileManager.default.removeItem(at: destination) }
            try bytes.write(to: destination)

            XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults), artifact, failure)
        }
    }

    func testIdentityMigrationRevisitsVersionOneForTheV35FamilyLedger() {
        let defaults = isolatedDefaults()
        defaults.set(1, forKey: KeldinMigration.completionKey)
        XCTAssertTrue(KeldinMigration.needsImport(defaults: defaults))
        defaults.set(2, forKey: KeldinMigration.completionKey)
        XCTAssertFalse(KeldinMigration.needsImport(defaults: defaults))
    }

    @MainActor
    func testImportRetainsFrenchFamilyUseAfterJobHistoryPruning() throws {
        let defaults = isolatedDefaults()
        let families = FrenchAssessmentRequest.familyIDs
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: families], into: defaults)
        let application = isolatedApplication(defaults: defaults)
        XCTAssertEqual(try application.savedFrenchFamilies(), Array(families.indices))
    }

    @MainActor
    func testImportUnionsFrenchFamilyUseWithoutReplacingCurrentUse() throws {
        let defaults = isolatedDefaults()
        let families = FrenchAssessmentRequest.familyIDs
        defaults.set([families[0]], forKey: AppStorageKey.frenchSavedFamilyIDs)
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: [families[4]]], into: defaults)
        XCTAssertEqual(try isolatedApplication(defaults: defaults).savedFrenchFamilies(), [0, 4])
    }

    @MainActor
    func testCorruptImportedFamilyLedgerBlocksGenerationWithoutDeletingCurrentUse() {
        let defaults = isolatedDefaults()
        let existing = [FrenchAssessmentRequest.familyIDs[0]]
        defaults.set(existing, forKey: AppStorageKey.frenchSavedFamilyIDs)
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: "not an array"], into: defaults)
        XCTAssertEqual(defaults.stringArray(forKey: AppStorageKey.frenchSavedFamilyIDs), existing)
        XCTAssertThrowsError(try isolatedApplication(defaults: defaults).savedFrenchFamilies())
        KeldinMigration.importPreferences([AppStorageKey.frenchSavedFamilyIDs: [FrenchAssessmentRequest.familyIDs[4]]], into: defaults)
        XCTAssertEqual(try isolatedApplication(defaults: defaults).savedFrenchFamilies(), [0, 4])
    }

    func testImportPreservesCurrentPreferencesAndIgnoresUnknownKeys() {
        let defaults = isolatedDefaults()
        defaults.set("current", forKey: AppStorageKey.ollamaModel)
        KeldinMigration.importPreferences([
            AppStorageKey.ollamaModel: "previous",
            AppStorageKey.selectedBoardID: "economics_aqa",
            "interfaceLanguage": "fr",
            "unrelated": "ignored",
        ], into: defaults)
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.ollamaModel), "current")
        XCTAssertEqual(defaults.string(forKey: AppStorageKey.selectedBoardID), "economics_aqa")
        XCTAssertEqual(defaults.string(forKey: "interfaceLanguage"), "fr")
        XCTAssertNil(defaults.object(forKey: "unrelated"))
    }

    func testImportMergesHistoryWithoutReplacingCurrentRecords() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old/Job History")
        let new = root.appendingPathComponent("new/Job History")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        try Data("old".utf8).write(to: old.appendingPathComponent("conflict.json"))
        try Data("new".utf8).write(to: new.appendingPathComponent("conflict.json"))
        try Data("accepted".utf8).write(to: old.appendingPathComponent("accepted.json"))
        try KeldinMigration.copyMissingTree(from: root.appendingPathComponent("old"), to: root.appendingPathComponent("new"))
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("conflict.json"), encoding: .utf8), "new")
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("accepted.json"), encoding: .utf8), "accepted")
        XCTAssertEqual(try String(contentsOf: old.appendingPathComponent("conflict.json"), encoding: .utf8), "old")
        XCTAssertThrowsError(try KeldinMigration.copyMissingTree(from: old, to: old.appendingPathComponent("recursive")))
    }

    func testEnvironmentAliasDoesNotOverrideAnExplicitEmptyValue() {
        XCTAssertEqual(KeldinMigration.environmentValue("KELDIN_ROOT", environment: ["PAPER_CREATOR_ROOT": "/old"]), "/old")
        XCTAssertEqual(KeldinMigration.environmentValue("KELDIN_ROOT", environment: ["KELDIN_ROOT": "", "PAPER_CREATOR_ROOT": "/old"]), "")
    }

    func testModelSnapshotLinksAreCopiedWithoutFollowingThem() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try Data("weights".utf8).write(to: old.appendingPathComponent("blob"))
        try FileManager.default.createSymbolicLink(atPath: old.appendingPathComponent("snapshot").path, withDestinationPath: "blob")
        try KeldinMigration.copyMissingTree(from: old, to: new)
        XCTAssertEqual(try FileManager.default.destinationOfSymbolicLink(atPath: new.appendingPathComponent("snapshot").path), "blob")
        XCTAssertEqual(try String(contentsOf: new.appendingPathComponent("snapshot"), encoding: .utf8), "weights")
    }


    func testImportedHistoryPointsToCopiedArtifactsWithoutChangingTheirIdentity() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let target = new.appendingPathComponent("paper.pdf")
        try Data("saved PDF".utf8).write(to: target)
        try Data("saved PDF".utf8).write(to: old.appendingPathComponent("paper.pdf"))
        let file = GeneratedFile(role: "question_paper", url: old.appendingPathComponent("paper.pdf"))
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let relocated = KeldinMigration.relocatedArtifact(file, defaults: defaults)
        XCTAssertEqual(relocated.id, file.id)
        XCTAssertEqual(relocated.url, target)
        XCTAssertEqual(relocated.createdAt, file.createdAt)
        let external = GeneratedFile(role: "question_paper", url: root.appendingPathComponent("elsewhere.pdf"))
        XCTAssertEqual(KeldinMigration.relocatedArtifact(external, defaults: defaults), external)
    }

    func testUnreadableOriginalCannotUseAnEarlierCopyProof() throws {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinMigrationDenied-\(UUID().uuidString)")
        defer { try? FileManager.default.removeItem(at: root) }
        let old = root.appendingPathComponent("old")
        let new = root.appendingPathComponent("new")
        try FileManager.default.createDirectory(at: old, withIntermediateDirectories: true)
        try FileManager.default.createDirectory(at: new, withIntermediateDirectories: true)
        let source = old.appendingPathComponent("paper.pdf")
        let destination = new.appendingPathComponent("paper.pdf")
        let bytes = Data("matching assessment".utf8)
        try bytes.write(to: source)
        try bytes.write(to: destination)
        let defaults = isolatedDefaults()
        defaults.set([old.path: new.path], forKey: KeldinMigration.artifactMappingsKey)
        let artifact = GeneratedFile(role: "question_paper", url: source)
        XCTAssertEqual(KeldinMigration.relocatedArtifact(artifact, defaults: defaults).url, destination)

        let result = KeldinMigration.relocatedArtifact(artifact, defaults: defaults, readData: { url in
            if url == source { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: url)
        })

        XCTAssertEqual(result, artifact)
        XCTAssertEqual(try Data(contentsOf: source), bytes)
        XCTAssertEqual(try Data(contentsOf: destination), bytes)
    }

}
