# Assessment Reliability Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the contract-first, item-transaction, evidence-validation, and checkpoint foundation needed to make all supported AI-generated papers correct, resumable, and independently reviewable.

**Architecture:** Extend the existing Pydantic blueprint models with typed immutable contracts while preserving compatibility with family generators. Replace position-sensitive numeric checks with role-aware validation, generate/review/repair one item transaction at a time, and persist accepted items in a versioned checkpoint store that can rehydrate the paper before rendering.

**Tech Stack:** Python 3.11+, Pydantic 2, pytest, JSON checkpoints, existing `Backend.Core` generation protocol

**Spec:** `docs/superpowers/specs/2026-08-23-contract-first-paper-generation-design.md`

## Global Constraints

- AI owns original contexts, question prose, and reasoning; deterministic code owns marks, AO allocations, numeric data, calculations, graph geometry, evidence references, and release checks.
- Existing preview generation and all seven registered generator entry points must remain operational during migration.
- Accepted items must survive retries and process restarts without reusing an invalid model response.
- Official questions, wording, logos, and claims of endorsement must not be copied.
- Work stays on `main`; commits are local unless the user requests a push.
- Every behavior change starts with a failing regression test.
- Run `graphify update .` after source changes and commit resulting graph artifacts with the relevant phase.

## File Structure

- Create `Backend/Core/assessment_contracts.py`: typed numeric, evidence, graph, and item contracts plus compatibility hydration from `GeneratedQuestion.authoring_context`.
- Create `Backend/Core/assessment_checkpoints.py`: atomic, versioned item checkpoint persistence and paper rehydration.
- Modify `Backend/Core/assessment_quality.py`: role-aware numeric extraction/comparison and evidence-bound marking validation.
- Modify `Backend/Core/exam_blueprints.py`: attach a typed contract to each generated question and validate its immutable assessment metadata.
- Modify `Backend/Core/ai_assessment.py`: item-scoped generation, validation, independent review, repair, checkpoint, and resume orchestration.
- Modify `Backend/Core/model_review.py`: return structured review diagnostics and enforce review independence.
- Modify `Backend/Core/events.py`: emit stable stage, item, attempt, and progress metadata.
- Modify `Backend/Core/generation.py`: create a durable job checkpoint location and pass it to compatible generators.
- Modify the seven AI family generator entry points under `Resources/*/*/generator/*/cli.py`: accept and forward the checkpoint store without changing their published output roles.
- Test in `tests/test_assessment_contracts.py`, `tests/test_assessment_checkpoints.py`, `tests/test_ai_assessment.py`, `tests/test_exam_blueprints.py`, `tests/test_app_backend.py`, and affected family test modules.

---

### Task 1: Typed Item Contracts

**Files:**
- Create: `Backend/Core/assessment_contracts.py`
- Modify: `Backend/Core/exam_blueprints.py`
- Create: `tests/test_assessment_contracts.py`
- Modify: `tests/test_exam_blueprints.py`

**Interfaces:**
- Consumes: existing `GeneratedQuestion.authoring_context`, marks, AO allocation, prompt, and `source_references`.
- Produces: `NumericRole`, `NumericValueContract`, `GeneratedNumericField`, `EvidenceRecord`, `GraphContract`, `AssessmentContract`, and `contract_for_question(question: GeneratedQuestion) -> AssessmentContract`.

- [ ] **Step 1: Write failing compatibility and validation tests**

