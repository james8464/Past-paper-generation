"""Provisional French paper layout measured from the 2026 Métropole NSI paper."""

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

from Backend.Core.fonts import register_font
from Backend.Core.france.nsi import NSIExercise


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
                70, 43, "Paper Creator - entraînement non officiel - non relu"
            )
            self.drawRightString(A4[0] - 54, 43, f"Page : {self._pageNumber} / {total}")
            super().showPage()
        super().save()


def render_assessment(
    path: Path,
    exercises: list[NSIExercise],
    *,
    correction: bool,
    large_print: bool = False,
):
    regular = register_font("ExamSans")
    bold = register_font("ExamSans-Bold")
    mono = register_font("AQACourier", fallback="Courier")
    size = 16 if large_print else 12
    body = ParagraphStyle(
        "NSIBody", fontName=regular, fontSize=size, leading=size * 1.25, spaceAfter=10
    )
    heading = ParagraphStyle(
        "NSIHeading",
        parent=body,
        fontName=bold,
        spaceBefore=14,
        spaceAfter=16,
        keepWithNext=True,
    )
    cover = ParagraphStyle(
        "NSICover",
        parent=heading,
        alignment=1,
        fontSize=16 if not large_print else 20,
        leading=24,
    )
    code = ParagraphStyle(
        "NSICode", parent=body, fontName=mono, fontSize=size, leading=size * 1.2
    )
    credit = ParagraphStyle(
        "NSICredit",
        parent=body,
        fontName=bold,
        spaceBefore=4,
        spaceAfter=4,
        keepWithNext=True,
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=70,
        rightMargin=54,
        topMargin=60,
        bottomMargin=65,
        title="NSI - sujet d'entraînement non officiel",
        author="Paper Creator",
        pageCompression=1,
    )
    story = []

    def paragraph(text, style=body):
        story.append(Paragraph(escape(text).replace("\n", "<br/>"), style))

    def content(text):
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
                paragraph(part.strip())

    story.append(Spacer(1, 50))
    paragraph("BACCALAURÉAT GÉNÉRAL", cover)
    paragraph("ÉPREUVE D'ENSEIGNEMENT DE SPÉCIALITÉ", cover)
    paragraph("NUMÉRIQUE ET SCIENCES INFORMATIQUES", cover)
    paragraph(
        "Corrigé proposé et barème indicatif"
        if correction
        else "Sujet d'entraînement - non officiel",
        cover,
    )
    paragraph("Préparation à la session 2027 - partie écrite uniquement")
    paragraph("Durée : 3 heures 30. Calculatrice interdite.")
    paragraph(
        "Trois exercices indépendants : 18 points techniques au total. Maîtrise de la langue : 2 points. Total : 20 points."
    )
    paragraph("Traiter les trois exercices sur une copie séparée.")
    paragraph(
        "PROTOTYPE NON RELU PAR UN ENSEIGNANT. Mise en page provisoire inspirée de sujets antérieurs. Ce document n'est ni un sujet officiel ni un corrigé officiel."
    )
    if correction:
        story.append(PageBreak())
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
    for exercise in exercises:
        story.append(PageBreak())
        paragraph(f"Exercice {exercise.id} (6 points)", heading)
        paragraph(exercise.title, heading)
        content(exercise.context)
        for question in exercise.questions:
            content(f"{question.id}. {question.prompt}")
            if correction:
                story[-1].keepWithNext = True
                paragraph(
                    f"Exercice {exercise.id}, question {question.id} - {question.points.replace('.', ',')} point(s)",
                    credit,
                )
                content(question.answer)
                for item in question.marking:
                    paragraph(
                        f"{item.points.replace('.', ',')} point(s) : {item.criterion}"
                    )
                story.append(Spacer(1, 8))
    doc.build(story, canvasmaker=NumberedCanvas)
