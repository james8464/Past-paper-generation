---
type: "query"
date: "2026-08-01T16:45:31.788294+00:00"
question: "How does the generation quality pipeline connect?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["AssessmentLLMClient", "generate_unique_paper()", "generation.py", "validate_pdf_for_release()", "AppViewModel"]
---

# Q: How does the generation quality pipeline connect?

## Answer

The registry selects a generator entry point. Its immutable blueprint is filled by AssessmentLLMClient through structured provider calls and bounded repair retries. generate_unique_paper validates marks, command words, AO totals, novelty, source grounding, and reviewer results. Generation then validates the assessment package and each PDF before transactional publication. Swift AppViewModel drives the JSONL workflow and exposes validation outcomes.

## Outcome

- Signal: useful

## Source Nodes

- AssessmentLLMClient
- generate_unique_paper()
- generation.py
- validate_pdf_for_release()
- AppViewModel