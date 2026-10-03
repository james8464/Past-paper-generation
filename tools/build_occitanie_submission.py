"""Build the maintained Prix Occitanie 2026 application evidence documents."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "occitanie-2026"
LIGHT_GREY = "D9D9D9"
HEADER_GREY = "F2F2F7"


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, value: int = 100) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for edge in ("top", "left", "bottom", "right"):
        element = margins.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            margins.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def set_cell_borders(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), LIGHT_GREY)


def set_repeat_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def prevent_row_split(row) -> None:
    properties = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    properties.append(cant_split)


def add_page_field(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, text, end])


def configure_document(doc: Document, *, compact: bool = False) -> None:
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.7 if compact else 1.9)
    section.bottom_margin = Cm(1.55 if compact else 1.7)
    section.left_margin = Cm(1.9 if compact else 2.1)
    section.right_margin = Cm(1.9 if compact else 2.1)
    section.header_distance = Cm(0.65)
    section.footer_distance = Cm(0.65)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10.2 if compact else 10.8)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(5 if compact else 6)
    normal.paragraph_format.line_spacing = 1.12
    for name, size in (("Title", 22), ("Heading 1", 13.5), ("Heading 2", 11.5)):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = name != "Title"
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
    title_properties = doc.styles["Title"].element.get_or_add_pPr()
    title_border = title_properties.find(qn("w:pBdr"))
    if title_border is not None:
        title_properties.remove(title_border)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Paper Creator  ·  Prix Occitanie 2026  ·  ")
    add_page_field(footer)
    for run in footer.runs:
        run.font.name = "Arial"
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(85, 85, 85)


def finalize_fonts(doc: Document) -> None:
    """Use an explicit portable face instead of Word's serif theme fallback."""
    paragraphs = list(doc.paragraphs)
    for paragraph in doc.paragraphs:
        paragraph.paragraph_format.keep_together = True
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    for paragraph in paragraphs:
        for run in paragraph.runs:
            run.font.name = "Arial"
            if paragraph.style.name == "Title":
                run.font.size = Pt(22)
                run.font.color.rgb = RGBColor(0, 0, 0)
            elif paragraph.style.name == "Heading 1":
                run.font.size = Pt(13.5)
                run.font.bold = True
            elif paragraph.style.name == "Heading 2":
                run.font.size = Pt(11.5)
                run.font.bold = True


def title_block(doc: Document, title: str, subtitle: str) -> None:
    title_paragraph = doc.add_paragraph(style="Title")
    title_paragraph.add_run(title)
    subtitle_paragraph = doc.add_paragraph(subtitle)
    subtitle_paragraph.paragraph_format.space_after = Pt(14)
    subtitle_paragraph.runs[0].font.size = Pt(11)
    subtitle_paragraph.runs[0].font.color.rgb = RGBColor(70, 70, 70)


