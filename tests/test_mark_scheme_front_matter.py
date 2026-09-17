from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from Backend.Core.mark_scheme_front_matter import (
    COMMON_PAGE_GUIDANCE,
    SUBJECT_GUIDANCE,
    aqa_front_matter_pages,
)


def test_aqa_common_marking_guidance_is_emitted_once_per_scheme() -> None:
    """Shared examiner instructions belong in one introduction, not every section."""
    styles = getSampleStyleSheet()
    flowables = aqa_front_matter_pages(
        "business",
        heading_style=styles["Heading1"],
        body_style=styles["BodyText"],
    )
    headings = [
        flowable.getPlainText()
        for flowable in flowables
        if isinstance(flowable, Paragraph)
    ]

    assert all(headings.count(title) == 1 for title, _ in COMMON_PAGE_GUIDANCE)
    assert all(headings.count(title) == 1 for title, _ in SUBJECT_GUIDANCE["business"])
