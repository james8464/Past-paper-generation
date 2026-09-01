from collections import Counter
from pathlib import Path

import pytest
from cspapergen.generator import (
    build_paper1_blueprint,
    build_paper2_blueprint,
    build_topic_question_bank,
)
from cspapergen.ollama_client import _part_demand_item
from cspapergen.syllabus import load_syllabus as aqa_syllabus
from cspapergen.validation import validate_blueprint
from ocrcsgen.configs import load_rule
from ocrcsgen.generator import build_paper
from ocrcsgen.render_pdf import _question_group_pages, _response_space
from ocrcsgen.syllabus import load_syllabus as ocr_syllabus

from Backend.Core.assessment_package import (
    validate_assessment_package,
    write_assessment_package,
)
from Backend.Core.independent_solver import IndependentSolver, reconcile_solution
from Backend.Core.reference_demand import build_item_demand_target, profile_for

ROOT = Path(__file__).resolve().parents[1]
AQA = aqa_syllabus(ROOT / "Resources/computer-science/aqa/generator/data/syllabus_seed.json")
OCR = ocr_syllabus(ROOT / "Resources/computer-science/ocr/generator/data/syllabus.json")


@pytest.mark.parametrize("paper_id,expected", [("1", {"AO1": 20, "AO2": 30, "AO3": 50}), ("2", {"AO1": 56, "AO2": 40, "AO3": 4})])
def test_aqa_cs_explicit_component_budgets_and_allotted_time(paper_id, expected):
    paper = build_paper1_blueprint(AQA, 26083125)[0] if paper_id == "1" else build_paper2_blueprint(AQA, 26083125)
    totals = Counter()
    minutes = 0
    for question in paper.questions:
        for part in question.parts:
            item = _part_demand_item(question, part)
            assert sum(item["assessment_objectives"].values()) == part.marks
            totals.update(item["assessment_objectives"])
            minutes += item.get("expected_minutes") or 0
    assert dict(totals) == expected
    assert minutes == 150


@pytest.mark.parametrize("mutation", ["ao4", "missing-objectives", "missing-time", "wrong-time"])
def test_aqa_current_or_saved_blueprints_fail_closed_on_invalid_policy(mutation):
    paper = build_paper2_blueprint(AQA, 26083125)
    part = paper.questions[0].parts[0]
    if mutation == "ao4":
        part.assessment_objectives = {"AO4": 2}
    elif mutation == "missing-objectives":
        part.assessment_objectives = {}
    else:
        part.expected_minutes = None if mutation == "missing-time" else 2.4
    with pytest.raises(ValueError, match=r"objective|timing|time|AO4"):
        validate_blueprint(paper, AQA)


def test_sql_credit_matches_six_mark_query_and_independent_row_analysis():
    question = build_paper2_blueprint(AQA, 26083125).questions[5]
    assert [p.marks for p in question.parts] == [1, 6, 2, 2, 1]
    assert question.parts[1].assessment_objectives == {"AO2": 4, "AO3": 2}
    assert question.parts[2].assessment_objectives == {"AO3": 2}
    assert question.parts[3].marking.closed_answers == {
        "first-booking": ["(1842,27)", "1842,27"], "second-booking": ["(1842,28)", "1842,28"]}
    assert question.parts[4].marking.closed_answers == {"removed-booking": ["(1844,27)", "1844,27"]}
    assert "independently" in question.stem
    assert "1844, 27, TRUE" in question.stimulus.code
    validate_blueprint(build_paper2_blueprint(AQA, 26083125), AQA)


def test_aqa_reachable_trace_defines_initial_state_and_complete_execution():
    import ast
    import re
    question = build_paper1_blueprint(AQA, 26083125)[0].questions[2]
    part = question.parts[4]
    call_text = re.search(r"Trace the call (.*?)\.", part.prompt).group(1)
    call = ast.parse(call_text, mode="eval").body
    source = ast.parse(question.stimulus.code)
    function = source.body[1]
    assert len(call.args) == len(function.args.args) == 3
    assert ast.literal_eval(call.args[0]) == 3
    assert ast.literal_eval(call.args[1]) == 6
    assert isinstance(call.args[2], ast.Call) and call.args[2].func.id == "set" and not call.args[2].args
    adjacency = ast.literal_eval(source.body[0].value)
    # Independent bounded DFS over literal candidate data, not execution of a
    # generated program or use of the private expected answer.
    calls, additions = [], []
    def visit(current):
        calls.append(current)
        if current == 6:
            return True
        additions.append(current)
        return any(visit(n) for n in adjacency[current] if n not in additions)
    assert visit(3) is True
    assert calls == [3, 2, 1, 4, 5, 6]
    assert additions == [3, 2, 1, 4, 5]
    assert part.marking.closed_answers == {
        "called-current-vertices-in-order": ["3,2,1,4,5,6", "[3,2,1,4,5,6]"],
        "visited-additions-in-order": ["3,2,1,4,5", "[3,2,1,4,5]"], "result": ["True"]}
    guidance = " ".join(part.marking.points)
    assert "{}" in guidance and "{3,2,1,4,5}" in guidance and "6 is not added" in guidance


