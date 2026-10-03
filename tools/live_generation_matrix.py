from __future__ import annotations

import argparse
import hashlib
import json
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from Backend.Core.events import BACKEND_VERSION
from Backend.Core.model_recommendations import default_ollama_model
from Backend.Core.qualification.manifest import (
    ArtifactEvidence,
    EvidenceRecord,
    GateState,
    ModelIdentity,
    QualificationManifest,
    VersionIdentity,
)
from tools.live_process import run_backend

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "Resources" / "generator-registry.json"


@dataclass(frozen=True)
class MatrixJob:
    seed_offset: int
    family_id: str
    backend_subject: str
    paper: str
    title: str
    detail: str
    expected_roles: tuple[str, ...]

    @property
    def id(self) -> str:
        return f"{self.backend_subject}:{self.paper}"


def matrix_jobs(payload: dict[str, Any]) -> list[MatrixJob]:
    if payload.get("schema_version") not in {2, 3, 4, 5}:
        raise ValueError("unsupported generator registry schema")
    jobs: list[MatrixJob] = []
    seen: set[str] = set()
    for family in payload.get("families", []):
        if not family.get("advertised"):
            continue
        subject = str(family["backend_subject"])
        outputs = family.get("outputs_by_paper", {})
        papers = family.get("papers", [])
        declared = [str(value) for value in family.get("declared_papers", [])]
        if [str(paper.get("id")) for paper in papers] != declared:
            raise ValueError(f"{family['id']} paper metadata is inconsistent")
        for paper in papers:
            paper_id = str(paper["id"])
            job = MatrixJob(
                seed_offset=len(jobs),
                family_id=str(family["id"]),
                backend_subject=subject,
                paper=paper_id,
                title=str(paper["title"]),
                detail=str(paper["detail"]),
                expected_roles=tuple(str(role) for role in outputs.get(paper_id, [])),
            )
            if not job.expected_roles:
                raise ValueError(f"{job.id} has no declared outputs")
            if job.id in seen:
                raise ValueError(f"duplicate matrix job: {job.id}")
            seen.add(job.id)
            jobs.append(job)
    if not jobs:
        raise ValueError("generator registry has no advertised papers")
    return jobs


