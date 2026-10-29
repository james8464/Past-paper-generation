"""An offline NSI activity using a pinned, openly licensed regional extract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import pymupdf
from reportlab.lib import colors
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
    Table,
    TableStyle,
)

from Backend.Core.events import emit, emit_progress
from Backend.Core.fonts import register_font, register_fonts
from Backend.Core.paths import REPO_ROOT, absolute_user_path
from Backend.Core.render_transaction import render_pdf_atomically

RESOURCE_PATH = REPO_ROOT / "Resources/france/occitanie-case-study-v1.json"
OUTPUT_FOLDER = "occitanie-nsi-etude-de-cas"
WORKSHEET_FILENAME = "occitanie-nsi-activite.pdf"
CORRECTION_FILENAME = "occitanie-nsi-correction.pdf"
PINNED_ROWS_SHA256 = "8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0"
PINNED_IDS = (
    "0300021K",
    "0300026R",
    "0300057Z",
    "0310036W",
    "0310038Y",
    "0310047H",
    "0340038G",
    "0340039H",
    "0340040J",
    "0460007H",
    "0460051F",
    "0460493L",
)
FIELDS = {
    "codeetab",
    "denomination_lycee",
    "lib_type_nom_lycee",
    "commune",
    "code_departement",
    "departement",
    "secteur",
    "internat",
}
SOURCE_URL = "https://data.laregion.fr/explore/dataset/lycees-occitanie/"
NOTICE = "Activité indépendante, sans note d'examen. Ce document n'est ni un sujet officiel ni un service d'orientation."
ATTRIBUTION = (
    "Source : Région Occitanie, Lycées d'Occitanie année scolaire 2025-2026. "
    "Données mises à jour le 12 mai 2026 ; extrait consulté le 29 octobre 2026. "
    "Licence Ouverte 2.0 (Etalab). Aucune caution du producteur n'est impliquée."
)
SQL_LOT = """SELECT nom, commune FROM LYCEE
WHERE code_departement = '46' AND internat = 'oui'
ORDER BY codeetab;"""
SQL_JOIN = """SELECT L.nom, D.nom FROM LYCEE AS L
JOIN DEPARTEMENT AS D ON L.code_departement = D.code
WHERE L.commune = 'Montpellier' AND L.internat = 'oui'
ORDER BY L.codeetab;"""
BAD_INDEX = """def indexer(lycees):
    resultat = {}
    for lycee in lycees:
        resultat[lycee["denomination_lycee"]] = lycee
    return resultat"""
FILTER = """def filtrer(lycees, ville):
    resultat = []
    for lycee in lycees:
        if lycee["commune"] == ville:
            if lycee["internat"] == "oui":
                resultat.append(lycee["codeetab"])
    return resultat"""
CORRECTED_FILTER = """def filtrer(lycees, ville):
    resultat = []
    for lycee in lycees:
        if lycee["commune"].casefold() == ville.casefold():
            if lycee["internat"] == "oui":
                resultat.append(lycee["codeetab"])
    return resultat"""
COUNT_CODE = """def compter_internats(lycees):
    comptes = {}
    for lycee in lycees:
        if lycee["internat"] == "oui":
            ville = lycee["commune"]
            comptes[ville] = comptes.get(ville, 0) + 1
    return comptes"""


def rows_sha256(rows: list[dict[str, str]]) -> str:
    return hashlib.sha256(
        json.dumps(
            rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def load_case_data(path: Path = RESOURCE_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError("L'extrait Occitanie dépasse la taille autorisée.")
    data = json.loads(raw)
    expected = {
        "schema_version": 1,
        "dataset_id": "lycees-occitanie",
        "title": "Lycées d'Occitanie année scolaire 2025-2026",
        "publisher": "Région Occitanie",
        "source_url": SOURCE_URL,
        "license_id": "etalab-2.0",
        "license_name": "Licence Ouverte v2.0 (Etalab)",
        "license_url": "https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf",
        "source_last_updated": "2026-05-12T12:46:56+00:00",
        "retrieved_on": "2026-10-29",
        "source_attributions": [
            "DRAAF",
            "MENJS",
            "INSEE IGN NaturalEarth DGCL - BANATIC MEFR MAA",
        ],
    }
    if not isinstance(data, dict) or any(
        data.get(key) != value for key, value in expected.items()
    ):
        raise ValueError(
            "La provenance de l'extrait Occitanie n'est pas celle de la version vérifiée."
        )
    rows, selection = data.get("records"), data.get("selection")
    if not isinstance(rows, list) or len(rows) != 12 or not isinstance(selection, dict):
        raise ValueError(
            "L'extrait Occitanie doit contenir les douze lignes vérifiées."
        )
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != FIELDS
            or not all(
                isinstance(value, str) and 0 < len(value) <= 180
                for value in row.values()
            )
        ):
            raise ValueError("Une ligne de l'extrait Occitanie est invalide.")
        if (
            not re.fullmatch(r"\d{7}[A-Z]", row["codeetab"])
            or row["secteur"] != "Public"
            or row["internat"] not in {"oui", "non"}
        ):
            raise ValueError(
                "Un identifiant ou un indicateur de l'extrait est invalide."
            )
    if tuple(row["codeetab"] for row in rows) != PINNED_IDS or selection.get(
        "record_ids"
    ) != list(PINNED_IDS):
        raise ValueError("La sélection des établissements a changé.")
    if (
        set(selection.get("fields", [])) != FIELDS
        or selection.get("rows_sha256") != PINNED_ROWS_SHA256
        or rows_sha256(rows) != PINNED_ROWS_SHA256
    ):
        raise ValueError(
            "L'extrait Occitanie ne correspond pas à son empreinte vérifiée."
        )
    return data


def solve_case_study(data: dict[str, Any]) -> dict[str, Any]:
    rows = data["records"]
    departments = sorted(
        {(row["code_departement"], row["departement"]) for row in rows}
    )
    expected_lot = [
        (row["denomination_lycee"], row["commune"])
        for row in rows
        if row["code_departement"] == "46" and row["internat"] == "oui"
    ]
    expected_join = [
        (row["denomination_lycee"], row["departement"])
        for row in rows
        if row["commune"] == "Montpellier" and row["internat"] == "oui"
    ]
    with sqlite3.connect(":memory:") as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(
            "CREATE TABLE DEPARTEMENT(code TEXT PRIMARY KEY, nom TEXT NOT NULL); CREATE TABLE LYCEE(codeetab TEXT PRIMARY KEY, nom TEXT NOT NULL, commune TEXT NOT NULL, code_departement TEXT NOT NULL REFERENCES DEPARTEMENT(code), internat TEXT NOT NULL);"
        )
        connection.executemany("INSERT INTO DEPARTEMENT VALUES (?, ?)", departments)
        connection.executemany(
            "INSERT INTO LYCEE VALUES (?, ?, ?, ?, ?)",
            [
                (
                    row["codeetab"],
                    row["denomination_lycee"],
                    row["commune"],
                    row["code_departement"],
                    row["internat"],
                )
                for row in rows
            ],
        )
        sql_lot = connection.execute(SQL_LOT).fetchall()
        sql_join = connection.execute(SQL_JOIN).fetchall()
    if sql_lot != expected_lot or sql_join != expected_join:
        raise ValueError("Les résultats SQL et Python de l'activité diffèrent.")
    return {
        "indexed_count": len({row["codeetab"]: row for row in rows}),
        "bad_index_count": len({row["denomination_lycee"]: row for row in rows}),
        "uppercase_montpellier": [
            row["codeetab"]
            for row in rows
            if row["commune"] == "MONTPELLIER" and row["internat"] == "oui"
        ],
        "normalised_montpellier": [
            row["codeetab"]
            for row in rows
            if row["commune"].casefold() == "MONTPELLIER".casefold()
            and row["internat"] == "oui"
        ],
        "boarding_by_commune": dict(
            Counter(row["commune"] for row in rows if row["internat"] == "oui")
        ),
        "sql_lot": sql_lot,
        "sql_join": sql_join,
        "departments": departments,
    }


class _ActivityCanvas(Canvas):
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
            self.setFont("ExamSans", 8)
            self.drawString(
                50, 29, "Keldin | Activité indépendante | Extrait 2025-2026"
            )
            self.drawRightString(A4[0] - 50, 29, f"Page {self._pageNumber} / {total}")
            super().showPage()
        super().save()


def _render(
    path: Path, data: dict[str, Any], answers: dict[str, Any], *, correction: bool
) -> None:
    faces = register_fonts("ExamSans", "ExamSans-Bold", "ExamSans-Italic")
    regular, bold = faces["ExamSans"], faces["ExamSans-Bold"]
    mono = register_font("AQACourier", fallback="Courier")
    body = ParagraphStyle(
        "OccitanieBody", fontName=regular, fontSize=11, leading=14, spaceAfter=7
    )
    title = ParagraphStyle(
        "OccitanieTitle",
        parent=body,
        fontName=bold,
        fontSize=18,
        leading=22,
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "OccitanieHeading",
        parent=body,
        fontName=bold,
        fontSize=13,
        leading=17,
        spaceBefore=9,
        spaceAfter=8,
        keepWithNext=True,
    )
    small = ParagraphStyle(
        "OccitanieSource", parent=body, fontSize=9, leading=12, spaceAfter=6
    )
    code_style = ParagraphStyle(
        "OccitanieCode", fontName=mono, fontSize=9, leading=12, spaceAfter=9
    )
    cells = ParagraphStyle(
        "OccitanieCell", parent=body, fontSize=9, leading=12, spaceAfter=0
    )
    story = []

    def prose(text: str, style=body):
        story.append(Paragraph(escape(text).replace("\n", "<br/>"), style))

    def code(text: str):
        if any(stringWidth(line, mono, 9) > A4[0] - 100 for line in text.splitlines()):
            raise ValueError("Une ligne de code dépasse la largeur de l'activité.")
        story.append(Preformatted(text, code_style))

    def table(headers, rows, widths):
        values = [
            [Paragraph(escape(str(value)), cells) for value in row]
            for row in [headers, *rows]
        ]
        result = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
        result.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEEEEE")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([result, Spacer(1, 9)])

    def question(number, text, space=0):
        prose(f"{number}. {text}", heading)
        if space:
            story.append(Spacer(1, space))

    prose("NSI : étude de cas Occitanie", title)
    prose(
        "Correction proposée"
        if correction
        else "Identifiants, dictionnaires et requêtes SQL",
        heading,
    )
    prose(NOTICE)
    prose(
        "Cette activité utilise douze lignes publiques choisies dans quatre communes. Les libellés, les accents et la casse de la source sont conservés. Ce n'est pas un échantillon représentatif de la région. « Internat » indique une présence sur le site, pas des places disponibles."
    )
    prose(ATTRIBUTION, small)
    prose(SOURCE_URL, small)
    if not correction:
        table(
            ["Code", "Nom", "Commune", "Dépt.", "Internat"],
            [
                [
                    row["codeetab"],
                    row["denomination_lycee"],
                    row["commune"],
                    row["code_departement"],
                    row["internat"],
                ]
                for row in data["records"]
            ],
            [69, 176, 104, 47, 97],
        )
        question(
            1,
            "Pourquoi le nom seul ne peut-il pas être la clé primaire de cette table ? Citer les deux lignes qui le montrent.",
            34,
        )
        question(
            2,
            "Pourquoi ces douze lignes ne permettent-elles pas d'estimer le nombre de lycées avec internat dans toute l'Occitanie ?",
            30,
        )
    else:
        question(1, "Choisir un identifiant stable")
        prose(
            "CLEMENT MAROT figure sous les codes 0460007H et 0460051F. Les valeurs d'internat diffèrent. Le nom n'est donc pas unique. codeetab distingue les douze lignes et convient comme clé primaire dans cet extrait."
        )
        question(2, "Respecter le périmètre de l'extrait")
        prose(
            "La sélection retient trois établissements dans chacune de quatre communes, sans tirage représentatif. Un résultat calculé ici porte seulement sur ces douze lignes. La source concerne 2025-2026 : elle ne décrit pas nécessairement la situation actuelle."
        )
        prose("Départements utilisés dans la relation DEPARTEMENT", heading)
        table(
            ["Code (texte)", "Nom issu de la source"],
            answers["departments"],
            [110, 300],
        )
    story.append(PageBreak())
    prose("Traitements Python", title)
    prose(
        "Chaque élément de lycees est un dictionnaire dont les clés sont les noms de champs montrés dans le code. Les lignes sont ordonnées par codeetab."
    )
    code(BAD_INDEX)
    question(
        3,
        "Combien d'entrées ce dictionnaire contient-il ? Quelle ligne est écrasée ? Comment corriger le choix de la clé ?",
    )
    if correction:
        prose(
            f'Le dictionnaire contient {answers["bad_index_count"]} entrées. La ligne 0460051F écrase la ligne 0460007H sous la clé CLEMENT MAROT. Remplacer la clé par lycee["codeetab"] conserve les {answers["indexed_count"]} lignes.'
        )
    else:
        story.append(Spacer(1, 45))
    if not correction:
        code(FILTER)
    question(
        4,
        "Que renvoie filtrer(lycees, 'MONTPELLIER') avec le code initial ? Modifier la comparaison pour que 'MONTPELLIER' et 'Montpellier' donnent le même résultat, sans changer les données. La méthode casefold() permet une comparaison sans distinction de casse.",
    )
    if correction:
        prose(
            f"Le code initial renvoie {answers['uppercase_montpellier']}, car la source contient Montpellier. Après correction, le résultat est {answers['normalised_montpellier']}."
        )
        code(CORRECTED_FILTER)
        prose(
            "casefold() ne supprime pas les accents. Le programme ne promet pas d'assimiler Nimes à Nîmes.",
            small,
        )
    else:
        story.append(Spacer(1, 50))
    question(
        5,
        "Écrire une fonction qui compte les lignes avec internat par commune et renvoie un dictionnaire. Conserver la casse de chaque commune telle qu'elle apparaît dans la source.",
    )
    if correction:
        code(COUNT_CODE)
        prose(str(answers["boarding_by_commune"]))
    else:
        story.append(Spacer(1, 70))
    story.append(PageBreak())
    prose("Exploiter les relations SQL", title)
    prose(
        "La relation LYCEE reprend codeetab, denomination_lycee renommé nom, commune, code_departement et internat. DEPARTEMENT contient une ligne par code et nom de département présent dans l'extrait. Les champs sont tous de type texte."
    )
    code(
        "DEPARTEMENT(code, nom)\nLYCEE(codeetab, nom, commune, code_departement, internat)"
    )
    prose(
        "Clés primaires : DEPARTEMENT.code et LYCEE.codeetab. Clé étrangère : LYCEE.code_departement référence DEPARTEMENT.code.",
        small,
    )
    question(
        6,
        "Écrire une requête donnant le nom et la commune des établissements du Lot (code 46) avec internat. Trier par codeetab.",
    )
    if correction:
        code(SQL_LOT)
        table(["nom", "commune"], answers["sql_lot"], [230, 180])
    else:
        story.append(Spacer(1, 75))
    question(
        7,
        "À l'aide d'une jointure, donner le nom du lycée et le nom de son département pour les lignes de Montpellier avec internat. Trier par codeetab.",
    )
    if correction:
        code(SQL_JOIN)
        table(["nom du lycée", "nom du département"], answers["sql_join"], [230, 180])
        prose(
            "Ces deux résultats SQL ont été comparés à une sélection Python effectuée sur les mêmes lignes.",
            small,
        )
    else:
        story.append(Spacer(1, 90))
    question(
        8,
        "Quelles mentions faut-il conserver lors de la réutilisation de cet extrait ? Pourquoi ne faut-il pas présenter l'activité comme approuvée par la Région ?",
    )
    if correction:
        prose(
            "Conserver la source et le producteur, la date de mise à jour des données et la référence à la Licence Ouverte 2.0. La date de consultation ne remplace pas la date des données. La licence autorise la réutilisation mais ne confère aucune approbation publique à cette activité indépendante."
        )
    else:
        story.append(Spacer(1, 65))
    prose("Crédits de la source : " + ", ".join(data["source_attributions"]), small)
    prose("Licence : " + data["license_url"], small)
    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=46,
        bottomMargin=52,
        title="NSI - Étude de cas Occitanie"
        + (" - Correction" if correction else " - Activité"),
        author="Keldin",
        subject=NOTICE,
    )
    document.build(story, canvasmaker=_ActivityCanvas)


def validate_case_pdf(path: Path, *, correction: bool) -> None:
    with pymupdf.open(path) as document:
        if not document.page_count:
            raise ValueError("L'activité PDF ne contient aucune page.")
        text = "\n".join(page.get_text() for page in document)
        compact = "".join(text.split())
        for expected in (
            "NSI : étude de cas Occitanie",
            NOTICE,
            SOURCE_URL,
            "12 mai 2026",
            "2025-2026",
            "Licence Ouverte 2.0",
            "1.",
            "8.",
        ):
            if "".join(expected.split()) not in compact:
                raise ValueError(
                    "Une mention ou une question manque dans l'activité PDF."
                )
        if not correction and any(code not in text for code in PINNED_IDS):
            raise ValueError("Le tableau de l'activité PDF est incomplet.")
        questions = [
            re.search(rf"^{number}\. ", text, re.MULTILINE) for number in range(1, 9)
        ]
        if any(question is None for question in questions) or [
            question.start() for question in questions
        ] != sorted(question.start() for question in questions):
            raise ValueError(
                "Les questions de l'activité sont incomplètes ou désordonnées."
            )
        printed_code = (
            (BAD_INDEX, CORRECTED_FILTER, COUNT_CODE, SQL_LOT, SQL_JOIN)
            if correction
            else (BAD_INDEX, FILTER)
        )
        if any("".join(code.split()) not in compact for code in printed_code):
            raise ValueError("Un traitement Python ou SQL est incomplet dans le PDF.")
        for index, page in enumerate(document, start=1):
            if abs(page.rect.width - A4[0]) > 1 or abs(page.rect.height - A4[1]) > 1:
                raise ValueError("Une page de l'activité n'est pas au format A4.")
            if f"Page {index} / {document.page_count}" not in page.get_text():
                raise ValueError("La pagination de l'activité est incomplète.")
            spans = [
                span
                for block in page.get_text("dict")["blocks"]
                if "lines" in block
                for line in block["lines"]
                for span in line["spans"]
                if span["text"].strip()
            ]
            body = [span for span in spans if span["bbox"][1] < page.rect.height - 52]
            if not body or any(
                span["bbox"][0] < 45
                or span["bbox"][2] > page.rect.width - 45
                or span["bbox"][1] < 35
                or span["bbox"][3] > page.rect.height - 45
                for span in body
            ):
                raise ValueError(
                    "Une page de l'activité est vide ou dépasse ses marges."
                )


def generate_case_study(output: Path) -> dict[str, Path]:
    data = load_case_data()
    answers = solve_case_study(data)
    output = absolute_user_path(output)
    target = output / OUTPUT_FOLDER
    if target.exists() or target.is_symlink():
        raise FileExistsError(
            "Le dossier de cette activité existe déjà. Choisir un autre dossier de sortie pour conserver les documents précédents."
        )
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".occitanie-case-study-", dir=output))
    names = {"question_paper": WORKSHEET_FILENAME, "mark_scheme": CORRECTION_FILENAME}
    try:
        for role, filename in names.items():
            correction = role == "mark_scheme"
            path = staging / filename
            render_pdf_atomically(
                path,
                lambda destination, correction=correction: _render(
                    destination, data, answers, correction=correction
                ),
                role="correction Occitanie" if correction else "activité Occitanie",
                language="fr-FR",
            )
            validate_case_pdf(path, correction=correction)
        if target.exists() or target.is_symlink():
            raise FileExistsError(
                "Le dossier de cette activité vient d'être créé par une autre opération."
            )
        os.rename(staging, target)
        return {role: target / filename for role, filename in names.items()}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def handle_generate_case_study(args: argparse.Namespace) -> int:
    def cancel(_number, _frame):
        raise InterruptedError("Création de l'activité annulée.")

    previous = signal.signal(signal.SIGTERM, cancel)
    try:
        emit_progress(
            "Préparation de l'extrait public d'Occitanie",
            stage="occitanie_case_study",
            progress=0.1,
        )
        paths = generate_case_study(Path(args.output))
        for role, path in paths.items():
            emit("file", role=role, path=str(path))
        emit(
            "done",
            message="Activité Occitanie créée. Document indépendant, sans note d'examen.",
        )
        return 0
    except InterruptedError:
        emit_progress("Création de l'activité annulée", stage="cancel", progress=0.0)
        return 130
    except Exception as error:
        emit("error", message=str(error), code="occitanie_case_study_failed")
        return 1
    finally:
        signal.signal(signal.SIGTERM, previous)