```python
from Backend.Core.assessment_contracts import (
    AssessmentContract,
    EvidenceRecord,
    GeneratedNumericField,
    NumericRole,
    NumericValueContract,
    contract_for_question,
)
from Backend.Core.exam_blueprints import GeneratedQuestion


def test_legacy_question_hydrates_a_contract_without_mutation() -> None:
    question = GeneratedQuestion(
        rule_id="q1", number="01", marks=4, kind="calculate",
        command_word="calculate", topic_id="accounting",
        prompt="Calculate contribution when revenue is £225 and variable cost is £169.",
        mark_scheme=["£56"], assessment_objectives={"AO2": 4},
    )
    contract = contract_for_question(question)
    assert contract.item_id == "q1"
    assert contract.marks == 4
    assert [value.text for value in contract.numeric_values] == ["£225", "£169"]
    assert all(value.role is NumericRole.ASSESSMENT_DATA for value in contract.numeric_values)


def test_contract_rejects_generated_field_outside_declared_range() -> None:
    field = GeneratedNumericField(name="equilibrium_price", minimum=10, maximum=80)
    assert field.validate_value(45) == 45
    with pytest.raises(ValueError, match="equilibrium_price"):
        field.validate_value(95)


def test_contract_rejects_unknown_evidence_reference() -> None:
    contract = AssessmentContract(
        item_id="q1", marks=4, assessment_objectives={"AO2": 4},
        evidence=[EvidenceRecord(id="extract-a", text="Exports rose by 4%.")],
        allowed_evidence_ids={"extract-a"},
    )
    with pytest.raises(ValueError, match="unknown evidence"):
        contract.validate_evidence_ids(["extract-b"])
```

- [ ] **Step 2: Run the focused tests and confirm missing-module failures**

Run: `.venv/bin/pytest tests/test_assessment_contracts.py tests/test_exam_blueprints.py -q`

Expected: collection fails because `Backend.Core.assessment_contracts` does not exist.

- [ ] **Step 3: Implement immutable Pydantic contracts and legacy hydration**

```python
class NumericRole(StrEnum):
    ASSESSMENT_DATA = "assessment_data"
    MARK = "mark"
    DATE = "date"
    ITEM_IDENTIFIER = "item_identifier"
    DISPLAY_LABEL = "display_label"
    CODE_LINE_LABEL = "code_line_label"


class NumericValueContract(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str = Field(min_length=1)
    role: NumericRole = NumericRole.ASSESSMENT_DATA
    ordered: bool = False


class GeneratedNumericField(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str = Field(min_length=1)
    minimum: float
    maximum: float

    def validate_value(self, value: float) -> float:
        if not self.minimum <= value <= self.maximum:
            raise ValueError(f"{self.name} must be between {self.minimum} and {self.maximum}")
        return value


class AssessmentContract(BaseModel):
    model_config = ConfigDict(frozen=True)
    item_id: str
    marks: int = Field(gt=0)
    assessment_objectives: dict[str, int]
    numeric_values: list[NumericValueContract] = Field(default_factory=list)
    generated_numeric_fields: list[GeneratedNumericField] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    allowed_evidence_ids: set[str] = Field(default_factory=set)
    graph: GraphContract | None = None

    def validate_evidence_ids(self, references: Iterable[str]) -> None:
        unknown = set(references) - self.allowed_evidence_ids
        if unknown:
            raise ValueError(f"{self.item_id} cites unknown evidence: {sorted(unknown)}")
```

Add `contract: AssessmentContract | None = None` to `GeneratedQuestion`, with a forward-safe import from `assessment_contracts`. `contract_for_question` returns the explicit contract when present and otherwise hydrates assessment-data values from the existing prompt and evidence IDs from `source_references`.

- [ ] **Step 4: Run focused tests**

Run: `.venv/bin/pytest tests/test_assessment_contracts.py tests/test_exam_blueprints.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the typed contract foundation**

```bash
git add Backend/Core/assessment_contracts.py Backend/Core/exam_blueprints.py tests/test_assessment_contracts.py tests/test_exam_blueprints.py
git commit -m "Add typed assessment item contracts"
```

### Task 2: Role-Aware Numeric and Evidence Validation

**Files:**
- Modify: `Backend/Core/assessment_quality.py`
- Modify: `Backend/Core/model_review.py`
- Modify: `tests/test_assessment_contracts.py`
- Modify: `tests/test_ai_assessment.py`

**Interfaces:**
- Consumes: `AssessmentContract`, original prompt, candidate prompt, candidate evidence IDs.
- Produces: `validate_candidate_contract(original: str, candidate: str, contract: AssessmentContract, generated_values: Mapping[str, float] | None = None) -> None` and `ReviewResult`.

- [ ] **Step 1: Add regressions for the four numeric failure modes**

```python
def test_unordered_assessment_values_compare_as_a_multiset() -> None:
    contract = contract_with_values("55", "5%")
    validate_candidate_contract("55 then 5%", "5% follows 55", contract)