def test_aqa_printed_trace_exemplar_does_not_show_invalid_two_argument_calls(tmp_path):
    import pymupdf
    from cspapergen.render_pdf import render_mark_scheme
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(build_paper1_blueprint(AQA, 26083125)[0], path)
    with pymupdf.open(path) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    assert "reachable(3, 6)" not in text
    assert "reachable(6, 6)" not in text
    assert "visited after step" in text
    assert "visited on entry" in text
    assert "Current / target" in text


@pytest.mark.parametrize("topic", ["4.2", "4.10", "4.12"])
def test_aqa_banks_use_declared_45_minute_allowance(topic):
    paper = build_topic_question_bank(AQA, topic_id=topic, seed=26083125)
    items = [_part_demand_item(q, p) for q in paper.questions for p in q.parts]
    assert sum(item.get("expected_minutes") or 0 for item in items) == 45
    assert sum(item["marks"] for item in items) == 30
    for item in items:
        target = build_item_demand_target(item, profile_for("aqa/computer-science", f"bank-{topic}"))
        assert target.expected_minutes_min == round(item["marks"] * 1.5 * .75, 2)


@pytest.mark.parametrize("command,kind,operation", [("Design", "programming", "design"), ("Complete", "programming", "program"), ("Trace", "trace", "trace")])
def test_computational_work_is_not_invented_prose_judgement(command, kind, operation):
    target = build_item_demand_target({"marks": 12, "kind": kind, "command_word": command,
        "prompt": f"{command} the supplied algorithm.", "assessment_objectives": {"AO2" if kind == "trace" else "AO3": 12}},
        profile_for("ocr/computer-science", "1"))
    assert not target.requires_judgement
    assert not target.requires_analysis_chain
    assert operation in target.required_cognitive_operations
    assert target.response_mode != "extended-evaluation"


@pytest.mark.parametrize("seed", [26083125, 26083126, 26083127])
def test_ocr_all_ten_closed_items_are_independently_solvable(seed):
    paper = build_paper(load_rule("1"), OCR, seed)
    closed = [q for s in paper.sections for o in s.options for q in o.questions if q.kind in {"calculation", "trace"}]
    assert {q.number for q in closed} == {"1(d)", "4(a)", "4(c)", "4(d)", "4(e)", "4(f)", "5(b)", "5(c)", "5(d)", "8(b)"}
    for question in closed:
        solution = IndependentSolver().solve(question, [])
        assert solution.solution_source == "deterministic-candidate-inputs"
        assert solution.response_slots
        result = reconcile_solution(solution, question)
        assert result.passed, (question.number, result.issues)
        # Missing or corrupt published answers must not pass via draft expectations.
        corrupt = question.model_copy(deep=True)
        corrupt.mark_scheme = ["No result is supplied."]
        corrupt.structured_mark_scheme = []
        assert not reconcile_solution(solution, corrupt).passed


@pytest.mark.parametrize("source,expected", [
    ({"kind": "bounded-sum-trace", "values": [12, 25, 40, 18], "initial_total": 3, "threshold": 25},
     {"iteration-1-total": "3", "iteration-2-total": "3", "iteration-3-total": "43", "iteration-4-total": "43", "output": "43"}),
    ({"kind": "denary-hex", "value": 175}, {"hexadecimal": "AF"}),
    ({"kind": "bitmap-bytes", "width": 128, "height": 64, "depth": 4}, {"file-size": "4,096 bytes"}),
    ({"kind": "sound-bytes", "sample_rate": 8000, "sample_depth": 16, "duration": 3, "channels": 1}, {"file-size": "48,000 bytes"}),
    ({"kind": "unsigned-sum", "left": 200, "right": 70}, {"8-bit-result": "00001110", "overflow": "yes"}),
    ({"kind": "floating-encode", "value": "6.5", "mantissa_bits": 5, "exponent_bits": 3}, {"representation": "01101011"}),
    ({"kind": "boolean-evaluation", "expression": "A XOR B", "inputs": [{"A": 0, "B": 0}, {"A": 1, "B": 1}]},
     {"case-1": "0", "case-2": "0"}),
])
def test_cs_closed_templates_recompute_literal_outputs_without_private_key(source, expected):
    item = {"marks": 4, "kind": "calculation", "authoring_context": {"cs_input_contract": source},
            "mark_scheme": ["deliberately false answer 97"], "correct_answer": "97"}
    assert IndependentSolver().solve(item, []).answer_slots == expected


