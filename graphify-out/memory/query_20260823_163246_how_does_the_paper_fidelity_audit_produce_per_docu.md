---
type: "query"
date: "2026-08-23T16:32:46.039301+00:00"
question: "How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["audit()", "_document_result()", "_registered_page_comparison()", "main()"]
---

# Q: How does the paper fidelity audit produce per-document and per-role scores, and where should release thresholds integrate?

## Answer

Expanded from original query via vocab: [audit, comparison, document, family, fidelity, minimum, release, role, score, scores]. paper_fidelity_audit.audit builds family document results through _document_result; each document exposes comparison.overall and role_scores from classified page comparisons. The release threshold check belongs after report and visual artifact generation in main so diagnostics remain available while the CLI still exits nonzero.

## Outcome

- Signal: useful

## Source Nodes

- audit()
- _document_result()
- _registered_page_comparison()
- main()