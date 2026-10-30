# Apple Intelligence helper

This executable uses Apple's installed `SystemLanguageModel.default` only. It does not load MLX weights, download a model, contact Private Cloud Compute or fall back to another provider. The app remains compatible with macOS 15; this helper reports unavailable before macOS 26.4, which supplies the token-counting API needed for admission.

## Build and placement

The existing backend build phase invokes `macOS/scripts/build_apple_intelligence.sh` before checking the Python helper cache. SwiftPM incrementally builds one release product in this package's reusable `.build` directory, independent of per-test DerivedData copies. The script copies it to `Keldin.app/Contents/Helpers/KeldinAppleIntelligence`, signs and verifies that copy with the app's selected identity, then replaces the destination. Store builds use the existing inherited helper sandbox entitlements and hardened runtime. App Store preflight checks both helpers. There is no runtime compilation or package download.

The packaging wrapper type-checks `CapabilityProbe.swift` without executing it. Only SDKs exposing all required token-counting and context APIs receive the `KELDIN_FOUNDATION_MODELS_CAPABLE` compilation flag. Older SDKs, including those with FoundationModels but without its macOS 26.4 additions, build an unavailable-only helper. Runtime availability checks remain necessary on supported SDKs, and the framework is weak-linked for older operating systems.

For standalone development, use `macOS/scripts/build_apple_intelligence.sh` with Xcode's `SRCROOT`, `TARGET_BUILD_DIR` and `CONTENTS_FOLDER_PATH` variables and the selected signing identity. A bare `swift build` intentionally produces the safe unavailable stub unless the verified capability flag is supplied. Unit protocol tests use `swift test --package-path macOS/AppleIntelligenceHelper --disable-xctest --no-parallel`; they do not perform inference.

## One-request protocol

Write one UTF-8 JSON object to stdin and close stdin. Maximum input is 262,144 bytes. The helper writes one JSON response line and exits. Callers must use the response `status`, not the exit code, to determine success. There is no server, listening port, API key or configurable endpoint.

Availability request:

```json
{"protocol_version":1,"request_id":"unique-id","operation":"availability","locale":"fr_FR"}
```

Generation request adds `prompt`, `instructions` (optional), `schema`, `schema_mode`, `max_output_tokens` and `temperature`. The production mode is `structured_text`, also the default. It places the complete original schema in an `OUTPUT_SCHEMA` section of the prompt. The framework returns an ordinary assistant string, exposed as `raw_output`. This mode does not claim that Apple's decoder enforces the schema. The backend must strictly parse exactly one JSON object and validate the original schema before admitting content. Do not extract code fences, repair JSON or replace failed answers.

`guided` is an optional constrained-decoding mode for small compatible contracts. It supports closed objects with required/optional properties, bounded arrays, strings or string enums, booleans, and integer/number minimum/maximum. Descriptions are accepted. Other keywords, including references, unions, patterns and string-length constraints, are explicitly refused. A guided response has `output` containing an object instead of `raw_output`.

For a caller-prepared complete prompt, set the strict boolean `prompt_includes_schema` to true. The helper requires a terminal `\nOUTPUT_SCHEMA=` section whose entire remaining JSON value equals the owned `schema`; it then uses the prompt verbatim. A mention in reference text, a different schema or trailing prose cannot bypass this binding. No reference text is removed or rewritten. The default false mode appends the complete schema once itself. This avoids charging scarce context twice for an already supplied contract.

Every response identifies `protocol_version`, `request_id`, `provider` (`apple_intelligence`), `model` (`apple-system-on-device`), `os_version` and `status`. Supported-system responses also contain `available`, `context_size` and `french_supported`. Availability replies use `status: available`, including when `available` is false; then `unavailable_reason` explains the device/settings/readiness state. Successful generation uses `status: ok` and `generation_mode`. Failures use `status: error` and a bounded `error` object with `code` and a fixed message. Codes are `invalid_request`, `unsupported_schema`, `unavailable`, `unsupported_locale`, `context_capacity`, `cancelled` and `generation_failed`. No raw input or framework error text is copied into errors.

## Admission and cancellation

Generation checks current device availability and locale support, counts the complete prompt and instructions (plus native schema for guided mode), reserves 256 framing tokens, and admits only when the requested maximum output also fits the current model context. It never truncates the prompt or references. The framework can still refuse a request, including for its own safety policies. Output is capped at 131,072 UTF-8 bytes. Input and output budgets do not demonstrate subject accuracy.

SIGTERM or SIGINT cancels the owned Swift task. The parent must keep its existing bounded termination/kill policy if framework cancellation does not promptly finish. No unrelated process is signalled. Requests are serial, one process per request. On-device system models can change with OS updates; the identity is not a fabricated weight hash.

## Verified scope

This package has protocol, schema-admission and cancellation-before-inference tests. A separate signed probe on macOS 27.0.1 reported an available 8,192-token context and French support. That is this Mac's observed capacity, not a universal constant. A tiny arithmetic response is not paper-quality qualification or App Store approval.
