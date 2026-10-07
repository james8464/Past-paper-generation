"""Framework-specific publication, sharing providers/events/render transactions."""

import json
import os
import re
import shutil
import signal
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request

import pymupdf

from Backend.Core.events import emit, emit_progress
from Backend.Core.france.database_binding import database_materials
from Backend.Core.france.database_contract import (
    DatabaseContract,
    build_database_contract,
)
from Backend.Core.france.graph_tree_binding import canonical_answer, graph_edge_manifest
from Backend.Core.france.graph_tree_contract import (
    GraphTreeContract,
    build_graph_tree_contract,
)
from Backend.Core.france.network import open_ollama_request
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.pipeline import (
    atomic_json,
    digest,
    exercise_candidate_text,
    generate_assessment,
    validate_package,
)
from Backend.Core.france.provider import FrenchOllamaClient
from Backend.Core.france.rendering import render_assessment
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
            contract_authoring_version="v13",
        )
        validate_package(package)
        staging = Path(tempfile.mkdtemp(prefix=".nsi-", dir=output))
        exercises = [NSIExercise.model_validate(item) for item in package["exercises"]]
        graph_tree_contract = build_graph_tree_contract(args.seed, "1")
        database_contract = build_database_contract(args.seed)
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
            validate_contract_pdf(
                path,
                graph_tree_contract,
                correction=correction,
                exercise=exercises[0],
            )
            validate_database_contract_pdf(
                path,
                database_contract,
                correction=correction,
                exercise=exercises[1],
            )
            paths[role] = path
        atomic_json(staging / "assessment.json", package)
        paths["assessment_package"] = staging / "assessment.json"
        from hashlib import sha256

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
