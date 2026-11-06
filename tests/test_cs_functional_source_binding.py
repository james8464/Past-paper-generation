"""Owned functional source admission, not general Haskell or paper qualification."""

import json
from copy import deepcopy

import pytest
from cspapergen.generator import build_topic_question_bank
from cspapergen.render_pdf import candidate_stimulus_data
from cspapergen.syllabus import load_syllabus
from cspapergen.validation import validate_blueprint

from Backend.Core.assessment_package import (
    validate_assessment_package,
    write_assessment_package,
)
from Backend.Core.computer_science_authoring import (
    aqa_cs_solver_item,
    question_content_sha256,
    reviewed_question_metadata,
    validate_aqa_cs_reviews,
    validate_question_review,
)
from Backend.Core.independent_solver import IndependentSolver
from Backend.Core.model_review import ReviewResult


def functional_question(seed=270100):
    bank = build_topic_question_bank(load_syllabus(), topic_id="4.12", seed=seed)
    question = next(q for q in bank.questions if q.style_id == "functional_programming")
    return question.model_dump(mode="json")


def solver_item(question):
    from cspapergen.models import Stimulus

    part = next(p for p in question["parts"] if len(p["response_slots"]) == 4)
    return aqa_cs_solver_item(
        question,
        part,
        candidate_stimulus_data(Stimulus.model_validate(question["stimulus"])),
    )


CANONICAL = (
    "values = [5, 2, 6]\n"
    "double n = 2 * n\n"
    "filtered xs = filter (>4) xs\n"
    "mapped xs = map double xs\n"
    "total xs = fold (+) 0 xs"
)
INVALID_SOURCES = [
    CANONICAL.replace(
        "mapped xs = map double xs", "mapped xs = map double xs ++ [999]"
    ),
    CANONICAL.replace("total xs = fold (+) 0 xs", "total xs = fold (+) 0 xs + 1"),
    CANONICAL + "\nmapped xs = []",
    CANONICAL + "\nhelper x = x + 1",
    CANONICAL.replace("double n = 2 * n", "double n = 2 * n\ndouble n = 9 * n"),
    CANONICAL.replace("mapped xs = map double xs", "-- mapped xs = map double xs"),
    CANONICAL.replace("total xs = fold (+) 0 xs", "total xs = fold (*) 0 xs"),
    CANONICAL.replace("values = [5, 2, 6]", "values = [5,,6]"),
    CANONICAL.replace("values = [5, 2, 6]", "values = [5, 2, 6,]"),
    CANONICAL.replace("mapped xs = map double xs", "  mapped xs = map double xs"),
    "\n".join(reversed(CANONICAL.splitlines())),
    "\n".join(CANONICAL.splitlines()[:-1]),
]


@pytest.mark.parametrize("source", INVALID_SOURCES)
@pytest.mark.parametrize(
    "path", ["solver", "built-in-review", "approved-export-review"]
)
def test_unsupported_complete_source_refuses_before_a_deterministic_contract(
    source, path
):
    question = functional_question()
    question["stimulus"]["code"] = source
    if path == "approved-export-review":
        # A matching historical content hash is not proof that its old source
        # projection described this complete program. Fresh admission still runs.
        question.update(
            reviewed_question_metadata(question, question, ReviewResult(approved=True))
        )
    original = deepcopy(question)
    with pytest.raises(ValueError, match="unsupported source code"):
        if path == "solver":
            solver_item(question)
        elif path == "built-in-review":
            validate_question_review(question)
        else:
            validate_aqa_cs_reviews(
                {"paper_code": "7517/2", "questions": [question]}, required=True
            )
    assert question == original


@pytest.mark.parametrize("seed", range(20))
def test_current_public_topic_sources_keep_their_contract_and_reviews(seed):
    bank = build_topic_question_bank(load_syllabus(), topic_id="4.12", seed=seed)
    validate_blueprint(bank, load_syllabus())
    question = functional_question(seed)
    original = deepcopy(question)
    item = solver_item(question)
    source = item["authoring_context"]["cs_input_contract"]
    solution = IndependentSolver().solve(item, [])
    assert solution.solution_source == "deterministic-candidate-inputs"
    assert solution.numeric_results["total-mapped"] == sum(source["values"]) * 2
    assert source["map_multiplier"] == 2 and source["filter_greater_than"] == 4
    reviewed = deepcopy(question)
    reviewed.update(
        reviewed_question_metadata(question, question, ReviewResult(approved=True))
    )
    validate_question_review(reviewed, question, required=True)
    assert question_content_sha256(reviewed) == question_content_sha256(question)
    assert question == original


@pytest.mark.parametrize("multiplier, threshold", [(2, 4), (-3, -1), (0, 0)])
@pytest.mark.parametrize("line_ending", ["\n", "\r\n", "\r"])
def test_supported_parameters_and_blank_lines_remain_literal(
    multiplier, threshold, line_ending
):
    question = functional_question()
    code = CANONICAL.replace("double n = 2 * n", f"double n = {multiplier} * n")
    code = code.replace(
        "filtered xs = filter (>4) xs", f"filtered xs = filter (>{threshold}) xs"
    )
    code = line_ending.join(["", *code.splitlines(), "", " "])
    question["stimulus"]["code"] = code
    before = deepcopy(question)
    item = solver_item(question)
    source = item["authoring_context"]["cs_input_contract"]
    assert source == {
        "kind": "functional-list-operations",
        "values": [5, 2, 6],
        "filter_greater_than": threshold,
        "map_multiplier": multiplier,
    }
    solution = IndependentSolver().solve(item, [])
    assert solution.numeric_results["total-mapped"] == 13 * multiplier
    assert question == before


def test_package_write_and_saved_package_read_revalidate_the_complete_source(tmp_path):
    bank = build_topic_question_bank(load_syllabus(), topic_id="4.12", seed=270100)
    path = tmp_path / "owned-package.json"
    write_assessment_package(
        bank,
        path,
        subject="computer_science",
        paper_number="2",
        preview=True,
        provider=None,
        model=None,
    )
    saved = json.loads(path.read_text())
    original = path.read_bytes()
    question = next(q for q in bank.questions if q.style_id == "functional_programming")
    question.stimulus.code += "\nhelper x = x + 1"
    with pytest.raises(ValueError, match="unsupported source code"):
        write_assessment_package(
            bank,
            path,
            subject="computer_science",
            paper_number="2",
            preview=True,
            provider=None,
            model=None,
        )
    assert path.read_bytes() == original
    stored_question = next(
        q
        for q in saved["blueprint"]["questions"]
        if q["style_id"] == "functional_programming"
    )
    stored_question["stimulus"]["code"] += "\nhelper x = x + 1"
    path.write_text(json.dumps(saved))
    invalid_bytes = path.read_bytes()
    with pytest.raises(ValueError, match="unsupported source code"):
        validate_assessment_package(
            path,
            subject="computer_science",
            paper_number="2",
            preview=True,
            provider=None,
            model=None,
        )
    assert path.read_bytes() == invalid_bytes
