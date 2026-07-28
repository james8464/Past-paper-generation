import SwiftUI

extension View {
    func nativePrimaryActionStyle() -> some View {
        buttonStyle(.borderedProminent)
    }

    func nativePanel() -> some View {
        self
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(20)
            .background(Color(nsColor: .controlBackgroundColor), in: RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(.quaternary, lineWidth: 1)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
    }
}
