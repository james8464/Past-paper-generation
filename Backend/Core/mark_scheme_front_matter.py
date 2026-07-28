from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer


SUBJECT_GUIDANCE = {
    "accounting": [
        ("Applying the mark scheme", "Read the complete response before awarding marks. Credit a valid accounting treatment when it is applied consistently and answers the requirement."),
        ("Workings and own figures", "Award method marks where workings make the intended method clear. Apply the own-figure rule to a later result that follows correctly from an earlier error."),
        ("Narrative responses", "Credit precise accounting terminology, developed consequences and conclusions supported by the figures or circumstances in the question."),
        ("Levels-based marking", "Choose the level that best describes the response as a whole, then use accuracy, development and judgement to select a mark within that level."),
        ("Quality of presentation", "Require clear labels, appropriate units and a recognisable accounting format. Do not penalise an alternative layout that communicates the same information."),
        ("Final checks", "Check that distinct marks reward distinct work, totals do not exceed the question maximum and valid alternative routes have received equivalent credit."),
    ],
    "business": [
        ("Applying the mark scheme", "Read the whole response before awarding marks. Credit accurate business knowledge only where it answers the question set."),
        ("Application and analysis", "Application must use the case evidence. Analysis must connect that evidence to a developed effect on the business, its decision or its stakeholders."),
        ("Evaluation", "Judge the quality of the argument as a whole. A supported conclusion should weigh the evidence, uncertainty, timescale and relative importance of the factors considered."),
    ],
    "economics": [
        ("Applying the mark scheme", "Credit accurate economic reasoning that answers the question. Do not reward the same developed point twice, and accept a valid alternative analytical route."),
        ("Assessment objectives", "Knowledge must be precise, application must use the context, analysis must show a connected transmission mechanism, and evaluation must support its final judgement."),
    ],
}


def aqa_front_matter_pages(
    subject: str,
    *,
    heading_style,
    body_style,
) -> list[Flowable]:
    pages: list[Flowable] = []
    for title, guidance in SUBJECT_GUIDANCE[subject]:
        pages.extend(
            [
                Paragraph(title, heading_style),
                Spacer(1, 6 * mm),
                Paragraph(guidance, body_style),
                Spacer(1, 6 * mm),
                Paragraph(
                    "This guidance is written for this independent practice mark scheme "
                    "and should be applied consistently to every candidate response.",
                    body_style,
                ),
                PageBreak(),
            ]
        )
    return pages
