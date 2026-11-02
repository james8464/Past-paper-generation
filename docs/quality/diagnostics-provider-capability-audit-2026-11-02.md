# Diagnostics and French provider capability audit

The internal reviewer `french_run23_review` read these three pending implementation files through EOF at `0bcb3d502e2fc91867fa088edfc325b1c253c00f` on 2 November 2026:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/generation_diagnostics.py` | 181 | `3cd4130cbe563fa9716ba6abfd35786d90de51feec1d4257f029020953b37baa` |
| `Backend/Core/france/provider.py` | 383 | `6e5dc1dce636cdba831b976510174a47fd0ff9e517b7a0862e75db3c35a1a8b6` |
| `tools/french_model_capability.py` | 420 | `74e545148c46d1e8fc0d878a3652b7e4a57dc0a78a6bbdd1103a98060bfa7cbd` |

The review selectively traced diagnostic callers and failure handling, typed request/schema validation, transport selection, runtime client selection and relevant existing tests. Diagnostic output remains private failure evidence. Capability results explicitly exclude teacher review and empirical calibration. The French Ollama wrapper serves historical generation paths, not the current V36 transport.

No confirmed P1/P2 defect was found in this bounded static review. No code was changed. No tests, model requests, network calls or native UI actions were performed. Dependencies and test files were not all read through EOF. This adds no evidence of ETA accuracy, measured generation speed, live paper quality or whole-project completion.