def test_code_line_labels_are_not_assessment_values() -> None:
    contract = contract_with_values("225")
    validate_candidate_contract("01 total = 225", "07 total = 225", contract)


def test_changed_immutable_value_is_rejected() -> None:
    contract = contract_with_values("225")
    with pytest.raises(ValueError, match="immutable numeric"):
        validate_candidate_contract("Value 225", "Value 169", contract)


def test_declared_generated_graph_value_is_range_checked() -> None:
    contract = contract_with_generated_field("year", 2024, 2030)
    validate_candidate_contract("Plot the result", "Plot the result for 2027", contract, {"year": 2027})
    with pytest.raises(ValueError, match="year"):
        validate_candidate_contract("Plot the result", "Plot the result for 2038", contract, {"year": 2038})
```

- [ ] **Step 2: Run the new tests and verify position-sensitive behavior fails**

Run: `.venv/bin/pytest tests/test_assessment_contracts.py tests/test_ai_assessment.py -q`

Expected: reordered values and line-label cases fail under the current tuple comparison.

- [ ] **Step 3: Implement role-aware comparison**

```python
def validate_candidate_contract(
    original: str,
    candidate: str,
    contract: AssessmentContract,
    generated_values: Mapping[str, float] | None = None,
) -> None:
    expected = Counter(
        value.text.casefold()
        for value in contract.numeric_values
        if value.role is NumericRole.ASSESSMENT_DATA and not value.ordered
    )
    actual = Counter(_assessment_data_tokens(candidate, contract))
    if actual != expected:
        raise ValueError(
            f"{contract.item_id} changed immutable numeric data: expected {expected}, got {actual}"
        )
    ordered = [value.text.casefold() for value in contract.numeric_values if value.ordered]
    if ordered and not _is_subsequence(ordered, [token.casefold() for token in numeric_tokens(candidate)]):
        raise ValueError(f"{contract.item_id} changed ordered immutable numeric data")
    supplied = generated_values or {}
    for field in contract.generated_numeric_fields:
        if field.name in supplied:
            field.validate_value(float(supplied[field.name]))
```

Classification removes explicit item numbers, bracketed mark labels, source labels, and leading two-digit pseudocode line labels before comparison. Do not discard quantities merely because they resemble years; dates are excluded only when their role is declared.

- [ ] **Step 4: Return structured review diagnostics**

```python
class ReviewResult(BaseModel):
    approved: bool
    factual_issues: list[str] = Field(default_factory=list)
    marking_issues: list[str] = Field(default_factory=list)
    source_issues: list[str] = Field(default_factory=list)
    difficulty_issues: list[str] = Field(default_factory=list)
    ambiguity_issues: list[str] = Field(default_factory=list)

    @property
    def issues(self) -> list[str]:
        return self.factual_issues + self.marking_issues + self.source_issues + self.difficulty_issues + self.ambiguity_issues
