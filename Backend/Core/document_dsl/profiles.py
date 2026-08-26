from __future__ import annotations

from functools import cache

from Backend.Core.document_dsl.model import (
    BoardProfile,
    DocumentRole,
    FontToken,
    FontTokens,
    Frame,
    Length,
    RendererContract,
    RuleToken,
    RuleTokens,
)


def _profile(
    profile_id: str,
    *,
    left_mm: float = 18.0,
    right_mm: float = 17.0,
    top_mm: float = 18.0,
    bottom_mm: float = 18.0,
    body_font: str = "Times-Roman",
    bold_font: str = "Times-Bold",
    answer_line_mm: float = 8.0,
) -> BoardProfile:
    page_width = Length.mm(210)
    page_height = Length.mm(297)
    return BoardProfile(
        id=profile_id,
        page_width=page_width,
        page_height=page_height,
        content_frame=Frame(
            x=Length.mm(left_mm),
            y=Length.mm(bottom_mm),
            width=Length.mm(210 - left_mm - right_mm),
            height=Length.mm(297 - top_mm - bottom_mm),
        ),
        safe_print_insets=(Length.mm(5),) * 4,
        fonts=FontTokens(
            body=FontToken(body_font, Length(10), Length(12.4)),
            bold=FontToken(bold_font, Length(10), Length(12.4)),
            small=FontToken(body_font, Length(7.5), Length(9.2)),
            title=FontToken(bold_font, Length(20), Length(23)),
        ),
        rules=RuleTokens(
            hairline=RuleToken(Length(0.35), 0.45),
            standard=RuleToken(Length(0.7), 0.0),
            heavy=RuleToken(Length(1.4), 0.0),
        ),
        answer_line_height=Length.mm(answer_line_mm),
        component_gap=Length.mm(3),
    )


@cache
def board_profile(profile_id: str) -> BoardProfile:
    normalized = profile_id.lower().strip()
    aliases = {
        "edexcel": "pearson-edexcel",
        "pearson": "pearson-edexcel",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized == "aqa":
        return _profile("aqa", left_mm=18, right_mm=17, answer_line_mm=9.0)
    if normalized == "ocr":
        return _profile(
            "ocr",
            left_mm=18,
            right_mm=17,
            body_font="Helvetica",
            bold_font="Helvetica-Bold",
            answer_line_mm=8.5,
        )
    if normalized == "pearson-edexcel":
        return _profile(
            "pearson-edexcel",
            left_mm=16,
            right_mm=16,
            top_mm=16,
            bottom_mm=17,
            body_font="Helvetica",
            bold_font="Helvetica-Bold",
            answer_line_mm=8.0,
        )
    raise KeyError(f"unknown board profile: {profile_id}")


def renderer_contract(
    profile_id: str,
    *,
    roles: tuple[DocumentRole, ...],
    vector_components: tuple[str, ...] = (),
) -> RendererContract:
    return RendererContract(
        profile=board_profile(profile_id),
        document_roles=roles,
        vector_components=vector_components,
    )
