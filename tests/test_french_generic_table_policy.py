"""Versioned host table layout, not model-content or paper qualification."""

from copy import deepcopy

import pytest
from reportlab.lib.styles import ParagraphStyle

from Backend.Core.france import llm_pdf, rendering
from Backend.Core.france import llm_pipeline as pipeline
from Backend.Core.france.llm_pipeline import PRINT_POLICY, validate_authored_exercise
from Backend.Core.france.nsi import NSITableMaterial
from Backend.Core.france.print_policy import (
    V34_PRINT_POLICY,
    V35_PRINT_POLICY,
    V36_FOREIGN_EDGE_PRINT_POLICIES,
    V36_GENERIC_TABLE_PRINT_POLICIES,
    V36_GRAPH_PRINT_POLICY,
    V36_PRINT_POLICIES,
)
from tests.test_french_llm_pdf import exercises, render
from tests.test_french_llm_pipeline import generate, raw_exercise
from tests.test_french_reviewed_redraft import ReviewedClient

COLLIDING_IDS = ("trace_initial", "trace_fermeture", "route_double_fermeture")
OLD_POLICIES = (
    None,
    V34_PRINT_POLICY,
    V35_PRINT_POLICY,
    *(f"fr-nsi-v36-model-review-v{version}" for version in range(1, 5)),
)


def material(identifier, columns, rows):
    return NSITableMaterial(
        kind="table",
        id=identifier,
        title="Generic data table",
        columns=tuple(f"Column {column}" for column in range(columns)),
        rows=tuple(
            tuple(f"R{row}C{column}" for column in range(columns))
            for row in range(rows)
        ),
    )


def table_for(source, **kwargs):
    block = rendering.structured_material(
        source,
        body=ParagraphStyle("table", fontName="Helvetica", fontSize=12, leading=15),
        bold_font="Helvetica-Bold",
        regular_font="Helvetica",
        available_width=440,
        **kwargs,
    )
    return next(item for item in block._content if hasattr(item, "_rowHeights"))


@pytest.mark.parametrize("identifier", ["donnees", *COLLIDING_IDS])
@pytest.mark.parametrize("columns,rows", [(2, 2), (3, 1), (8, 4)])
def test_new_policy_uses_dimensions_not_material_identity(identifier, columns, rows):
    source = material(identifier, columns, rows)
    before = source.model_dump(mode="json")
    table = table_for(
        source, generic_tables=PRINT_POLICY in V36_GENERIC_TABLE_PRINT_POLICIES
    )
    assert table._nrows == rows + 1
    assert table._colWidths == [440 / columns] * columns
    assert table._rowHeights == [None] * (rows + 1)
    assert source.model_dump(mode="json") == before


@pytest.mark.parametrize("identifier", COLLIDING_IDS)
@pytest.mark.parametrize("explicit", [False, True])
def test_default_and_explicit_legacy_working_space_is_unchanged(identifier, explicit):
    trace = identifier != "route_double_fermeture"
    source = material(identifier, 7 if trace else 2, 4 if trace else 1)
    table = table_for(source, **({"generic_tables": False} if explicit else {}))
    assert table._rowHeights == ([None, *([38] * 4)] if trace else [None, 72])
    assert table._colWidths == (
        [440 * 0.3, *([440 * 0.7 / 6] * 6)] if trace else [220, 220]
    )


@pytest.mark.parametrize("policy", [*OLD_POLICIES, PRINT_POLICY])
def test_resolved_host_policy_selects_table_scope_without_model_fields(
    tmp_path, monkeypatch, policy
):
    observed = []
    original = rendering.structured_material

    def capture(*args, **kwargs):
        observed.append((kwargs["generic_tables"], kwargs["avoid_foreign_graph_edges"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(rendering, "structured_material", capture)
    monkeypatch.setattr(
        rendering.SimpleDocTemplate, "build", lambda *_args, **_kwargs: None
    )
    path = tmp_path / "not-created.pdf"
    rendering.render_assessment(
        path, exercises(), correction=False, print_policy=policy
    )
    assert observed
    assert set(observed) == {
        (policy == PRINT_POLICY, policy in V36_FOREIGN_EDGE_PRINT_POLICIES)
    }
    assert not path.exists()


def test_policy_membership_keeps_all_historical_versions():
    assert PRINT_POLICY == "fr-nsi-v36-model-review-v5"
    assert V36_GRAPH_PRINT_POLICY == "fr-nsi-v36-model-review-v4"
    assert {f"fr-nsi-v36-model-review-v{i}" for i in range(1, 6)} == V36_PRINT_POLICIES
    assert {PRINT_POLICY} == V36_GENERIC_TABLE_PRINT_POLICIES
    assert {V36_GRAPH_PRINT_POLICY, PRINT_POLICY} == V36_FOREIGN_EDGE_PRINT_POLICIES


def test_unknown_policy_still_refuses_before_creating_a_pdf(tmp_path):
    path = tmp_path / "not-created.pdf"
    with pytest.raises(ValueError, match="policy"):
        rendering.render_assessment(path, [], correction=False, print_policy="unknown")
    assert not path.exists()


def test_recovery_evidence_is_bound_to_current_policy_not_historical_layout(tmp_path):
    with pytest.raises(pipeline.SemanticReviewRefusal) as caught:
        generate(tmp_path, ReviewedClient(refuse_rounds=(1, 2)))
    details = caught.value.details
    assert details["recovery_identity"]["print_policy"] == PRINT_POLICY
    pipeline.validate_rejected_rounds(details)
    for policy in OLD_POLICIES:
        changed = deepcopy(details)
        changed["recovery_identity"]["print_policy"] = policy
        with pytest.raises(ValueError, match="Identité du refus modifiée"):
            pipeline.validate_rejected_rounds(changed)


def collision_exercises():
    result = []
    for identifier, table_id in zip(("1", "2", "3"), COLLIDING_IDS, strict=True):
        raw = raw_exercise(identifier)
        raw["materials"][0]["id"] = table_id
        for question in raw["questions"]:
            question["material_ids"] = [table_id]
        before = deepcopy(raw)
        result.append(validate_authored_exercise(raw, identifier, large_print=False))
        assert raw == before
    return result


@pytest.mark.parametrize("correction", [False, True])
@pytest.mark.parametrize("large_print", [False, True])
def test_real_v5_pdf_accepts_all_colliding_generic_table_ids(
    tmp_path, correction, large_print
):
    source = collision_exercises()
    path = tmp_path / "generic-tables.pdf"
    render(path, source, correction=correction, large_print=large_print)
    llm_pdf.validate_llm_pdf(
        path,
        source,
        correction=correction,
        large_print=large_print,
        print_policy=PRINT_POLICY,
    )