@pytest.mark.parametrize("number,prefix,alternative,valid", [
    ("4(a)", "Hexadecimal:", "Accept FF.", False),
    ("4(a)", "Hexadecimal:", "Accept 6c.", True),
    ("4(e)", "Overflow:", "Accept yes.", False),
    ("4(e)", "Overflow:", "Allow NO.", True),
    ("4(e)", "Overflow:", "Accept no or yes.", False),
    ("4(e)", "Overflow:", "Accept no.\nyes", False),
])
def test_encoded_alternatives_are_verified_at_real_candidate_boundary(number, prefix, alternative, valid):
    from Backend.Core.ai_assessment import _independently_validate_candidate, _tasks
    paper = build_paper(load_rule("1"), OCR, 26083125)
    task = next(t for t in _tasks(paper, {topic.id: topic for topic in OCR.topics}) if t.question.number == number)
    raw = task.question.model_dump(mode="json")
    point = next(p for p in raw["structured_mark_scheme"] if p["text"].startswith(prefix))
    point["alternatives"] = [alternative]
    candidate = task.question.model_validate(raw)
    solution = IndependentSolver().solve(candidate, [])
    assert reconcile_solution(solution, candidate).passed is valid
    if valid:
        _independently_validate_candidate(task, candidate, client=None)
    else:
        with pytest.raises(ValueError, match="reconciliation"):
            _independently_validate_candidate(task, candidate, client=None)


@pytest.mark.parametrize("alternative,valid", [("overflow: NO", True), ("Accept no", False),
    ("overflow: yes", False), ("8-bit-result: 01111011", True), ("overflow: no bytes", False)])
def test_multi_output_encoded_alternatives_require_one_named_role(alternative, valid):
    paper = build_paper(load_rule("1"), OCR, 26083125)
    question = next(q for s in paper.sections for q in s.options[0].questions if q.number == "4(e)")
    raw = question.model_dump(mode="json")
    raw["alternatives"] = [alternative]
    assert reconcile_solution(IndependentSolver().solve(question, []), raw).passed is valid


@pytest.mark.parametrize("seed", [26083125, 26083126, 26083127])
def test_ocr_trace_candidate_source_and_rendered_rows_agree(seed):
    paper = build_paper(load_rule("1"), OCR, seed)
    for section in (paper.sections[0], paper.sections[7]):
        option = section.options[0]
        question = next(q for q in option.questions if q.kind == "trace")
        source = question.authoring_context["cs_input_contract"]
        assert option.chart_values == source["values"]
        count = len(source["values"])
        assert f"index = 0 to {count - 1}" in option.stimulus[1]
        assert f"all {count} iterations" in question.prompt
        response = _response_space(question, 6)
        assert len(response[0]._cellvalues) == count + 1
        assert response[0]._cellvalues[0] == ["Iteration", "total after iteration"]
        # The source array must be on the candidate page, not solely in JSON.
        story = _question_group_pages(paper.paper_id, paper.paper_code, option, include_section_page=True)
        tables = [f for f in story if hasattr(f, "_cellvalues")]
        assert any(t._cellvalues[-1] == ["Value", *map(str, source["values"])] for t in tables)


@pytest.mark.parametrize("paper_id,expected", [("1", {"AO1": 74, "AO2": 31, "AO3": 35}), ("2", {"AO1": 53, "AO2": 63, "AO3": 24})])
def test_ocr_inferred_task_budgets_do_not_use_ao4_or_prose_programming_levels(paper_id, expected):
    paper = build_paper(load_rule(paper_id), OCR, 26083125)
    totals = Counter()
    for section in paper.sections:
        for question in section.options[0].questions:
            totals.update(question.assessment_objectives)
            assert set(question.assessment_objectives) <= {"AO1", "AO2", "AO3"}
            for line in question.mark_scheme:
                if line.startswith(("AO1:", "AO2:", "AO3:")):
                    assert line.split(":")[0] in question.assessment_objectives
            if question.kind == "programming":
                assert not any(line.startswith("Level ") for line in question.mark_scheme)
    assert dict(totals) == expected


@pytest.mark.parametrize("prompt,operation,mode", [
    ("Design an algorithm to group the records.", "design", "computational-design"),
    ("Develop a subroutine to validate each record.", "program", "programming"),
    ("Trace the supplied algorithm.", "trace", "algorithm-trace"),
    ("Write a SQL query that joins these tables.", "program", "programming"),
    ("Write down the meaning of encapsulation.", "explain", "constructed-response"),
])
def test_reference_and_generated_cs_operations_use_same_task_meaning(prompt, operation, mode):
    from tools.reference_demand_profiles import extract_reference_items
    reference = extract_reference_items(prompt + "\n[4 marks]", board="aqa", family_id="aqa/computer-science", paper_id="1")[0]
    target = build_item_demand_target({"marks": 4, "prompt": prompt, "assessment_objectives": {}},
                                    profile_for("aqa/computer-science", "1"))
    assert reference["cognitive_operation"] == operation
    assert operation in target.required_cognitive_operations
    assert reference["response_mode"] == target.response_mode == mode


