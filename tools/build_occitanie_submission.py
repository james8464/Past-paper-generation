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
        "Paper Creator pour le baccalauréat NSI",
        "Dossier technique et parcours utilisateur, Prix Occitanie 2026",
    )
    doc.add_paragraph(
        "Ce dossier explique le prototype, ce qu’un enseignant peut en faire aujourd’hui et les preuves encore nécessaires avant un usage scolaire qualifié. Le socle technique existe, mais la première campagne complète avec Gemma 4 12B a rejeté dix sujets sur dix. Aucun modèle français n’est donc recommandé. La suite dépend de corrections mesurées, de deux relecteurs NSI et d’un pilote encadré."
    )
    doc.add_heading("Besoin utilisateur", level=1)
    doc.add_paragraph(
        "Un enseignant dispose d’un nombre fini d’annales et doit préparer des exercices nouveaux sans introduire d’erreur de contenu ou de barème. Paper Creator produit un brouillon complet à relire. L’enseignant garde la décision de diffusion ; l’application ne corrige pas les copies et ne collecte aucune donnée élève."
    )
    add_table(
        doc,
        ["Étape", "Action de l’enseignant", "Action du logiciel"],
        [
            ["1", "Préparer les références officielles avec son accord.", "Télécharger, identifier et indexer localement les documents autorisés."],
            ["2", "Choisir un modèle Ollama et le profil d’impression.", "Vérifier que le modèle est local et enregistrer son empreinte."],
            ["3", "Créer un sujet non relu.", "Planifier trois exercices, générer, résoudre, contrôler et réparer les échecs."],
            ["4", "Lire le sujet, le corrigé et les preuves.", "Afficher le statut, les sources, les contrôles et les limites."],
            ["5", "Enregistrer une décision de relecture.", "Lier le compte rendu aux empreintes exactes des fichiers."],
        ],
        [1.2, 7.3, 8.3],
    )

    doc.add_heading("Architecture", level=1)
    doc.add_paragraph(
        "L’interface SwiftUI communique avec un moteur Python par messages JSON. Le registre d’évaluations sélectionne une politique française explicite. Cette séparation empêche les objectifs d’évaluation britanniques, les barèmes entiers et les consignes en anglais de s’appliquer par défaut au baccalauréat."
    )
    add_table(
        doc,
        ["Couche", "Responsabilité", "Preuve produite"],
        [
            ["Catalogue", "Contexte éducatif, version du programme, règles 2027 et langue.", "Identifiants immuables et compatibilité contrôlée."],
            ["Références", "Filtrage France, Terminale, NSI, programme compatible, catégorie et droits.", "URL, date, SHA-256, pages et séparation référence/holdout."],
            ["Génération", "Trois plans indépendants, contexte, questions, réponses et barème en français.", "Candidats et tentatives rejetées conservés dans le point de reprise."],
            ["Vérification", "SQL borné, traces, binaire, graphes, cohérence, solution indépendante et originalité.", "Résultats déterministes et statut non résolu quand le contrôle manque."],
            ["Publication", "Sujet, corrigé et manifeste atomiques en français.", "Empreintes des artefacts et absence de publication partielle."],
            ["Relecture", "Décision humaine et grille de huit dimensions.", "Enregistrement séparé lié aux empreintes."],
        ],
        [3.0, 8.0, 5.8],
    )

    doc.add_heading("Règles françaises implémentées", level=1)
    add_bullets(
        doc,
        [
            "Partie écrite de Terminale générale, session 2027 : 3 h 30 et trois exercices indépendants.",
            "Dix-huit points techniques et deux points distincts pour la maîtrise de la langue. Le détail du barème reste indicatif.",
            "Connaissances de Première utilisables comme prérequis, sans remplacer les capacités essentielles de Terminale.",
            "Chaque question porte un à trois codes de capacité officiels, une opération cognitive, une difficulté de 1 à 4 et un temps estimé.",
            "Chaque exercice couvre ses thèmes annoncés, totalise 70 minutes, contient au moins trois opérations cognitives et une question de difficulté 4."
        ],
    )

    doc.add_heading("Qualité des questions", level=1)
    doc.add_paragraph(
        "Le modèle reçoit un plan contraint plutôt qu’une demande vague. Pour les bases de données, le plan peut exiger une interrogation complexe, une mutation INSERT, UPDATE ou DELETE, ou la détection d’une anomalie. Pour les graphes, le sujet contient des sommets, arêtes et poids structurés, puis le moteur vérifie que la figure et le contrat de réponse décrivent exactement le même graphe. Les questions fermées passent par un calcul de référence ; les affirmations non couvertes restent explicitement non résolues."
    )
    doc.add_paragraph(
        "La difficulté ne peut pas être prouvée par une étiquette du modèle. Le schéma refuse les suites de questions de simple rappel et impose une progression vers l’analyse, la conception, le débogage ou la justification. La calibration finale compare les sujets à un holdout d’annales et aux temps observés pendant le pilote."
    )

    doc.add_heading("Fidélité des PDF", level=1)
    doc.add_paragraph(
        "Le profil A4 a été mesuré sur le sujet Métropole 2026 : géométrie 595,32 × 841,92 points, corps principal proche d’Arial 12 points et code proche de Courier New 12 points. La couverture 2027 reprend la hiérarchie, les positions verticales, la durée et l’interdiction de la calculatrice. Les exercices utilisent des titres centrés, une phrase de portée en italique, des numéros en retrait et des figures vectorielles. Le pied de page et le titre « entraînement non officiel » conservent une identité indépendante ; le logiciel n’imite aucun identifiant officiel."
    )

    doc.add_heading("Sécurité, confidentialité et droits", level=1)
    add_table(
        doc,
        ["Risque", "Mesure actuelle", "Limite"],
        [
            ["Fuite de données", "Modèle local par défaut, aucune copie élève, aucun repli cloud silencieux.", "Un serveur Ollama distant reste possible uniquement avec accord explicite et HTTPS."],
            ["Code généré", "SQL isolé et borné ; interprétation restreinte des constructions prises en charge.", "Le logiciel n’exécute jamais un programme Python arbitraire."],
            ["Source inadaptée", "Filtrage du périmètre avant classement, holdout séparé et échec explicite si aucune source ne convient.", "Les droits et illustrations tierces restent examinés document par document."],
            ["Copie d’annale", "Comparaison du texte, du code normalisé, de la structure et des générations précédentes.", "Un score de similarité ne constitue pas une garantie juridique."],
            ["Droits documentaires", "Références conservées localement avec URL, droits et empreinte.", "Les illustrations tierces demandent une analyse document par document."],
        ],
        [3.0, 8.0, 5.8],
    )

    doc.add_heading("Qualification technique", level=1)
    doc.add_paragraph(
        "Le banc d’essai autonome exécute dix sujets par modèle, soit trente exercices par configuration, sur des graines fixes. Il conserve les sorties, erreurs, points de reprise, temps, version Ollama, matériel, empreinte du modèle et empreinte du code. Un verrou empêche deux campagnes françaises simultanées. Si le code ou les références changent, la campagne s’arrête au lieu de mélanger des résultats incompatibles."
    )
    add_table(
        doc,
        ["Niveau", "Condition de passage", "Statut au 3 octobre 2026"],
        [
            ["Automatisé", "Tests, contrôles de contenu, publication et inspection PDF sans défaut bloquant.", "Contrôles implémentés ; première campagne Gemma 4 12B : 0/10 sujet accepté. Correctifs et nouvel essai requis."],
            ["Enseignants", "Deux enseignants relisent indépendamment six sujets ; exactitude et barème à 4/4, autres dimensions au moins 3/4.", "Relecteurs non encore recrutés."],
            ["Élèves", "Pilote supervisé : durée, ambiguïtés, accessibilité et charge enseignant.", "Planifié, sous réserve d’un établissement volontaire."],
        ],
        [3.2, 9.0, 4.6],
    )

    doc.add_heading("Déploiement en Occitanie", level=1)
    doc.add_paragraph(
        "Le premier déploiement garde la création sur le Mac de l’enseignant et utilise les canaux existants pour les élèves. La Région indique que tous les lycées publics sont labellisés « Lycées numériques » et que loRdi vise l’accès aux ressources pédagogiques. Le projet ne prétend pas faire tourner l’application sur ces ordinateurs Windows ; ils lisent simplement les PDF. Le pilote cherchera des enseignants dans les académies de Toulouse et de Montpellier et documentera les différences réelles de contexte avant toute affirmation territoriale."
    )
    doc.add_paragraph(
        "Le module régional prévu utilisera des jeux sous Licence Ouverte 2.0. Les valeurs officielles resteront distinguées des données synthétiques d’un exercice. Les premiers thèmes envisagés sont l’infrastructure des lycées et loRdi, la consommation d’énergie, les énergies renouvelables et les transports. Chaque contexte devra servir une capacité NSI réelle, par exemple une requête SQL, un graphe de routage ou une analyse algorithmique."
    )

    doc.add_heading("Risques et décisions", level=1)
    add_table(
        doc,
        ["Risque", "Décision"],
        [
            ["Erreur pédagogique crédible mais fausse", "Bloquer la publication automatisée quand un contrôle échoue et conserver la relecture humaine comme condition d’usage."],
            ["Modèle trop lourd pour le matériel", "Comparer la qualité avant la vitesse, mesurer le matériel réel et ne pas annoncer une compatibilité avec tous les Mac."],
            ["Mise en page historiquement exacte mais règles 2027 nouvelles", "Étiqueter le profil 2027 comme provisoire jusqu’à publication d’exemples contemporains."],
            ["Faible lien régional", "Évaluer un pilote réel et des données régionales plutôt que renommer artificiellement les villes d’un exercice."],
            ["Résultat de pilote défavorable", "Publier la limite, restreindre le périmètre ou arrêter l’extension concernée."],
        ],
        [6.0, 10.8],
    )

    doc.add_heading("Sources", level=1)
    sources = [
        ("Règlement du Prix Occitanie 2026", "https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf"),
        ("Définition officielle de l’épreuve NSI 2027", "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N"),
        ("Programmes et ressources NSI", "https://eduscol.education.gouv.fr/5823/programmes-et-ressources-en-numerique-et-sciences-informatiques-voie-g"),
        ("Annales officielles", "https://eduscol.education.gouv.fr/5199/annales-des-epreuves-du-baccalaureat-des-voies-generale-et-technologique"),
        ("loRdi", "https://www.laregion.fr/aide-a-l-acquisition-d-un-ordinateur-portable-lordi"),
        ("Lycées de demain", "https://www.laregion.fr/Quelle-demarche-pour-le-lycee-de-demain-39604"),
        ("Open data des lycées d’Occitanie", "https://data.laregion.fr/explore/dataset/lycees-occitanie/"),
        ("Historique de consommation d’énergie", "https://data.laregion.fr/explore/dataset/historique-de-la-consommation-denergie-en-occitanie/"),
        ("Recommandations CNIL pour les enseignants", "https://www.cnil.fr/fr/enseignant-usage-systeme-ia"),
    ]
    for index, (label, url) in enumerate(sources, 1):
        add_source(doc, index, label, url)

    path = OUTPUT / "Paper-Creator-NSI-Dossier-Technique-et-Usage.docx"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    finalize_fonts(doc)
    doc.save(path)
    return path


