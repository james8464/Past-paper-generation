import copy

import pytest

from Backend.Core.independent_solver import IndependentSolver, reconcile_solution

ANSWER = "Machine instructions are held in main memory. The CPU fetches and executes them in sequence."
ADVICE = {
    "score": 1,
    "description": "Mentioning memory but failing to explain why this is significant.",
}
# Verbatim solver response from the exploratory (not commit-qualified)
# tmp/task7e-cpu-live-probe.json. Frozen here so tests need no private QA files.
CAPTURED_CPU_RESPONSE = {
    "steps": [
        "Identify the core definition of the 'stored program' concept within computer architecture.",
        "Describe how instructions (code) and data are treated identically by the hardware.",
        "Explain that both programs and data are stored in the same memory space (RAM).",
        "Conclude that this allows the CPU to fetch and execute instructions sequentially without needing manual reconfiguration for different tasks.",
    ],
    "answer": "The stored program concept is the principle where both the program instructions and the data they operate on are stored in the same memory (RAM). This allows the Central Processing Unit (CPU) to treat code as data, enabling it to fetch, decode, and execute instructions sequentially from memory. Because the machine does not need to be physically rewired or manually reprogrammed to perform different tasks, it can switch between functions simply by loading different sets of instructions into memory.",
    "mark_points": [
        "Both instructions and data are stored in the same memory location/space.",
        "Allows the CPU to process any instruction stored in memory automatically.",
    ],
    "evidence_ids": [],
    "alternatives": [],
    "partial_credit_boundaries": [
        {
            "score": 1,
            "description": "Mentioning that both data and instructions are kept in memory, but failing to explain how the CPU interacts with them or why this is significant.",
        }
    ],
    "follow_through_rules": [],
}

# Verbatim semantic response shape from the frozen seed-26083134 live capture.
# The semantic content is retained as evidence, but the missing ordered
# ``criteria`` envelope must remain invalid rather than being repaired.
FLATTENED_LIVE_SEMANTIC_RESPONSE = {
    "instructions-main-memory": {
        "decision": "supported",
        "answer_quote": "both program instructions and data are stored in the same memory space.",
        "scheme_quote": "Machine-code instructions are stored in main memory",
        "point_index": 0,
        "marks": 1,
    },
    "serial-processor-execution": {
        "decision": "supported",
        "answer_quote": "the CPU can fetch and execute instructions as needed.",
        "scheme_quote": "The processor fetches and executes the instructions serially / in sequence",
        "point_index": 1,
        "marks": 1,
    },
    "issues": [],
    "advisory_conflicts": [],
}

# Verbatim answer and semantic response from the source-verified round-2 live
# transaction in tmp/task7j2-cpu-live-probe-0901.json. The model's supported
# decision for the second criterion is the false positive under regression.
ROUND2_LIVE_ANSWER = (
    "The stored program concept is the principle where both program instructions "
    "and data are stored in the same memory space. Because they are stored "
    "together, the CPU can fetch and execute instructions as needed. This allows "
    "a computer to switch between different tasks or functions by loading "
    "different sets of instructions into memory."
)
ROUND2_LIVE_SEMANTIC_RESPONSE = {
    "criteria": [
        {
            "criterion_id": "instructions-main-memory",
            "decision": "supported",
            "answer_quote": "both program instructions and data are stored in the same memory space",
            "scheme_quote": "Machine-code instructions are stored in main memory",
            "point_index": 0,
            "marks": 1,
        },
        {
            "criterion_id": "serial-processor-execution",
            "decision": "supported",
            "answer_quote": "the CPU can fetch and execute instructions as needed",
            "scheme_quote": "The processor fetches and executes the instructions serially / in sequence",
            "point_index": 1,
            "marks": 1,
        },
    ],
    "issues": [],
    "advisory_conflicts": [],
}


class ReplaySolver:
    def __init__(self, *, exact_response=None, **updates):
        self.prompts = []
        self.response = (
            copy.deepcopy(exact_response)
            if exact_response is not None
            else {
                "answer": ANSWER,
                "steps": ["Recall storage and execution."],
                "mark_points": [
                    "Instructions in memory",
                    "Processor fetches instructions",
                ],
                "evidence_ids": [],
                "alternatives": [],
                "partial_credit_boundaries": [ADVICE],
                "follow_through_rules": [],
                **updates,
            }
        )

    def generate_json(self, prompt):
        self.prompts.append(prompt)
        return copy.deepcopy(self.response)


