// Preview generated PDFs and handle their export and printing actions.

import AppKit
import Combine
import PDFKit
@preconcurrency import Quartz
import SwiftUI
import UniformTypeIdentifiers

struct DocumentPreviewView: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    let files: [GeneratedFile]
    let selectedID: GeneratedFile.ID?
    @State private var selection: GeneratedFile.ID?
    @StateObject private var documentActions = DocumentActionController()

    init(files: [GeneratedFile], selectedID: GeneratedFile.ID? = nil) {
        self.files = files.filter { $0.url.pathExtension.lowercased() == "pdf" }
        self.selectedID = selectedID
        _selection = State(initialValue: selectedID ?? self.files.first?.id)
    }

    var body: some View {
        Group {
            if files.isEmpty {
                ContentUnavailableView {
                    Label("No PDFs to preview", systemImage: "doc.richtext")
                } description: {
                    Text("Create a paper or choose an existing PDF from History.")
                }
            } else {
                VStack(spacing: 0) {
                    DocumentPickerView(files: files, selection: selectedBinding)
                    .padding()
                    .frame(minWidth: 0, maxWidth: .infinity)

                    Divider()

                    if let file = selectedFile, let pdf = documentActions.loadedPDF {
                        PDFDocumentView(document: pdf.document)
                            .id(file.id)
                            .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
                            .accessibilityLabel("Preview of \(file.title)")
                    } else {
                        ContentUnavailableView {
                            Label("PDF unavailable", systemImage: "doc.badge.ellipsis")
                        } description: {
                            if let failure = documentActions.loadFailure { Text(failure.messageResource) }
                        } actions: {
                            Button("Choose This PDF…", action: documentActions.choosePDFForAccess)
                                .disabled(selectedFile == nil)
                            Button("Try Again", action: documentActions.refresh)
                        }
                    }
                }
                .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
            }
        }
        .navigationTitle("Documents")
        .focusedSceneObject(documentActions)
        .onChange(of: selectedFile, initial: true) {
            documentActions.update(file: selectedFile, provenance: provenanceRecord)
        }
        .onChange(of: provenanceRecord) {
            documentActions.update(file: selectedFile, provenance: provenanceRecord)
        }
        .onChange(of: selectedID) {
            selection = selectedID
        }
        .onAppear { documentActions.update(file: selectedFile, provenance: provenanceRecord) }
        .onDisappear { documentActions.clear() }
        .toolbar {
            ToolbarItemGroup {
                Button("Quick Look", systemImage: "eye", action: documentActions.quickLookSelected)
                    .disabled(!documentActions.canAccessDocument)

                Button("Print…", systemImage: "printer", action: documentActions.printSelected)
                    .disabled(!documentActions.canAccessDocument)

                Button("Export…", systemImage: "square.and.arrow.up", action: documentActions.exportSelected)
                    .disabled(!documentActions.canAccessDocument)

                Button("Copy Provenance", systemImage: "doc.on.clipboard", action: documentActions.copyProvenance)
                    .disabled(documentActions.provenance == nil)

                Button("Reveal in Finder", systemImage: "folder", action: documentActions.revealSelected)
                    .disabled(!documentActions.canAccessDocument)
            }
        }
        .alert("Couldn't complete the PDF action", isPresented: exportAlertBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(documentActions.exportError ?? "Try another destination.")
        }
    }

    private var selectedBinding: Binding<GeneratedFile.ID> {
        documentActions.selectionBinding(selection: $selection, files: files, records: application.recentDocumentStore.records)
    }

    private var selectedFile: GeneratedFile? {
        files.first { $0.id == selection } ?? files.first
    }

    private var provenanceRecord: GenerationJobRecord? {
        guard let file = selectedFile else { return nil }
        return PDFDocumentActions.provenanceRecord(for: file, records: application.recentDocumentStore.records)
    }

    private var exportAlertBinding: Binding<Bool> {
        Binding(
            get: { documentActions.exportError != nil },
            set: { if !$0 { documentActions.exportError = nil } }
        )
    }
}

@MainActor
final class DocumentActionController: ObservableObject {
    @Published private(set) var selectedFile: GeneratedFile?
    @Published private(set) var provenance: GenerationJobRecord?
    @Published var exportError: String?
    @Published private(set) var loadedPDF: LoadedPDF?
    @Published private(set) var loadFailure: PDFLoadFailure?
    private let access: PDFDocumentAccess
    private let quickLook = QuickLookCoordinator()

    var canAccessDocument: Bool { loadedPDF != nil && selectedFile?.exists == true }

    init(access: PDFDocumentAccess = PDFDocumentAccess()) { self.access = access }

    func selectionBinding(selection: Binding<GeneratedFile.ID?>, files: [GeneratedFile], records: [GenerationJobRecord]) -> Binding<GeneratedFile.ID> {
        Binding(
            get: { files.first(where: { $0.id == selection.wrappedValue })?.id ?? files[0].id },
            set: { id in
                let file = files.first(where: { $0.id == id })
                let provenance = file.flatMap { PDFDocumentActions.provenanceRecord(for: $0, records: records) }
                // File-menu shortcuts can run before SwiftUI's next onChange.
                // Publish the selection only after its action target is ready.
                self.update(file: file, provenance: provenance)
                selection.wrappedValue = id
            }
        )
    }

