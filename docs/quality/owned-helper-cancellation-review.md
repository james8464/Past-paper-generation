# Normal cancellation owns its helper

Normal Cancel previously sent only a graceful termination request. A helper
that ignored it could remain running after the interface released the job.
Apple MLX setup retained ownership until exit and could instead remain in its
cancelling state. App Quit already had a separate escalation path.

An owned shell fixture installed an ignored TERM handler before reporting ready.
The normal-cancel regression executed one test and failed its completion and
process-exit checks after 3.578 seconds. Its replacement process stayed running.
The fixture cleanup used the existing owned shutdown path.

The backend protocol now exposes cancellation. Production clients route it
through their own lifecycle registry. The registry sends TERM immediately and
waits asynchronously for about one second before forcing only the same
registered, still-running object. The interface does not wait. No process
group, shared model service, discovered PID or replacement job is targeted.
Cancellation does not close the launch gate.

The focused lifecycle and run-isolation group passed 92 tests. The real stubborn
helper completed cancellation in 1.285 seconds. A subsequent 80-test isolation
run included two additional spies proving that generation and benchmark Cancel
dispatch through the owning backend, once per run. Graceful exit, completed and
unregistered processes, and completion before escalation have separate controls.
These are scoped measurements, not a hard real-time guarantee.

Independent review found no actionable defect in the production delta. It
covered the complete lifecycle and client/benchmark context, plus the exact
generation-coordinator cancellation path. It was not a fresh whole-file review
of the large application coordinator. Prior full-file attestations remain
separate evidence. Root reviewed every production and test delta.

| Production file | SHA256 |
| --- | --- |
| `BackendClient.swift` | `f034036a21539f3cab054d24ca90619c19a4db183b9228e1d3a372708dccd655` |
| `BackendProcessLifecycle.swift` | `bd7328d56be9e49432428164dc2be4223240b216efb847d6d1675412204994e0` |
| `ApplicationCoordinator.swift` | `3f65a459a72747b9dc3eb90c4bce8332eff7d2918a5ed483bfc87b437b5de892` |
| `BenchmarkCoordinator.swift` | `d0c7de495d4906e7544f6a888446717fdea51703c0634fcbd4c396e4c2b64167` |

Evidence: `tmp/nov5-cancel-red-final.log`, `tmp/nov5-cancel-green.log` and
`tmp/nov5-cancel-routing.log`, with their retained XCTest results. Tests used an
isolated home and ad-hoc Debug signing, without changing real preferences.

This repair does not diagnose the earlier memory incident, stop arbitrary
descendant processes, or claim that cancelling a remote request stops billing.
Release signing, complete tests and installed-app acceptance remain separate
gates.
