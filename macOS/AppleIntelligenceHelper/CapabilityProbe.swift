// Type-check only during packaging. This function is never executed.
import Foundation
import FoundationModels

@available(macOS 26.4, *)
func requiredFoundationModelsAPIs(schema: GenerationSchema) async throws {
  let model = SystemLanguageModel.default
  _ = model.contextSize
  _ = model.supportsLocale(Locale(identifier: "fr_FR"))
  _ = try await model.tokenCount(for: "probe")
  _ = try await model.tokenCount(for: Instructions("probe"))
  _ = try await model.tokenCount(for: schema)
}

// Runtime availability cannot hide an unknown type from an older SDK compiler.
// Cover the same unified error symbols used by the enabled helper as well.
@available(macOS 27.0, *)
func requiredFoundationModelsErrorAPIs(_ error: any Error) {
  if let failure = error as? LanguageModelError {
    switch failure {
    case .contextSizeExceeded: break
    case .unsupportedGenerationGuide: break
    case .unsupportedLanguageOrLocale: break
    default: break
    }
  }
}
