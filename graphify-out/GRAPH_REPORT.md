# Graph Report - .  (2026-05-12)

## Corpus Check
- 114 files · ~136,773 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 35 nodes · 45 edges · 5 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `economics/pastpapergen/cli.py` - 5 edges
2. `computer science/cspapergen/cli.py` - 5 edges
3. `app_bridge/generation.py` - 5 edges
4. `app_bridge/providers.py` - 4 edges
5. `app_bridge/cli.py` - 3 edges
6. `a-levels/catalog.json` - 2 edges
7. `app_bridge/ollama.py` - 2 edges
8. `app_bridge/preview.py` - 2 edges
9. `mac app/Tests/AppTests.swift` - 2 edges
10. `app_bridge/events.py` - 1 edges

## Surprising Connections (you probably didn't know these)
- `app_bridge/generation.py` ----> `economics/pastpapergen/cli.py`  [EXTRACTED]
  app_bridge/generation.py → economics/pastpapergen/cli.py
- `app_bridge/generation.py` ----> `computer science/cspapergen/cli.py`  [EXTRACTED]
  app_bridge/generation.py → computer science/cspapergen/cli.py
- `economics/pastpapergen/cli.py` ----> `app_bridge/providers.py`  [EXTRACTED]
  economics/pastpapergen/cli.py → app_bridge/providers.py
- `computer science/cspapergen/cli.py` ----> `app_bridge/providers.py`  [EXTRACTED]
  computer science/cspapergen/cli.py → app_bridge/providers.py
- `app_bridge/cli.py` ----> `app_bridge/generation.py`  [EXTRACTED]
  app_bridge/cli.py → app_bridge/generation.py

## Communities

### Community 0 - "Python"
Cohesion: 0.22
Nodes (10): Anthropic provider, app_bridge/providers.py, CS blueprint/builders, computer science/cspapergen/cli.py, CS PDF renderers, ~/Downloads output, economics blueprint/builders, economics/pastpapergen/cli.py (+2 more)

### Community 1 - "Resource Catalog"
Cohesion: 0.25
Nodes (8): a-levels resource catalog, app_bridge package, a-levels/catalog.json, computer science package, a-levels/computer-science/aqa, economics package, a-levels/economics/edexcel-a, Past Paper Creation repo

### Community 2 - "SwiftUI App"
Cohesion: 0.46
Nodes (2): mac app/PastPaperCreator, mac app/Tests/AppTests.swift

### Community 3 - "Python"
Cohesion: 0.4
Nodes (4): app_bridge/cli.py, app_bridge/ollama.py, Ollama local model, tests/test_app_backend.py

### Community 4 - "Backend Bridge"
Cohesion: 0.5
Nodes (4): app_bridge/events.py, app_bridge/generation.py, app_bridge/preview.py, ~/Library/Caches/Past Paper Creation

## Knowledge Gaps
- **2 isolated node(s):** `app_bridge/events.py`, `tests/test_app_backend.py`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `app_bridge/cli.py` connect `Python` to `Backend Bridge`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `app_bridge/generation.py` connect `Backend Bridge` to `Python`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `economics/pastpapergen/cli.py` connect `Python` to `Python`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `app_bridge/events.py`, `tests/test_app_backend.py` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._