def open_item(**context):
    return {
        "id": "cpu",
        "marks": 2,
        "prompt": "Explain the stored program concept.",
        "authoring_context": context,
    }


def scheme():
    return {"marks": 2, "mark_scheme": [ANSWER]}


def test_model_partial_commentary_is_not_a_compulsory_extra_obligation():
    solution = IndependentSolver(ReplaySolver()).solve(
        open_item(partial_credit_boundaries=[]), []
    )
    result = reconcile_solution(solution, scheme())
    assert result.passed, result.issues
    rule = solution.credit_rules[0]
    assert (rule.origin, rule.score, rule.text, rule.raw) == (
        "model-advisory",
        1,
        ADVICE["description"],
        ADVICE,
    )
    assert solution.partial_credit_boundaries == []


def test_open_model_alternatives_and_followthrough_remain_nonexhaustive_advice():
    solution = IndependentSolver(
        ReplaySolver(
            alternatives=["Develop a medium-switching-cost argument."],
            follow_through_rules=["Require an additional significance explanation."],
        )
    ).solve(open_item(), [])
    assert reconcile_solution(solution, scheme()).passed
    assert {r.kind for r in solution.credit_rules} == {
        "alternatives",
        "partial_credit_boundaries",
        "follow_through_rules",
    }


def test_declared_method_only_cap_and_dependencies_are_retained_and_mandatory():
    rule = {
        "condition": "Correct method but incorrect final result",
        "score": 1,
        "cap": 1,
        "dependencies": ["method"],
        "id": "method-only",
    }
    solution = IndependentSolver(ReplaySolver(partial_credit_boundaries=[])).solve(
        open_item(partial_credit_boundaries=[rule]), []
    )
    typed = solution.credit_rules[0]
    assert (typed.origin, typed.score, typed.cap, typed.dependencies) == (
        "source-declared",
        1,
        1,
        ["method"],
    )
    assert not reconcile_solution(solution, scheme()).passed
    full = {**scheme(), "partial_credit_boundaries": [rule]}
    assert reconcile_solution(solution, full).passed
    full["partial_credit_boundaries"] = [{**rule, "cap": 2}]
    assert not reconcile_solution(solution, full).passed
    full["partial_credit_boundaries"] = [rule, {**rule, "cap": 2}]
    assert not reconcile_solution(solution, full).passed


def test_contradictory_advisory_cap_is_flagged_without_replacing_declared_cap():
    solution = IndependentSolver(
        ReplaySolver(
            partial_credit_boundaries=[
                {"score": 3, "description": "Award three marks."}
            ]
        )
    ).solve(
        open_item(partial_credit_boundaries=[{"condition": "Method only", "cap": 1}]),
        [],
    )
    assert solution.advisory_issues
    assert solution.credit_rules[0].cap == 1
    assert solution.credit_rules[1].score == 3


def test_actual_blind_prompt_excludes_private_cpu_contract_and_review_at_any_depth():
    client = ReplaySolver()
    IndependentSolver(client).solve(
        open_item(
            source_data={"public_fact": "Candidate-visible processor description"},
            open_credit_contract={
                "id": "PRIVATE_ANSWER_BEARING_ID",
                "criteria": [{"text": "PRIVATE_CRITERION"}],
            },
            open_credit_review={"answer": "PRIVATE_REVIEW_ANSWER"},
            assessment_contract={"private": "PRIVATE_F_CRITERION"},
        ),
        [],
    )
    prompt = client.prompts[0]
    assert "Explain the stored program concept." in prompt
    assert "Candidate-visible processor description" in prompt
    assert "PRIVATE_" not in prompt


def cpu_fixture():
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.ollama_client import _part_solver_item

    from tests.test_computer_science_objectives import AQA

    question = build_paper2_blueprint(AQA, 26083134).questions[6]
    part = question.parts[0]
    item = _part_solver_item(question, part)
    solution = IndependentSolver(ReplaySolver()).solve(item, [])
    return question, part, item, solution


def adjudication_response(part):
    return {
        "criteria": [
            {
                "criterion_id": "instructions-main-memory",
                "decision": "supported",
                "answer_quote": "Machine instructions are held in main memory.",
                "scheme_quote": "Machine-code instructions are stored in main memory (1 mark);",
                "point_index": 0,
                "marks": 1,
            },
            {
                "criterion_id": "serial-processor-execution",
                "decision": "supported",
                "answer_quote": ANSWER,
                "scheme_quote": "The processor fetches and executes the instructions serially / in sequence (1 mark);",
                "point_index": 1,
                "marks": 1,
            },
        ],
        "issues": [],
        "advisory_conflicts": [],
    }


