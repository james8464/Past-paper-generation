# Originality report isolation and bounded source reviews

The originality screen returned its live module-level threshold dictionary in
each evidence report. An owned caller could mutate that report and change both
later reports and the thresholds used by subsequent screening. No production
caller performing that mutation was found. This was a latent shared-state
admission fault, not evidence that a delivered paper passed with relaxed checks.

Root reproduced two failing controls and one passing control against the old
implementation. The one-line repair returns `dict(THRESHOLDS)`. Threshold values,
calibration identifier, normalization, similarity algorithms and repeat-practice
selection policy are unchanged. Existing serialized report values are unchanged;
there is no policy-version bump or historical-record rewrite. The three new
tests isolate their mutable module state and check independent snapshots,
unchanged later copy refusal, and serialization. Sixteen focused originality
and provider tests passed; after an assertion-order cleanup, the final six
originality tests passed. Ruff checking and formatting passed. These are owned
offline controls, not a new live paper or provider qualification.

The full 154-line originality implementation and 54-line existing regression
file were reviewed by the Accounting audit agent and root. The independent
French reviewer also read both and the complete 53-line new test file. Scoped
history callers retain the twenty-entry, 100,000-character history admission
bound and the explicit repeat-practice policy. This review does not establish a
copyright guarantee, exhaustive similarity detection or a worst-case runtime
bound for every admitted string.

Additional unchanged-file reviews are recorded here with their actual readers.
The French reviewer read the complete network file and provider regression file, and the complete
inline-prose implementation and tests. Inline-policy renderer and source-stream
consumers were inspected only in scope: literal historical policies and opaque
fenced code remain distinct from explicitly enabled inline formatting. Root read
the complete Economics source factory and CLI at the already reviewed versioned
descriptor/checkpoint repair. These are attributed EOF receipts, not a claim
that the metadata integrator repeated those source reads. No network, provider,
compiler, library or display implementation was changed by this batch.

| Reviewed file | Lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/france/originality.py` | 154 | `81eda6245f73c1b2e2ca8a12b58b3901623349a4ab908f88d074860ac5f0dccc` |
| `tests/test_french_originality.py` | 54 | `458fdea7b6ab3b621fbf66d677d76e1294ecf25e6341d010451b76edbefd2247` |
| `tests/test_french_originality_report_isolation.py` | 53 | `a791db86a680fc84a77c95606a51100fbecd5a782831c795934b1d07a3fe526d` |
| `Backend/Core/france/network.py` | 58 | `bb376ccf77fb34ca224580fed098c5f92fd056c898524d0759208eb9094256bd` |
| `tests/test_french_provider.py` | 243 | `51513a6e400a6ef911e6186031cb566fbe43ca084166068c2c638dc69dd136dc` |
| `Backend/Core/france/inline_prose.py` | 142 | `3e9ccb844ad0ce5aaf89698d11e189335c1e8d42efb4ff0c6cbf04d299619ccb` |
| `tests/test_french_inline_prose.py` | 311 | `c4b10b70529f3a1f9cec96b5cf84d25bd676b2ede5fce4a3a52f6858e75d9fd7` |
| `Resources/economics/edexcel-a/generator/pastpapergen/assessment_contracts.py` | 490 | `0156884ec5ed9901a6827049a4659ad33be37c8bf2b46d222217f97fc6425207` |
| `Resources/economics/edexcel-a/generator/pastpapergen/cli.py` | 199 | `374059c42734c524682fca2a3f48699b31f8a1f77442fe6775a5ee56927f4a4d` |

The inline and factory/CLI receipts are retained privately as
`tmp/nov6-french-inline-eof-review.json` and
`tmp/nov6-economics-factory-cli-eof-review.json`. Existing library dependencies,
remote consent, source accuracy, rights, question semantics, learner timing and
complete project coverage are not certified by these reviews. Full frozen
tests, compiled products, protected checks and installed-app acceptance remain
separate release gates. No models, paid calls, GUI or new release build was used
to prepare this note or its metadata.
