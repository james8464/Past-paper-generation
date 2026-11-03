# Economics stimulus figure repair

## Confirmed defects

The merged 164 frozen offline Paper 2 preview placed a Laffer curve under a development-economics poverty-trap question. Its tax-rate and tax-revenue axes did not represent the declared stimulus. Source review found other aliases drawing unrelated models: price controls used tax/subsidy shifts, an import tariff used a domestic tax, monopsony used competitive labour curves, money and foreign-exchange markets used generic axes, and demand/supply shifts used unchanged curves. These were renderer defects, not evidence that a model had supplied a bad answer.

The shared competitive labour helper also marked employment 100 and wage 14 although its supply curve passed through wage 17.5 at that employment. Its repair is kept in a separate source commit. Both curves now pass through the requested equilibrium, with finite geometry checked before creating axes. Dimensionless construction avoids intermediate overflow for balanced large values. Exact numerical ticks and offset symbolic labels preserve the public 24/120 adapter example without collisions.

## Bounded repair

The Edexcel-specific module supplies the declared models using the existing PNG renderer contract and shared style. The development poverty cycle links low income, savings, investment and productivity. Price controls distinguish binding and non-binding limits. The tariff shows world and landed prices and the changing import gap without shifting domestic supply. Monopsony distinguishes ACL, MCL and MRP. Money supply is vertical; foreign-exchange axes describe sterling and dollars per pound. Shift diagrams contain different curves.

Supplied numeric parameters are labelled. Unsupported or nonrepresentable geometry refuses rather than drawing another model. The public source projection keeps the requested parameters and adds the numbers actually printed, including visible defaults. It does not add private marking points or computed answers. Original blueprint facts, marks and source fingerprints are unchanged. The adapter prompt identity advances from v10 to v11 so a review of an old wrong figure is not reused. The old checkpoint remains readable with its original identity and bytes; it is not deleted or rebound.

## Evidence and review

Owned baseline tests reproduced the wrong aliases and labour equilibrium. The later review controls reproduced 11 failures involving exact labels, description extras, extreme arithmetic and collisions (`tmp/nov3-stimulus-review-followup-red.log`). Four further projection controls failed before the printed-default fix (`tmp/nov3-stimulus-printed-values-red.log`). The final focused run passed 66 tests in 8.75 seconds. The broader Edexcel and shared-source/checkpoint run passed 474 tests in 80.82 seconds, with five existing PyMuPDF deprecation warnings (`tmp/nov3-economics-stimulus-reviewed-final-broad.log`). Whole maintained-Python Ruff check and format check passed, including the new files. Local resource, shared graph and adapter import paths were asserted to avoid testing an editable primary checkout by mistake. Earlier unpinned attempts remain retained but are not current acceptance evidence.

Owned samples are under `tmp/pdfs/nov3-economics-stimulus-review/run-5`. The 13 diagrams have visual coverage: four changed/new samples were freshly inspected and the other nine are pixel-identical to the previously inspected run 4. `followup-comparison.json` also confirms all 36 question-paper page words, boxes and rasters match run 4. The earlier baseline comparison isolates the original poverty-figure change to page 8; the other 35 pages are identical. The original frozen assessment SHA-256 remains `7a7713b599606bff7b2c20267ac762ce96995f7b2d3cf8734bf666f8a18d9c77`. These samples are current-source QA renders of original frozen facts, not a new frozen executable run or live AI qualification.

The author read the complete new module, both new test files and the 196-line CLI through EOF. Renderer dispatch/public projection and the shared labour function were reviewed as bounded changes; the remaining 4,153-line renderer and 880-line shared graph file are not claimed as complete-file reviews. Two independent reviewers and the root reviewer cleared the final scoped changes. The 39 audit/inventory hygiene tests passed. AST-only Graphify update completed with 49 zero-node source warnings and changed community labels; no semantic relabelling or API call was performed. Full-suite, native/build and protected checks remain release gates after this source freeze.

| Complete-file scope | Lines | SHA-256 |
| --- | ---: | --- |
| `Resources/economics/edexcel-a/generator/pastpapergen/stimulus_diagrams.py` | 424 | `c4a1ceaed6fc15fc27642edad6f93b8ea8b46c558d26932e26ee78ed508fd809` |
| `Resources/economics/edexcel-a/generator/pastpapergen/cli.py` | 196 | `13e65d063b577fa32e108169c7d101d3a8a8b2ec4cb290085ab93637cc1164cb` |
| `Resources/economics/edexcel-a/generator/tests/test_stimulus_diagrams.py` | 468 | `b230e3cbccd105fbdae7106e72ae8f6eacb45a301f969f0c5df6f694aae62443` |
| `tests/test_labour_graph_geometry.py` | 89 | `64ca3210ea7ac6e367a90d2517e2721d7208d5971f18a767dbddfbd5b852a7b5` |

## Curriculum boundary

The [Pearson Economics A qualification and specification](https://qualifications.pearson.com/en/qualifications/edexcel-a-levels/economics-a-2015.html) informed the model distinctions. The development cycle is consistent with the savings/investment mechanism discussed in [World Bank research on poverty traps](https://documents1.worldbank.org/curated/en/455841468313750427/pdf/wps3631.pdf). These are app-owned illustrative models, not copied official question figures. No official PDF is bundled. This repair does not qualify a paper's difficulty, duration, model answers or every possible numerical configuration, and is not teacher or examiner approval.
