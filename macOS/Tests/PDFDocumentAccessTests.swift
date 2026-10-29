import Foundation
import PDFKit
import SwiftUI
import XCTest
@testable import Keldin

final class PDFDocumentAccessTests: XCTestCase {
    private var root: URL!

    override func setUpWithError() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent("KeldinPDFAccess-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws { try FileManager.default.removeItem(at: root) }

    @MainActor
    func testPickerSelectionUpdatesTheActionDocumentBeforeDeferredViewChanges() throws {
        let scheme = GeneratedFile(role: "mark_scheme", url: try makePDF(name: "scheme.pdf", pages: 24))
        let subject = GeneratedFile(role: "question_paper", url: try makePDF(name: "subject.pdf", pages: 36))
        func record(for file: GeneratedFile) -> GenerationJobRecord {
            GenerationJobRecord(
                configuration: GenerationConfiguration(boardID: "accounting-aqa", paperID: "1", provider: "fixture", model: "fixture", seed: 1, dryRun: false),
                provenance: GenerationProvenance(appVersion: "fixture", provider: "fixture", model: "fixture"),
                state: .completed, artifacts: [file],
                qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false)
            )
        }
        let records = [record(for: scheme), record(for: subject)]
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: scheme, provenance: records[0])
        var selectedID: GeneratedFile.ID? = scheme.id
        let binding = controller.selectionBinding(
            selection: Binding(get: { selectedID }, set: { selectedID = $0 }),
            files: [scheme, subject], records: records
        )

        binding.wrappedValue = subject.id
        // An immediate Print/Quick Look action refreshes before opening its
        // panel. No SwiftUI onChange or run-loop turn has occurred here.
        controller.refresh()

