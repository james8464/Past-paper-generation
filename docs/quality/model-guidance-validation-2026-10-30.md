# Model guidance validation

The backend reader accepted the string `"false"` as a true qualification flag.
It also accepted `true` as schema version 1, `false` as a zero-GB memory limit,
and an infinite boundary between two memory tiers. These errors were reproduced
in 12 failing tests before the parser changed.

The reader now requires an integer schema version, a boolean qualification flag
and finite numeric memory limits. It rejects missing qualification flags and
integers too large to represent as a finite memory boundary. Valid fractional
boundaries and both boolean flag values retain their meaning. The bundled
recommendations, default model and warning copy are unchanged.

The final focused scope passed 42 tests, covering backend recommendations and
the existing native guidance contract. Ruff and a separate scoped mypy check
passed. A read-only second review read the complete parser, changed tests and
current resource and found no further issue. Full regression and protected
release checks are separate requirements. This review does not qualify a model
or complete the whole-project code audit.

## French run 22

The latest paid diagnostic used `deepseek-flash`, seed 270200 and the V36-v3
print policy. Nine calls completed in 512.100 seconds. All three authored
exercises passed initial admission. The final SQL review refused the third
exercise, so the application published no PDFs. Source identity remained
unchanged throughout the run. Retained evidence is under
`tmp/french-v36-live-20261030/deepseek-flash-run-22-fence-v3-270200`.

Internal reviewers first solved the question-only requests, then compared the
proposed corrections. The first stock-reservation exercise had sound answers,
with repeated work between two questions and an uncalibrated duration. In the
second exercise, inserting at the front and removing at the end compensate:
the resulting arrivals are still FIFO. The proposed correction falsely
describes the removal as returning the last planned item, although its own
trace gives the correct arrival order. A separate undo defect and the stated
public representation invariant still make the faulty example usable. The
model review accepted it despite the contradictory explanation.

The third correction adds a city to each volunteer, even though the source
city belongs to the workshop and a volunteer can use workshops in different
cities. It later says city is stored only in the workshop table, contradicting
its proposed schema. The refusal is justified. A valid decomposition can keep
city in Atelier and connect Benevole to Reparation through foreign keys.

No answers were patched, generated code executed, learner timings observed or
teacher records invented. These findings prevent a whole-paper quality pass.
They also show that a model review can miss an incorrect explanation. Any
future bounded re-draft must retain the rejected round and undergo a fresh
solve and review; that workflow is not implemented by this change.
