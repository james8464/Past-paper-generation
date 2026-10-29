// Describe the current paper selection for the creation interface.

enum KeldinCreationContext: Equatable {
    case board
    case french(largePrint: Bool)
    case presentingModal

    func presentingModal(_ isPresented: Bool) -> Self { isPresented ? .presentingModal : self }

    static func allowsNavigation(
        from context: Self?, applicationModal: Bool,
        mainSceneIsFocused: Bool = true, settingsModal: Bool = false
    ) -> Bool {
        !(applicationModal && mainSceneIsFocused) && !settingsModal && context != .presentingModal
    }

    var frenchLargePrint: Bool? {
        guard case let .french(largePrint) = self else { return nil }
        return largePrint
    }

    func canCreate(boardCanGenerate: Bool, hasFrenchReferences: Bool, isBusy: Bool) -> Bool {
        guard !isBusy else { return false }
        switch self {
        case .board: return boardCanGenerate
        case .french: return hasFrenchReferences
        case .presentingModal: return false
        }
    }
}
