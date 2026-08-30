import SwiftUI

enum WorkspaceLayoutMode: Equatable {
    case compact
    case standard
    case expanded

    var showsSidebar: Bool {
        self != .compact
    }

    var showsInspector: Bool {
        self == .expanded
    }
}

enum WorkspaceLayoutPolicy {
    static func mode(for width: CGFloat) -> WorkspaceLayoutMode {
        if width < 840 {
            return .compact
        }
        if width < 1_100 {
            return .standard
        }
        return .expanded
    }
}

extension View {
    func nativePrimaryActionStyle() -> some View {
        buttonStyle(.borderedProminent)
    }

}
