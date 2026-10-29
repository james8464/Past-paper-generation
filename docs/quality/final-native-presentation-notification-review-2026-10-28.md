# Modal commands and notification copy

The parent tested the consolidated `a93ecb86` direct Release and found File >
New Paper and Create Paper enabled behind both Quality Review and the optional
French review sheet. No creation command was invoked. Empty-review Save was
disabled, and Cancel closed the sheet. Observations are retained in primary
`tmp/consolidated-modal-menu-observations-20261028.md`.

## Presentation ownership

The creation context now has a typed `presentingModal` value, derived directly
from the existing view-local sheet/confirmation state. Quality Review uses its
existing `showsQualityReview`; the French workspace uses its existing review,
reference-download consent and reference-deletion presentation state. No second
global copy of those booleans is introduced.

Menu policy also reads the six existing application presentation bindings:
Welcome, Help, error alert, hosted-provider consent, MLX setup confirmation and
model-download confirmation. New/Create, in-app workspace navigation, latest
document preview, Help/Welcome and benchmark-start commands share this policy.
Affected actions check the policy as well as displaying a disabled state.
Selected-document actions retain their access checks. Cancellation remains
available for work already running. Unrelated panes with no creation context
still permit New Paper when no modal is presented.

The normal/enlarged French choice remains owned by its workspace and is
preserved by the context value. Closing a presentation restores the original
context; the change does not persist new identifiers or change paper content.

## Notifications

`WorkNotification` builds finite title/body copy for paper, model download and
MLX start/success/failure events. Copy resolves through the selected application
language, including interpolated folder and model names. All nine events retain
their English wording and have French translations. Caller-provided failure
details remain verbatim, including backend codes, paths and OS diagnostics.

The existing notification setting, system permission request, delivery task,
sound and authorization checks are unchanged. No notification was sent and no
permission, clipboard, credential or user-data change was made during these
tests. Actual system delivery is a separate acceptance check.

## Evidence

- `tmp/final-interface-guards-red.log`: three controlled tests, 20 assertion failures before the policy/copy implementation.
- `tmp/final-interface-guards-green.log`: 89 targeted tests passed: four new policy/copy tests, 55 application tests and 30 run-isolation tests. Strict concurrency and warnings-as-errors were enabled.
- Result bundle: `macOS/build/logs/final-interface-guards-green/test.xcresult`.

Tests exercise modal context blocking/restoration, nil-context navigation,
every existing global binding, all nine English/French notification events and
raw-detail preservation. They do not introspect native menus or claim system
notification delivery. The parent must recheck the actual menus in the signed
final build. No Core changes, live paper qualification, whole-HIG certification,
Store approval or full-suite result is claimed by this scoped pass.
