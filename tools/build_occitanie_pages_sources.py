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
                    "I am developing Keldin, a Mac application for preparing computing practice. My work covers the interface, the printed questions and the checks on their proposed answers. An answer can sound convincing and still be wrong, so checking it has become a substantial part of the project. Details of my studies and other commitments: to complete.",
                ),
                (
                    "Project title",
                    "Keldin: NSI practice and an Occitanie open-data activity",
                ),
                (
                    "Summary of your project",
                    "Keldin includes a French activity built from twelve public lycée records in Occitanie. Students use Python and SQL to investigate the data, including two records with the same name but different identifiers. The worksheet and its proposed answers work offline.\nThe app also asks a selected AI model to write NSI practice papers and corrections: three independent exercises, 18 technical points and a separate indicative 2-point language component. It checks their structure and supported answers before producing PDFs. No complete paper from the current model-generated route has yet passed qualification.",
                ),
            ),
        ),
        Page(
            "The project and its users",
            (
                (
                    "What is original about your project?",
                    "The regional activity uses an error that students can reproduce. Two CLEMENT MAROT records have different school IDs and boarding flags. A dictionary indexed by name keeps only one of them. The questions ask students to explain the loss and use a suitable identifier.\nFor generated papers, Keldin asks the model to solve an exercise without seeing its proposed answer, then reviews the questions and runs supported executable checks. Disagreements can stop publication. I retain the failed attempts as well as the results that pass those checks.",
                ),
                (
                    "Who could benefit from your project?",
                    "People preparing NSI practice can use the Mac app and share its PDFs with students. A student can read or print the documents without an AI account. Keldin does not collect pupil responses.\nThe regional worksheet connects familiar programming operations to data about local schools. It is intended for teaching and practice; its educational benefit has not been measured with learners, and no school partnership has been arranged.",
                ),
                (
                    "What stage of development has your project reached?",
                    "The regional activity produces a three-page worksheet and a three-page correction. The app has standard and enlarged print, visible progress and cancellation. Earlier fixed papers underwent internal curriculum and page review, but that work cannot establish the quality of a new AI draft.\nComplete French drafts from local models have contained mistakes. The immediate work is to evaluate stronger models and inspect their papers against the programme and official subjects. Difficulty and completion time have not been calibrated. French teacher review and learner timing evidence are unavailable; App Store publication is pending.",
                ),
            ),
        ),
        Page(
            "Previous support and planned work",
            (
                (
                    "Have you already presented this project, and has it been the subject of a request for support?",
                    "I presented an earlier British version to a computing teacher. The comments concerned difficulty, SQL and how precisely the marking criteria awarded credit. I used them when setting requirements for the software. They did not assess the French papers.\nOther presentations, support requested or received, and previous funding: applicant to complete and confirm before submission.",
                ),
                (
                    "Additional information to explain your project",
                    "The extract contains three public establishments from each of Nîmes, Toulouse, Montpellier and Cahors. It retains the published labels from the 2025-2026 dataset, updated on 12 May 2026. Licence Ouverte 2.0 (Etalab) permits attributed reuse. These records do not establish NSI provision or current boarding vacancies.\nOver the next twelve months, I would spend months 1 and 2 recording failures and extending the checks. In months 3 to 6, I would compare complete papers with official questions. Months 7 to 9 would focus on PDF accessibility and further activities using regional data. The final three months would be used to assess the results before extending the project. Any school study would require agreement in advance.\nThe 1,000-euro prize could help pay for testing on different Macs, accessibility work and regional activities. Budget allocation: applicant to complete before submission. Reference-document rights, educational calibration and distribution requirements remain unresolved. No regional endorsement or school deployment has been agreed.",
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
            "One name, two records",
            (
                (
                    "",
                    "Two records in Région Occitanie's lycée dataset are named CLEMENT MAROT. Their school IDs and boarding flags differ. Store them in a Python dictionary keyed by name and one record overwrites the other. Keldin's regional worksheet asks students to find the loss, explain it and choose an identifier that keeps both records.",
                ),
                (
                    "",
                    "The same extract mixes uppercase and title case for commune names. A lookup for MONTPELLIER misses records until the comparison handles case consistently. Accents still matter. Eight questions take these problems through dictionaries and SQL, including a join. The correction compares two SQLite results with separate Python selections.",
                ),
                (
                    "A local activity",
                    "The twelve records comprise three public establishments from each of Nîmes, Toulouse, Montpellier and Cahors. The fixed extract works offline. Its three-page worksheet and three-page correction can be printed or opened in an ordinary PDF reader, without an AI account.",
                ),
                (
                    "Source and limits",
                    "The 2025-2026 dataset was updated on 12 May 2026 and retrieved on 29 October. Each PDF credits the Region and dataset under Licence Ouverte 2.0 (Etalab). Contacts, pupil metrics and coordinates are omitted. This small selection cannot represent the region, guide admissions, establish NSI provision or identify boarding vacancies.",
                ),
            ),
        ),
        Page(
            "Making a practice paper",
            (
                (
                    "",
                    "A user chooses an AI provider and model, then standard or enlarged print. Keldin asks the model to write three independent French NSI exercises and their proposed answers, using French programme and paper references. Each exercise is worth 6 technical points; an indicative 2-point language component is separate.",
                ),
                (
                    "Checking the work",
                    "The model then solves each exercise without seeing its proposed answer and reviews the questions individually. Supported executable checks examine SQL, Python traces and shortest paths. A reported issue can stop publication. Agreement between model calls cannot prove correctness: both can make the same mistake.",
                ),
                (
                    "",
                    "The SwiftUI Mac interface passes the work to a Python backend, which reports progress. Other sections remain available, and the user can cancel. Local models run on the Mac. Hosted generation sends prompts after the user's consent and uses their API credits. Keldin does not collect pupil responses.",
                ),
                (
                    "Saving the result",
                    "The subject and correction are prepared in private storage and checked before publication. Failed or cancelled work is not recorded as a completed paper. Users export the PDFs; technical records stay private. The regional activity also publishes its pair together and refuses to replace existing output. Both documents should be read before they are shared.",
                ),
            ),
        ),
        Page(
            "Current state of the project",
            (
                (
                    "French papers",
                    "The current model-generated route, V36, has not yet produced a complete French paper that passes qualification. Local drafts have contained incorrect reasoning and code. Internal review compares the work with the programme, the announced 2027 structure and the 2026 Métropole subject, which has 36 questions over 16 pages. It examines reasoning, supplied information and credit, rather than treating page count as a difficulty measure.",
                ),
                (
                    "",
                    "Earlier fixed papers, V35, received internal curriculum and page review. That evidence is historical. New model output needs its own inspection. French teacher review and learner timing studies have not been conducted, so difficulty and completion time remain uncalibrated. No school partnership or regional endorsement has been obtained.",
                ),
                (
                    "Distribution",
                    "Developer-signed Mac builds have passed local checks and selected native workflows. Testing does not cover every interaction on every Mac or establish full HIG compliance. App Store release still requires a personal Distribution identity and the remaining release work. Official exam PDFs are not bundled; rights for individual reference documents remain unresolved.",
                ),
                (
                    "Sources",
                    "Regional data: data.laregion.fr/explore/dataset/lycees-occitanie/\nWritten definition: education.gouv.fr/bo/2026/Special4/MENE2622643N\nThe repository retains the 28 October fixed-paper review, 29 October regional activity review and later model diagnostics, including failed attempts and source versions.",
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
                    "",
                    "Keldin checks that a question's marking criteria add up to its stated mark, using exact decimal arithmetic. Three 6-point exercises give 18 technical points. A separate indicative language component adds 2. The target duration is 210 minutes; no learner study has measured the actual time needed.",
                ),
                (
                    "Answer checks",
                    "In the current route, V36, a solve attempt cannot see the proposed answer. A further review records findings for each question. SQL, Python traces and shortest paths have supported executable checks; other work may remain unchecked. A successful check covers its defined case, and can still share a mistaken interpretation of the printed question.",
                ),
                (
                    "Printed content",
                    "PDF checks look for missing or out-of-order content, wrong dimensions, absent footers and empty page bodies. Visual inspection covers code indentation, diagrams and continuation across pages. An unchanged page can inherit its earlier inspection through a pixel match. That match is recorded as reused evidence, not a second independent review.",
                ),
                (
                    "Regional worksheet",
                    "Tests compare its two SQLite queries with separate Python selections and run the printed Python solutions. All six worksheet and correction pages were reviewed. The extract contains twelve IDs and eight fields. Its rows-only SHA-256 is 8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0. This identifies the selected rows, not the full dataset; a source change needs fresh checks.",
                ),
            ),
        ),
        Page(
            "Evidence and remaining limits",
            (
                (
                    "Paper trials",
                    "The first historical Gemma 4 12B French campaign accepted 0 of 10 complete papers. No complete current V36 paper has yet passed qualification. Small successful tasks and short parallel-task timings cannot establish complete-paper quality or faster generation across subjects. Results retain the model, settings and source version, including failed attempts.",
                ),
                (
                    "Historical page review",
                    "V35 contained five fixed families with 34 or 36 questions and standard subjects of 7 to 9 pages. Its 341-page review included fresh inspection and matches to previously inspected pages. The official comparator has 36 questions over 16 pages. Repeated families and enlarged copies are not independent cases, and their inspection cannot validate newly generated papers.",
                ),
                (
                    "Educational evaluation",
                    "French teacher review and empirical calibration remain not run. There is no examiner approval or evidence of national difficulty equivalence, learning gains or time savings. A timing study would need observed attempts and a stated treatment of unfinished work and accommodations.",
                ),
                (
                    "Small samples",
                    "With zero blocking defects in n independent cases, a simple one-sided 95% upper bound is 1 - 0.05^(1/n). For n = 30, the bound is about 9.5%. This illustrative calculation is not Keldin's measured defect rate. It does not apply to a failed campaign or repeated versions of five fixed families.",
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
    # Unlabelled paragraphs let the narrative continue without another heading.
    if not label:
        return paragraph(text, indent=3800, after=240)
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