def add_label_paragraph(doc: Document, label: str, text: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(label + " ")
    run.bold = True
    paragraph.add_run(text)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.add_run(item)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    set_repeat_header(header)
    prevent_row_split(header)
    for index, value in enumerate(headers):
        cell = header.cells[index]
        set_cell_shading(cell, HEADER_GREY)
        set_cell_margins(cell, 120)
        set_cell_borders(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        run = cell.paragraphs[0].add_run(value)
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
    for row_index, values in enumerate(rows):
        row = table.add_row()
        prevent_row_split(row)
        cells = row.cells
        for index, value in enumerate(values):
            cell = cells[index]
            set_cell_margins(cell, 120)
            set_cell_borders(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if row_index % 2:
                set_cell_shading(cell, "F5F7F9")
            cell.paragraphs[0].add_run(value)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    return table


def add_source(doc: Document, number: int, label: str, url: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.add_run(f"[{number}] {label}. ").bold = True
    paragraph.add_run(url)


def build_application() -> Path:
    doc = Document()
    configure_document(doc, compact=True)
    title_block(
        doc,
        "Candidature au Prix Occitanie 2026",
        "Paper Creator, pilote NSI Occitanie",
    )
    identity = add_table(
        doc,
        ["Nom", "Prénom", "Promotion", "Courriel", "Téléphone"],
        [["Durup", "James", "À compléter", "james.durup@student-cs.fr", "À compléter"]],
        [2.6, 2.6, 2.4, 6.2, 3.0],
    )
    identity.rows[1].cells[3].paragraphs[0].runs[0].font.size = Pt(8.4)
    add_label_paragraph(doc, "Adresse", "À compléter")
    doc.add_heading("Présentation du candidat", level=1)
    doc.add_paragraph(
        "Je suis étudiant à CentraleSupélec et je développe Paper Creator, une application macOS qui utilise des modèles d’intelligence artificielle locaux pour produire des sujets d’entraînement originaux. Je m’intéresse à la conception de logiciels vérifiables et à l’usage responsable de l’IA dans l’éducation. Une première version consacrée aux A levels britanniques m’a permis de construire le moteur de génération, les contrôles techniques et la production de PDF. Le projet présenté ici adapte ce travail au baccalauréat français et prépare un pilote avec des enseignants de NSI en Occitanie."
    )
    doc.add_heading("Titre du projet", level=1)
    doc.add_paragraph("Paper Creator, pilote NSI Occitanie")
    doc.add_heading("Description synthétique du projet", level=1)
    doc.add_paragraph(
        "Le projet aide un enseignant de Terminale à créer un sujet inédit de spécialité Numérique et sciences informatiques, accompagné d’un corrigé proposé et d’un barème indicatif. L’enseignant choisit un modèle local, lance la génération, puis relit les deux PDF avant de les imprimer ou de les distribuer par l’ENT. Les élèves n’ont besoin ni d’un Mac, ni d’un compte, ni d’un accès à une IA. L’application ne collecte aucune copie d’élève."
    )
    doc.add_paragraph(
        "La version française suit les règles annoncées pour la session 2027 : trois exercices indépendants, 3 h 30, 18 points techniques et 2 points pour la maîtrise de la langue. Chaque question est rattachée à une capacité du programme officiel. Le logiciel vérifie les totaux, les durées, certaines réponses calculables, les requêtes SQL, les traces d’algorithmes, les graphes et la cohérence entre le sujet et le corrigé. Les documents portent clairement la mention « entraînement non officiel » et restent non relus tant qu’un enseignant n’a pas enregistré sa décision."
    )

    doc.add_heading("Originalité du projet", level=1)
    doc.add_paragraph(
        "Paper Creator ne se limite pas à envoyer une consigne générale à un agent conversationnel. Il sépare le programme, les règles d’examen et les références historiques. Il demande au modèle de produire des données structurées, résout ensuite chaque exercice sans lui montrer le corrigé proposé, puis applique des contrôles déterministes et un second contrôle indépendant. Les preuves, les versions du modèle et les empreintes des fichiers restent attachées au sujet. Une relecture humaine est liée aux empreintes exactes des PDF : toute modification la rend caduque."
    )
    doc.add_paragraph(
        "L’ancrage régional sera construit et mesuré, non simplement nommé. Je souhaite organiser un pilote avec des enseignants des académies de Toulouse et de Montpellier, puis créer un module optionnel fondé sur des données ouvertes d’Occitanie. Les lycées, les transports, la consommation d’énergie et, si les droits le permettent, les ressources en eau pourront nourrir des exercices d’algorithmique et de bases de données sur des questions territoriales et climatiques réelles. Aucun partenariat régional n’est encore conclu."
    )
    doc.add_heading("Bénéficiaires", level=1)
    doc.add_paragraph(
        "Les premiers bénéficiaires sont les enseignants de NSI qui manquent de sujets nouveaux pour entraîner leurs classes. Les élèves reçoivent un PDF ordinaire, lisible sur loRdi, sur l’ENT ou sur papier. La création reste sur le Mac de l’enseignant. Ce choix respecte le parc régional existant : loRdi sert à consulter les ressources, sans prétendre exécuter l’application macOS ou un modèle volumineux."
    )
    doc.add_heading("État de développement", level=1)
    add_bullets(
        doc,
        [
            "Prototype technique : parcours français distinct, génération locale, références filtrées, points décimaux exacts, contrôles de réponses et PDF standard ou agrandi.",
            "Qualité non qualifiée : 79 annales officielles 2021–2026 sont réconciliées et 13 réservées à l’évaluation. La première campagne a rejeté dix sujets complets sur dix ; le modèle testé ne peut pas encore être recommandé.",
            "Validation humaine à organiser : aucun partenariat régional ni avis d’enseignant français n’est revendiqué. Le prix financerait l’amélioration et l’évaluation indépendante."
        ],
    )
    doc.add_heading("Présentation et aides antérieures", level=1)
    doc.add_paragraph(
        "J’ai soumis une première version britannique à une enseignante d’informatique. Ses remarques sur la difficulté des questions, le SQL, les réponses calculées, les bus informatiques et la précision des barèmes ont été transformées en contrôles et en exigences de génération."
    )
    add_label_paragraph(
        doc,
        "Financement ou demande d’aide antérieure",
        "À confirmer avant envoi.",
    )
    doc.add_heading("Adéquation au Prix Occitanie", level=1)
    doc.add_paragraph(
        "Le prix transformerait un prototype individuel en une expérimentation régionale vérifiable. Son apport ne servirait pas à acheter de la visibilité ni à revendiquer prématurément une adoption : il financerait la relecture par des enseignants, l’observation d’un pilote et l’intégration prudente de données ouvertes d’Occitanie dans des exercices réellement utiles au programme de NSI."
    )
    doc.add_paragraph(
        "Le projet est techniquement faisable dans les douze mois parce que le moteur, le parcours macOS et la production de PDF existent déjà. Le travail restant est précisément celui que le jury peut rendre possible : confronter l’outil au territoire, mesurer son utilité et documenter aussi bien les résultats positifs que les limites."
    )

    doc.add_heading("Travaux prévus pendant les douze mois suivant le prix", level=1)
    add_table(
        doc,
        ["Période", "Travail", "Résultat vérifiable"],
        [
            ["Mois 1 à 2", "Achever le banc d’essai local sur le corpus réconcilié. Recruter deux enseignants de NSI.", "Résultats conservés, modèle retenu ou rejet motivé, protocole signé par les relecteurs."],
            ["Mois 3 à 4", "Faire relire six sujets stratifiés et corriger les défauts.", "Deux avis indépendants par sujet, défauts et révisions tracés."],
            ["Mois 5 à 6", "Conduire un pilote encadré dans un établissement volontaire.", "Temps enseignant, durées élèves, ambiguïtés et contraintes d’accès mesurés."],
            ["Mois 7 à 9", "Créer le module de contextes issus de données ouvertes d’Occitanie et auditer l’accessibilité.", "Provenance des jeux de données, sujets relus, PDF standard et agrandi."],
            ["Mois 10 à 12", "Évaluer l’extension à une deuxième spécialité ou à une inférence mutualisée.", "Décision documentée à partir du pilote et des limites matérielles."],
        ],
        [2.3, 7.0, 7.0],
    )
    doc.add_heading("Utilisation du prix de 1 000 euros", level=1)
    add_table(
        doc,
        ["Dépense", "Montant", "Justification"],
        [
            ["Relecture par des enseignants", "500 €", "Rémunérer le temps d’analyse détaillée et de seconde lecture."],
            ["Déplacements du pilote", "200 €", "Rencontrer les équipes et observer l’usage réel en Occitanie."],
            ["Essais matériels et accessibilité", "200 €", "Tester plusieurs configurations et les PDF agrandis."],
            ["Données et imprévus", "100 €", "Préparer les ressources régionales et absorber un besoin validé par le pilote."],
        ],
        [6.1, 2.0, 8.2],
    )
    doc.add_heading("Faisabilité et résultats attendus", level=1)
    doc.add_paragraph(
        "Le socle logiciel fonctionne déjà sur macOS. Le risque principal n’est pas la production d’un PDF, mais la justesse pédagogique. Le projet impose donc une séquence de qualification qui conserve les échecs et interdit de confondre un contrôle automatisé avec l’avis d’un enseignant. À douze mois, le résultat attendu est un outil que deux enseignants de NSI recommandent pour un usage d’entraînement après relecture, accompagné de mesures transparentes sur le temps gagné, les erreurs rencontrées, le matériel et l’accessibilité."
    )
    doc.add_heading("Schéma d’usage", level=1)
    add_table(
        doc,
        ["Création", "Contrôles", "Décision", "Diffusion"],
        [["Mac de l’enseignant\nModèle local", "Programme, réponses, barème, originalité et PDF", "Relecture liée aux empreintes des fichiers", "PDF sur ENT, loRdi ou papier"]],
        [4.0, 4.3, 4.3, 4.0],
    )
    doc.add_paragraph(
        "Sources principales : règlement du Prix Occitanie 2026 ; Bulletin officiel NSI session 2027 ; programme officiel de Terminale NSI ; portail open data de la Région Occitanie ; dispositif loRdi. Les liens complets figurent dans le dossier technique joint au projet."
    )

    path = OUTPUT / "Prix-Occitanie-2026-Candidature-James-Durup.docx"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    finalize_fonts(doc)
    doc.save(path)
    return path


def build_technical_dossier() -> Path:
    doc = Document()
    configure_document(doc, compact=True)
    title_block(
        doc,
        "Paper Creator for French NSI",
        "Technical and user report · Prix Occitanie 2026",
    )
    doc.add_paragraph(
        "This report explains the prototype, what a teacher can do with it today, and the evidence still needed before it can be recommended for classroom practice. The engineering foundation exists, but the first complete Gemma 4 12B campaign rejected all ten papers. No French model is therefore recommended. Progress depends on measured repairs, two independent NSI teacher reviewers, and a supervised pilot."
    )
    doc.add_heading("The teacher’s task", level=1)
    doc.add_paragraph(
        "A teacher has a finite supply of past papers and needs fresh practice without introducing errors in questions or marking. Paper Creator produces a complete draft for review. The teacher decides whether to share it; the app neither marks student work nor collects student responses."
    )
    add_table(
        doc,
        ["Step", "Teacher", "Application"],
        [
            ["1", "Approve preparation of official references.", "Download, identify, and index permitted documents locally."],
            ["2", "Choose an Ollama model and print profile.", "Check the local model and record its identity."],
            ["3", "Create an unreviewed draft.", "Plan three exercises; generate, solve, check, and repair failures."],
            ["4", "Read both PDFs and the evidence.", "Show status, sources, checks, and limitations."],
            ["5", "Record a review decision.", "Bind the review to the exact file hashes."],
        ],
        [1.2, 7.3, 8.3],
    )

    doc.add_heading("Architecture", level=1)
    doc.add_paragraph(
        "A SwiftUI interface exchanges JSON messages with a Python engine. The assessment registry selects an explicit French policy. This boundary prevents UK assessment objectives, integer-only marks, and English instructions from silently applying to the baccalauréat."
    )
    add_table(
        doc,
        ["Layer", "Responsibility", "Evidence retained"],
        [
            ["Catalogue", "Education context, curriculum version, 2027 rules, and language.", "Immutable IDs and checked compatibility."],
            ["References", "Filter by France, Terminale, NSI, curriculum, category, and rights.", "URL, date, SHA-256, pages, and reference/holdout split."],
            ["Generation", "Three independent plans; French contexts, questions, answers, and credit.", "Candidates and rejected attempts in resumable checkpoints."],
            ["Verification", "Bounded SQL, traces, binary, graphs, consistency, blind solving, originality.", "Deterministic results; unresolved status when a check is unavailable."],
            ["Publication", "Atomic French question paper, proposed solution, and manifest.", "Artifact hashes; no partial release."],
            ["Review", "Human decision against an eight-part rubric.", "Separate record tied to artifact hashes."],
        ],
        [3.0, 8.0, 5.8],
    )

    doc.add_heading("Implemented French assessment rules", level=1)
    add_bullets(
        doc,
        [
            "Terminale written component, session 2027: 3 hours 30 minutes and three independent exercises.",
            "Eighteen technical points plus a separate two-point French-language component. Detailed credit is indicative, not an official marking grid.",
            "Première knowledge may be a prerequisite but cannot replace the essential Terminale focus.",
            "Each question records one to three official capability codes, a cognitive operation, a 1–4 difficulty label, and an estimated time.",
            "Each exercise covers its declared topics, totals 70 minutes, uses at least three cognitive operations, and includes a difficulty-4 question."
        ],
    )

    doc.add_heading("Question quality", level=1)
    doc.add_paragraph(
        "The model receives a constrained plan, not a vague request. A database plan can require a complex query, an INSERT/UPDATE/DELETE operation, or error diagnosis. Graph tasks carry structured vertices, edges, and weights, so the engine can check that the diagram and answer contract describe the same graph. Closed-answer questions receive a reference calculation; unsupported claims stay explicitly unresolved."
    )
    doc.add_paragraph(
        "A difficulty label from a model is not proof of difficulty. The schema rejects recall-only sequences and requires progression towards analysis, design, debugging, or justification. Final calibration must compare drafts with held-out past papers and observed learner timings."
    )

    doc.add_heading("PDF fidelity", level=1)
    doc.add_paragraph(
        "The A4 profile was measured against a 2026 Métropole paper: 595.32 × 841.92 points, body text close to 12-point Arial, and code close to 12-point Courier New. The provisional 2027 cover carries the hierarchy, vertical placement, duration, and no-calculator notice. Exercises use centred titles, italic scope lines, indented numbering, and vector diagrams. Independent branding and a visible ‘non-official practice’ title prevent confusion with an official examination paper."
    )

    doc.add_heading("Safety, privacy, and rights", level=1)
    add_table(
        doc,
        ["Risk", "Current safeguard", "Limit"],
        [
            ["Data exposure", "French UI uses loopback Ollama; no student responses or silent cloud fallback.", "The separate CLI permits a remote Ollama server only by explicit opt-in over HTTPS."],
            ["Generated code", "SQL runs in an isolated, bounded setting; supported code has restricted interpretation.", "Arbitrary generated Python is never executed."],
            ["Wrong source", "Scope filter precedes ranking; holdouts are separate; empty eligible sets fail explicitly.", "Third-party rights still need document-level review."],
            ["Past-paper copying", "Compare text, normalised code, structure, and previous generations.", "Similarity is risk evidence, not a legal guarantee."],
            ["Document rights", "Local references retain URL, rights status, and hash.", "Third-party illustrations need separate clearance."],
        ],
        [3.0, 8.0, 5.8],
    )

    doc.add_heading("Qualification evidence", level=1)
    doc.add_paragraph(
        "The benchmark runner attempts ten complete papers per model—30 exercises per configuration—using fixed seeds. It retains outputs, errors, checkpoints, timing, Ollama version, hardware, model digest, and source identity. A lock prevents duplicate French campaigns. If code or references change, the run stops rather than mixing incompatible evidence."
    )
    add_table(
        doc,
        ["Gate", "Required evidence", "Status · 3 October 2026"],
        [
            ["Automated", "Tests, content checks, publication checks, and PDF inspection with no blocking defect.", "Controls implemented; Gemma 4 12B first campaign: 0/10 accepted. Redesign and rerun needed."],
            ["Teachers", "Two NSI teachers independently review six papers; correctness and marking 4/4, other dimensions at least 3/4.", "Reviewers not yet recruited."],
            ["Learners", "Supervised pilot measuring timing, ambiguity, accessibility, and teacher workload.", "Planned; no partner school yet."],
        ],
        [3.2, 9.0, 4.6],
    )

    doc.add_heading("Occitanie deployment", level=1)
    doc.add_paragraph(
        "The first deployment keeps generation on a teacher’s Mac and uses existing channels to share PDFs with students. Occitanie’s loRdi devices support access to resources; the project does not claim that these Windows laptops run the Mac app or a large model. The pilot will seek teachers in the Toulouse and Montpellier academies and document actual access conditions rather than assert an unevidenced regional divide."
    )
    doc.add_paragraph(
        "A planned regional module will use cleared Open Licence 2.0 datasets. Official values will remain distinct from synthetic exercise data. Candidate contexts include school infrastructure, loRdi, energy use, renewables, and transport. Every context must support a genuine NSI capability, such as SQL, route graphs, or algorithm analysis; regional names alone are not educational value."
    )

    doc.add_heading("Risks and decisions", level=1)
    add_table(
        doc,
        ["Risk", "Decision"],
        [
            ["Plausible but wrong question", "Block automated publication on failed checks; require human review before classroom use."],
            ["Model exceeds available memory", "Prioritise correctness over speed, measure actual hardware, and do not promise compatibility with every Mac."],
            ["Historical layout, new 2027 rules", "Label the 2027 visual profile provisional until contemporary papers support it."],
            ["Weak regional connection", "Test a real pilot and relevant regional data rather than merely rename places in a question."],
            ["Unfavourable pilot", "Publish the limitation, narrow scope, or stop the affected extension."],
        ],
        [6.0, 10.8],
    )

    doc.add_heading("Primary sources", level=1)
    sources = [
        ("Prix Occitanie 2026 rules", "https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf"),
        ("Official NSI 2027 examination definition", "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N"),
        ("NSI curriculum and resources", "https://eduscol.education.gouv.fr/5823/programmes-et-ressources-en-numerique-et-sciences-informatiques-voie-g"),
        ("Official past-paper archive", "https://eduscol.education.gouv.fr/5199/annales-des-epreuves-du-baccalaureat-des-voies-generale-et-technologique"),
        ("loRdi", "https://www.laregion.fr/aide-a-l-acquisition-d-un-ordinateur-portable-lordi"),
        ("Occitanie school strategy", "https://www.laregion.fr/Quelle-demarche-pour-le-lycee-de-demain-39604"),
        ("Occitanie schools open data", "https://data.laregion.fr/explore/dataset/lycees-occitanie/"),
        ("Occitanie energy-use history", "https://data.laregion.fr/explore/dataset/historique-de-la-consommation-denergie-en-occitanie/"),
        ("CNIL guidance for teachers", "https://www.cnil.fr/fr/enseignant-usage-systeme-ia"),
    ]
    for index, (label, url) in enumerate(sources, 1):
        add_source(doc, index, label, url)

    path = OUTPUT / "Paper-Creator-NSI-Technical-and-User-Report.docx"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    finalize_fonts(doc)
    doc.save(path)
    return path


def build_mathematical_analysis() -> Path:
    doc = Document()
    configure_document(doc)
    title_block(
        doc,
        "Mathematical analysis of qualification",
        "Paper Creator · Occitanie NSI pilot · 3 October 2026",
    )
    doc.add_paragraph(
        "This note defines what the project measures and the thresholds for deciding whether a paper may proceed through qualification. A small sample cannot prove psychometric equivalence to the baccalauréat. Numerical examples remain illustrative until a supervised pilot supplies observations."
    )
    doc.add_paragraph(
        "Observed result on 3 October 2026: the first campaign of ten complete Gemma 4 12B papers accepted none. The zero-defect sample calculations below describe a possible future result; they do not apply to this campaign or justify recommending that model."
    )

    doc.add_heading("Exact paper constraints", level=1)
    doc.add_paragraph(
        "For three exercises e = 1, 2, 3, the plan assigns mₑ = 70 minutes each. Thus Σmₑ = 210 minutes, or 3 hours 30 minutes. Technical credits pₑ are 5.5, 6, and 6.5 points in a seed-dependent order, with Σpₑ = 18. A separate French-language component contributes exactly 2 points, making the printed total 20. Credit uses exact decimal arithmetic, not binary floating point."
    )
    doc.add_paragraph(
        "For every question q, its marking criteria must satisfy Σcᵢ = p_q; estimated question times in each exercise must satisfy Σt_q = 70 minutes. A mismatch—even 0.5 point—blocks the document."
    )

    doc.add_heading("Cognitive demand", level=1)
    doc.add_paragraph(
        "Each question is labelled as recall, application, analysis, design, debugging, or justification, and receives an integer difficulty label from 1 to 4. A valid exercise has at most one recall-only question, at least three different operations, at least two higher-order operations, and at least one difficulty-4 question. These constraints are structural guardrails; they do not establish how difficult learners will actually find the work."
    )

    doc.add_heading("Defect rates and sample size", level=1)
    doc.add_paragraph(
        "Let p be the probability that an exercise has a blocking defect detectable during review. Given n independent exercises and zero observed defects, a simple one-sided 95% upper bound is p₉₅ = 1 − 0.05^(1/n). For n = 30 exercises from one model, p₉₅ ≈ 9.5%. Even a flawless 30-exercise run would not establish a true defect rate below 1%; roughly 299 defect-free exercises would be needed for that bound."
    )
    add_table(
        doc,
        ["Zero-defect sample", "95% upper bound", "Interpretation"],
        [
            ["30 exercises", "9.5%", "Initial model screen, not a strong reliability claim."],
            ["90 exercises", "3.3%", "A pooled total would not transfer to each model."],
            ["299 exercises", "1.0%", "Approximate scale needed for a bound below 1%."],
        ],
        [4.0, 4.0, 8.8],
    )
    doc.add_paragraph(
        "Independence is optimistic: exercises may share a model, prompt, or verification weakness. The evaluation must therefore retain defects by category and version rather than publish a context-free aggregate rate."
    )

    doc.add_heading("Teacher evaluation", level=1)
    doc.add_paragraph(
        "Two teachers score six papers independently on eight dimensions: correctness, ambiguity, curriculum fit, French, difficulty, duration, marking, and authentic structure. Scores run from 1 to 4. After revisions, a paper passes only if both reviewers give correctness = 4 and marking = 4, with every other dimension at least 3. A high average cannot hide a substantive error."
    )
    doc.add_paragraph(
        "Agreement will be reported per dimension. For ordinal ratings, the project will calculate quadratically weighted kappa κw, alongside a disagreement matrix and comments. High agreement can still coexist with shared bias, and only twelve review sheets leave wide uncertainty."
    )

    doc.add_heading("Timing calibration", level=1)
    doc.add_paragraph(
        "For learner i and paper j, relative duration error is eᵢⱼ = (Tᵢⱼ − 210) / 210. The median T better describes a typical completion time than a mean distorted by abandoned attempts. Results will include the median, interquartile range, number of completed papers, and share exceeding 210 minutes. Contexts and approved accommodations will be reported separately; a small pilot cannot define a national norm."
    )

    doc.add_heading("Teacher time", level=1)
    doc.add_paragraph(
        "Time saved per paper is Δt = t_manual − (t_supervised generation + t_review + t_repair). The pilot will measure each term rather than ask for a general impression. Across N papers, annual time saved is N × Δt. Illustration only: if a manual paper takes 120 minutes and assisted generation, review, and repair take 35, twelve papers save 17 hours. This is not an observed result."
    )

    doc.add_heading("Layout fidelity", level=1)
    doc.add_paragraph(
        "Visual comparison uses measurements, not an opaque ‘similarity percentage’. For feature k—such as a margin, font size, or heading position—the normalised distance is d_k = |x_k − r_k| / s_k, where r_k is the reference measurement and s_k is a justified tolerance. Aggregate layout distance D = Σw_k d_k flags regressions; published weights sum to 1. This score says nothing about question quality."
    )
    doc.add_paragraph(
        "The current profile uses A4 at 595.32 × 841.92 points, 12-point body text, a left margin near 70.6 points, 14-point exercise titles, and cover positions measured from a 2026 Métropole paper. Independent branding and the non-official notice are deliberate differences."
    )

    doc.add_heading("Originality", level=1)
    doc.add_paragraph(
        "Screening compares text n-grams, normalised code, question structure, and previous generations. Thresholds must be calibrated on labelled copies, superficial renamings, and genuinely different tasks; precision and recall are reported separately. A threshold is acceptable only if it rejects copied and renamed holdout cases without discarding too many original ones. This reduces risk but is not a copyright guarantee."
    )

    doc.add_heading("Energy and resource use", level=1)
    doc.add_paragraph(
        "Model download size is neither memory use nor energy consumption. During benchmarking, energy per accepted paper will be E = P_mean × t / 3600, with P in watts and t in seconds. The report will include energy spent on rejected attempts and the number of times a PDF is reused. No carbon-reduction claim is justified without measured power, an explicit emissions factor, and a relevant comparator."
    )

    doc.add_heading("Budget and decision rule", level=1)
    add_table(
        doc,
        ["Use", "Amount", "Evidence purchased"],
        [
            ["Teacher review", "€500", "Twelve independent review sheets for six papers and time spent."],
            ["Pilot travel", "€200", "Observed school context and access constraints."],
            ["Hardware/accessibility", "€200", "Tested configurations, memory, speed, standard/enlarged PDFs."],
            ["Data/contingency", "€100", "Regional resources or a documented pilot need."],
        ],
        [5.2, 2.2, 9.4],
    )
    doc.add_paragraph(
        "Continuing beyond the pilot requires all of the following: no unresolved blocking defect, two written teacher recommendations for reviewed practice use, plausible completion time, observed teacher time savings, and hardware suitable for the chosen deployment. One favourable metric is not enough."
    )

    doc.add_heading("References", level=1)
    add_source(doc, 1, "NSI 2027 rules", "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")
    add_source(doc, 2, "Official past papers", "https://eduscol.education.gouv.fr/5199/annales-des-epreuves-du-baccalaureat-des-voies-generale-et-technologique")
    add_source(doc, 3, "Official French-language rubric", "https://www.education.gouv.fr/sites/default/files/document/annexe-attendus-et-observables-redactionnels-520693.pdf")
    add_source(doc, 4, "Prix Occitanie 2026 rules", "https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf")

    path = OUTPUT / "Paper-Creator-NSI-Mathematical-Analysis.docx"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    finalize_fonts(doc)
    doc.save(path)
    return path


def main() -> None:
    for path in (build_application(), build_technical_dossier(), build_mathematical_analysis()):
        print(path)


if __name__ == "__main__":
    main()
