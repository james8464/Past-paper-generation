from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from Backend.Core.document_dsl.components import (
    AnswerSpace,
    BlankPage,
    ContinuationPage,
    Cover,
    Diagram,
    Graph,
    InstructionBlock,
    LevelTable,
    MarkBox,
    QuestionBlock,
    RuleSet,
    SchemeGrid,
    SourcePanel,
    Table,
)
from Backend.Core.document_dsl.model import LayoutBox, LayoutPlan, RenderEvidence


@dataclass
class ReportLabBackend:
    max_render_seconds: float = 30.0

    def render(self, plan: LayoutPlan, destination: Path) -> RenderEvidence:
        started = time.monotonic()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            pdf = Canvas(
                str(temporary),
                pagesize=(plan.profile.page_width.pt, plan.profile.page_height.pt),
                pageCompression=1,
                invariant=1,
            )
            pdf.setTitle(plan.metadata.title)
            pdf.setAuthor(plan.metadata.author)
            pdf.setSubject(plan.metadata.subject)
            pdf.setKeywords(", ".join(plan.metadata.keywords))
            for page in plan.pages:
                for box in page.boxes:
                    self._draw(pdf, plan, box)
                self._draw_furniture(pdf, plan, page.number)
                pdf.showPage()
                if time.monotonic() - started > self.max_render_seconds:
                    raise TimeoutError(
                        "document rendering exceeded its progress deadline"
                    )
            pdf.save()
            os.replace(temporary, destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        data = destination.read_bytes()
        with fitz.open(destination) as document:
            selectable = any(page.get_text().strip() for page in document)
            page_count = document.page_count
        return RenderEvidence(
            destination=str(destination),
            sha256=hashlib.sha256(data).hexdigest(),
            page_count=page_count,
            elapsed_seconds=time.monotonic() - started,
            selectable_text=selectable,
            atomic_publication=True,
            warnings=("PDF/UA structure tags require a post-processing backend",),
        )

    def _draw(self, pdf: Canvas, plan: LayoutPlan, box: LayoutBox) -> None:
        component = box.component
        profile = plan.profile
        body = profile.fonts.body
        bold = profile.fonts.bold
        x, y, width, height = box.x.pt, box.y.pt, box.width.pt, box.height.pt
        pdf.saveState()
        pdf.setFillColor(colors.black)
        pdf.setStrokeColor(colors.black)
        if isinstance(component, Cover):
            pdf.setFont(bold.name, profile.fonts.title.size.pt)
            pdf.drawString(x, y + height - 30, component.board_label)
            pdf.setFont(bold.name, 24)
            pdf.drawString(x, y + height - 75, component.title.upper())
            pdf.setFont(body.name, 14)
            pdf.drawString(x, y + height - 100, component.subtitle)
            pdf.drawRightString(x + width, y + height - 100, component.code)
        elif isinstance(component, InstructionBlock):
            pdf.setFont(bold.name, bold.size.pt)
            pdf.drawString(x, y + height - bold.leading.pt, component.heading)
            cursor = y + height - bold.leading.pt - body.leading.pt
            pdf.setFont(body.name, body.size.pt)
            for item in component.items:
                pdf.drawString(x + 8, cursor, f"• {item}")
                cursor -= body.leading.pt
        elif isinstance(component, QuestionBlock):
            pdf.setFont(bold.name, bold.size.pt)
            pdf.drawString(x, y + height - body.leading.pt, component.number)
            pdf.setFont(body.name, body.size.pt)
            self._wrapped_text(
                pdf,
                component.prompt,
                x + 42,
                y + height - body.leading.pt,
                width - 75,
                body,
            )
            pdf.drawRightString(x + width, y + 4, f"[{component.marks} marks]")
        elif isinstance(component, (AnswerSpace, RuleSet)):
            line_height = (component.line_height or profile.answer_line_height).pt
            pdf.setLineWidth(profile.rules.hairline.width.pt)
            for line in range(component.lines):
                rule_y = y + height - (line + 1) * line_height
                pdf.line(x, rule_y, x + width, rule_y)
        elif isinstance(component, MarkBox):
            pdf.rect(x, y, width, height, stroke=1, fill=0)
            pdf.setFont(body.name, body.size.pt)
            pdf.drawCentredString(
                x + width / 2, y + height / 2 - 3, str(component.marks)
            )
        elif isinstance(component, (Table, SchemeGrid)):
            self._table(
                pdf,
                (component.headers, *component.rows),
                x,
                y,
                width,
                height,
                body.name,
            )
        elif isinstance(component, LevelTable):
            self._table(
                pdf,
                (("Level", "Descriptor", "Marks"), *component.levels),
                x,
                y,
                width,
                height,
                body.name,
            )
        elif isinstance(component, Graph):
            self._graph(pdf, component, x, y, width, height, body.name)
        elif isinstance(component, Diagram):
            self._diagram(pdf, component, x, y, width, height, body.name)
        elif isinstance(component, SourcePanel):
            pdf.setLineWidth(profile.rules.standard.width.pt)
            pdf.rect(x, y, width, height, stroke=1, fill=0)
            pdf.setFont(bold.name, bold.size.pt)
            pdf.drawString(x + 8, y + height - 16, component.title)
            pdf.setFont(body.name, body.size.pt)
            self._wrapped_text(
                pdf, component.body, x + 8, y + height - 32, width - 16, body
            )
        elif isinstance(component, ContinuationPage):
            pdf.setFont(bold.name, bold.size.pt)
            pdf.drawCentredString(x + width / 2, y + height - 18, component.heading)
            spacing = max(12, (height - 36) / max(1, component.lines))
            for line in range(component.lines):
                pdf.line(
                    x,
                    y + height - 36 - line * spacing,
                    x + width,
                    y + height - 36 - line * spacing,
                )
        elif isinstance(component, BlankPage):
            pdf.setFont(bold.name, 11)
            pdf.drawCentredString(x + width / 2, y + height / 2, component.message)
        else:
            raise TypeError(
                f"unsupported document component: {type(component).__name__}"
            )
        pdf.restoreState()

    @staticmethod
    def _wrapped_text(
        pdf: Canvas, text: str, x: float, y: float, width: float, font
    ) -> None:  # type: ignore[no-untyped-def]
        words = text.split()
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if pdf.stringWidth(candidate, font.name, font.size.pt) <= width:
                line = candidate
            else:
                pdf.drawString(x, y, line)
                y -= font.leading.pt
                line = word
        if line:
            pdf.drawString(x, y, line)

    @staticmethod
    def _table(
        pdf: Canvas, rows, x: float, y: float, width: float, height: float, font: str
    ) -> None:  # type: ignore[no-untyped-def]
        columns = max(len(row) for row in rows)
        row_height = height / len(rows)
        column_width = width / columns
        pdf.setFont(font, 8)
        pdf.rect(x, y, width, height, stroke=1, fill=0)
        for row_index, row in enumerate(rows):
            row_y = y + height - (row_index + 1) * row_height
            if row_index:
                pdf.line(x, row_y + row_height, x + width, row_y + row_height)
            for column_index, value in enumerate(row):
                if column_index:
                    pdf.line(
                        x + column_index * column_width,
                        y,
                        x + column_index * column_width,
                        y + height,
                    )
                pdf.drawString(
                    x + column_index * column_width + 4,
                    row_y + row_height / 2 - 3,
                    str(value),
                )

    @staticmethod
    def _graph(
        pdf: Canvas,
        graph: Graph,
        x: float,
        y: float,
        width: float,
        height: float,
        font: str,
    ) -> None:
        left, bottom = x + 28, y + 22
        right, top = x + width - 8, y + height - 8
        pdf.line(left, bottom, right, bottom)
        pdf.line(left, bottom, left, top)
        pdf.setFont(font, 8)
        pdf.drawCentredString((left + right) / 2, y + 5, graph.x_label)
        pdf.drawString(x, top, graph.y_label)
        if len(graph.series) >= 2:
            xs = [point[0] for point in graph.series]
            ys = [point[1] for point in graph.series]
            x_span = max(xs) - min(xs) or 1
            y_span = max(ys) - min(ys) or 1
            path = pdf.beginPath()
            for index, (x_value, y_value) in enumerate(graph.series):
                px = left + (x_value - min(xs)) / x_span * (right - left)
                py = bottom + (y_value - min(ys)) / y_span * (top - bottom)
                (path.moveTo if index == 0 else path.lineTo)(px, py)
            pdf.drawPath(path, stroke=1, fill=0)

    @staticmethod
    def _diagram(
        pdf: Canvas,
        diagram: Diagram,
        x: float,
        y: float,
        width: float,
        height: float,
        font: str,
    ) -> None:
        if not diagram.nodes:
            return
        step = width / len(diagram.nodes)
        positions = []
        pdf.setFont(font, 8)
        for index, node in enumerate(diagram.nodes):
            cx = x + step * (index + 0.5)
            cy = y + height / 2
            pdf.rect(cx - 18, cy - 10, 36, 20, stroke=1, fill=0)
            pdf.drawCentredString(cx, cy - 3, node)
            positions.append((cx, cy))
        for source, target in diagram.edges:
            if 0 <= source < len(positions) and 0 <= target < len(positions):
                pdf.line(
                    positions[source][0] + 18,
                    positions[source][1],
                    positions[target][0] - 18,
                    positions[target][1],
                )

    @staticmethod
    def _draw_furniture(pdf: Canvas, plan: LayoutPlan, page_number: int) -> None:
        profile = plan.profile
        pdf.saveState()
        pdf.setFont(profile.fonts.small.name, profile.fonts.small.size.pt)
        pdf.drawCentredString(profile.page_width.pt / 2, 12, str(page_number))
        pdf.drawRightString(
            profile.page_width.pt - profile.safe_print_insets[1].pt,
            12,
            "UNOFFICIAL PRACTICE",
        )
        pdf.restoreState()
