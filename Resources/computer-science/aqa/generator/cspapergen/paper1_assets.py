from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen import canvas

from Backend.Core.fonts import register_fonts
from cspapergen.models import Paper1Context, PaperBlueprint


A4 = (595.32, 841.92)
FONT = "AQAArial"
FONT_BOLD = "AQAArial-Bold"
FONT_MONO = "AQACourier"

register_fonts(FONT, FONT_BOLD, FONT_MONO, default_fallback="Times-Roman")


def write_paper1_supporting_files(
    blueprint: PaperBlueprint,
    context: Paper1Context,
    output_dir: Path,
) -> dict[str, Path]:
    preliminary = output_dir / "cs-paper-1-preliminary-material.pdf"
    electronic_answer = output_dir / "cs-paper-1-electronic-answer-document.pdf"
    skeleton = output_dir / "cs-paper-1-skeleton-program.py"
    data_file = output_dir / "cs-paper-1-practice-data.txt"
    render_preliminary_material(blueprint, context, preliminary)
    render_electronic_answer_document(blueprint, electronic_answer)
    skeleton.write_text(context.skeleton_program, encoding="utf-8")
    data_file.write_text(context.data_file, encoding="utf-8")
    return {
        "preliminary_material": preliminary,
        "electronic_answer_document": electronic_answer,
        "skeleton_program": skeleton,
        "data_file": data_file,
    }


def render_preliminary_material(
    blueprint: PaperBlueprint,
    context: Paper1Context,
    output_path: Path,
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    _practice_header(pdf, "PRELIMINARY MATERIAL", blueprint.paper_code)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(55, 735, "A-level COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 15)
    pdf.drawString(55, 706, f"Paper {blueprint.paper_number}: {context.scenario_title}")
    y = 655
    y = _paragraph(
        pdf,
        y,
        "This independently created practice scenario must be used with the supplied Python 3 Skeleton Program and data file.",
    )
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(55, y - 8, "Scenario")
    y = _paragraph(pdf, y - 34, context.scenario_summary)
    y = _paragraph(
        pdf,
        y,
        f"Each {context.record_name} has a unique integer identifier, a category and an integer value. "
        "The supplied program can load records, calculate adjusted values and identify the best record.",
    )
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(55, y - 8, "Valid categories")
    y -= 34
    pdf.setFont(FONT, 10.5)
    for category in context.category_names:
        pdf.drawString(70, y, f"• {category}")
        y -= 18
    pdf.setFont(FONT_BOLD, 12)
    pdf.drawString(55, y - 6, "Commands")
    y -= 34
    commands = [
        ("ADD", "validate and add one record"),
        ("REPORT", "show ordered totals and category leaders"),
        ("BEST", "show the record with the greatest adjusted value"),
        ("QUIT", "end the program"),
    ]
    for command, purpose in commands:
        pdf.setFont(FONT_BOLD, 10)
        pdf.drawString(70, y, command)
        pdf.setFont(FONT, 10)
        pdf.drawString(150, y, purpose)
        y -= 20
    _page_footer(pdf, 1, blueprint.paper_code)
    pdf.showPage()

    _practice_header(pdf, "PRELIMINARY MATERIAL", blueprint.paper_code)
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, 750, "Supplied files")
    y = 720
    supplied = [
        ("cs-paper-1-skeleton-program.py", "Python 3 Skeleton Program"),
        ("cs-paper-1-practice-data.txt", "comma-separated practice data"),
        ("cs-paper-1-electronic-answer-document.pdf", "response document"),
    ]
    for name, purpose in supplied:
        pdf.setFont(FONT_MONO, 9)
        pdf.drawString(70, y, name)
        pdf.setFont(FONT, 9.5)
        pdf.drawString(315, y, purpose)
        y -= 24
    y -= 10
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, y, "Preparation")
    y = _paragraph(
        pdf,
        y - 30,
        "Run the unmodified Skeleton Program with the supplied data file. Review each function, the data model and the command loop. During the practice assessment, save working copies frequently and include requested evidence in the Electronic Answer Document.",
    )
    pdf.setFont(FONT_BOLD, 13)
    pdf.drawString(55, y - 8, "Data format")
    y -= 38
    pdf.setFont(FONT_MONO, 10)
    pdf.drawString(70, y, "identifier,category,value")
    y -= 24
    pdf.setFont(FONT, 10)
    pdf.drawString(70, y, "Example structure only; use the unique supplied data file for calculations.")
    _page_footer(pdf, 2, blueprint.paper_code)
    pdf.save()


def render_electronic_answer_document(
    blueprint: PaperBlueprint,
    output_path: Path,
) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=0)
    page = 1
    _practice_header(pdf, "ELECTRONIC ANSWER DOCUMENT", blueprint.paper_code)
    pdf.setFont(FONT_BOLD, 20)
    pdf.drawString(55, 735, "A-level COMPUTER SCIENCE")
    pdf.setFont(FONT_BOLD, 15)
    pdf.drawString(55, 704, "Paper 1 response document")
    pdf.setFont(FONT, 10)
    pdf.drawString(55, 650, "Candidate name")
    pdf.line(150, 648, 500, 648)
    pdf.drawString(55, 615, "Candidate number")
    pdf.line(160, 613, 310, 613)
    _paragraph(
        pdf,
        560,
        "Type or write each response in the matching numbered area. For programming tasks, include your final code and concise test evidence. This is an unofficial practice document.",
    )
    _page_footer(pdf, page, blueprint.paper_code)
    pdf.showPage()

    for question in blueprint.questions:
        for part in question.parts:
            page += 1
            _practice_header(pdf, "ELECTRONIC ANSWER DOCUMENT", blueprint.paper_code)
            pdf.setFont(FONT_BOLD, 14)
            pdf.drawString(55, 755, f"Question {question.number}.{part.label}")
            pdf.setFont(FONT, 9.5)
            y = 725
            for line in _wrap(part.prompt, 88):
                pdf.drawString(55, y, line)
                y -= 13
            y -= 8
            pdf.setFont(FONT_BOLD, 9)
            pdf.drawRightString(535, y, f"[{part.marks} marks]")
            y -= 20
            height = max(280, y - 100)
            pdf.acroForm.textfield(
                name=f"question_{question.number}_{part.label}",
                tooltip=f"Response to question {question.number}.{part.label}",
                x=55,
                y=80,
                width=480,
                height=height,
                borderColor=colors.HexColor("#6f6f6f"),
                fillColor=colors.white,
                textColor=colors.black,
                borderWidth=1,
                borderStyle="solid",
                fontName="Helvetica",
                fontSize=10,
                forceBorder=True,
                fieldFlags="multiline",
            )
            _page_footer(pdf, page, blueprint.paper_code)
            pdf.showPage()
    pdf.save()


def _practice_header(pdf: canvas.Canvas, document: str, code: str) -> None:
    pdf.setFont(FONT_BOLD, 8)
    pdf.drawCentredString(297, 820, f"UNOFFICIAL PRACTICE {document}")
    pdf.setFont(FONT, 8)
    pdf.drawRightString(540, 800, code)


def _page_footer(pdf: canvas.Canvas, page: int, code: str) -> None:
    pdf.setFont(FONT, 8)
    pdf.drawCentredString(297, 30, str(page))
    pdf.drawRightString(540, 30, f"PRACTICE/{code}")


def _paragraph(pdf: canvas.Canvas, y: float, text: str) -> float:
    pdf.setFont(FONT, 10.5)
    for line in _wrap(text, 90):
        pdf.drawString(55, y, line)
        y -= 15
    return y - 10


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]