```

Change `require_independent_review` to return `ReviewResult`; it still raises when the response schema is invalid, but a valid rejection becomes structured repair input.

- [ ] **Step 5: Run focused and core suites**

Run: `.venv/bin/pytest tests/test_assessment_contracts.py tests/test_ai_assessment.py tests/test_exam_blueprints.py -q`

Expected: PASS.

- [ ] **Step 6: Commit role-aware validation**

```bash
git add Backend/Core/assessment_quality.py Backend/Core/model_review.py tests/test_assessment_contracts.py tests/test_ai_assessment.py
git commit -m "Validate generated items with numeric roles"
```

### Task 3: Item-Scoped Draft, Review, and Repair

**Files:**
- Modify: `Backend/Core/ai_assessment.py`
- Modify: `tests/test_ai_assessment.py`

**Interfaces:**
- Consumes: `AssessmentLLMClient`, `_Task`, `AssessmentContract`, `GenerationPolicy`.
- Produces: `_generate_item_transaction(task, *, client, subject, seed, policy, progress, accepted_prompts) -> GeneratedQuestion` and `_repair_prompt(...) -> str`.

- [ ] **Step 1: Write a test proving one bad item does not regenerate accepted items**

```python
def test_failed_second_item_does_not_regenerate_first_item() -> None:
    client = ScriptedClient([
        response_for("0/0/0", prompt="Explain valid concept A."),
        approved_review("0/0/0"),
        response_for("0/0/1", prompt="Explain invalid concept B."),
        rejected_review("0/0/1", factual_issues=["causal direction is reversed"]),
        response_for("0/0/1", prompt="Explain corrected concept B."),
        approved_review("0/0/1"),
    ])
    result = generate_unique_paper(two_item_paper(), rule=two_item_rule(), syllabus_topics=topics(), syllabus_topic_ids={"a"}, client=client, subject="Economics")
    assert prompts(result) == ["Explain valid concept A.", "Explain corrected concept B."]
    assert client.generation_ids == ["0/0/0", "0/0/1", "0/0/1"]
```

- [ ] **Step 2: Write a test proving repair prompts contain only structured diagnostics**

```python
def test_repair_prompt_targets_rejected_fields() -> None:
    prompt = _repair_prompt(task(), candidate(), ReviewResult(approved=False, source_issues=["claim has no evidence id"]), attempt=2)
    assert "claim has no evidence id" in prompt
    assert '"id": "0/0/0"' in prompt
    assert "other paper items" not in prompt.casefold()
```

- [ ] **Step 3: Run the tests and confirm batch orchestration regenerates work**

Run: `.venv/bin/pytest tests/test_ai_assessment.py -q`

Expected: new item-transaction tests fail because `_generate_item_transaction` and `_repair_prompt` do not exist.

- [ ] **Step 4: Implement the item transaction loop**

```python
def _generate_item_transaction(...):
    failure = ""
    candidate: GeneratedQuestion | None = None
    for attempt in range(1, policy.attempts + 1):
        raw = client.generate_json(
            _generation_prompt([task], subject=subject, seed=seed, attempt=attempt, previous_failure=failure)
            if candidate is None
            else _repair_prompt(task, candidate, review, attempt=attempt)
        )
        candidate = _parse_batch(raw, [task], client=client, policy=policy)[0]
        review = _review_item(task, candidate, client=client, subject=subject)
        if review.approved and not review.issues:
            assert_distinct_items([*accepted_prompts, {"id": task.id, "prompt": candidate.prompt}], threshold=policy.paper_similarity_limit)
            return candidate
        failure = "; ".join(review.issues)
        progress(GenerationUpdate(stage="repair", item_id=task.id, attempt=attempt, message=failure))
    raise RuntimeError(f"{task.id} exhausted {policy.attempts} item attempts: {failure}")
```

Keep remote concurrency by running independent item transactions in the existing executor. Local Ollama runs serially, minimizing context and making retry cost proportional to one item.

- [ ] **Step 5: Add independent-review identity protection**

Hash the canonical candidate and review payload. Reject a review that echoes candidate fields instead of returning the review schema, and require the review prompt to omit withheld draft prose. Preserve the existing similarity guard for replacement text.

- [ ] **Step 6: Run AI and family unit tests**

Run: `.venv/bin/pytest tests/test_ai_assessment.py Resources/economics/edexcel-a/generator/tests/test_ollama_generation.py Resources/computer-science/aqa/generator/tests/test_paper1.py -q`

Expected: PASS.

- [ ] **Step 7: Commit item-scoped repair**

```bash
git add Backend/Core/ai_assessment.py tests/test_ai_assessment.py
git commit -m "Review and repair AI questions individually"
```

### Task 4: Atomic Checkpoints and Resume

**Files:**
- Create: `Backend/Core/assessment_checkpoints.py`
- Create: `tests/test_assessment_checkpoints.py`
- Modify: `Backend/Core/ai_assessment.py`
- Modify: `tests/test_ai_assessment.py`

**Interfaces:**
- Consumes: paper identity, seed, provider, model, prompt version, task key, and accepted `GeneratedQuestion`.
- Produces: `CheckpointIdentity`, `AssessmentCheckpointStore.load_item(key)`, `.save_item(key, question)`, `.clear()`, and `generate_unique_paper(..., checkpoint_store: AssessmentCheckpointStore | None = None)`.

- [ ] **Step 1: Write atomicity and identity tests**

```python
def test_checkpoint_round_trips_an_accepted_question(tmp_path: Path) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    store.save_item("0/0/0", question())
    assert store.load_item("0/0/0") == question()


