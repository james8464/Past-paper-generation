import Foundation

enum JSONValue: Codable, Sendable, Equatable {
  case object([String: JSONValue])
  case array([JSONValue])
  case string(String)
  case number(Double)
  case bool(Bool)
  case null

  init(from decoder: any Decoder) throws {
    let value = try decoder.singleValueContainer()
    if value.decodeNil() {
      self = .null
    } else if let result = try? value.decode(Bool.self) {
      self = .bool(result)
    } else if let result = try? value.decode(String.self) {
      self = .string(result)
    } else if let result = try? value.decode([String: JSONValue].self) {
      self = .object(result)
    } else if let result = try? value.decode([JSONValue].self) {
      self = .array(result)
    } else {
      let result = try value.decode(Double.self)
      guard result.isFinite else { throw HelperFailure.invalidRequest }
      // Reject integer rounding before a guided response crosses the protocol.
      if result.rounded() == result {
        guard let integer = try? value.decode(Int.self),
          Double(exactly: integer) == result,
          let decimal = try? value.decode(Decimal.self), decimal == Decimal(integer)
        else { throw HelperFailure.invalidRequest }
      }
      self = .number(result)
    }
  }

  func encode(to encoder: any Encoder) throws {
    var value = encoder.singleValueContainer()
    switch self {
    case .object(let result): try value.encode(result)
    case .array(let result): try value.encode(result)
    case .string(let result): try value.encode(result)
    case .number(let result):
      if let integer = Int(exactly: result) {
        // Floating notation can shorten a large exact integer's decimal digits.
        try value.encode(integer)
      } else {
        try value.encode(result)
      }
    case .bool(let result): try value.encode(result)
    case .null: try value.encodeNil()
    }
  }

  static func decode(_ data: Data) throws -> JSONValue {
    try JSONDecoder().decode(Self.self, from: data)
  }
  var object: [String: JSONValue]? { if case .object(let value) = self { value } else { nil } }
  var string: String? { if case .string(let value) = self { value } else { nil } }
  var array: [JSONValue]? { if case .array(let value) = self { value } else { nil } }
  var number: Double? { if case .number(let value) = self { value } else { nil } }
  var integer: Int? {
    guard let number, number.isFinite, number.rounded() == number,
      number >= Double(Int.min), number < Double(Int.max)
    else { return nil }
    return Int(number)
  }
}

enum HelperFailure: String, Error {
  case invalidRequest = "invalid_request"
  case unsupportedSchema = "unsupported_schema"
  case unavailable
  case unsupportedLocale = "unsupported_locale"
  case contextCapacity = "context_capacity"
  case cancelled
  case generationFailed = "generation_failed"

  var message: String {
    switch self {
    case .invalidRequest: "The Apple Intelligence request is invalid or exceeds its size limit."
    case .unsupportedSchema:
      "This structured request uses constraints Apple Intelligence cannot safely represent."
    case .unavailable:
      "Apple Intelligence is not available. Check device support, system settings and model readiness."
    case .unsupportedLocale:
      "Apple Intelligence does not support the requested language on this Mac."
    case .contextCapacity:
      "This request exceeds the Apple Intelligence context capacity. Use a smaller task."
    case .cancelled: "Apple Intelligence generation was cancelled."
    case .generationFailed: "Apple Intelligence could not complete this request."
    }
  }
}

struct HelperRequest: Sendable {
  let requestID: String
  let operation: String
  let locale: String
  let prompt: String
  let instructions: String
  let schema: JSONValue?
  let outputTokens: Int
  let temperature: Double
  let schemaMode: String
  let promptIncludesSchema: Bool

  static func parse(_ data: Data) throws -> HelperRequest {
    guard data.count <= 262_144,
      let value = try? JSONValue.decode(data).object,
      value["protocol_version"]?.integer == 1,
      let requestID = value["request_id"]?.string, !requestID.isEmpty, requestID.utf8.count <= 128,
      let operation = value["operation"]?.string, ["availability", "generate"].contains(operation),
      let locale = value["locale"]?.string, !locale.isEmpty, locale.utf8.count <= 64
    else {
      throw HelperFailure.invalidRequest
    }
    let base: Set<String> = ["protocol_version", "request_id", "operation", "locale"]
    if operation == "availability" {
      guard Set(value.keys) == base else { throw HelperFailure.invalidRequest }
      return HelperRequest(
        requestID: requestID, operation: operation, locale: locale,
        prompt: "", instructions: "", schema: nil, outputTokens: 0, temperature: 0,
        schemaMode: "structured_text", promptIncludesSchema: false)
    }
    guard
      Set(value.keys).isSubset(
        of: base.union([
          "prompt", "instructions", "schema", "schema_mode", "max_output_tokens", "temperature",
          "prompt_includes_schema",
        ])),
      let prompt = value["prompt"]?.string,
      !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
      prompt.utf8.count <= 131_072,
      let schema = value["schema"], schema.object != nil,
      let output = value["max_output_tokens"]?.integer, (1...8192).contains(output),
      let temperature = value["temperature"]?.number, (0...2).contains(temperature),
      value["instructions"] == nil || value["instructions"]?.string != nil
    else {
      throw HelperFailure.invalidRequest
    }
    let instructions = value["instructions"]?.string ?? ""
    let schemaMode = value["schema_mode"]?.string ?? "structured_text"
    let binding = value["prompt_includes_schema"] ?? .bool(false)
    guard instructions.utf8.count <= 32_768,
      ["guided", "structured_text", "guided_with_postvalidation"].contains(schemaMode),
      value["schema_mode"] == nil || value["schema_mode"]?.string != nil,
      binding == .bool(false) || binding == .bool(true),
      binding == .bool(false) || schemaMode != "guided"
    else { throw HelperFailure.invalidRequest }
    return HelperRequest(
      requestID: requestID, operation: operation, locale: locale,
      prompt: prompt, instructions: instructions, schema: schema,
      outputTokens: output, temperature: temperature, schemaMode: schemaMode,
      promptIncludesSchema: binding == .bool(true))
  }

  func completePrompt() throws -> String {
    guard schemaMode != "guided", let schema else { return prompt }
    if promptIncludesSchema {
      guard let marker = prompt.range(of: "\nOUTPUT_SCHEMA=", options: .backwards),
        let supplied = try? JSONValue.decode(Data(prompt[marker.upperBound...].utf8)),
        supplied == schema
      else { throw HelperFailure.invalidRequest }
      return prompt
    }
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
    let encoded = try encoder.encode(schema)
    let contract = String(decoding: encoded, as: UTF8.self)
    return prompt
      + "\n\nReturn exactly one JSON object matching OUTPUT_SCHEMA. Do not add an outer Markdown fence, comments or trailing commas. Code fences and formatting requested inside JSON string values are allowed. Preserve the requested language."
      + "\nOUTPUT_SCHEMA=" + contract
  }
}

func admitContext(inputTokens: Int, outputTokens: Int, contextSize: Int) throws {
  // Reserve framing space in addition to separately counted instructions, prompt and schema.
  guard inputTokens >= 0, outputTokens > 0, contextSize > 256,
    inputTokens <= contextSize - 256,
    outputTokens <= contextSize - 256 - inputTokens
  else { throw HelperFailure.contextCapacity }
}
