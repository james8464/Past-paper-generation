# Publish French assessments using shared providers, events and render transactions.

import json
import os
import re
import shutil
import signal
import tempfile
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request

import pymupdf

from Backend.Core.events import emit, emit_progress
from Backend.Core.france.database_audit_contract import (
    DatabaseAuditContract,
    build_database_audit_contract,
)
from Backend.Core.france.database_audit_prose import database_audit_working_materials
from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.database_contract import (
    DatabaseContract,
    build_database_contract,
)
from Backend.Core.france.database_depth_contract import (
    DatabaseDepthContract,
    build_database_depth_contract,
)
from Backend.Core.france.database_reconciliation_contract import (
    DatabaseReconciliationContract,
    build_database_reconciliation_contract,
)
from Backend.Core.france.database_reconciliation_prose import (
    database_reconciliation_working_materials,
)
from Backend.Core.france.expanded_pipeline import (
    VERSION as EXPANDED_VERSION,
)
from Backend.Core.france.expanded_pipeline import (
    FamilyCatalogueExhausted,
    choose_fresh_seed,
)
from Backend.Core.france.extended_pipeline import (
    VERSION as EXTENDED_VERSION,
)
from Backend.Core.france.graph_resilience_contract import (
    GraphResilienceContract,
    build_graph_resilience_contract,
)
from Backend.Core.france.graph_route_trace_contract import (
    GraphRouteTraceContract,
    build_graph_route_trace_contract,
)
from Backend.Core.france.graph_tree_binding import canonical_answer, graph_edge_manifest
from Backend.Core.france.graph_tree_contract import (
    GraphTreeContract,
    build_graph_tree_contract,
)
from Backend.Core.france.graph_tree_depth_contract import (
    GraphTreeDepthContract,
    build_graph_tree_depth_contract,
)
from Backend.Core.france.graph_two_outage_contract import (
    GraphTwoOutageContract,
    build_graph_two_outage_contract,
)
from Backend.Core.france.network import open_ollama_request
from Backend.Core.france.network_binding import network_materials
from Backend.Core.france.network_contract import NetworkContract, build_network_contract
from Backend.Core.france.network_depth_contract import (
    NetworkDepthContract,
    build_network_depth_contract,
)
from Backend.Core.france.network_incident_contract import (
    NetworkIncidentContract,
    build_network_incident_contract,
)
from Backend.Core.france.network_incident_prose import (
    validate_network_incident_exercise,
)
from Backend.Core.france.network_incident_timeline_contract import (
    NetworkIncidentTimelineContract,
    build_network_incident_timeline_contract,
)
from Backend.Core.france.network_incident_timeline_prose import (
    validate_network_incident_timeline_exercise,
)
from Backend.Core.france.network_reasoning_contract import (
    NetworkReasoningContract,
    build_network_reasoning_contract,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import (
    CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION,
    CONTROLLED_DATABASE_CONSTRUCTION_PROMPT_VERSION,
    CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
    CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    CONTROLLED_DATABASE_RECONCILIATION_PROMPT_VERSION,
    CONTROLLED_GRAPH_RESILIENCE_PROMPT_VERSION,
    CONTROLLED_GRAPH_ROUTE_TRACE_PROMPT_VERSION,
    CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
    CONTROLLED_GRAPH_TWO_OUTAGE_PROMPT_VERSION,
    CONTROLLED_NETWORK_DEPTH_PROMPT_VERSION,
    CONTROLLED_NETWORK_INCIDENT_MARKING_PROMPT_VERSION,
    CONTROLLED_NETWORK_INCIDENT_PROMPT_VERSION,
    CONTROLLED_NETWORK_INCIDENT_TIMELINE_PROMPT_VERSION,
    CONTROLLED_NETWORK_PROMPT_VERSION,
    CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
    CONTROLLED_ROUTE_FAMILIES_PROMPT_VERSION,
    CONTROLLED_ROUTE_SELECTION_PROMPT_VERSION,
    CONTROLLED_TREE_CONSTRUCTION_PROMPT_VERSION,
    CONTROLLED_WHOLE_CASE_PROMPT_VERSION,
    atomic_json,
    digest,
    exercise_candidate_text,
    generate_assessment,
    validate_package,
)
from Backend.Core.france.provider import (
    ApplicationOwnedFrenchClient,
    FrenchOllamaClient,
)
from Backend.Core.france.rendering import (
    printable_database_criterion,
    render_assessment,
)
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.generator_registry import assessment_framework
from Backend.Core.legacy_migration import LEGACY_PUBLISHER, output_directory
from Backend.Core.render_transaction import render_pdf_atomically

REPEAT_PRACTICE_POLICY = "repeat-practice-v1"


def validate_endpoint(url: str, *, allow_remote: bool):
    parsed = urlparse(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("Adresse Ollama invalide")
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        if not allow_remote:
            raise ValueError(
                "Un serveur Ollama distant nécessite votre accord explicite"
            )
        if parsed.scheme != "https":
            raise ValueError("Un serveur distant doit utiliser HTTPS")


def model_identity(url: str, name: str) -> str:
    if "cloud" in name.casefold():
        raise ValueError(
            "Le prototype français exige un modèle local, pas un modèle cloud"
        )
    with open_ollama_request(
        Request(f"{url.rstrip('/')}/api/tags"), timeout=15
    ) as response:
        content = response.read(4 * 1024 * 1024 + 1)
        if len(content) > 4 * 1024 * 1024:
            raise ValueError("La liste des modèles dépasse la taille autorisée")
        models = json.loads(content)["models"]
    candidates = {name, f"{name}:latest"}
    match = [
        model
        for model in models
        if model.get("name") in candidates or model.get("model") in candidates
    ]
    if len(match) != 1 or not match[0].get("digest"):
        raise ValueError(
            "Modèle local introuvable : installez-le dans les réglages Ollama"
        )
    return match[0]["digest"]


def validate_pdf(path: Path):
    with pymupdf.open(path) as pdf:
        if len(pdf) < 1 or pdf.xref_get_key(pdf.pdf_catalog(), "Lang")[1] != "fr-FR":
            raise ValueError("PDF français invalide")
        for page in pdf:
            for word in page.get_text("words"):
                if (
                    word[0] < 0
                    or word[1] < 0
                    or word[2] > page.rect.width
                    or word[3] > page.rect.height
                ):
                    raise ValueError("Texte hors page")
        text = " ".join(" ".join(page.get_text() for page in pdf).split())
        if (
            "18 points" not in text
            or "2 points" not in text
            or "non officiel" not in text
        ):
            raise ValueError("Crédits ou statut du document manquants")


# Compare extracted printed facts with the locked first-exercise contract.
def validate_contract_pdf(
    path: Path,
    contract: GraphTreeContract,
    *,
    correction: bool,
    exercise: NSIExercise | None = None,
) -> None:
    data = contract.to_dict()
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    graph_header = "Réseau pondéré des postes"
    tree_header = "Arbre des identifiants d'intervention — arbre"
    if text.count(graph_header) != 1 or text.count(tree_header) != 1:
        raise ValueError("Figure de graphe ou arbre absente du PDF")
    graph_segment = text.split(graph_header + "\n", 1)[1].split("\n" + tree_header, 1)[
        0
    ]
    printed_graph = graph_segment.splitlines()
    expected_graph = [str(edge[2]) for edge in data["graph"]["edges"]] + data["graph"][
        "nodes"
    ]
    if printed_graph != expected_graph:
        raise ValueError(
            "Poids ou sommets du graphe imprimé incompatibles avec le contrat"
        )
    tree_segment = text.split(tree_header + "\n", 1)[1].split("\n1a.", 1)[0]
    printed_tree = tree_segment.splitlines()
    expected_tree = list(data["tree"]["columns"]) + [
        str(value) if value is not None else "—"
        for row in data["tree"]["rows"]
        for value in row
    ]
    if printed_tree != expected_tree:
        raise ValueError("Table de l'arbre imprimé incompatible avec le contrat")
    flat = " ".join(text.split())
    if " ".join(graph_edge_manifest(data["graph"]).split()) not in flat:
        raise ValueError("Arêtes textuelles du graphe incompatibles avec le contrat")
    if (
        " ".join(data["debug_case"]["faulty_code"].split()) not in flat
        or " ".join(data["node_api"].split()) not in flat
        or not re.search(
            rf"racine est {data['tree']['root']}\b.*?clé à insérer est {data['tree']['insert_key']}\b",
            flat,
        )
    ):
        raise ValueError("Code ou données d'ABR imprimés incompatibles avec le contrat")
    for task_id in data["task_ids"]:
        answer = canonical_answer(task_id, data["expected"][task_id])
        if correction and answer not in flat:
            raise ValueError(f"Résultat corrigé {task_id} absent du PDF")
        if not correction and answer in flat:
            raise ValueError(f"Réponse {task_id} révélée dans le sujet")
    if exercise is not None:
        if (
            exercise.id != "1"
            or [item.id for item in exercise.questions] != data["task_ids"]
        ):
            raise ValueError("Exercice du PDF incompatible avec le contrat")
        for question in exercise.questions:
            prompt = " ".join(question.prompt.split())
            if flat.count(prompt) != 1:
                raise ValueError(
                    f"Consigne {question.id} absente ou dupliquée dans le PDF"
                )
            answer = " ".join(question.answer.split())
            if correction and answer not in flat:
                raise ValueError(f"Réponse {question.id} absente du corrigé")
            if not correction and answer in flat:
                raise ValueError(f"Réponse {question.id} révélée dans le sujet")
            for credit in question.marking:
                criterion = " ".join(credit.criterion.split())
                label = credit.points.replace(".", ",")
                unit = "point" if credit.points in {"0.5", "1", "1.0"} else "points"
                expected_credit = f"{label} {unit} {criterion}"
                if correction and expected_credit not in flat:
                    raise ValueError(f"Crédit {question.id} absent du corrigé")
                if not correction and criterion in flat:
                    raise ValueError(f"Barème {question.id} révélé dans le sujet")


# Check every printed V17 graph/tree fact, question and credit.
def validate_graph_tree_depth_contract_pdf(
    path: Path,
    contract: GraphTreeDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Graph/tree depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 1 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Graph/tree depth exercise credit differs from blueprint")
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(
                f"Graph/tree depth question {task_id} missing or duplicated"
            )
    graph_header = "Réseau pondéré des postes"
    tree_header = "Arbre des identifiants — arbre"
    if text.count(graph_header) != 1 or text.count(tree_header) != 1:
        raise ValueError("Graph/tree depth figure missing")
    graph_lines = (
        text.split(graph_header + "\n", 1)[1]
        .split("\n" + tree_header, 1)[0]
        .splitlines()
    )
    expected_graph = [str(edge[2]) for edge in data["graph"]["edges"]] + data["graph"][
        "nodes"
    ]
    if graph_lines != expected_graph:
        raise ValueError("Graph/tree depth figure weights or vertices differ")
    tree_lines = text.split(tree_header + "\n", 1)[1].split("\n1a.", 1)[0].splitlines()
    expected_tree = list(data["tree"]["columns"]) + [
        str(value) if value is not None else "—"
        for row in data["tree"]["rows"]
        for value in row
    ]
    if tree_lines != expected_tree:
        raise ValueError("Graph/tree depth table differs from locked facts")
    for source in (
        graph_edge_manifest(data["graph"]),
        data["debug_case"]["faulty_code"],
        data["node_api"],
        data["search_code"],
    ):
        if " ".join(source.split()) not in flat:
            raise ValueError("Graph/tree depth source or graph facts missing")
    if not re.search(
        rf"racine {data['tree']['root']}\b.*?clé à insérer est {data['tree']['insert_key']}\b",
        flat,
    ):
        raise ValueError("Graph/tree depth root or insertion key missing")
    if not correction and any(
        re.search(pattern, flat)
        for pattern in (
            r"\bif\s+cle\s*<\s*noeud\.valeur\s*:",
            r"\bif\s+voisin\s+not\s+in\s+visites\s*:",
        )
    ):
        raise ValueError("Correction de code révélée dans le sujet")
    for question in exercise.questions:
        prompt = " ".join(question.prompt.split())
        if flat.count(prompt) != 1:
            raise ValueError(
                f"Graph/tree depth prompt {question.id} missing or duplicated"
            )
        answer = " ".join(question.answer.split())
        if correction and answer not in flat:
            raise ValueError(f"Graph/tree depth answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Réponse {question.id} révélée dans le sujet")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            if correction and f"{label} {unit} {criterion}" not in flat:
                raise ValueError(f"Graph/tree depth credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(
                    f"Graph/tree depth rubric {question.id} revealed in paper"
                )


# Fail closed on V20 printed facts, staging, answers and exact credit.
def validate_graph_resilience_pdf(
    path: Path,
    contract: GraphResilienceContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Graph resilience exercise differs from locked contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 1 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Graph resilience exercise credit differs from blueprint")
    positions = {}
    for task_id in data["task_ids"]:
        matches = [
            index
            for index, line in enumerate(lines)
            if re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Graph resilience question {task_id} missing or duplicated"
            )
        positions[task_id] = matches[0]
    graph_header = "Réseau pondéré des postes"
    tree_header = "Arbre des identifiants — arbre"
    if lines.count(graph_header) != 1 or lines.count(tree_header) != 1:
        raise ValueError("Graph resilience materials missing or duplicated")
    graph_at, tree_at = lines.index(graph_header), lines.index(tree_header)
    if not (graph_at < positions["1a"] < positions["1g"] < tree_at < positions["1h"]):
        raise ValueError("Graph resilience material is not staged by its questions")
    graph_lines = lines[graph_at + 1 : positions["1a"]]
    expected_graph = [str(edge[2]) for edge in data["graph"]["edges"]] + data["graph"][
        "nodes"
    ]
    if graph_lines != expected_graph:
        raise ValueError("Graph resilience figure differs from locked facts")
    tree_lines = lines[tree_at + 1 : positions["1h"]]
    expected_tree = list(data["tree"]["columns"]) + [
        str(value) if value is not None else "—"
        for row in data["tree"]["rows"]
        for value in row
    ]
    if tree_lines != expected_tree:
        raise ValueError("Graph resilience tree table differs from locked facts")
    exercise_at = lines.index(heading)
    before_1a = " ".join(lines[exercise_at : positions["1a"]])
    after_1j = next(
        (
            index
            for index in range(positions["1j"] + 1, len(lines))
            if lines[index].startswith("Exercice 2 (")
        ),
        len(lines),
    )
    in_1j = " ".join(lines[positions["1j"] : after_1j])
    for source, staged_text in (
        (graph_edge_manifest(data["graph"]), before_1a),
        (data["debug_case"]["faulty_code"], before_1a),
        (data["search_code"], in_1j),
    ):
        normalised = " ".join(source.split())
        if staged_text.count(normalised) != 1 or flat.count(normalised) != 1:
            raise ValueError("Graph resilience source or working facts outside stage")
    if not correction and any(
        re.search(pattern, flat)
        for pattern in (
            r"\bif\s+cle\s*<\s*noeud\.valeur\s*:",
            r"\bif\s+voisin\s+not\s+in\s+visites\s*:",
        )
    ):
        raise ValueError("Graph resilience corrected code revealed in paper")
    for question_index, question in enumerate(exercise.questions):
        prompt_text = (
            question.prompt.partition("\n\n```")[0]
            if question.id == "1j"
            else question.prompt
        )
        prompt = " ".join(prompt_text.split())
        if flat.count(prompt) != 1:
            raise ValueError(f"Graph resilience prompt {question.id} missing")
        answer = " ".join(question.answer.split())
        next_position = (
            positions[exercise.questions[question_index + 1].id]
            if question_index + 1 < len(exercise.questions)
            else next(
                (
                    index
                    for index in range(positions[question.id] + 1, len(lines))
                    if lines[index].startswith("Exercice 2 (")
                ),
                len(lines),
            )
        )
        section = " ".join(lines[positions[question.id] : next_position])
        if correction and answer not in section:
            raise ValueError(f"Graph resilience answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Graph resilience answer {question.id} leaked")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            if correction and f"{label} {unit} {criterion}" not in section:
                raise ValueError(f"Graph resilience credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Graph resilience rubric {question.id} leaked")


# Bind every V22 printed stage and credit to its immutable route facts.
def validate_graph_route_trace_pdf(
    path: Path,
    contract: GraphRouteTraceContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Route trace exercise differs from locked contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    flat = " ".join(" ".join(lines).split())
    heading = f"Exercice 1 ({exercise.target_points.replace('.', ',')} points)"
    if lines.count(heading) != 1:
        raise ValueError("Route trace exercise heading or credit missing")
    positions = {}
    for task_id in data["task_ids"]:
        matches = [
            index
            for index, line in enumerate(lines)
            if re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError(f"Route trace question {task_id} missing or repeated")
        positions[task_id] = matches[0]
    if list(positions.values()) != sorted(positions.values()):
        raise ValueError("Route trace questions are out of order")
    titles = (
        "Réseau pondéré des postes",
        "Trace de Dijkstra avant fermeture — trace_initial",
        "Trace de Dijkstra après fermeture de "
        + "–".join(data["closed_edge"])
        + " — trace_fermeture",
        "Arbre des identifiants — arbre",
    )
    if any(lines.count(title) != 1 for title in titles):
        raise ValueError("Route trace working material missing or duplicated")
    graph_at, before_at, after_at, tree_at = (lines.index(title) for title in titles)
    if not (
        graph_at < positions["1a"]
        and positions["1b"] < before_at < positions["1c"]
        and positions["1f"] < after_at < positions["1g"]
        and positions["1g"] < tree_at < positions["1h"]
    ):
        raise ValueError("Route trace working material is outside its phase")
    graph_lines = lines[graph_at + 1 : positions["1a"]]
    expected_graph = [str(edge[2]) for edge in data["graph"]["edges"]] + data["graph"][
        "nodes"
    ]
    if graph_lines != expected_graph:
        raise ValueError("Route trace figure differs from locked graph")
    for start, end in ((before_at, positions["1c"]), (after_at, positions["1g"])):
        table = lines[start + 1 : end]
        expected_table = [
            "Fixation / donnée",
            *"ABCDEF",
            "1re distance (fixé : ___)",
            *(["_____"] * 6),
            "1re préd.",
            *(["_____"] * 6),
            "2e distance (fixé : ___)",
            *(["_____"] * 6),
            "2e préd.",
            *(["_____"] * 6),
        ]
        if " ".join(" ".join(table).split()) != " ".join(expected_table):
            raise ValueError("Route trace working table is altered or filled")
    expected_tree = list(data["tree"]["columns"]) + [
        str(value) if value is not None else "—"
        for row in data["tree"]["rows"]
        for value in row
    ]
    if lines[tree_at + 1 : positions["1h"]] != expected_tree:
        raise ValueError("Route trace tree differs from locked facts")
    exercise_at = lines.index(heading)
    before_1a = " ".join(lines[exercise_at : positions["1a"]])
    after_1j = next(
        (
            index
            for index in range(positions["1j"] + 1, len(lines))
            if lines[index].startswith("Exercice 2 (")
        ),
        len(lines),
    )
    for source, section in (
        (graph_edge_manifest(data["graph"]), before_1a),
        (
            data["debug_case"]["faulty_code"],
            " ".join(lines[positions["1e"] : positions["1f"]]),
        ),
        (data["search_code"], " ".join(lines[positions["1j"] : after_1j])),
    ):
        normalised = " ".join(source.split())
        if section.count(normalised) != 1 or flat.count(normalised) != 1:
            raise ValueError("Route trace source code or graph facts outside phase")
    if not correction and "if voisin not in visites:" in flat:
        raise ValueError("Route trace corrected code revealed to candidate")
    for index, question in enumerate(exercise.questions):
        prompt = " ".join(question.prompt.partition("\n\n```")[0].split())
        if flat.count(prompt) != 1:
            raise ValueError(f"Route trace prompt {question.id} missing")
        next_position = (
            positions[exercise.questions[index + 1].id]
            if index + 1 < len(exercise.questions)
            else after_1j
        )
        section = " ".join(lines[positions[question.id] : next_position])
        answer = " ".join(question.answer.split())
        if correction and answer not in section:
            raise ValueError(f"Route trace answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Route trace answer {question.id} leaked")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            if correction and f"{label} {unit} {criterion}" not in section:
                raise ValueError(f"Route trace credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Route trace rubric {question.id} leaked")


# Bind V30's public catalogue/helper and all answer/credit phases.
def _validate_route_selection_pdf(
    path, data, exercise, *, correction, coherent_material_flow
):
    from Backend.Core.france.route_selection_authoring import (
        HELPER_CODE,
        route_material,
    )
    from Backend.Core.france.verification import verify_contract

    for question in exercise.questions[5:7]:
        if (
            question.verification.get("kind")
            not in {"route_selection_contract", "route_family_contract"}
            or question.verification.get("task_id") != question.id
            or question.verification.get("contract") != data
            or not verify_contract(question.verification)["passed"]
        ):
            raise ValueError("Route selection evidence differs from canonical facts")
    if not verify_contract(exercise.questions[-1].verification)["passed"]:
        raise ValueError("Tree construction evidence differs from canonical facts")
    with pymupdf.open(path) as pdf:
        pages = [
            [
                line.strip()
                for line in page.get_text().splitlines()
                if line.strip()
                and not line.startswith(
                    ("Keldin —", f"{LEGACY_PUBLISHER} —", "Page : ")
                )
            ]
            for page in pdf
        ]
    lines = [line for page in pages for line in page]
    page_by_line = [i for i, page in enumerate(pages) for _ in page]

    def normal(text):
        return " ".join(re.sub(r"```(?:sql|python)?", " ", text).split())

    flat = normal(" ".join(lines))
    positions = {}
    for question in exercise.questions:
        matches = [
            i
            for i, line in enumerate(lines)
            if re.match(rf"^{re.escape(question.id)}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError("Route selection question missing or repeated")
        positions[question.id] = matches[0]
    if list(positions.values()) != sorted(positions.values()):
        raise ValueError("Route selection questions out of order")
    expected_ids = {"reseau", "trace_initial", "catalogue_trajets", "arbre"}
    if {material.id for material in exercise.materials} != expected_ids:
        raise ValueError("Route selection material set differs")
    catalogue = route_material(data)
    table = next(m for m in exercise.materials if m.id == "catalogue_trajets")
    if table.model_dump(mode="json") != catalogue:
        raise ValueError("Route catalogue differs from canonical facts")
    titles = [
        "Réseau pondéré des postes",
        "Trace de Dijkstra avant fermeture",
        catalogue["title"],
        "Arbre des identifiants",
    ]
    for title, task_id in zip(titles, ("1a", "1c", "1f", "1h"), strict=True):
        if lines.count(title) != 1:
            raise ValueError("Route selection material missing or duplicated")
        start, end = lines.index(title), positions[task_id]
        previous = {"1a": None, "1c": "1b", "1f": "1e", "1h": "1g"}[task_id]
        if not start < end or (previous and start <= positions[previous]):
            raise ValueError("Route selection material outside question phase")
        if (
            coherent_material_flow
            and previous
            and page_by_line[start] != page_by_line[end]
        ):
            raise ValueError("Route selection material separated from question")
        if task_id == "1a":
            expected = [str(edge[2]) for edge in data["graph"]["edges"]] + data[
                "graph"
            ]["nodes"]
        elif task_id == "1c":
            expected = [
                "Fixation / donnée",
                *"ABCDEF",
                "1re distance (fixé : ___)",
                *(["_____"] * 6),
                "1re préd.",
                *(["_____"] * 6),
                "2e distance (fixé : ___)",
                *(["_____"] * 6),
                "2e préd.",
                *(["_____"] * 6),
            ]
        elif task_id == "1f":
            expected = catalogue["columns"] + [
                cell for row in catalogue["rows"] for cell in row
            ]
        else:
            expected = data["tree"]["columns"] + [
                str(value) if value is not None else "—"
                for row in data["tree"]["rows"]
                for value in row
            ]
        if normal(" ".join(lines[start + 1 : end])) != normal(" ".join(expected)):
            raise ValueError("Route selection printed material altered or filled")
    heading = f"Exercice 1 ({exercise.target_points.replace('.', ',')} points)"
    if (
        lines.count(heading) != 1
        or flat.count(normal(graph_edge_manifest(data["graph"]))) != 1
    ):
        raise ValueError("Route selection heading or graph source missing")
    if normal(graph_edge_manifest(data["graph"])) not in normal(
        " ".join(lines[lines.index(heading) : positions["1a"]])
    ):
        raise ValueError("Route selection graph source outside its phase")
    if normal(data["debug_case"]["faulty_code"]) not in normal(
        " ".join(lines[positions["1e"] : positions["1f"]])
    ):
        raise ValueError("Route selection BFS source missing")
    if flat.count(normal(HELPER_CODE)) != 1:
        raise ValueError("Route selection helper missing or repeated")
    end_exercise = next(
        (
            i
            for i in range(positions["1j"] + 1, len(lines))
            if lines[i].startswith("Exercice 2 (")
        ),
        len(lines),
    )
    for index, question in enumerate(exercise.questions):
        end = (
            positions[exercise.questions[index + 1].id]
            if index + 1 < len(exercise.questions)
            else end_exercise
        )
        section = normal(" ".join(lines[positions[question.id] : end]))
        if section.count(normal(question.prompt)) != 1:
            raise ValueError(f"Route selection prompt {question.id} missing or altered")
        if correction and normal(question.answer) not in section:
            raise ValueError(f"Route selection answer {question.id} missing")
        if not correction and normal(question.answer) in flat:
            raise ValueError("Route selection answer leaked")
        for credit in question.marking:
            criterion = normal(credit.criterion)
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            label = credit.points.replace(".", ",")
            if correction and f"{label} {unit} {criterion}" not in section:
                raise ValueError(f"Route selection credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError("Route selection credit leaked")
    if not correction and any(
        token in flat
        for token in (
            "def meilleur_trajet",
            "def trajets_admissibles",
            "def premiere_coupure",
            "def compter_intervalle",
            "if voisin not in visites:",
        )
    ):
        raise ValueError("Route selection solution code leaked")


# Bind V25's two ordered outages, working surfaces, answers and credit.
def validate_graph_two_outage_pdf(
    path: Path,
    contract: GraphTwoOutageContract,
    *,
    correction: bool,
    exercise: NSIExercise,
    human_readable_titles: bool = False,
    coherent_material_flow: bool = False,
) -> None:
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Two-outage exercise differs from locked contract")
    if exercise.questions[5].verification.get("kind") in {
        "route_selection_contract",
        "route_family_contract",
    }:
        return _validate_route_selection_pdf(
            path,
            data,
            exercise,
            correction=correction,
            coherent_material_flow=coherent_material_flow,
        )
    tree_construction = (
        exercise.questions[-1].verification.get("kind") == "tree_construction_contract"
    )
    if tree_construction:
        from Backend.Core.france.verification import verify_contract

        if not verify_contract(exercise.questions[-1].verification)["passed"]:
            raise ValueError("Tree construction evidence differs from canonical facts")
    with pymupdf.open(path) as pdf:
        page_lines = [
            [
                line.strip()
                for line in page.get_text().splitlines()
                if line.strip()
                and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
                and not line.startswith("Page : ")
            ]
            for page in pdf
        ]
    lines = [line for page in page_lines for line in page]
    page_by_line = [index for index, page in enumerate(page_lines) for _line in page]
    flat = " ".join(" ".join(lines).split())
    heading = f"Exercice 1 ({exercise.target_points.replace('.', ',')} points)"
    if lines.count(heading) != 1:
        raise ValueError("Two-outage heading or credit missing")
    positions = {}
    for task_id in data["task_ids"]:
        matches = [
            index
            for index, line in enumerate(lines)
            if re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError(f"Two-outage question {task_id} missing or repeated")
        positions[task_id] = matches[0]
    if list(positions.values()) != sorted(positions.values()):
        raise ValueError("Two-outage questions out of order")
    titles = (
        "Réseau pondéré des postes",
        "Trace de Dijkstra avant fermeture — trace_initial",
        "Trace de Dijkstra après fermeture de "
        + "–".join(data["closed_edge"])
        + " — trace_fermeture",
        "Trajet après fermeture de "
        + "–".join(data["closed_edge_second"])
        + " — route_double_fermeture",
        "Arbre des identifiants — arbre",
    )
    if human_readable_titles:
        titles = tuple(title.split(" — ", 1)[0] for title in titles)
    if coherent_material_flow:
        for title, task_id in zip(titles[1:], ("1c", "1f", "1g", "1h"), strict=True):
            if page_by_line[lines.index(title)] != page_by_line[positions[task_id]]:
                raise ValueError(
                    f"Two-outage material separated from question {task_id}"
                )
    if any(lines.count(title) != 1 for title in titles):
        raise ValueError("Two-outage working material missing or duplicated")
    graph_at, before_at, first_at, second_at, tree_at = (
        lines.index(title) for title in titles
    )
    if not (
        graph_at < positions["1a"]
        and positions["1b"] < before_at < positions["1c"]
        and positions["1e"] < first_at < positions["1f"]
        and positions["1f"] < second_at < positions["1g"]
        and positions["1g"] < tree_at < positions["1h"]
    ):
        raise ValueError("Two-outage working material outside its phase")
    if not correction and (
        page_by_line[first_at] != page_by_line[positions["1f"]]
        or page_by_line[second_at] != page_by_line[positions["1g"]]
    ):
        raise ValueError("Two-outage working surface orphaned from question")
    if (
        lines[graph_at + 1 : positions["1a"]]
        != [str(edge[2]) for edge in data["graph"]["edges"]] + data["graph"]["nodes"]
    ):
        raise ValueError("Two-outage graph differs from locked facts")
    expected_trace = [
        "Fixation / donnée",
        *"ABCDEF",
        "1re distance (fixé : ___)",
        *(["_____"] * 6),
        "1re préd.",
        *(["_____"] * 6),
        "2e distance (fixé : ___)",
        *(["_____"] * 6),
        "2e préd.",
        *(["_____"] * 6),
    ]
    for start, end in ((before_at, positions["1c"]), (first_at, positions["1f"])):
        if " ".join(" ".join(lines[start + 1 : end]).split()) != " ".join(
            expected_trace
        ):
            raise ValueError("Two-outage Dijkstra surface altered or filled")
    if " ".join(" ".join(lines[second_at + 1 : positions["1g"]]).split()) != " ".join(
        ["Trajet restant", "Somme des poids", "Coût", "Comparaison", *(["_____"] * 4)]
    ):
        raise ValueError("Two-outage route surface altered or filled")
    expected_tree = list(data["tree"]["columns"]) + [
        str(value) if value is not None else "—"
        for row in data["tree"]["rows"]
        for value in row
    ]
    if lines[tree_at + 1 : positions["1h"]] != expected_tree:
        raise ValueError("Two-outage tree differs from locked facts")
    after_1j = next(
        (
            index
            for index in range(positions["1j"] + 1, len(lines))
            if lines[index].startswith("Exercice 2 (")
        ),
        len(lines),
    )
    for source, section in (
        (
            graph_edge_manifest(data["graph"]),
            " ".join(lines[lines.index(heading) : positions["1a"]]),
        ),
        (
            data["debug_case"]["faulty_code"],
            " ".join(lines[positions["1e"] : positions["1f"]]),
        ),
        *(
            []
            if tree_construction
            else [(data["search_code"], " ".join(lines[positions["1j"] : after_1j]))]
        ),
    ):
        normalised = " ".join(source.split())
        if section.count(normalised) != 1 or flat.count(normalised) != 1:
            raise ValueError("Two-outage source code or graph facts outside phase")
    if not correction and "if voisin not in visites:" in flat:
        raise ValueError("Two-outage corrected code revealed to candidate")
    if tree_construction and not correction and "def compter_intervalle" in flat:
        raise ValueError("Tree construction solution revealed to candidate")
    if not correction:
        candidate_answers = flat
        for question in exercise.questions:
            prompt = " ".join(question.prompt.partition("\n\n```")[0].split())
            candidate_answers = candidate_answers.replace(prompt, "", 1)
        second_result = data["expected"]["1g"]
        second_cost = second_result["cost_after"]
        route_pattern = (
            r"\b"
            + r"\s*(?:→|->|[-–—>,])\s*".join(
                re.escape(node) for node in second_result["route_after"]
            )
            + r"\b"
        )
        cost_pattern = (
            r"\b(?:co[uû]t|poids|distance)\s*"
            r"(?:(?:total(?:e)?|minimal(?:e)?|gagnant|du trajet(?: restant)?|de la route)\s*)?"
            r"(?:(?:est|vaut)\s*)?(?:de\s*)?(?:[:=]\s*)?"
            + re.escape(str(second_cost))
            + r"\b"
        )
        if re.search(route_pattern, candidate_answers, re.IGNORECASE) or re.search(
            cost_pattern, candidate_answers, re.IGNORECASE
        ):
            raise ValueError("Two-outage route or cost revealed to candidate")
    first = "–".join(data["closed_edge"])
    second = "–".join(data["closed_edge_second"])
    if (
        flat.count(f"La liaison {first} est fermée.") != 1
        or flat.count(f"la liaison {second} est à son tour fermée.") != 1
    ):
        raise ValueError("Two-outage closure sequence differs from locked facts")
    for index, question in enumerate(exercise.questions):
        prompt = " ".join(question.prompt.partition("\n\n```")[0].split())
        if flat.count(prompt) != 1:
            raise ValueError(f"Two-outage prompt {question.id} missing")
        next_position = (
            positions[exercise.questions[index + 1].id]
            if index + 1 < len(exercise.questions)
            else after_1j
        )
        section = " ".join(lines[positions[question.id] : next_position])
        answer = " ".join(re.sub(r"```(?:sql|python)?", " ", question.answer).split())
        if correction and answer not in section:
            raise ValueError(f"Two-outage answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Two-outage answer {question.id} leaked")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            if correction and f"{label} {unit} {criterion}" not in section:
                raise ValueError(f"Two-outage credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Two-outage rubric {question.id} leaked")


# Check that both PDF roles print the exact locked database exercise.
def validate_database_contract_pdf(
    path: Path,
    contract: DatabaseContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if (
        exercise.id != "2"
        or [question.id for question in exercise.questions] != data["task_ids"]
    ):
        raise ValueError("Database exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 2 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Database exercise credit differs from locked blueprint")
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(f"Database question label {task_id} missing or duplicated")
    for key_fact in (
        "id_agent, id_cat et id_incident sont des clés primaires",
        "id_agent référence agent.id_agent",
        "id_cat référence categorie.id_cat",
    ):
        if key_fact not in flat:
            raise ValueError("Database key explanation differs from locked contract")
    materials = database_materials(contract)
    headers = [f"{item['title']} — {item['id']}" for item in materials]
    for index, material in enumerate(materials):
        header = headers[index]
        following = headers[index + 1] if index < 2 else "2a."
        if text.count(header) != 1 or following not in text:
            raise ValueError("Database table heading missing from PDF")
        printed = (
            text.split(header + "\n", 1)[1].split("\n" + following, 1)[0].splitlines()
        )
        expected = list(material["columns"]) + [
            cell for row in material["rows"] for cell in row
        ]
        if printed != expected:
            raise ValueError("Database table rows differ from locked contract")
    if (
        " ".join(data["faulty_sql"].split()) not in flat
        or " ".join(data["faulty_python"].split()) not in flat
    ):
        raise ValueError("Database SQL or Python code missing from PDF")
    for question in exercise.questions:
        prompt = " ".join(question.prompt.split())
        if flat.count(prompt) != 1:
            raise ValueError(f"Database prompt {question.id} missing or duplicated")
        answer = " ".join(re.sub(r"```(?:sql|python)?", " ", question.answer).split())
        if correction and answer not in flat:
            raise ValueError(f"Database answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Database answer {question.id} leaked into paper")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if credit.points in {"0.5", "1", "1.0"} else "points"
            if correction and f"{label} {unit} {criterion}" not in flat:
                raise ValueError(f"Database credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Database rubric {question.id} leaked into paper")


# Fail closed on missing V2 facts, ten tasks, answers or rubric credits.
def validate_database_depth_contract_pdf(
    path: Path,
    contract: DatabaseDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "2" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Database depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 2 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Database depth exercise credit differs from blueprint")
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(
                f"Database depth question label {task_id} missing or duplicated"
            )
    materials = database_materials(contract)
    headers = [f"{item['title']} — {item['id']}" for item in materials]
    for index, material in enumerate(materials):
        header = headers[index]
        following = headers[index + 1] if index < 2 else "2a."
        if text.count(header) != 1 or following not in text:
            raise ValueError("Database depth table heading missing")
        printed = (
            text.split(header + "\n", 1)[1].split("\n" + following, 1)[0].splitlines()
        )
        expected = list(material["columns"]) + [
            cell for row in material["rows"] for cell in row
        ]
        if printed != expected:
            raise ValueError("Database depth table rows differ from locked facts")
    for source in (data["faulty_sql"], data["faulty_python"]):
        if " ".join(source.split()) not in flat:
            raise ValueError("Database depth SQL or Python source missing")
    for question in exercise.questions:
        prompt = " ".join(question.prompt.split())
        if flat.count(prompt) != 1:
            raise ValueError(
                f"Database depth prompt {question.id} missing or duplicated"
            )
        answer = " ".join(re.sub(r"```(?:sql|python)?", " ", question.answer).split())
        if correction and answer not in flat:
            raise ValueError(f"Database depth answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Database depth answer {question.id} leaked into paper")
        for credit in question.marking:
            criterion = printable_database_criterion(credit.criterion)
            label = credit.points.replace(".", ",")
            unit = "point" if Decimal(credit.points) <= 1 else "points"
            if correction and f"{label} {unit} {criterion}" not in flat:
                raise ValueError(f"Database depth credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(
                    f"Database depth rubric {question.id} leaked into paper"
                )


# Require V2 facts and each V19 reasoning phase in its intended role.
def validate_database_reasoning_pdf(
    path: Path,
    contract: DatabaseDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    validate_database_depth_contract_pdf(
        path, contract, correction=correction, exercise=exercise
    )
    with pymupdf.open(path) as pdf:
        raw_pages = [page.get_text() for page in pdf]
    pages = [" ".join(page.split()) for page in raw_pages]
    flat = " ".join(pages)
    for phase, task_id in (("Partie A", "2a"), ("Partie B", "2e"), ("Partie C", "2g")):
        question = next(q for q in exercise.questions if q.id == task_id)
        if phase not in question.prompt or flat.count(phase) != 1:
            raise ValueError(f"Database reasoning phase {phase} missing or duplicated")
    if not correction:
        update_sql = " ".join(contract.to_dict()["update_sql"].split())
        if update_sql in flat:
            raise ValueError("Database reasoning update answer leaked")
        for question in exercise.questions:
            # The old whole-answer check cannot see a leaked result or trace step.
            # These finite V19 answer-value patterns do not occur in the source
            # tables or prompts, so each is a safe candidate-facing rejection.
            answer = " ".join(question.answer.split())
            fragments = re.findall(
                r"\b(?:10[1-9]\s*:\s*[A-Za-zÀ-ÿ]+(?:\s*\(id_cat\s*=\s*\d+\))?"
                r"|[A-Za-zÀ-ÿ]+\s*:\s*\d+\b"
                r"|catégorie\s+\d+\s*:\s*\d+\b"
                r"|(?:Avant|après)\s*:\s*\d+\s+incidents clos"
                r"|incident\.id_cat\s*=\s*categorie\.id_cat"
                r"|assert\s+nombre_clos\(incidents\)\s*==\s*\d+"
                r"|incident\['statut'\]\s*==\s*'clos'"
                r"|renvoie\s+\d+\b)",
                answer,
                flags=re.IGNORECASE,
            )
            fragments.extend(re.findall(r"\b\d+\s+incidents clos\b", answer))
            if any(" ".join(fragment.split()) in flat for fragment in fragments):
                raise ValueError(f"Database reasoning answer {question.id} leaked")
    if correction:
        raw = "\n".join(raw_pages)
        matches = [
            re.search(rf"(?m)^{re.escape(question.id)}\.(?:\s|$)", raw)
            for question in exercise.questions
        ]
        if any(match is None for match in matches):
            raise ValueError("Database reasoning question section missing")
        for index, question in enumerate(exercise.questions):
            start = matches[index].start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
            section = " ".join(raw[start:end].split())
            answer = " ".join(
                re.sub(r"```(?:sql|python)?", " ", question.answer).split()
            )
            rubric = f"Barème indicatif — question {question.id}"
            if (
                answer not in section
                or section.count(rubric) != 1
                or not any(answer in page and rubric in page for page in pages)
            ):
                raise ValueError(
                    f"Database reasoning answer/rubric for {question.id} separated"
                )
            for credit in question.marking:
                label = credit.points.replace(".", ",")
                unit = "point" if Decimal(credit.points) <= 1 else "points"
                criterion = printable_database_criterion(credit.criterion)
                if f"{label} {unit} {criterion}" not in section:
                    raise ValueError(
                        f"Database reasoning credit {question.id} misplaced"
                    )


# Bind V24 printed facts, staged working surfaces and exact correction credit.
def validate_database_reconciliation_pdf(
    path: Path,
    contract: DatabaseReconciliationContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "2" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Incident-reconciliation exercise differs from contract")
    if [item.model_dump(mode="json") for item in exercise.materials] != (
        database_materials(contract) + database_reconciliation_working_materials()
    ):
        raise ValueError("Incident-reconciliation material differs from contract")
    with pymupdf.open(path) as pdf:
        pages = [page.get_text() for page in pdf]
    lines = [
        line.strip()
        for page in pages
        for line in page.splitlines()
        if line.strip()
        and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
        and not line.startswith("Page : ")
    ]
    flat = " ".join(lines)
    heading = f"Exercice 2 ({exercise.target_points.replace('.', ',')} points)"
    if lines.count(heading) != 1:
        raise ValueError("Incident-reconciliation heading or credit mismatch")
    positions = {}
    for task_id in data["task_ids"]:
        matches = [
            i
            for i, line in enumerate(lines)
            if re.match(rf"^{task_id}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError(f"Incident-reconciliation question {task_id} missing")
        positions[task_id] = matches[0]
    if list(positions.values()) != sorted(positions.values()):
        raise ValueError("Incident-reconciliation questions out of order")
    phases = {
        "recon_jointure": ("2b", "2c"),
        "recon_effectifs": ("2e", "2f"),
        "recon_etats": ("2h", "2i"),
    }
    for material in exercise.materials:
        matches = [i for i, line in enumerate(lines) if line.startswith(material.title)]
        if len(matches) != 1:
            raise ValueError(f"Incident-reconciliation material {material.id} missing")
        at = matches[0]
        if material.id in phases:
            before, after = phases[material.id]
            if not positions[before] < at < positions[after]:
                raise ValueError(
                    f"Incident-reconciliation material {material.id} misplaced"
                )
        elif at > positions["2a"]:
            raise ValueError(f"Incident-reconciliation source {material.id} misplaced")
        expected = list(material.columns) + [
            cell for row in material.rows for cell in row
        ]
        expected_tokens = " ".join(expected).split()
        actual_tokens = " ".join(lines[at + 1 :]).split()[: len(expected_tokens)]
        if actual_tokens != expected_tokens:
            raise ValueError(f"Incident-reconciliation material {material.id} altered")
    if " ".join(data["faulty_sql"].split()) not in flat:
        raise ValueError("Incident-reconciliation faulty source missing")
    if not correction:
        for source in (
            data["correct_sql"],
            data["group_sql"],
            data["correct_python"],
            data["update_sql_1"],
            data["update_sql_2"],
        ):
            if " ".join(source.split()) in flat:
                raise ValueError("Incident-reconciliation answer leaked")
        if "Réponse attendue" in flat or "Barème indicatif — question 2" in flat:
            raise ValueError("Incident-reconciliation correction leaked")
    next_exercise = next(
        (i for i, line in enumerate(lines) if line.startswith("Exercice 3 (")),
        len(lines),
    )
    for index, question in enumerate(exercise.questions):
        expected_verification = data["expected"]
        if "construction_version" in question.verification:
            from Backend.Core.france.database_construction_authoring import (
                construction_expected,
            )

            if question.verification[
                "construction_version"
            ] != "v28" or question.id not in {"2h", "2l"}:
                raise ValueError("Incident-reconciliation construction version changed")
            expected_verification = construction_expected(data)
        if (
            question.verification.get("kind") != "database_reconciliation_contract"
            or question.verification.get("contract") != data
            or question.verification.get("task_id") != question.id
            or question.verification.get("expected") != expected_verification
        ):
            raise ValueError(
                f"Incident-reconciliation verification {question.id} changed"
            )
        end = (
            positions[exercise.questions[index + 1].id]
            if index + 1 < len(exercise.questions)
            else next_exercise
        )
        section = " ".join(lines[positions[question.id] : end])
        prompt = " ".join(re.sub(r"```(?:sql|python)?", " ", question.prompt).split())
        if prompt not in section:
            raise ValueError(f"Incident-reconciliation prompt {question.id} missing")
        answer = " ".join(re.sub(r"```(?:sql|python)?", " ", question.answer).split())
        if correction:
            rubric = f"Barème indicatif — question {question.id}"
            matching_pages = [
                " ".join(page.split()) for page in pages if rubric in page
            ]
            if (
                answer not in section
                or len(matching_pages) != 1
                or answer not in matching_pages[0]
                or "Réponse attendue" not in section
                or not section.index("Réponse attendue")
                < section.index(answer)
                < section.index(rubric)
            ):
                raise ValueError(
                    f"Incident-reconciliation answer/rubric {question.id} separated"
                )
            credit_text = section.split(rubric, 1)[1]
            if len(
                re.findall(r"(?<!\w)\d+(?:,\d+)?\s+points?(?!\w)", credit_text)
            ) != len(question.marking):
                raise ValueError(
                    f"Incident-reconciliation credit {question.id} altered"
                )
            previous_credit = -1
            for credit in question.marking:
                label = credit.points.replace(".", ",")
                unit = "point" if Decimal(credit.points) <= 1 else "points"
                expected_credit = (
                    f"{label} {unit} {printable_database_criterion(credit.criterion)}"
                )
                at = credit_text.find(expected_credit)
                if at <= previous_credit:
                    raise ValueError(
                        f"Incident-reconciliation credit {question.id} missing"
                    )
                previous_credit = at


# Bind V21 printed incident facts, staged working tables and exact credit.
def validate_database_audit_pdf(
    path: Path,
    contract: DatabaseAuditContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "2" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Incident-audit exercise differs from locked contract")
    with pymupdf.open(path) as pdf:
        raw_pages = [page.get_text() for page in pdf]
    raw = "\n".join(raw_pages)
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
        and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
        and not line.startswith("Page : ")
    ]
    flat = " ".join(raw.split())
    positions = {}
    for task_id in data["task_ids"]:
        matches = [
            i
            for i, line in enumerate(lines)
            if re.match(rf"^{task_id}\.(?:\s|$)", line)
        ]
        if len(matches) != 1:
            raise ValueError(f"Incident-audit question {task_id} missing or duplicated")
        positions[task_id] = matches[0]
    if list(positions.values()) != sorted(positions.values()):
        raise ValueError("Incident-audit questions out of order")
    expected_materials = (
        database_materials(contract) + database_audit_working_materials()
    )
    if [
        material.model_dump(mode="json") for material in exercise.materials
    ] != expected_materials:
        raise ValueError("Incident-audit material differs from contract")
    materials = {material.id: material for material in exercise.materials}
    stages = {
        "audit_jointure": ("2b", "2c"),
        "audit_etats": ("2f", "2g"),
        "audit_trace": ("2g", "2h"),
    }
    for material_id, material in materials.items():
        title = material.title
        matches = [i for i, line in enumerate(lines) if line.startswith(title)]
        if len(matches) != 1:
            raise ValueError(
                f"Incident-audit material {material_id} missing or duplicated"
            )
        at = matches[0]
        if material_id in stages:
            before, after = stages[material_id]
            if not positions[before] < at < positions[after]:
                raise ValueError(
                    f"Incident-audit material {material_id} at wrong phase"
                )
        elif at > positions["2a"]:
            raise ValueError("Incident-audit source tables not before first task")
        expected = list(material.columns) + [
            cell for row in material.rows for cell in row
        ]
        if lines[at + 1 : at + 1 + len(expected)] != expected:
            raise ValueError(
                f"Incident-audit material {material_id} differs from contract"
            )
    faulty_sql = " ".join(data["faulty_sql"].split())
    faulty_python = " ".join(data["faulty_python"].split())
    if flat.count(faulty_sql) != 1 or flat.count(faulty_python) != 1:
        raise ValueError("Incident-audit faulty source missing or duplicated")
    exercise_start = next(
        (index for index, line in enumerate(lines) if line.startswith("Exercice 2 (")),
        None,
    )
    if exercise_start is None:
        raise ValueError("Incident-audit exercise heading missing")
    before_2a = " ".join(lines[exercise_start : positions["2a"]])
    in_2h = " ".join(lines[positions["2h"] : positions["2i"]])
    if faulty_sql not in before_2a or faulty_python not in in_2h:
        raise ValueError("Incident-audit faulty source outside intended phase")
    if not correction:
        corrected_join = next(
            line.strip()
            for line in data["correct_sql"].splitlines()
            if "incident.id_cat = categorie.id_cat" in line
        )
        for source in (
            data["correct_sql"],
            data["group_sql"],
            data["correct_python"],
            data["update_sql_1"],
            data["update_sql_2"],
            corrected_join,
            "COUNT(incident.id_incident)",
            "if incident['statut'] == 'clos':",
        ):
            if " ".join(source.split()) in flat:
                raise ValueError("Incident-audit answer leaked into subject")
        if "Réponse attendue" in flat or "Barème indicatif — question 2" in flat:
            raise ValueError("Incident-audit answer or rubric role leaked")
        closed = ", ".join(str(value) for value in data["expected"]["closed_by_state"])
        faulty = ", ".join(
            str(value) for value in data["expected"]["faulty_python_by_state"]
        )
        for fragment in (
            f"S0, S1, S2 : {closed}",
            f"S0, S1, S2 donnent {faulty}",
            f"renvoie {closed}",
        ):
            if fragment in flat:
                raise ValueError("Incident-audit derived answer leaked")
        candidate_source = " ".join(
            [exercise.context, *(question.prompt for question in exercise.questions)]
        )
        candidate_source = " ".join(candidate_source.split())
        for question in exercise.questions:
            answer_prose = re.sub(
                r"```(?:sql|python)?[\s\S]*?```", "; ", question.answer
            )
            for clause in re.split(r";\s+|(?<=\.)\s+", answer_prose):
                fragment = " ".join(clause.split()).strip(" .")
                if (
                    len(fragment) >= 20
                    and fragment not in candidate_source
                    and fragment in flat
                ):
                    raise ValueError("Incident-audit answer clause leaked into subject")
        if any(
            printable_database_criterion(credit.criterion) in flat
            for question in exercise.questions
            for credit in question.marking
        ):
            raise ValueError("Incident-audit credit leaked into subject")
    for index, question in enumerate(exercise.questions):
        end = (
            positions[exercise.questions[index + 1].id]
            if index + 1 < len(exercise.questions)
            else len(lines)
        )
        section = " ".join(lines[positions[question.id] : end])
        prompt = " ".join(re.sub(r"```(?:sql|python)?", " ", question.prompt).split())
        if prompt not in section:
            raise ValueError(f"Incident-audit prompt {question.id} missing")
        answer = " ".join(re.sub(r"```(?:sql|python)?", " ", question.answer).split())
        if correction:
            rubric = f"Barème indicatif — question {question.id}"
            if answer not in section or rubric not in section:
                raise ValueError(
                    f"Incident-audit answer/rubric {question.id} misplaced"
                )
            rubric_pages = [
                " ".join(page.split()) for page in raw_pages if rubric in page
            ]
            if len(rubric_pages) != 1 or answer not in rubric_pages[0]:
                raise ValueError(
                    f"Incident-audit answer/rubric {question.id} separated"
                )
            if rubric_pages[0].index(answer) > rubric_pages[0].index(rubric):
                raise ValueError(
                    f"Incident-audit answer/rubric {question.id} out of order"
                )
            for credit in question.marking:
                label = credit.points.replace(".", ",")
                unit = "point" if Decimal(credit.points) <= 1 else "points"
                criterion = printable_database_criterion(credit.criterion)
                printed_credit = f"{label} {unit} {criterion}"
                if printed_credit not in section:
                    raise ValueError(f"Incident-audit credit {question.id} misplaced")
                if printed_credit not in rubric_pages[0] or rubric_pages[0].index(
                    printed_credit
                ) < rubric_pages[0].index(rubric):
                    raise ValueError(f"Incident-audit credit {question.id} separated")
        elif answer in flat:
            raise ValueError(f"Incident-audit answer {question.id} leaked")


# Require exact app-owned network evidence in each published PDF role.
def validate_network_contract_pdf(
    path: Path,
    contract: NetworkContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if (
        exercise.id != "3"
        or [question.id for question in exercise.questions] != data["task_ids"]
    ):
        raise ValueError("Network exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 3 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Network exercise credit differs from locked blueprint")
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(f"Network question label {task_id} missing or duplicated")
    for premise in (
        "aucun secret partagé initial",
        "clé publique de la station est authentifiée",
        "observateur passif",
        f"R1–Station passe de {data['links'][1][2]} à {data['change']['new_cost']}",
    ):
        if premise not in flat:
            raise ValueError("Network premise missing from PDF")
    materials = network_materials(contract)
    headers = [item["title"] for item in materials]
    for index, material in enumerate(materials):
        header = headers[index]
        following = headers[index + 1] if index == 0 else "3a."
        if text.count(header) != 1 or following not in text:
            raise ValueError("Network table heading missing from PDF")
        printed = (
            text.split(header + "\n", 1)[1].split("\n" + following, 1)[0].splitlines()
        )
        expected = list(material["columns"]) + [
            cell for row in material["rows"] for cell in row
        ]
        if printed != expected:
            raise ValueError("Network table rows differ from locked contract")
    for question in exercise.questions:
        prompt = " ".join(question.prompt.split())
        if flat.count(prompt) != 1:
            raise ValueError(f"Network prompt {question.id} missing or duplicated")
        answer = " ".join(question.answer.split())
        if correction and answer not in flat:
            raise ValueError(f"Network answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Network answer {question.id} leaked into paper")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            label = credit.points.replace(".", ",")
            unit = "point" if credit.points in {"0.5", "1", "1.0"} else "points"
            if correction and f"{label} {unit} {criterion}" not in flat:
                raise ValueError(f"Network credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Network rubric {question.id} leaked into paper")


# Fail closed if a v15 PDF omits locked facts or exposes an answer.
def validate_network_depth_contract_pdf(
    path: Path,
    contract: NetworkDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "3" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Network depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 3 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1:
        raise ValueError("Network depth exercise credit differs from blueprint")
    titles = (
        "Sept liaisons bidirectionnelles et coûts initiaux",
        "État simultané des processus",
    )
    if text.count(titles[0]) != 1:
        raise ValueError("Network depth case material missing")
    case_context = " ".join(
        text.split(heading + "\n", 1)[1].split("\n" + titles[0], 1)[0].split()
    )
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(f"Network depth question {task_id} missing or duplicated")
    for premise in (
        f"R1–R3 passe de {data['links'][2][2]} à {data['change']['new_cost']}",
        "les autres coûts restent inchangés",
        "P2, qui libère B",
        "A avant B",
        "Aucun secret n'est partagé au départ",
        "clé publique de la station est authentifiée",
        "clé de session est chiffrée pour elle",
        "capteur n'appose pas de signature",
        "observateur est passif",
    ):
        if premise not in case_context:
            raise ValueError("Network depth premise missing from PDF")
    materials = exercise.materials
    expected_rows = [
        [[left, right, str(cost)] for left, right, cost in data["links"]],
        [
            [
                name,
                data["processes"][name]["holds"],
                data["processes"][name]["waits_for"],
            ]
            for name in ("P1", "P2")
        ],
    ]
    columns = (
        ("Extrémité 1", "Extrémité 2", "Coût"),
        ("Processus", "Ressource détenue", "Ressource attendue"),
    )
    for index, (material, title, rows) in enumerate(
        zip(materials, titles, expected_rows, strict=True)
    ):
        following = titles[index + 1] if index == 0 else "3a."
        if (
            material.title != title
            or material.columns != columns[index]
            or [list(row) for row in material.rows] != rows
            or text.count(title) != 1
        ):
            raise ValueError("Network depth material differs from contract")
        printed = (
            text.split(title + "\n", 1)[1].split("\n" + following, 1)[0].splitlines()
        )
        expected = list(material.columns) + [cell for row in rows for cell in row]
        if printed != expected:
            raise ValueError("Network depth table rows differ from contract")
    for index, question in enumerate(exercise.questions):
        start = text.index("\n" + question.id + ".")
        end = (
            text.index("\n" + exercise.questions[index + 1].id + ".")
            if index + 1 < len(exercise.questions)
            else len(text)
        )
        question_text = " ".join(text[start:end].split())
        for label in ("Réponse attendue", "Barème indicatif"):
            if question_text.count(label) != int(correction):
                raise ValueError(f"Network depth role label {question.id} invalid")
        prompt = " ".join(question.prompt.split())
        answer = " ".join(question.answer.split())
        if question_text.count(prompt) != 1:
            raise ValueError(
                f"Network depth prompt {question.id} missing or duplicated"
            )
        if correction and answer not in question_text:
            raise ValueError(f"Network depth answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Network depth answer {question.id} leaked")
        if correction:
            for points in {credit.points for credit in question.marking}:
                label = points.replace(".", ",")
                unit = "point" if Decimal(points) <= 1 else "points"
                expected_count = sum(
                    credit.points == points for credit in question.marking
                )
                if question_text.count(f"{label} {unit}") != expected_count:
                    raise ValueError(f"Network depth credit {question.id} missing")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            if correction and question_text.count(criterion) != 1:
                raise ValueError(f"Network depth credit {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Network depth rubric {question.id} leaked")


# Reject V18 PDFs whose case facts or per-question roles do not print.
def validate_network_reasoning_contract_pdf(
    path: Path,
    contract: NetworkReasoningContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "3" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Network reasoning exercise differs from contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —"))
            and not line.startswith("Page : ")
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 3 ({exercise.target_points.replace('.', ',')} points)"
    titles = (
        "Sept liaisons et coûts initiaux",
        "Tableau de travail Dijkstra avant et après la hausse",
        "États simultanés et reprise à compléter",
        "Cartes de messages à remettre dans l'ordre",
        "Situations de sécurité à analyser",
    )
    if text.count(heading) != 1 or any(text.count(title) != 1 for title in titles):
        raise ValueError("Network reasoning heading or material missing")
    context = " ".join(
        text.split(heading + "\n", 1)[1].split("\n" + titles[0], 1)[0].split()
    )
    if " ".join(exercise.context.split()) not in context:
        raise ValueError("Network reasoning premise differs from exercise")
    if len(exercise.materials) != 5:
        raise ValueError("Network reasoning materials incomplete")
    for task_id in data["task_ids"]:
        if (
            sum(
                bool(re.match(rf"^{re.escape(task_id)}\.(?:\s|$)", line))
                for line in lines
            )
            != 1
        ):
            raise ValueError(
                f"Network reasoning question {task_id} missing or duplicated"
            )
    cards = data["security_messages"]
    expected_rows = (
        [[left, right, str(cost)] for left, right, cost in data["links"]],
        [
            [node, "à compléter", "à compléter"]
            for node in data["working_surfaces"]["route_nodes"]
        ],
        [
            [item["step"], item["P1"], item["P2"]]
            for item in data["process_schedule"][:2]
        ]
        + [
            [step, "à compléter", "à compléter"]
            for step in data["working_surfaces"]["process_steps"][2:]
        ],
        [
            ["M1", cards[2]["sender"], cards[2]["content"]],
            ["M2", cards[0]["sender"], cards[0]["content"]],
            ["M3", cards[1]["sender"], cards[1]["content"]],
        ],
        [
            [situation, "à compléter"]
            for situation in data["working_surfaces"]["threat_scenarios"]
        ],
    )
    columns = (
        ("Extrémité 1", "Extrémité 2", "Coût"),
        ("Sommet", "Avant : coût / prédécesseur", "Après : coût / prédécesseur"),
        ("Moment", "P1", "P2"),
        ("Carte", "Émetteur", "Contenu"),
        ("Situation", "Conclusion et justification"),
    )
    following_titles = (
        titles[1],
        "3a.",
        "3e.",
        titles[4],
        "3i.",
    )
    for index, material in enumerate(exercise.materials):
        title = titles[index]
        following = following_titles[index]
        rows = expected_rows[index]
        if (
            material.title != title
            or material.columns != columns[index]
            or [list(row) for row in material.rows] != rows
        ):
            raise ValueError("Network reasoning material differs from contract")
        printed = text.split(title + "\n", 1)[1].split("\n" + following, 1)[0]
        expected = " ".join(
            [*material.columns, *(cell for row in rows for cell in row)]
        )
        if " ".join(printed.split()) != expected:
            raise ValueError("Network reasoning printed table differs from contract")
    for index, question in enumerate(exercise.questions):
        start = text.index("\n" + question.id + ".")
        end = (
            text.index("\n" + exercise.questions[index + 1].id + ".")
            if index + 1 < len(exercise.questions)
            else len(text)
        )
        question_text = " ".join(text[start:end].split())
        for label in ("Réponse attendue", "Barème indicatif"):
            if question_text.count(label) != int(correction):
                raise ValueError(f"Network reasoning role label {question.id} invalid")
        if question_text.count(" ".join(question.prompt.split())) != 1:
            raise ValueError(f"Network reasoning prompt {question.id} missing")
        answer = " ".join(question.answer.split())
        if correction and answer not in question_text:
            raise ValueError(f"Network reasoning answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Network reasoning answer {question.id} leaked")
        if correction:
            for credit_points in {credit.points for credit in question.marking}:
                unit = "point" if Decimal(credit_points) <= 1 else "points"
                label = f"{credit_points.replace('.', ',')} {unit}"
                expected_count = sum(
                    credit.points == credit_points for credit in question.marking
                )
                if question_text.count(label) != expected_count:
                    raise ValueError(f"Network reasoning credit {question.id} missing")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            if correction and question_text.count(criterion) != 1:
                raise ValueError(f"Network reasoning rubric {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Network reasoning rubric {question.id} leaked")


# Bind V23's three displayed incident stages and answer/credit roles.
def validate_network_incident_pdf(
    path: Path,
    contract: NetworkIncidentContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    data = contract.to_dict()
    if exercise.id != "3" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Network incident exercise differs from contract")
    from Backend.Core.france.pipeline import _tasks_for_seed_v23

    validate_network_incident_exercise(
        contract, exercise, _tasks_for_seed_v23(data["seed"])[2]["question_blueprint"]
    )
    titles = (
        "Liaisons et coûts initiaux",
        "Routes : tableau de travail avant et après la hausse",
        "Échéance du paquet M-27",
        "Ressources et reprise à compléter",
        "Cartes après la reprise, à ordonner",
        "Situations à analyser",
    )
    if len(exercise.materials) != len(titles):
        raise ValueError("Network incident materials incomplete")
    expected_rows = (
        [[left, right, str(cost)] for left, right, cost in data["links"]],
        [
            [node, "à compléter", "à compléter"]
            for node in data["working_surfaces"]["route_nodes"]
        ],
        [["t=0", f"t={data['packet']['deadline']} min", "à calculer / à calculer"]],
        [
            [
                "arrivée",
                "détient A ; attend B ; M-27 en attente",
                "détient B ; attend A",
            ],
            ["après arrêt P2", "à compléter", "libère B"],
            ["après fin P1", "à compléter", "à compléter"],
            ["après redémarrage", "à compléter", "à compléter"],
        ],
        [list(card) for card in data["security"]["messages"]],
        [
            [scenario, "à compléter"]
            for scenario in data["working_surfaces"]["threat_scenarios"]
        ],
    )
    expected_columns = (
        ("Extrémité 1", "Extrémité 2", "Minutes"),
        ("Sommet", "Avant : coût / prédécesseur", "Après : coût / prédécesseur"),
        ("Départ", "Échéance", "Arrivée avant/après hausse"),
        ("Moment", "P1 : ingestion M-27", "P2 : maintenance"),
        ("Carte", "Émetteur", "Contenu"),
        ("Situation", "Conclusion et justification"),
    )
    expected_ids = (
        "links",
        "route_working",
        "packet_card",
        "process_initial",
        "message_cards",
        "threat_working",
    )
    for material, title, material_id, columns, rows in zip(
        exercise.materials,
        titles,
        expected_ids,
        expected_columns,
        expected_rows,
        strict=True,
    ):
        if (
            material.id != material_id
            or material.title != title
            or material.columns != columns
            or [list(row) for row in material.rows] != rows
        ):
            raise ValueError(f"Network incident material {material_id} differs")
    if (
        f"t={data['packet']['deadline']} min" not in exercise.context
        or "P2 est arrêté et libère B" not in exercise.context
        or "clé publique de Central est authentifiée" not in exercise.context
    ):
        raise ValueError("Network incident premise differs from contract")
    with pymupdf.open(path) as pdf:
        pages = [page.get_text() for page in pdf]
        lines = [
            line.strip()
            for page in pages
            for line in page.splitlines()
            if line.strip()
            and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —", "Page : "))
        ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 3 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1 or any(text.count(title) != 1 for title in titles):
        raise ValueError("Network incident heading or material missing")
    displayed_context = " ".join(
        text.split(heading + "\n", 1)[1].split("\n" + titles[0], 1)[0].split()
    )
    if " ".join(exercise.context.split()) not in displayed_context:
        raise ValueError("Network incident printed premise differs")
    following = (titles[1], titles[2], "3a.", "3e.", titles[5], "3i.")
    for material, next_marker in zip(exercise.materials, following, strict=True):
        printed = text.split(material.title + "\n", 1)[1].split("\n" + next_marker, 1)[
            0
        ]
        expected = " ".join(
            [*material.columns, *(cell for row in material.rows for cell in row)]
        )
        if " ".join(printed.split()) != expected:
            raise ValueError(f"Network incident printed table {material.id} differs")
    for title, question_id in ((titles[0], "3a"), (titles[3], "3e"), (titles[4], "3i")):
        material_pages = [i for i, page in enumerate(pages) if title in page]
        question_pages = [
            i for i, page in enumerate(pages) if f"{question_id}." in page
        ]
        if (
            len(material_pages) != 1
            or len(question_pages) != 1
            or not 0 <= question_pages[0] - material_pages[0] <= 1
        ):
            raise ValueError(f"Network incident stage {question_id} is separated")
    for index, question in enumerate(exercise.questions):
        if (
            question.verification.get("kind") != "network_incident_contract"
            or question.verification.get("contract") != data
            or question.verification.get("task_id") != question.id
            or question.verification.get("expected") != data["expected"]
        ):
            raise ValueError(f"Network incident question {question.id} unbound")
        expected_material_ids = (
            expected_ids[:3]
            if index < 4
            else (expected_ids[2], expected_ids[3])
            if index < 8
            else (expected_ids[2], expected_ids[4], expected_ids[5])
        )
        if question.material_ids != expected_material_ids:
            raise ValueError(f"Network incident evidence {question.id} interchanged")
        if (
            sum(bool(re.match(rf"^{question.id}\.(?:\s|$)", line)) for line in lines)
            != 1
        ):
            raise ValueError(f"Network incident question {question.id} missing")
        start = text.index("\n" + question.id + ".")
        end = (
            text.index("\n" + exercise.questions[index + 1].id + ".")
            if index + 1 < len(exercise.questions)
            else len(text)
        )
        segment = " ".join(text[start:end].split())
        if segment.count(" ".join(question.prompt.split())) != 1:
            raise ValueError(f"Network incident prompt {question.id} differs")
        if segment.count("Réponse attendue") != int(correction) or segment.count(
            f"Barème indicatif — question {question.id}"
        ) != int(correction):
            raise ValueError(f"Network incident answer role {question.id} invalid")
        answer = " ".join(question.answer.split())
        if correction and answer not in segment:
            raise ValueError(f"Network incident answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Network incident answer {question.id} leaked")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            if correction and segment.count(criterion) != 1:
                raise ValueError(f"Network incident criterion {question.id} missing")
            if not correction and criterion in flat:
                raise ValueError(f"Network incident criterion {question.id} leaked")
        if correction:
            expected_credit_count = sum(
                item.points == "0.25" for item in question.marking
            )
            if segment.count("0,25 point") != expected_credit_count:
                raise ValueError(f"Network incident credit {question.id} missing")


# Bind V26's printed chronology, questions and correction credits.
def validate_network_incident_timeline_pdf(
    path: Path,
    contract: NetworkIncidentTimelineContract,
    *,
    correction: bool,
    exercise: NSIExercise,
    revision: int = 1,
) -> None:
    from Backend.Core.france.pipeline import _tasks_for_seed_v26

    data = contract.to_dict()
    validate_network_incident_timeline_exercise(
        contract,
        exercise,
        _tasks_for_seed_v26(data["seed"])[2]["question_blueprint"],
        revision=revision,
    )
    titles = tuple(material.title for material in exercise.materials)
    expected_ids = (
        "links",
        "route_working",
        "packet_card",
        "process_initial",
        "message_cards",
        "threat_working",
    )
    if (
        len(titles) != 6
        or tuple(item.id for item in exercise.materials) != expected_ids
    ):
        raise ValueError("Network incident timeline materials incomplete")
    if (
        f"t={data['packet']['deadline']} min" not in exercise.context
        or f"t={data['timeline']['report_deadline']} min" not in exercise.context
    ):
        raise ValueError("Network incident timeline premises differ")
    with pymupdf.open(path) as pdf:
        pages = [page.get_text() for page in pdf]
    lines = [
        line.strip()
        for page in pages
        for line in page.splitlines()
        if line.strip()
        and not line.startswith(("Keldin —", f"{LEGACY_PUBLISHER} —", "Page : "))
    ]
    text = "\n".join(lines)
    flat = " ".join(text.split())
    heading = f"Exercice 3 ({exercise.target_points.replace('.', ',')} points)"
    if text.count(heading) != 1 or any(text.count(title) != 1 for title in titles):
        raise ValueError("Network incident timeline heading or material missing")
    displayed_context = " ".join(
        text.split(heading + "\n", 1)[1].split("\n" + titles[0], 1)[0].split()
    )
    if " ".join(exercise.context.split()) not in displayed_context:
        raise ValueError("Network incident timeline printed premise differs")
    following = (titles[1], titles[2], "3a.", "3e.", titles[5], "3i.")
    for material, next_marker in zip(exercise.materials, following, strict=True):
        printed = text.split(material.title + "\n", 1)[1].split("\n" + next_marker, 1)[
            0
        ]
        expected = " ".join(
            [*material.columns, *(cell for row in material.rows for cell in row)]
        )
        if " ".join(printed.split()) != expected:
            raise ValueError(f"Network incident timeline table {material.id} differs")
    for title, question_id in ((titles[0], "3a"), (titles[3], "3e"), (titles[4], "3i")):
        material_pages = [i for i, page in enumerate(pages) if title in page]
        question_pages = [
            i for i, page in enumerate(pages) if f"{question_id}." in page
        ]
        if (
            len(material_pages) != 1
            or len(question_pages) != 1
            or not 0 <= question_pages[0] - material_pages[0] <= 1
        ):
            raise ValueError(f"Network incident timeline stage {question_id} separated")
    for index, question in enumerate(exercise.questions):
        if (
            question.verification.get("kind") != "network_incident_timeline_contract"
            or question.verification.get("contract") != data
            or question.verification.get("task_id") != question.id
            or question.verification.get("expected") != data["expected"]
        ):
            raise ValueError(
                f"Network incident timeline question {question.id} unbound"
            )
        expected_material_ids = (
            expected_ids[:3]
            if index < 4
            else (expected_ids[2], expected_ids[3])
            if index < 8
            else (expected_ids[2], expected_ids[4], expected_ids[5])
        )
        if question.material_ids != expected_material_ids:
            raise ValueError(
                f"Network incident timeline evidence {question.id} changed"
            )
        if (
            sum(bool(re.match(rf"^{question.id}\.(?:\s|$)", line)) for line in lines)
            != 1
        ):
            raise ValueError(
                f"Network incident timeline question {question.id} missing"
            )
        start = text.index("\n" + question.id + ".")
        end = (
            text.index("\n" + exercise.questions[index + 1].id + ".")
            if index + 1 < len(exercise.questions)
            else len(text)
        )
        segment = " ".join(text[start:end].split())
        if segment.count(" ".join(question.prompt.split())) != 1:
            raise ValueError(f"Network incident timeline prompt {question.id} differs")
        if segment.count("Réponse attendue") != int(correction) or segment.count(
            f"Barème indicatif — question {question.id}"
        ) != int(correction):
            raise ValueError(
                f"Network incident timeline answer role {question.id} invalid"
            )
        answer = " ".join(question.answer.split())
        if correction and answer not in segment:
            raise ValueError(f"Network incident timeline answer {question.id} missing")
        if not correction and answer in flat:
            raise ValueError(f"Network incident timeline answer {question.id} leaked")
        for credit in question.marking:
            criterion = " ".join(credit.criterion.split())
            if correction and segment.count(criterion) != 1:
                raise ValueError(
                    f"Network incident timeline criterion {question.id} missing"
                )
            if not correction and criterion in flat:
                raise ValueError(
                    f"Network incident timeline criterion {question.id} leaked"
                )
        if correction:
            expected_credit_count = sum(
                item.points == "0.25" for item in question.marking
            )
            if segment.count("0,25 point") != expected_credit_count:
                raise ValueError(
                    f"Network incident timeline credit {question.id} missing"
                )


# Read recent, valid local candidate text, independently of seed ordering.
def load_originality_history(output: Path) -> list[str]:
    history: list[str] = []
    if not output.is_dir():
        return history
    candidates: list[tuple[int, str, Path]] = []
    for bundle in output.glob("nsi-2027-*"):
        assessment = bundle / "assessment.json"
        try:
            if (
                bundle.is_symlink()
                or not bundle.is_dir()
                or assessment.is_symlink()
                or not assessment.is_file()
                or assessment.stat().st_size > 5 * 1024 * 1024
            ):
                continue
            candidates.append((assessment.stat().st_mtime_ns, bundle.name, assessment))
        except OSError:
            continue
    for _, _, assessment in sorted(candidates, reverse=True):
        try:
            # Recheck links in case a bundle changed while the list was built.
            if assessment.is_symlink() or assessment.parent.is_symlink():
                continue
            package = json.loads(assessment.read_text(encoding="utf-8"))
            if (
                not isinstance(package, dict)
                or package.get("schema_version") != 2
                or package.get("assessment_policy") != "fr-bac-general-nsi-written-2027"
                or not isinstance(package.get("exercises"), list)
            ):
                continue
            # Validate the entire bundle before taking any text from it. A bad
            # later exercise must not leave partial history behind.
            texts = [
                exercise_candidate_text(NSIExercise.model_validate(raw))
                for raw in package["exercises"]
            ]
            history.extend(texts[: 20 - len(history)])
            if len(history) == 20:
                return history
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return history


# Never silently render an unknown French package with an older validator.
def network_pdf_contract_version(prompt_version: str) -> str:
    if prompt_version == EXPANDED_VERSION:
        return "v35"
    if prompt_version == EXTENDED_VERSION:
        return "v34"
    if prompt_version == CONTROLLED_WHOLE_CASE_PROMPT_VERSION:
        return "v32"
    if prompt_version == CONTROLLED_ROUTE_FAMILIES_PROMPT_VERSION:
        return "v31"
    if prompt_version == CONTROLLED_ROUTE_SELECTION_PROMPT_VERSION:
        return "v30"
    if prompt_version == CONTROLLED_TREE_CONSTRUCTION_PROMPT_VERSION:
        return "v29"
    if prompt_version == CONTROLLED_DATABASE_CONSTRUCTION_PROMPT_VERSION:
        return "v28"
    if prompt_version == CONTROLLED_NETWORK_INCIDENT_MARKING_PROMPT_VERSION:
        return "v27"
    if prompt_version == CONTROLLED_NETWORK_INCIDENT_TIMELINE_PROMPT_VERSION:
        return "v26"
    if prompt_version in {
        CONTROLLED_NETWORK_INCIDENT_PROMPT_VERSION,
        CONTROLLED_DATABASE_RECONCILIATION_PROMPT_VERSION,
        CONTROLLED_GRAPH_TWO_OUTAGE_PROMPT_VERSION,
    }:
        return "v23"
    if prompt_version in {
        CONTROLLED_GRAPH_ROUTE_TRACE_PROMPT_VERSION,
        CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION,
        CONTROLLED_GRAPH_RESILIENCE_PROMPT_VERSION,
        CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
        CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    }:
        return "v18"
    if prompt_version in {
        CONTROLLED_NETWORK_DEPTH_PROMPT_VERSION,
        CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
        CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
    }:
        return "v15"
    if prompt_version == CONTROLLED_NETWORK_PROMPT_VERSION:
        return "v14"
    raise ValueError("Version de contrat réseau incompatible avec le PDF")


def database_pdf_contract_version(prompt_version: str) -> str:
    if prompt_version == EXPANDED_VERSION:
        return "v35"
    if prompt_version == EXTENDED_VERSION:
        return "v34"
    if prompt_version == CONTROLLED_WHOLE_CASE_PROMPT_VERSION:
        return "v32"
    if prompt_version in {
        CONTROLLED_DATABASE_RECONCILIATION_PROMPT_VERSION,
        CONTROLLED_GRAPH_TWO_OUTAGE_PROMPT_VERSION,
        CONTROLLED_NETWORK_INCIDENT_MARKING_PROMPT_VERSION,
        CONTROLLED_DATABASE_CONSTRUCTION_PROMPT_VERSION,
        CONTROLLED_TREE_CONSTRUCTION_PROMPT_VERSION,
        CONTROLLED_ROUTE_SELECTION_PROMPT_VERSION,
        CONTROLLED_ROUTE_FAMILIES_PROMPT_VERSION,
        CONTROLLED_NETWORK_INCIDENT_TIMELINE_PROMPT_VERSION,
    }:
        return "v24"
    if prompt_version in {
        CONTROLLED_GRAPH_ROUTE_TRACE_PROMPT_VERSION,
        CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION,
        CONTROLLED_NETWORK_INCIDENT_PROMPT_VERSION,
    }:
        return "v21"
    if prompt_version in {
        CONTROLLED_GRAPH_RESILIENCE_PROMPT_VERSION,
        CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    }:
        return "v19"
    if prompt_version in {
        CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
        CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
        CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
    }:
        return "v2"
    if prompt_version in {
        CONTROLLED_NETWORK_DEPTH_PROMPT_VERSION,
        CONTROLLED_NETWORK_PROMPT_VERSION,
    }:
        return "v1"
    raise ValueError("Version de contrat de base de données incompatible avec le PDF")


def handle_generate_assessment(args) -> int:
    if (
        getattr(args, "provider", "ollama") != "application-owned"
        and getattr(args, "authoring_version", "v32") == "v36"
    ):
        from Backend.Core.france.llm_runtime import handle_generate_llm_assessment

        return handle_generate_llm_assessment(args)
    staging = None
    previous_handler = None

    def cancel(_signal, _frame):
        raise InterruptedError(
            "Création annulée; les exercices acceptés sont conservés"
        )

    try:
        definition = assessment_framework(args.assessment)
        if not args.reference_index.is_file():
            raise ValueError(
                "Le catalogue de références manque. Préparez les sources françaises avant de créer un sujet."
            )
        reference_index_sha256 = sha256(args.reference_index.read_bytes()).hexdigest()
        # Explicit Ollama mode remains available for historical diagnostic labels.
        # The public CLI defaults to app-owned authoring with no model dependency.
        application_owned = getattr(args, "provider", "ollama") == "application-owned"
        excluded_families = getattr(args, "exclude_family", [])
        repeat_practice = getattr(args, "repeat_practice", False)
        if type(repeat_practice) is not bool:
            raise ValueError("Repeat practice must be an explicit Boolean flag")
        if repeat_practice and not application_owned:
            raise ValueError("Repeat practice requires application-owned generation")
        if excluded_families and not application_owned:
            raise ValueError(
                "Saved-family exclusions require application-owned generation"
            )
        if application_owned:
            client = ApplicationOwnedFrenchClient()
            identity = client.model_digest
        else:
            validate_endpoint(
                args.ollama_url, allow_remote=getattr(args, "allow_remote", False)
            )
            identity = model_identity(args.ollama_url, args.model)
            client = FrenchOllamaClient(
                model=args.model, base_url=args.ollama_url, seed=args.seed
            )
            client.model_digest = identity
        output = Path(args.output).expanduser().absolute()
        output.mkdir(parents=True, exist_ok=True)
        history = load_originality_history(output)
        # Repetition is an explicit practice policy, not a uniqueness verdict.
        # Keep saved files/history intact; only omit cross-history comparison.
        comparison_history = [] if repeat_practice else history
        run_implementation = implementation_identity() if application_owned else None
        selected_seed = args.seed
        if application_owned:
            try:
                selected_seed = choose_fresh_seed(
                    args.seed,
                    previous_texts=comparison_history,
                    excluded_families=excluded_families,
                )
            except FamilyCatalogueExhausted:
                if not repeat_practice:
                    raise
        checkpoint_name = (
            f"{definition.id}-{EXPANDED_VERSION}-{run_implementation}-"
            f"{REPEAT_PRACTICE_POLICY + '-' if repeat_practice else ''}{selected_seed}.json"
            if application_owned
            else f"{definition.id}-{selected_seed}.json"
        )
        checkpoint = output_directory(output, ".keldin-checkpoints") / checkpoint_name
        previous_handler = signal.signal(signal.SIGTERM, cancel)
        package = generate_assessment(
            index_path=args.reference_index,
            client=client,
            seed=selected_seed,
            checkpoint=checkpoint,
            progress=lambda message: emit_progress(message, stage="french_generation"),
            previous_texts=comparison_history,
            contract_graph_tree=True,
            contract_authoring_version="v35" if application_owned else "v32",
        )
        validate_package(package)
        if (
            application_owned
            and package["identity"]["implementation_sha256"] != run_implementation
        ):
            raise ValueError(
                "Le programme a changé pendant la génération; publication refusée"
            )
        staging = Path(tempfile.mkdtemp(prefix=".nsi-", dir=output))
        exercises = [NSIExercise.model_validate(item) for item in package["exercises"]]
        whole_case = package["identity"]["prompt_version"] in {
            CONTROLLED_WHOLE_CASE_PROMPT_VERSION,
            EXTENDED_VERSION,
            EXPANDED_VERSION,
        }
        graph_route_trace = package["identity"]["prompt_version"] in {
            CONTROLLED_GRAPH_ROUTE_TRACE_PROMPT_VERSION,
            CONTROLLED_NETWORK_INCIDENT_PROMPT_VERSION,
            CONTROLLED_DATABASE_RECONCILIATION_PROMPT_VERSION,
        }
        graph_two_outage = package["identity"]["prompt_version"] in {
            CONTROLLED_GRAPH_TWO_OUTAGE_PROMPT_VERSION,
            CONTROLLED_NETWORK_INCIDENT_MARKING_PROMPT_VERSION,
            CONTROLLED_DATABASE_CONSTRUCTION_PROMPT_VERSION,
            CONTROLLED_TREE_CONSTRUCTION_PROMPT_VERSION,
            CONTROLLED_ROUTE_SELECTION_PROMPT_VERSION,
            CONTROLLED_ROUTE_FAMILIES_PROMPT_VERSION,
            CONTROLLED_NETWORK_INCIDENT_TIMELINE_PROMPT_VERSION,
        }
        graph_resilience = package["identity"]["prompt_version"] in {
            CONTROLLED_GRAPH_RESILIENCE_PROMPT_VERSION,
            CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION,
        }
        graph_tree_depth = package["identity"]["prompt_version"] in {
            CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
            CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
            CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
        }
        graph_tree_contract = (
            None
            if whole_case
            else build_graph_two_outage_contract(args.seed)
            if graph_two_outage
            else build_graph_route_trace_contract(args.seed)
            if graph_route_trace
            else build_graph_resilience_contract(args.seed)
            if graph_resilience
            else build_graph_tree_depth_contract(args.seed)
            if graph_tree_depth
            else build_graph_tree_contract(args.seed, "1")
        )
        database_pdf_version = database_pdf_contract_version(
            package["identity"]["prompt_version"]
        )
        database_depth = database_pdf_version in {"v2", "v19"}
        database_contract = (
            None
            if whole_case
            else build_database_reconciliation_contract(args.seed)
            if database_pdf_version == "v24"
            else build_database_audit_contract(args.seed)
            if database_pdf_version == "v21"
            else build_database_depth_contract(args.seed)
            if database_depth
            else build_database_contract(args.seed)
        )
        network_pdf_version = network_pdf_contract_version(
            package["identity"]["prompt_version"]
        )
        network_timeline = network_pdf_version in {
            "v26",
            "v27",
            "v28",
            "v29",
            "v30",
            "v31",
        }
        human_readable_graph_titles = network_pdf_version in {
            "v27",
            "v28",
            "v29",
            "v30",
            "v31",
            "v32",
            "v34",
            "v35",
        }
        network_incident = network_pdf_version == "v23"
        network_reasoning = network_pdf_version == "v18"
        network_depth = network_pdf_version == "v15"
        network_contract = (
            None
            if whole_case
            else build_network_incident_timeline_contract(args.seed)
            if network_timeline
            else build_network_incident_contract(args.seed)
            if network_incident
            else build_network_reasoning_contract(args.seed)
            if network_reasoning
            else build_network_depth_contract(args.seed)
            if network_depth
            else build_network_contract(args.seed)
        )
        paths = {}
        for role, correction, filename in (
            ("question_paper", False, "sujet.pdf"),
            ("mark_scheme", True, "corrige.pdf"),
        ):
            path = staging / filename
            render_pdf_atomically(
                path,
                lambda destination, correction=correction: render_assessment(
                    destination,
                    exercises,
                    correction=correction,
                    large_print=args.large_print,
                    human_readable_graph_titles=human_readable_graph_titles,
                    coherent_material_flow=network_pdf_version
                    in {"v28", "v29", "v30", "v31", "v32", "v34", "v35"},
                    compact_correction=network_pdf_version in {"v34", "v35"},
                    print_policy=package["identity"].get("print_policy"),
                ),
                role=role,
                language="fr-FR",
            )
            validate_pdf(path)
            if whole_case:
                from Backend.Core.france.whole_case_pdf import validate_whole_case_pdf

                validate_whole_case_pdf(path, package, correction=correction)
                paths[role] = path
                continue
            graph_tree_validator = (
                validate_graph_two_outage_pdf
                if graph_two_outage
                else validate_graph_route_trace_pdf
                if graph_route_trace
                else validate_graph_resilience_pdf
                if graph_resilience
                else validate_graph_tree_depth_contract_pdf
                if graph_tree_depth
                else validate_contract_pdf
            )
            graph_tree_validator(
                path,
                graph_tree_contract,
                correction=correction,
                exercise=exercises[0],
                **(
                    {
                        "human_readable_titles": human_readable_graph_titles,
                        "coherent_material_flow": network_pdf_version
                        in {"v28", "v29", "v30", "v31"}
                        and not args.large_print,
                    }
                    if graph_two_outage
                    else {}
                ),
            )
            database_validator = (
                validate_database_reconciliation_pdf
                if database_pdf_version == "v24"
                else validate_database_audit_pdf
                if database_pdf_version == "v21"
                else validate_database_reasoning_pdf
                if database_pdf_version == "v19"
                else validate_database_depth_contract_pdf
                if database_depth
                else validate_database_contract_pdf
            )
            database_validator(
                path,
                database_contract,
                correction=correction,
                exercise=exercises[1],
            )
            network_validator = (
                validate_network_incident_timeline_pdf
                if network_timeline
                else validate_network_incident_pdf
                if network_incident
                else validate_network_reasoning_contract_pdf
                if network_reasoning
                else validate_network_depth_contract_pdf
                if network_depth
                else validate_network_contract_pdf
            )
            network_validator(
                path,
                network_contract,
                correction=correction,
                exercise=exercises[2],
                **(
                    {
                        "revision": 2
                        if network_pdf_version in {"v27", "v28", "v29", "v30", "v31"}
                        else 1
                    }
                    if network_timeline
                    else {}
                ),
            )
            paths[role] = path
        atomic_json(staging / "assessment.json", package)
        paths["assessment_package"] = staging / "assessment.json"
        artifacts = {
            role: {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}
            for role, path in paths.items()
        }
        atomic_json(
            staging / "manifest.json",
            {
                "schema_version": 1,
                "assessment": definition.id,
                "status": "unreviewed_draft",
                "artifacts": artifacts,
                "identity": package["identity"],
                "reference_index_sha256": reference_index_sha256,
                "large_print": args.large_print,
                "teacher_review": "not_run",
                "empirical_calibration": "not_run",
                "visual_calibration": "not_run",
                "generation_origin": "application_owned"
                if whole_case
                else "model_assisted",
                "model_used": not whole_case,
                **(
                    {
                        "practice_policy": REPEAT_PRACTICE_POLICY,
                        "cross_history_comparison": "not_performed",
                    }
                    if repeat_practice
                    else {}
                ),
            },
        )
        paths["package_manifest"] = staging / "manifest.json"
        if (
            not application_owned
            and model_identity(args.ollama_url, args.model) != identity
        ):
            raise ValueError(
                "Le modèle a changé pendant la génération; publication refusée"
            )
        if implementation_identity() != package["identity"]["implementation_sha256"]:
            raise ValueError(
                "Le programme a changé pendant la génération; publication refusée"
            )
        if (
            sha256(args.reference_index.read_bytes()).hexdigest()
            != reference_index_sha256
        ):
            raise ValueError(
                "Les références ont changé pendant la génération; publication refusée"
            )
        destination = output / f"nsi-2027-{selected_seed}-{digest(artifacts)[:12]}"
        if destination.exists():
            raise ValueError(
                "Ce dossier existe déjà; aucun document existant n'a été remplacé"
            )
        os.rename(staging, destination)
        staging = None
        for role, path in paths.items():
            emit("file", role=role, path=str(destination / path.name))
        emit(
            "done",
            message=(
                "Sujet d'entraînement créé. Barème indicatif, difficulté et durée non calibrées."
                if package["identity"]["prompt_version"]
                in {EXTENDED_VERSION, EXPANDED_VERSION}
                else "Brouillon créé. Relecture par un enseignant requise."
            ),
        )
        return 0
    except InterruptedError as error:
        emit("error", message=str(error), code="cancelled")
        return 130
    except Exception as error:
        emit("error", message=str(error), code="french_generation_failed")
        return 1
    finally:
        if previous_handler is not None:
            signal.signal(signal.SIGTERM, previous_handler)
        if staging is not None:
            shutil.rmtree(staging)
