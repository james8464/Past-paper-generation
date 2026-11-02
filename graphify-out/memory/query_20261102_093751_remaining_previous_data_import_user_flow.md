---
type: "query"
date: "2026-11-02T09:37:51.819895+00:00"
question: "Remaining previous-data import user flow"
contributor: "graphify"
outcome: "useful"
source_nodes: [".importData()"]
---

# Q: Remaining previous-data import user flow

## Answer

Expanded from graph vocabulary: import history settings error. At commit 80ccd624, the graph led to KeldinMigration.importData; source inspection confirmed that ApplicationCoordinator.importPreviousAppData calls its synchronous recursive copy from MainActor. Large folder copying can block the UI. This is a source-based finding, not a timed native import or evidence that a later repair passed. No original data was imported or modified. Recheck the current caller and isolation before applying this historical finding to another version.

## Outcome

- Signal: useful

## Source Nodes

- .importData()
