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
        validate_saved_difficulty_evidence,
    )
    profile = profile_for("aqa/computer-science", "1")
    item = {"marks": 4, "prompt": "Write a function.", "assessment_objectives": {"AO3": 4},
            "task_operation": "program", "expected_minutes": 6}
    first = build_item_demand_target(item, profile)
    for altered in ({**item, "task_operation": "design"}, {**item, "expected_minutes": 6.1},
                    {**item, "assessment_objectives": {"AO2": 1, "AO3": 3}}):
        target = build_item_demand_target(altered, profile)
        assert target.demand_band == first.demand_band
        assert target.objective_policy_fingerprint != first.objective_policy_fingerprint
    old = DifficultyReviewResult(approved=True, estimated_demand="standard", reasoning_steps=2,
        tariff_fit=True, command_word_fit=True, context_fit=True, profile_fit=True,
        solution_integrity_version="closed-numeric-v2")
    with pytest.raises(ValueError, match="objective policy"):
        validate_saved_difficulty_evidence(old.model_dump(), first, item_id="old")


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