        XCTAssertEqual(selectedID, subject.id)
        XCTAssertEqual(controller.selectedFile?.id, subject.id)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 36)
        XCTAssertEqual(controller.provenance?.id, records[1].id)
        XCTAssertTrue(controller.canAccessDocument)
        binding.wrappedValue = scheme.id
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 24)
        XCTAssertEqual(controller.provenance?.id, records[0].id)
    }

    @MainActor
    func testPickerSelectionCannotActOnThePriorPDFWhenTheNewFileIsUnreadable() throws {
        let readable = GeneratedFile(role: "mark_scheme", url: try makePDF())
        let unreadable = GeneratedFile(role: "question_paper", url: root.appendingPathComponent("missing.pdf"))
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: readable, provenance: nil)
        var selectedID: GeneratedFile.ID? = readable.id
        let binding = controller.selectionBinding(
            selection: Binding(get: { selectedID }, set: { selectedID = $0 }),
            files: [readable, unreadable], records: []
        )

        binding.wrappedValue = unreadable.id

        XCTAssertEqual(controller.selectedFile?.id, unreadable.id)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
    }

    @MainActor
    func testExistingButDeniedPDFHasAnHonestFailureAndDisabledActions() throws {
        let url = try makePDF()
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(), readData: { _ in throw CocoaError(.fileReadNoPermission) }))
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        XCTAssertTrue(FileManager.default.fileExists(atPath: url.path))
        XCTAssertEqual(controller.loadFailure, .permissionDenied)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
    }

    @MainActor
    func testMissingInvalidAndLockedInputsAreNotReadyDocuments() throws {
        let access = PDFDocumentAccess(defaults: defaults())
        assertFailure(access.load(root.appendingPathComponent("missing.pdf")), .missing)
        let invalid = root.appendingPathComponent("invalid.pdf")
        try Data("not a PDF".utf8).write(to: invalid)
        assertFailure(access.load(invalid), .invalid)
        let locked = try makePDF(name: "locked.pdf")
        let document = try XCTUnwrap(PDFDocument(url: locked))
        XCTAssertTrue(document.write(to: locked, withOptions: [.ownerPasswordOption: "owner", .userPasswordOption: "secret"]))
        assertFailure(access.load(locked), .locked)
    }

    @MainActor
    func testSelectionAndLaterReadFailureNeverLeaveThePreviousPDFReady() throws {
        let first = try makePDF()
        let second = try makePDF(name: "second.pdf")
        var denied = false
        let access = PDFDocumentAccess(defaults: defaults(), readData: { url in
            if denied { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: url)
        })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: first), provenance: nil)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 1)
        denied = true
        controller.update(file: GeneratedFile(role: "mark_scheme", url: second), provenance: nil)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
        denied = false
        controller.refresh()
        XCTAssertTrue(controller.canAccessDocument)
        denied = true
        controller.refresh()
        XCTAssertFalse(controller.canAccessDocument)
        controller.update(file: nil, provenance: nil)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertNil(controller.loadFailure)
    }

    @MainActor
    func testRecoveryCancelAndWrongFileDoNotGrantAccessOrOverwriteAnything() throws {
        let expected = try makePDF()
        let other = try makePDF(name: "other.pdf")
        let original = try Data(contentsOf: expected)
        let settings = defaults()
        settings.set(Data("output-grant".utf8), forKey: AppStorageKey.outputFolderBookmark)
        var starts = 0
        let access = PDFDocumentAccess(defaults: settings, startAccess: { _ in starts += 1; return true })
        XCTAssertFalse(try access.recover(expected: expected, selected: nil))
        XCTAssertThrowsError(try access.recover(expected: expected, selected: other)) { XCTAssertEqual($0 as? PDFLoadFailure, .wrongFile) }
        XCTAssertEqual(starts, 0)
        XCTAssertNil(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey))
        XCTAssertEqual(settings.data(forKey: AppStorageKey.outputFolderBookmark), Data("output-grant".utf8))
        XCTAssertEqual(try Data(contentsOf: expected), original)
    }

    @MainActor
    func testExactFileRecoveryAndRestartRestoreBalancedReadOnlyGrants() throws {
        let expected = try makePDF()
        let bytes = try Data(contentsOf: expected)
        let settings = defaults()
        let marker = Data("per-document-grant".utf8)
        var active = false
        var starts = 0
        var stops = 0
        func service() -> PDFDocumentAccess {
            PDFDocumentAccess(defaults: settings, readData: { url in
                guard active else { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            }, startAccess: { _ in starts += 1; active = true; return true }, stopAccess: { _ in stops += 1; active = false }, makeBookmark: { _ in marker }, resolveBookmark: { data in
                XCTAssertEqual(data, marker)
                return (expected, false)
            })
        }
        let access = service()
        assertFailure(access.load(expected), .permissionDenied)
        XCTAssertTrue(try access.recover(expected: expected, selected: expected))
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey)?[expected.standardizedFileURL.path] as? Data, marker)
        XCTAssertNotNil(try? access.load(expected).get())
        access.release()
        XCTAssertEqual(stops, 1)
        let restarted = service()
        XCTAssertNotNil(try? restarted.load(expected).get())
        XCTAssertEqual(starts, 2)
        restarted.release()
        XCTAssertEqual(stops, 2)
        XCTAssertEqual(try Data(contentsOf: expected), bytes)
    }

    @MainActor
    func testFailedOrWrongBookmarkResolutionNeverChangesOutputGrant() throws {
        let expected = try makePDF()
        let settings = defaults()
        settings.set([expected.standardizedFileURL.path: Data("old".utf8)], forKey: PDFDocumentAccess.bookmarkKey)
        settings.set(Data("output".utf8), forKey: AppStorageKey.outputFolderBookmark)
        var starts = 0
        let access = PDFDocumentAccess(defaults: settings, readData: { _ in throw CocoaError(.fileReadNoPermission) }, startAccess: { _ in starts += 1; return true }, resolveBookmark: { _ in (self.root.appendingPathComponent("other.pdf"), false) })
        assertFailure(access.load(expected), .permissionDenied)
        XCTAssertEqual(starts, 0)
        XCTAssertEqual(settings.data(forKey: AppStorageKey.outputFolderBookmark), Data("output".utf8))
    }

    @MainActor
    func testActionsRecheckReadabilityBeforeOpeningPanelsOrPrinting() throws {
        let url = try makePDF()
        var denied = false
        let access = PDFDocumentAccess(defaults: defaults(), readData: { source in
            if denied { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: source)
        })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        denied = true
        controller.printSelected()
        XCTAssertFalse(controller.canAccessDocument)
        XCTAssertEqual(controller.loadFailure, .permissionDenied)
        XCTAssertNotNil(controller.exportError)
        controller.exportError = nil
        controller.exportSelected()
        XCTAssertNotNil(controller.exportError)
        XCTAssertNil(controller.loadedPDF)
    }

    @MainActor
    func testUnchangedRefreshPreservesTheReaderDocumentButNewBytesReplaceIt() throws {
        let url = try makePDF()
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        let original = try XCTUnwrap(controller.loadedPDF?.document)

        controller.refresh()
        XCTAssertTrue(controller.loadedPDF?.document === original)

        let changed = PDFDocument()
        changed.insert(PDFPage(), at: 0)
        changed.insert(PDFPage(), at: 1)
        XCTAssertTrue(changed.write(to: url))
        controller.refresh()
        XCTAssertFalse(controller.loadedPDF?.document === original)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 2)

        try Data("now invalid".utf8).write(to: url)
        controller.refresh()
        XCTAssertNil(controller.loadedPDF)
        XCTAssertEqual(controller.loadFailure, .invalid)
        XCTAssertFalse(controller.canAccessDocument)
    }

    @MainActor
    func testFailedBookmarkSaveBalancesAccessAndPreservesPriorBookmarks() throws {
        let expected = try makePDF()
        let settings = defaults()
        let previous = ["/some/other/file.pdf": Data("prior-grant".utf8)]
        settings.set(previous, forKey: PDFDocumentAccess.bookmarkKey)
        var starts = 0
        var stops = 0
        let access = PDFDocumentAccess(defaults: settings, startAccess: { _ in starts += 1; return true }, stopAccess: { _ in stops += 1 }, makeBookmark: { _ in throw CocoaError(.fileWriteNoPermission) })
        XCTAssertThrowsError(try access.recover(expected: expected, selected: expected)) { XCTAssertEqual($0 as? PDFLoadFailure, .bookmark) }
        XCTAssertEqual(starts, 1)
        XCTAssertEqual(stops, 1)
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey) as? [String: Data], previous)
    }

    @MainActor
    func testStaleBookmarkIsRenewedOnlyForTheSameReadableFile() throws {
        let expected = try makePDF()
        let settings = defaults()
        settings.set([expected.standardizedFileURL.path: Data("stale".utf8)], forKey: PDFDocumentAccess.bookmarkKey)
        settings.set(Data("output".utf8), forKey: AppStorageKey.outputFolderBookmark)
        var stopped = 0
        let access = PDFDocumentAccess(defaults: settings, startAccess: { _ in true }, stopAccess: { _ in stopped += 1 }, makeBookmark: { _ in Data("renewed".utf8) }, resolveBookmark: { _ in (expected, true) })
        XCTAssertNotNil(try? access.load(expected).get())
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey)?[expected.standardizedFileURL.path] as? Data, Data("renewed".utf8))
        XCTAssertEqual(settings.data(forKey: AppStorageKey.outputFolderBookmark), Data("output".utf8))
        access.release()
        XCTAssertEqual(stopped, 1)
    }

    func testFailureNoticesHaveFrenchTranslations() {
        let cases: [(PDFLoadFailure, String)] = [
            (.missing, "Ce PDF ne se trouve plus à l’emplacement enregistré."),
            (.permissionDenied, "Keldin ne peut pas lire ce PDF. Choisissez le même fichier pour autoriser l’accès."),
            (.unreadable, "Impossible de lire ce PDF. Vérifiez le fichier, puis réessayez."),
            (.invalid, "Ce fichier n’a pas pu être ouvert en tant que PDF."),
            (.locked, "Ce PDF est verrouillé. Déverrouillez-le en dehors de Keldin, puis réessayez."),
            (.wrongFile, "Choisissez le PDF indiqué dans Historique. Aucun autre fichier ne le remplacera."),
            (.bookmark, "L’autorisation d’accès à ce PDF n’a pas pu être enregistrée. Choisissez à nouveau le fichier."),
        ]
        for (failure, expected) in cases {
            XCTAssertEqual(InterfaceText.resolve(failure.messageResource, language: "fr"), expected)
            XCTAssertNotEqual(InterfaceText.resolve(failure.messageResource, language: "en"), expected)
        }
    }

    private func defaults() -> UserDefaults { UserDefaults(suiteName: "PDFAccessTests-\(UUID().uuidString)")! }

    private func makePDF(name: String = "paper.pdf", pages: Int = 1) throws -> URL {
        let url = root.appendingPathComponent(name)
        let pdf = PDFDocument()
        for index in 0 ..< pages { pdf.insert(PDFPage(), at: index) }
        XCTAssertTrue(pdf.write(to: url))
        return url
    }

    private func assertFailure(_ result: Result<LoadedPDF, PDFLoadFailure>, _ expected: PDFLoadFailure, file: StaticString = #filePath, line: UInt = #line) {
        switch result {
        case .success: XCTFail("Expected unavailable PDF", file: file, line: line)
        case .failure(let actual): XCTAssertEqual(actual, expected, file: file, line: line)
        }
    }
}
