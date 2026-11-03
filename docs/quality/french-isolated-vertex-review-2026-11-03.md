# Declared isolated graph vertices

## Reproduction

An owned graph fixture declares vertices A, B and C, with one undirected edge
A-B of weight 1. The current public V36 admission accepted A-to-B distance 1,
but refused C-to-C distance 0 because the verifier reconstructed vertices from
edge endpoints. C was present in the printed graph. An unknown X-to-X path was
correctly refused.

The same valid self-path failed for directed graphs. Red tests reproduced both
failures with eight passing controls. This is a source-based implementation
finding; no live generated paper is claimed to contain it.

## Repair

Current V36 verification resolves the question's referenced printed graph and
rechecks its type, reference, edges and direction. It supplies the declared
vertices through a trusted keyword argument outside the model-authored contract.
The shortest-path verifier initializes those vertices before adding edges, so
isolated vertices remain present. It rejects malformed vertex context, foreign
edge endpoints and unknown start/end vertices before the existing path search.

The model schema and stored question contracts are unchanged. Model-authored
extra `nodes` cannot replace the printed source. Calls without trusted vertex
context retain historical edge-derived behavior. No question answer, graph or
mark was rewritten.

## Checks and review

The final scoped run passed 159 tests, including 17 new cases. These cover both
graph directions, ordinary and isolated paths, unknown and disconnected
vertices, wrong distances, source divergence, unchanged input/contracts,
historical direct calls and malformed/forged node contexts. An initial new
negative test expected `ValueError` where the unchanged JSON schema correctly
raises its own `ValidationError`; the test now expects that precise exception.
Validation was not changed for it.

`release_gap_audit` independently reviewed the complete production delta and the
new test file, with the earlier verifier EOF review retained. No additional
regression was found. Root subsequently corrected the one exception assertion
and reran the scoped tests. The large LLM pipeline was inspected selectively;
this does not attest an EOF review of that entire file.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Backend/Core/france/verification.py` | 610 | `8326ae4c0b16be7d180eb4409fb5168a52bf5951209725b4b86c619b8997e1e2` |
| `Backend/Core/france/llm_pipeline.py` | 2083 | `e6c3825f79027e4a882c8c40266661ebea9d59144bc92e5db77987bc16749966` |
| `tests/test_french_isolated_graph_vertex.py` | 104 | `75df4f5b0945caf1b98c6c1061fee9c5234562dca42ed6a478110876b9143a83` |

Evidence is retained under `tmp/nov3-isolated-vertex-*`. The full frozen suite,
latest-head protected checks and packaged acceptance remain release gates for
this later source. Earlier PR168 release evidence does not certify this repair.
French full-paper and provider qualification remain open.

Maintained Ruff checks and formatting passed across 623 files. The 39 repository
hygiene and audit tests passed. Graphify's AST-only update completed and warned
that 49 JSON sources produced no graph nodes; graph output is navigation
metadata, not semantic review evidence. The regenerated ledger records 227
reviewed files, 613 pending and 332 excluded. Changed source without a renewed
whole-file attestation remains pending.
