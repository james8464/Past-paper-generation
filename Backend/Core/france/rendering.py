"""Provisional French paper layout measured from the 2026 Métropole NSI paper."""

import re
from decimal import Decimal
from math import atan2, cos, pi, sin
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from Backend.Core.fonts import register_font, register_fonts
from Backend.Core.france.nsi import (
    LANGUAGE_RUBRIC_2027,
    NSIExercise,
    NSITableMaterial,
    NSIWeightedGraphMaterial,
)


def printable_database_criterion(criterion: str) -> str:
    """Remove source Markdown delimiters without mutating replayable rubric data."""
    return " ".join(re.sub(r"```(?:sql|python)?", " ", criterion).split())


def exercise_scope_text(title: str) -> str:
    scope = title.strip().rstrip(".")
    if scope.lower().startswith("cet exercice"):
        return f"{scope}."
    return f"Thème de l'exercice : « {scope} »."


def structured_material(
    material: NSITableMaterial | NSIWeightedGraphMaterial,
    *,
    body: ParagraphStyle,
    bold_font: str,
    regular_font: str,
    available_width: float,
    show_id: bool = True,
):
    heading = (
        f"{material.title} — {material.id}"
        if show_id and isinstance(material, NSITableMaterial)
        else material.title
    )
    title = Paragraph(escape(heading), body)
    if isinstance(material, NSITableMaterial):
        rows = [
            [Paragraph(escape(value), body) for value in material.columns],
            *[
                [Paragraph(escape(value), body) for value in row]
                for row in material.rows
            ],
        ]
        table = Table(
            rows,
            colWidths=[available_width / len(material.columns)] * len(material.columns),
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                    ("FONTNAME", (0, 0), (-1, 0), bold_font),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return KeepTogether([title, Spacer(1, 4), table, Spacer(1, 10)])

    width = min(available_width, 440)
    height = min(280, max(180, 42 * len(material.nodes)))
    drawing = Drawing(width, height)
    centre_x, centre_y = width / 2, height / 2
    radius = min(width * 0.34, height * 0.34)
    app_graph_pairs = {
        tuple(sorted(pair))
        for pair in (
            ("A", "B"),
            ("B", "C"),
            ("C", "D"),
            ("D", "E"),
            ("E", "F"),
            ("A", "C"),
            ("B", "D"),
            ("C", "E"),
            ("D", "F"),
        )
    }
    if (
        not material.directed
        and material.id == "reseau"
        and set(material.nodes) == set("ABCDEF")
        and {tuple(sorted((start, end))) for start, end, _ in material.edges}
        == app_graph_pairs
    ):
        # The app-owned E1 graph is a ladder, not a cycle. Two rows keep all
        # nine edges visible without the crossings produced by circular order.
        positions = {
            node: (width * x, height * y)
            for node, x, y in (
                ("A", 0.15, 0.75),
                ("B", 0.15, 0.25),
                ("C", 0.50, 0.75),
                ("D", 0.50, 0.25),
                ("E", 0.85, 0.75),
                ("F", 0.85, 0.25),
            )
        }
    else:
        positions = {
            node: (
                centre_x + radius * cos(-pi / 2 + 2 * pi * index / len(material.nodes)),
                centre_y + radius * sin(-pi / 2 + 2 * pi * index / len(material.nodes)),
            )
            for index, node in enumerate(material.nodes)
        }
    for start, end, weight in material.edges:
        x1, y1 = positions[start]
        x2, y2 = positions[end]
        drawing.add(Line(x1, y1, x2, y2, strokeWidth=1.2))
        if material.directed:
            angle = atan2(y2 - y1, x2 - x1)
            tip_x = x2 - 16 * cos(angle)
            tip_y = y2 - 16 * sin(angle)
            drawing.add(
                Polygon(
                    [
                        tip_x,
                        tip_y,
                        tip_x - 7 * cos(angle - 0.45),
                        tip_y - 7 * sin(angle - 0.45),
                        tip_x - 7 * cos(angle + 0.45),
                        tip_y - 7 * sin(angle + 0.45),
                    ],
                    fillColor=colors.black,
                    strokeColor=colors.black,
                )
            )
        label = str(weight)
        label_x = (x1 + x2) / 2 + 5
        label_y = (y1 + y2) / 2 + 5
        drawing.add(
            Rect(
                label_x - 3,
                label_y - 3,
                stringWidth(label, regular_font, 9) + 6,
                12,
                fillColor=colors.white,
                strokeColor=None,
            )
        )
        drawing.add(
            String(
                label_x,
                label_y,
                label,
                fontName=regular_font,
                fontSize=9,
            )
        )
    for node, (x, y) in positions.items():
        drawing.add(Circle(x, y, 16, fillColor=colors.white, strokeWidth=1.2))
        drawing.add(
            String(
                x,
                y - 3,
                node,
                textAnchor="middle",
                fontName=bold_font,
                fontSize=8,
            )
        )
    return KeepTogether([title, Spacer(1, 4), drawing, Spacer(1, 10)])


def code_listing(source: str, style: ParagraphStyle, available_width: float):
    """Never rewrite executable text to make it fit a page."""
    if any(
        stringWidth(line, style.fontName, style.fontSize) > available_width
        for line in source.splitlines()
    ):
        raise ValueError(
            "Une ligne de code dépasse la largeur disponible. Reformuler le "
            "programme sans modifier son résultat avant de publier le PDF."
        )
    return Preformatted(source, style, dedent=0)


class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self.setFont("ExamSans", 9)
            self.drawString(
                70, 43, "Paper Creator — entraînement non officiel — non relu"
            )
            self.setFont("ExamSans", 10)
            self.drawRightString(A4[0] - 54, 43, f"Page : {self._pageNumber} / {total}")
            super().showPage()
        super().save()


def draw_cover_page(
    canvas: Canvas,
    doc: SimpleDocTemplate,
    *,
    correction: bool,
    large_print: bool,
    regular_font: str,
    bold_font: str,
    italic_font: str,
) -> None:
    """Draw the cover from measured 2026 coordinates, with independent branding."""

    width, height = A4
    scale = 1.15 if large_print else 1.0

    def centred(text: str, top: float, size: float, font: str) -> None:
        canvas.setFont(font, size * scale)
        # The offset approximates the baseline used by the measured Arial source.
        canvas.drawCentredString(width / 2, height - top - size * scale, text)

    centred("BACCALAURÉAT GÉNÉRAL", 79, 20, regular_font)
    centred("ÉPREUVE D’ENSEIGNEMENT DE SPÉCIALITÉ", 136, 11, regular_font)
    centred("SESSION 2027", 203, 14, bold_font)
    centred("NUMÉRIQUE ET SCIENCES INFORMATIQUES", 297, 20, bold_font)
    centred(
        "CORRIGÉ PROPOSÉ ET BARÈME INDICATIF"
        if correction
        else "SUJET D’ENTRAÎNEMENT — NON OFFICIEL",
        376,
        14,
        bold_font,
    )
    centred("Durée de l’épreuve : 3 heures 30", 447, 11, regular_font)
    if correction:
        centred(
            "Document de travail pour la relecture pédagogique.", 515, 11, italic_font
        )
        centred(
            "Réponses et crédits à vérifier avant toute évaluation.",
            560,
            11,
            regular_font,
        )
    else:
        centred("L’usage de la calculatrice n’est pas autorisé.", 515, 11, italic_font)
        centred(
            "Dès que ce sujet vous est remis, assurez-vous qu’il est complet.",
            560,
            11,
            regular_font,
        )
    centred(
        "Ce document doit être relu par un enseignant avant toute utilisation.",
        583,
        11,
        regular_font,
    )
    centred(
        "Évaluation : 18 points techniques et 2 points pour la maîtrise de la langue.",
        610,
        11,
        regular_font,
    )
    centred(
        "Trois exercices indépendants - corrigé proposé."
        if correction
        else "Le sujet est composé de trois exercices indépendants.",
        650,
        15,
        bold_font,
    )
    centred(
        "Barème et variantes à confirmer par un enseignant."
        if correction
        else "Le candidat traite les trois exercices.",
        678,
        15,
        bold_font,
    )

    canvas.setTitle(
        "NSI - corrigé proposé et barème indicatif"
        if correction
        else "NSI - sujet d'entraînement non officiel"
    )
    canvas.setAuthor("Paper Creator")


def render_assessment(
    path: Path,
    exercises: list[NSIExercise],
    *,
    correction: bool,
    large_print: bool = False,
):
    faces = register_fonts("ExamSans", "ExamSans-Bold", "ExamSans-Italic")
    regular = faces["ExamSans"]
    bold = faces["ExamSans-Bold"]
    italic = faces["ExamSans-Italic"]
    mono = register_font("AQACourier", fallback="Courier")
    size = 16 if large_print else 12
    body = ParagraphStyle(
        "NSIBody",
        fontName=regular,
        fontSize=size,
        leading=size * 1.25,
        spaceAfter=6 if correction else 10,
    )
    heading = ParagraphStyle(
        "NSIHeading",
        parent=body,
        fontName=bold,
        fontSize=13 if not large_print else 17,
        leading=16 if not large_print else 21,
        spaceBefore=10,
        spaceAfter=8,
        keepWithNext=True,
    )
    exercise_heading = ParagraphStyle(
        "NSIExerciseHeading",
        parent=body,
        fontName=bold,
        alignment=1,
        fontSize=14 if not large_print else 18,
        leading=18 if not large_print else 23,
        spaceBefore=0,
        spaceAfter=15,
        keepWithNext=True,
    )
    exercise_scope = ParagraphStyle(
        "NSIExerciseScope",
        parent=body,
        fontName=italic,
        spaceBefore=6,
        spaceAfter=6 if correction else 10,
        keepWithNext=True,
    )
    question_style = ParagraphStyle(
        "NSIQuestion",
        parent=body,
        leftIndent=30,
        firstLineIndent=0,
        bulletIndent=6,
        bulletFontName=regular,
        bulletFontSize=size,
        spaceAfter=4 if correction else 10,
    )
    question_followup = ParagraphStyle(
        "NSIQuestionFollowup",
        parent=body,
        leftIndent=30,
        spaceAfter=6 if correction else 10,
    )
    code = ParagraphStyle(
        "NSICode", parent=body, fontName=mono, fontSize=size, leading=size * 1.2
    )
    trace_row = ParagraphStyle("NSITraceRow", parent=body, leftIndent=12, spaceAfter=2)
    credit = ParagraphStyle(
        "NSICredit",
        parent=body,
        fontName=bold,
        spaceBefore=3 if correction else 4,
        spaceAfter=2 if correction else 4,
        keepWithNext=True,
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=70,
        rightMargin=54,
        topMargin=60,
        bottomMargin=65,
        title=(
            "NSI - corrigé proposé et barème indicatif"
            if correction
            else "NSI - sujet d'entraînement non officiel"
        ),
        author="Paper Creator",
        pageCompression=1,
    )
    # Platypus frames reserve six points of padding on each side.
    story = [Spacer(1, doc.height - 14), PageBreak()]

    def paragraph(text, style=body):
        story.append(Paragraph(escape(text).replace("\n", "<br/>"), style))

    def content(text, *, paragraph_style=body):
        first_paragraph = True
        for position, part in enumerate(
            re.split(r"```(?:python|sql)?[ \t]*(?:\r?\n)?", text)
        ):
            if not part.strip():
                continue
            if position % 2:
                story.append(
                    code_listing(
                        part.strip("\n"),
                        code,
                        doc.width - 12,
                    )
                )
            else:
                paragraph(part.strip(), paragraph_style if first_paragraph else body)
                first_paragraph = False

    def network_depth_trace_answer(answer: str) -> None:
        marker = (
            "Après le changement, trace de Dijkstra "
            "(sommet fixé et distances provisoires) : "
        )
        introduction, separator, remainder = answer.partition(marker)
        trace, ending, conclusion = remainder.partition(". Le nouveau trajet ")
        rows = trace.split("; ")
        if not separator or not ending or len(rows) != 5:
            raise ValueError("Network depth correction trace is incomplete")
        paragraph(introduction + marker)
        for index, row in enumerate(rows):
            paragraph(row + (";" if index < len(rows) - 1 else "."), trace_row)
        paragraph("Le nouveau trajet " + conclusion)

    def question_content(identifier: str, text: str) -> None:
        first_paragraph = True
        for position, part in enumerate(
            re.split(r"```(?:python|sql)?[ \t]*(?:\r?\n)?", text)
        ):
            if not part.strip():
                continue
            if position % 2:
                story.append(code_listing(part.strip("\n"), code, doc.width - 42))
            else:
                value = escape(part.strip()).replace("\n", "<br/>")
                story.append(
                    Paragraph(
                        value,
                        question_style if first_paragraph else question_followup,
                        bulletText=f"{identifier}.",
                    )
                    if first_paragraph
                    else Paragraph(value, question_followup)
                )
                first_paragraph = False

    def point_label(value: str) -> str:
        numeric = value.replace(".", ",")
        return f"{numeric} point" if Decimal(value) <= 1 else f"{numeric} points"

    if correction:
        paragraph("Consignes générales de correction", heading)
        paragraph(
            "Barème indicatif : attribuer uniquement les crédits explicitement justifiés. Accepter une méthode équivalente correcte. Ne pas compter deux fois le même élément. Faire vérifier les réponses, variantes et cas limites par un enseignant avant toute utilisation évaluative."
        )
        paragraph(
            "Maîtrise de la langue - 2 points sur l'ensemble de la copie", heading
        )
        paragraph(
            "Apprécier l'orthographe, la syntaxe, la précision du vocabulaire et l'organisation du raisonnement conformément à la grille nationale. La répartition détaillée entre ces dimensions n'est pas présentée comme officielle. Cette application ne note pas les copies des élèves."
        )
        rubric_rows = [["Appréciation globale", "Points indicatifs"]]
        rubric_rows.extend(
            [
                band["label"],
                LANGUAGE_RUBRIC_2027["indicative_points"][band["id"]].replace(".", ","),
            ]
            for band in LANGUAGE_RUBRIC_2027["bands"]
        )
        rubric = Table(rubric_rows, colWidths=[doc.width * 0.72, doc.width * 0.28])
        rubric.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                    ("FONTNAME", (0, 0), (-1, 0), bold),
                    ("FONTNAME", (0, 1), (-1, -1), regular),
                    ("FONTSIZE", (0, 0), (-1, -1), size),
                    ("LEADING", (0, 0), (-1, -1), size * 1.2),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([Spacer(1, 5), rubric, Spacer(1, 8)])
        paragraph(
            "Profil indicatif du logiciel, non barème officiel : retenir une appréciation globale à partir des quatre dimensions officielles (orthographe, syntaxe, lexique et organisation du raisonnement)."
        )
    v18_paper = any(
        question.verification.get("kind") == "network_reasoning_contract"
        for exercise in exercises
        for question in exercise.questions
    )
    for exercise_index, exercise in enumerate(exercises):
        if correction or exercise_index:
            story.append(PageBreak())
        paragraph(
            f"Exercice {exercise.id} ({exercise.target_points.replace('.', ',')} points)",
            exercise_heading,
        )
        paragraph(exercise_scope_text(exercise.title), exercise_scope)
        content(exercise.context)
        staged_network_materials = bool(exercise.questions) and all(
            question.verification.get("kind")
            in {
                "network_reasoning_contract",
                "graph_resilience_contract",
                "database_audit_contract",
            }
            for question in exercise.questions
        )
        staged_material_ids: set[str] = set()

        def add_material(material, *, show_id=exercise.id != "3"):
            story.append(
                structured_material(
                    material,
                    body=body,
                    bold_font=bold,
                    regular_font=regular,
                    available_width=doc.width,
                    show_id=show_id,
                )
            )

        if not staged_network_materials:
            for material in exercise.materials:
                add_material(material)
        final_network_pair_start = None
        for question_index, question in enumerate(exercise.questions):
            material_start = len(story)
            if staged_network_materials:
                for material in exercise.materials:
                    if (
                        material.id in question.material_ids
                        and material.id not in staged_material_ids
                    ):
                        add_material(material)
                        staged_material_ids.add(material.id)
            graph_depth_correction = (
                correction
                and question.verification.get("kind") == "graph_tree_depth_contract"
            )
            question_start = len(story)
            if (
                not correction
                and question.id == "3e"
                and question.verification.get("kind") == "network_depth_contract"
            ):
                final_network_pair_start = question_start
            question_content(question.id, question.prompt)
            if (
                not correction
                and question.verification.get("kind") == "database_audit_contract"
            ):
                start = material_start if question.id == "2g" else question_start
                story[start:] = [KeepTogether(story[start:])]
            if (
                not correction
                and question.verification.get("kind") == "database_depth_contract"
            ):
                story[question_start:] = [KeepTogether(story[question_start:])]
            if (
                not correction
                and question.id == "3f"
                and question.verification.get("kind") == "network_depth_contract"
                and final_network_pair_start is not None
            ):
                story[final_network_pair_start:] = [
                    KeepTogether(story[final_network_pair_start:])
                ]
            if correction:
                story[-1].keepWithNext = True
                paragraph("Réponse attendue", credit)
                if (
                    question.id == "3b"
                    and question.verification.get("kind") == "network_depth_contract"
                ):
                    network_depth_trace_answer(question.answer)
                else:
                    content(question.answer)
                paragraph(f"Barème indicatif — question {question.id}", credit)
                marking_rows = [
                    [
                        Paragraph(escape(point_label(item.points)), body),
                        Paragraph(
                            escape(
                                printable_database_criterion(item.criterion)
                                if question.verification.get("kind")
                                == "database_depth_contract"
                                else item.criterion
                            ),
                            body,
                        ),
                    ]
                    for item in question.marking
                ]
                marking_table = Table(
                    marking_rows,
                    colWidths=[100, doc.width - 100]
                    if large_print
                    else [72, doc.width - 72],
                    hAlign="LEFT",
                )
                marking_table.setStyle(
                    TableStyle(
                        [
                            (
                                "GRID",
                                (0, 0),
                                (-1, -1),
                                0.35,
                                colors.HexColor("#B8B8B8"),
                            ),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                2
                                if graph_depth_correction
                                else (3 if correction else 4),
                            ),
                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                2
                                if graph_depth_correction
                                else (3 if correction else 4),
                            ),
                        ]
                    )
                )
                story.append(marking_table)
                if (
                    v18_paper
                    or question.verification.get("kind") == "graph_resilience_contract"
                    or question.verification.get("kind") == "network_reasoning_contract"
                    or question.id == "3f"
                    or (
                        question.id == "3d"
                        and question.verification.get("kind")
                        == "network_depth_contract"
                    )
                    or (
                        question.id in {"1b", "1e", "1f", "1h", "1j"}
                        and question.verification.get("kind")
                        == "graph_tree_depth_contract"
                    )
                ):
                    story[question_start:] = [KeepTogether(story[question_start:])]
                if (
                    exercise_index < len(exercises) - 1
                    or question_index < len(exercise.questions) - 1
                ):
                    story.append(Spacer(1, 2 if graph_depth_correction else 5))

    def cover_page(canvas, built_doc):
        draw_cover_page(
            canvas,
            built_doc,
            correction=correction,
            large_print=large_print,
            regular_font=regular,
            bold_font=bold,
            italic_font=italic,
        )

    doc.build(story, canvasmaker=NumberedCanvas, onFirstPage=cover_page)
