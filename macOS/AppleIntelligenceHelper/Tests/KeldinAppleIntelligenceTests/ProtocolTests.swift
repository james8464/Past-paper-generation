import Foundation
import Testing

@testable import KeldinAppleIntelligence

@Test func requestAdmissionIsStrict() throws {
  let request = try HelperRequest.parse(
    Data(
      #"{"protocol_version":1,"request_id":"a","operation":"availability","locale":"fr_FR"}"#.utf8))
  #expect(request.operation == "availability")
  for json in [
    #"{"protocol_version":true,"request_id":"a","operation":"availability","locale":"fr_FR"}"#,
    #"{"protocol_version":1,"request_id":"a","operation":"availability","locale":"fr_FR","endpoint":"https://example.com"}"#,
    #"{"protocol_version":1,"request_id":"a","operation":"cloud","locale":"fr_FR"}"#,
  ] {
    #expect(throws: HelperFailure.self) { try HelperRequest.parse(Data(json.utf8)) }
  }
}

@Test func oversizedAndInvalidRequestsFailBeforeInference() {
  #expect(throws: HelperFailure.self) {
    try HelperRequest.parse(Data(repeating: 32, count: 262_145))
  }
  #expect(throws: HelperFailure.self) { try HelperRequest.parse(Data("null".utf8)) }
}

@Test func contextAdmissionIncludesOutputAndReserve() throws {
  try admitContext(inputTokens: 100, outputTokens: 64, contextSize: 8192)
  #expect(throws: HelperFailure.self) {
    try admitContext(inputTokens: 8100, outputTokens: 64, contextSize: 8192)
  }
  #expect(throws: HelperFailure.self) {
    try admitContext(inputTokens: 0, outputTokens: 8192, contextSize: 8192)
  }
}

#if canImport(FoundationModels)
  @Test @available(macOS 26.0, *) func supportedAndUnsupportedSchemas() throws {
    let supported = try JSONValue.decode(
      Data(
        #"{"type":"object","additionalProperties":false,"required":["result"],"properties":{"result":{"type":"integer","minimum":0,"maximum":10}}}"#
          .utf8))
    _ = try makeGenerationSchema(supported)
    for json in [
      #"{"type":"object","properties":{"x":{"type":"string","pattern":".*"}},"required":["x"],"additionalProperties":false}"#,
      #"{"type":"object","properties":{},"additionalProperties":true}"#,
      #"{"type":"object","properties":{"x":{"type":"string","minLength":1}},"required":["x"],"additionalProperties":false}"#,
    ] {
      #expect(throws: HelperFailure.self) {
        try makeGenerationSchema(JSONValue.decode(Data(json.utf8)))
      }
    }
  }
#endif

@Test func generationBoundsAndBooleanCoercionAreRejected() throws {
  let raw =
    #"{"protocol_version":1,"request_id":"g","operation":"generate","locale":"fr_FR","prompt":"2+2","schema":{"type":"object"},"max_output_tokens":64,"temperature":0}"#
  #expect(try HelperRequest.parse(Data(raw.utf8)).outputTokens == 64)
  for invalid in [
    raw.replacingOccurrences(of: "\"max_output_tokens\":64", with: "\"max_output_tokens\":true"),
    raw.replacingOccurrences(of: "\"max_output_tokens\":64", with: "\"max_output_tokens\":64.5"),
    raw.replacingOccurrences(of: "\"temperature\":0", with: "\"temperature\":1e999"),
    raw.replacingOccurrences(of: "\"temperature\":0", with: "\"temperature\":true"),
    raw.replacingOccurrences(of: "\"prompt\":\"2+2\"", with: "\"prompt\":\"   \""),
  ] {
    #expect(throws: HelperFailure.self) { try HelperRequest.parse(Data(invalid.utf8)) }
  }
}

