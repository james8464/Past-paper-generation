---
type: "query"
date: "2026-08-01T16:45:31.852821+00:00"
question: "How is the macOS backend bundle kept complete?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["generator_registry.py", "build_backend.sh", "handle_bundle_check()"]
---

# Q: How is the macOS backend bundle kept complete?

## Answer

The schema-v2 generator registry owns package names, Python roots, entry points, syllabus assets, papers, providers, and outputs. build_backend.sh expands every package file into explicit PyInstaller hidden imports, bundles registry-derived data, and executes bundle-check. bundle-check imports all seven entry points and verifies syllabus assets, causing Xcode to fail before copying an incomplete helper.

## Outcome

- Signal: useful

## Source Nodes

- generator_registry.py
- build_backend.sh
- handle_bundle_check()