    func update(file: GeneratedFile?, provenance: GenerationJobRecord?) {
        if selectedFile?.url != file?.url { access.release() }
        selectedFile = file
        self.provenance = provenance
        refresh()
    }

    func clear() {
        access.release()
        selectedFile = nil
        provenance = nil
        loadedPDF = nil
        loadFailure = nil
    }

    func refresh() {
        loadFailure = nil
        guard let selectedFile else {
            loadedPDF = nil
            return
        }
        switch access.load(selectedFile.url) {
        case .success(let pdf):
            // Keep PDFView's page and zoom when validation reads the same bytes.
            if loadedPDF?.bytes != pdf.bytes { loadedPDF = pdf }
        case .failure(let failure):
            loadedPDF = nil
            loadFailure = failure
        }
    }

    func quickLookSelected() {
        guard prepareAction() else { return }
        guard canAccessDocument, let file = selectedFile else { return }
        quickLook.present(file.url)
    }

    func revealSelected() {
        guard prepareAction() else { return }
        guard canAccessDocument, let file = selectedFile else { return }
        NSWorkspace.shared.activateFileViewerSelecting([file.url])
    }

    func printSelected() {
        guard prepareAction(), let pdf = loadedPDF,
              let operation = pdf.document.printOperation(for: NSPrintInfo.shared, scalingMode: .pageScaleToFit, autoRotate: true)
        else { return }
        operation.run()
    }

    func exportSelected() {
        guard prepareAction(), let file = selectedFile, let bytes = loadedPDF?.bytes else { return }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = file.url.lastPathComponent
        panel.allowedContentTypes = [.pdf]
        guard panel.runModal() == .OK, let destination = panel.url else { return }
        do {
            if file.url.standardizedFileURL != destination.standardizedFileURL {
                try bytes.write(to: destination, options: .atomic)
            }
        } catch {
            exportError = error.localizedDescription
        }
    }

    func choosePDFForAccess() {
        guard let file = selectedFile else { return }
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.resolvesAliases = false
        panel.allowedContentTypes = [.pdf]
        panel.directoryURL = file.url.deletingLastPathComponent()
        panel.message = InterfaceText.resolve("Choose the same PDF shown in History. Other files won't replace it.", language: language)
        recoverAccess(selected: panel.runModal() == .OK ? panel.url : nil)
    }

    func recoverAccess(selected: URL?) {
        guard let file = selectedFile else { return }
        do {
            if try access.recover(expected: file.url, selected: selected) { refresh() }
        } catch {
            let failure = (error as? PDFLoadFailure) ?? .unreadable
            exportError = InterfaceText.resolve(failure.messageResource, language: language)
        }
    }

    private var language: String { UserDefaults.standard.string(forKey: "interfaceLanguage") ?? "system" }

    private func prepareAction() -> Bool {
        refresh()
        guard canAccessDocument else {
            if let loadFailure { exportError = InterfaceText.resolve(loadFailure.messageResource, language: language) }
            return false
        }
        return true
    }

    func copyProvenance() {
        guard let provenance else { return }
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(provenance.provenanceSummary, forType: .string)
    }
}

enum PDFDocumentActions {
    static func provenanceRecord(for file: GeneratedFile, records: [GenerationJobRecord]) -> GenerationJobRecord? {
        let matches = records.filter { record in
            record.artifacts.contains { $0.id == file.id }
        }
        // Old history may have copied a library artifact into several jobs.
        // A reused filename is not proof of provenance for this revision.
        return matches.count == 1 ? matches.first : nil
    }

    @MainActor
    static func printOperation(for url: URL) -> NSPrintOperation? {
        guard let document = PDFDocument(url: url) else { return nil }
        // A zero-sized PDFView cannot print the whole paper.
        return document.printOperation(
            for: NSPrintInfo.shared,
            scalingMode: .pageScaleToFit,
            autoRotate: true
        )
    }

    static func export(from source: URL, to destination: URL) throws {
        if source.standardizedFileURL == destination.standardizedFileURL { return }
        // Read before replacing anything. Atomic writing keeps an existing
        // export intact if the source is missing or writing cannot finish.
        try Data(contentsOf: source, options: .mappedIfSafe).write(to: destination, options: .atomic)
    }
}

private struct PDFDocumentView: NSViewRepresentable {
    let document: PDFDocument

    func makeNSView(context: Context) -> PDFView {
        let view = PDFView()
        view.autoScales = true
        view.displayMode = .singlePageContinuous
        view.displaysPageBreaks = true
        view.backgroundColor = .windowBackgroundColor
        return view
    }

    func updateNSView(_ view: PDFView, context: Context) {
        if view.document !== document {
            view.document = document
        }
    }
}

@MainActor
private final class QuickLookCoordinator: NSObject, ObservableObject,
    QLPreviewPanelDataSource
{
    private var url: URL?

    func present(_ url: URL) {
        self.url = url
        guard let panel = QLPreviewPanel.shared() else { return }
        panel.dataSource = self
        panel.reloadData()
        panel.makeKeyAndOrderFront(nil)
    }

    nonisolated func numberOfPreviewItems(in panel: QLPreviewPanel!) -> Int {
        MainActor.assumeIsolated { url == nil ? 0 : 1 }
    }

    nonisolated func previewPanel(
        _ panel: QLPreviewPanel!,
        previewItemAt index: Int
    ) -> QLPreviewItem! {
        MainActor.assumeIsolated { url as NSURL? }
    }
}
