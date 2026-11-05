import Foundation
import PDFKit
import SwiftUI
import Synchronization
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
    func testSlowPDFReadDoesNotBlockMainActorHeartbeat() async throws {
        let url = try makePDF()
        let bytes = try Data(contentsOf: url)
        let heartbeat = expectation(description: "Main actor responds while PDF read is pending")
        let readFinished = expectation(description: "Bounded PDF read finished")
        let probe = BoundedPDFReadProbe()
        let access = PDFDocumentAccess(defaults: defaults(), readData: { _ in
            probe.state.withLock {
                $0.readerOnMainThread = Thread.isMainThread
                $0.readStarted = DispatchTime.now().uptimeNanoseconds
            }
            // Queue the heartbeat only after the reader starts. An inherited
            // MainActor Task must not pass by returning before its slow read.
            DispatchQueue.global(qos: .userInitiated).async {
                probe.state.withLock { $0.heartbeatRequested = DispatchTime.now().uptimeNanoseconds }
                DispatchQueue.main.async {
                    probe.state.withLock { $0.heartbeatRan = DispatchTime.now().uptimeNanoseconds }
                    heartbeat.fulfill()
                }
            }
            // Deliberately simulate one bounded slow I/O operation, not a wait
            // for asynchronous state or an attempt to synchronise the test.
            Thread.sleep(forTimeInterval: 1)
            probe.state.withLock { $0.readFinished = DispatchTime.now().uptimeNanoseconds }
            readFinished.fulfill()
            return bytes
        }, makeBookmark: { Data($0.path.utf8) })
        let controller = DocumentActionController(access: access)
        defer { controller.clear() }
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        await controller.waitForPendingLoad()
        await fulfillment(of: [heartbeat, readFinished], timeout: 5)
        let sample = probe.state.withLock { $0 }
        guard sample.readStarted > 0, sample.heartbeatRequested >= sample.readStarted,
              sample.heartbeatRan >= sample.heartbeatRequested, sample.readFinished >= sample.readStarted else {
            return XCTFail("The bounded reader and heartbeat must produce ordered timestamps")
        }
        XCTAssertGreaterThan(sample.heartbeatRequested, sample.readStarted)
        XCTAssertLessThan(sample.heartbeatRequested, sample.readFinished,
            "The independent scheduler must request the heartbeat during the slow read")
        let delay = Double(sample.heartbeatRan - sample.heartbeatRequested) / 1_000_000_000
        print("PDF_READ_ISOLATION: readerOnMainThread=\(sample.readerOnMainThread), heartbeatDelaySeconds=\(delay), readDurationSeconds=\(Double(sample.readFinished - sample.readStarted) / 1_000_000_000)")
        XCTAssertFalse(sample.readerOnMainThread, "Blocking PDF byte reads must not run on the main thread")
        XCTAssertLessThan(delay, 0.25, "PDF loading must leave the main actor responsive during slow I/O")
    }

    @MainActor
    func testRapidSelectionRejectsLateErrorsAndKeepsReadLeasesUntilCompletion() async throws {
        let first = try makePDF()
        let second = try makePDF(name: "second.pdf", pages: 2)
        let bytes = try Data(contentsOf: second)
        let began = expectation(description: "First read entered")
        let stoppedFirst = expectation(description: "Cancelled first lease released")
        let reader = GatedPDFReader(started: began, blockedCalls: [1]) { _, call in
            if call == 1 { throw CocoaError(.fileReadNoPermission) }
            return bytes
        }
        var starts: [URL] = [], stops: [URL] = []
        let access = PDFDocumentAccess(defaults: defaults(), readData: { try reader.read($0) },
            startAccess: { starts.append($0); return true }, stopAccess: {
                stops.append($0)
                if $0 == first { stoppedFirst.fulfill() }
            }, makeBookmark: { Data($0.path.utf8) })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: first), provenance: nil)
        await fulfillment(of: [began], timeout: 3)
        let target = GeneratedFile(role: "mark_scheme", url: second)
        controller.update(file: target, provenance: nil)
        XCTAssertTrue(controller.isLoading)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertTrue(stops.isEmpty, "An interrupted read must keep its grant until it returns")
        reader.gate.signal()
        await controller.waitForPendingLoad()
        await fulfillment(of: [stoppedFirst], timeout: 3)
        XCTAssertEqual(controller.selectedFile, target)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 2)
        XCTAssertNil(controller.loadFailure)
        XCTAssertEqual(reader.calls.withLock { $0 }, [first, second])
        XCTAssertEqual(stops, [first])
        controller.clear()
        XCTAssertEqual(starts, [first, second])
        XCTAssertEqual(stops, [first, second])
    }

    @MainActor
    func testClearAndDeallocationKeepPendingReadGrantUntilWorkerFinishes() async throws {
        for lateError in [false, true] {
            let url = try makePDF(name: "pending-\(lateError).pdf")
            let bytes = try Data(contentsOf: url)
            let began = expectation(description: "Pending read entered")
            let stopped = expectation(description: "Pending grant released")
            let reader = GatedPDFReader(started: began, blockedCalls: [1]) { _, _ in
                if lateError { throw CocoaError(.fileReadNoPermission) }
                return bytes
            }
            let settings = defaults()
            var stopCount = 0
            let access = PDFDocumentAccess(defaults: settings, readData: { try reader.read($0) },
                startAccess: { _ in true }, stopAccess: { _ in stopCount += 1; stopped.fulfill() },
                makeBookmark: { _ in XCTFail("Cancelled reads must not save bookmarks"); return Data() })
            var controller: DocumentActionController? = DocumentActionController(access: access)
            let controllerWasReleased = { [weak controller] in controller == nil }
            controller?.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
            await fulfillment(of: [began], timeout: 3)
            if !lateError { controller?.clear() }
            controller = nil
            XCTAssertTrue(controllerWasReleased(), "Pending I/O must not retain its UI controller")
            XCTAssertEqual(stopCount, 0)
            reader.gate.signal()
            await fulfillment(of: [stopped], timeout: 3)
            XCTAssertEqual(stopCount, 1)
            XCTAssertNil(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey))
        }
    }

    @MainActor
    func testSameURLNewIdentityCancelsOldResultAndRepeatedUpdatesDoNotReadAgain() async throws {
        let url = try makePDF()
        let firstBytes = try Data(contentsOf: url)
        let replacementBytes = try Data(contentsOf: makePDF(name: "replacement.pdf", pages: 2))
        let began = expectation(description: "Old identity read entered")
        let reader = GatedPDFReader(started: began, blockedCalls: [1]) { _, call in
            call == 1 ? firstBytes : replacementBytes
        }
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(),
            readData: { try reader.read($0) }, makeBookmark: { Data($0.path.utf8) }))
        let old = GeneratedFile(role: "question_paper", url: url)
        let replacement = GeneratedFile(role: "mark_scheme", url: url)
        controller.update(file: old, provenance: nil)
        await fulfillment(of: [began], timeout: 3)
        controller.update(file: replacement, provenance: nil)
        controller.update(file: replacement, provenance: nil)
        XCTAssertNil(controller.loadedPDF)
        reader.gate.signal()
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.selectedFile, replacement)
        XCTAssertEqual(controller.loadedPDF?.bytes, replacementBytes)
        XCTAssertEqual(reader.calls.withLock { $0.count }, 2)
        let provenance = GenerationJobRecord(
            configuration: GenerationConfiguration(boardID: "accounting-aqa", paperID: "1", provider: "fixture", model: "fixture", seed: 1, dryRun: false),
            provenance: GenerationProvenance(appVersion: "fixture", provider: "fixture", model: "fixture"), state: .completed,
            artifacts: [replacement], qualification: QualificationSnapshot(engineeringValidated: false, visuallyCalibrated: false, empiricallyCalibrated: false))
        controller.update(file: replacement, provenance: provenance)
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.provenance, provenance)
        XCTAssertEqual(reader.calls.withLock { $0.count }, 2)
        controller.clear()
    }

    @MainActor
    func testAllActionsRevalidateOriginalBytesBeforeCallingNativePresenter() async throws {
        let url = try makePDF()
        let currentBytes = try Data(contentsOf: makePDF(name: "action-current.pdf", pages: 2))
        let reads = Mutex(0)
        var presented: [DocumentActionController.Action] = []
        let file = GeneratedFile(role: "question_paper", url: url)
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(), readData: { url in
            reads.withLock { $0 += 1 }
            return try Data(contentsOf: url)
        }), presentAction: { action, selected, pdf in
            presented.append(action)
            XCTAssertEqual(selected, file)
            XCTAssertEqual(pdf.bytes, currentBytes)
        })
        controller.update(file: file, provenance: nil)
        await controller.waitForPendingLoad()
        try currentBytes.write(to: url)
        for action in [DocumentActionController.Action.quickLook, .reveal, .print, .export] {
            invoke(action, on: controller)
            XCTAssertFalse(controller.canAccessDocument)
            await controller.waitForPendingLoad()
        }
        XCTAssertEqual(presented, [.quickLook, .reveal, .print, .export])
        XCTAssertEqual(reads.withLock { $0 }, 5)
        controller.clear()
    }

    @MainActor
    func testStaleActionReadsNeverPresentAnyNativeAction() async throws {
        for action in [DocumentActionController.Action.quickLook, .reveal, .print, .export] {
            let first = try makePDF(name: "action-first.pdf")
            let second = try makePDF(name: "action-second.pdf", pages: 2)
            let bytes = try Data(contentsOf: first)
            let began = expectation(description: "Action revalidation entered")
            let reader = GatedPDFReader(started: began, blockedCalls: [2]) { _, _ in bytes }
            var presented = 0
            let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(),
                readData: { try reader.read($0) }), presentAction: { _, _, _ in presented += 1 })
            controller.update(file: GeneratedFile(role: "question_paper", url: first), provenance: nil)
            await controller.waitForPendingLoad()
            invoke(action, on: controller)
            await fulfillment(of: [began], timeout: 3)
            let replacement = GeneratedFile(role: "mark_scheme", url: second)
            controller.update(file: replacement, provenance: nil)
            XCTAssertNil(controller.loadedPDF)
            reader.gate.signal()
            await controller.waitForPendingLoad()
            XCTAssertEqual(presented, 0)
            XCTAssertEqual(controller.selectedFile, replacement)
            controller.clear()
        }
    }

    @MainActor
    func testAsyncStaleBookmarkRenewsTheRestoredSecurityURLRepresentation() async throws {
        let expected = try makePDF()
        let restored = URL(fileURLWithPath: expected.deletingLastPathComponent().path + "/./" + expected.lastPathComponent)
        XCTAssertNotEqual(restored.absoluteString, expected.absoluteString)
        let bytes = try Data(contentsOf: expected)
        let settings = defaults()
        settings.set([expected.standardizedFileURL.path: Data("stale".utf8)], forKey: PDFDocumentAccess.bookmarkKey)
        var starts: [URL] = [], bookmarks: [URL] = [], stops: [URL] = []
        let access = PDFDocumentAccess(defaults: settings, readData: { _ in bytes },
            startAccess: { starts.append($0); return true }, stopAccess: { stops.append($0) },
            makeBookmark: { bookmarks.append($0); return Data("renewed".utf8) },
            resolveBookmark: { _ in (restored, true) })
        let loaded = try await access.loadAsync(expected)
        XCTAssertNoThrow(try access.remember(loaded).get())
        XCTAssertEqual(starts.map(\.absoluteString), [restored.absoluteString])
        XCTAssertEqual(bookmarks.map(\.absoluteString), [restored.absoluteString])
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey)?[expected.standardizedFileURL.path] as? Data, Data("renewed".utf8))
        loaded.lease.release()
        XCTAssertEqual(stops.map(\.absoluteString), [restored.absoluteString])
    }

    @MainActor
    func testAsyncRecoveryUsesSelectedURLGrantAndBalancesFailedBookmarkLease() async throws {
        let expected = try makePDF()
        let selected = URL(fileURLWithPath: expected.deletingLastPathComponent().path + "/./" + expected.lastPathComponent)
        XCTAssertNotEqual(selected.absoluteString, expected.absoluteString)
        XCTAssertEqual(selected.standardizedFileURL, expected.standardizedFileURL)
        let bytes = try Data(contentsOf: expected)
        var grants: [URL] = [], bookmarks: [URL] = [], stops: [URL] = []
        var failBookmark = false
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(), readData: { _ in bytes },
            startAccess: { grants.append($0); return true }, stopAccess: { stops.append($0) }, makeBookmark: {
                bookmarks.append($0)
                if failBookmark { throw CocoaError(.fileWriteNoPermission) }
                return Data($0.absoluteString.utf8)
            }))
        controller.update(file: GeneratedFile(role: "question_paper", url: expected), provenance: nil)
        await controller.waitForPendingLoad()
        let prior = try XCTUnwrap(controller.loadedPDF?.document)
        grants.removeAll(); bookmarks.removeAll(); stops.removeAll()
        controller.recoverAccess(selected: nil)
        controller.recoverAccess(selected: expected.deletingLastPathComponent().appendingPathComponent("wrong.pdf"))
        XCTAssertTrue(grants.isEmpty)
        XCTAssertTrue(controller.loadedPDF?.document === prior)
        controller.recoverAccess(selected: selected)
        await controller.waitForPendingLoad()
        XCTAssertEqual(grants.map(\.absoluteString), [selected.absoluteString])
        XCTAssertEqual(bookmarks.map(\.absoluteString), [selected.absoluteString])
        failBookmark = true
        controller.recoverAccess(selected: selected)
        await controller.waitForPendingLoad()
        XCTAssertNotNil(controller.exportError)
        XCTAssertTrue(controller.loadedPDF?.document === prior)
        XCTAssertEqual(stops.count, 2, "The failed new bookmark must release its lease before completion")
        controller.clear()
        XCTAssertEqual(stops.count, 3)
    }

    @MainActor
    func testRetainedActionLeaseSurvivesSelectionReleaseAndStopsOnceAfterClose() throws {
        var stops = 0
        let selection = PDFReadLease { stops += 1 }
        let firstPreview = try XCTUnwrap(selection.retained())
        let owner = QuickLookLeaseOwner()
        owner.replace(with: firstPreview)
        owner.replace(with: firstPreview)
        selection.release()
        XCTAssertEqual(stops, 0)
        XCTAssertNil(selection.retained())
        let replacementPreview = try XCTUnwrap(firstPreview.retained())
        owner.replace(with: replacementPreview)
        firstPreview.release()
        XCTAssertEqual(stops, 0)
        owner.clear()
        owner.clear()
        replacementPreview.release()
        XCTAssertEqual(stops, 1)
    }

    @MainActor
    private func invoke(_ action: DocumentActionController.Action, on controller: DocumentActionController) {
        switch action {
        case .quickLook: controller.quickLookSelected()
        case .reveal: controller.revealSelected()
        case .print: controller.printSelected()
        case .export: controller.exportSelected()
        }
    }

    @MainActor
    func testNonFilePDFURLsRefuseBeforeReaderBookmarksOrScopeAccess() throws {
        for url in [URL(string: "https://example.invalid/owned.pdf")!, URL(string: "data:application/pdf,owned")!] {
            let settings = defaults()
            let saved = [url.standardizedFileURL.path: Data("owned-fixture".utf8)]
            settings.set(saved, forKey: PDFDocumentAccess.bookmarkKey)
            let reads = Mutex(0)
            var resolves = 0
            var bookmarks = 0
            var starts = 0
            var stops = 0
            let access = PDFDocumentAccess(defaults: settings, readData: { _ in
                reads.withLock { $0 += 1 }
                throw CocoaError(.fileReadNoSuchFile)
            }, startAccess: { _ in starts += 1; return true }, stopAccess: { _ in stops += 1 }, makeBookmark: { _ in
                bookmarks += 1
                return Data()
            }, resolveBookmark: { _ in
                resolves += 1
                return (url, false)
            })
            assertFailure(access.load(url), .invalid)
            access.release()
            XCTAssertEqual(reads.withLock { $0 }, 0)
            XCTAssertEqual(resolves, 0)
            XCTAssertEqual(bookmarks, 0)
            XCTAssertEqual(starts, 0)
            XCTAssertEqual(stops, 0)
            XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey) as? [String: Data], saved)
        }
    }

    @MainActor
    func testNonFileLoadReleasesPriorLeaseExactlyOnce() throws {
        let url = try makePDF()
        let settings = defaults()
        let saved = [url.standardizedFileURL.path: Data("owned-fixture".utf8)]
        settings.set(saved, forKey: PDFDocumentAccess.bookmarkKey)
        let reads = Mutex(0)
        var starts = 0
        var stopped: [URL] = []
        let access = PDFDocumentAccess(defaults: settings, readData: { selected in
            reads.withLock { $0 += 1 }
            guard selected.isFileURL else { throw CocoaError(.fileReadNoSuchFile) }
            return try Data(contentsOf: selected)
        }, startAccess: { _ in starts += 1; return true }, stopAccess: { stopped.append($0) }, resolveBookmark: { _ in (url, false) })
        XCTAssertNotNil(try? access.load(url).get())
        XCTAssertEqual(starts, 1)
        assertFailure(access.load(URL(string: "https://example.invalid/owned.pdf")!), .invalid)
        access.release()
        access.release()
        XCTAssertEqual(reads.withLock { $0 }, 1)
        XCTAssertEqual(stopped, [url])
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey) as? [String: Data], saved)
    }

    @MainActor
    func testNonFileSelectionClearsPriorPDFAndDisablesDocumentActions() async throws {
        let local = try makePDF()
        let bytes = try Data(contentsOf: local)
        let reads = Mutex(0)
        let access = PDFDocumentAccess(defaults: defaults(), readData: { _ in
            reads.withLock { $0 += 1 }
            return bytes
        }, makeBookmark: { _ in Data("owned-fixture".utf8) })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: local), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertNotNil(controller.loadedPDF)
        XCTAssertTrue(controller.canAccessDocument)
        let remote = GeneratedFile(role: "question_paper", url: URL(string: "https://example.invalid/owned.pdf")!)
        controller.update(file: remote, provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.selectedFile, remote)
        XCTAssertEqual(controller.loadFailure, .invalid)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.hasFormFields)
        XCTAssertFalse(controller.canAccessDocument)
        controller.refresh()
        await controller.waitForPendingLoad()
        XCTAssertEqual(reads.withLock { $0 }, 1)
        XCTAssertEqual(controller.loadFailure, .invalid)
        controller.clear()
    }

    @MainActor
    func testFirstSuccessfulReadsRememberBothPDFsAfterFolderChangeAndNewController() async throws {
        let files = [
            GeneratedFile(role: "question_paper", url: try makePDF(name: "subject.pdf", pages: 2)),
            GeneratedFile(role: "mark_scheme", url: try makePDF(name: "correction.pdf", pages: 3)),
        ]
        let settings = defaults()
        let folderGrant = Mutex(true)
        let granted = Mutex(Set<URL>())
        var starts = 0
        var stops = 0
        func service() -> PDFDocumentAccess {
            PDFDocumentAccess(defaults: settings, readData: { url in
                guard folderGrant.withLock({ $0 }) || granted.withLock({ $0.contains(url) }) else { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            }, startAccess: { url in starts += 1; _ = granted.withLock { $0.insert(url) }; return true }, stopAccess: { url in
                stops += 1; _ = granted.withLock { $0.remove(url) }
            }, makeBookmark: { Data($0.path.utf8) }, resolveBookmark: { data in
                (URL(fileURLWithPath: String(decoding: data, as: UTF8.self)), false)
            })
        }
        let initial = service()
        for file in files { XCTAssertNotNil(try? initial.load(file.url).get()) }
        initial.release()
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey)?.count, 2)
        XCTAssertEqual(starts, 0)
        XCTAssertEqual(stops, 0)

        folderGrant.withLock { $0 = false }
        settings.set(Data("different-folder".utf8), forKey: AppStorageKey.outputFolderBookmark)
        let restarted = DocumentActionController(access: service())
        for (index, file) in files.enumerated() {
            restarted.update(file: file, provenance: nil)
            await restarted.waitForPendingLoad()
            XCTAssertEqual(restarted.loadedPDF?.document.pageCount, index + 2)
            XCTAssertTrue(restarted.canAccessDocument)
        }
        restarted.clear()
        XCTAssertEqual(starts, 2)
        XCTAssertEqual(stops, 2)
        XCTAssertTrue(granted.withLock { $0.isEmpty })
        XCTAssertEqual(settings.data(forKey: AppStorageKey.outputFolderBookmark), Data("different-folder".utf8))
    }

    @MainActor
    func testFirstReadBookmarkFailurePreservesReadablePDFAndPriorBookmarks() throws {
        let url = try makePDF()
        let bytes = try Data(contentsOf: url)
        let settings = defaults()
        let prior = ["/older.pdf": Data("retained".utf8)]
        settings.set(prior, forKey: PDFDocumentAccess.bookmarkKey)
        let access = PDFDocumentAccess(defaults: settings, makeBookmark: { _ in throw CocoaError(.fileWriteNoPermission) })
        XCTAssertEqual(try access.load(url).get().bytes, bytes)
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey) as? [String: Data], prior)
        XCTAssertEqual(try Data(contentsOf: url), bytes)
    }

    @MainActor
    func testRememberingOtherValidPDFsDoesNotStealTheReadersLeaseOrPersistInvalidInputs() throws {
        let selected = try makePDF(name: "selected.pdf")
        let another = try makePDF(name: "another.pdf")
        let invalid = root.appendingPathComponent("invalid.pdf")
        try Data("invalid".utf8).write(to: invalid)
        let settings = defaults()
        settings.set([selected.standardizedFileURL.path: Data(selected.path.utf8)], forKey: PDFDocumentAccess.bookmarkKey)
        var starts = 0
        var stops = 0
        let access = PDFDocumentAccess(defaults: settings, startAccess: { _ in starts += 1; return true },
            stopAccess: { _ in stops += 1 }, makeBookmark: { Data($0.path.utf8) },
            resolveBookmark: { _ in (selected, false) })
        XCTAssertNotNil(try? access.load(selected).get())
        XCTAssertNoThrow(try access.rememberReadablePDF(another).get())
        if case .success = access.rememberReadablePDF(invalid) { XCTFail("Invalid PDF must not be remembered") }
        if case .success = access.rememberReadablePDF(root.appendingPathComponent("missing.pdf")) { XCTFail("Missing PDF must not be remembered") }
        XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey)?.count, 2)
        XCTAssertNotNil(try? access.load(selected).get())
        XCTAssertEqual(starts, 1)
        XCTAssertEqual(stops, 0)
        access.release()
        XCTAssertEqual(stops, 1)
        let deniedSettings = defaults()
        let denied = PDFDocumentAccess(defaults: deniedSettings, readData: { _ in throw CocoaError(.fileReadNoPermission) },
            makeBookmark: { _ in XCTFail("Unreadable PDF must not be bookmarked"); return Data() })
        if case .success = denied.rememberReadablePDF(another) { XCTFail("Denied PDF must not be remembered") }
        XCTAssertNil(deniedSettings.dictionary(forKey: PDFDocumentAccess.bookmarkKey))
    }

    @MainActor
    func testPublicationRemembersEveryPDFBeforeFolderAccessEndsAndFailureIsNonfatal() async throws {
        let subject = try makePDF(name: "subject.pdf", pages: 2)
        let correction = try makePDF(name: "correction.pdf", pages: 3)
        let privateJSON = root.appendingPathComponent("assessment.json")
        try Data("private diagnostic".utf8).write(to: privateJSON)
        let bytes = try [Data(contentsOf: subject), Data(contentsOf: correction)]
        for failBookmark in [false, true] {
            let settings = defaults()
            settings.set("en", forKey: "interfaceLanguage")
            let prior = ["/older.pdf": Data("prior".utf8)]
            settings.set(prior, forKey: PDFDocumentAccess.bookmarkKey)
            let folderGrant = Mutex(true)
            let fileGrants = Mutex(Set<URL>())
            var starts = 0
            var stops = 0
            var remembered: [URL] = []
            func service() -> PDFDocumentAccess {
                PDFDocumentAccess(defaults: settings, readData: { url in
                    guard folderGrant.withLock({ $0 }) || fileGrants.withLock({ $0.contains(url) }) else { throw CocoaError(.fileReadNoPermission) }
                    return try Data(contentsOf: url)
                }, startAccess: { url in starts += 1; _ = fileGrants.withLock { $0.insert(url) }; return true }, stopAccess: { url in
                    stops += 1; _ = fileGrants.withLock { $0.remove(url) }
                }, makeBookmark: { url in
                    XCTAssertTrue(folderGrant.withLock { $0 })
                    remembered.append(url)
                    if failBookmark { throw CocoaError(.fileWriteNoPermission) }
                    return Data(url.path.utf8)
                }, resolveBookmark: { data in
                    (URL(fileURLWithPath: String(decoding: data, as: UTF8.self)), false)
                })
            }
            let application = ApplicationCoordinator(defaults: settings, secrets: PDFBookmarkTestSecrets(),
                historyDirectory: root.appendingPathComponent(UUID().uuidString), backend: ControlledRunBackend(),
                pdfDocumentAccess: service())
            application.beginDocumentCollection()
            for (role, url) in [("question_paper", subject), ("mark_scheme", correction), ("teacher_review", privateJSON)] {
                application.apply(.file(role: role, path: url.path))
            }
            try application.publishUKGeneratedFiles(from: root, to: root.appendingPathComponent(UUID().uuidString))
            let published = application.currentGenerationFiles.filter { $0.url.pathExtension == "pdf" }
            XCTAssertEqual(Set(remembered), Set(published.map(\.url)))
            XCTAssertEqual(published.count, 2)
            XCTAssertEqual(starts, 0)
            XCTAssertEqual(stops, 0)
            XCTAssertFalse(application.showError)
            for (index, role) in ["question_paper", "mark_scheme"].enumerated() {
                let file = try XCTUnwrap(published.first { $0.role == role })
                XCTAssertEqual(try Data(contentsOf: file.url), bytes[index])
            }
            XCTAssertEqual(try Data(contentsOf: privateJSON), Data("private diagnostic".utf8))
            XCTAssertEqual(application.currentGenerationFiles.first { $0.role == "teacher_review" }?.url, privateJSON)
            folderGrant.withLock { $0 = false }
            application.outputFolder = root.appendingPathComponent("another-folder")
            if failBookmark {
                XCTAssertEqual(settings.dictionary(forKey: PDFDocumentAccess.bookmarkKey) as? [String: Data], prior)
                XCTAssertEqual(application.progressEntries.last?.stage, "document_access")
                XCTAssertEqual(application.progressEntries.last?.message, "The PDFs were saved, but access couldn't be remembered for some files. If a PDF becomes unavailable, choose it again in Documents.")
            } else {
                let restarted = DocumentActionController(access: service())
                for file in published {
                    restarted.update(file: file, provenance: nil)
                    await restarted.waitForPendingLoad()
                    XCTAssertTrue(restarted.canAccessDocument)
                }
                restarted.clear()
                XCTAssertEqual(starts, 2)
                XCTAssertEqual(stops, 2)
            }
        }
    }

    @MainActor
    func testPickerSelectionUpdatesTheActionDocumentBeforeDeferredViewChanges() async throws {
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
        await controller.waitForPendingLoad()
        var selectedID: GeneratedFile.ID? = scheme.id
        let binding = controller.selectionBinding(
            selection: Binding(get: { selectedID }, set: { selectedID = $0 }),
            files: [scheme, subject], records: records
        )

        binding.wrappedValue = subject.id

        await controller.waitForPendingLoad()
        // The binding publishes the target before SwiftUI's deferred onChange;
        // asynchronous loading must finish before its actions become available.
        controller.refresh()
        await controller.waitForPendingLoad()

        XCTAssertEqual(selectedID, subject.id)
        XCTAssertEqual(controller.selectedFile?.id, subject.id)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 36)
        XCTAssertEqual(controller.provenance?.id, records[1].id)
        XCTAssertTrue(controller.canAccessDocument)
        binding.wrappedValue = scheme.id
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 24)
        XCTAssertEqual(controller.provenance?.id, records[0].id)
    }

    @MainActor
    func testPickerSelectionCannotActOnThePriorPDFWhenTheNewFileIsUnreadable() async throws {
        let readable = GeneratedFile(role: "mark_scheme", url: try makePDF())
        let unreadable = GeneratedFile(role: "question_paper", url: root.appendingPathComponent("missing.pdf"))
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: readable, provenance: nil)
        await controller.waitForPendingLoad()
        var selectedID: GeneratedFile.ID? = readable.id
        let binding = controller.selectionBinding(
            selection: Binding(get: { selectedID }, set: { selectedID = $0 }),
            files: [readable, unreadable], records: []
        )

        binding.wrappedValue = unreadable.id

        await controller.waitForPendingLoad()

        XCTAssertEqual(controller.selectedFile?.id, unreadable.id)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
    }

    @MainActor
    func testExistingButDeniedPDFHasAnHonestFailureAndDisabledActions() async throws {
        let url = try makePDF()
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults(), readData: { _ in throw CocoaError(.fileReadNoPermission) }))
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        await controller.waitForPendingLoad()
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
    func testSelectionAndLaterReadFailureNeverLeaveThePreviousPDFReady() async throws {
        let first = try makePDF()
        let second = try makePDF(name: "second.pdf")
        let denied = Mutex(false)
        let access = PDFDocumentAccess(defaults: defaults(), readData: { url in
            if denied.withLock({ $0 }) { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: url)
        })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: first), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 1)
        denied.withLock { $0 = true }
        controller.update(file: GeneratedFile(role: "mark_scheme", url: second), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
        denied.withLock { $0 = false }
        controller.refresh()
        await controller.waitForPendingLoad()
        XCTAssertTrue(controller.canAccessDocument)
        denied.withLock { $0 = true }
        controller.refresh()
        await controller.waitForPendingLoad()
        XCTAssertFalse(controller.canAccessDocument)
        controller.update(file: nil, provenance: nil)
        await controller.waitForPendingLoad()
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
        let active = Mutex(false)
        var starts = 0
        var stops = 0
        func service() -> PDFDocumentAccess {
            PDFDocumentAccess(defaults: settings, readData: { url in
                guard active.withLock({ $0 }) else { throw CocoaError(.fileReadNoPermission) }
                return try Data(contentsOf: url)
            }, startAccess: { _ in starts += 1; active.withLock { $0 = true }; return true }, stopAccess: { _ in stops += 1; active.withLock { $0 = false } }, makeBookmark: { _ in marker }, resolveBookmark: { data in
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
    func testActionsRecheckReadabilityBeforeOpeningPanelsOrPrinting() async throws {
        let url = try makePDF()
        let denied = Mutex(false)
        let access = PDFDocumentAccess(defaults: defaults(), readData: { source in
            if denied.withLock({ $0 }) { throw CocoaError(.fileReadNoPermission) }
            return try Data(contentsOf: source)
        })
        let controller = DocumentActionController(access: access)
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        await controller.waitForPendingLoad()
        denied.withLock { $0 = true }
        controller.printSelected()
        await controller.waitForPendingLoad()
        XCTAssertFalse(controller.canAccessDocument)
        XCTAssertEqual(controller.loadFailure, .permissionDenied)
        XCTAssertNotNil(controller.exportError)
        controller.exportError = nil
        controller.exportSelected()
        await controller.waitForPendingLoad()
        XCTAssertNotNil(controller.exportError)
        XCTAssertNil(controller.loadedPDF)
    }

    @MainActor
    func testPreviewWidgetsAreReadOnlyWithoutChangingValuesLinksOrExportBytes() async throws {
        let url = root.appendingPathComponent("fillable.pdf")
        let document = PDFDocument()
        let page = PDFPage()
        let widget = PDFAnnotation(bounds: CGRect(x: 20, y: 20, width: 160, height: 40), forType: .widget, withProperties: nil)
        widget.widgetFieldType = .text
        widget.fieldName = "answer"
        widget.widgetStringValue = "An existing answer"
        page.addAnnotation(widget)
        let link = PDFAnnotation(bounds: CGRect(x: 20, y: 100, width: 160, height: 30), forType: .link, withProperties: nil)
        link.url = URL(string: "https://example.invalid/owned-fixture")
        page.addAnnotation(link)
        document.insert(page, at: 0)
        XCTAssertTrue(document.write(to: url))
        let originalBytes = try Data(contentsOf: url)
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: GeneratedFile(role: "electronic_answer_document", url: url), provenance: nil)
        await controller.waitForPendingLoad()

        let loaded = try XCTUnwrap(controller.loadedPDF)
        let annotations = try XCTUnwrap(loaded.document.page(at: 0)).annotations
        let previewWidget = try XCTUnwrap(annotations.first { $0.type == "Widget" })
        let previewLink = try XCTUnwrap(annotations.first { $0.type == "Link" })
        XCTAssertTrue(controller.hasFormFields)
        XCTAssertTrue(previewWidget.isReadOnly)
        XCTAssertEqual(previewWidget.widgetStringValue, "An existing answer")
        XCTAssertEqual(previewLink.url, link.url)
        XCTAssertFalse(previewLink.isReadOnly)
        XCTAssertEqual(loaded.bytes, originalBytes)
        controller.refresh()
        await controller.waitForPendingLoad()
        XCTAssertTrue(controller.loadedPDF?.document === loaded.document)
        XCTAssertTrue(controller.hasFormFields)
        let exported = root.appendingPathComponent("exported.pdf")
        try loaded.bytes.write(to: exported, options: .atomic)
        XCTAssertEqual(try Data(contentsOf: exported), originalBytes)
        let exportedWidget = try XCTUnwrap(PDFDocument(url: exported)?.page(at: 0)?.annotations.first { $0.type == "Widget" })
        XCTAssertFalse(exportedWidget.isReadOnly)
        XCTAssertEqual(exportedWidget.widgetStringValue, "An existing answer")
        XCTAssertEqual(try Data(contentsOf: url), originalBytes)

        controller.clear()
        XCTAssertFalse(controller.hasFormFields)
        XCTAssertNil(controller.loadedPDF)
        controller.update(file: GeneratedFile(role: "question_paper", url: try makePDF(name: "plain.pdf")), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertFalse(controller.hasFormFields)
        controller.update(file: GeneratedFile(role: "question_paper", url: root.appendingPathComponent("missing.pdf")), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertFalse(controller.hasFormFields)
    }

    @MainActor
    func testReadOnlyPreviewHintIsAvailableInEnglishAndFrench() {
        let loading: LocalizedStringResource = "Loading PDF…"
        XCTAssertEqual(InterfaceText.resolve(loading, language: "en"), "Loading PDF…")
        XCTAssertEqual(InterfaceText.resolve(loading, language: "fr"), "Chargement du PDF…")
        let key: LocalizedStringResource = "This preview is read-only. Export the PDF to fill it in another app."
        XCTAssertEqual(InterfaceText.resolve(key, language: "en"), "This preview is read-only. Export the PDF to fill it in another app.")
        XCTAssertEqual(InterfaceText.resolve(key, language: "fr"), "Cet aperçu est en lecture seule. Exportez le PDF pour le remplir dans une autre app.")
    }

    @MainActor
    func testUnchangedRefreshPreservesTheReaderDocumentButNewBytesReplaceIt() async throws {
        let url = try makePDF()
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults()))
        controller.update(file: GeneratedFile(role: "question_paper", url: url), provenance: nil)
        await controller.waitForPendingLoad()
        let original = try XCTUnwrap(controller.loadedPDF?.document)

        controller.refresh()

        await controller.waitForPendingLoad()
        XCTAssertTrue(controller.loadedPDF?.document === original)

        let changed = PDFDocument()
        changed.insert(PDFPage(), at: 0)
        changed.insert(PDFPage(), at: 1)
        XCTAssertTrue(changed.write(to: url))
        controller.refresh()
        await controller.waitForPendingLoad()
        XCTAssertFalse(controller.loadedPDF?.document === original)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 2)

        try Data("now invalid".utf8).write(to: url)
        controller.refresh()
        await controller.waitForPendingLoad()
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
        XCTAssertEqual(InterfaceText.resolve(
            "The PDFs were saved, but access couldn't be remembered for some files. If a PDF becomes unavailable, choose it again in Documents.", language: "fr"
        ), "Les PDF ont été enregistrés, mais l’accès à certains fichiers n’a pas pu être mémorisé. Si un PDF devient indisponible, sélectionnez-le à nouveau dans Documents.")
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

    private func defaults() -> UserDefaults { isolatedDefaults() }

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

private final class BoundedPDFReadProbe: Sendable {
    struct Sample: Sendable {
        var readerOnMainThread = false
        var readStarted: UInt64 = 0
        var heartbeatRequested: UInt64 = 0
        var heartbeatRan: UInt64 = 0
        var readFinished: UInt64 = 0
    }

    let state = Mutex(Sample())
}

private final class GatedPDFReader: Sendable {
    let calls = Mutex([URL]())
    let gate = DispatchSemaphore(value: 0)
    let started: XCTestExpectation
    let blockedCalls: Set<Int>
    let response: @Sendable (URL, Int) throws -> Data

    init(started: XCTestExpectation, blockedCalls: Set<Int>, response: @escaping @Sendable (URL, Int) throws -> Data) {
        self.started = started
        self.blockedCalls = blockedCalls
        self.response = response
    }

    func read(_ url: URL) throws -> Data {
        let call = calls.withLock { $0.append(url); return $0.count }
        if blockedCalls.contains(call) {
            started.fulfill()
            // Simulate bounded I/O waiting for its device, never block MainActor.
            guard gate.wait(timeout: .now() + 5) == .success else { throw CocoaError(.fileReadUnknown) }
        }
        return try response(url, call)
    }
}

private final class PDFBookmarkTestSecrets: SecretStoring {
    func read(_ account: String) -> String { "" }
    func save(_ value: String, account: String) {}
}
