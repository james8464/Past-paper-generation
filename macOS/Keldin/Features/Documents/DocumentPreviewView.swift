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

                    if documentActions.hasFormFields {
                        Text("This preview is read-only. Export the PDF to fill it in another app.")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding([.horizontal, .bottom])
                    }

                    Divider()

                    if let file = selectedFile, let pdf = documentActions.loadedPDF {
                        PDFDocumentView(document: pdf.document)
                            .id(file.id)
                            .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity)
                            .accessibilityLabel("Preview of \(file.title)")
                            .overlay(alignment: .topTrailing) {
                                if documentActions.isLoading { ProgressView("Loading PDF…").padding() }
                            }
                    } else if documentActions.isLoading {
                        ProgressView("Loading PDF…")
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
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
    @Published private(set) var hasFormFields = false
    @Published private(set) var loadFailure: PDFLoadFailure?
    @Published private(set) var isLoading = false
    private let access: PDFDocumentAccess
    private let quickLook = QuickLookCoordinator()
    private var loadTask: Task<Void, Never>?
    private var revision = UUID()
    private var selectionLease: PDFReadLease?
    enum Action: Equatable { case quickLook, reveal, print, export }
    private let presentAction: (@MainActor (Action, GeneratedFile, LoadedPDF) -> Void)?

    var canAccessDocument: Bool { !isLoading && loadedPDF != nil && selectedFile?.exists == true }

    init(access: PDFDocumentAccess, presentAction: (@MainActor (Action, GeneratedFile, LoadedPDF) -> Void)? = nil) {
        self.access = access
        self.presentAction = presentAction
    }

    convenience init() { self.init(access: PDFDocumentAccess()) }

    func selectionBinding(selection: Binding<GeneratedFile.ID?>, files: [GeneratedFile], records: [GenerationJobRecord]) -> Binding<GeneratedFile.ID> {
        Binding(
            get: { files.first(where: { $0.id == selection.wrappedValue })?.id ?? files[0].id },
            set: { id in
                let file = files.first(where: { $0.id == id })
                let provenance = file.flatMap { PDFDocumentActions.provenanceRecord(for: $0, records: records) }
                // Clear the prior target before publishing the selection.
                // Actions stay disabled until the new bytes are validated.
                self.update(file: file, provenance: provenance)
                selection.wrappedValue = id
            }
        )
    }

    func update(file: GeneratedFile?, provenance: GenerationJobRecord?) {
        self.provenance = provenance
        guard selectedFile?.id != file?.id || selectedFile?.url != file?.url else { return }
        invalidateLoad()
        selectionLease?.release()
        selectionLease = nil
        loadedPDF = nil
        hasFormFields = false
        loadFailure = nil
        selectedFile = file
        refresh()
    }

    func clear() {
        invalidateLoad()
        quickLook.closeOwnedPreview()
        selectionLease?.release()
        selectionLease = nil
        selectedFile = nil
        provenance = nil
        loadedPDF = nil
        hasFormFields = false
        loadFailure = nil
    }

    func refresh() {
        startLoad()
    }

    func quickLookSelected() {
        startLoad(action: .quickLook)
    }

    func revealSelected() {
        startLoad(action: .reveal)
    }

    func printSelected() {
        startLoad(action: .print)
    }

    func exportSelected() {
        startLoad(action: .export)
    }

    private func perform(_ action: Action, file: GeneratedFile, pdf: LoadedPDF) {
        if let presentAction { presentAction(action, file, pdf); return }
        switch action {
        case .quickLook:
            guard let lease = selectionLease?.retained() else { return }
            quickLook.present(file.url, lease: lease)
        case .reveal: NSWorkspace.shared.activateFileViewerSelecting([file.url])
        case .print:
            pdf.document.printOperation(for: NSPrintInfo.shared, scalingMode: .pageScaleToFit, autoRotate: true)?.run()
        case .export: export(file: file, bytes: pdf.bytes, revision: revision)
        }
    }

    private func export(file: GeneratedFile, bytes: Data, revision expectedRevision: UUID) {
        let panel = NSSavePanel()
        panel.nameFieldStringValue = file.url.lastPathComponent
        panel.allowedContentTypes = [.pdf]
        guard panel.runModal() == .OK, let destination = panel.url else { return }
        guard revision == expectedRevision, matches(file) else { return }
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
        let selected = panel.runModal() == .OK ? panel.url : nil
        guard matches(file) else { return }
        recoverAccess(selected: selected)
    }

    func recoverAccess(selected: URL?) {
        guard let selected, let file = selectedFile else { return }
        guard selected.isFileURL, selected.standardizedFileURL == file.url.standardizedFileURL else {
            exportError = InterfaceText.resolve(PDFLoadFailure.wrongFile.messageResource, language: language)
            return
        }
        startLoad(recovering: selected)
    }

    private var language: String { UserDefaults.standard.string(forKey: "interfaceLanguage") ?? "system" }

    func waitForPendingLoad() async { await loadTask?.value }

    private func matches(_ file: GeneratedFile) -> Bool {
        selectedFile?.id == file.id && selectedFile?.url == file.url
    }

    private func invalidateLoad() {
        revision = UUID()
        loadTask?.cancel()
        loadTask = nil
        isLoading = false
    }

    private func startLoad(action: Action? = nil, recovering: URL? = nil) {
        if action != nil && isLoading { return }
        invalidateLoad()
        guard let file = selectedFile else { return }
        let request = revision
        isLoading = true
        loadFailure = nil
        let access = access
        loadTask = Task { [weak self, access] in
            do {
                let loaded = try await access.loadAsync(file.url, recovering: recovering)
                guard !Task.isCancelled, let self, self.revision == request, self.matches(file) else {
                    loaded.lease.release()
                    return
                }
                if recovering != nil {
                    if case .failure(let failure) = access.remember(loaded) {
                        loaded.lease.release()
                        throw failure
                    }
                } else { _ = access.remember(loaded) }
                self.selectionLease?.release()
                self.selectionLease = loaded.lease
                if self.loadedPDF?.bytes != loaded.pdf.bytes {
                    self.hasFormFields = PDFDocumentActions.prepareReadOnlyPreview(loaded.pdf.document)
                    self.loadedPDF = loaded.pdf
                }
                self.isLoading = false
                self.loadTask = nil
                if let action { self.perform(action, file: file, pdf: loaded.pdf) }
            } catch {
                guard !Task.isCancelled, let self, self.revision == request, self.matches(file) else { return }
                self.isLoading = false
                self.loadTask = nil
                let failure = (error as? PDFLoadFailure) ?? .unreadable
                if recovering == nil {
                    self.selectionLease?.release()
                    self.selectionLease = nil
                    self.loadedPDF = nil
                    self.hasFormFields = false
                    self.loadFailure = failure
                }
                if action != nil || recovering != nil {
                    self.exportError = InterfaceText.resolve(failure.messageResource, language: self.language)
                }
            }
        }
    }

    deinit {
        loadTask?.cancel()
        let quickLook = quickLook
        Task { @MainActor in quickLook.closeOwnedPreview() }
    }

    func copyProvenance() {
        guard let provenance else { return }
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(provenance.provenanceSummary, forType: .string)
    }
}

