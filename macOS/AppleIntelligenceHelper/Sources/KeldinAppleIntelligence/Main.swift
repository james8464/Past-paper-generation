import Darwin
import Dispatch
import Foundation

#if canImport(FoundationModels)
  import FoundationModels
#endif

@main
struct HelperMain {
  static func main() async {
    let data = FileHandle.standardInput.readData(ofLength: 262_145)
    let request: HelperRequest
    do { request = try HelperRequest.parse(data) } catch {
      emit(errorResponse(.invalidRequest, requestID: ""))
      return
    }
    let task = Task { await execute(request) }
    signal(SIGTERM, SIG_IGN)
    signal(SIGINT, SIG_IGN)
    let signals = [SIGTERM, SIGINT].map { signalNumber in
      let source = DispatchSource.makeSignalSource(signal: signalNumber, queue: .global())
      source.setEventHandler { task.cancel() }
      source.resume()
      return source
    }
    emit(await task.value)
    for source in signals { source.cancel() }
  }

  static func emit(_ response: JSONValue) {
    guard let encoded = try? JSONEncoder().encode(response), encoded.count <= 1_048_576 else {
      return
    }
    FileHandle.standardOutput.write(encoded + Data([10]))
  }

  static func errorResponse(
    _ failure: HelperFailure, requestID: String, fields: [String: JSONValue] = [:]
  ) -> JSONValue {
    var result = fields
    result["protocol_version"] = .number(1)
    result["request_id"] = .string(requestID)
    result["provider"] = .string("apple_intelligence")
    result["model"] = .string("apple-system-on-device")
    result["os_version"] = .string(ProcessInfo.processInfo.operatingSystemVersionString)
    result["status"] = .string("error")
    result["error"] = .object([
      "code": .string(failure.rawValue), "message": .string(failure.message),
    ])
    return .object(result)
  }

  static func execute(_ request: HelperRequest) async -> JSONValue {
    if Task.isCancelled { return errorResponse(.cancelled, requestID: request.requestID) }
    #if canImport(FoundationModels)
      guard #available(macOS 26.4, *) else {
        return errorResponse(.unavailable, requestID: request.requestID)
      }
      return await executeSupported(request)
    #else
      return errorResponse(.unavailable, requestID: request.requestID)
    #endif
  }

  #if canImport(FoundationModels)
    @available(macOS 26.4, *)
    static func executeSupported(_ request: HelperRequest) async -> JSONValue {
      let model = SystemLanguageModel.default
      var result: [String: JSONValue] = [
        "protocol_version": .number(1), "request_id": .string(request.requestID),
        "provider": .string("apple_intelligence"), "model": .string("apple-system-on-device"),
        "os_version": .string(ProcessInfo.processInfo.operatingSystemVersionString),
        "available": .bool(model.isAvailable), "context_size": .number(Double(model.contextSize)),
        "french_supported": .bool(model.supportsLocale(Locale(identifier: "fr_FR"))),
      ]
      if request.operation == "availability" {
        result["status"] = .string("available")
        switch model.availability {
        case .available: break
        case .unavailable(let reason):
          switch reason {
          case .deviceNotEligible: result["unavailable_reason"] = .string("device_not_eligible")
          case .appleIntelligenceNotEnabled:
            result["unavailable_reason"] = .string("apple_intelligence_not_enabled")
          case .modelNotReady: result["unavailable_reason"] = .string("model_not_ready")
          @unknown default: result["unavailable_reason"] = .string("unknown")
          }
        }
        return .object(result)
      }
      do {
        try Task.checkCancellation()
        guard model.isAvailable else { throw HelperFailure.unavailable }
        guard model.supportsLocale(Locale(identifier: request.locale)) else {
          throw HelperFailure.unsupportedLocale
        }
        guard let rawSchema = request.schema else { throw HelperFailure.invalidRequest }
        let schema = request.schemaMode == "guided" ? try makeGenerationSchema(rawSchema) : nil
        let instructions = Instructions(request.instructions)
        let prompt = try request.completePrompt()
        var input = try await model.tokenCount(for: prompt) + model.tokenCount(for: instructions)
        if let schema { input += try await model.tokenCount(for: schema) }
        result["input_token_count"] = .number(Double(input))
        try admitContext(
          inputTokens: input, outputTokens: request.outputTokens, contextSize: model.contextSize)
        try Task.checkCancellation()
        let session = LanguageModelSession(model: model, instructions: instructions)
        let options = GenerationOptions(
          temperature: request.temperature, maximumResponseTokens: request.outputTokens)
        if let schema {
          let response = try await session.respond(to: prompt, schema: schema, options: options)
          try Task.checkCancellation()
          let outputData = Data(response.content.jsonString.utf8)
          guard outputData.count <= 131_072,
            let output = try? JSONValue.decode(outputData), output.object != nil
          else { throw HelperFailure.generationFailed }
          result["output"] = output
        } else {
          let response = try await session.respond(to: prompt, options: options)
          try Task.checkCancellation()
          guard response.content.utf8.count <= 131_072 else { throw HelperFailure.generationFailed }
          result["raw_output"] = .string(response.content)
        }
        result["status"] = .string("ok")
        result["generation_mode"] = .string(request.schemaMode)
        return .object(result)
      } catch is CancellationError {
        return errorResponse(.cancelled, requestID: request.requestID, fields: result)
      } catch let failure as HelperFailure {
        return errorResponse(failure, requestID: request.requestID, fields: result)
      } catch {
        let failure = Task.isCancelled ? HelperFailure.cancelled : classifyGenerationError(error)
        return errorResponse(failure, requestID: request.requestID, fields: result)
      }
    }

    static func classifyGenerationError(_ error: any Error) -> HelperFailure {
      #if compiler(>=6.4)
        if #available(macOS 27.0, *), let failure = error as? LanguageModelError {
          switch failure {
          case .contextSizeExceeded: return .contextCapacity
          case .unsupportedGenerationGuide: return .unsupportedSchema
          case .unsupportedLanguageOrLocale: return .unsupportedLocale
          default: return .generationFailed
          }
        }
      #endif
      return .generationFailed
    }
  #endif
}
