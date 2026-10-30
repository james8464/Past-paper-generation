"""Publish model-authored French drafts without a catalogue fallback."""

from __future__ import annotations

import fnmatch
import os
import shutil
import signal
import tempfile
from hashlib import sha256
from pathlib import Path

from Backend.Core.apple_intelligence import FRENCH_FULL_PAPER_ERROR
from Backend.Core.events import emit, emit_progress
from Backend.Core.france import llm_pipeline
from Backend.Core.france.code_layout import CODE_LAYOUT_POLICY
from Backend.Core.france.llm_pdf import validate_llm_pdf
from Backend.Core.france.pipeline import atomic_json, digest
from Backend.Core.france.recovery_evidence import save_recovery_evidence
from Backend.Core.france.rendering import render_assessment
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.france.sql_sources import SQL_SOURCE_POLICY
from Backend.Core.generation_diagnostics import save_failure_diagnostic
from Backend.Core.generator_registry import assessment_framework
from Backend.Core.providers import HostedLLMClient
from Backend.Core.render_transaction import render_pdf_atomically


def _file_hash(path: Path) -> str:
    result = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _model_snapshot(args) -> str | None:
    if args.provider == "ollama":
        from Backend.Core.france.runtime import model_identity, validate_endpoint

        validate_endpoint(
            args.ollama_url, allow_remote=getattr(args, "allow_remote", False)
        )
        return model_identity(args.ollama_url, args.model)
    if args.provider == "apple":
        from Backend.Core.mlx_setup import MLX_MODEL_PATTERNS, resolve_local_mlx_model

        root = Path(resolve_local_mlx_model(args.model))
        files = sorted(
            path
            for path in root.rglob("*")
            if path.is_file()
            and any(
                fnmatch.fnmatch(path.name, pattern) for pattern in MLX_MODEL_PATTERNS
            )
        )
        if not (root / "config.json").is_file() or not any(
            path.suffix == ".safetensors" for path in files
        ):
            raise ValueError(
                "Le modèle MLX local est incomplet; préparez-le dans les réglages."
            )
        result = sha256()
        for path in files:
            result.update(path.relative_to(root).as_posix().encode() + b"\0")
            result.update(_file_hash(path).encode())
        return result.hexdigest()
    return None