def test_classification_pdf_edges_are_orthogonal_and_labels_readable():
    from io import BytesIO

    import pymupdf
    from cspapergen.render_pdf import _draw_classification_diagram
    from reportlab.pdfgen.canvas import Canvas
    buffer = BytesIO()
    canvas = Canvas(buffer)
    stimulus = build_paper2_blueprint(AQA, 26083125).questions[0].stimulus
    _draw_classification_diagram(canvas, stimulus, 80, 700)
    canvas.save()
    document = pymupdf.open(stream=buffer.getvalue(), filetype="pdf")
    segments = [item for drawing in document[0].get_drawings() for item in drawing["items"] if item[0] == "l"]
    # Main connectors use axis-aligned segments; short arrowheads may be diagonal.
    assert all(abs(a.x-b.x) < .1 or abs(a.y-b.y) < .1 for _, a, b in segments if abs(a-b) > 8)
    labels = [span for block in document[0].get_text("dict")["blocks"] for line in block.get("lines", []) for span in line["spans"]]
    assert min(span["size"] for span in labels) >= 9


def test_export_binds_cs_budget_and_timing_to_current_blueprint(tmp_path):
    import json
    paper = build_paper2_blueprint(AQA, 26083125)
    path = write_assessment_package(paper, tmp_path / "paper.json", subject="computer_science",
                                   paper_number="2", preview=True, provider=None, model=None)
    data = json.loads(path.read_text())
    assert data.get("assessment_policy", {}).get("candidate_paths") == [{
        "marks": 100, "allotted_minutes": 150.0,
        "assessment_objectives": {"AO1": 56, "AO2": 40, "AO3": 4},
    }]
    data["blueprint"]["questions"][0]["parts"][0]["expected_minutes"] = 2.4
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=r"timing|time"):
        validate_assessment_package(path, subject="computer_science", paper_number="2",
                                    preview=True, provider=None, model=None)


def test_cs_review_identity_changes_with_same_band_but_changed_task_or_time():
    from Backend.Core.model_review import (
        DifficultyReviewResult,
        require_difficulty_review,
        validate_saved_difficulty_evidence,
    )
    profile = profile_for("aqa/computer-science", "1")
    item = {"marks": 4, "prompt": "Write a function.", "assessment_objectives": {"AO3": 4},
            "task_operation": "program", "expected_minutes": 6}
    first = build_item_demand_target(item, profile)
    altered_targets = []
    for altered in ({**item, "task_operation": "design"}, {**item, "expected_minutes": 6.1},
                    {**item, "assessment_objectives": {"AO2": 1, "AO3": 3}}):
        target = build_item_demand_target(altered, profile)
        altered_targets.append(target)
        assert target.demand_band == first.demand_band
        assert target.objective_policy_fingerprint != first.objective_policy_fingerprint

    class Client:
        def generate_json(self, _prompt):
            return DifficultyReviewResult(
                approved=True,
                estimated_demand=first.demand_band,
                reasoning_steps=first.minimum_reasoning_steps,
                tariff_fit=True,
                command_word_fit=True,
                context_fit=True,
                profile_fit=True,
                observed_cognitive_operations=first.required_cognitive_operations,
                estimated_minutes=first.expected_minutes_min,
            ).model_dump(mode="json")

    old = require_difficulty_review(
        Client(),
        item_id="old",
        subject="Computer Science",
        target=first,
        candidate=item,
        specification={},
    )
    with pytest.raises(ValueError, match="objective policy"):
        validate_saved_difficulty_evidence(
            old.model_dump(),
            altered_targets[0],
            item_id="old",
            candidate=item,
        )


@pytest.mark.parametrize("number", ["4(a)", "4(e)", "4(f)", "1(d)"])
@pytest.mark.parametrize("suffix", [" or 97.", " bytes.", "\nAlternative result: 97.", "\n0"])
def test_ocr_deterministic_result_rejects_complete_suffix_contradictions(number, suffix):
    paper = build_paper(load_rule("1"), OCR, 26083125)
    question = next(q for s in paper.sections for o in s.options for q in o.questions if q.number == number)
    solution = IndependentSolver().solve(question, [])
    broken = question.model_copy(deep=True)
    broken.structured_mark_scheme = []
    marker = {"4(a)": "Hexadecimal:", "4(e)": "8-bit result:", "4(f)": "Floating representation:", "1(d)": "Final output:"}[number]
    broken.mark_scheme = [line + suffix if line.startswith(marker) else line for line in question.mark_scheme]
    assert not reconcile_solution(solution, broken).passed


