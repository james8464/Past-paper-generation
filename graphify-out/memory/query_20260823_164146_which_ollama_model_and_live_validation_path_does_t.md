---
type: "query"
date: "2026-08-23T16:41:46.668091+00:00"
question: "Which Ollama model and live validation path does the project use for all supported papers?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["live_generation_matrix.py", "OllamaModelRecommendation", "default_ollama_model()", "matrix_jobs()"]
---

# Q: Which Ollama model and live validation path does the project use for all supported papers?

## Answer

Expanded from original query via vocab: [generation, live, matrix, model, models, ollama, paper, papers, provider, recommendation, validation]. Resources/ollama-model-recommendations.json selects gemma4:12b for Macs with at least 16 GB and qwen2.5:7b as the tighter-memory compatibility tier. tools/live_generation_matrix.py derives all 18 jobs from the registry and verifies declared roles. The prior 2026-08-22 gemma4:12b live matrix passed only 3/18, so a fresh post-fix full live run is required.

## Outcome

- Signal: useful

## Source Nodes

- live_generation_matrix.py
- OllamaModelRecommendation
- default_ollama_model()
- matrix_jobs()