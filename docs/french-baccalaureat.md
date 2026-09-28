# French NSI prototype: architecture and operation

The national-framework route is additive. Existing UK `families` and IDs retain
their AO policies and package schema. Registry v5 adds `assessment_frameworks`;
the separate `generate-assessment` command prevents French material being routed
through UK board validation. Shared providers, events, history and render
transactions are reused. This is intentionally not a universal-engine rewrite.

## Data flow

EducationContext + CurriculumVersion + AssessmentDefinition → scoped references →
French NSI exercises → deterministic checks → blind solver → independent review →
hash-bound draft package → French PDF checks → atomic directory publication.

UI language is independent of document language (`fr-FR`). French history records
carry optional education-system/assessment/language metadata; older records without
those fields remain readable. Fractional points are decimal strings. The written
component has 75% weighting in the complete NSI examination, but this app generates
only the written component, not the practical assessment or diploma grade.

## Developer commands

```sh
python -m tools.french_reference_corpus \
  --register Resources/france/nsi/source-register.json \
  --output 'Reference Corpus/france/nsi'

python bridge.py generate-assessment \
  --assessment fr-bac-general-nsi-written-2027 \
  --reference-index 'Reference Corpus/france/nsi/references.sqlite' \
  --provider ollama --model gemma4:12b --seed 26092801 \
  --output tmp/pdfs/french-nsi
```

Do not run model generation while the existing UK qualification controller is
active. `--large-print` selects enlarged type. Remote Ollama requires explicit
`--allow-remote` and HTTPS; the native French workspace uses loopback only.
Reference preparation is online and requires user consent. Generation uses the
installed local model. No fine-tuning occurs. No model download is silently started.

## Storage and privacy

The app stores reference PDFs/index under its Application Support `Paper Creator/
French References` folder. Outputs go to the selected folder (via the app's existing
App Store export path when applicable). Checkpoints and failed attempts are in
`.papercreator-checkpoints` under the output root. Existing history remains local.
Reference requests expose normal network metadata to source hosts. Local Ollama
requests contain source excerpts and generated content; an explicitly selected
remote server receives those too. There is no new telemetry or student-answer
storage. Removing reference data requires re-preparing sources; deleting history
does not necessarily remove exported documents or model files.

## Adding another framework

Add an explicit context and authoritative, dated curriculum/assessment definition;
provide a separate policy and registry entry. Implement scoped references, native
prompts, exact scoring and content verification before exposing a UI route. Reuse
low-level services, never another country's grading assumptions. Unknown policies
fail closed. Add compatibility, cross-scope, failure, language and artifact tests.
Keep framework qualification independent from technical availability.

## Current limitations

See `occitanie-project.md` and `quality/french-nsi-evaluation.md`. The seed corpus,
initial equal-weight blueprint, restricted verifier and provisional renderer are
not the completed qualification programme. Native structured diagrams/tables,
complete corpus reconciliation, calibrated originality, full interface translation,
benchmark matrix and teacher/pilot evidence remain explicit work items. A generated
draft is not automatically suitable for classroom assessment.
