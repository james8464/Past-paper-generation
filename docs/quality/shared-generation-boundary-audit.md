# Shared generation boundary audit

This is a bounded source review, not a whole-project audit or proof of live paper
quality. The files below were read through EOF at the listed source hashes.
The first three were reviewed by root; the remaining three by the independent
shared-module reviewer. Relevant callers were inspected without claiming their
complete files had received a new review.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/france/graph_pdf.py` | 198 | `5b6e54d4c947af5bb14fae1552ece967c08053875622ad3658237a3434520e54` |
| `Backend/Core/france/question_review.py` | 201 | `fd7bcde5a56e51ae8b59f08999305b3dfc9c312dd28e269e2557fc66aab813de` |
| `Backend/Core/france/source_identity.py` | 29 | `b0696388dafd9e43702a37cadfa7602916c1293f63af0949f1e9003a308a5ead` |
| `Backend/Core/mark_scheme_front_matter.py` | 128 | `33126b6f1232ba1d01ef775fb859394d943397c185ee827268fe88c951c80c33` |
| `Backend/Core/ocr_scheme_content.py` | 190 | `fe9af01297f6cee8ecdbe8e9de343eec6c6acdd8cccd2262af4739e0ad9bc956` |
| `Backend/Core/subject_plugins.py` | 119 | `58d5480336582153f8511f87410732a1c26e92d8d7ceb7e226a0eff79e359fde` |

No actionable deterministic fault was established in these six files. The graph
validator checks source-bound vector endpoints, directions and label placement;
it does not certify arbitrary raster visibility. Question alignment requires
complete ordered item evidence and strict approval fields. Its caller separately
binds the candidate view, so this helper is not a stand-alone semantic certificate.
Implementation identity includes actual source or frozen executable bytes and
French resource JSON, rather than trusting a version label alone.

Shared front matter keeps common guidance separate from per-question content.
OCR scheme content binds assessed items and question-specific credit roles, not
factual truth by itself. Subject plugins provide schema/discovery contracts,
not a guarantee that generated answers are correct.

The separate response-simulation review records the concrete nested-private-key
finding and its repair. Synthetic diagnostic responses are not observed student
responses. None of this work establishes teacher approval, learner calibration,
official-paper equivalence, full interaction coverage or distribution approval.