def build_mathematical_analysis() -> Path:
    doc = Document()
    configure_document(doc)
    title_block(
        doc,
        "Analyse mathématique de la qualification",
        "Paper Creator, pilote NSI Occitanie, version du 3 octobre 2026",
    )
    doc.add_paragraph(
        "Cette note définit les quantités que le projet mesure et les seuils utilisés pour décider si un sujet peut poursuivre la qualification. Elle ne transforme pas un petit échantillon en preuve d’équivalence psychométrique avec le baccalauréat. Les exemples numériques sont signalés comme illustratifs tant que le pilote n’a pas fourni de données."
    )
    doc.add_paragraph(
        "Résultat observé au 3 octobre 2026 : la première campagne de dix sujets complets avec Gemma 4 12B n’a accepté aucun sujet. Les calculs d’échantillonnage ci-dessous décrivent un scénario futur sans défaut ; ils ne s’appliquent pas à cette campagne et ne justifient aucune recommandation du modèle."
    )

    doc.add_heading("Contraintes exactes du sujet", level=1)
    doc.add_paragraph(
        "Pour les trois exercices e = 1, 2, 3, le logiciel impose une durée mₑ = 70 minutes. La durée totale vaut donc Σmₑ = 210 minutes, soit 3 h 30. Les crédits techniques pₑ sont tirés parmi 5,5 ; 6 ; 6,5 points dans un ordre dépendant de la graine, avec Σpₑ = 18. Le composant de langue vaut exactement 2 points et reste séparé. Le total imprimé est 20 points. Les calculs utilisent des nombres décimaux exacts, et non des flottants binaires."
    )
    doc.add_paragraph(
        "Pour chaque question q d’un exercice, les points de ses critères doivent vérifier Σcᵢ = p_q et les temps estimés doivent vérifier Σt_q = 70. Une différence, même de 0,5 point, bloque le document."
    )

    doc.add_heading("Demande cognitive", level=1)
    doc.add_paragraph(
        "Chaque question reçoit une opération parmi rappel, application, analyse, conception, débogage et justification, ainsi qu’une difficulté entière de 1 à 4. Un exercice valide contient au plus une question de rappel, au moins trois opérations différentes, au moins deux opérations de niveau supérieur parmi analyse, conception, débogage et justification, et au moins une question de difficulté 4. Ces inégalités constituent un garde-fou structurel ; elles ne prouvent pas que des élèves ressentiront la difficulté attendue."
    )

    doc.add_heading("Taux de défaut et taille d’échantillon", level=1)
    doc.add_paragraph(
        "Soit p la probabilité qu’un exercice contienne un défaut bloquant détectable pendant la revue. Après n exercices indépendants et zéro défaut observé, une borne supérieure unilatérale simple à 95 % est p₉₅ = 1 - 0,05^(1/n). Pour n = 30 exercices d’un modèle, p₉₅ ≈ 9,5 %. Même une campagne sans échec ne permet donc pas d’affirmer que le taux réel est inférieur à 1 %. Il faudrait environ 299 exercices sans défaut pour atteindre cette borne."
    )
    add_table(
        doc,
        ["Observations sans défaut", "Borne supérieure 95 %", "Interprétation"],
        [
            ["30 exercices", "9,5 %", "Premier tri d’un modèle, insuffisant pour une affirmation forte."],
            ["90 exercices", "3,3 %", "Résultat agrégé de trois modèles, non transférable à chaque modèle."],
            ["299 exercices", "1,0 %", "Ordre de grandeur nécessaire pour une borne inférieure à 1 %."],
        ],
        [4.0, 4.0, 8.8],
    )
    doc.add_paragraph(
        "L’hypothèse d’indépendance est optimiste : plusieurs exercices peuvent partager le même modèle, le même prompt ou la même faiblesse de contrôle. Le rapport conserve donc les défauts par catégorie et par version, au lieu de publier un taux unique sans contexte."
    )

    doc.add_heading("Évaluation par les enseignants", level=1)
    doc.add_paragraph(
        "Deux enseignants notent six sujets sur huit dimensions : exactitude, ambiguïté, programme, français, difficulté, durée, barème et structure authentique. Chaque note va de 1 à 4. Un sujet ne passe que si exactitude = 4, barème = 4 et toutes les autres notes sont au moins 3 pour les deux relecteurs après révision. Cette règle privilégie l’absence d’erreur substantielle plutôt qu’une moyenne qui pourrait masquer un défaut grave."
    )
    doc.add_paragraph(
        "L’accord entre relecteurs sera décrit par dimension. Pour les notes ordinales, le projet calculera le kappa pondéré quadratique κw. Il publiera aussi la matrice des désaccords et les commentaires, car un κ élevé peut coexister avec un biais partagé. Avec seulement douze fiches de revue, l’intervalle d’incertitude restera large."
    )

    doc.add_heading("Calibration du temps", level=1)
    doc.add_paragraph(
        "Pour un élève i et un sujet j, l’erreur relative de durée vaut eᵢⱼ = (Tᵢⱼ - 210) / 210. La médiane de T décrit mieux le temps typique qu’une moyenne sensible aux abandons. Le rapport donnera la médiane, l’écart interquartile, le nombre de copies terminées et la proportion dépassant 210 minutes. Les observations seront séparées selon le contexte et l’aménagement éventuel ; elles ne serviront pas à construire une norme nationale."
    )

    doc.add_heading("Mesure du temps enseignant", level=1)
    doc.add_paragraph(
        "Le gain par sujet est Δt = t_manuel - (t_génération surveillée + t_relecture + t_correction). Le pilote mesure chaque terme au lieu de demander une impression globale. Pour N sujets, la valeur annuelle en temps est N × Δt. Exemple illustratif : si un sujet manuel demande 120 minutes et que la génération, la relecture et les corrections demandent 35 minutes, douze sujets économisent 17 heures. Ce chiffre ne sera pas présenté comme un résultat avant observation."
    )

    doc.add_heading("Fidélité de mise en page", level=1)
    doc.add_paragraph(
        "La comparaison visuelle repose sur des mesures, pas sur un pourcentage opaque de ressemblance. Pour une caractéristique k, par exemple la marge, la taille de police ou la position verticale d’un titre, la distance normalisée est d_k = |x_k - r_k| / s_k, où r_k est la mesure de référence et s_k une tolérance justifiée. La distance de mise en page D = Σw_k d_k sert à détecter une régression. Les poids w_k totalisent 1 et sont publiés. Le score ne couvre pas la qualité des questions."
    )
    doc.add_paragraph(
        "Le profil actuel utilise notamment A4 595,32 × 841,92 points, un corps de 12 points, une marge gauche proche de 70,6 points, des titres d’exercice de 14 points et des positions de couverture mesurées sur le sujet Métropole 2026. L’identité indépendante et la mention non officielle restent des écarts voulus."
    )

    doc.add_heading("Originalité", level=1)
    doc.add_paragraph(
        "Le contrôle compare les n-grammes de texte, le code normalisé, la structure des questions et les générations précédentes. Les seuils sont ajustés sur trois classes étiquetées : copie, renommage superficiel et exercice réellement différent. La précision et le rappel sont rapportés séparément. Un seuil est acceptable seulement si les copies et renommages du jeu de validation sont rejetés sans éliminer une part excessive des exercices différents. Ce contrôle réduit un risque ; il ne constitue pas une garantie de droit d’auteur."
    )

    doc.add_heading("Énergie et sobriété", level=1)
    doc.add_paragraph(
        "La taille d’un téléchargement de modèle ne mesure ni la mémoire utilisée ni l’énergie. Lors du banc d’essai, l’énergie par sujet accepté sera E = P_moyenne × t / 3600, avec P en watts et t en secondes. Le rapport donnera l’énergie des tentatives rejetées et le nombre de réutilisations du PDF. Aucune réduction d’empreinte carbone ne sera revendiquée sans mesure de puissance, facteur d’émission explicite et scénario de comparaison pertinent."
    )

    doc.add_heading("Budget et seuil de décision", level=1)
    add_table(
        doc,
        ["Poste", "Montant", "Mesure associée"],
        [
            ["Relecture", "500 €", "Douze fiches indépendantes sur six sujets et temps réellement passé."],
            ["Déplacements", "200 €", "Séances du pilote, contexte de l’établissement et contraintes observées."],
            ["Matériel et accessibilité", "200 €", "Configurations testées, mémoire, durée, PDF standard et agrandi."],
            ["Données et imprévus", "100 €", "Ressources régionales ou besoin documenté par le pilote."],
        ],
        [5.2, 2.2, 9.4],
    )
    doc.add_paragraph(
        "La poursuite au-delà du pilote exige simultanément : aucun défaut bloquant non résolu, deux recommandations écrites pour un usage d’entraînement après relecture, une durée plausible, un gain de temps enseignant observé et un matériel compatible avec le scénario choisi. Un seul indicateur favorable ne suffit pas."
    )

    doc.add_heading("Références", level=1)
    add_source(doc, 1, "Règles NSI 2027", "https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N")
    add_source(doc, 2, "Annales officielles", "https://eduscol.education.gouv.fr/5199/annales-des-epreuves-du-baccalaureat-des-voies-generale-et-technologique")
    add_source(doc, 3, "Grille nationale de maîtrise de la langue", "https://www.education.gouv.fr/sites/default/files/document/annexe-attendus-et-observables-redactionnels-520693.pdf")
    add_source(doc, 4, "Règlement du Prix Occitanie 2026", "https://association.centralesupelec-alumni.com/medias/editor/PRIX_OCCITANIE_2026/REGLEMENT_PRIX_OCCITANIE_2026.pdf")

    path = OUTPUT / "Paper-Creator-NSI-Analyse-Mathematique.docx"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    finalize_fonts(doc)
    doc.save(path)
    return path


def main() -> None:
    for path in (build_application(), build_technical_dossier(), build_mathematical_analysis()):
        print(path)


if __name__ == "__main__":
    main()
