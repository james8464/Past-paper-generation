// Share native appearance and status styling across the app.

import SwiftUI

enum WorkspaceLayoutMode: Equatable {
    case compact
    case standard
    case expanded

    var showsSidebar: Bool {
        self != .compact
    }

    var qualityReviewWidth: CGFloat {
        switch self {
        case .compact: 420
        case .standard: 480
        case .expanded: 560
        }
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

enum WorkspaceSidebarPolicy {
    static func columnVisibility(
        for layoutMode: WorkspaceLayoutMode, preference: Binding<String>
    ) -> Binding<NavigationSplitViewVisibility> {
        Binding(
            get: {
                resolvedVisibility(for: layoutMode, preference: preference.wrappedValue)
            },
            set: { value in
                // Layout callbacks can echo the resolved value without a user change.
                guard value != resolvedVisibility(for: layoutMode, preference: preference.wrappedValue) else {
                    return
                }
                switch value {
                case .detailOnly: preference.wrappedValue = "detail"
                case .doubleColumn: preference.wrappedValue = "double"
                default: preference.wrappedValue = "all"
                }
            }
        )
    }

    private static func resolvedVisibility(
        for layoutMode: WorkspaceLayoutMode, preference: String
    ) -> NavigationSplitViewVisibility {
        switch preference {
        case "detail": return .detailOnly
        case "double": return .doubleColumn
        case "all": return .all
        default: return layoutMode.showsSidebar ? .all : .detailOnly
        }
    }
}

extension View {
    func nativePrimaryActionStyle() -> some View {
        buttonStyle(.borderedProminent)
            .tint(Color("ControlAccent"))
    }

}
