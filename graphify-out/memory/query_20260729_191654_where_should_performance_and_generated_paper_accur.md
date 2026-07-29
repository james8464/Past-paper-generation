---
type: "query"
date: "2026-07-29T19:16:54.006074+00:00"
question: "Where should performance and generated-paper accuracy fixes be made?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["exam_blueprints.py", "providers.py", "layout_master.py", "pdf_validation.py", "paper_fidelity_audit.py", "generation.py", "MarkSchemePoint", "validate_generated_paper"]
---

# Q: Where should performance and generated-paper accuracy fixes be made?

## Answer

Use exam_blueprints.py as the fail-closed assessment contract; keep source figures and worked answers in a shared subject calculation model; render question papers and schemes from that same model; declare provider parallel-safety in providers.py; parallelize only independent hosted requests; and avoid repeated PDF geometry/text extraction in validation, conformance, and fidelity auditing.

## Outcome

- Signal: useful

## Source Nodes

- exam_blueprints.py
- providers.py
- layout_master.py
- pdf_validation.py
- paper_fidelity_audit.py
- generation.py
- MarkSchemePoint
- validate_generated_paper
