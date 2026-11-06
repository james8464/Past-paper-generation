# Assessment helper boundaries

## Scope and review attribution

The subject-helper reviewer read the six subject files listed below through EOF
at their original hashes, along with the existing Mathematics, Essay, Computer
Science and science tests. Root read the original Mathematics and Essay files,
their complete repair deltas and the new helper tests. An independent reviewer read the current 365-line
Mathematics file, the current 115-line Essay file and both complete new test
files. The unchanged Biology, Chemistry and Computer Science files retain the
hashes from the subject-helper reviewer's EOF receipt.

For psychometrics, root read the original 558-line module through EOF. The
author, root and independent reviewer subsequently reviewed the two-line saved
policy check and its complete 138-line test module. This is a review of the
original file plus its exact delta; it is not a claim that root reread all 560
current lines. Root also read the complete existing 147-line psychometrics tests.

The native configuration review covered seven complete files, totalling 179
lines. It used selected project, signing-script, privacy-check and tint callsites
as context. Those callers were not all read through EOF. Existing source-bound
audit entries and exclusions retain their previous evidence and attribution.

## Repairs and owned checks

Significant-figure rounding now reserves one coefficient digit for a carry such
as 9.99 rounding to 10, then adjusts the final quantum when that carry moves the
significant-digit boundary. Nonfinite inputs and invalid significant-figure
counts receive controlled refusals. The helper preserves the caller's context and
uses its rounding mode. It still inherits exponent limits and traps; this change
does not promise unrestricted, context-independent Decimal arithmetic.

Mathematical comparison computes a complex difference's magnitude before
converting that magnitude to Decimal, with explicit finite-value checks. The
tests cover equal complex expressions and supported finite magnitudes within
and outside tolerance. They do not establish correctness for all SymPy inputs
or add an unrestricted symbolic resource guarantee.

Essay validation checks the marks type before comparing an extended-response
tariff. Truthy strings, containers and other invalid mark types now return
diagnostics instead of raising a comparison error. Valid integer tariffs retain
the existing level-policy requirement.

The calibration reader now requires the saved `policy_approved` value to be the
same Boolean as the current policy's computed approval. A synthetic report with
a draft policy, rewritten checks and a recomputed fingerprint previously returned
verified. That contradiction now refuses. Consistent draft and retired policies
remain readable as unverified; a consistent synthetic approved-policy control
remains readable. The fixtures contain no real learner or reviewer records.
The fingerprint remains an unkeyed content hash and cannot authenticate external
approval or empirical truth.

Before repair, the helper tests produced 18 failures and 10 passing controls;
their final Mathematics, Essay and helper group passed 54 tests. The calibration
tests produced 16 failures and six passing controls; their final policy,
psychometrics and calibration-store group passed 46 tests. These are separate
focused runs, not a claim of 100 distinct tests or a full-suite result.

These are latent shared-plugin and helper API defects. Registry discovery does
not demonstrate that the current native generation routes call them. The typed
Computer Science contract solver does reach independent solving and OCR source
templates; this review found no new defect within its bounded source scope.
No model prompts, answers, numeric policy values, schemes or generation features
were changed for these repairs.

## Native configuration observations

The reviewed plist, entitlement and accent files agree with the selected build
configuration. Store parent permissions cover selected-file access, client
networking and printing; its helpers use sandbox inheritance. The Direct
entitlement dictionary is empty. The inspected files contain no library-validation
or unsigned-executable exception. These are source observations, not a new
OS-enforcement or signature test.

The privacy manifest declares tracking as disabled and supplies the required
reason categories expected by the maintained preflight. Its scoped runtime
calls were inspected, without a complete third-party privacy audit or a fresh
check of Apple's current reason-code policy. AccentColor and ControlAccent have
different documented roles in scene tint and filled controls. This review adds
no screenshot, contrast, accessibility, full HIG or Store approval claim.

## Source-bound receipts

