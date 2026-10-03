# French Baccalauréat implementation

Approved specification: the user's complete 2026-09-28 French Baccalauréat
extension and Occitanie pilot plan in this task. Mac-first, Terminale NSI written
session 2027; preserve all UK behaviour. No fine-tuning, student accounts,
Windows/web client, cloud fallback, or claims of teacher approval.

## Global constraints

- Work in the isolated `french-baccalaureat` worktree. Main's live UK matrix
  remains untouched; no model job while that controller is active.
- Programme 2019 and assessment rules 2027 are separate identities. Three
  independent exercises, 210 minutes, 18 technical + 2 language points; all
  detailed marking remains indicative. Written component only.
- All sources carry scope, rights, hash and document category. Holdouts never
  enter retrieval. No UK fallback. No unsupported quality gate can pass.
- Original questions, French authoring and independent practice branding.
- Tests first; update Graphify/inventory; protected PR workflow, no baseline merge.

## Task 1: Education context and scoped reference catalogue

Implement frozen education/curriculum/assessment/source records, exact decimal
points and SQLite scoped full-text retrieval. Reject incomplete/mixed scope,
unknown versions, unreviewed rights and holdout retrieval. Add source register,
corpus ingestion CLI and a reproducible holdout assignment. Tests cover isolation,
hash identity, malformed metadata, decimal scoring and missing evidence.

## Task 2: French NSI assessment pipeline

Native French exercise schema, curriculum mapping, constrained blueprint,
generation/independent solving/quality review, bounded deterministic verification,
originality, hash-bound evidence and checkpoint identity. Never execute arbitrary
model code. Preserve failures and distinguish preview/unreviewed/validated.

## Task 3: Integration and French PDF rendering

Add framework policy hooks at registry, family adapter and package/publication
boundaries without changing UK policies. French package schema, standard and
large-print PDFs, measured layout profiles, language metadata and atomic output.
Tests: old package readers, route preservation, printed credit, Unicode, clipping,
checkpoint/cancellation/failure behaviour and no partial publication.

## Task 4: Teacher-facing macOS workflow

Education-system selection, neutral programme metadata, French localisation,
independent UI/document language, review provenance and hash-bound approval.
Retain existing route IDs, favourites and saved history. Tutorial and local model
guidance; UI/Swift tests, accessibility and build checks.

## Task 5: Evidence, evaluation and delivery

Official corpus reconciliation, layout measurements, 30 exercise benchmark tasks,
10 selected-model papers, six-paper two-teacher rubric, offline/privacy audit,
compatibility inventory, Occitanie status document, budget/roadmap/application.
Model runs wait for the UK controller; hardware and teachers not available are
explicit external gates, never simulated results. Full tests, branch review,
Graphify/inventory, commits and PR. No merge during active UK baseline.

## Verification

Run focused tests RED then GREEN per behaviour and the full pytest suite per
completed task. Build/test macOS after UI changes. Qualification evidence binds
source, prompt, corpus, model and artifacts. Automated success is not educational
approval. Teacher recruitment and organiser eligibility confirmation need people.
