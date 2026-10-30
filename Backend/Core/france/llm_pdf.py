"""Compare the complete generic V36 print stream and scoped vector figures."""

import re
from decimal import Decimal
from pathlib import Path

import pymupdf

from Backend.Core.france.code_fences import printed_text
from Backend.Core.france.code_layout import code_blocks
from Backend.Core.france.graph_layout import graph_layout
from Backend.Core.france.graph_pdf import validate_graph
from Backend.Core.france.llm_pipeline import CHECKABLE, PRINT_POLICY
from Backend.Core.france.nsi import (
    NSIExercise,
    NSITableMaterial,
    NSIWeightedGraphMaterial,
)
from Backend.Core.france.print_policy import (
    V34_FOOTER,
    V36_PRINT_POLICIES,
    V36_PRINT_POLICY,
    V36_READABLE_PRINT_POLICIES,
)
from Backend.Core.france.sql_sources import sql_caption
from Backend.Core.france.whole_case_pdf import (
    _compact,
    _expected_preface,
    _heading,
    _prose,
)


def _expected_exercise(
    exercise: NSIExercise, correction: bool, *, print_policy=PRINT_POLICY
) -> str:
    prose = printed_text if print_policy == V36_PRINT_POLICY else _prose
    title = exercise.title.strip().rstrip(".")
    scope = (
        f"{title}."
        if title.lower().startswith("cet exercice")
        else f"Thème de l'exercice : « {title} »."
    )
    parts = [_heading(exercise), scope, prose(exercise.context)]
    # Generic exercises print every material before the first question. Unlike
    # the historical whole-case layout, first-use IDs do not stage these figures.
    for material in exercise.materials:
        if isinstance(material, NSIWeightedGraphMaterial):
            parts.extend(
                [
                    material.title,
                    *[str(weight) for _, _, weight in material.edges],
                    *material.nodes,
                ]
            )
        elif isinstance(material, NSITableMaterial):
            label = material.title
            if (
                exercise.id == "2"
                and material.id not in {"case_states", "tree_nodes", "tree_states"}
                and not material.id.startswith("recon_")
            ):
                label += f" — {material.id}"
            parts.extend([label, sql_caption(material), *material.columns])
            for row in material.rows:
                parts.extend(row)
        else:
            raise ValueError("Document V36 non pris en charge")
    for question in exercise.questions:
        if question.verification.get("kind") not in CHECKABLE | {"human"}:
            raise ValueError("Ce contrôle exige le rendu générique V36")
        parts.extend([f"{question.id}.", prose(question.prompt)])
        if correction:
            parts.extend(
                [
                    "Réponse attendue",
                    prose(question.answer),
                    f"Barème indicatif — question {question.id}",
                ]
            )
            for credit in question.marking:
                suffix = "point" if Decimal(credit.points) <= 1 else "points"
                parts.extend(
                    [f"{credit.points.replace('.', ',')} {suffix}", credit.criterion]
                )
    return _compact("\n".join(parts))


class _FigurePage:
    def __init__(self, page, drawings):
        self.page, self.drawings = page, drawings

    def get_drawings(self):
        return self.drawings

    def get_text(self, mode):
        return self.page.get_text(mode)

    def get_texttrace(self):
        return self.page.get_texttrace()


def _check_graphs(
    pages, exercises, starts, *, large_print=False, print_policy=PRINT_POLICY
) -> None:
    for index, exercise in enumerate(exercises):
        graphs = [
            material
            for material in exercise.materials
            if isinstance(material, NSIWeightedGraphMaterial)
        ]
        geometries = [
            graph_layout(graph, large_print)
            if print_policy in V36_READABLE_PRINT_POLICIES
            else None
            for graph in graphs
        ]
        diameters = {
            2 * geometry.radius if geometry is not None else 32
            for geometry in geometries
        }
        scoped_pages = pages[
            starts[index] : starts[index + 1] if index + 1 < len(starts) else len(pages)
        ]
        circles = []
        for page in scoped_pages:
            drawings = page.get_drawings()
            for drawing in drawings:
                rect = drawing["rect"]
                if (
                    len(drawing["items"]) == 4
                    and all(item[0] == "c" for item in drawing["items"])
                    and any(
                        abs(rect.width - diameter) < 0.4
                        and abs(rect.height - diameter) < 0.4
                        for diameter in diameters
                    )
                ):
                    circles.append((page, drawing))
        if len(circles) != sum(len(graph.nodes) for graph in graphs):
            raise ValueError("Nombre de sommets imprimés incompatible avec les figures")
        offset = 0
        for graph, geometry in zip(graphs, geometries, strict=True):
            group = circles[offset : offset + len(graph.nodes)]
            offset += len(graph.nodes)
            page = group[0][0]
            if any(item[0].number != page.number for item in group):
                raise ValueError("Une figure graphe est séparée entre deux pages")
            bounds = pymupdf.Rect(group[0][1]["rect"])
            for _, circle in group[1:]:
                bounds |= circle["rect"]
            bounds += (-0.5, -0.5, 0.5, 0.5)
            # The source renderer draws each figure separately. Restricting the
            # vector stream, not node names, permits conventional labels to recur.
            figure_drawings = [
                drawing
                for drawing in page.get_drawings()
                if bounds.contains(drawing["rect"])
            ]
            validate_graph(
                [_FigurePage(page, figure_drawings)], graph, geometry=geometry
            )