@pytest.mark.parametrize("field", ["chart_values", "stimulus", "prompt"])
def test_ocr_export_rejects_trace_source_drift(field):
    from Backend.Core.computer_science_audit import audit_computer_science_blueprint
    data = build_paper(load_rule("1"), OCR, 26083125).model_dump(mode="json")
    option = data["sections"][0]["options"][0]
    if field == "chart_values":
        option[field][0] += 1
    elif field == "stimulus":
        option[field][1] = option[field][1].replace("print(total)", "print(index)")
    else:
        question = next(q for q in option["questions"] if q["kind"] == "trace")
        question["prompt"] = "Trace the first two iterations only."
    with pytest.raises(ValueError, match="trace source"):
        audit_computer_science_blueprint(data)


def test_cs_candidate_paths_count_selected_options_only():
    from Backend.Core.computer_science_audit import audit_computer_science_blueprint
    part = {"marks": 30, "assessment_objectives": {"AO2": 30}, "expected_minutes": 45}
    data = {"assessment_kind": "question-bank", "total_marks": 30, "duration_minutes": 45,
            "sections": [{"answer_options": 1, "options": [{"questions": [part]}, {"questions": [part]}]}]}
    audit = audit_computer_science_blueprint(data)
    assert len(audit["candidate_paths"]) == 2
    assert all(path["marks"] == 30 and path["allotted_minutes"] == 45 for path in audit["candidate_paths"])
    assert not audit["whole_paper_percentage_target_applied"]
    assert "insufficient topic-specific" in audit["reference_scope"]


def test_discounted_2025_item_is_not_reference_demand_evidence():
    from tools.reference_demand_profiles import _pdf_text, extract_reference_items
    path = ROOT / "Reference Corpus/a-level/aqa/computer-science/computer-science-7517/question-papers/AQA-75171-QP-JUN25.PDF"
    items = extract_reference_items(_pdf_text(path), board="aqa", family_id="aqa/computer-science",
                                    paper_id="1", source_name=path.name)
    assert len(items) == 39 and sum(item["marks"] for item in items) == 100
    assert [i for i, item in enumerate(items) if not item.get("demand_eligible", True)] == [22]
    assert items[22]["marks"] == 1


def test_aqa_programming_requires_implementation_and_authoring_knows_cs_policy():
    from cspapergen.ollama_client import _prompt
    paper = build_paper1_blueprint(AQA, 26083125)[0]
    question = paper.questions[3]
    part = question.parts[0]
    assert part.task_operation == "program"
    assert "program" in part.prompt.lower() and "structured English" not in part.prompt
    assert "run_X" in part.prompt and "run_Y" in part.prompt
    prompt = _prompt(question, "Algorithms", "", paper)
    assert "AO2" in prompt and "computational" in prompt and "AO4" in prompt


def test_ocr_extended_level_policy_uses_three_bands_consistent_with_scheme():
    from Backend.Core.level_of_response import load_level_policies, scale_level_policy
    policies = load_level_policies(ROOT / "Resources/level-of-response-policies.json")
    paper = build_paper(load_rule("2"), OCR, 26083125)
    question = next(q for s in paper.sections for o in s.options for q in o.questions if q.marks == 12)
    policy = scale_level_policy(policies[question.authoring_context["level_policy_id"]], 12)
    assert [(level.minimum_mark, level.maximum_mark) for level in policy.levels] == [(0, 0), (1, 4), (5, 8), (9, 12)]


@pytest.mark.parametrize("task,expected", [
    ("Evidence required: Your PROGRAM SOURCE CODE for the new function.", "program"),
    ("SCREEN CAPTURE(S) showing results of the requested test.", "judge"),
    ("Give the identifiers of variables used in this program.", "analyse"),
    ("Show the contents of the queue after the following actions: enqueue(7), dequeue().", "trace"),
    ("Complete the trace table for the supplied function. Give the final output.", "trace"),
    ("Explain which strings the FSM in Figure 2 accepts.", "analyse"),
    ("Define the term recursion.", "retrieve"),
    ("Complete the table by matching each scheduling policy to its description.", "analyse"),
])
def test_reference_cs_evidence_tasks_survive_layout_spacing_and_later_instructions(task, expected):
    from tools.reference_demand_profiles import extract_reference_items
    text = task.replace(" ", " " * 30) + "\n" + " " * 3500 + "[4 marks]"
    result = extract_reference_items(text, board="aqa", family_id="aqa/computer-science", paper_id="1")
    assert result[0]["cognitive_operation"] == expected


