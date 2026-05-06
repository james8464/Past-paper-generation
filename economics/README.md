# Past Paper Generator

Unofficial A-Level Economics A practice paper generator for Pearson Edexcel-style papers.

## Run

```bash
cd economics
../.venv/bin/python -m pip install -e ".[dev]"
../.venv/bin/python generate_paper.py
```

Outputs:

```txt
~/Downloads/paper-1-question-paper.pdf
~/Downloads/paper-1-source-booklet.pdf
~/Downloads/paper-1-mark-scheme.pdf
```

## Ollama

```bash
ollama pull qwen2.5:14b
cd economics
../.venv/bin/python -m pastpapergen --paper paper_1 --seed 123 --model qwen2.5:14b
```

`--paper` accepts `1`, `2`, `3`, `paper_1`, `paper_2`, or `paper_3`.
By default, CLI output also goes to `~/Downloads`.

## Paper Structures

- Paper 1: Themes 1 and 3; Section A = 5 questions / 25 marks; Section B = 5, 8, 12, 10, 15; Section C = choice of two 25-mark essays.
- Paper 2: Themes 2 and 4; same section split as Paper 1.
- Paper 3: Themes 1-4; Section A and Section B each contain 5, 8, 12, and a choice of two 25-mark essays.

Command-word rules are encoded for Ollama prompts:

- 5 marks: explain
- 8 marks: examine
- 10 marks: assess
- 12 marks: discuss
- 15 marks: discuss
- 25 marks: evaluate

## Source Material Needed

The runtime uses:

- `data/syllabus_seed.json`
- extracted note text in `data/notes/text`
- local Ollama, unless `--dry-run` is used

## Tests

```bash
cd economics
PYTHONPATH=. ../.venv/bin/pytest -q
```