def _check_code_lines(
    pages, exercises, *, correction: bool, print_policy=PRINT_POLICY
) -> None:
    expected = []
    for exercise in exercises:
        texts = [exercise.context]
        for question in exercise.questions:
            texts.append(question.prompt)
            if correction:
                texts.append(question.answer)
        for text in texts:
            blocks = (
                code_blocks(text)
                if print_policy == V36_PRINT_POLICY
                else re.split(r"```(?:python|sql)?[ \t]*(?:\r?\n)?", text)[1::2]
            )
            for code in blocks:
                expected.extend(
                    line.expandtabs(8).rstrip()
                    for line in code.strip("\n").splitlines()
                    if line.strip()
                )
    actual = []
    for page in pages:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = line["spans"]
                if any(
                    span["flags"] & 8
                    or "courier" in span["font"].casefold()
                    or "mono" in span["font"].casefold()
                    for span in spans
                ):
                    text = "".join(span["text"] for span in spans).rstrip()
                    if text.strip():
                        actual.append(text)
    if actual != expected:
        raise ValueError("Le code imprimé ou son indentation diffère de la source")


def validate_llm_pdf(
    path: Path,
    exercises: list[NSIExercise],
    *,
    correction: bool,
    large_print: bool = False,
    print_policy: str = PRINT_POLICY,
) -> None:
    from Backend.Core.france.runtime import validate_pdf

    if type(large_print) is not bool or print_policy not in V36_PRINT_POLICIES:
        raise ValueError("Politique ou mode de rendu V36 invalide")
    if [exercise.id for exercise in exercises] != ["1", "2", "3"]:
        raise ValueError("Trois exercices ordonnés requis")
    validate_pdf(path)
    with pymupdf.open(path) as pdf:
        pages, lines, starts = list(pdf), [], []
        headings = [_compact(_heading(exercise)) for exercise in exercises]
        for number, page in enumerate(pages, 1):
            if (
                abs(page.rect.width - 595.276) > 0.5
                or abs(page.rect.height - 841.89) > 0.5
            ):
                raise ValueError("Page V36 hors format A4")
            if not page.get_text(clip=pymupdf.Rect(0, 0, page.rect.width, 760)).strip():
                raise ValueError("Page V36 sans contenu hors pied de page")
            page_lines = [line.strip() for line in page.get_text().splitlines()]
            if page_lines.count(V34_FOOTER) != 1:
                raise ValueError("Pied de page V36 absent ou dupliqué")
            counters = [
                _compact(line)
                for line in page_lines
                if re.fullmatch(r"Page\s*:\s*\d+\s*/\s*\d+", line)
            ]
            if counters != [f"Page:{number}/{len(pages)}"]:
                raise ValueError("Pagination V36 invalide")
            body_lines = [
                line
                for line in page_lines
                if line
                and line != V34_FOOTER
                and not re.fullmatch(r"Page\s*:\s*\d+\s*/\s*\d+", line)
            ]
            page_text = _compact("\n".join(body_lines))
            for heading in headings:
                if heading in page_text:
                    starts.append((headings.index(heading), number - 1))
            lines.extend(body_lines)
        text = _compact("\n".join(lines))
        if any(text.count(heading) != 1 for heading in headings):
            raise ValueError("Exercice absent ou dupliqué dans le PDF")
        positions = [text.index(heading) for heading in headings]
        if positions != sorted(positions) or text[: positions[0]] != _expected_preface(
            correction, print_policy=print_policy
        ):
            raise ValueError("Couverture, rôle ou ordre des exercices invalide")
        for index, exercise in enumerate(exercises):
            end = positions[index + 1] if index + 1 < len(positions) else len(text)
            if text[positions[index] : end] != _expected_exercise(
                exercise, correction, print_policy=print_policy
            ):
                raise ValueError(
                    f"Contenu imprimé différent de l'exercice {exercise.id}"
                )
        if [index for index, _ in starts] != [0, 1, 2]:
            raise ValueError("Début des exercices ambigu")
        _check_graphs(
            pages,
            exercises,
            [page for _, page in starts],
            large_print=large_print,
            print_policy=print_policy,
        )
        _check_code_lines(
            pages, exercises, correction=correction, print_policy=print_policy
        )
