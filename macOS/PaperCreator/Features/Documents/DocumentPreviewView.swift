import AppKit
import Combine
import PDFKit
@preconcurrency import Quartz
import SwiftUI
import UniformTypeIdentifiers

struct DocumentPreviewView: View {
    @EnvironmentObject private var application: ApplicationCoordinator
    let files: [GeneratedFile]
    @State private var selection: GeneratedFile.ID?
    @State private var exportError: String?
    @StateObject private var quickLook = QuickLookCoordinator()

    init(files: [GeneratedFile], selectedID: GeneratedFile.ID? = nil) {
        self.files = files.filter { $0.url.pathExtension.lowercased() == "pdf" }
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
              let document = PDFDocument(url: file.url)
        else { return }
        let view = PDFView(frame: .zero)
        view.document = document
        view.autoScales = true
        NSPrintOperation(view: view).run()
    }

    private func exportSelected() {
        guard let file = selectedFile else { return }
        let panel = NSSavePanel()
        panel.nameFieldStringValue = file.url.lastPathComponent
        panel.allowedContentTypes = [.pdf]
        guard panel.runModal() == .OK, let destination = panel.url else { return }
        do {
            if FileManager.default.fileExists(atPath: destination.path) {
                try FileManager.default.removeItem(at: destination)
            }
            try FileManager.default.copyItem(at: file.url, to: destination)
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