def test_checkpoint_rejects_model_or_blueprint_mismatch(tmp_path: Path) -> None:
    AssessmentCheckpointStore(tmp_path / "job.json", identity(model="gemma4:12b")).save_item("0/0/0", question())
    with pytest.raises(CheckpointMismatch, match="model"):
        AssessmentCheckpointStore(tmp_path / "job.json", identity(model="other-model"))


def test_checkpoint_write_is_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = AssessmentCheckpointStore(tmp_path / "job.json", identity())
    store.save_item("0/0/0", question())
    assert not list(tmp_path.glob("*.tmp"))
    json.loads((tmp_path / "job.json").read_text())
```

- [ ] **Step 2: Run checkpoint tests and verify missing-module failure**

Run: `.venv/bin/pytest tests/test_assessment_checkpoints.py -q`

Expected: collection fails because `assessment_checkpoints` does not exist.

- [ ] **Step 3: Implement the versioned atomic store**

```python
class CheckpointIdentity(BaseModel):
    schema_version: Literal[1] = 1
    paper_id: str
    seed: int
    provider: str
    model: str
    blueprint_sha256: str
    prompt_version: str


class AssessmentCheckpointStore:
    def save_item(self, key: str, question: GeneratedQuestion) -> None:
        document = self._read_or_empty()
        document["items"][key] = question.model_dump(mode="json")
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def load_item(self, key: str) -> GeneratedQuestion | None:
        raw = self._read_or_empty()["items"].get(key)
        return GeneratedQuestion.model_validate(raw) if raw is not None else None
```

Validate identity field by field and report the mismatched name. Use `os.fsync` before replacement so an accepted item survives abrupt termination.

- [ ] **Step 4: Resume accepted items before model calls**

In `generate_unique_paper`, load each task key. Revalidate the stored item against its current rule and contract; use it only if valid. Save immediately after independent review and before the next item begins.

- [ ] **Step 5: Test resume without repeated calls**

Run: `.venv/bin/pytest tests/test_assessment_checkpoints.py tests/test_ai_assessment.py -q`

Expected: PASS, including a test where a second `generate_unique_paper` call makes zero model requests for already accepted items.

- [ ] **Step 6: Commit checkpoint support**

```bash
git add Backend/Core/assessment_checkpoints.py Backend/Core/ai_assessment.py tests/test_assessment_checkpoints.py tests/test_ai_assessment.py
git commit -m "Checkpoint accepted assessment items"
```

### Task 5: Backend Job Integration and Truthful Progress

**Files:**
- Modify: `Backend/Core/events.py`
- Modify: `Backend/Core/generation.py`
- Modify: `tests/test_app_backend.py`
- Modify: `Resources/accounting/aqa/generator/aqaaccountgen/cli.py`
- Modify: `Resources/business/aqa/generator/aqabizgen/cli.py`
- Modify: `Resources/computer-science/aqa/generator/cspapergen/cli.py`
- Modify: `Resources/computer-science/ocr/generator/ocrcsgen/cli.py`
- Modify: `Resources/economics/aqa/generator/aqaecongen/cli.py`
- Modify: `Resources/economics/ocr/generator/ocregen/cli.py`
- Modify: `Resources/economics/edexcel-a/generator/pastpapergen/cli.py`

**Interfaces:**
- Consumes: optional `checkpoint_store`, item-stage updates, existing JSON event protocol v2.
- Produces: `GenerationUpdate(stage, message, item_id, completed_units, total_units, attempt)` and progress event fields `item_id`, `attempt`, `completed_units`, `total_units`, and monotonic `progress`.

- [ ] **Step 1: Add protocol tests for item progress and persistent checkpoint location**

```python
def test_progress_event_contains_stable_item_units() -> None:
    event = progress_event(GenerationUpdate(stage="review", message="Reviewing", item_id="0/0/2", completed_units=2, total_units=12, attempt=1))
    assert event["progress"] == pytest.approx(2 / 12)
    assert event["item_id"] == "0/0/2"
    assert event["attempt"] == 1


