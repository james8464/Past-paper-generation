from __future__ import annotations

import ast
import copy
import hashlib
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, Spacer, Table

from Backend.Core.document_dsl import (
    aqa_lozenge,
    aqa_section_intro,
    flowable_question_block,
    independent_practice_page,
    page_sequence,
)

ROOT = Path(__file__).resolve().parents[1]
SHARED_FURNITURE_NAMES = {
    "_answer_lines",
    "_cover",
    "_draw_dotted_answer_rule",
    "_draw_footer_barcode",
    "_page_sequence",
}


def test_every_family_renderer_imports_the_shared_document_dsl() -> None:
    missing_imports: list[str] = []

    for renderer in sorted(ROOT.glob("Resources/**/generator/**/render_pdf.py")):
        imports = {
            node.module
            for node in ast.parse(renderer.read_text(encoding="utf-8")).body
            if isinstance(node, ast.ImportFrom)
        }
        if not any(
            module == "Backend.Core.document_dsl"
            or module.startswith("Backend.Core.document_dsl.")
            for module in imports
            if module is not None
        ):
            missing_imports.append(str(renderer.relative_to(ROOT)))

    assert missing_imports == [], (
        "family renderers must use Backend.Core.document_dsl: "
        + repr(missing_imports)
    )


def test_shared_flowable_furniture_preserves_the_measured_contract() -> None:
    sample_styles = getSampleStyleSheet()
    styles = {
        "centre_bold": sample_styles["Heading2"],
        "instruction": sample_styles["BodyText"],
        "heading": sample_styles["Heading2"],
        "small": sample_styles["BodyText"],
    }
    section = SimpleNamespace(id="A", instructions="Answer every question.")
    question = SimpleNamespace(number="01", prompt="Calculate the value.", marks=2)

    intro = aqa_section_intro(
        section,
        styles=styles,
        ink=colors.HexColor("#181818"),
    )
    practice = independent_practice_page(
        styles=styles,
    )
    block = flowable_question_block(
        question,
        question_table=lambda item: Paragraph(item.prompt, sample_styles["BodyText"]),
    )
    pages = page_sequence([[Paragraph("One", sample_styles["BodyText"])], block])

    assert isinstance(intro[0], Table)
    assert isinstance(intro[1], Spacer)
    assert isinstance(practice[0], Spacer)
    assert isinstance(aqa_lozenge(colors.HexColor("#181818")), object)
    assert isinstance(block[-1], Spacer)
    assert [type(flowable) for flowable in pages] == [
        PageBreak,
        Paragraph,
        PageBreak,
        Paragraph,
        Spacer,
    ]


def test_family_renderers_do_not_repeat_identical_top_level_functions() -> None:
    groups: dict[str, list[str]] = defaultdict(list)
    renderers = sorted(ROOT.glob("Resources/**/generator/**/render_pdf.py"))

    for renderer in renderers:
        for node in ast.parse(renderer.read_text(encoding="utf-8")).body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            normalised = copy.deepcopy(node)
            normalised.name = "_shared_candidate"
            fingerprint = hashlib.sha256(
                ast.dump(normalised, include_attributes=False).encode("utf-8")
            ).hexdigest()
            groups[fingerprint].append(
                f"{renderer.relative_to(ROOT)}:{node.lineno} {node.name}"
            )

    repeated = [locations for locations in groups.values() if len(locations) > 1]

    assert repeated == [], (
        "move repeated renderer functions into document_dsl: " + repr(repeated)
    )


def test_family_renderers_do_not_reintroduce_shared_page_furniture() -> None:
    local_furniture: list[str] = []

    for renderer in sorted(ROOT.glob("Resources/**/generator/**/render_pdf.py")):
        for node in ast.parse(renderer.read_text(encoding="utf-8")).body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and node.name in SHARED_FURNITURE_NAMES:
                local_furniture.append(
                    f"{renderer.relative_to(ROOT)}:{node.lineno} {node.name}"
                )

    assert local_furniture == [], (
        "use the shared document_dsl page furniture: " + repr(local_furniture)
    )
