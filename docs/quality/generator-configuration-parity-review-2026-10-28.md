# Advertised generator configuration parity

## Reproduced gap

The local backend bootstrap installed only Edexcel Economics and AQA Computer
Science, while the registry advertises seven UK generator roots. Accounting,
Business, OCR Computer Science, AQA Economics and OCR Economics were omitted.
Business and OCR Computer Science declare Pydantic >=2.9 and ReportLab >=4.2;
the two previously installed projects permit >=2.0 and >=4.0. The local setup
therefore did not enforce every advertised family's dependency requirements.
This finding does not assert that the current, newer installed versions failed
at runtime.

Backend CI already installed all seven projects. The pytest import and test
collection paths, conftest working-directory routing and subprocess PYTHONPATH
also covered all seven. Packaging already derives its generator paths, modules
and syllabuses from the registry. The experimental eighth family is not
advertised and is outside this parity contract.

## Repair and checks

The bootstrap now passes all seven editable projects to the existing pip
installation alongside `requirements-build.txt`. No dependency ranges,
provider settings or runtime installation policy changed. A registry expansion
will fail the parity test until the installation and test configurations are
updated. This small check avoids a release-time rewrite of every root list.

The regression executes a copied bootstrap inside a temporary repository with
spaces in its path. Fake Python, venv and pip commands record arguments only.
It never modifies the real environment or accesses the network. Before repair,
the run failed because five editable projects were missing; the other three
configuration checks passed. After repair, all four tests pass.

The other checks compare CI editable roots and pytest import/collection paths
with the advertised registry set. A fake conftest request and recorder exercise
working-directory and PYTHONPATH routing for each family without changing the
test process's directory or environment. These are configuration checks, not
evidence of a fresh dependency installation, frozen bundle acceptance, live
generation or paper quality.

Evidence is retained in `tmp/generator-configuration-parity-red.log` and
`tmp/generator-configuration-parity-green.log`. Bash syntax and Ruff checks pass.
The full suite, real bootstrap, signed builds and protected publication were
not run for this scoped repair.
