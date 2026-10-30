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