def test_cpu_has_two_source_supported_printable_marks_not_a_shared_data_requirement(
    tmp_path,
):
    import pymupdf
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.render_pdf import render_mark_scheme

    from tests.test_computer_science_objectives import AQA

    question, part, _, _ = cpu_fixture()
    assert [c["marks"] for c in part.open_credit_contract["criteria"]] == [1, 1]
    assert "data are stored" not in " ".join(part.marking.points)
    assert "shared" not in " ".join(part.marking.accept)
    path = tmp_path / "cpu-scheme.pdf"
    render_mark_scheme(build_paper2_blueprint(AQA, 26083134), path)
    with pymupdf.open(path) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    assert "Machine-code instructions are stored in main memory (1 mark)" in text
    assert "processor fetches and executes the instructions serially" in text
    assert "For both marks" in text
    assert question.parts[0].marks == 2


def test_cpu_adjudication_is_separate_model_evidence_bound_to_the_actual_answer_and_scheme():
    from Backend.Core.open_credit import review_open_credit, validate_open_credit_review

    _, part, item, solution = cpu_fixture()
    client = ReplaySolver(exact_response=adjudication_response(part))
    evidence = review_open_credit(client, item, solution)
    validate_open_credit_review(item, evidence, solution=solution)
    assert evidence["provenance"] == "model-semantic-adjudication"
    assert evidence["solution"]["answer"] == ANSWER
    assert "instructions-main-memory" in client.prompts[0]
    assert "not required" in client.prompts[0]
    assert solution.mark_points == [
        "Instructions in memory",
        "Processor fetches instructions",
    ]


def test_cpu_semantic_prompt_gives_the_exact_ordered_outer_response_envelope():
    from Backend.Core.open_credit import review_open_credit

    _, part, item, solution = cpu_fixture()
    client = ReplaySolver(exact_response=adjudication_response(part))
    review_open_credit(client, item, solution)
    expected = (
        'Exact response envelope (replace every angle-bracket placeholder; use [] when an array is empty):\n'
        '{"criteria": [{"criterion_id": "instructions-main-memory", '
        '"decision": "<supported|unsupported|uncertain>", '
        '"answer_quote": "<exact final-answer substring or empty string>", '
        '"scheme_quote": "<exact printed-point substring or empty string>", '
        '"point_index": 0, "marks": 1}, '
        '{"criterion_id": "serial-processor-execution", '
        '"decision": "<supported|unsupported|uncertain>", '
        '"answer_quote": "<exact final-answer substring or empty string>", '
        '"scheme_quote": "<exact printed-point substring or empty string>", '
        '"point_index": 1, "marks": 1}], '
        '"issues": ["<zero or more issue strings>"], '
        '"advisory_conflicts": ["<zero or more advisory-conflict strings>"]}'
    )
    assert expected in client.prompts[0]
    assert (
        "Criterion IDs must be values of criterion_id in that ordered array, never top-level keys."
        in client.prompts[0]
    )
    assert (
        "Fetches and executes instructions 'as needed' does not establish ordered execution."
        in client.prompts[0]
    )


def test_cpu_semantic_review_rejects_the_actual_flattened_live_response():
    from Backend.Core.open_credit import review_open_credit

    _, _, item, solution = cpu_fixture()
    client = ReplaySolver(exact_response=FLATTENED_LIVE_SEMANTIC_RESPONSE)
    with pytest.raises(ValueError):
        review_open_credit(client, item, solution)
    assert len(client.prompts) == 1


def test_cpu_semantic_review_rejects_top_level_criterion_keys_beside_valid_array():
    from Backend.Core.open_credit import review_open_credit

    _, part, item, solution = cpu_fixture()
    response = adjudication_response(part)
    response["instructions-main-memory"] = copy.deepcopy(response["criteria"][0])
    with pytest.raises(ValueError):
        review_open_credit(ReplaySolver(exact_response=response), item, solution)