enum PDFDocumentActions {
    @MainActor
    static func prepareReadOnlyPreview(_ document: PDFDocument) -> Bool {
        var hasFormFields = false
        for index in 0 ..< document.pageCount {
            for annotation in document.page(at: index)?.annotations ?? [] where annotation.type == "Widget" {
                annotation.isReadOnly = true
                hasFormFields = true
            }
        }
        return hasFormFields
    }

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
final class QuickLookLeaseOwner {
    private var lease: PDFReadLease?

    func replace(with lease: PDFReadLease?) {
        guard self.lease !== lease else { return }
        self.lease?.release()
        self.lease = lease
    }

    func clear() { replace(with: nil) }
}

@MainActor
private final class QuickLookCoordinator: NSObject, ObservableObject,
    QLPreviewPanelDataSource, QLPreviewPanelDelegate
{
    private var url: URL?
    private let leaseOwner = QuickLookLeaseOwner()
    private weak var panel: QLPreviewPanel?

    func present(_ url: URL, lease: PDFReadLease) {
        guard let panel = QLPreviewPanel.shared() else {
            lease.release()
            return
        }
        if let previous = panel.dataSource as? QuickLookCoordinator, previous !== self {
            previous.finishPreview(close: false)
        }
        if let previous = panel.delegate as? QuickLookCoordinator, previous !== self {
            previous.finishPreview(close: false)
        }
        finishPreview(close: false)
        self.panel = panel
        leaseOwner.replace(with: lease)
        self.url = url
        panel.dataSource = self
        panel.delegate = self
        panel.reloadData()
        panel.makeKeyAndOrderFront(nil)
    }

    func closeOwnedPreview() { finishPreview(close: true) }

    func windowWillClose(_ notification: Notification) { finishPreview(close: false) }

    private func finishPreview(close: Bool) {
        let panel = panel
        self.panel = nil
        leaseOwner.clear()
        url = nil
        if let panel {
            let ownsPanel = panel.dataSource === self && panel.delegate === self
            if panel.dataSource === self { panel.dataSource = nil }
            if panel.delegate === self { panel.delegate = nil }
            if close && ownsPanel { panel.close() }
        }
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