@pytest.mark.parametrize("seed", [26083125, 26083138, 26083139])
def test_ocr_trace_exercises_both_branches_and_prints_every_result(seed, tmp_path):
    import pymupdf
    from ocrcsgen.render_pdf import render_mark_scheme
    paper = build_paper(load_rule("1"), OCR, seed)
    output = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, output)
    with pymupdf.open(output) as pdf:
        text = " ".join(page.get_text() for page in pdf)
    for option in (paper.sections[0].options[0], paper.sections[7].options[0]):
        question = next(q for q in option.questions if q.kind == "trace")
        source = question.authoring_context["cs_input_contract"]
        assert min(source["values"]) < source["threshold"] < max(source["values"])
        assert source["threshold"] in source["values"]
        total = source["initial_total"]
        for index, value in enumerate(source["values"], 1):
            if value > source["threshold"]:
                total += value
            assert f"After iteration {index}, total: {total}." in text
        assert f"Final output: {total}." in text


def test_sql_insert_is_absent_key_and_scheme_has_complete_nonadditive_query():
    question = build_paper2_blueprint(AQA, 26083125).questions[5]
    insert = question.parts[2]
    assert "1900" in insert.prompt and "1900" in " ".join(insert.marking.points)
    assert "1900 is not yet used" in question.stem
    assert "1842" not in insert.prompt
    exemplar = " ".join(question.parts[1].marking.accept)
    assert all(word in exemplar for word in ("SELECT", "JOIN", "GROUP BY", "HAVING", "ORDER BY"))
    assert "non-additive" in exemplar


def test_aqa_boolean_scheme_preserves_operator_glyphs_and_visible_ink(tmp_path):
    import pymupdf
    from cspapergen.render_pdf import render_mark_scheme
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(build_paper2_blueprint(AQA, 26083125), path)
    with pymupdf.open(path) as pdf:
        page = pdf[32]
        assert all(symbol in page.get_text() for symbol in "⊕⊼⊽")
        for symbol in "⊕⊼⊽":
            rect = page.search_for(symbol)[0]
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=rect)
            assert sum(value < 100 for value in pixmap.samples) > 20


@pytest.mark.parametrize("identity", ["aqa/computer-science", "ocr/computer-science", "computer_science", "computer_science_ocr", "AQA Computer Science", "OCR A-level Computer Science", "7517/1", "H446/02"])
def test_supported_cs_aliases_keep_strict_policy(identity):
    from Backend.Core.assessment_objectives import objective_policy_for
    assert objective_policy_for(identity).computational


def test_explicit_unqualified_cambridge_identity_does_not_inherit_aqa_ocr_policy():
    import json

    from Backend.Core.assessment_objectives import objective_policy_for
    from Backend.Core.generator_registry import REGISTRY_PATH
    assert not objective_policy_for("cambridge_international_computer_science").computational
    assert not objective_policy_for("Computer Science", "9618").computational
    family = next(f for f in json.loads(REGISTRY_PATH.read_text())["families"]
                  if "cambridge" in f["id"] and "computer" in f["id"])
    assert not family["advertised"]
    assert all(evidence["state"] == "not_run" for paper in family["papers"]
               for evidence in paper["qualification"].values())


@pytest.mark.parametrize("field,value", [("assessment_objectives", {}), ("expected_minutes", None)])
def test_ocr_saved_metadata_is_not_silently_backfilled(field, value):
    from Backend.Core.exam_blueprints import validate_generated_paper
    rule = load_rule("1")
    paper = build_paper(rule, OCR, 26083125)
    setattr(paper.sections[0].options[0].questions[0], field, value)
    with pytest.raises(ValueError, match="explicit CS"):
        validate_generated_paper(paper, rule, OCR.topic_ids)


def test_ocr_knowledge_tasks_credit_specific_knowledge_without_invented_context():
    paper = build_paper(load_rule("1"), OCR, 26083125)
    for q in [paper.sections[2].options[0].questions[2], paper.sections[5].options[0].questions[1],
              *paper.sections[9].options[0].questions]:
        assert q.command_word == "Describe"
        assert q.assessment_objectives == {"AO1": q.marks}
        points = q.authoring_context["observable_mark_points"]
        assert len(points) == q.marks
        assert not any("linked technical chain" in point or "supplied evidence" in point for point in points)


def test_all_ocr_ao1_explanation_rubrics_credit_concrete_knowledge_features():
    paper = build_paper(load_rule("1"), OCR, 26083125)
    for section in paper.sections:
        for question in section.options[0].questions:
            if question.kind == "analysis" and set(question.assessment_objectives) == {"AO1"}:
                points = question.authoring_context["observable_mark_points"]
                assert len(points) == question.marks
                assert all(not point.startswith(("Accurate knowledge", "A linked technical chain", "Application to the constraints")) for point in points)


