enum PaperCreationContext: Equatable {
    case board
    case french(largePrint: Bool)

    var frenchLargePrint: Bool? {
        guard case let .french(largePrint) = self else { return nil }
        return largePrint
    }

    func canCreate(boardCanGenerate: Bool, hasFrenchReferences: Bool, isBusy: Bool) -> Bool {
        guard !isBusy else { return false }
        switch self {
        case .board: return boardCanGenerate
        case .french: return hasFrenchReferences
        }
    }
}
