"""Write editable RTF inputs for Pages; native Pages owns final pagination/export."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output/occitanie-2026/pages-20261029"
DATE = "29 October 2026"


@dataclass(frozen=True)
class Page:
    title: str
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Report:
    filename: str
    name: str
    pages: tuple[Page, ...]
    cover: tuple[str, str] | None = None
    french: bool = False


APPLICATION = Report(
    "Prix-Occitanie-2026-Candidature-James-Durup.rtf",
    "Candidature",
    (
        Page(
            "Candidature au Prix Occitanie 2026",
            (
                (
                    "Identité",
                    "Nom : Durup\nPrénom : James\nPromo : à compléter\nEmail : james.durup@student-cs.fr\nTéléphone : à compléter\nAdresse : à compléter\nStatut étudiant 2026-2027 et éligibilité : à confirmer par le candidat.",
                ),
                (
                    "Présentez-vous brièvement",
                    "Je développe Keldin, une application macOS de préparation de sujets d'entraînement. Je m'intéresse aux logiciels dont on peut vérifier les résultats et à l'usage de l'informatique pour apprendre. Le projet m'a conduit à travailler sur les programmes scolaires, les réponses calculables, la mise en page des PDF et l'exécution de modèles locaux. Parcours, engagements et centres d'intérêt personnels complémentaires : à compléter.",
                ),
                (
                    "Titre du projet",
                    "Keldin : entraînement en NSI et étude de données ouvertes d'Occitanie",
                ),
                (
                    "Description synthétique de votre projet",
                    "Keldin prépare des PDF de sujets et de corrigés proposés. Le parcours français V35 construit cinq familles finies de sujets de Terminale NSI sans appeler de modèle d'IA. Elles comportent trois exercices indépendants, 18 points techniques et 2 points indicatifs de langue. Les sujets comptent 34 ou 36 questions. La difficulté et la durée restent non étalonnées.\nUne activité distincte utilise douze enregistrements publics de lycées, sélectionnés dans quatre communes d'Occitanie. Elle relie identifiants, dictionnaires Python et requêtes SQL à des données réelles. Cette activité est sans note d'examen et ne constitue pas une nouvelle famille de sujets.",
                ),
            ),
        ),
        Page(
            "Le projet et ses usages",
            (
                (
                    "Quelle est l'originalité de votre projet ?",
                    "Le parcours français associe les questions à des réponses et à des critères de crédit définis dans le logiciel. Des cas exécutables vérifient notamment les algorithmes et les requêtes SQL. Les contrôles des PDF portent sur le contenu et la mise en page ; ils ne prouvent pas une équivalence pédagogique au baccalauréat.\nL'activité Occitanie conserve deux noms CLEMENT MAROT avec des identifiants différents, ainsi que les différences de casse entre communes. Ces propriétés réelles permettent d'étudier une clé qui écrase une ligne, une comparaison de chaînes trop stricte et une jointure. La provenance et la licence accompagnent les documents.",
                ),
                (
                    "A qui pourra bénéficier le projet que vous proposez ?",
                    "Le projet s'adresse aux personnes qui préparent ou utilisent des exercices de NSI. Les destinataires reçoivent des PDF ordinaires, consultables sur un ordinateur, sur l'ENT ou sur papier. Ils n'ont besoin ni d'un Mac ni d'un compte d'IA pour les lire. L'application macOS sert à préparer les documents. Elle ne recueille aucune copie d'élève.\nL'activité régionale peut servir de support à un travail sur la qualité des données et leur réutilisation. Aucun établissement partenaire, déploiement scolaire ou bénéfice mesuré pour les élèves n'est revendiqué.",
                ),
                (
                    "A quel stade de développement en est votre projet ?",
                    "Le prototype produit des sujets et corrigés français, en impression standard ou agrandie. Les cinq familles V35 ont fait l'objet de contrôles internes de programme, de logique, de réponses et de pages. Les 341 pages standard et agrandies ont été inspectées ou comparées intégralement à des pages déjà inspectées. Les sujets standard ont 7 à 9 pages, contre 16 pour l'annale officielle 2026 comparée ; ce nombre ne mesure pas la difficulté.\nL'activité régionale hors ligne produit deux PDF à partir d'un extrait vérifié de 2025-2026. Aucune validation d'enseignant ni mesure de temps auprès d'élèves n'est disponible. La publication sur l'App Store n'est pas acquise.",
                ),
            ),
        ),
        Page(
            "Présentation et suite du travail",
            (
                (
                    "Avez-vous déjà eu l’opportunité de présenter ce projet ? et ce projet a-t-il déjà fait l’objet d’une demande d’aide ?",
                    "Une première version britannique a été présentée à une enseignante d'informatique. Ses remarques sur la difficulté, le SQL et la précision des barèmes ont alimenté les exigences du logiciel. Ce retour ne constitue pas une validation du parcours français.\nPrésentation complémentaire, aide demandée ou reçue et financement antérieur : à compléter et à confirmer par le candidat avant envoi. L'éligibilité au règlement dépend notamment de cette déclaration.",
                ),
                (
                    "Eléments complémentaires que vous souhaitez apporter pour préciser votre projet",
                    "Le lien avec l'Occitanie repose sur un usage concret de données publiées par la Région. L'extrait porte sur trois établissements publics dans chacune de quatre communes : Nîmes, Toulouse, Montpellier et Cahors. Il conserve les libellés de la source, datée de 2025-2026 et mise à jour le 12 mai 2026. La Licence Ouverte 2.0 (Etalab) autorise sa réutilisation avec attribution. La sélection n'est pas représentative de la région et n'indique ni offre de NSI ni places d'internat disponibles. Aucune approbation de la Région n'est impliquée.\nPendant les deux premiers mois, je prévois de documenter les défauts et d'étendre les cas de test. Des mois 3 à 6, le travail portera sur la variété des sujets et leur comparaison interne aux annales, puis sur l'utilisation réelle de l'application. Des mois 7 à 9, je poursuivrai l'accessibilité des PDF et les activités de données ouvertes. Les trois derniers mois serviront à établir un bilan des résultats et des limites avant de choisir une extension. Tout essai en établissement nécessitera un accord préalable ; aucun partenariat n'est promis.\nLe prix de 1 000 euros pourrait contribuer aux essais sur plusieurs configurations de Mac, à l'accessibilité et au travail sur les données régionales. La répartition exacte et toute dépense restent à compléter et à confirmer par le candidat. Le moteur et les PDF existent déjà ; la difficulté pédagogique, les droits de chaque document de référence et les conditions de distribution restent des limites à traiter.",
                ),
            ),
        ),
    ),
    french=True,
)

TECHNICAL = Report(
    "Keldin-NSI-Technical-and-User-Report.rtf",
    "Technical and user report",
    (
        Page(
            "The French workflow",
            (
                (
                    "Use",
                    "Keldin prepares non-official practice papers and proposed corrections. The user selects a print profile, creates a draft and reads the PDFs before deciding whether to share them. Recipients can use ordinary PDF readers or paper. The app does not collect pupil responses or mark their work.",
                ),
                (
                    "Catalogue",
                    "Public French V35 uses five finite whole-paper families without an AI-provider call. Four have 34 questions; the fifth has 36. Standard subjects occupy 7 to 9 pages. Each paper has three independent exercises worth 6 technical points each, plus a separate indicative 2-point language component. The announced written duration is 3 hours 30 minutes; the software's time allocations are estimates, not measured learner timings.",
                ),
                (
                    "Question logic",
                    "Versioned source data binds the question, answer and marking criteria. Tasks include graph and tree reasoning, SQL, routing and process behaviour. The fifth family adds object-graph construction and traversal, allocation through backtracking, and a blocking channel with an explicit atomic operation. Executable cases check supported answers. Such checks can find a wrong result but cannot establish the educational suitability of every question.",
                ),
                (
                    "Documents",
                    "The user receives a subject and a proposed correction in standard or enlarged print. Printing, export and document navigation have undergone native checks for selected workflows. The retained evidence does not establish complete interaction coverage on every Mac. Sparse correction tails and a shorter subject than the official comparator remain recorded limitations.",
                ),
            ),
        ),
        Page(
            "An Occitanie case study",
            (
                (
                    "Real extract",
                    "A separate offline activity uses twelve public lycée records from Région Occitanie's 2025-2026 dataset, three from each of Nîmes, Toulouse, Montpellier and Cahors. The source was updated on 12 May 2026 and retrieved on 29 October 2026. The selected records and fields have a pinned hash. Generation makes no network request.",
                ),
                (
                    "Data reasoning",
                    "Two CLEMENT MAROT records have different school IDs and boarding flags. Indexing by name overwrites one record; indexing by school ID keeps all twelve. The source also mixes uppercase commune names with Montpellier and Nîmes. A case-sensitive lookup for MONTPELLIER fails, while a corrected casefold comparison returns the two selected Montpellier records with boarding. The activity explains that casefold does not remove accents.",
                ),
                (
                    "Python and SQL",
                    "Eight questions connect these observations to primary keys, dictionary operations, filtering, counts and a relational join. Two SQLite query results are checked against separate Python selections. Both documents identify the source, producer, data date and Licence Ouverte 2.0 (Etalab). The activity exports one worksheet and one correction. It has no exam marks and is not a sixth V35 paper family.",
                ),
                (
                    "Boundaries",
                    "The extract is not a representative regional sample, an admissions tool or evidence that a school offers NSI. A boarding flag does not indicate vacancies. Contacts, pupil metrics and coordinates are omitted. No school partnership or regional endorsement is claimed. Reuse permission for this dataset does not clear the rights of other reference documents.",
                ),
            ),
        ),
        Page(
            "Implementation and acceptance",
            (
                (
                    "Architecture",
                    "A SwiftUI macOS interface coordinates a Python backend. Typed events report progress and completion; the app retains run identity and history. Separate French source contracts preserve historical packages. UK subject routes can use local AI providers, including Ollama and Apple MLX. These are distinct workflows: a successful French app-owned run does not qualify an AI model.",
                ),
                (
                    "Safety",
                    "Supported paths validate structured responses and checked answers before publication. Output preparation uses private working data; the user-facing export is the usable document pair. The Occitanie activity renders and validates both PDFs in a sibling staging folder before publishing the folder. Existing activity output refuses replacement. A failed second render publishes neither PDF.",
                ),
                (
                    "Review",
                    "Internal V35 comparison used the official 2026 Métropole subject, which has 36 questions over 16 pages, alongside the programme and announced 2027 structure. All 341 standard and enlarged pages were inspected or fully raster-matched to inspected pages. The review concerns source logic, printed content and layout. Difficulty and duration remain uncalibrated. Teacher review and empirical calibration remain not run.",
                ),
                (
                    "Distribution",
                    "A developer-signed macOS build has undergone local checks. This does not establish App Store approval, universal hardware support or full HIG compliance. The personal Distribution identity and remaining release requirements must be resolved before submission. No official exam PDF is bundled. Per-document reference rights remain open. The applicant must confirm eligibility, contact details and prior funding before the competition application is sent.",
                ),
                (
                    "Sources",
                    "Région Occitanie: data.laregion.fr/explore/dataset/lycees-occitanie/\nNSI written definition: education.gouv.fr/bo/2026/Special4/MENE2622643N\nRetained source reviews: docs/quality/french-nsi-v35-expanded-practice-review-2026-10-28.md and occitanie-case-study-review-2026-10-29.md in the project repository.",
                ),
            ),
        ),
    ),
    cover=("Keldin", "French NSI\nTechnical and user report\nPrix Occitanie 2026"),
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
                    "The three French exercises allocate 6 technical points each. Exact decimal arithmetic checks that question credits sum to the exercise totals and that technical credit is 18. Separate indicative language credit adds 2 points. Estimated question times sum to 210 minutes. These checks establish internal consistency, not an observed completion time or an official marking grid.",
                ),
                (
                    "Answer cases",
                    "Source-owned inputs support reproducible checks of graph behaviour, algorithms and SQL. The Occitanie activity runs its two queries in SQLite and compares their rows with independent Python selections from the same pinned extract. Tests also execute its printed Python solutions. Agreement detects some implementation mistakes; a shared misunderstanding of the task can still affect both implementations.",
                ),
                (
                    "Printed evidence",
                    "Validation checks ordered content, page dimensions, footers and nonempty page bodies. Visual inspection checks whether code, diagrams, tables and answer flow are readable. A full-page raster match can carry forward a previous inspection when the page is unchanged. It is not a new independent review. The separate Occitanie activity has three worksheet pages and three correction pages, all reviewed.",
                ),
                (
                    "Source identity",
                    "The data extract pins twelve explicit IDs and eight fields from the regional source. Its rows-only SHA-256 is 8a6a75c869d444fbd637af4976702dc7f2c436e08db5af0faa656df8ccd866f0. This is not the hash of the complete regional dataset. Source date and retrieval date are recorded separately. A changed source or generated artifact requires new acceptance evidence.",
                ),
            ),
        ),
        Page(
            "Limits and decisions",
            (
                (
                    "Finite evidence",
                    "Five V35 families are five source-owned cases. Enlarged copies, repeated generation and repeated inspections do not increase an independent sample. Four families contain 34 questions and one contains 36; standard subjects have 7 to 9 pages. The official 2026 comparator has 36 questions over 16 pages. Matching a page count would not prove matched reasoning demand.",
                ),
                (
                    "Model evidence",
                    "The historical first Gemma 4 12B French campaign accepted 0 of 10 complete papers. Later app-owned V35 output is a separate route and does not repair that model result. Provider benchmarks must retain the model, implementation, settings and failed attempts. A short parallel-task speed measurement cannot establish faster complete-paper generation or equal question quality for every model and subject.",
                ),
                (
                    "Unknowns",
                    "No French teacher panel or learner timing study is available. Teacher review and empirical calibration remain not run. No examiner approval, national difficulty equivalence, measured learning gain or time saving is claimed. A claim about completion time would require observed attempts and a stated treatment of abandoned work and accommodations.",
                ),
                (
                    "Interpretation",
                    "If independent trials had zero blocking defects in n cases, a simple one-sided 95% upper bound would be 1 - 0.05^(1/n). For n = 30 it is about 9.5%, not proof of a defect rate below 1%. This is an illustration of sample limits, not a result from the failed historical campaign or a calculation applicable to repeated versions of the five families.",
                ),
                (
                    "Next evidence",
                    "Further work should publish each defect, its corrected source and fresh artifact checks, then compare new tasks with official content and structure. User testing should record actual navigation failures and readable output on the tested hardware. Any school study requires its own agreement. The current documents support internal engineering acceptance within the stated scope; they do not supply missing external evidence.",
                ),
            ),
        ),
    ),
    cover=("Keldin", "French NSI\nReliability and validation\nPrix Occitanie 2026"),
)
REPORTS = (APPLICATION, TECHNICAL, RELIABILITY)


def rtf_text(text: str) -> str:
    """Escape text as signed UTF-16 units, including RTF's fallback characters."""
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
    text: str, *, size: int = 21, bold: bool = False, after: int = 180
) -> str:
    leading = max(280, size * 12)
    return (
        rf"\pard\f0\fs{size}\sl{leading}\slmult0\sa{after} "
        + (r"\b " if bold else r"\b0 ")
        + rtf_text(text)
        + r"\par"
        + "\n"
    )


