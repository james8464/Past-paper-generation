# Read only PDF preview safety

Reviewed on 2 November 2026. Keldin previews generated PDFs and exports their original bytes. It does not save answers entered into a form.

## Confirmed loss boundary

An isolated Swift/PDFKit diagnostic used the actual document controller, PDF access and export code with temporary files and private defaults. Both a small owned form and an owned copy of the generated AQA Computer Science Paper 1 electronic answer document allowed form entry: the document permission was true and its text widgets were not read-only.

Setting a widget value programmatically changed the preview document. Refresh retained that document, while export kept the original blank field. Clearing and reloading the controller discarded the in-memory value. The retained generated EAD, owned source copy and export remained byte-identical, SHA-256 `7967f94d40c15b6ba3f3d0d1b009a7c8220e0ab97884eb740365e05e315d3767`. No canonical user document or visible typing session was involved.

The private diagnostic is `tmp/nov2-pdf-widget-preview-probe.py`; results are in `tmp/nov2-pdf-widget-preview-probe.log` and `tmp/nov2-pdf-widget-preview-actual-ead.log`. It assembled the current implementation with minimal data-model and localization stubs. The export check used the exact original-byte snapshot selected before the Save panel and the actual direct export API, without opening a Save panel.

## Preview behavior

The controller now marks only widget annotations read-only when accepting a new PDF byte revision. It caches whether form fields exist and shows a localized English/French hint directing users to export the PDF to fill it in another app. Page scanning happens when new bytes are accepted, outside SwiftUI body updates. Refreshing unchanged bytes retains the reader document and its page/zoom state; clearing or losing access resets the cached field state.

Existing field values remain unchanged. The original file and export bytes retain their original widget permissions, so an originally editable EAD remains editable externally. Keldin does not save newly entered answers. Non-widget links are untouched, and existing text-selection, scrolling, zoom, Print and Quick Look implementations remain in place.

## Verification

All 19 `PDFDocumentAccessTests` passed with complete strict concurrency and warnings treated as errors. New cases check a prefilled widget's read-only preview flag, retained answer value, unchanged link, exact source/export bytes, external field editability, unchanged-document identity, reset/plain-PDF states and English/French text. The test-only initial fixture type mismatch was corrected before the final red build, which failed for the absent cached-state API. The green log is `tmp/nov2-readonly-preview-green.log`; the final red log is `tmp/nov2-readonly-preview-red-final.log`.

The focused build used only the author's `macOS/build/DerivedData/nov1-output-preflight-native` cache. It did not replace the installed app or accepted release products. No model requests, downloads, full suite, Store build or accessibility tests were performed. Physical typing, the new hint's visual layout and a complete native action journey remain outside this acceptance result.

## File review scope

`macOS/Keldin/Features/Documents/DocumentPreviewView.swift` was freshly read from line 1 through EOF after the change: 354 lines, SHA-256 `c1c2e9b2706bcd82660d8bb328fab30d89bd84513ed2a4c51da88d9b56ed4d09`. No further P1/P2 finding was confirmed in that scope. The 56 added test lines were reviewed and the complete focused test class was executed; this does not attest a new full-file semantic review of every existing test. The change is author commit `948943bc2ec736bc41fb7c18aad7a0942132638d`, based on `17883e18de40675060e22f2a4074db83040248c8`.