@pytest.mark.parametrize("paper_id", ["1", "2"])
@pytest.mark.parametrize("seed", [26083138, 26083139, 26083140])
def test_ocr_printed_scheme_uses_reference_size_and_fits_every_table_cell(paper_id, seed, tmp_path):
    import pymupdf
    from ocrcsgen.render_pdf import (
        MARK_SCHEME_PAGE_PLANS,
        _scheme_page_table,
        render_mark_scheme,
    )
    paper = build_paper(load_rule(paper_id), OCR, seed)
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, path)
    with pymupdf.open(path) as pdf:
        spans = [span for page in pdf for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", []) for span in line["spans"]
                 if "After iteration" in span["text"] or "Credit a" in span["text"]]
        assert spans and all(span["size"] == pytest.approx(11) for span in spans)
    for entries in MARK_SCHEME_PAGE_PLANS[paper.paper_id]:
        items = [(paper.sections[s].options[0].questions[q], segment, count) for s,q,segment,count in entries]
        table = _scheme_page_table(items, (268 if paper_id == "1" else 260) * 72 / 25.4)
        table.wrap(800, 500)
        for row, height in zip(table._cellvalues, table._rowHeights, strict=True):
            for cell, width in zip(row, table._colWidths, strict=True):
                assert cell.wrap(width - 8, 1000)[1] + 7 <= height + .1


@pytest.mark.parametrize("paper_id", ["1", "2"])
def test_ocr_scheme_prints_every_owned_specific_credited_feature(paper_id, tmp_path):
    import pymupdf
    from ocrcsgen.render_pdf import render_mark_scheme
    from ocrcsgen.task_calibration import TASKS
    paper = build_paper(load_rule(paper_id), OCR, 26083125)
    path = tmp_path / "scheme.pdf"
    render_mark_scheme(paper, path)
    with pymupdf.open(path) as pdf:
        text = " ".join(" ".join(page.get_text() for page in pdf).split())
    if paper_id == "2":
        assert "Adding one removes the tested item and makes the interval shrink." in text
        assert "Copy the remaining items once the other sublist is exhausted." in text
    for (component, group, index), (_prompt, points) in TASKS.items():
        if component == int(paper_id):
            for point in points:
                assert " ".join(point.split()) in text, (group, index, point)


def test_ocr_complete_scheme_overflow_preserves_rows_on_continuation_pages():
    from ocrcsgen.render_pdf import _scheme_tables
    paper = build_paper(load_rule("2"), OCR, 26083125)
    questions = paper.sections[5].options[0].questions
    items = [(question, 1, 1) for question in questions] * 3
    tables = _scheme_tables(items, 260 * 72 / 25.4)
    assert len(tables) > 1
    assert sum(len(table._cellvalues) - 1 for table in tables) == len(items)
    for table in tables:
        assert table.wrap(800, 500)[1] <= 479
        for row, height in zip(table._cellvalues, table._rowHeights, strict=True):
            for cell, width in zip(row, table._colWidths, strict=True):
                assert cell.wrap(width - 8, 1000)[1] + 7 <= height + .1


class CSReviewClient:
    supports_parallel_generation = False

    def __init__(self, payload=None, approved=True):
        self.payload = payload or {}
        self.approved = approved
        self.calls = []

    def generate_json(self, prompt):
        review = "second-pass UK A-level assessment editor" in prompt
        self.calls.append("review" if review else "author")
        return ({"approved": self.approved, "factual_issues": [], "marking_issues": [],
                 "source_issues": [], "difficulty_issues": [], "ambiguity_issues": []}
                if review else self.payload)


def test_aqa_fixed_source_transaction_reviews_without_authorship_and_resumes(tmp_path):
    import json

    from cspapergen.cli import ADAPTER
    from cspapergen.ollama_client import improve_questions_with_ollama

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        identity_for_blueprint,
    )
    full = build_paper2_blueprint(AQA, 26083125)
    original = full.questions[5]
    paper = full.model_copy(update={"questions": [original]})
    store = AssessmentCheckpointStore(tmp_path / "checkpoint.json", identity_for_blueprint(
        ADAPTER.checkpoint_identity(paper, None, "2"), provider="test", model="test", prompt_version=ADAPTER.prompt_version))
    client = CSReviewClient()
    messages = []
    result = improve_questions_with_ollama(client, paper, AQA, messages.append, store)
    assert client.calls == ["review"]
    fixed = result.questions[0]
    assert fixed.stem == original.stem and fixed.stimulus == original.stimulus and fixed.parts == original.parts
    assert fixed.provenance == "reviewed-fixed"
    assert fixed.content_review["approved"] is True
    assert any("Reviewed fixed" in message for message in messages)
    resumed = improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    assert resumed == result and client.calls == ["review"]
    full.questions[5] = fixed
    path = tmp_path / "assessment.json"
    write_assessment_package(full, path, subject="AQA A-level Computer Science", paper_number="2", preview=True, provider=None, model=None)
    package = json.loads(path.read_text())
    assert {item["provenance"] for item in package["items"] if ".5.parts." in item["id"]} == {"reviewed-fixed"}
    validate_assessment_package(path, subject="AQA A-level Computer Science", paper_number="2", preview=True, provider=None, model=None)