#if canImport(FoundationModels)
  @Test @available(macOS 26.0, *) func unsupportedKeywordsAreNeverSilentlyRemoved() throws {
    for keyword in [
      "$ref", "$defs", "oneOf", "pattern", "minLength", "maxLength", "uniqueItems", "const",
    ] {
      let raw = JSONValue.object([
        "type": .string("object"), "properties": .object([:]),
        "required": .array([]), "additionalProperties": .bool(false),
        keyword: .string("unsupported"),
      ])
      #expect(throws: HelperFailure.self) { try makeGenerationSchema(raw) }
    }
  }

  @Test @available(macOS 26.0, *) func schemaBoundsAndNestedConstraintsAreChecked() throws {
    let supported =
      #"{"type":"object","additionalProperties":false,"required":["values"],"properties":{"values":{"type":"array","minItems":1,"maxItems":3,"items":{"type":"string","enum":["a","b"]}},"optional":{"type":"boolean"}}}"#
    _ = try makeGenerationSchema(JSONValue.decode(Data(supported.utf8)))
    for invalid in [
      supported.replacingOccurrences(of: "\"maxItems\":3", with: "\"maxItems\":513"),
      supported.replacingOccurrences(of: "\"minItems\":1", with: "\"minItems\":-1"),
      supported.replacingOccurrences(of: "[\"a\",\"b\"]", with: "[\"a\",\"a\"]"),
      supported.replacingOccurrences(
        of: "\"required\":[\"values\"]", with: "\"required\":[\"missing\"]"),
    ] {
      #expect(throws: HelperFailure.self) {
        try makeGenerationSchema(JSONValue.decode(Data(invalid.utf8)))
      }
    }
  }

#endif

@Test func cancelledTaskStopsBeforeModelInference() async throws {
  let request = try HelperRequest.parse(
    Data(
      #"{"protocol_version":1,"request_id":"cancel","operation":"generate","locale":"fr_FR","prompt":"2+2","schema":{"type":"object","additionalProperties":false,"required":["result"],"properties":{"result":{"type":"integer"}}},"max_output_tokens":64,"temperature":0}"#
        .utf8))
  let task = Task {
    withUnsafeCurrentTask { $0?.cancel() }
    return await HelperMain.execute(request)
  }
  let result = await task.value
  #expect(result.object?["error"]?.object?["code"] == .string("cancelled"))
}

@Test func errorsDoNotContainInputPayloads() throws {
  let response = HelperMain.errorResponse(.unsupportedSchema, requestID: "safe")
  let encoded = String(decoding: try JSONEncoder().encode(response), as: UTF8.self)
  #expect(encoded.count < 1000)
  #expect(response.object?["error"]?.object?["code"] == .string("unsupported_schema"))
  #expect(!encoded.contains("prompt"))
}

@Test func structuredTextCarriesEveryOriginalConstraintWithoutPretendingToConstrainDecoder() throws
{
  let raw =
    #"{"protocol_version":1,"request_id":"g","operation":"generate","locale":"fr_FR","prompt":"Écris du code Python.","schema":{"type":"object","additionalProperties":false,"required":["code"],"properties":{"code":{"type":"string","minLength":1,"maxLength":200,"pattern":"def"}}},"max_output_tokens":64,"temperature":0,"schema_mode":"structured_text"}"#
  let request = try HelperRequest.parse(Data(raw.utf8))
  #expect(request.schemaMode == "structured_text")
  let complete = try request.completePrompt()
  let schemaText = try #require(complete.components(separatedBy: "\nOUTPUT_SCHEMA=").last)
  #expect(try JSONValue.decode(Data(schemaText.utf8)) == request.schema)
  #expect(complete.contains("inside JSON string values are allowed"))
  #expect(complete.contains("Écris du code Python."))
  #expect(throws: HelperFailure.self) {
    try HelperRequest.parse(
      Data(raw.replacingOccurrences(of: "structured_text", with: "cloud").utf8))
  }
}