def test_round2_live_semantic_result_rejects_fetch_and_execute_as_needed():
    from Backend.Core.open_credit import review_open_credit

    _, _, item, _ = cpu_fixture()
    solution = IndependentSolver(ReplaySolver(answer=ROUND2_LIVE_ANSWER)).solve(
        item, []
    )
    client = ReplaySolver(exact_response=ROUND2_LIVE_SEMANTIC_RESPONSE)
    with pytest.raises(ValueError, match=r"serial-processor-execution.*ordered"):
        review_open_credit(client, item, solution)
    assert len(client.prompts) == 1


@pytest.mark.parametrize(
    "answer_quote,expected",
    [
        ("Machine-code instructions are stored in main memory.", True),
        ("The program is held in RAM.", True),
        ("Program instructions are kept within main memory.", True),
        ("The CPU loads machine code into RAM.", True),
        ("Main memory holds the program instructions.", True),
        ("Program code is kept in main memory.", True),
        ("MACHINE‑CODE instructions are loaded into MAIN MEMORY.", True),
        ("Instructions must be stored in main memory.", True),
        ("Program instructions are kept in RAM; data may be elsewhere.", True),
        (
            "Instructions are stored in main memory, not only on secondary storage.",
            True,
        ),
        (
            "Instructions are stored in main memory, not stored in processor registers.",
            True,
        ),
        ("Data is stored in main memory.", False),
        ("This is called the stored program concept.", False),
        ("Program instructions are stored only on secondary storage.", False),
        ("The program is stored permanently in processor registers.", False),
        ("Program instructions are not stored in main memory.", False),
        ("Instructions are stored in main memory, but not always.", False),
        ("Instructions are stored in main memory only sometimes.", False),
        ("Instructions may be stored in main memory.", False),
        ("Instructions can be kept in RAM.", False),
        ("The CPU may load instructions into RAM.", False),
        ("The CPU can place instructions in main memory.", False),
        ("The CPU could load instructions into RAM.", False),
        ("The CPU might place instructions in main memory.", False),
        ("Instructions are stored in main memory, although not always.", False),
        ("Instructions are stored in main memory. But not always.", False),
        (
            "Instructions are stored in RAM. Instructions are not always stored in main memory.",
            False,
        ),
        (
            "Main memory stores program instructions. Main memory does not store program instructions.",
            False,
        ),
        (
            "The program instructions are stored in secondary storage; main memory holds only data.",
            False,
        ),
        ("Machine code is loaded from RAM into a processor register.", False),
    ],
)
def test_cpu_storage_quote_requires_instructions_stored_in_main_memory(
    answer_quote, expected
):
    from Backend.Core.open_credit import review_open_credit

    _, part, item, _ = cpu_fixture()
    serial_quote = "The processor executes machine instructions sequentially."
    solution = IndependentSolver(
        ReplaySolver(answer=f"{answer_quote} {serial_quote}")
    ).solve(item, [])
    response = adjudication_response(part)
    response["criteria"][0]["answer_quote"] = answer_quote
    response["criteria"][1]["answer_quote"] = serial_quote
    client = ReplaySolver(exact_response=response)
    if expected:
        assert review_open_credit(client, item, solution)["judgement"]["criteria"]
    else:
        with pytest.raises(ValueError, match="instructions-main-memory"):
            review_open_credit(client, item, solution)


