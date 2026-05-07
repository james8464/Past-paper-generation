# Computer Science Paper Generator

Unofficial AQA A-level Computer Science 7517 Paper 2 practice paper generator.

Run:

```bash
cd "computer science"
../.venv/bin/python generate_cs_paper.py
```

Outputs:

- `~/Downloads/cs-paper-2-question-paper.pdf`
- `~/Downloads/cs-paper-2-mark-scheme.pdf`

The generator uses the AQA Paper 2 syllabus seed in `data/syllabus_seed.json` and caches local notes from `/Users/james/Downloads/CS Notes` into `data/notes/` when run. Cached PDFs/text are ignored by git.

By default, no seed means a fresh random paper each run. The blueprint validator keeps generated questions inside AQA Paper 2 spec topics 4.5-4.12.

The runner applies an AQA Paper 2 template-overlay pass using local reference PDFs from `/Users/james/Downloads/CS paper 2` when available, or cached reference templates in `data/templates/reference/`.