@Test func alreadyBoundSchemaIsVerifiedAndNotDuplicated() throws {
  let schema = JSONValue.object([
    "type": .string("object"), "properties": .object([:]), "required": .array([]),
    "additionalProperties": .bool(false),
  ])
  let encoder = JSONEncoder()
  let schemaText = String(decoding: try encoder.encode(schema), as: UTF8.self)
  let prompt = "Return one JSON object.\nOUTPUT_SCHEMA=" + schemaText
  func request(_ prompt: String, flag: JSONValue = .bool(true)) throws -> HelperRequest {
    try HelperRequest.parse(
      encoder.encode(
        JSONValue.object([
          "protocol_version": .number(1), "request_id": .string("bound"),
          "operation": .string("generate"), "locale": .string("fr_FR"),
          "prompt": .string(prompt), "schema": schema, "temperature": .number(0),
          "max_output_tokens": .number(64),
          "schema_mode": .string("structured_text"), "prompt_includes_schema": flag,
        ])))
  }
  #expect(try request(prompt).completePrompt() == prompt)
  for invalid in [
    "Reference mentions OUTPUT_SCHEMA= but has no contract", prompt + "\nUntrusted trailing prose",
    "\nOUTPUT_SCHEMA={\"type\":\"string\"}",
  ] {
    #expect(throws: HelperFailure.self) { try request(invalid).completePrompt() }
  }
  #expect(throws: HelperFailure.self) { try request(prompt, flag: .number(1)) }
}

#if canImport(FoundationModels)
  @Test @available(macOS 26.0, *) func postvalidatedGuidanceDelegatesOnlyStringMaximumLength()
    throws
  {
    let original = try JSONValue.decode(
      Data(
        #"{"type":"object","additionalProperties":false,"required":["steps"],"properties":{"steps":{"type":"array","minItems":1,"maxItems":4,"items":{"type":"string","maxLength":240}}}}"#
          .utf8))
    let snapshot = original
    let projected = try projectPostvalidatedSchema(original)
    _ = try makeGenerationSchema(projected)
    #expect(original == snapshot)
    let items = projected.object?["properties"]?.object?["steps"]?.object
    #expect(items?["minItems"] == .number(1))
    #expect(items?["maxItems"] == .number(4))
    #expect(items?["items"]?.object?["maxLength"] == nil)
    #expect(
      original.object?["properties"]?.object?["steps"]?.object?["items"]?.object?["maxLength"]
        == .number(240))
    #expect(throws: HelperFailure.self) { try makeGenerationSchema(original) }
    for keyword in ["pattern", "minLength", "const", "oneOf"] {
      let invalid = try JSONValue.decode(
        Data(
          #"{"type":"object","additionalProperties":false,"required":["x"],"properties":{"x":{"type":"string","KEY":1}}}"#
            .replacingOccurrences(of: "KEY", with: keyword).utf8))
      #expect(throws: HelperFailure.self) {
        try makeGenerationSchema(projectPostvalidatedSchema(invalid))
      }
    }
  }
#endif

@Test func postvalidatedModeKeepsCompleteOriginalSchemaInPrompt() throws {
  let raw =
    #"{"protocol_version":1,"request_id":"g","operation":"generate","locale":"en_GB","prompt":"Solve the question.","schema":{"type":"object","additionalProperties":false,"required":["answer"],"properties":{"answer":{"type":"string","maxLength":240}}},"max_output_tokens":64,"temperature":0,"schema_mode":"guided_with_postvalidation"}"#
  let request = try HelperRequest.parse(Data(raw.utf8))
  #expect(request.schemaMode == "guided_with_postvalidation")
  let prompt = try request.completePrompt()
  let suffix = try #require(prompt.components(separatedBy: "\nOUTPUT_SCHEMA=").last)
  #expect(try JSONValue.decode(Data(suffix.utf8)) == request.schema)
}