@pytest.mark.parametrize(
    "answer_quote,expected",
    [
        ("The processor executes each instruction serially.", True),
        ("Machine instructions are processed sequentially.", True),
        ("The CPU carries out instructions in sequence.", True),
        (
            "Machine instructions are ready; the processor runs them one at a time.",
            True,
        ),
        ("The CPU executes instructions one after another.", True),
        ("The processor processes machine code instruction by instruction.", True),
        ("The processor executes machine‑code instructions one—by—one.", True),
        ("The processor completes one instruction before fetching the next.", True),
        ("An instruction is finished before the following one is started.", True),
        ("Not in parallel; instructions are executed sequentially.", True),
        (
            "Instructions are not executed in parallel; they are executed sequentially.",
            True,
        ),
        ("One instruction is executed at a time.", True),
        ("The processor performs each instruction sequentially.", True),
        ("Instructions must be executed sequentially.", True),
        ("The CPU executes one instruction at a time.", True),
        ("Instructions are fetched and executed sequentially.", True),
        ("The CPU executes these instructions sequentially.", True),
        (
            "Instructions are executed sequentially; data are processed in parallel.",
            True,
        ),
        ("the CPU can fetch and execute instructions as needed", False),
        ("The CPU fetches, decodes and executes instructions.", False),
        ("The CPU fetches instructions in order to execute them.", False),
        ("The fetch-decode-execute cycle processes an instruction.", False),
        ("The current instruction is executed and the next instruction is fetched.", False),
        ("Instructions are not executed sequentially.", False),
        ("Instructions are executed, but not sequentially.", False),
        ("The processor does not necessarily execute instructions sequentially.", False),
        ("The processor executes instructions sequentially, but not always.", False),
        ("The processor executes instructions sequentially only sometimes.", False),
        ("Instructions may be executed sequentially.", False),
        ("Instructions are executed sequentially. But not always.", False),
        (
            "Instructions are executed sequentially. Instructions are not executed sequentially.",
            False,
        ),
        ("Only sometimes the CPU executes instructions sequentially.", False),
        ("The CPU could execute instructions sequentially.", False),
        ("Instructions might be executed sequentially.", False),
        ("Instructions are stored sequentially in RAM.", False),
        ("The processor executes instructions in any order.", False),
        ("The CPU starts the next instruction before completing the current one.", False),
        ("The processor executes data one at a time.", False),
        ("The CPU executes data while fetching instructions one at a time.", False),
        ("The CPU executes instructions; data arrives one at a time.", False),
        ("The CPU can fetch the next instruction.", False),
        ("One instruction after another is loaded into RAM.", False),
        (
            "Program instructions are stored in RAM. Data arrive from memory; they are processed sequentially.",
            False,
        ),
        (
            "Program instructions are stored in RAM. Data arrive from memory; these are processed sequentially.",
            False,
        ),
        (
            "Program instructions are stored in RAM. Data arrive from memory; the CPU processes them sequentially.",
            False,
        ),
        ("The CPU processes these sequentially.", False),
    ],
)
def test_cpu_serial_quote_requires_explicit_ordered_execution(answer_quote, expected):
    from Backend.Core.open_credit import review_open_credit

    _, part, item, _ = cpu_fixture()
    storage_quote = "Machine-code instructions are held in RAM."
    solution = IndependentSolver(
        ReplaySolver(answer=f"{storage_quote} {answer_quote}")
    ).solve(item, [])
    response = adjudication_response(part)
    response["criteria"][0]["answer_quote"] = storage_quote
    response["criteria"][1]["answer_quote"] = answer_quote
    client = ReplaySolver(exact_response=response)
    if expected:
        assert review_open_credit(client, item, solution)["judgement"]["criteria"]
    else:
        with pytest.raises(ValueError, match=r"serial-processor-execution.*ordered"):
            review_open_credit(client, item, solution)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-criterion",
        "duplicate-criterion",
        "unknown-criterion",
        "uncertain",
        "unsupported",
        "invented-quote",
        "wrong-mark",
        "duplicate-point",
        "issues",
        "missing-issues",
    ],
)
def test_cpu_semantic_review_fails_closed_on_incomplete_or_unsubstantiated_decisions(
    mutation,
):
    from Backend.Core.open_credit import review_open_credit

    _, part, item, solution = cpu_fixture()
    response = adjudication_response(part)
    first = response["criteria"][0]
    if mutation == "missing-criterion":
        response["criteria"].pop()
    elif mutation == "duplicate-criterion":
        response["criteria"][1]["criterion_id"] = first["criterion_id"]
    elif mutation == "unknown-criterion":
        first["criterion_id"] = "significance"
    elif mutation in {"uncertain", "unsupported"}:
        first["decision"] = mutation
    elif mutation == "invented-quote":
        first["answer_quote"] = "NOT IN ACTUAL ANSWER"
    elif mutation == "wrong-mark":
        first["marks"] = 2
    elif mutation == "duplicate-point":
        response["criteria"][1]["point_index"] = 0
    elif mutation == "issues":
        response["issues"] = ["Same-address confusion"]
    else:
        del response["issues"]
    with pytest.raises(ValueError):
        review_open_credit(ReplaySolver(exact_response=response), item, solution)


