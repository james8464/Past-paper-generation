# Project Graph

```mermaid
flowchart TD
  repo["Past Paper Creation"]
  repo --> app["mac app / SwiftUI"]
  repo --> bridge["app_backend.py + app_bridge"]
  repo --> econ["economics generator"]
  repo --> cs["computer science generator"]
  repo --> packs["a-levels resource packs"]

  app --> content["ContentView.swift
NavigationSplitView + catalog UI"]
  app --> vm["AppViewModel.swift
state + generation control"]
  app --> client["BackendClient.swift
subprocess JSONL stream"]
  app --> models["AppModels.swift
subjects, boards, papers, events"]
  app --> style["NativeVisualStyle.swift
material/glass/panels"]
  app --> secrets["SecretStore.swift
Keychain API keys"]

  content --> vm
  content --> models
  content --> style
  vm --> client
  vm --> secrets
  client --> shim["app_backend.py"]

  shim --> cli["app_bridge/cli.py"]
  cli --> gen["app_bridge/generation.py"]
  cli --> ol["app_bridge/ollama.py"]
  gen --> events["app_bridge/events.py"]
  gen --> preview["app_bridge/preview.py"]
  gen --> providers["app_bridge/providers.py"]

  ol --> ollama["Ollama local models"]
  providers --> openai["OpenAI API"]
  providers --> anthropic["Anthropic API"]

  gen --> econ_cli["pastpapergen.generate_package"]
  gen --> cs_cli["cspapergen.generate_package"]
  econ_cli --> econ_pdf["QP + source booklet + MS PDFs"]
  cs_cli --> cs_pdf["QP + MS PDFs"]
  econ_pdf --> downloads["~/Downloads"]
  cs_pdf --> downloads
  preview --> cache["~/Library/Caches/Past Paper Creation"]

  packs --> catalog["a-levels/catalog.json"]
  packs --> econ_pack["economics/edexcel-a"]
  packs --> cs_pack["computer-science/aqa"]
  packs --> placeholders["placeholder subject/board folders"]

  tests["tests"] --> shim
  swift_tests["mac app/Tests"] --> app
```

## Token-Saving Context

- UI source of truth: `mac app/PastPaperCreator/AppModels.swift` catalog.
- App command path: `ContentView` -> `AppViewModel` -> `BackendClient` -> `app_backend.py` -> `app_bridge/cli.py`.
- Generation path: `app_bridge/generation.py` -> subject `generate_package()` -> PDFs -> previews.
- Ready generators: Economics Edexcel A papers 1/2/3; Computer Science AQA Paper 2.
- Placeholders live under `a-levels/<subject>/<board>/{syllabus,past-papers,mark-schemes,notes,templates}`.
- Default local model provider: Ollama. Optional hosted providers: OpenAI/Anthropic.
