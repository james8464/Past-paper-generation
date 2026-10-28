# Model guidance and French interface review

Date: 28 October 2026

The model registry still records `validated_for_full_matrix: false` for both
local suggestions. Memory-based selection is not evidence of paper quality.
This change removes claims that a suggested model has sufficient reasoning
capacity, reliably follows every schema, or provides a proven quality level.
It does not change the selected models, context limits, provider behaviour or
generation checks.

The Gemma download estimate is now approximately 8.0 GB, consistent with the
published Ollama tag sizes reviewed on this date. Download size is not runtime
memory use. The display is explicitly approximate, since quantisations and tags
can change. Sources: <https://ollama.com/library/gemma4/tags> and
<https://ollama.com/library/qwen2.5:7b>.

## Checks

- Red tests reproduced unsupported guidance and missing French resource lookup.
- The final native suite passed 102 tests, including both memory tiers, provider
  subtitles, selected-language decimal formatting and fallback registry parity.
- Targeted Python tests check the limits stated in the registry and French
  translations. They do not establish model performance.
- Computer control opened the rebuilt Debug candidate with French selected on
  an English-language Mac. Settings displayed the translated Ollama subtitle
  and `Environ 8,0 Go`. The model guide displayed `Environ 8,0 Go`, `18 Go`, a
  separate context row, translated review limits and readable wrapping.
- System interface language and the Downloads output preference were restored.
  No paper was generated, provider changed, model downloaded or user file removed.

Evidence is retained under ignored `tmp/final-validation-20261028`, including
`model-guidance-locale-native.log` and the earlier red and first-pass logs.
The Store preflight is a personal-development-signing check, not App Store
approval. The complete supported-paper/provider quality matrix remains open.

An existing backend status, `Ollama is available.`, still appears in English
in the French Settings view. This review does not claim complete localisation
or complete interaction coverage.