def test_generation_passes_checkpoint_outside_transaction_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured = capture_plugin_arguments(monkeypatch)
    run_generation(tmp_path)
    assert captured["checkpoint_path"].parent == tmp_path / ".papercreator-checkpoints"
```

- [ ] **Step 2: Run backend tests and confirm missing structured-update behavior**

Run: `.venv/bin/pytest tests/test_app_backend.py -q`

Expected: new assertions fail because progress is currently inferred from message regexes.

- [ ] **Step 3: Implement structured progress conversion**

```python
@dataclass(frozen=True)
class GenerationUpdate:
    stage: str
    message: str
    item_id: str | None = None
    completed_units: int = 0
    total_units: int = 1
    attempt: int = 1

    @property
    def progress(self) -> float:
        return max(0.0, min(1.0, self.completed_units / max(self.total_units, 1)))
```

Keep the string callback adapter for legacy generators, but all migrated AI paths emit `GenerationUpdate` directly.

- [ ] **Step 4: Create and pass a stable checkpoint path**

Derive the filename from subject, paper, seed, provider, and model using a SHA-256 suffix. Store it under `<output>/.papercreator-checkpoints/`. Add `checkpoint_path` to `_invoke_plugin` candidate arguments and to each generator entry-point signature. Each family constructs `AssessmentCheckpointStore` using its fully built blueprint hash, then passes it to `generate_unique_paper`.

- [ ] **Step 5: Preserve successful checkpoints on cancellation and remove them after publication**

`handle_generate` deletes a checkpoint only after `finalize_generated_documents` and `emit_generated_files` succeed. Cancellation and generation failure leave it available for resume. Add a `resumed` progress event when at least one item loads.

- [ ] **Step 6: Run backend and all family dry-run tests**

Run: `.venv/bin/pytest tests/test_app_backend.py Resources/*/*/generator/tests -q`

Expected: PASS.

- [ ] **Step 7: Commit job integration**

```bash
git add Backend/Core/events.py Backend/Core/generation.py tests/test_app_backend.py Resources/*/*/generator/*/cli.py
git commit -m "Resume generation with truthful item progress"
```

### Task 6: Observed Subject Regression Contracts

**Files:**
- Modify: `Resources/accounting/aqa/generator/aqaaccountgen/generator.py`
- Modify: `Resources/accounting/aqa/generator/tests/test_aqa_accounting.py`
- Modify: `Resources/economics/aqa/generator/tests/test_aqa_economics.py`
- Modify: `Resources/economics/ocr/generator/tests/test_ocr_economics.py`
- Modify: `Resources/computer-science/ocr/generator/tests/test_ocr_computer_science.py`
- Modify: `Resources/computer-science/aqa/generator/tests/test_paper1.py`
- Modify: `Resources/economics/edexcel-a/generator/tests/test_ollama_generation.py`

**Interfaces:**
- Consumes: typed contracts from Tasks 1-2.
- Produces: explicit immutable/generated numeric roles and evidence IDs for every previously failing item family.

- [ ] **Step 1: Encode the accounting identity regression**

```python
def test_contribution_is_revenue_minus_variable_cost_not_profit() -> None:
    case = build_case_data(seed=123)
    assert case.contribution == case.revenue - case.variable_cost
    assert case.profit == case.contribution - case.fixed_cost
```

- [ ] **Step 2: Encode OCR and AQA numeric-role regressions**

Add family-level tests proving that reordered percentages remain valid, OCR pseudocode labels 01-07 are `code_line_label`, immutable 225 cannot become 169, and AQA Business graph years are declared generated fields rather than prompt invariants.

- [ ] **Step 3: Encode review and evidence regressions**

Add fixtures for the AQA Computer Science assembler ambiguity, identical-draft review, Edexcel unsupported disposable-income/rail/hotel claims, and the exchange-rate appreciation direction. Each fixture must fail contract/review validation before the later items in its paper are generated.

- [ ] **Step 4: Implement the minimal family metadata and formula corrections**

Populate each affected question's explicit `AssessmentContract`. Replace the accounting calculation branch with named values derived from the canonical case-data model. Bind Edexcel source claims to normalized extract IDs. Add deterministic economics causal rules for appreciation/depreciation and import/export price directions.

- [ ] **Step 5: Run affected family suites**

Run: `.venv/bin/pytest Resources/accounting/aqa/generator/tests Resources/economics/aqa/generator/tests Resources/economics/ocr/generator/tests Resources/computer-science/aqa/generator/tests Resources/computer-science/ocr/generator/tests Resources/economics/edexcel-a/generator/tests -q`

Expected: PASS.

- [ ] **Step 6: Commit subject regressions**

```bash
git add Resources/accounting Resources/business Resources/computer-science Resources/economics
git commit -m "Encode subject-specific assessment invariants"
```

### Task 7: Phase Verification, Documentation, and Graph Update

**Files:**
- Modify: `docs/ASSESSMENT_QUALITY.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `graphify-out/*` through `graphify update .`

**Interfaces:**
- Consumes: the complete reliability-core implementation.
- Produces: a documented package/checkpoint lifecycle, updated graph, clean committed worktree, and regression evidence.

- [ ] **Step 1: Run formatting and static repository checks**

Run: `.venv/bin/ruff check Backend Resources tests tools`

Expected: no diagnostics.

- [ ] **Step 2: Run the complete Python test suite**

Run: `.venv/bin/pytest -q`

Expected: all tests pass with no unexpected skip or warning increase.

- [ ] **Step 3: Run macOS backend and release smoke checks**

Run: `make bundle-check && make test-swift && make build-macos-release`

Expected: bundle health is true, Swift tests pass, and the release build succeeds.

- [ ] **Step 4: Document the lifecycle**

Update `docs/ASSESSMENT_QUALITY.md` with numeric roles, evidence binding, review/repair, and checkpoint invalidation. Update `docs/ARCHITECTURE.md` with the transaction sequence: blueprint → contract → item draft → validate → review/repair → checkpoint → package → render.

- [ ] **Step 5: Update Graphify**

Run: `graphify update .`

Expected: AST extraction completes and the graph artifacts reflect new contract and checkpoint nodes.

- [ ] **Step 6: Inspect and commit all phase artifacts**

Run: `git diff --check && git status --short`

Expected: only intended documentation and Graphify artifacts are modified.

```bash
git add docs/ASSESSMENT_QUALITY.md docs/ARCHITECTURE.md graphify-out
git commit -m "Document assessment reliability architecture"
```

- [ ] **Step 7: Verify the handoff is clean**

Run: `git status --short --branch`

Expected: `main` is ahead of `origin/main` and the worktree has no staged or unstaged changes.

## Subsequent Phase Plans

After this foundation passes, create and execute separate plans in this order:

1. Family renderer termination, mark-scheme depth, and page-density contracts.
2. Board document profiles, measured geometry, typography, diagrams, and fidelity thresholds.
3. Native macOS progress/resume UX, accessibility, tutorial, and HIG qualification.
4. Full 18-paper live generation, automated fidelity audit, all-page manual review, cleanup, and final release qualification.

Each later plan argues from the same approved design specification and begins only after its dependency phase is committed and clean.