Current source files:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/subjects/biology.py` | 71 | `d234cde687241c09b1c5825a8788b04081059002fa8d136292dd683c465bc680` |
| `Backend/Core/subjects/chemistry.py` | 153 | `da68092ec5af9ba3e0ce8404b5dc8186b5119d2389e1cbacfdd2bef049d88ee4` |
| `Backend/Core/subjects/computer_science.py` | 230 | `b477b0bcec748bcd1462a96964cd048b3e3eba4cb7ea30d6a696fcc79730cbd8` |
| `Backend/Core/subjects/computer_science_contracts.py` | 319 | `ba73d680f5694fa30d4bd6c425b8a2317a35f43dede08e1361cf65232ed5e205` |
| `Backend/Core/subjects/mathematics.py` | 365 | `7a2cdee367f1c1ae84c3a3fdee1b207143330bcad8a094285b0b42038127d71c` |
| `Backend/Core/subjects/essay.py` | 115 | `0880cb347c42110f2730eee766c909d6b0f713c4aa9476c509e6bf15ac74ccde` |
| `Backend/Core/psychometrics.py` | 560 | `19d9d10a1800fae0ee4977d03acfab9e237bf04d78a37169ee0c04ec7af4da5f` |

Complete test files covered by these receipts:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `tests/test_subject_helper_guards.py` | 108 | `023ce3cb963ba948b7eaa4fb1474ee39a324956ffc0b051f5c47778346497709` |
| `tests/test_calibration_policy_consistency.py` | 138 | `4218252e8c5a770040e819711d75dbcfba16eaf9883714d535f4e56001958049` |
| `tests/test_mathematics_subject.py` | 150 | `c696ec5544308d9cd0a0a70cd24c97e5eb125cd97a5bd6ed87fa04a5ec7da95f` |
| `tests/test_essay_subjects.py` | 98 | `1d55d2e1deb0a572f6b1450c73db3d7b4f4aef5ddde2bec116ceafecfa38a75f` |
| `tests/test_computer_science_subject.py` | 98 | `c3deffe498199bde771c6d06d8d02e390467142a0ca8713c7f10a2e97188342c` |
| `tests/test_psychometrics.py` | 147 | `c3fbb202b15cf02a1e01dd2f443a757e69669449eab1392eb7f4d6d4c4f3d999` |

The existing science-test audit entry remains attached to its earlier Physics
review; its 133-line source hash remains
`558a6858b93ab7895a78f5129147e73106e213680cabc53d9114b1711cbea68a`.

Complete native configuration files:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/Info.plist` | 38 | `4f40f5ec5a8b0c522cdb7171119e522b02f39fdfeb4842968eb73e2429115b99` |
| `macOS/Keldin/Keldin.entitlements` | 14 | `6ae30bd536ecacb350f27657502803317237808167450e53fd71224b15e74439` |
| `macOS/Keldin/KeldinBackend.entitlements` | 10 | `d33a02772c2336042341aa6684614d931cf3d8f00a15a25594d0d919e4f2019f` |
| `macOS/Keldin/KeldinDirect.entitlements` | 6 | `8dbc2ce9bca7bb3db32a1006c72ea859d9838ff71a28c3c28a35d2c7f292b23c` |
| `macOS/Keldin/PrivacyInfo.xcprivacy` | 52 | `9c9ce5579039f740314be0525ab2e7b4f283064ba4b4b9673e8185cf91088dab` |
| `macOS/Keldin/Assets.xcassets/AccentColor.colorset/Contents.json` | 39 | `277705fd066f1993b212e95456d38e63d9a07cc4ef500fc1a17b08c239dfec5c` |
| `macOS/Keldin/Assets.xcassets/ControlAccent.colorset/Contents.json` | 20 | `4bbe0b314e2a34834b3fd0b3e12e8e181d8b6596e27d378c57d028b9fbacb95a` |

Ignored audit receipts and focused logs retain the detailed source traces.
Graph and inventory refreshes record file relationships and coverage only.
They do not certify all dependencies, generated paper quality, learner timing,
external reviews, distribution readiness or a complete project audit.
