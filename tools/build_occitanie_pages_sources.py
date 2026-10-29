"""Write English RTF and original SVG inputs for native Pages editing/export."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output/occitanie-2026/pages-20261029-english"
DATE = "29 October 2026"


@dataclass(frozen=True)
class Page:
    title: str
    sections: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Report:
    filename: str
    name: str
    pages: tuple[Page, ...]
    subtitle: str | None = None
    formal: bool = False


APPLICATION = Report(
    "Prix-Occitanie-2026-Application-English-James-Durup.rtf",
    "Application draft",
    (
        Page(
            "Prix Occitanie 2026 application",
            (
                (
                    "Identity",
                    "Name: James Durup\nYear group: to complete\nEmail: james.durup@student-cs.fr\nTelephone and postal address: to complete\nStudent status for 2026-2027 and eligibility: applicant to confirm.",
                ),
                (
                    "Briefly introduce yourself",
                    "I develop Keldin, a macOS application for preparing practice papers. My interests include software whose results can be checked and the use of computing in education. The project has involved school curricula, executable answer checks, PDF layout and local AI models. Further details of my studies, interests and commitments: to complete.",
                ),
                (
                    "Project title",
                    "Keldin: NSI practice and an Occitanie open-data activity",
                ),
                (
                    "Summary of your project",
                    "Keldin prepares subjects and proposed corrections as ordinary PDFs. Public French V35 constructs five finite paper families without calling an AI model. They contain 34 or 36 questions across three independent exercises, with 18 technical points and a separate indicative 2-point language component. Difficulty and duration remain uncalibrated.\nA separate, unmarked activity uses twelve public school records from four Occitanie communes. It connects identifiers, Python dictionaries and SQL to real data. It is not a sixth examination-paper family.",
                ),
            ),
        ),
        Page(
            "The project and its users",
            (
                (
                    "What is original about your project?",
                    "French questions are bound to source-owned answers and marking criteria. Executable cases check supported algorithms and SQL; page checks address printed content and layout. These controls do not prove educational equivalence to the baccalaureate.\nThe regional activity preserves two CLEMENT MAROT records with different identifiers and boarding flags. Source casing also differs between communes. These real properties support tasks about dictionary overwrite, string comparison and a join, with attribution attached.",
                ),
                (
                    "Who could benefit from your project?",
                    "The intended users prepare or use NSI practice. Recipients need an ordinary PDF reader or printed copy, not a Mac or an AI account. The macOS application prepares the documents and collects no pupil responses.\nThe Occitanie activity provides a concrete example of data quality and reuse. No school partnership, regional deployment or measured learner benefit is claimed.",
                ),
                (
                    "What stage of development has your project reached?",
                    "The prototype produces standard and enlarged French PDFs. Internal V35 review covered curriculum, logic, answers and 341 pages, either inspected or fully compared with inspected pages. Standard subjects have 7 to 9 pages, compared with 16 in the official 2026 comparator. Page count does not establish difficulty.\nThe offline regional activity produces a worksheet and correction from a verified 2025-2026 extract. French teacher review and learner timing evidence are unavailable. App Store publication is not secured.",
                ),
            ),
        ),
        Page(
            "Previous support and planned work",
            (
                (
                    "Have you already presented this project, and has it been the subject of a request for support?",
                    "An earlier British version was presented to a computing teacher. Comments on difficulty, SQL and marking precision informed software requirements. That feedback does not validate the French route.\nOther presentations, support requested or received, and previous funding: applicant to complete and confirm before submission.",
                ),
                (
                    "Additional information to explain your project",
                    "The Occitanie link uses data published by the Region. The extract selects three public establishments in each of Nîmes, Toulouse, Montpellier and Cahors. It preserves source labels from 2025-2026, updated on 12 May 2026. Licence Ouverte 2.0 (Etalab) permits attributed reuse. The selection is not representative and shows neither NSI provision nor boarding vacancies. No regional endorsement is implied.\nMonths 1 and 2 would document defects and extend test cases. Months 3 to 6 would address paper variety, internal comparison with official material and actual app use. Months 7 to 9 would focus on PDF accessibility and open-data activities. The final three months would assess results and limitations before choosing an extension. Any school study requires prior agreement; no partner is promised.\nThe 1,000-euro prize could support tests on different Macs, accessibility and regional data work. The applicant must complete the allocation and confirm expenditure. Reference-document rights, educational calibration and distribution requirements remain unresolved.",
                ),
            ),
        ),
    ),
    formal=True,
)

TECHNICAL = Report(
    "Keldin-NSI-Technical-and-User-Report.rtf",
    "Technical and user report",
    (
        Page(
            "An Occitanie activity",
            (
                (
                    "Regional source",
                    "A separate offline worksheet uses twelve public lycée records from Région Occitanie's 2025-2026 dataset. Three records come from each of Nîmes, Toulouse, Montpellier and Cahors. The source was updated on 12 May 2026 and retrieved on 29 October 2026. Generation uses a pinned extract and makes no network request.",
                ),
                (
                    "A real data problem",
                    "Two CLEMENT MAROT records have different school IDs and boarding flags. An index keyed by name overwrites one record. Source commune names also mix uppercase and title case. A lookup for MONTPELLIER fails until the comparison handles case consistently. Accents remain significant.",
                ),
                (
                    "Executable work",
                    "Eight questions cover identifiers, dictionaries, filtering, counting and SQL, including a join. Two SQLite results are checked against separate Python selections. The worksheet and correction each have three pages. This unmarked activity is separate from the five V35 examination-paper families.",
                ),
                (
                    "Reuse and scope",
                    "Both PDFs identify the source, producer, data date and Licence Ouverte 2.0 (Etalab). Contacts, pupil metrics and coordinates are omitted. The extract is not representative, an admissions tool or evidence of NSI provision. Boarding flags do not indicate vacancies. No regional endorsement or school partnership is claimed.",
                ),
            ),
        ),
        Page(
            "How the application works",
            (
                (
                    "French papers",
                    "Public V35 constructs five finite whole-paper families without an AI-provider call. Four contain 34 questions and the fifth 36. Each has three independent exercises worth 6 technical points, plus a separate indicative 2-point language component. Standard subjects have 7 to 9 pages. Difficulty and duration are uncalibrated.",
                ),
                (
                    "Source and checks",
                    "Versioned inputs bind questions, answers and marking criteria. Supported checks cover algorithms, graph behaviour and SQL. The fifth family includes object graphs, backtracking allocation and an explicitly atomic blocking channel. These checks establish specific properties, not educational suitability for every learner.",
                ),
                (
                    "User workflow",
                    "The user chooses standard or enlarged print, creates a draft and reads both PDFs before sharing them. Recipients need only a PDF reader or paper. The app collects no pupil responses. A SwiftUI interface coordinates a Python backend and receives typed progress events.",
                ),
                (
                    "Publication",
                    "The regional activity renders and validates both documents privately before publishing its folder. A failed second render publishes neither PDF; existing output refuses replacement. UK subject routes can use Ollama or Apple MLX. Their model quality is a separate question from the model-free French route.",
                ),
            ),
        ),
        Page(
            "Acceptance and remaining limits",
            (
                (
                    "Internal comparison",
                    "V35 review used the programme, the announced 2027 written structure and the official 2026 Métropole subject: 36 questions over 16 pages. All 341 standard and enlarged pages were inspected or fully raster-matched to inspected pages. Sparse correction tails and shorter subjects remain documented.",
                ),
                (
                    "Unavailable evidence",
                    "Teacher review and empirical calibration remain not run. No examiner approval, measured learning gain or learner completion time is claimed. Selected native workflows have been checked, but complete interaction coverage on every Mac and full HIG compliance are not established.",
                ),
                (
                    "Distribution",
                    "A developer-signed macOS build has undergone local checks. App Store approval is not secured; the personal Distribution identity and release requirements remain unresolved. No official exam PDF is bundled. Per-document reference rights remain open. Dataset reuse permission does not clear other source documents.",
                ),
                (
                    "Sources",
                    "Regional dataset: data.laregion.fr/explore/dataset/lycees-occitanie/\nWritten definition: education.gouv.fr/bo/2026/Special4/MENE2622643N\nThe repository retains the V35 expanded-practice review dated 28 October 2026 and Occitanie case-study review dated 29 October 2026, including artifact hashes and page evidence.",
                ),
            ),
        ),
    ),
    subtitle="French NSI\nTechnical and user report\nPrix Occitanie 2026",
)

RELIABILITY = Report(
    "Keldin-NSI-Reliability-and-Validation-Note.rtf",
    "Reliability and validation",
    (
        Page(
            "What the checks establish",
            (
                (
                    "Exact constraints",
                    "Exact decimal arithmetic checks question credits against exercise totals. Three exercises contribute 18 technical points; separate indicative language credit adds 2. Estimated times sum to 210 minutes. These checks establish internal consistency, not observed completion time or an official marking grid.",
                ),
                (
                    "Answer cases",
                    "Source-owned inputs support reproducible algorithm, graph and SQL checks. The regional activity runs two queries in SQLite and compares their rows with independent Python selections. Tests execute its printed Python solutions. A shared misunderstanding of the task can still affect both implementations.",
                ),
                (
                    "Printed evidence",
                    "Checks cover ordered content, dimensions, footers and nonempty page bodies. Visual inspection considers code, tables, diagrams and answer flow. A full-page raster match can carry forward an earlier inspection; it is not another independent opinion. All six regional activity pages were reviewed.",
                ),
                (
                    "Data identity",
                    "The regional extract pins twelve IDs and eight fields. Its rows-only SHA-256 is 8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0. This is not a whole-dataset hash. Data and retrieval dates are separate. Changed source or artifacts require fresh acceptance evidence.",
                ),
            ),
        ),
        Page(
            "Measurement limits",
            (
                (
                    "Finite cases",
                    "Five V35 families are five source-owned cases. Enlarged copies and repeated runs do not increase an independent sample. Standard subjects have 7 to 9 pages and 34 or 36 questions. The official comparator has 16 pages and 36 questions. Matching its length would not prove matched reasoning demand.",
                ),
                (
                    "Model results",
                    "The first historical Gemma 4 12B French campaign accepted 0 of 10 complete papers. Model-free V35 does not repair that result. Provider evidence must retain model, settings, source and failed attempts. Short parallel-task timing cannot establish faster complete papers or equal quality across subjects.",
                ),
                (
                    "Unknowns",
                    "No French teacher panel or learner timing study is available. Teacher review and empirical calibration remain not run. Examiner approval, national difficulty equivalence and measured time savings are not claimed. Timing claims require observed attempts with stated handling of abandonment and accommodations.",
                ),
                (
                    "Sample interpretation",
                    "For n independent cases with zero blocking defects, a simple one-sided 95% upper bound is 1 - 0.05^(1/n). At n = 30 it is about 9.5%. This illustrates sample limits; it is not a result from the failed campaign or repeated versions of five families.",
                ),
            ),
        ),
    ),
    subtitle="French NSI\nReliability and validation\nPrix Occitanie 2026",
)
REPORTS = (APPLICATION, TECHNICAL, RELIABILITY)
DIAGRAMS = {
    "occitanie-data-workflow.svg": (
        "Regional extract",
        (
            ("12 records", "4 communes"),
            ("School ID", "Keep both names"),
            ("Python / SQL", "Compare results"),
            ("Two PDFs", "Unmarked activity"),
        ),
    ),
    "application-workflow.svg": (
        "Paper workflow",
        (
            ("Source contracts", "Questions + answers"),
            ("Checks", "Logic + exact credit"),
            ("PDF pair", "Subject + correction"),
            ("User review", "Read before sharing"),
        ),
    ),
    "paper-structure.svg": (
        "French V35",
        (
            ("3 exercises", "6 points each"),
            ("18 + 2 points", "Language separate"),
            ("5 finite families", "34 or 36 questions"),
            ("Uncalibrated", "Difficulty + duration"),
        ),
    ),
    "validation-limits.svg": (
        "Evidence boundaries",
        (
            ("Exact checks", "Credits + answers"),
            ("Page review", "Content + layout"),
            ("Not measured", "Learner duration"),
            ("Not obtained", "Teacher approval"),
        ),
    ),
}


def rtf_text(text: str) -> str:
    """Escape literal text using signed UTF-16 RTF units."""
    result = []
    for character in text:
        if character in "\\{}":
            result.append("\\" + character)
        elif character == "\n":
            result.append(r"\line ")
        elif 32 <= ord(character) < 127:
            result.append(character)
        else:
            encoded = character.encode("utf-16-le")
            for offset in range(0, len(encoded), 2):
                unit = int.from_bytes(encoded[offset : offset + 2], "little")
                result.append(f"\\u{unit if unit < 32768 else unit - 65536}?")
    return "".join(result)


def paragraph(
    text: str,
    *,
    size: int = 20,
    bold: bool = False,
    indent: int = 0,
    before: int = 0,
    after: int = 200,
    font: int = 0,
) -> str:
    leading = max(280, size * 12)
    return (
        rf"\pard\f{font}\fs{size}\li{indent}\ri0\fi0\sb{before}\sa{after}\sl{leading}\slmult0 "
        + (r"\b " if bold else r"\b0 ")
        + rtf_text(text)
        + r"\par"
        + "\n"
    )


def body_section(label: str, text: str, *, formal: bool) -> str:
    if formal:
        return paragraph(label, size=25, bold=True, after=120) + paragraph(
            text, after=230
        )
    # Reserve the left 190 pt for original illustrations inserted in Pages.
    return (
        r"\pard\f0\fs20\li3800\ri0\fi-180\tx3800\sb0\sa240\sl280\slmult0 "
        + r"\u8226?\tab\b "
        + rtf_text(label)
        + r".\b0\~ "
        + rtf_text(text)
        + r"\par"
        + "\n"
    )


def render(report: Report) -> str:
    blocks = [
        r"{\rtf1\ansi\ansicpg1252\uc1\deff0{\fonttbl{\f0\fnil SF Pro Text;}{\f1\fnil SF Pro Display;}}"
        r"\paperw11906\paperh16838\margl1000\margr1000\margt1000\margb1000\widowctrl\lang2057"
        + "\n",
        r"{\footer\pard\f0\fs16 "
        + rtf_text(f"Keldin | {report.name} | {DATE}")
        + r"\tab {\field{\*\fldinst PAGE}{\fldrslt 1}}\par}"
        + "\n",
    ]
    if report.subtitle:
        blocks.extend(
            [
                # Pages discards space-before on the first paragraph. A retained
                # NBSP paragraph with exact 170 pt leading reserves the cover gap.
                r"\pard\f0\fs2\li0\fi0\sb0\sa0\sl-3400\slmult0 \u160?\par" + "\n",
                paragraph("Keldin", size=56, bold=True, indent=3500, after=300, font=1),
                paragraph(
                    report.subtitle, size=32, bold=True, indent=3500, after=400, font=1
                ),
                paragraph(DATE, size=22, indent=3500),
                r"\page" + "\n",
            ]
        )
    for index, page in enumerate(report.pages):
        if index:
            blocks.append(r"\page" + "\n")
        blocks.append(paragraph(page.title, size=40, bold=True, after=380))
        if report.formal and index == 0:
            blocks.append(
                paragraph(
                    "English working draft. This is not a French filing translation; confirm the accepted submission language before sending.",
                    after=220,
                )
            )
        blocks.extend(
            body_section(label, text, formal=report.formal)
            for label, text in page.sections
        )
    return "".join(blocks) + "}"


def diagram_svg(title: str, nodes: tuple[tuple[str, str], ...]) -> str:
    """Original workflow illustration; no external imagery or copied artwork."""
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="150pt" height="360pt" viewBox="0 0 150 360">',
        '<rect width="150" height="360" fill="white"/>',
        f'<text x="6" y="21" font-family="SF Pro Text, sans-serif" font-size="11" font-weight="600">{escape(title)}</text>',
    ]
    for index, (label, detail) in enumerate(nodes):
        y = 48 + index * 76
        parts.extend(
            [
                f'<rect x="6" y="{y}" width="138" height="54" rx="7" fill="#F5F5F5" stroke="#D2D2D2"/>',
                f'<circle cx="17" cy="{y + 17}" r="3" fill="#FF9500"/>',
                f'<text x="26" y="{y + 21}" font-family="SF Pro Text, sans-serif" font-size="10" font-weight="600">{escape(label)}</text>',
                f'<text x="16" y="{y + 40}" font-family="SF Pro Text, sans-serif" font-size="8.5" fill="#484848">{escape(detail)}</text>',
            ]
        )
        if index < len(nodes) - 1:
            parts.append(
                f'<path d="M75 {y + 56} v15 m-3 -3 l3 3 3 -3" fill="none" stroke="#777" stroke-width="1"/>'
            )
    return "".join(parts) + "</svg>"


def build(output: Path = DEFAULT_OUTPUT) -> tuple[Path, ...]:
    output.mkdir(parents=True, exist_ok=True)
    paths = tuple(output / report.filename for report in REPORTS)
    illustrations = tuple(output / name for name in DIAGRAMS)
    if any(path.exists() for path in (*paths, *illustrations)):
        raise FileExistsError(
            "Pages inputs already exist; choose a fresh output folder."
        )
    for report, path in zip(REPORTS, paths, strict=True):
        path.write_text(render(report), encoding="ascii")
    for name, (title, nodes) in DIAGRAMS.items():
        (output / name).write_text(diagram_svg(title, nodes), encoding="utf-8")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    for path in build(args.output):
        print(path)


if __name__ == "__main__":
    main()
