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
    @State private var exportError: String?
    @StateObject private var quickLook = QuickLookCoordinator()

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
                    Picker("Document", selection: selectedBinding) {
                        ForEach(files) { file in
                            Text(file.title).tag(file.id)
                        }
                    }
                    .pickerStyle(.segmented)
                    .labelsHidden()
                    .padding()

                    Divider()

                    if let file = selectedFile, file.exists {
                        PDFDocumentView(url: file.url)
                            .id(file.id)
                            .accessibilityLabel("Preview of \(file.title)")
                    } else {
                        ContentUnavailableView(
                            "PDF not found",
                            systemImage: "doc.badge.ellipsis",
                            description: Text("Reveal the job in History or create the paper again.")
                        )
                    }
                }
            }
        }
        .navigationTitle("Documents")
        .onChange(of: selectedID) {
            selection = selectedID
        }
        .toolbar {
            ToolbarItemGroup {
                Button("Quick Look", systemImage: "eye") {
                    if let file = selectedFile { quickLook.present(file.url) }
                }
                .disabled(selectedFile?.exists != true)

                Button("Print", systemImage: "printer", action: printSelected)
                    .disabled(selectedFile?.exists != true)

                Button("Export…", systemImage: "square.and.arrow.up", action: exportSelected)
                    .disabled(selectedFile?.exists != true)

                Button("Copy Provenance", systemImage: "doc.on.clipboard", action: copyProvenance)
                    .disabled(provenanceRecord == nil)

                Button("Reveal in Finder", systemImage: "folder") {
                    if let file = selectedFile { application.revealGeneratedFile(file) }
                }
                .disabled(selectedFile?.exists != true)
            }
        }
        .alert("The PDF could not be exported", isPresented: exportAlertBinding) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(exportError ?? "Try another destination.")
        }
    }

    private var selectedBinding: Binding<GeneratedFile.ID> {
        Binding(
            get: { selection ?? files[0].id },
            set: { selection = $0 }
        )
    }

    private var selectedFile: GeneratedFile? {
        files.first { $0.id == selection } ?? files.first
    }

    private var provenanceRecord: GenerationJobRecord? {
        guard let file = selectedFile else { return nil }
        return application.recentDocumentStore.records.first { record in
            record.artifacts.contains { $0.id == file.id || $0.url == file.url }
        }
    }

    private var exportAlertBinding: Binding<Bool> {
        Binding(
            get: { exportError != nil },
            set: { if !$0 { exportError = nil } }
        )
    }

    private func printSelected() {
        guard let file = selectedFile,
              let operation = PDFDocumentActions.printOperation(for: file.url)
        else { return }
        operation.run()
    }

    private func exportSelected() {
        guard let file = selectedFile else { return }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = file.url.lastPathComponent
        panel.allowedContentTypes = [.pdf]
        guard panel.runModal() == .OK, let destination = panel.url else { return }
        do {
            try PDFDocumentActions.export(from: file.url, to: destination)
        } catch {
            exportError = error.localizedDescription
        }
    }

    private func copyProvenance() {
        guard let provenanceRecord else { return }
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(provenanceRecord.provenanceSummary, forType: .string)
    }
}

enum PDFDocumentActions {
    @MainActor
    static func printOperation(for url: URL) -> NSPrintOperation? {
        guard let document = PDFDocument(url: url) else { return nil }
        // Printing a zero-sized PDFView prints the view, not the whole paper.
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
    let url: URL

    func makeNSView(context: Context) -> PDFView {
        let view = PDFView()
        view.autoScales = true
        view.displayMode = .singlePageContinuous
        view.displaysPageBreaks = true
        view.backgroundColor = .windowBackgroundColor
        return view
    }

    func updateNSView(_ view: PDFView, context: Context) {
        if view.document?.documentURL != url {
            view.document = PDFDocument(url: url)
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
