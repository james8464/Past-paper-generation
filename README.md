# Past Paper Creation

Subject folders:

- `economics/` - A-Level Economics Edexcel A practice paper generator.
- `computer science/` - AQA A-Level Computer Science Paper 2 practice paper generator.

Each subject keeps its own README, package, tests and data inside its folder.
Generated PDFs go to `~/Downloads`; runtime caches live under `~/Library/Caches/Past Paper Creation/`.

## Economics Quick Start

```bash
cd economics
../.venv/bin/python -m pip install -e ".[dev]"
../.venv/bin/python generate_paper.py
```

## Computer Science Quick Start

```bash
cd "computer science"
../.venv/bin/python -m pip install -e ".[dev]"
../.venv/bin/python generate_cs_paper.py
```

Computer Science outputs:

- `~/Downloads/cs-paper-2-question-paper.pdf`
- `~/Downloads/cs-paper-2-mark-scheme.pdf`
