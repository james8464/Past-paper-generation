"""Framework-specific publication, sharing providers/events/render transactions."""

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
from Backend.Core.france.graph_resilience_contract import (
    GraphResilienceContract,
    build_graph_resilience_contract,
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
from Backend.Core.france.network import open_ollama_request
from Backend.Core.france.network_binding import network_materials
from Backend.Core.france.network_contract import NetworkContract, build_network_contract
from Backend.Core.france.network_depth_contract import (
    NetworkDepthContract,
    build_network_depth_contract,
)
from Backend.Core.france.network_reasoning_contract import (
    NetworkReasoningContract,
    build_network_reasoning_contract,
)
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import (
    CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION,
    CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
    CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    CONTROLLED_GRAPH_RESILIENCE_PROMPT_VERSION,
    CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
    CONTROLLED_NETWORK_DEPTH_PROMPT_VERSION,
    CONTROLLED_NETWORK_PROMPT_VERSION,
    CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
    atomic_json,
    digest,
    exercise_candidate_text,
    generate_assessment,
    validate_package,
)
from Backend.Core.france.provider import FrenchOllamaClient
from Backend.Core.france.rendering import (
    printable_database_criterion,
    render_assessment,
)
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.generator_registry import assessment_framework
from Backend.Core.render_transaction import render_pdf_atomically


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


def validate_contract_pdf(
    path: Path,
    contract: GraphTreeContract,
    *,
    correction: bool,
    exercise: NSIExercise | None = None,
) -> None:
    """Compare extracted printed facts with the locked first-exercise contract."""
    data = contract.to_dict()
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def validate_graph_tree_depth_contract_pdf(
    path: Path,
    contract: GraphTreeDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Check every printed V17 graph/tree fact, question and credit."""
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Graph/tree depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def validate_graph_resilience_pdf(
    path: Path,
    contract: GraphResilienceContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Fail closed on V20 printed facts, staging, answers and exact credit."""
    data = contract.to_dict()
    if exercise.id != "1" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Graph resilience exercise differs from locked contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def validate_database_contract_pdf(
    path: Path,
    contract: DatabaseContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Check that both PDF roles print the exact locked database exercise."""
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
            and not line.startswith("Paper Creator —")
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


def validate_database_depth_contract_pdf(
    path: Path,
    contract: DatabaseDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Fail closed on missing V2 facts, ten tasks, answers or rubric credits."""
    data = contract.to_dict()
    if exercise.id != "2" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Database depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def validate_database_reasoning_pdf(
    path: Path,
    contract: DatabaseDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Require V2 facts and each V19 reasoning phase in its intended role."""
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


def validate_database_audit_pdf(
    path: Path,
    contract: DatabaseAuditContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Bind V21 printed incident facts, staged working tables and exact credit."""
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
        and not line.startswith("Paper Creator —")
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


def validate_network_contract_pdf(
    path: Path,
    contract: NetworkContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Require exact app-owned network evidence in each published PDF role."""
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
            and not line.startswith("Paper Creator —")
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


def validate_network_depth_contract_pdf(
    path: Path,
    contract: NetworkDepthContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Fail closed if a v15 PDF omits locked facts or exposes an answer."""
    data = contract.to_dict()
    if exercise.id != "3" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Network depth exercise does not match its contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def validate_network_reasoning_contract_pdf(
    path: Path,
    contract: NetworkReasoningContract,
    *,
    correction: bool,
    exercise: NSIExercise,
) -> None:
    """Reject V18 PDFs whose case facts or per-question roles do not print."""
    data = contract.to_dict()
    if exercise.id != "3" or [q.id for q in exercise.questions] != data["task_ids"]:
        raise ValueError("Network reasoning exercise differs from contract")
    with pymupdf.open(path) as pdf:
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and not line.startswith("Paper Creator —")
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


def load_originality_history(output: Path) -> list[str]:
    """Read a bounded set of candidate-only text from earlier local bundles."""
    history: list[str] = []
    if not output.is_dir():
        return history
    for bundle in sorted(output.glob("nsi-2027-*"), reverse=True):
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
            package = json.loads(assessment.read_text(encoding="utf-8"))
            if (
                package.get("schema_version") != 2
                or package.get("assessment_policy") != "fr-bac-general-nsi-written-2027"
                or not isinstance(package.get("exercises"), list)
            ):
                continue
            for raw in package["exercises"]:
                history.append(exercise_candidate_text(NSIExercise.model_validate(raw)))
                if len(history) == 20:
                    return history
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return history


def network_pdf_contract_version(prompt_version: str) -> str:
    """Never silently render an unknown French package with an older validator."""
    if prompt_version in {
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
    if prompt_version == CONTROLLED_DATABASE_AUDIT_PROMPT_VERSION:
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
        validate_endpoint(
            args.ollama_url, allow_remote=getattr(args, "allow_remote", False)
        )
        identity = model_identity(args.ollama_url, args.model)
        output = Path(args.output).expanduser().absolute()
        output.mkdir(parents=True, exist_ok=True)
        checkpoint = (
            output / ".papercreator-checkpoints" / f"{definition.id}-{args.seed}.json"
        )
        client = FrenchOllamaClient(
            model=args.model, base_url=args.ollama_url, seed=args.seed
        )
        client.model_digest = identity
        previous_handler = signal.signal(signal.SIGTERM, cancel)
        package = generate_assessment(
            index_path=args.reference_index,
            client=client,
            seed=args.seed,
            checkpoint=checkpoint,
            progress=lambda message: emit_progress(message, stage="french_generation"),
            previous_texts=load_originality_history(output),
            contract_graph_tree=True,
            contract_authoring_version="v21",
        )
        validate_package(package)
        staging = Path(tempfile.mkdtemp(prefix=".nsi-", dir=output))
        exercises = [NSIExercise.model_validate(item) for item in package["exercises"]]
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
            build_graph_resilience_contract(args.seed)
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
            build_database_audit_contract(args.seed)
            if database_pdf_version == "v21"
            else build_database_depth_contract(args.seed)
            if database_depth
            else build_database_contract(args.seed)
        )
        network_pdf_version = network_pdf_contract_version(
            package["identity"]["prompt_version"]
        )
        network_reasoning = network_pdf_version == "v18"
        network_depth = network_pdf_version == "v15"
        network_contract = (
            build_network_reasoning_contract(args.seed)
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
                ),
                role=role,
                language="fr-FR",
            )
            validate_pdf(path)
            graph_tree_validator = (
                validate_graph_resilience_pdf
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
            )
            database_validator = (
                validate_database_audit_pdf
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
                validate_network_reasoning_contract_pdf
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
            },
        )
        paths["package_manifest"] = staging / "manifest.json"
        if model_identity(args.ollama_url, args.model) != identity:
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
        destination = output / f"nsi-2027-{args.seed}-{digest(artifacts)[:12]}"
        if destination.exists():
            raise ValueError(
                "Ce dossier existe déjà; aucun document existant n'a été remplacé"
            )
        os.rename(staging, destination)
        staging = None
        for role, path in paths.items():
            emit("file", role=role, path=str(destination / path.name))
        emit("done", message="Brouillon créé. Relecture par un enseignant requise.")
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