@pytest.mark.parametrize(
    "mutation", ["source", "criteria", "scheme", "answer", "policy", "missing-origin"]
)
def test_cpu_saved_evidence_rejects_mutated_identity_or_untyped_history(mutation):
    from Backend.Core.open_credit import review_open_credit, validate_open_credit_review

    _, part, item, solution = cpu_fixture()
    evidence = review_open_credit(
        ReplaySolver(exact_response=adjudication_response(part)), item, solution
    )
    if mutation == "source":
        item["context"] += " Different source."
    elif mutation == "criteria":
        item["authoring_context"]["open_credit_contract"]["criteria"][0]["meaning"] = (
            "Different meaning"
        )
    elif mutation == "scheme":
        item["marking"]["points"][1] = "Only repeats storage."
    elif mutation == "answer":
        evidence["solution"]["answer"] = "Only secondary storage."
    elif mutation == "policy":
        evidence["credit_policy_version"] = "old"
    else:
        evidence["solution"].pop("credit_policy_version")
    with pytest.raises(ValueError):
        validate_open_credit_review(item, evidence)


def test_cpu_reconciliation_cannot_accept_nonempty_model_points_without_semantic_credit_evidence():
    _, part, _, solution = cpu_fixture()
    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "mark_scheme": part.marking.points,
            "assessment_objectives": {"AO1": 2},
        },
    )
    assert not result.passed
    assert any(issue.field == "open_credit_review" for issue in result.issues)


def test_actual_cpu_pipeline_orders_blind_solver_semantic_review_then_difficulty():
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.ollama_client import review_blueprint_difficulty

    from Backend.Core.computer_science_authoring import validate_aqa_cs_reviews
    from tests.test_computer_science_objectives import AQA

    question, part, _, _ = cpu_fixture()
    paper = build_paper2_blueprint(AQA, 26083134)
    paper.questions = [question.model_copy(update={"parts": [part]})]
    prompts = []

    class PipelineClient:
        def generate_json(self, prompt):
            prompts.append(prompt)
            if prompt.startswith("Independently solve"):
                return ReplaySolver().response
            if prompt.startswith("Act as a scoped semantic"):
                return adjudication_response(part)
            return {
                "approved": True,
                "estimated_demand": "low",
                "reasoning_steps": 1,
                "tariff_fit": True,
                "command_word_fit": True,
                "context_fit": True,
                "profile_fit": True,
                "observed_cognitive_operations": ["retrieve", "explain"],
                "cognitive_operations_fit": True,
                "reasoning_range_fit": True,
                "shortcut_resistant": True,
                "timing_fit": True,
                "scaffolding_fit": True,
                "estimated_minutes": 3.0,
                "issues": [],
            }

    reviewed = review_blueprint_difficulty(PipelineClient(), paper, AQA)
    assert len(prompts) == 3
    assert (
        prompts[0].startswith("Independently solve")
        and "instructions-main-memory" not in prompts[0]
    )
    assert "Explain the stored program concept." in prompts[0]
    assert "Machine-code instructions are stored in main memory" not in prompts[0]
    assert "serial-processor-execution" not in prompts[0]
    assert "4.7.2.1" not in prompts[0]
    assert prompts[1].startswith("Act as a scoped semantic")
    assert prompts[2].startswith("Act as an independent UK A-level difficulty")
    semantic_only = (
        "instructions-main-memory",
        "serial-processor-execution",
        "4.7.2.1",
        "open_credit_contract",
        "credit_allocations",
    )
    for token in semantic_only:
        assert token in prompts[1]
        assert token not in prompts[0]
        assert token not in prompts[2]
    assert "open_credit_review" not in prompts[0]
    assert "open_credit_review" not in prompts[2]
    assert "A computer executes machine-code instructions" in prompts[2]
    assert "Explain the stored program concept." in prompts[2]
    assert '"marks": 2' in prompts[2]
    assert "Machine-code instructions are stored in main memory;" in prompts[2]
    solution_answer = ReplaySolver().response["answer"]
    assert solution_answer in prompts[2]
    assert "Recall storage and execution." in prompts[2]
    assert (
        reviewed.questions[0].parts[0].open_credit_review["provenance"]
        == "model-semantic-adjudication"
    )
    validate_aqa_cs_reviews(reviewed.model_dump(mode="json"))
    assert len(prompts) == 3


def test_saved_cpu_difficulty_without_credit_review_is_not_export_eligible():
    from Backend.Core.computer_science_authoring import validate_aqa_cs_reviews

    question, part, _, _ = cpu_fixture()
    part.difficulty_evidence = {"approved": True}
    with pytest.raises(ValueError, match="credit review"):
        validate_aqa_cs_reviews(
            {"paper_code": "7517/2", "questions": [question.model_dump(mode="json")]}
        )


