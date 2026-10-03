import SwiftUI
import TipKit

enum PaperCreationTips {
    static let modelRecommendation = ModelRecommendationTip()
    static let preview = PreviewTip()
    static let quality = QualityTip()
}

struct ModelRecommendationTip: Tip {
    var title: Text { Text("Use the recommended local model") }
    var message: Text? {
        Text("Other Ollama models and quantisations can change question and mark-scheme quality.")
    }
    var image: Image? { Image(systemName: "cpu") }
}

struct PreviewTip: Tip {
    var title: Text { Text("Preview before a live generation") }
    var message: Text? {
        Text("Layout preview checks pagination without using AI. Its placeholder questions are not finished papers.")
    }
    var image: Image? { Image(systemName: "doc.text.magnifyingglass") }
}

struct QualityTip: Tip {
    var title: Text { Text("Review both documents") }
    var message: Text? {
        Text("Open both PDFs in Documents, then review the quality evidence.")
    }
    var image: Image? { Image(systemName: "checklist") }
}
