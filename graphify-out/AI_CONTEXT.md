# AI Context: Economics Past Paper Generator

Start here to save tokens:

- `graphify-out/graph.json`: GraphRAG-ready architecture graph.
- `graphify-out/graph.html`: interactive map.
- `graphify-out/GRAPH_REPORT.md`: plain-English architecture summary.

Critical flow:
`generate_paper.py` -> `pastpapergen.cli.generate_package` -> `generator.build_paper_blueprint` -> optional `ollama_client.generate_questions_with_ollama` -> `validation.validate_blueprint` -> `render_pdf` outputs.

Important constraints:
- Unseeded runs use random 64-bit seeds and write seed to audit.
- Section B/C essay topics use `notes.essay_capable_topic_ids` to avoid shallow essay topics.
- Uploaded notes live in `data/notes/pdf` and `data/notes/text`.
- Ollama prompts include syllabus points plus note snippets.
- Mark schemes include question focus, source evidence, and note-derived answer points.
