# French question-review advisory boundary

Internal engineering follow-up, 30 October 2026. This is not paper qualification.

The baseline full-file review is recorded in `hosted-and-french-full-file-review-2026-10-30.md` at pipeline SHA-256 `29f81375b79c230791059059436fd4f80c9e0bcb2bd6d7deee540073f8a1638d`. The subsequent complete source diff and its regression cases were reviewed. The final `Backend/Core/france/llm_pipeline.py` SHA-256 is `333121cdefe6752b7a8d64e5a0166c9dfa796139f675d18ab884497aa3085d67`.

A live response placed explicitly nonblocking grammar and terminology comments in the blocking `issues` channel. The app correctly refused that response under its existing contract. The contract lacked a separate place for optional question-level advice.

New live review schemas require `advisories` for every question: at most three nonblank strings of at most 600 characters each. The prompt restricts these to optional form/style suggestions that do not affect correctness, necessary data, curriculum or credit. Every existing `issues` entry and negative Boolean still refuses, including an issue whose prose says "Non bloquant". No text is parsed to infer severity, and no old failed issue is moved to the advisory channel.

Saved legacy reviews retain their strict original schema when all advisory fields are absent. A present advisory field selects the complete new shape; partial or malformed additions refuse. Warnings are recomputed in source question order with actual question identifiers. Removing or altering warnings without matching retained review evidence refuses package validation. The independent blind-note adjudication is unchanged.

The initial new tests produced 21 failures before implementation. The agent's fixed-source focused suite passed 174 tests, including live/stored rejection, legacy replay, warning tampering, runtime/PDF cases and actual structured-output schema compilation with and without blind notes. Final integrated regression and protected CI remain separate gates.

The live draft that motivated the channel remains refused and unqualified. Independent review also found an insufficient minimum-route justification credited by its rubric. A numerical shortest-path check does not prove that explanation. Neither the response nor the generated answer was patched.
