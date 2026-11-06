# Response simulation answer projection review

The optional model-backed response simulator removed four top-level marking fields, but left private keys inside nested dictionaries and lists. An owned fake client confirmed that nested part marking, a keyed option and observable mark points reached the diagnostic prompt. No model or network request was needed to reproduce this.

The simulator now uses the existing `without_private_answer_keys` helper for its client prompt. The helper also traverses tuples, which Python's JSON encoder accepts as arrays, while preserving tuple containers in its returned projection. Its private-key set is unchanged, and the simulator does not import the independent solver. Public choices, source observations, assumptions and an ordinary source `credit` field remain available. The input object is unchanged. No JSON round trip is used, so a nonserialisable value under an excluded private key remains harmless.

The no-client path still reads raw observable mark points to construct its synthetic response bands. It is separate from blind model simulation and remains unchanged. The inspected production assessment-package callers use this synthetic path, so this repair addresses a latent API boundary rather than a demonstrated installed-app quality failure.

## Evidence

The initial focused run failed four nested-projection cases and passed three controls. A subsequent tuple review found three further failing controls: direct tuple and mixed tuple/list leaks, and a public-tuple projection containing private keys. The final focused run passed 60 tests across response simulation, the minimal JSON client contract, levels of response, prompt characterisation and accounting public assumptions. Controls cover private canaries, public data and tuple types, unchanged inputs, ignored nonserialisable private values and exact unchanged synthetic responses.

The earlier characterisation required a clean tuple to retain object identity. It now checks equality and tuple type instead: recursive traversal preserves public values and serialisation, but need not return the original tuple object. All preceding private-key, ordinary source-field and input-immutability assertions remain intact. Ruff checking and formatting passed for the four changed Python files. The configured type gate passed its four configured infrastructure files, not a whole-project static audit.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/response_simulation.py` | `e7795aca2be21e2be3c12d651c0db98db04074e415db741371373ae2ceaa1978` |
| `tests/test_response_simulation.py` | `53804ac16ff0b46f5d8877601c367e581c7f9d9fe04812a06b389fc94b2b8502` |
| `Backend/Core/answer_projection.py` | `83eae23215ca81df4453b44519f6ac70e45aed21da8d88d43e9c8ef95613735b` |
| `tests/test_assessment_prompt_characterisation.py` | `cecf98d162766fdd22450ddbff364d648d68a1f90d6f7716535665545bb0b6e1` |

This filter removes known private keys; it is not a whitelist proving that every remaining field is printed for a candidate. The tests establish prompt projection and synthetic-path compatibility, not realistic student responses, empirical calibration, live model quality or factual answer correctness. No paid calls, builds or full-suite acceptance were part of this bounded repair.