@pytest.mark.parametrize("mutation", ["stem", "credit", "provenance", "review", "original"])
def test_aqa_immutable_resume_and_export_reject_stale_reviewed_content(tmp_path, mutation):
    from cspapergen.cli import ADAPTER
    from cspapergen.ollama_client import improve_questions_with_ollama

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        identity_for_blueprint,
    )
    full = build_paper2_blueprint(AQA, 26083125)
    paper = full.model_copy(update={"questions": [full.questions[5]]})
    store = AssessmentCheckpointStore(tmp_path / "checkpoint.json", identity_for_blueprint(
        ADAPTER.checkpoint_identity(paper, None, "2"), provider="test", model="test", prompt_version=ADAPTER.prompt_version))
    client = CSReviewClient()
    reviewed = improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    corrupt = reviewed.questions[0].model_copy(deep=True)
    if mutation == "stem":
        corrupt.stem += " Another source row exists."
    elif mutation == "credit":
        corrupt.parts[3].marking.closed_answers = {"first-booking": ["wrong"]}
    elif mutation == "provenance":
        corrupt.provenance = "ai-authored"
    elif mutation == "review":
        corrupt.content_review["approved"] = False
    else:
        paper = paper.model_copy(deep=True)
        paper.questions[0].stem += " This is a separately checked source revision."
    store.save_payload("question-6", corrupt.model_dump(mode="json"))
    if mutation != "original":
        full.questions[5] = corrupt
        with pytest.raises(ValueError, match=r"review|provenance"):
            write_assessment_package(full, tmp_path / "invalid.json", subject="AQA A-level Computer Science", paper_number="2", preview=True, provider=None, model=None)
    result = improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    assert client.calls == ["review", "review"]
    assert result.questions[0].stem == paper.questions[0].stem
    assert result.questions[0].provenance == "reviewed-fixed"


def test_aqa_editable_scenario_receives_actual_content_review():
    from cspapergen.ollama_client import improve_questions_with_ollama
    full = build_paper1_blueprint(AQA, 26083125)[0]
    question = full.questions[0]
    assert question.stimulus is None
    paper = full.model_copy(update={"questions": [question]})
    payload = {"stem": "A marine archive compares keyed retrieval with sequentially arranged observations.", "parts": []}
    client = CSReviewClient(payload)
    result = improve_questions_with_ollama(client, paper, AQA)
    assert client.calls == ["author", "review"]
    assert result.questions[0].stem == payload["stem"]
    assert result.questions[0].parts == question.parts
    assert result.questions[0].provenance == "ai-authored"
    rejecting = CSReviewClient(payload, approved=False)
    with pytest.raises(ValueError, match="second-pass"):
        improve_questions_with_ollama(rejecting, paper, AQA)
    assert rejecting.calls == ["author", "review"] * 3


def test_aqa_editable_resume_revalidates_original_source_and_review_hash(tmp_path):
    from cspapergen.cli import ADAPTER
    from cspapergen.ollama_client import improve_questions_with_ollama

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        identity_for_blueprint,
    )
    full = build_paper1_blueprint(AQA, 26083125)[0]
    paper = full.model_copy(update={"questions": [full.questions[0]]})
    store = AssessmentCheckpointStore(tmp_path / "checkpoint.json", identity_for_blueprint(
        ADAPTER.checkpoint_identity(paper, None, "1"), provider="test", model="test", prompt_version=ADAPTER.prompt_version))
    client = CSReviewClient({"stem": "A marine archive compares keyed retrieval with sequentially arranged observations.", "parts": []})
    result = improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    assert improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store) == result
    assert client.calls == ["author", "review"]
    paper.questions[0].stem += " Records are retained for subsequent comparison."
    improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    assert client.calls == ["author", "review"] * 2


def test_aqa_fixed_content_rejection_never_saves_an_approved_checkpoint(tmp_path):
    from cspapergen.cli import ADAPTER
    from cspapergen.ollama_client import improve_questions_with_ollama

    from Backend.Core.assessment_checkpoints import (
        AssessmentCheckpointStore,
        identity_for_blueprint,
    )
    full = build_paper2_blueprint(AQA, 26083125)
    paper = full.model_copy(update={"questions": [full.questions[5]]})
    store = AssessmentCheckpointStore(tmp_path / "checkpoint.json", identity_for_blueprint(
        ADAPTER.checkpoint_identity(paper, None, "2"), provider="test", model="test", prompt_version=ADAPTER.prompt_version))
    client = CSReviewClient(approved=False)
    with pytest.raises(ValueError, match="second-pass"):
        improve_questions_with_ollama(client, paper, AQA, checkpoint_store=store)
    assert client.calls == ["review"]
    assert store.load_payload("question-6") is None
