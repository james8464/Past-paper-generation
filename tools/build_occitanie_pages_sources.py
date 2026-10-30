"""Write English RTF and original SVG inputs for native Pages editing/export."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output/occitanie-2026/pages-20261030-english"
DATE = "30 October 2026"


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
                    "I develop Keldin, a Mac application for preparing practice papers. The project brings together my interest in computing and a practical question: how can I check an AI-generated question before someone tries to learn from it? I have worked on the application, answer checks and printed papers. Further details of my studies and commitments: to complete.",
                ),
                (
                    "Project title",
                    "Keldin: NSI practice and an Occitanie open-data activity",
                ),
                (
                    "Summary of your project",
                    "Keldin asks a selected AI model to draft French NSI exercises and proposed corrections, then checks the work before producing two PDFs. Its V36 route targets three independent exercises, 18 technical points and a separate indicative 2-point language component. Complete model-generated papers have not yet passed the current qualification process.\nA working activity uses twelve public lycée records from four Occitanie communes. Students can investigate real data through Python and SQL. This activity works offline and is separate from exam-paper generation.",
                ),
            ),
        ),
        Page(
            "The project and its users",
            (
                (
                    "What is original about your project?",
                    "Keldin treats the proposed correction as something to test. It asks the model to solve an exercise without seeing its first answer, reviews each question and runs supported answer checks. A disagreement can stop publication. Agreement alone cannot prove that a question is right.\nThe Occitanie activity starts with an actual data problem: two CLEMENT MAROT records share a name but have different identifiers and boarding flags. Indexing them by name loses a record. Students can see the error, explain it and choose a better identifier.",
                ),
                (
                    "Who could benefit from your project?",
                    "The intended users are people preparing NSI practice and students using it. Keldin runs on a Mac; the resulting documents can be read on any PDF reader or printed. Students do not need an AI account, and the app collects no pupil responses.\nThe regional worksheet gives an NSI lesson a local subject: the Region's own school data. I have not yet tested its educational benefit with learners or arranged a school partnership.",
                ),
                (
                    "What stage of development has your project reached?",
                    "The app supports standard and enlarged print, progress updates and cancellation. Its regional activity produces a three-page worksheet and three-page correction. An earlier fixed catalogue, V35, underwent internal curriculum and page review. Those results do not validate the new model-generated papers.\nCurrent local models still make mistakes in complete French drafts. Improving model selection and checking the accepted papers are the immediate priorities. Difficulty and duration remain uncalibrated; French teacher review and learner timing evidence are unavailable. App Store publication is still pending.",
                ),
            ),
        ),
        Page(
            "Previous support and planned work",
            (
                (
                    "Have you already presented this project, and has it been the subject of a request for support?",
                    "I presented an earlier British version to a computing teacher. Comments on difficulty, SQL and the precision of marking criteria helped shape the software requirements. This was feedback on that version, not validation of the French papers.\nOther presentations, support requested or received, and previous funding: applicant to complete and confirm before submission.",
                ),
                (
                    "Additional information to explain your project",
                    "The regional activity uses three public establishments in each of Nîmes, Toulouse, Montpellier and Cahors. The 2025-2026 source was updated on 12 May 2026. Licence Ouverte 2.0 (Etalab) allows attributed reuse. The extract preserves the published labels; it cannot establish NSI provision or current boarding vacancies.\nDuring months 1 and 2, I would document failures and extend the checks. Months 3 to 6 would focus on complete papers and comparison with official questions. Months 7 to 9 would address PDF accessibility and further regional activities. I would use the final three months to assess what worked before extending the project. Any school study would need prior agreement.\nThe 1,000-euro prize could support testing on different Macs, accessibility work and regional data activities. The applicant must complete the budget allocation before submission. Reference-document rights, educational calibration and distribution requirements still need resolving. There is no regional endorsement or agreed school deployment.",
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
            "Learning from Occitanie data",
            (
                (
                    "Twelve records, four communes",
                    "Keldin's regional worksheet uses lycée data published by Région Occitanie. It takes three public establishments from each of Nîmes, Toulouse, Montpellier and Cahors. The 2025-2026 source was updated on 12 May 2026 and retrieved on 29 October. A fixed local extract lets the activity run without a network connection.",
                ),
                (
                    "When a name is not an identifier",
                    "Two records are named CLEMENT MAROT. Their school IDs and boarding flags differ. Put them in a dictionary keyed by name and one overwrites the other. The same extract mixes uppercase and title case for communes: a lookup for MONTPELLIER misses records until the comparison handles case consistently. Accents still matter.",
                ),
                (
                    "From the record to the query",
                    "Eight questions follow these problems through Python dictionaries and SQL, including a join. The correction checks two SQLite results against separate Python selections. Both documents have three pages. A recipient can use the unmarked activity with an ordinary PDF reader or a printed copy.",
                ),
                (
                    "What this example can show",
                    "The activity gives data-quality work a local context. Its small selection is not representative and cannot guide admissions, show NSI provision or identify boarding vacancies. Contacts, pupil metrics and coordinates are omitted. Each PDF credits the producer and dataset, with its date and Licence Ouverte 2.0 (Etalab). No school partnership or regional endorsement has been obtained.",
                ),
            ),
        ),
        Page(
            "From a model to a practice paper",
            (
                (
                    "Drafting",
                    "In V36, the selected model writes the French exercises and proposed corrections. The target is three independent exercises worth 6 technical points each, with a separate indicative 2-point language component. French programme and paper references inform the requests. The earlier five-family V35 catalogue is retained for historical checks; it is no longer the public authoring route.",
                ),
                (
                    "Checking the answer",
                    "Keldin asks the model to solve each exercise without seeing its proposed answer, then review each question. Supported executable checks examine SQL, Python traces and shortest paths. A reported issue can stop the paper. The same model can make the same mistake twice, so these steps leave a draft that still needs reading.",
                ),
                (
                    "Using the app",
                    "The user chooses a provider and model, then standard or enlarged print. Progress stays visible while other sections remain available, and generation can be cancelled. SwiftUI controls the Mac interface; a Python backend carries out generation and sends progress events. Keldin collects no pupil responses.",
                ),
                (
                    "Two documents to read",
                    "Keldin prepares the subject and correction privately and checks them before publication. Failed or cancelled work is not recorded as a completed paper. Technical records stay in private storage; users export the PDFs. The regional activity also publishes its pair together and refuses to replace existing output. Read both documents before sharing them.",
                ),
            ),
        ),
        Page(
            "What is ready, and what is not",
            (
                (
                    "Paper review",
                    "Internal review uses the programme, the announced 2027 written structure and the official 2026 Métropole subject. That subject has 36 questions over 16 pages. Review considers the steps a student must reason through, the information supplied and the proposed marks. Page count alone cannot establish comparable difficulty.",
                ),
                (
                    "Current result",
                    "No complete V36 model-generated French paper has yet passed qualification. Local drafts have contained incorrect reasoning and code; the app has refused them. Earlier V35 page review covered 341 pages, inspected or matched to inspected pages. It does not establish the quality of new model output. Teacher review and learner timing studies have not been conducted.",
                ),
                (
                    "Release work",
                    "Developer-signed Mac builds have passed local checks, including selected native workflows. Testing every interaction on every Mac and full HIG compliance have not been established. App Store release still needs a personal Distribution identity and the remaining release requirements. Official exam PDFs are not bundled; rights for individual reference documents remain unresolved.",
                ),
                (
                    "Source records",
                    "Regional dataset: data.laregion.fr/explore/dataset/lycees-occitanie/\nWritten definition: education.gouv.fr/bo/2026/Special4/MENE2622643N\nThe repository retains the 28 October V35 review, 29 October regional activity review and subsequent V36 model diagnostics. These records identify the source versions and retain failed attempts.",
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
            "How a draft is checked",
            (
                (
                    "Marks and structure",
                    "A question's credits must add up to its stated mark. Exact decimal arithmetic checks these totals against three 6-point exercises. A separate indicative language component adds 2 points to the 18 technical points. The paper targets 210 minutes, but no learner study has measured its actual completion time.",
                ),
                (
                    "Answers and disagreements",
                    "V36 separates drafting from a solve attempt that cannot see the proposed answer. A further review records issues question by question. Supported executable checks cover SQL, Python traces and shortest paths. Some answers remain unchecked. Even a successful check cannot rule out a shared misunderstanding of the printed question.",
                ),
                (
                    "The printed page",
                    "The PDF checks look for missing or out-of-order content, incorrect dimensions, missing footers and empty page bodies. Visual review examines code indentation, diagrams and how a question continues across pages. A pixel match can carry forward an earlier inspection of an unchanged page. It does not add another independent review.",
                ),
                (
                    "The regional activity",
                    "Its two SQLite queries are compared with independent Python selections, and tests run the printed Python solutions. All six worksheet and correction pages were reviewed. The extract fixes twelve IDs and eight fields; its rows-only SHA-256 is 8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0. The hash identifies these rows, not the full dataset. A changed source needs fresh checks.",
                ),
            ),
        ),
        Page(
            "Reading the results",
            (
                (
                    "Earlier fixed papers",
                    "V35 contained five fixed families with 34 or 36 questions. Their standard subjects had 7 to 9 pages; the official comparator has 16 pages and 36 questions. Repeating a family or enlarging its print does not create another independent case. Those results remain historical evidence about V35, not acceptance of the current V36 model-generated route.",
                ),
                (
                    "Models still need qualification",
                    "The first historical Gemma 4 12B French campaign accepted 0 of 10 complete papers. No complete current V36 French paper has yet passed qualification either. A small successful task cannot establish complete-paper quality. Each result needs its model, settings and source version, with failed attempts retained. Short parallel-task timings also cannot establish faster complete papers across subjects.",
                ),
                (
                    "What has not been measured",
                    "There is no French teacher panel or learner timing study. Teacher review and empirical calibration remain not run. The project has no examiner approval or evidence of national difficulty equivalence, learning gains or time savings. A timing study would need observed attempts and a stated treatment of unfinished work and accommodations.",
                ),
                (
                    "Why sample size matters",
                    "For n independent cases with zero blocking defects, a simple one-sided 95% upper bound is 1 - 0.05^(1/n). At n = 30 it is about 9.5%. This is an illustration of uncertainty, not a measured defect rate for Keldin. It cannot be applied to the failed campaign or repeated versions of the same five families.",
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
            ("Selected model", "Draft + blind solve"),
            ("Checks", "Review + exact credit"),
            ("PDF pair", "Subject + correction"),
            ("User review", "Read before sharing"),
        ),
    ),
    "paper-structure.svg": (
        "French V36",
        (
            ("3 exercises", "6 points each"),
            ("18 + 2 points", "Language separate"),
            ("Model-authored", "Read every draft"),
            ("Uncalibrated", "Difficulty + duration"),
        ),
    ),
    "validation-limits.svg": (
        "Evidence boundaries",
        (
            ("Scoped checks", "Credits + cases"),
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
    # Keep the illustration column; give each idea a heading and a paragraph.
    return paragraph(label, size=22, bold=True, indent=3800, after=70) + paragraph(
        text, indent=3800, after=240
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