def run_matrix(
    jobs: list[MatrixJob],
    *,
    output_root: Path,
    command_prefix: list[str],
    model: str,
    provider: str,
    ollama_url: str,
    base_seed: int,
    timeout_seconds: int,
    dry_run: bool,
    resume: bool,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    started = time.time()
    _save_matrix_report(
        results,
        output_root=output_root,
        started=started,
        jobs=jobs,
        model=model,
        provider=provider,
        dry_run=dry_run,
        base_seed=base_seed,
        ollama_url=ollama_url,
        command_prefix=command_prefix,
    )
    for index, job in enumerate(jobs):
        run_dir = output_root / job.backend_subject / f"paper-{job.paper}"
        run_dir.mkdir(parents=True, exist_ok=True)
        result_path = run_dir / "matrix-result.json"
        seed = base_seed + job.seed_offset
        model_digest = (
            _model_digest(provider, model, ollama_url) if not dry_run else None
        )
        request_identity = _request_identity(
            job,
            seed=seed,
            model=model,
            provider=provider,
            ollama_url=ollama_url,
            dry_run=dry_run,
            command_prefix=command_prefix,
            model_digest=model_digest,
        )
        if resume:
            previous = _resumable_result(result_path, request_identity=request_identity)
            if previous is not None:
                qualification_path = previous.get("qualification_manifest")
                if (
                    not qualification_path
                    or not Path(str(qualification_path)).is_file()
                ):
                    qualification_path = _write_qualification_manifest(
                        job=job,
                        result=previous,
                        result_path=result_path,
                        run_dir=run_dir,
                        output_root=output_root,
                    )
                    previous["qualification_manifest"] = str(qualification_path)
                    result_path.write_text(
                        json.dumps(previous, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                print(f"[{index + 1}/{len(jobs)}] {job.id}: already passed", flush=True)
                results.append(previous)
                _save_matrix_report(
                    results,
                    output_root=output_root,
                    started=started,
                    jobs=jobs,
                    model=model,
                    provider=provider,
                    dry_run=dry_run,
                    base_seed=base_seed,
                    ollama_url=ollama_url,
                    command_prefix=command_prefix,
                )
                continue

        command = [
            *command_prefix,
            "generate",
            "--subject",
            job.backend_subject,
            "--paper",
            job.paper,
            "--output",
            str(run_dir),
            "--seed",
            str(seed),
            "--model",
            model,
            "--provider",
            provider,
            "--ollama-url",
            ollama_url,
        ]
        if dry_run:
            command.append("--dry-run")

        print(f"[{index + 1}/{len(jobs)}] {job.id}: generating", flush=True)
        active_result = {
            "id": job.id,
            "seed": seed,
            "status": "running",
            "passed": False,
            "generation_passed": False,
            "reference_demand_passed": False,
            "request_identity": request_identity,
            "files": {},
            "model": None if dry_run else model,
            "provider": None if dry_run else provider,
            "model_digest": model_digest,
        }
        result_path.write_text(json.dumps(active_result) + "\n", encoding="utf-8")
        (run_dir / "events.jsonl").write_text("", encoding="utf-8")
        _write_qualification_manifest(
            job=job,
            result=active_result,
            result_path=result_path,
            run_dir=run_dir,
            output_root=output_root,
        )
        before = time.monotonic()
        completed = run_backend(
            command,
            cwd=ROOT,
            run_dir=run_dir,
            timeout_seconds=timeout_seconds,
        )
        return_code = completed.return_code
        timed_out = completed.timed_out
        stdout, stderr = completed.stdout, completed.stderr
        duration = round(time.monotonic() - before, 2)
        (run_dir / "events.jsonl").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")

        events = _events(stdout)
        file_events = {
            str(event.get("role")): Path(str(event.get("path")))
            for event in events
            if event.get("type") == "file"
        }
        expected = set(job.expected_roles) | {"package_manifest"}
        missing_roles = sorted(expected - file_events.keys())
        missing_files = sorted(
            role for role, path in file_events.items() if not path.is_file()
        )
        error_messages = [
            str(event.get("message"))
            for event in events
            if event.get("type") == "error"
        ]
        if not error_messages and return_code != 0:
            error_messages = [_process_failure_message(return_code, timed_out, stderr)]
        generation_passed = (
            return_code == 0
            and not missing_roles
            and not missing_files
            and any(event.get("type") == "done" for event in events)
        )
        current_identity = _request_identity(
            job,
            seed=seed,
            model=model,
            provider=provider,
            ollama_url=ollama_url,
            dry_run=dry_run,
            command_prefix=command_prefix,
            model_digest=_model_digest(provider, model, ollama_url)
            if not dry_run
            else None,
        )
        if current_identity != request_identity:
            generation_passed = False
            error_messages.append(
                "runtime source or model changed during generation; rerun on stable inputs"
            )
        demand = _read_package_manifest(file_events.get("assessment_package")).get(
            "reference_demand"
        )
        demand_passed = isinstance(demand, dict) and demand.get("passed") is True
        if generation_passed and not demand_passed:
            checks = demand.get("failed_checks", []) if isinstance(demand, dict) else []
            error_messages.append(
                "reference-demand audit failed: "
                + (", ".join(map(str, checks)) or "missing or invalid evidence")
            )
        passed = generation_passed and demand_passed
        result = {
            "id": job.id,
            "family_id": job.family_id,
            "backend_subject": job.backend_subject,
            "paper": job.paper,
            "title": job.title,
            "detail": job.detail,
            "seed": seed,
            "model": None if dry_run else model,
            "provider": None if dry_run else provider,
            "preview": dry_run,
            "status": "completed",
            "request_identity": request_identity,
            "model_digest": model_digest,
            "peak_backend_rss_bytes": completed.peak_backend_rss_bytes,
            "memory_scope": "Backend peak resident memory; separate model-server/GPU memory excluded.",
            "duration_seconds": duration,
            "return_code": return_code,
            "timed_out": timed_out,
            "passed": passed,
            "generation_passed": generation_passed,
            "reference_demand_passed": demand_passed,
            "missing_roles": missing_roles,
            "missing_files": missing_files,
            "errors": error_messages,
            "files": {role: str(path) for role, path in sorted(file_events.items())},
            "artifact_sha256": {
                role: _sha256(path)
                for role, path in sorted(file_events.items())
                if path.is_file()
            },
            "events_sha256": _sha256(run_dir / "events.jsonl"),
        }
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        qualification_path = _write_qualification_manifest(
            job=job,
            result=result,
            result_path=result_path,
            run_dir=run_dir,
            output_root=output_root,
        )
        result["qualification_manifest"] = str(qualification_path)
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        results.append(result)
        verdict = "passed" if passed else "failed"
        print(
            f"[{index + 1}/{len(jobs)}] {job.id}: {verdict} in {duration:.0f}s",
            flush=True,
        )
        _save_matrix_report(
            results,
            output_root=output_root,
            started=started,
            jobs=jobs,
            model=model,
            provider=provider,
            dry_run=dry_run,
            base_seed=base_seed,
            ollama_url=ollama_url,
            command_prefix=command_prefix,
        )

    return _save_matrix_report(
        results,
        output_root=output_root,
        started=started,
        jobs=jobs,
        model=model,
        provider=provider,
        dry_run=dry_run,
        base_seed=base_seed,
        ollama_url=ollama_url,
        command_prefix=command_prefix,
    )


def _save_matrix_report(
    results: list[dict[str, Any]],
    *,
    output_root: Path,
    started: float,
    jobs: list[MatrixJob],
    model: str,
    provider: str,
    dry_run: bool,
    base_seed: int,
    ollama_url: str,
    command_prefix: list[str],
) -> dict[str, Any]:
    model_digest = _model_digest(provider, model, ollama_url) if not dry_run else None
    runtime_sha256 = _runtime_sha256()
    by_id = {job.id: job for job in jobs}
    for result in results:
        if result.get("passed") is not True:
            continue
        job = by_id[result["id"]]
        expected = _request_identity(
            job,
            seed=base_seed + job.seed_offset,
            model=model,
            provider=provider,
            ollama_url=ollama_url,
            dry_run=dry_run,
            command_prefix=command_prefix,
            model_digest=model_digest,
            runtime_sha256=runtime_sha256,
        )
        run_dir = output_root / job.backend_subject / f"paper-{job.paper}"
        result_path = run_dir / "matrix-result.json"
        if _resumable_result(result_path, request_identity=expected) is None:
            result["passed"] = result["generation_passed"] = False
            result["errors"].append(
                "qualification evidence is stale, incomplete or unverifiable; rerun this route"
            )
            result_path.write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            _write_qualification_manifest(
                job=job,
                result=result,
                result_path=result_path,
                run_dir=run_dir,
                output_root=output_root,
            )
    passed_count = sum(bool(result["passed"]) for result in results)
    report = {
        "schema_version": 1,
        "complete": len(results) == len(jobs),
        "expected_jobs": len(jobs),
        "generated_at_unix": round(time.time()),
        "duration_seconds": round(time.time() - started, 2),
        "model": None if dry_run else model,
        "provider": None if dry_run else provider,
        "preview": dry_run,
        "summary": {
            "papers": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
        },
        "results": results,
    }
    (output_root / "matrix-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_root / "matrix-report.md").write_text(
        matrix_markdown(report),
        encoding="utf-8",
    )
    _write_run_qualification_manifest(
        output_root=output_root,
        report=report,
        model=None if dry_run else model,
        provider=None if dry_run else provider,
        base_seed=base_seed,
    )
    return report


def matrix_markdown(report: dict[str, Any]) -> str:
    rows = [
        "# Live generation matrix",
        "",
        f"Model: `{report['model'] or 'preview mode'}`",
        f"Scope: {len(report['results'])}/{report.get('expected_jobs', len(report['results']))} routes completed; "
        + ("complete run." if report.get("complete", True) else "INCOMPLETE run."),
        "",
        "| Generator | Paper | Result | Time | Error |",
        "|---|---:|---|---:|---|",
    ]
    for result in report["results"]:
        error = "; ".join(result["errors"]) or "—"
        rows.append(
            f"| {result['family_id']} | {result['paper']} | "
            f"{'Passed' if result['passed'] else 'Failed'} | "
            f"{result['duration_seconds']:.0f}s | {error} |"
        )
    summary = report["summary"]
    rows.extend(
        [
            "",
            f"**{summary['passed']}/{summary['papers']} papers passed.**",
            "",
        ]
    )
    return "\n".join(rows)


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


def _request_identity(
    job: MatrixJob,
    *,
    seed: int,
    model: str,
    provider: str,
    ollama_url: str,
    dry_run: bool,
    command_prefix: list[str],
    model_digest: str | None,
    runtime_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "version": 1,
        "job": job.id,
        "seed": seed,
        "preview": dry_run,
        "model": None if dry_run else model,
        "provider": None if dry_run else provider,
        "model_digest": model_digest,
        "endpoint_sha256": hashlib.sha256(ollama_url.rstrip("/").encode()).hexdigest(),
        "runtime_sha256": runtime_sha256
        if runtime_sha256 is not None
        else _runtime_sha256(),
        "command": command_prefix,
        "executable_sha256": _sha256(Path(command_prefix[0]))
        if Path(command_prefix[0]).is_file()
        else None,
        "expected_roles": list(job.expected_roles),
    }


def _runtime_sha256() -> str:
    runtime_files = [ROOT / "bridge.py", ROOT / "requirements-build.txt"]
    for folder in (ROOT / "Backend", ROOT / "Resources"):
        runtime_files.extend(
            path
            for path in folder.rglob("*")
            if path.is_file()
            and "tests" not in path.parts
            and path.suffix.casefold() in {".py", ".json", ".toml", ".ttf", ".otf"}
            and path.name != "repository-inventory.json"
        )
    digest = hashlib.sha256()
    for path in sorted(runtime_files):
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(_sha256(path).encode())
    return digest.hexdigest()


def _model_digest(provider: str, model: str, ollama_url: str) -> str | None:
    if provider != "ollama":
        return None
    try:
        with urllib.request.urlopen(
            ollama_url.rstrip("/") + "/api/tags", timeout=5
        ) as response:
            payload = json.load(response)
        for entry in payload.get("models", []):
            if entry.get("name") == model or entry.get("model") == model:
                value = entry.get("digest")
                return value if isinstance(value, str) else None
    except (OSError, ValueError, AttributeError):
        pass
    return None


def _resumable_result(
    path: Path, *, request_identity: dict[str, Any]
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(result, dict) or result.get("passed") is not True:
        return None
    if result.get("request_identity") != request_identity:
        return None
    if (
        request_identity["provider"] == "ollama"
        and not request_identity["model_digest"]
    ):
        return None
    files = result.get("files")
    expected = set(request_identity["expected_roles"]) | {"package_manifest"}
    hashes = result.get("artifact_sha256")
    if (
        not isinstance(files, dict)
        or not expected.issubset(files)
        or not isinstance(hashes, dict)
    ):
        return None
    try:
        if any(
            not Path(value).is_file() or _sha256(Path(value)) != hashes.get(role)
            for role, value in files.items()
        ):
            return None
    except (OSError, TypeError, ValueError):
        return None
    events_path = path.parent / "events.jsonl"
    if not events_path.is_file() or _sha256(events_path) != result.get("events_sha256"):
        return None
    demand = _read_package_manifest(files.get("assessment_package")).get(
        "reference_demand"
    )
    if not isinstance(demand, dict) or demand.get("passed") is not True:
        return None
    result["generation_passed"] = True
    result["reference_demand_passed"] = True
    return result


def _process_failure_message(
    return_code: int,
    timed_out: bool,
    stderr: str,
) -> str:
    if timed_out:
        return "backend timed out"
    if return_code < 0:
        signal_number = -return_code
        try:
            signal_name = signal.Signals(signal_number).name
        except ValueError:
            signal_name = "unknown signal"
        return f"backend terminated by signal {signal_name} ({signal_number})"
    detail = next(
        (line.strip() for line in reversed(stderr.splitlines()) if line.strip()), ""
    )
    if detail:
        return f"backend exited with status {return_code}: {detail}"
    return f"backend exited with status {return_code}"


def _write_qualification_manifest(
    *,
    job: MatrixJob,
    result: dict[str, Any],
    result_path: Path,
    run_dir: Path,
    output_root: Path,
) -> Path:
    package = _read_package_manifest(result.get("files", {}).get("package_manifest"))
    inputs = package.get("inputs", {})
    generator = package.get("generator", {})
    backend = package.get("backend", {})
    passed = bool(result["passed"])
    running = result.get("status") == "running"
    generation_passed = bool(result.get("generation_passed", passed))
    artifacts = [
        ArtifactEvidence.from_path(role, Path(path))
        for role, path in result.get("files", {}).items()
        if Path(path).is_file()
    ]
    events_path = run_dir / "events.jsonl"
    evidence = [
        EvidenceRecord(
            gate="generation",
            path=str(events_path.relative_to(output_root)),
            sha256=_sha256(events_path),
            reviewer_identity_class="automation",
        )
    ]
    unavailable = "not-recorded"
    manifest = QualificationManifest(
        generator_id=job.family_id,
        paper_id=job.paper,
        seed=int(result["seed"]),
        model=ModelIdentity(
            provider=result.get("provider"),
            name=result.get("model"),
            digest=result.get("model_digest"),
        ),
        versions=VersionIdentity(
            contract=str(inputs.get("assessment_schema", unavailable)),
            blueprint=str(
                inputs.get(
                    "blueprint_version",
                    f"{job.family_id}:paper-{job.paper}:{generator.get('version') or unavailable}",
                )
            ),
            prompt=str(inputs.get("prompt_version", unavailable)),
            syllabus=str(inputs.get("syllabus_sha256", unavailable)),
            renderer=str(inputs.get("layout_profile_sha256", unavailable)),
        ),
        artifacts=artifacts,
        gate_results={
            "generation": GateState.NOT_RUN
            if running
            else GateState.PASSED
            if generation_passed
            else GateState.FAILED,
            "pdf": GateState.NOT_RUN
            if running
            else GateState.PASSED
            if generation_passed
            else GateState.FAILED,
            "reference_demand": (
                GateState.NOT_RUN
                if running
                else GateState.PASSED
                if result.get("reference_demand_passed")
                else GateState.FAILED
            ),
            "visual": GateState.NOT_RUN,
            "expert_review": GateState.NOT_RUN,
            "student_calibration": GateState.NOT_RUN,
        },
        evidence=evidence,
        reviewer_identity_class="automation",
        tool_versions={
            "live-generation-matrix": "2",
            "paper-creator-backend": str(backend.get("version", BACKEND_VERSION)),
        },
        created_at=datetime.now(UTC),
    )
    path = result_path.with_name("qualification-manifest.json")
    manifest.save(path)
    return path


def _write_run_qualification_manifest(
    *,
    output_root: Path,
    report: dict[str, Any],
    model: str | None,
    provider: str | None,
    base_seed: int,
) -> Path:
    paper_manifests = []
    for result in report["results"]:
        value = result.get("qualification_manifest")
        if not value:
            continue
        path = Path(str(value))
        if path.is_file():
            paper_manifests.append(
                {
                    "id": result["id"],
                    "path": str(path.relative_to(output_root)),
                    "sha256": _sha256(path),
                }
            )
    payload = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "base_seed": base_seed,
        "model": model,
        "provider": provider,
        "summary": report["summary"],
        "complete": report["complete"],
        "expected_jobs": report["expected_jobs"],
        "paper_manifests": paper_manifests,
    }
    path = output_root / "qualification-run-manifest.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _read_package_manifest(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(Path(str(value)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate every advertised paper through the app backend."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=default_ollama_model())
    parser.add_argument(
        "--provider",
        choices=("ollama", "openai", "anthropic", "apple"),
        default="ollama",
    )
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--seed", type=int, default=26_080_100)
    parser.add_argument("--timeout-seconds", type=int, default=3_600)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--backend-executable",
        type=Path,
        help="Use a packaged PaperCreatorBackend instead of bridge.py.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="SUBJECT:PAPER",
        help="Run only a specific registry job; may be repeated.",
    )
    args = parser.parse_args(argv)
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    jobs = matrix_jobs(registry)
    if args.only:
        selected = set(args.only)
        jobs = [job for job in jobs if job.id in selected]
        unknown = selected - {job.id for job in jobs}
        if unknown:
            parser.error("unknown matrix job(s): " + ", ".join(sorted(unknown)))
    command_prefix = (
        [str(args.backend_executable.resolve())]
        if args.backend_executable
        else [sys.executable, str(ROOT / "bridge.py")]
    )
    report = run_matrix(
        jobs,
        output_root=args.output.resolve(),
        command_prefix=command_prefix,
        model=args.model,
        provider=args.provider,
        ollama_url=args.ollama_url,
        base_seed=args.seed,
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
        resume=args.resume,
    )
    return 0 if report["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
