# Offline Occitanie NSI activity

This is a separate, unmarked activity with a proposed correction. It is not a
sixth French paper family, an official exam, an orientation service or evidence
of regional approval. V35 and historical exam packages are unchanged.

## Source and permitted reuse

The [Région Occitanie dataset](https://data.laregion.fr/explore/dataset/lycees-occitanie/)
is titled *Lycées d'Occitanie année scolaire 2025-2026*. Its
[metadata API](https://data.laregion.fr/api/explore/v2.1/catalog/datasets/lycees-occitanie)
identifies Région Occitanie as publisher and Licence Ouverte v2.0 (Etalab) as
the licence. The data update timestamp was `2026-05-12T12:46:56+00:00`, not the
retrieval date, 29 October 2026. The activity explicitly retains this distinction.

The [producer's licence link](https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf)
and [Etalab's licence text](https://github.com/etalab/licence-ouverte/blob/master/LO.md)
permit reuse with attribution and the data's last-update date. Reuse does not
imply endorsement. Both PDFs carry source, producer, update date and licence;
the final page also carries the dataset's upstream attributions.
This clearance concerns this extract only, not the project's other reference
documents or its unresolved corpus-rights questions.

The bundled resource retains twelve explicitly selected public records, three
per commune: Nîmes, Toulouse, Montpellier and Cahors. It omits contacts, pupil
metrics and coordinates. It makes no claim about NSI provision, available
boarding places or regional representativeness. Source spelling and casing are
preserved. Two CLEMENT MAROT records have distinct IDs and boarding flags.
These genuine data properties drive the dictionary-key and case-comparison tasks.

Selection is by the twelve IDs listed in the resource, using the records API's
`codeetab IN (...)`, `order_by=codeetab`, `limit=12` and the eight explicit fields.
The canonical rows-only SHA-256 is
`8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0`.
This is not a hash of the complete regional dataset. The loader pins both rows
and rights metadata. Generation does not contact the API.

## Activity and answer checks

Eight questions cover identifier uniqueness, sample limitations, dictionary
overwrite, case-insensitive matching, Python counting, SELECT/WHERE/ORDER BY,
a two-relation JOIN, and reuse attribution. No GROUP BY, HAVING, LEFT JOIN or
COALESCE is required. Python solutions execute against the actual twelve rows;
the two SQL solutions run in SQLite and are compared with separately computed
Python selections. The index has eleven entries when names are used, twelve
when source IDs are used. Boarding counts are Nîmes 2, TOULOUSE 1, Montpellier 2,
CAHORS 2. The original uppercase Montpellier lookup returns an empty list;
the corrected lookup returns `0340038G`, `0340040J`.

The activity has no exam marks, promised completion time or teacher-validation
claim. Internal checking is not observed learner calibration.

## CLI and publication

`generate-occitanie-case-study --output DIRECTORY` requires no model, seed,
reference index or internet access. It publishes exactly:

- `DIRECTORY/occitanie-nsi-etude-de-cas/occitanie-nsi-activite.pdf`
- `DIRECTORY/occitanie-nsi-etude-de-cas/occitanie-nsi-correction.pdf`

Both files are rendered and checked in a private sibling directory, then that
directory is renamed into place. Existing output refuses without overwriting.
A failed second render publishes neither file. File events use the existing
`question_paper` and `mark_scheme` roles. No JSON file is exported. Native app
integration and frozen-resource inclusion are separate acceptance gates.

## Render review

Retained evidence is under the implementation worktree's
`tmp/pdfs/occitanie-case-study-20261029/`. Run 1 produced two three-page A4 PDFs.
All six pages were rendered with Poppler and visually inspected: tables, source
labels, code indentation, question spacing, query results and footers were
legible, with no clipping or blank page. The worksheet reserves response space;
the correction does not add artificial answer space.

A wording review found that question 4 could imply the original function did
not already accept title-case Montpellier. Run 2 asks for uppercase and
title-case spellings to yield the same result. Both changed page 2s were
freshly inspected. Full-page 100 dpi raster comparison found pages 1 and 3 of
both documents identical to the reviewed run 1. Final SHA-256 values:

- Activity: `d0ec2a4cab394efa754d95292ef96f8c9c78e7358d06ed8692aa2876f9dd8208`
- Correction: `cce3b62cb77aa37fecf6017b121906607aaf97c1ad707ac93426b404be36f541`

Automated checks cover all question headings in order, complete printed code
and queries, A4 bounds, nonempty page bodies, pagination, all twelve worksheet
IDs, provenance, cancellation, existing-output refusal and pair-render failure.
This is source-based activity acceptance, not live AI qualification or a full
native interaction-coverage claim.