def test_real_captured_cpu_advisory_boundary_is_not_promoted_to_declared_credit():
    solution = IndependentSolver(ReplaySolver(**CAPTURED_CPU_RESPONSE)).solve(
        open_item(partial_credit_boundaries=[]), []
    )
    original_scheme = {
        "marks": 2,
        "mark_scheme": [
            "Instructions and data are stored in main memory;",
            "The processor fetches instructions from memory to execute them;",
        ],
    }
    # This tests the original false lexical obligation only, not the semantic
    # correctness of the capture's overspecific shared-memory answer.
    assert reconcile_solution(solution, original_scheme).passed
    assert (
        solution.credit_rules[0].raw
        == CAPTURED_CPU_RESPONSE["partial_credit_boundaries"][0]
    )


@pytest.mark.parametrize(
    "mutation",
    ["missing-storage", "missing-execution", "double-storage", "two-for-storage"],
)
def test_builtin_cpu_preview_rejects_missing_or_duplicate_actual_credit(mutation):
    from Backend.Core.computer_science_authoring import validate_aqa_cs_reviews

    question, part, _, _ = cpu_fixture()
    if mutation.startswith("missing"):
        part.marking.points.pop(0 if mutation == "missing-storage" else 1)
    elif mutation == "double-storage":
        part.marking.points[1] = "The memory holds the instructions (1 mark);"
    else:
        part.marking.credit_allocations[0]["marks"] = 2
        part.marking.credit_allocations[1]["marks"] = 0
    with pytest.raises(ValueError, match=r"credit|criteria|CPU"):
        validate_aqa_cs_reviews(
            {"paper_code": "7517/2", "questions": [question.model_dump(mode="json")]}
        )


@pytest.mark.parametrize(
    "answer,decision",
    [
        (
            "Main memory contains the machine instructions. In order, the CPU retrieves and runs them.",
            "supported",
        ),
        ("Programs are kept only on the SSD and run there.", "unsupported"),
        (
            "The processor permanently stores the whole program rather than using main memory.",
            "unsupported",
        ),
        (
            "Instructions and data must occupy an identical memory address. The CPU runs them.",
            "unsupported",
        ),
    ],
)
def test_source_distinction_uses_explicit_semantic_decisions_not_keyword_overlap(
    answer, decision
):
    from Backend.Core.open_credit import review_open_credit

    _, part, item, _ = cpu_fixture()
    solution = IndependentSolver(ReplaySolver(answer=answer)).solve(item, [])
    response = adjudication_response(part)
    for row in response["criteria"]:
        row.update(answer_quote=answer, decision=decision)
    if decision == "supported":
        evidence = review_open_credit(
            ReplaySolver(exact_response=response), item, solution
        )
        assert evidence["provenance"] == "model-semantic-adjudication"
    else:
        with pytest.raises(ValueError, match="does not support"):
            review_open_credit(ReplaySolver(exact_response=response), item, solution)


def test_genuine_paraphrase_and_reordered_allocations_are_eligible_after_semantic_review():
    from Backend.Core.open_credit import review_open_credit

    _, part, item, solution = cpu_fixture()
    item["marking"]["points"] = [
        "CPU retrieves then carries out the instruction sequence",
        "Main memory holds the machine instructions",
    ]
    item["marking"]["credit_allocations"][0]["point_index"] = 1
    item["marking"]["credit_allocations"][1]["point_index"] = 0
    response = adjudication_response(part)
    for row in response["criteria"]:
        index = 1 if row["criterion_id"] == "instructions-main-memory" else 0
        row.update(point_index=index, scheme_quote=item["marking"]["points"][index])
    # Re-solve after the candidate scheme mutation: the blind answer is unchanged.
    solution = IndependentSolver(ReplaySolver()).solve(item, [])
    assert (
        review_open_credit(ReplaySolver(exact_response=response), item, solution)[
            "judgement"
        ][
            "criteria"
        ][0]["point_index"]
        == 1
    )


def test_declared_numeric_own_figure_credit_stays_conditional_and_required():
    from tests.test_independent_solver import _calculation_item

    item = _calculation_item()
    rule = "If the candidate's own contribution is £50 per unit, allow £500 for multiplying by 10 units."
    item["authoring_context"]["follow_through_rules"] = [rule]
    solution = IndependentSolver().solve(item, [])
    raw = {
        "marks": 4,
        "assessment_objectives": {"AO2": 4},
        "mark_scheme": [
            "Subtract variable cost from revenue; multiply unit contribution by units. Answer 400"
        ],
        "follow_through_rules": [rule],
    }
    assert reconcile_solution(solution, raw).passed
    assert not solution.alternatives
    raw.pop("follow_through_rules")
    assert not reconcile_solution(solution, raw).passed


