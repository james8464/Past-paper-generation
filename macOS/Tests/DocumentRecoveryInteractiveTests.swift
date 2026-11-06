import AppKit
import Combine
import PDFKit
import SwiftUI
import XCTest
@testable import Keldin

final class DocumentRecoveryInteractiveTests: XCTestCase {
    @MainActor
    func testUserCancelsRejectsWrongPDFAndReopensExactOwnedFile() async throws {
        guard ProcessInfo.processInfo.environment["KELDIN_INTERACTIVE_PDF_RECOVERY_CHECK"] == "1" else {
            throw XCTSkip("Opt-in real PDF picker check with isolated owned files and bookmarks.")
        }
        let hostDomain = try XCTUnwrap(Bundle.main.bundleIdentifier)
        let domains = Set(["com.jamesdurup.Keldin", hostDomain])
        let standardBefore = Dictionary(uniqueKeysWithValues: domains.map {
            ($0, NSDictionary(dictionary: UserDefaults.standard.persistentDomain(forName: $0) ?? [:]))
        })
        let panelFolderKey = "NSOSPLastRootDirectory"
        let panelFolderBefore = standardBefore[hostDomain]?[panelFolderKey]
        let suite = "Keldin.DocumentRecovery.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(suite)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let expected = folder.appendingPathComponent("expected.pdf")
        let other = folder.appendingPathComponent("other.pdf")
        let original = try ownedPDF(label: "Owned expected document")
        let otherBytes = try ownedPDF(label: "Wrong owned document")
        try otherBytes.write(to: other)
        let sentinel = folder.appendingPathComponent("sentinel.txt")
        let sentinelBytes = Data("Owned recovery sentinel\n".utf8)
        try sentinelBytes.write(to: sentinel)
        let outputGrant = Data("preserved-owned-output-grant".utf8)
        defaults.set(outputGrant, forKey: AppStorageKey.outputFolderBookmark)
        let controller = DocumentActionController(access: PDFDocumentAccess(defaults: defaults))
        let window = NSWindow(contentRect: NSRect(x: 100, y: 100, width: 900, height: 700),
            styleMask: [.titled, .closable, .resizable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        defer {
            controller.clear()
            window.contentView = nil
            window.close()
            let panelFolderNow = UserDefaults.standard.persistentDomain(forName: hostDomain)?[panelFolderKey]
            let previous = NSDictionary(dictionary: panelFolderBefore.map { [panelFolderKey: $0] } ?? [:])
            let current = NSDictionary(dictionary: panelFolderNow.map { [panelFolderKey: $0] } ?? [:])
            if previous != current {
                let otherKeysUnchanged = standardBefore.allSatisfy { domain, original in
                    guard let before = original.mutableCopy() as? NSMutableDictionary else { return false }
                    let after = NSMutableDictionary(dictionary: UserDefaults.standard.persistentDomain(forName: domain) ?? [:])
                    before.removeObject(forKey: panelFolderKey)
                    after.removeObject(forKey: panelFolderKey)
                    return before == after
                }
                var stale = false
                if otherKeysUnchanged, let bookmark = panelFolderNow as? Data,
                   let restored = try? URL(resolvingBookmarkData: bookmark,
                    options: [.withoutUI, .withoutMounting], relativeTo: nil, bookmarkDataIsStale: &stale),
                   restored.resolvingSymlinksInPath().standardizedFileURL == folder.resolvingSymlinksInPath().standardizedFileURL {
                    if let panelFolderBefore { UserDefaults.standard.set(panelFolderBefore, forKey: panelFolderKey) }
                    else { UserDefaults.standard.removeObject(forKey: panelFolderKey) }
                    UserDefaults.standard.synchronize()
                } else { XCTFail("Refused cleanup of unrelated or unresolvable picker preference state.") }
            }
            defaults.removePersistentDomain(forName: suite)
            try? FileManager.default.removeItem(at: folder)
            for (domain, original) in standardBefore {
                XCTAssertEqual(original, NSDictionary(dictionary:
                    UserDefaults.standard.persistentDomain(forName: domain) ?? [:]))
            }
        }
        controller.update(file: GeneratedFile(role: "question_paper", url: expected), provenance: nil)
        await controller.waitForPendingLoad()
        XCTAssertEqual(controller.loadFailure, .missing)
        XCTAssertFalse(controller.canAccessDocument)
        let finished = expectation(description: "Real owned PDF picker recovery completed")
        let controls = DocumentRecoveryControls(controller: controller, defaults: defaults,
            expected: expected, original: original, finish: { finished.fulfill() })
        window.title = "Keldin owned PDF recovery check"
        window.contentView = NSHostingView(rootView: DocumentRecoveryFixture(controller: controller, controls: controls))
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        print("KELDIN_INTERACTIVE_PDF_RECOVERY_READY: owned fixture only; use Choose This PDF…, real Open/Cancel/OK, then labelled checks. Go to Folder inside the Open panel is allowed; no app menus or app-global shortcuts.")
        print("OWNED_PDF_RECOVERY_FOLDER: \(folder.path)")
        await fulfillment(of: [finished], timeout: 240)
        XCTAssertEqual(controls.phase, 4)
        XCTAssertEqual(try Data(contentsOf: expected), original)
        XCTAssertEqual(try Data(contentsOf: other), otherBytes)
        XCTAssertEqual(try Data(contentsOf: sentinel), sentinelBytes)
        XCTAssertEqual(defaults.data(forKey: AppStorageKey.outputFolderBookmark), outputGrant)
    }

    @MainActor
    private func ownedPDF(label: String) throws -> Data {
        let image = NSImage(size: NSSize(width: 595, height: 842), flipped: false) { rectangle in
            NSColor.white.setFill()
            rectangle.fill()
            (label as NSString).draw(at: NSPoint(x: 50, y: 740), withAttributes: [
                .font: NSFont.systemFont(ofSize: 24), .foregroundColor: NSColor.black,
            ])
            return true
        }
        let document = PDFDocument()
        document.insert(try XCTUnwrap(PDFPage(image: image)), at: 0)
        return try XCTUnwrap(document.dataRepresentation())
    }
}

@MainActor
private final class DocumentRecoveryControls: ObservableObject {
    @Published private(set) var phase = 0
    private(set) var sawWrongFile = false
    private var pickerCount = 0
    private let controller: DocumentActionController
    private let defaults: UserDefaults
    private let expected: URL
    private let original: Data
    private let finish: () -> Void

    init(controller: DocumentActionController, defaults: UserDefaults, expected: URL,
         original: Data, finish: @escaping () -> Void) {
        self.controller = controller
        self.defaults = defaults
        self.expected = expected
        self.original = original
        self.finish = finish
    }

    func observedError(_ error: String?) {
        let expected = InterfaceText.resolve(PDFLoadFailure.wrongFile.messageResource,
            language: UserDefaults.standard.string(forKey: "interfaceLanguage") ?? "system")
        if phase == 1, error == expected { sawWrongFile = true }
    }

    func choose() { pickerCount += 1; controller.choosePDFForAccess() }

    func checkCancel() {
        guard phase == 0 else { return }
        XCTAssertEqual(pickerCount, 1)
        XCTAssertEqual(controller.loadFailure, .missing)
        XCTAssertNil(controller.exportError)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertFalse(controller.canAccessDocument)
        XCTAssertNil(defaults.dictionary(forKey: PDFDocumentAccess.bookmarkKey))
        phase = 1
        print("PDF_RECOVERY_CANCEL_CHECKED: choose other.pdf, inspect refusal, press real OK, then Check wrong selection.")
    }

    func checkWrongFile() {
        guard phase == 1, sawWrongFile, controller.exportError == nil else {
            return XCTFail("Select other.pdf through the real picker and dismiss its refusal first.")
        }
        XCTAssertEqual(controller.loadFailure, .missing)
        XCTAssertNil(controller.loadedPDF)
        XCTAssertEqual(pickerCount, 2)
        XCTAssertFalse(controller.canAccessDocument)
        XCTAssertNil(defaults.dictionary(forKey: PDFDocumentAccess.bookmarkKey))
        XCTAssertFalse(FileManager.default.fileExists(atPath: expected.path))
        phase = 2
    }

    func restoreOwnedFile() {
        guard phase == 2 else { return }
        do { try original.write(to: expected, options: .atomic) }
        catch { return XCTFail("Owned fixture restore failed: \(error)") }
        phase = 3
        print("PDF_RECOVERY_RESTORED: choose exact expected.pdf through the real picker, inspect its preview, then Finish recovery check.")
    }

    func complete() {
        guard phase == 3, !controller.isLoading, controller.canAccessDocument else {
            return XCTFail("Open the exact restored expected.pdf through the real picker first.")
        }
        XCTAssertNil(controller.exportError)
        XCTAssertNil(controller.loadFailure)
        XCTAssertEqual(pickerCount, 3)
        XCTAssertEqual(controller.loadedPDF?.bytes, original)
        XCTAssertEqual(controller.loadedPDF?.document.pageCount, 1)
        let bookmarks = defaults.dictionary(forKey: PDFDocumentAccess.bookmarkKey)
        XCTAssertEqual(bookmarks?.count, 1)
        XCTAssertNotNil(bookmarks?[expected.standardizedFileURL.path] as? Data)
        phase = 4
        finish()
    }
}

@MainActor
private struct DocumentRecoveryFixture: View {
    @ObservedObject var controller: DocumentActionController
    @ObservedObject var controls: DocumentRecoveryControls
    var body: some View {
        VStack(spacing: 12) {
            if let pdf = controller.loadedPDF {
                OwnedRecoveryPDFView(document: pdf.document)
            } else {
                Text("PDF unavailable").font(.title)
                if let failure = controller.loadFailure { Text(failure.messageResource) }
                Spacer()
            }
            Button("Choose This PDF…", action: controls.choose)
                .disabled(controller.isLoading)
            HStack {
                Button("Check Cancel", action: controls.checkCancel).disabled(controls.phase != 0)
                Button("Check wrong selection", action: controls.checkWrongFile).disabled(controls.phase != 1)
                Button("Restore owned PDF", action: controls.restoreOwnedFile).disabled(controls.phase != 2)
                Button("Finish recovery check", action: controls.complete).disabled(controls.phase != 3)
            }
        }
        .padding()
        .onChange(of: controller.exportError) { _, error in controls.observedError(error) }
        .alert("Couldn't complete the PDF action", isPresented: Binding(
            get: { controller.exportError != nil },
            set: { if !$0 { controller.exportError = nil } }
        )) { Button("OK", role: .cancel) {} } message: { Text(controller.exportError ?? "") }
    }
}

private struct OwnedRecoveryPDFView: NSViewRepresentable {
    let document: PDFDocument
    func makeNSView(context: Context) -> PDFView {
        let view = PDFView()
        view.autoScales = true
        view.document = document
        return view
    }
    func updateNSView(_ view: PDFView, context: Context) {
        if view.document !== document { view.document = document }
    }
}