def handle_generate_llm_assessment(args) -> int:
    staging = None
    previous_handler = None
    output = Path(args.output).expanduser().absolute()

    def cancel(_signal, _frame):
        raise InterruptedError("Création annulée; aucun PDF incomplet n'a été publié.")

    try:
        definition = assessment_framework(args.assessment)
        if args.provider == "apple_intelligence":
            raise ValueError(FRENCH_FULL_PAPER_ERROR)
        if args.provider not in {
            "ollama",
            "apple",
            "openai",
            "anthropic",
            "deepseek",
        }:
            raise ValueError("Un fournisseur de modèle est requis")
        if getattr(args, "repeat_practice", False) or getattr(
            args, "exclude_family", []
        ):
            raise ValueError(
                "Les options du catalogue ne s'appliquent pas aux sujets générés par modèle"
            )
        if type(args.seed) is not int or not -(2**31) <= args.seed < 2**31:
            raise ValueError("Graine de génération invalide")
        if not args.reference_index.is_file():
            raise ValueError(
                "Préparez les références françaises avant de créer un sujet."
            )
        if args.provider in {"openai", "anthropic", "deepseek"} and not getattr(
            args, "api_key", ""
        ):
            raise ValueError("Ajoutez la clé du fournisseur dans les réglages.")
        if args.provider == "deepseek" and not args.api_key.strip():
            raise ValueError("Ajoutez la clé du fournisseur dans les réglages.")
        reference_hash = _file_hash(args.reference_index)
        source_hash = implementation_identity()
        model_snapshot = _model_snapshot(args)
        output.mkdir(parents=True, exist_ok=True)
        previous_handler = signal.signal(signal.SIGTERM, cancel)
        client = HostedLLMClient(
            provider=args.provider,
            model=args.model,
            api_key=getattr(args, "api_key", ""),
            base_url=args.ollama_url,
        )
        steps = 0

        def progress(message):
            nonlocal steps
            steps += 1
            emit_progress(
                message,
                stage="french_generation",
                progress=min(0.8, 0.04 + steps * 0.08),
            )

        package = llm_pipeline.generate(
            index_path=args.reference_index,
            client=client,
            seed=args.seed,
            progress=progress,
            large_print=args.large_print,
            record_round=lambda snapshot: save_recovery_evidence(
                output, snapshot, secrets=(getattr(args, "api_key", ""),)
            ),
        )
        exercises = llm_pipeline.validate_package(package)
        identity = package["identity"]
        if (
            identity["provider"] != args.provider
            or identity["model"] != args.model
            or identity["seed"] != args.seed
            or identity["implementation_sha256"] != source_hash
            or identity.get("layout_policy") != CODE_LAYOUT_POLICY
            or identity.get("sql_source_policy") != SQL_SOURCE_POLICY
            or identity.get("review_recovery_policy")
            != llm_pipeline.REVIEW_RECOVERY_POLICY
            or type(identity.get("large_print")) is not bool
            or identity["large_print"] is not args.large_print
        ):
            raise ValueError(
                "Le brouillon ne correspond pas au modèle et à la demande."
            )
        staging = Path(tempfile.mkdtemp(prefix=".nsi-llm-", dir=output))
        paths = {}
        for role, correction, filename in (
            ("question_paper", False, "sujet.pdf"),
            ("mark_scheme", True, "corrige.pdf"),
        ):
            emit_progress(
                "Mise en page et vérification du document",
                stage="french_render",
                progress=0.86 if not correction else 0.92,
            )
            path = staging / filename
            render_pdf_atomically(
                path,
                lambda destination, correction=correction: render_assessment(
                    destination,
                    exercises,
                    correction=correction,
                    large_print=args.large_print,
                    human_readable_graph_titles=True,
                    coherent_material_flow=True,
                    print_policy=identity["print_policy"],
                ),
                role=role,
                language="fr-FR",
            )
            validate_llm_pdf(
                path,
                exercises,
                correction=correction,
                large_print=args.large_print,
                print_policy=identity["print_policy"],
            )
            paths[role] = path
        atomic_json(staging / "assessment.json", package)
        paths["assessment_package"] = staging / "assessment.json"
        artifacts = {
            role: {"file": path.name, "sha256": _file_hash(path)}
            for role, path in paths.items()
        }
        if (
            implementation_identity() != source_hash
            or _file_hash(args.reference_index) != reference_hash
            or _model_snapshot(args) != model_snapshot
        ):
            raise ValueError(
                "Le modèle, les sources ou le programme ont changé; publication refusée."
            )
        llm_pipeline.validate_package(package)
        manifest = {
            "schema_version": 1,
            "assessment": definition.id,
            "status": "unreviewed_draft",
            "generation_origin": "model_authored",
            "model_used": True,
            "teacher_review": "not_run",
            "empirical_calibration": "not_run",
            "visual_calibration": "not_run",
            "identity": package["identity"],
            "artifacts": artifacts,
            "reference_index_sha256": reference_hash,
            "model_snapshot_sha256": model_snapshot,
            "model_snapshot_status": "pinned_local_data"
            if model_snapshot
            else "hosted_revision_not_available",
            "large_print": args.large_print,
            "warnings": package["warnings"],
        }
        atomic_json(staging / "manifest.json", manifest)
        paths["package_manifest"] = staging / "manifest.json"
        destination = output / f"nsi-2027-v36-{args.seed}-{digest(artifacts)[:12]}"
        if destination.exists():
            raise ValueError("Ce dossier existe déjà; aucun document n'a été remplacé.")
        os.rename(staging, destination)
        staging = None
        for role, path in paths.items():
            emit("file", role=role, path=str(destination / path.name))
        emit(
            "done",
            message="Brouillon NSI généré par le modèle. Consultez les avertissements avant utilisation.",
        )
        return 0
    except InterruptedError as error:
        emit("error", message=str(error), code="cancelled")
        return 130
    except Exception as error:
        save_failure_diagnostic(
            output,
            error,
            secrets=(getattr(args, "api_key", ""),),
            context={
                "assessment": args.assessment,
                "provider": args.provider,
                "model": args.model,
            },
        )
        emit("error", message=str(error), code="french_generation_failed")
        return 1
    finally:
        if previous_handler is not None:
            signal.signal(signal.SIGTERM, previous_handler)
        if staging is not None:
            shutil.rmtree(staging)