def test_source_declared_closed_numeric_alternative_cannot_evade_numeric_validation():
    from tests.test_independent_solver import _calculation_item

    item = _calculation_item()
    item["authoring_context"]["valid_alternatives"] = ["result: £500"]
    solution = IndependentSolver().solve(item, [])
    raw = {
        "marks": 4,
        "assessment_objectives": {"AO2": 4},
        "mark_scheme": [
            "Subtract variable cost from revenue; multiply unit contribution by units. Answer 400",
            "result: £500",
        ],
    }
    assert not reconcile_solution(solution, raw).passed


def test_host_permission_typing_does_not_reclassify_a_concrete_numeric_answer():
    from Backend.Core.credit_policy import alternative_permission
    from tests.test_independent_solver import _calculation_item

    item = _calculation_item()
    item["authoring_context"].update(
        alternative_permission("equivalent-assessed-route")
    )
    item["authoring_context"]["valid_alternatives"] = ["result: £500"]
    with pytest.raises(ValueError, match="permission"):
        IndependentSolver().solve(item, [])


@pytest.mark.parametrize("mutation", ["unknown-id", "missing-version", "old-version"])
def test_host_permission_typing_rejects_unknown_or_legacy_metadata(mutation):
    from Backend.Core.credit_policy import alternative_permission
    from tests.test_independent_solver import _calculation_item

    item = _calculation_item()
    context = item["authoring_context"]
    context.update(alternative_permission("equivalent-assessed-route"))
    if mutation == "unknown-id":
        context["alternative_permission_ids"] = ["custom-exemption"]
    elif mutation == "missing-version":
        context.pop("alternative_permission_version")
    else:
        context["alternative_permission_version"] = "old"
    with pytest.raises(ValueError, match="permission"):
        IndependentSolver().solve(item, [])


def test_model_cannot_claim_host_permission_origin_for_a_concrete_closed_alternative():
    solution = IndependentSolver(
        ReplaySolver(
            answer={"result": "True"},
            mark_points={"result": "True"},
            alternatives=[
                {
                    "text": "False",
                    "origin": "source-declared",
                    "content_kind": "permission",
                }
            ],
        )
    ).solve({**open_item(), "response_slots": ["result"]}, [])
    rule = next(rule for rule in solution.credit_rules if rule.kind == "alternatives")
    assert (rule.origin, rule.content_kind) == ("closed-answer-validation", "answer")
    assert not reconcile_solution(
        solution,
        {"marks": 2, "mark_scheme": ["True"], "closed_answers": {"result": ["True"]}},
    ).passed


def test_paraphrased_cpu_credit_still_prints_its_actual_typed_one_mark_allocations(
    tmp_path,
):
    import pymupdf
    from cspapergen.generator import build_paper2_blueprint
    from cspapergen.render_pdf import render_mark_scheme

    from tests.test_computer_science_objectives import AQA

    paper = build_paper2_blueprint(AQA, 26083134)
    part = paper.questions[6].parts[0]
    part.marking.points = [
        "Main memory holds machine-code instructions",
        "CPU fetches and runs them sequentially",
    ]
    path = tmp_path / "paraphrase.pdf"
    render_mark_scheme(paper, path)
    with pymupdf.open(path) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    assert "Main memory holds machine-code instructions (1 mark)" in text
    assert "CPU fetches and runs them sequentially (1 mark)" in text


def test_wrong_model_closed_alternative_fails_even_if_also_printed_as_guidance():
    solution = IndependentSolver(
        ReplaySolver(
            answer={"result": "True"},
            mark_points={"result": "True"},
            alternatives=[
                {
                    "text": "False",
                    "origin": "source-declared",
                    "content_kind": "permission",
                }
            ],
        )
    ).solve({**open_item(), "response_slots": ["result"]}, [])
    result = reconcile_solution(
        solution,
        {
            "marks": 2,
            "mark_scheme": ["True", "Allow False"],
            "closed_answers": {"result": ["True"]},
        },
    )
    assert not result.passed
    assert any(issue.field == "alternatives" for issue in result.issues)
