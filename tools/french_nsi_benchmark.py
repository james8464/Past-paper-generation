"""Resumable live qualification runner for the French NSI written assessment.

The runner launches the public backend command in a separate process, preserves
every log and checkpoint, and refuses to continue if the implementation changes.
It does not convert automated success into teacher or learner approval.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import platform
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Core.education_context import NSI_2027  # noqa: E402
from Backend.Core.france.database_depth_contract import (  # noqa: E402
    build_database_depth_contract,
)
from Backend.Core.france.database_depth_prose import (  # noqa: E402
    DATABASE_DEPTH_PROSE_VERSION,
    database_depth_catalogue_digest,
)
from Backend.Core.france.database_reasoning_prose import (  # noqa: E402
    DATABASE_REASONING_PROSE_VERSION,
    database_reasoning_catalogue_digest,
)
from Backend.Core.france.graph_tree_depth_contract import (  # noqa: E402
    build_graph_tree_depth_contract,
)
from Backend.Core.france.graph_tree_depth_prose import (  # noqa: E402
    GRAPH_TREE_DEPTH_PROSE_VERSION,
    graph_tree_depth_catalogue_digest,
)
from Backend.Core.france.graph_tree_prose import (  # noqa: E402
    PROSE_CONTRACT_VERSION,
    prose_catalogue_digest,
)
from Backend.Core.france.network_depth_contract import (  # noqa: E402
    build_network_depth_contract,
)
from Backend.Core.france.network_depth_prose import (  # noqa: E402
    NETWORK_DEPTH_PROSE_VERSION,
    network_depth_catalogue_digest,
)
from Backend.Core.france.network_reasoning_contract import (  # noqa: E402
    build_network_reasoning_contract,
)
from Backend.Core.france.network_reasoning_prose import (  # noqa: E402
    NETWORK_REASONING_PROSE_VERSION,
    network_reasoning_catalogue_digest,
)
from Backend.Core.france.pipeline import (  # noqa: E402
    CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
    CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
    CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
)
from Backend.Core.france.runtime import model_identity  # noqa: E402
from Backend.Core.france.source_identity import implementation_identity  # noqa: E402
from Backend.Core.paths import REPO_ROOT  # noqa: E402
from tools.live_process import BackendRun, run_backend  # noqa: E402

ASSESSMENT = "fr-bac-general-nsi-written-2027"
DEFAULT_MODELS = ("gemma4:12b", "ministral-3:8b", "qwen3:8b")


@dataclass(frozen=True)
class BenchmarkItem:
    model: str
    seed: int
    exercise_count: int = 3


def build_plan(
    models: list[str], *, base_seed: int, papers: int
) -> list[BenchmarkItem]:
    if not models or len(set(models)) != len(models):
        raise ValueError("La liste des modèles doit être non vide et sans doublon")
    if type(base_seed) is not int or papers < 1:
        raise ValueError("Graine et nombre de sujets invalides")
    seeds = range(base_seed, base_seed + papers)
    return [BenchmarkItem(model, seed) for model in models for seed in seeds]


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def accepted_result(
    path: Path, identity: dict[str, Any], *, expected_prompt_version: str | None = None
) -> bool:
    return _accepted_payload(
        _load_json(path), path, identity, expected_prompt_version=expected_prompt_version
    )


def _accepted_payload(
    value: dict[str, Any] | None,
    path: Path,
    identity: dict[str, Any],
    *,
    expected_prompt_version: str | None = None,
) -> bool:
    if (
        not value
        or value.get("status") != "passed"
        or value.get("identity") != identity
    ):
        return False
    recorded_artifacts = value.get("artifacts")
    if not isinstance(recorded_artifacts, dict):
        return False
    manifest_name = recorded_artifacts.get("manifest")
    manifest_sha256 = recorded_artifacts.get("manifest_sha256")
    if not isinstance(manifest_name, str) or not isinstance(manifest_sha256, str):
        return False
    manifest_path = path.parent / manifest_name
    manifest = _load_json(manifest_path)
    if not manifest or manifest.get("schema_version") != 1:
        return False
    try:
        if _sha256(manifest_path) != manifest_sha256:
            return False
    except OSError:
        return False
    if (
        manifest.get("assessment") != ASSESSMENT
        or manifest.get("status") != "unreviewed_draft"
        or manifest.get("reference_index_sha256")
        != identity.get("reference_index_sha256")
    ):
        return False
    manifest_identity = manifest.get("identity")
    if not isinstance(manifest_identity, dict) or any(
        manifest_identity.get(manifest_key) != identity.get(result_key)
        for manifest_key, result_key in (
            ("implementation_sha256", "implementation"),
            ("model", "model"),
            ("model_digest", "model_digest"),
            ("seed", "seed"),
        )
    ):
        return False
    if (
        manifest_identity.get("assessment") != asdict(NSI_2027)
        or (
            expected_prompt_version is not None
            and manifest_identity.get("prompt_version") != expected_prompt_version
        )
        or manifest_identity.get("prompt_version")
        not in {
            CONTROLLED_DATABASE_DEPTH_PROMPT_VERSION,
            CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
            CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
            CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
        }
        or manifest_identity.get("database_depth_contract_sha256")
        != build_database_depth_contract(identity["seed"]).digest
        or manifest_identity.get("provider") != "ollama"
    ):
        return False
    if (
        manifest_identity["prompt_version"]
        == CONTROLLED_DATABASE_REASONING_PROMPT_VERSION
    ):
        if (
            manifest_identity.get("database_reasoning_prose_contract_version")
            != DATABASE_REASONING_PROSE_VERSION
            or manifest_identity.get("database_reasoning_prose_catalogue_sha256")
            != database_reasoning_catalogue_digest()
            or any(
                field in manifest_identity
                for field in (
                    "database_depth_prose_contract_version",
                    "database_depth_prose_catalogue_sha256",
                )
            )
        ):
            return False
    elif (
        manifest_identity.get("database_depth_prose_contract_version")
        != DATABASE_DEPTH_PROSE_VERSION
        or manifest_identity.get("database_depth_prose_catalogue_sha256")
        != database_depth_catalogue_digest()
    ):
        return False
    if manifest_identity["prompt_version"] in {
        CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
        CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    }:
        if (
            manifest_identity.get("network_reasoning_contract_sha256")
            != build_network_reasoning_contract(identity["seed"]).digest
            or manifest_identity.get("network_reasoning_prose_contract_version")
            != NETWORK_REASONING_PROSE_VERSION
            or manifest_identity.get("network_reasoning_prose_catalogue_sha256")
            != network_reasoning_catalogue_digest()
            or any(
                field in manifest_identity
                for field in (
                    "network_depth_contract_sha256",
                    "network_depth_prose_contract_version",
                    "network_depth_prose_catalogue_sha256",
                )
            )
        ):
            return False
    elif (
        manifest_identity.get("network_depth_contract_sha256")
        != build_network_depth_contract(identity["seed"]).digest
        or manifest_identity.get("network_depth_prose_contract_version")
        != NETWORK_DEPTH_PROSE_VERSION
        or manifest_identity.get("network_depth_prose_catalogue_sha256")
        != network_depth_catalogue_digest()
    ):
        return False
    if manifest_identity["prompt_version"] in {
        CONTROLLED_GRAPH_TREE_DEPTH_PROMPT_VERSION,
        CONTROLLED_NETWORK_REASONING_PROMPT_VERSION,
        CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
    }:
        if (
            manifest_identity.get("graph_tree_depth_contract_sha256")
            != build_graph_tree_depth_contract(identity["seed"]).digest
            or manifest_identity.get("graph_tree_depth_prose_contract_version")
            != GRAPH_TREE_DEPTH_PROSE_VERSION
            or manifest_identity.get("graph_tree_depth_prose_catalogue_sha256")
            != graph_tree_depth_catalogue_digest()
        ):
            return False
    elif (
        manifest_identity.get("prose_contract_version") != PROSE_CONTRACT_VERSION
        or manifest_identity.get("prose_catalogue_sha256") != prose_catalogue_digest()
    ):
        return False
    artifacts = manifest.get("artifacts")
    if (
        not isinstance(artifacts, dict)
        or not {"question_paper", "mark_scheme", "assessment_package"}
        <= artifacts.keys()
    ):
        return False
    for artifact in artifacts.values():
        if not isinstance(artifact, dict):
            return False
        filename, expected_hash = artifact.get("file"), artifact.get("sha256")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not isinstance(expected_hash, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_hash)
        ):
            return False
        try:
            if _sha256(manifest_path.parent / filename) != expected_hash:
                return False
        except OSError:
            return False
    package_file = artifacts["assessment_package"]["file"]
    package = _load_json(manifest_path.parent / package_file)
    return bool(
        package
        and package.get("assessment_policy") == ASSESSMENT
        and package.get("identity") == manifest_identity
    )


def _events(stdout: str) -> list[dict[str, Any]]:
    result = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def summarize_run(
    run: BackendRun,
    *,
    elapsed_seconds: float,
    checkpoint: Path,
    artifact_manifest: Path | None,
) -> dict[str, Any]:
    checkpoint_value = _load_json(checkpoint) or {}
    failures = checkpoint_value.get("failed_attempts", [])
    failures = failures if isinstance(failures, list) else []
    events = _events(run.stdout)
    errors = [event.get("message") for event in events if event.get("type") == "error"]
    status = (
        "passed" if run.return_code == 0 and artifact_manifest is not None else "failed"
    )
    if run.timed_out:
        status = "timed_out"
    return {
        "status": status,
        "return_code": run.return_code,
        "timed_out": run.timed_out,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "peak_backend_rss_bytes": run.peak_backend_rss_bytes,
        "repair_attempts": len(failures),
        "first_pass": status == "passed" and not failures,
        "error": errors[-1] if errors else (run.stderr.strip()[-2000:] or None),
    }


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _command_output(command: list[str]) -> str | None:
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def hardware_record() -> dict[str, Any]:
    return {
        "captured_at": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "macos": _command_output(["sw_vers"]),
        "hardware": _command_output(["system_profiler", "SPHardwareDataType", "-json"]),
        "ollama_version": _command_output(["ollama", "--version"]),
        "python": sys.version,
    }


def _manifest_from_events(stdout: str) -> Path | None:
    paths = [
        Path(str(event["path"]))
        for event in _events(stdout)
        if event.get("type") == "file"
        and event.get("role") == "package_manifest"
        and isinstance(event.get("path"), str)
    ]
    return paths[-1] if paths and paths[-1].is_file() else None


@contextmanager
def exclusive_runner_lock():
    lock = REPO_ROOT / "tmp" / "french-nsi-benchmark.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Une qualification française est déjà active") from error
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def run_plan(args: argparse.Namespace) -> int:
    reference_index = args.reference_index.expanduser().resolve()
    if not reference_index.is_file():
        raise FileNotFoundError(f"Catalogue introuvable : {reference_index}")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    models = [value.strip() for value in args.models.split(",") if value.strip()]
    plan = build_plan(models, base_seed=args.base_seed, papers=args.papers_per_model)
    source_identity = implementation_identity()
    reference_identity = _sha256(reference_index)
    model_digests = {model: model_identity(args.ollama_url, model) for model in models}
    session_identity = {
        "schema_version": 1,
        "assessment": ASSESSMENT,
        "implementation": source_identity,
        "reference_index_sha256": reference_identity,
        "models": model_digests,
        "base_seed": args.base_seed,
        "papers_per_model": args.papers_per_model,
    }
    session_path = output / "session.json"
    if session_path.exists():
        existing = _load_json(session_path)
        if existing is None:
            raise ValueError("La session a perdu son intégrité; conserver le dossier")
        if existing.get("identity") != session_identity:
            raise ValueError(
                "Ce dossier appartient à une autre identité de qualification"
            )
    else:
        if any(output.iterdir()):
            raise ValueError("La session a perdu son intégrité; conserver le dossier")
        _atomic_json(
            session_path,
            {
                "identity": session_identity,
                "hardware": hardware_record(),
                "created_at": datetime.now(UTC).isoformat(),
                "qualification_limits": [
                    "Les contrôles automatisés ne constituent pas un avis d'enseignant.",
                    "La mémoire mesurée du processus backend exclut le serveur Ollama.",
                ],
            },
        )

    results = []
    for item in plan:
        if (
            implementation_identity() != source_identity
            or _sha256(reference_index) != reference_identity
        ):
            raise RuntimeError(
                "Le code ou les références ont changé; qualification arrêtée"
            )
        digest = model_digests[item.model]
        identity = {
            "implementation": source_identity,
            "reference_index_sha256": reference_identity,
            "model": item.model,
            "model_digest": digest,
            "seed": item.seed,
        }
        item_root = output / "runs" / _slug(item.model) / digest[:12] / str(item.seed)
        result_path = item_root / "result.json"
        previous = _load_json(result_path)
        if result_path.exists() and (
            not previous
            or previous.get("identity") != identity
            or previous.get("status") not in {"passed", "failed", "timed_out"}
        ):
            raise ValueError("Le résultat a perdu son intégrité; conserver le dossier")
        if previous is None and item_root.exists() and any(item_root.iterdir()):
            raise ValueError("Le résultat a perdu son intégrité; conserver le dossier")
        if accepted_result(
            result_path,
            identity,
            expected_prompt_version=CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
        ):
            results.append(previous)
            continue
        if previous is not None and previous.get("status") == "passed":
            raise ValueError(
                "Une preuve acceptée a perdu son intégrité; conserver le dossier "
                "et enquêter avant toute nouvelle génération"
            )
        if previous is not None and not args.retry_failed:
            results.append(previous)
            continue

        attempt_count = len(list(item_root.glob("attempt-*"))) + 1
        attempt = item_root / f"attempt-{attempt_count:03d}"
        attempt.mkdir(parents=True, exist_ok=False)
        artifact_root = output / "artifacts" / _slug(item.model) / digest[:12]
        checkpoint = (
            artifact_root
            / ".papercreator-checkpoints"
            / f"{ASSESSMENT}-{item.seed}.json"
        )
        command = [
            sys.executable,
            "-u",
            "-m",
            "Backend.Core.cli",
            "generate-assessment",
            "--assessment",
            ASSESSMENT,
            "--reference-index",
            str(reference_index),
            "--output",
            str(artifact_root),
            "--seed",
            str(item.seed),
            "--model",
            item.model,
            "--ollama-url",
            args.ollama_url,
        ]
        started = time.monotonic()
        run = run_backend(
            command,
            cwd=REPO_ROOT,
            run_dir=attempt,
            timeout_seconds=args.timeout_seconds,
        )
        manifest = _manifest_from_events(run.stdout)
        summary = summarize_run(
            run,
            elapsed_seconds=time.monotonic() - started,
            checkpoint=checkpoint,
            artifact_manifest=manifest,
        )
        relative_manifest = (
            os.path.relpath(manifest, item_root) if manifest is not None else None
        )
        result = {
            **summary,
            "identity": identity,
            "exercise_count": item.exercise_count,
            "attempt_directory": attempt.name,
            "artifacts": {
                "manifest": relative_manifest,
                "manifest_sha256": _sha256(manifest) if manifest is not None else None,
            },
            "completed_at": datetime.now(UTC).isoformat(),
        }
        if result["status"] == "passed" and not _accepted_payload(
            result,
            result_path,
            identity,
            expected_prompt_version=CONTROLLED_DATABASE_REASONING_PROMPT_VERSION,
        ):
            result["status"] = "failed"
            result["error"] = "L'intégrité des artefacts publiés est invalide"
            _atomic_json(result_path, result)
            raise ValueError(
                "Les artefacts ont perdu leur intégrité; conserver le dossier"
            )
        _atomic_json(result_path, result)
        results.append(result)
        if implementation_identity() != source_identity:
            raise RuntimeError(
                "Le code a changé pendant une génération; arrêt immédiat"
            )

    complete = len(results) == len(plan)
    report = {
        "identity": session_identity,
        "planned_papers": len(plan),
        "planned_exercises_per_model": args.papers_per_model * 3,
        "passed": sum(
            result and result.get("status") == "passed" for result in results
        ),
        "failed": sum(
            result and result.get("status") != "passed" for result in results
        ),
        "complete": complete,
        "results": results,
        "educational_qualification": "not_run",
    }
    _atomic_json(output / "benchmark-summary.json", report)
    return 0 if complete and report["failed"] == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run and resume French NSI local-model qualification."
    )
    parser.add_argument("--reference-index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS))
    parser.add_argument("--base-seed", type=int, default=270100)
    parser.add_argument("--papers-per-model", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=10_800)
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--retry-failed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with exclusive_runner_lock():
        return run_plan(args)


if __name__ == "__main__":
    raise SystemExit(main())
