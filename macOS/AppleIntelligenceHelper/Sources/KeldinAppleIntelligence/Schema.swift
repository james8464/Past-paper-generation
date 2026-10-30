import Foundation

#if canImport(FoundationModels)
  import FoundationModels

  @available(macOS 26.0, *)
  func makeGenerationSchema(_ value: JSONValue) throws -> GenerationSchema {
    guard value.object?["type"]?.string == "object" else { throw HelperFailure.unsupportedSchema }
    var nodes = 0
    let root = try dynamicSchema(value, depth: 0, nodes: &nodes)
    do { return try GenerationSchema(root: root, dependencies: []) } catch {
      throw HelperFailure.unsupportedSchema
    }
  }

  @available(macOS 26.0, *)
  private func dynamicSchema(_ value: JSONValue, depth: Int, nodes: inout Int) throws
    -> DynamicGenerationSchema
  {
    nodes += 1
    guard depth <= 16, nodes <= 512, let schema = value.object,
      let type = schema["type"]?.string
    else { throw HelperFailure.unsupportedSchema }
    let common: Set<String> = ["type", "description"]
    guard schema["description"] == nil || schema["description"]?.string != nil else {
      throw HelperFailure.unsupportedSchema
    }
    let description = schema["description"]?.string
    guard (description?.utf8.count ?? 0) <= 2000 else { throw HelperFailure.unsupportedSchema }
    switch type {
    case "object":
      guard
        Set(schema.keys).isSubset(
          of: common.union(["properties", "required", "additionalProperties"])),
        schema["additionalProperties"] == .bool(false),
        let properties = schema["properties"]?.object, properties.count <= 64,
        let requiredValues = schema["required"]?.array
      else { throw HelperFailure.unsupportedSchema }
      let required = requiredValues.compactMap(\.string)
      guard required.count == requiredValues.count, Set(required).count == required.count,
        Set(required).isSubset(of: Set(properties.keys))
      else { throw HelperFailure.unsupportedSchema }
      let name = "Object\(nodes)"
      var converted: [DynamicGenerationSchema.Property] = []
      for key in properties.keys.sorted() {
        guard !key.isEmpty, key.utf8.count <= 128, let child = properties[key] else {
          throw HelperFailure.unsupportedSchema
        }
        converted.append(
          .init(
            name: key, schema: try dynamicSchema(child, depth: depth + 1, nodes: &nodes),
            isOptional: !required.contains(key)))
      }
      return .init(name: name, description: description, properties: converted)
    case "array":
      guard Set(schema.keys).isSubset(of: common.union(["items", "minItems", "maxItems"])),
        let items = schema["items"]
      else { throw HelperFailure.unsupportedSchema }
      let minimum = schema["minItems"]?.integer
      let maximum = schema["maxItems"]?.integer
      guard schema["minItems"] == nil || minimum != nil,
        schema["maxItems"] == nil || maximum != nil,
        (minimum ?? 0) >= 0, (maximum ?? 512) <= 512, (maximum ?? 512) >= (minimum ?? 0)
      else { throw HelperFailure.unsupportedSchema }
      return .init(
        arrayOf: try dynamicSchema(items, depth: depth + 1, nodes: &nodes),
        minimumElements: minimum,
        maximumElements: maximum)
    case "string":
      guard Set(schema.keys).isSubset(of: common.union(["enum"])) else {
        throw HelperFailure.unsupportedSchema
      }
      if let values = schema["enum"]?.array {
        let strings = values.compactMap(\.string)
        guard !strings.isEmpty, strings.count <= 64, strings.count == values.count,
          Set(strings).count == strings.count, strings.allSatisfy({ $0.utf8.count <= 1024 })
        else { throw HelperFailure.unsupportedSchema }
        return .init(type: String.self, guides: [.anyOf(strings)])
      }
      guard schema["enum"] == nil else { throw HelperFailure.unsupportedSchema }
      return .init(type: String.self)
    case "boolean":
      guard Set(schema.keys).isSubset(of: common) else { throw HelperFailure.unsupportedSchema }
      return .init(type: Bool.self)
    case "integer":
      guard Set(schema.keys).isSubset(of: common.union(["minimum", "maximum"])) else {
        throw HelperFailure.unsupportedSchema
      }
      var guides: [GenerationGuide<Int>] = []
      if let raw = schema["minimum"] {
        guard let bound = raw.integer else { throw HelperFailure.unsupportedSchema }
        guides.append(.minimum(bound))
      }
      if let raw = schema["maximum"] {
        guard let bound = raw.integer else { throw HelperFailure.unsupportedSchema }
        guides.append(.maximum(bound))
      }
      if let lower = schema["minimum"]?.integer, let upper = schema["maximum"]?.integer,
        lower > upper
      {
        throw HelperFailure.unsupportedSchema
      }
      return .init(type: Int.self, guides: guides)
    case "number":
      guard Set(schema.keys).isSubset(of: common.union(["minimum", "maximum"])) else {
        throw HelperFailure.unsupportedSchema
      }
      var guides: [GenerationGuide<Double>] = []
      if let raw = schema["minimum"] {
        guard let bound = raw.number else { throw HelperFailure.unsupportedSchema }
        guides.append(.minimum(bound))
      }
      if let raw = schema["maximum"] {
        guard let bound = raw.number else { throw HelperFailure.unsupportedSchema }
        guides.append(.maximum(bound))
      }
      if let lower = schema["minimum"]?.number, let upper = schema["maximum"]?.number, lower > upper
      {
        throw HelperFailure.unsupportedSchema
      }
      return .init(type: Double.self, guides: guides)
    default: throw HelperFailure.unsupportedSchema
    }
  }
#endif
