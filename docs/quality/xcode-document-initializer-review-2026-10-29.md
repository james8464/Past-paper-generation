# Xcode document-controller initializer review

Date: 29 October 2026

The user reported that building the project in Xcode failed. The actual project
in the primary checkout reported a call to the main-actor-isolated
`PDFDocumentAccess` initializer from a synchronous nonisolated default argument
in `DocumentActionController`.

The designated initializer now requires its injected access object. A separate
convenience initializer creates the default object inside the controller's
main-actor isolation. Existing injected test callers keep the same API. This
does not add `nonisolated`, unchecked sendability, or a new concurrency escape.

Computer control invoked Build in the user's actual Xcode project. The report
navigator showed Build succeeded, no issues, on 29 October at 12:29, taking
117.5 seconds. The earlier failed build report was retained. The user's project
settings and other local edits were preserved. The same initializer fix was
then ported to the isolated integration branch.

The reviewer read all of
`macOS/Keldin/Features/Documents/DocumentPreviewView.swift`, including selection
binding, document access, print/export actions and Quick Look handling. The
change is confined to the two initializer declarations. Existing native tests
construct both the default controller and injected access controllers; the
integrated native suite remains a separate acceptance gate.

Reviewed source SHA-256:
`b8487c162f2f1af6626cfdfbaaab7bc510bca31ba7d023596b7c4c51fcef4dc8`.

This report records the observed GUI build and source review. It does not claim
that every document interaction was retested in this build, that the installed
Release app was launched through its canonical path, or that Store approval or
whole-app HIG compliance follows from a successful build.
