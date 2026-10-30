# French reference and figure follow-up

This is an implementation review, not acceptance of a generated paper.

## Changes reviewed

The authoring request now explains that previously covered domains should not
produce the same principal task again. Shared prerequisites remain allowed.
References inform a task without prescribing its topic. Retrieval queries the
existing five curriculum domains, keeps at most ten distinct programme pages and
two official-paper pages, and retains the French curriculum and reference-split
filters. Conflicting duplicate content is refused. Missing evidence is not
replaced with British material or holdout papers.

Read-only retrieval against the primary reference index returned programme pages
4 through 9 and the existing two New Caledonia 2022 summary pages. Its SHA-256
remained `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`.
These excerpts do not establish comprehensive syllabus coverage or task variety.

DeepSeek receives an explicit JSON/schema instruction while keeping the existing
schema response format. Code fences requested inside JSON strings remain valid.
Parsing, budgets, one-call behaviour and provider security checks are unchanged.
Two retained single-call transport probes passed JSON and local schema checks
when given explicit instructions. Neither probe produced or qualified a paper.

The V36-v2 print policy puts a code-first question's number before its code and
uses shared bounded graph geometry for admission, rendering and vector checks.
Enlarged node names and weights use 14-point text. Reciprocal directed edges
have separate routes and labels. A route must clear unrelated node circles.
Unsupported congestion is refused without shrinking text or rewriting content.
Historical V36-v1 and earlier rendering paths remain available.

## Review scope

The root reviewer read the complete new graph geometry and graph PDF validator,
and the integrated source/test diffs. The rendering reviewer read rendering.py
and llm_pdf.py completely before implementing and reviewing the scoped changes.
Earlier complete-file pipeline, runtime and provider reviews remain in
`hosted-and-french-full-file-review-2026-10-30.md`; this review covers their new
diffs. No claim of a complete new review of every test or project file is made.

Integrated focused checks passed 197 tests. The rendering reviewer also passed
257 focused checks and strict geometry typing. Four normal and five enlarged
historical fixture pages were pixel-identical to their retained originals.
Twenty-six current fixture pages and detailed diagrams were visually reviewed.
Root review independently identified the unrelated-node obstruction before its
regression test and fix. Full release checks remain separate.

## Source identities

| File | SHA-256 |
| --- | --- |
| Backend/Core/france/graph_layout.py | fa414aefc8852861aed2e39d9d85e9240a1fa428f3537518862cbbf26a4f3132 |
| Backend/Core/france/graph_pdf.py | 5b6e54d4c947af5bb14fae1552ece967c08053875622ad3658237a3434520e54 |
| Backend/Core/france/rendering.py | c3b4b3f7e66e2bfef7f623fdda65b7e0f02f3688aff10f4d719064f4b889bfbf |
| Backend/Core/france/llm_pdf.py | d56ef78f277425c8cbfc4c51060f24a39afe3505bb359e5c9dc154ca9e2ba085 |
| Backend/Core/france/llm_pipeline.py | f0322eb03ab0575a3af35743b505ec945096f20ff18c9c9fe22280b9faaa69e2 |
| Backend/Core/france/llm_runtime.py | 0a3aa2e2bfbd33600cd07f3e97cd2f21bd72c38c4deab3353f4898e8c1eb7d78 |
| Backend/Core/providers.py | 0fc2319463fa786f824a7186aaf6ffd76b74b845ea7467b4b6d8304f4269e181 |
| Backend/Core/france/print_policy.py | 1860e63a1307f34fd60004bd51012327753ba6022ff9b3e8b2104e0a7673e7b1 |
| macOS/Keldin/Domain/FrenchLLMAssessmentRequest.swift | 99aaa34da392e6e29d634c88770baa8fe958410253c9f749762dbf7387029600 |

No complete current model-generated French paper has passed qualification.
Reasoning, marking, variety and every printed page still need evaluation on a
fresh public run. Teacher review and empirical calibration remain not run.
