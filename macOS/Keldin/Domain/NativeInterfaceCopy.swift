import Foundation

enum NativeInterfaceCopy {
    static func benchmarkText(_ text: String, locale: Locale) -> String {
        guard let resource = benchmarkResources[text] else { return text }
        return String(localized: InterfaceText.localizedResource(resource, locale: locale))
    }

    static func benchmarkUnit(_ unit: String, locale: Locale) -> String {
        let resource: LocalizedStringResource
        switch unit {
        case "cores": resource = "cores"
        case "GB": resource = "GB"
        case "MB/s": resource = "MB/s"
        default: return unit
        }
        return String(localized: InterfaceText.localizedResource(resource, locale: locale))
    }

    // Only copy emitted by the supported benchmark protocol is translated.
    // Device descriptions, power-source values and unknown diagnostics stay verbatim.
    private static let benchmarkResources: [String: LocalizedStringResource] = [
        "The benchmark returned an invalid score.": "The benchmark returned an invalid score.",
        "Benchmark failed": "Benchmark failed",
        "No samples were collected.": "No samples were collected.",
        "Ready for local generation": "Ready for local generation",
        "This Mac should generate papers comfortably with the selected local setup.": "This Mac should generate papers comfortably with the selected local setup.",
        "Capable with slower local models": "Capable with slower local models",
        "Generation should work, but large Ollama models may take noticeably longer.": "Generation should work, but large Ollama models may take noticeably longer.",
        "Use smaller models or hosted AI": "Use smaller models or hosted AI",
        "The diagnostic found limited headroom for local generation.": "The diagnostic found limited headroom for local generation.",
        "Hashing workload used as a local model proxy.": "Hashing workload used as a local model proxy.",
        "Proxy for many small PDF and image writes.": "Proxy for many small PDF and image writes.",
        "Unavailable during benchmark": "Unavailable during benchmark",
        "Ollama was not reachable during benchmark": "Ollama was not reachable during benchmark",
        "Unavailable on this Mac": "Unavailable on this Mac",
        "Device": "Device",
        "Architecture": "Architecture",
        "Processor": "Processor",
        "CPU Cores": "CPU Cores",
        "Memory": "Memory",
        "Python Runtime": "Python Runtime",
        "Performance Cores": "Performance Cores",
        "Efficiency Cores": "Efficiency Cores",
        "CPU Throughput": "CPU Throughput",
        "Average CPU Load": "Average CPU Load",
        "Free Memory": "Free Memory",
        "Memory Pressure": "Memory Pressure",
        "Swap Used": "Swap Used",
        "Disk Write": "Disk Write",
        "Disk Read": "Disk Read",
        "Small-file Latency": "Small-file Latency",
        "Output Free Space": "Output Free Space",
        "PDF Render": "PDF Render",
        "Network Latency": "Network Latency",
        "Network Download": "Network Download",
        "Ollama Response": "Ollama Response",
        "Thermal Speed Limit": "Thermal Speed Limit",
        "Power Source": "Power Source",
        "Battery Level": "Battery Level",
    ]

    static func creationTitle(for kind: AssessmentKind) -> LocalizedStringResource {
        kind == .questionBank ? "Create Practice Set" : "Create Paper"
    }
}

extension GenerationQualityState {
    var titleResource: LocalizedStringResource {
        switch self {
        case .passed: "Passed"
        case .pending: "Pending"
        case .preview: "Preview"
        case .atCreation: "At creation"
        case .unknown: "Unknown"
        case .insufficient: "Insufficient"
        }
    }
}

extension GenerationJobState {
    var titleResource: LocalizedStringResource {
        switch self {
        case .pending: "Pending"
        case .running: "Creating"
        case .completed: "Completed"
        case .cancelled: "Cancelled"
        case .failed: "Failed"
        case .interrupted: "Interrupted"
        case .missingArtifacts: "Files Missing"
        }
    }
}

extension SavedGenerationMode {
    var titleResource: LocalizedStringResource {
        switch self {
        case .preview: "Preview"
        case .live: "Live"
        case .unknown: "Unknown"
        }
    }
}

extension GeneratedFile {
    var titleResource: LocalizedStringResource {
        switch role {
        case "question_paper": "Question Paper"
        case "source_booklet": "Source Booklet"
        case "mark_scheme": "Mark Scheme"
        case "assessment_package": "Assessment Package"
        case "package_manifest": "Package Manifest"
        case "preliminary_material": "Preliminary Material"
        case "electronic_answer_document": "Electronic Answer Document"
        case "skeleton_program": "Skeleton Program"
        case "data_file": "Practice Data"
        default: "\(title)"
        }
    }
}