def row(label: str, text: str, *, formal: bool) -> str:
    # Pages needs preferred cell widths as well as RTF's legacy cell edges.
    left_size = 25 if formal else 30
    borders = (
        r"\clvertalt\clbrdrt\brdrnil\clbrdrl\brdrnil\clbrdrb\brdrnil\clbrdrr\brdrnil"
    )
    return (
        r"\trowd\trgaph120\trleft0\trkeep\trrh0\trftsWidth3\trwWidth9600"
        + r"\clftsWidth3\clwWidth2700"
        + borders
        + r"\cellx2700"
        + r"\clftsWidth3\clwWidth6900"
        + borders
        + r"\cellx9600"
        + "\n"
        + rf"\pard\intbl\f0\fs{left_size}\b\sl310\slmult0\sa160 "
        + rtf_text(label)
        + r"\cell"
        + "\n"
        + r"\pard\intbl\f0\fs21\b0\sl280\slmult0\sa180 "
        + rtf_text(text)
        + r"\cell\row"
        + "\n"
        + r"\pard\fs10\sa80\par"
        + "\n"
    )


def render(report: Report) -> str:
    header = (
        r"{\rtf1\ansi\ansicpg1252\uc1\deff0"
        r"{\fonttbl{\f0\fnil SF Pro Text;}{\f1\fnil SF Pro Display;}}"
        r"\paperw11906\paperh16838\margl1134\margr1134\margt1000\margb1000"
        r"\widowctrl\ftnbj\lang" + ("1036" if report.french else "2057") + "\n"
    )
    footer = (
        r"{\footer\pard\f0\fs16\b0\tqr\tx9600 "
        + rtf_text(f"Keldin | {report.name} | {DATE}")
        + r"\tab {\field{\*\fldinst PAGE}{\fldrslt 1}}\par}"
        + "\n"
    )
    blocks = [header, footer]
    if report.cover:
        blocks.extend(
            [
                paragraph("", after=1700),
                paragraph(report.cover[0], size=88, bold=True, after=420),
                paragraph(report.cover[1], size=42, after=650),
                paragraph(
                    "Independent practice documents\nInternal engineering review\nDifficulty and duration uncalibrated",
                    size=24,
                ),
                paragraph(DATE, size=21),
                r"\page" + "\n",
            ]
        )
    for index, page in enumerate(report.pages):
        if index:
            blocks.append(r"\page" + "\n")
        blocks.append(paragraph(page.title, size=40, bold=True, after=400))
        blocks.extend(
            row(label, text, formal=report.french) for label, text in page.rows
        )
    return "".join(blocks) + "}"


def build(output: Path = DEFAULT_OUTPUT) -> tuple[Path, ...]:
    output.mkdir(parents=True, exist_ok=True)
    paths = tuple(output / report.filename for report in REPORTS)
    if any(path.exists() for path in paths):
        raise FileExistsError(
            "Pages inputs already exist; choose a fresh output folder."
        )
    for report, path in zip(REPORTS, paths, strict=True):
        path.write_text(render(report), encoding="ascii")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    for path in build(args.output):
        print(path)


if __name__ == "__main__":
    main()
