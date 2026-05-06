# Past Paper Creation

Subject folders:

- `economics/` - A-Level Economics Edexcel A practice paper generator.
- `computer science/` - reserved for future Computer Science work.

The Economics project keeps its own README, package, tests and data inside `economics/`.
The `computer science/` folder is intentionally empty apart from `.gitkeep`, so Git can track it.

## Economics Quick Start

```bash
cd economics
../.venv/bin/python -m pip install -e ".[dev]"
../.venv/bin/python generate_paper.py
```

