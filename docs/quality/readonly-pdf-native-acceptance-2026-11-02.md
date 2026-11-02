# Native read-only PDF acceptance

Root operated a disposable native app on 2 November 2026, following the earlier code/unit review in `readonly-pdf-preview-review-2026-11-02.md`. That earlier evidence remains unchanged.

The test app compiled the unchanged production preview, picker, PDF access and localization code with the actual English/French catalogue. Only document metadata, an empty history coordinator, a test window and language/show-preview controls were stubbed. This exercised the production reader and action implementation, not the installed app's history integration or Store sandbox.

Production preview SHA-256: `c1c2e9b2706bcd82660d8bb328fab30d89bd84513ed2a4c51da88d9b56ed4d09`.
PDF access SHA-256: `046381db27116bb145129a79ba6a6f5b0e8c4ad6a481b4a8d9658754a129970b`.

## Observations

The English and French read-only notices were visually readable. Clicking the answer area and typing `READONLY42` did not enter an answer; the native response widget was disabled. An earlier attempt containing spaces scrolled PDFKit rather than focusing a form field and was not counted as successful field focus. Export used the production Save panel and produced an exact original-byte copy, SHA-256 `7967f94d40c15b6ba3f3d0d1b009a7c8220e0ab97884eb740365e05e315d3767`.

Preview opened that export. Explicitly navigating to page 2, clicking the visible box and typing `EXTERNAL42` populated question 1.1. Native Save persisted it, and closing/reopening that PDF through Open Recent visibly retained the answer. An independent field read confirmed `question_1_1 = EXTERNAL42`. Its edited export hash was `1affe8aa9f530c5ea022fc22774029300b733660a19a428870c71bfcd6ea0e8a`; the owned source retained its original hash. Earlier AX-target attempts had not focused the field and were not counted as successful external entry. The user's pre-existing Preview tab was preserved.

Removing and recreating the production preview reloaded the original document and read-only notice. Cmd-P opened the print panel with All 40 Pages selected, then Cancel closed it without printing. Quick Look opened the original source and Escape closed it. The disposable app was quit normally. No canonical history, user PDF, model call or installed-app preference was changed.

## Limits and retained evidence

The retained harness, build log and detailed observations are under `tmp/nov2-readonly-native/`, including `native-acceptance.md`. This closes the bounded native typing, notice, export and external save/reopen checks. It does not certify every document action, printed output, whole-app interaction coverage, paper quality or accessibility.

The owned EAD is a retained layout-preview fixture, not a newly qualified paper. Its old `[1 marks]` labels are not a current-source defect: a separate fresh seed270100 EAD render passed the existing renderer regression and contained twenty `[1 mark]` labels and zero `[1 marks]`. That fresh diagnostic is retained under `tmp/nov2-current-ead-label-audit-pytest/`; no renderer repair was needed.
