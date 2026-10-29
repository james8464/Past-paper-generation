import SwiftUI

struct DocumentPickerView: View {
    @Environment(\.locale) private var locale
    let files: [GeneratedFile]
    @Binding var selection: GeneratedFile.ID

    var body: some View {
        Picker("Document", selection: $selection) {
            ForEach(files) { file in
                Text(Self.label(for: file, locale: locale))
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .help(file.url.path)
                    .tag(file.id)
            }
        }
        .pickerStyle(.menu)
        .labelsHidden()
        .lineLimit(1)
        .truncationMode(.middle)
        .frame(minWidth: 0, maxWidth: .infinity, alignment: .leading)
        .help(files.first(where: { $0.id == selection })?.url.path ?? "")
    }

    static func label(for file: GeneratedFile, locale: Locale) -> String {
        let role = String(localized: InterfaceText.localizedResource(file.titleResource, locale: locale))
        let date = file.createdAt.formatted(
            .dateTime.year().month(.abbreviated).day().hour().minute().second().locale(locale)
        )
        return [role, file.subject, file.paper, date]
            .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
            .joined(separator: " · ")
    }
}
