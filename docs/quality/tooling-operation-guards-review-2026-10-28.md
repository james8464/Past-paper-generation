# Tooling operation guards

This bounded T9/T10 change addresses findings A and B from the second tooling
file review. It does not format the application or change Core/native source.

## T9: process deadlines

`tools/live_process.py` now rejects nonnumeric, Boolean, nonfinite, zero and
negative deadlines before opening output logs or spawning a child. Positive
integer and fractional values retain the existing process-launch behavior.
The French benchmark's floating-point CLI input and live matrix's integer input
both reach this shared boundary. Process-group termination, wait4 ownership,
return codes and backend-only RSS conversion remain unchanged.

## T10: secure calibration modes

`tools/calibrate_student_responses.py` validates operation selection before
loading a review file, key or dataset, and repeats the guard at its secure helper
entry point. Delete/export require an existing dataset ID and are mutually
exclusive. Existing IDs cannot be mixed with import inputs; destructive/export
actions cannot silently ignore aggregation arguments. Secure-only flags require
a secure store, and secure imports require all three import inputs. Secure
metadata supplies family/form identity rather than ignored legacy CLI flags.

Valid deletion, encrypted export, new import and existing aggregation remain
available. Tests use fake stores/keys and synthetic path contents only. No real
student rows, credentials, encrypted stores or model services were accessed.

## Evidence and limits

The initial regression run failed 19 cases and passed six. The red log is
`tmp/tooling-operation-guards-red.log`. The final fake-boundary run passed 27
tests; `tmp/tooling-operation-guards-green.log` records its exact duration. Ruff
and whitespace checks pass. No full suite, application build, source formatter
or live qualification was run. Existing real-process cleanup tests are left for
the parent integration gate; this batch did not execute child processes.

Suggested audit-plan rows: T9, validate finite process deadlines before side
effects, implemented with fake-process regressions; T10, validate secure dataset
operation modes before access, implemented with fake-store regressions. Final
acceptance still requires the coordinated fixed-source gates.
