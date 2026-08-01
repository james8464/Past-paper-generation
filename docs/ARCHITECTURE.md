# Architecture

## Product boundary

Paper Creator produces independently authored, unofficial A-level practice
packages. It treats assessment design and visual composition as separate
problems: an immutable paper blueprint controls what must be assessed, AI writes
new content inside that blueprint, validators reject unsafe output, and
board-specific renderers project the validated model into PDFs.

```text
macOS task
  → JSONL bridge
  → registry-selected family generator
  → immutable specification blueprint
  → provider adapter
  → constrained AI draft
  → independent AI review
  → assessment + originality validation
  → board renderer
  → PDF geometry + typography validation
  → atomic package publication
```

No normal generation path publishes a template question, a partially generated
paper, or an unvalidated PDF. Preview mode is explicitly a layout preview and is
not release output.

## Repository map

```text
Backend/Core/
  ai_assessment.py          shared generation and review orchestration
  assessment_package.py     renderer-independent assessment artifact
  assessment_quality.py     fingerprints and duplicate/exposure checks
  exam_blueprints.py        shared immutable assessment schema
  generation.py             transaction, validation, manifest, publication
  pdf_validation.py         PDF release and typography checks
  providers.py              hosted/local provider boundary
  psychometrics.py          exact-form response-data calibration

Resources/
  generator-registry.json   canonical capability and output registry
  layout-profiles.json      derived visual tolerances
  <subject>/<board>/
    generator/
      <package>/             family blueprint, renderer, and CLI
      data/                  syllabus and derived calibration data

macOS/PaperCreator/
  Application/              app entry point, commands, configuration
  Components/               reusable native views and view styles
  Domain/                   value types and generation estimates
  Features/                 generation, benchmark, settings, onboarding
  Navigation/               split-view and sidebar composition
  Services/                 backend process and Keychain access
  State/                    observable app state and task coordination

tests/                      cross-family protocol and quality tests
tools/                      corpus, fidelity, calibration, and release tools
graphify-out/               token-efficient architectural graph
```

The Xcode target uses a file-system-synchronised root group, so the feature
folders are the build structure as well as the Finder structure.

## Canonical registry

`Resources/generator-registry.json` is the only advertised-family registry. It
owns:

- app and backend subject IDs;
- Python package and entry point;
- syllabus path;
- supported papers and providers;
- required output roles;
- evidence gates.

The backend dispatcher, macOS capability model, bundle script, and tests all
consume this record. Adding a family requires a registry entry and conforming
entry point, not another hard-coded dispatch branch.

The bundle script expands every registry package into explicit PyInstaller
hidden imports. Its internal `bundle-check` command then imports all declared
entry points and verifies every syllabus asset inside the completed helper.
The Xcode build fails before copying the helper if that health check fails.

## Package transaction

Each generation is written to an output-local hidden staging directory. Before
publication:

1. declared roles must exactly match the registry;
2. the assessment JSON must match the request, provider, model, marks, and
   fingerprints;
3. every normal-mode question must pass within-paper and output-history
   similarity thresholds;
4. every PDF must pass metadata, page-box, font, placement, image-resolution,
   and role-specific typography checks;
5. the package manifest records hashes and evidence.

Only after all checks pass does `os.replace` atomically move every artifact into
the selected folder. A failure removes staging output and leaves no partial
paper.

## Trust boundaries

- Provider credentials remain in macOS Keychain and are passed to the child
  process only for the selected provider.
- Hosted prompt transmission requires explicit consent.
- Provider URLs are validated and response bodies are size-bounded.
- Model output is untrusted structured data: Pydantic models and independent
  validation own marks, identities, and publication.
- Official PDFs remain in the ignored development corpus. Shipped layout
  profiles contain derived numeric measurements, not official question text.

## Extension contract

A family entry point returns `dict[str, Path]` and must include at least
`question_paper`, `mark_scheme`, and `assessment_package`. It accepts the
registry-dispatched paper ID, output directory, seed, preview flag, and the
selected provider client. Family renderers may add source booklets or practical
support files, but cannot weaken shared release validation.
