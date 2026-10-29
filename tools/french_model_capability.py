"""Plan or explicitly run a small, pinned French authoring capability comparison."""

from __future__ import annotations

import argparse
import importlib
import io
import json
import re
import sqlite3
import sys
import time
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Core.france.source_identity import implementation_identity  # noqa: E402
from Backend.Core.france.verification import verify_contract  # noqa: E402
from Backend.Core.generation_requests import GenerationRequest  # noqa: E402
from Backend.Core.providers import HostedLLMClient, urllib_request  # noqa: E402
from tools.atomic_json import write_json_atomically  # noqa: E402
from tools.live_generation_matrix import _model_digest  # noqa: E402
from tools.live_process import run_backend  # noqa: E402


def plan(seeds: list[int], *, provider: str) -> list[dict]:
    if (
        provider not in {"ollama", "apple"}
        or not 1 <= len(seeds) <= 2
        or any(type(seed) is not int for seed in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError(
            "Choose one or two distinct integer seeds and a local provider."
        )
    jobs = []
    for index, seed in enumerate(seeds):
        modes = [False, True] if index % 2 == 0 else [True, False]
        if provider == "apple":
            # Its single-phase constrained decoder does not support a thinking
            # prelude. Do not claim that changing its template is equivalent.
            modes = [False]
        for thinking in modes:
            for kind, budget in [("known_logic", 2048), ("authoring", 14000)]:
                jobs.append(
                    {
                        "seed": seed,
                        "thinking": thinking,
                        "kind": kind,
                        "max_tokens": budget,
                    }
                )
    return jobs


def logic_request(seed: int) -> tuple[GenerationRequest, dict]:
    offset = seed % 7
    edges = [
        ["A", "B", 9 + offset],
        ["A", "C", 2 + offset],
        ["C", "B", 2],
        ["B", "D", 3],
        ["C", "D", 12 + offset],
    ]
    rows = [[1, "Lina", 30 + offset], [2, "Noé", 55 + offset], [3, "Lina", 70 + offset]]
    query = "SELECT nom FROM Commande WHERE total >= 50 ORDER BY id;"
    trace = f"valeurs = [2, 5, 1, {4 + offset}]\nr = 0\nfor x in valeurs:\n    if x > 2:\n        r = r + x * 2"
    # Independently compute the expected rows from fixed input, never from a
    # candidate's answer or model-supplied executable code.
    with sqlite3.connect(":memory:") as database:
        database.execute("CREATE TABLE Commande(id INTEGER, nom TEXT, total INTEGER)")
        database.executemany("INSERT INTO Commande VALUES (?, ?, ?)", rows)
        sql_names = [row[0] for row in database.execute(query)]
    expected = {
        "distance": 7 + offset,
        "sql_names": sql_names,
        "trace_value": sum(x * 2 for x in [2, 5, 1, 4 + offset] if x > 2),
    }
    assert verify_contract(
        {
            "kind": "shortest_path",
            "edges": edges,
            "directed": True,
            "start": "A",
            "end": "D",
            "expected": expected["distance"],
        }
    )["passed"]
    assert verify_contract(
        {
            "kind": "python_trace",
            "code": trace,
            "variable": "r",
            "expected": expected["trace_value"],
        }
    )["passed"]
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["distance", "sql_names", "trace_value"],
        "properties": {
            "distance": {"type": "integer", "minimum": 0, "maximum": 10000},
            "sql_names": {
                "type": "array",
                "maxItems": 10,
                "items": {"type": "string", "maxLength": 40},
            },
            "trace_value": {"type": "integer", "minimum": -10000, "maximum": 10000},
        },
    }
    prompt = (
        "Résous trois tâches indépendantes de NSI. Aucun corrigé n'est fourni. "
        "Retourne seulement les résultats dans le JSON demandé. "
        "distance : poids du plus court chemin dirigé de A à D dans les arêtes "
        + json.dumps(edges, ensure_ascii=False)
        + ". sql_names : liste ordonnée des noms retournés, sans supprimer les doublons. "
        "Commande(id INTEGER, nom TEXT, total INTEGER), lignes "
        + json.dumps(rows, ensure_ascii=False)
        + ", requête : "
        + query
        + " trace_value : valeur finale de r dans le programme suivant :\n"
        + trace
    )
    return GenerationRequest(
        prompt,
        "solver",
        schema,
        generation_seed=seed,
        temperature=0.2,
        output_budget=2048,
    ), expected


def check_logic(actual: dict, expected: dict) -> dict:
    checks = {
        key: type(actual.get(key)) is type(value) and actual.get(key) == value
        for key, value in expected.items()
    }
    return {
        "passed": set(actual) == set(expected) and all(checks.values()),
        "checks": checks,
        "expected": expected,
        "actual": actual,
    }


class ProbeClient(HostedLLMClient):
    """Probe-only thinking override; production provider defaults stay unchanged."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        thinking: bool,
        max_tokens: int,
        base_url: str = "http://localhost:11434",
    ):
        if provider == "apple" and thinking:
            raise ValueError(
                "The current MLX JSON decoder has no separate thinking phase."
            )
        super().__init__(provider=provider, model=model, api_key="", base_url=base_url)
        self.parallel_generation_workers = self.parallel_review_workers = 1
        self.thinking, self.max_tokens = thinking, max_tokens
        self.calls: list[dict] = []

    def generate_request(
        self, request: GenerationRequest, retries: int = 1
    ) -> dict[str, object]:
        # One measured attempt; do not conceal failures behind automatic repairs.
        return super().generate_request(request, retries=1)

    def _ollama(self, prompt: str, **kwargs) -> dict:
        def capture(url, data, headers, **_kwargs):
            payload = json.loads(data)
            payload["think"] = self.thinking
            encoded = json.dumps(payload, ensure_ascii=False).encode()
            record = {
                "request": payload,
                "shared_output_token_budget": self.max_tokens,
                "thinking_token_budget": None,
                "thinking_token_count": None,
            }
            self.calls.append(record)
            started = time.monotonic()
            try:
                with urllib_request(url, encoded, headers, attempts=1) as response:
                    raw = response.read(2_097_153)
                record["response_sha256"] = sha256(raw).hexdigest()
                if len(raw) > 2_097_152:
                    raise ValueError("Probe response exceeds 2 MiB.")
                decoded = json.loads(raw)
                record["response"] = decoded
                message = decoded.get("message", {})
                record["thinking_characters"] = len(message.get("thinking", ""))
                record["content_characters"] = len(message.get("content", ""))
                record["total_generated_tokens"] = decoded.get("eval_count")
                record["completion_reason"] = decoded.get("done_reason")
                return io.BytesIO(raw)
            except Exception as error:
                record["transport_error"] = str(error)
                raise
            finally:
                record["elapsed_seconds"] = time.monotonic() - started

        kwargs.update(
            request_function=capture, strict_json=True, output_budget=self.max_tokens
        )
        return super()._ollama(prompt, **kwargs)


def _authoring_api():
    return importlib.import_module("Backend.Core.france.llm_pipeline")


def execute_one(job: dict, run_dir: Path) -> dict:
    client = ProbeClient(
        provider=job["provider"],
        model=job["model"],
        thinking=job["thinking"],
        max_tokens=job["max_tokens"],
        base_url=job["ollama_url"],
    )
    result = {
        "job": job,
        "capability_only": True,
        "teacher_review": "not_run",
        "empirical_calibration": "not_run",
    }
    try:
        if job["kind"] == "known_logic":
            request, expected = logic_request(job["seed"])
        else:
            api = _authoring_api()
            request = api.exercise_request("1", job["seed"], [])
        write_json_atomically(
            run_dir / "request.json",
            {
                "prompt": request.prompt,
                "schema": request.schema,
                "effective_seed": request.seed,
                "temperature": request.temperature,
                "requested_output_budget": request.output_budget,
            },
        )
        candidate = client.generate_request(request)
        write_json_atomically(run_dir / "candidate.json", candidate)
        if job["kind"] == "known_logic":
            result.update(check_logic(candidate, expected))
        else:
            exercise = api.validate_authored_exercise(candidate, "1")
            checks = [
                {"question": question.id, **verify_contract(question.verification)}
                for question in exercise.questions
            ]
            checked = sum(check["state"] == "passed" for check in checks)
            unresolved = sum(check["state"] == "unresolved" for check in checks)
            result.update(
                {
                    "passed": checked > 0
                    and not any(check["state"] == "failed" for check in checks),
                    "supported_contracts_checked": checked,
                    "unresolved_contracts": unresolved,
                    "contract_checks": checks,
                    "requires_internal_question_review": True,
                    "exercise": exercise.model_dump(mode="json"),
                }
            )
    except Exception as error:
        result.update(
            {"passed": False, "error_type": type(error).__name__, "error": str(error)}
        )
    finally:
        result["provider_calls"] = client.calls
        write_json_atomically(run_dir / "result.json", result)
    return result


def run_plan(
    *,
    model: str,
    expected_digest: str,
    provider: str,
    output: Path,
    seeds: list[int],
    ollama_url: str,
    timeout: int,
) -> dict:
    if output.exists():
        raise FileExistsError("Capability evidence exists; choose a fresh directory.")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise ValueError("A pinned 64-character model digest is required.")
    if not 10 <= timeout <= 1200:
        raise ValueError(
            "Each capability call needs a timeout from 10 to 1200 seconds."
        )
    if _model_digest(provider, model, ollama_url) != expected_digest:
        raise ValueError("Installed model digest does not match the requested model.")
    jobs = plan(seeds, provider=provider)
    identity = implementation_identity()
    output.mkdir(parents=True, mode=0o700)
    report = {
        "capability_only": True,
        "model": model,
        "model_digest": expected_digest,
        "implementation_sha256": identity,
        "harness_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_scope": "none_capability_only",
        "results": [],
    }
    write_json_atomically(output / "summary.json", report)
    for index, specification in enumerate(jobs):
        if (
            implementation_identity() != identity
            or _model_digest(provider, model, ollama_url) != expected_digest
        ):
            raise ValueError(
                "Model or implementation changed; retained results cannot be mixed."
            )
        directory = (
            output
            / f"{index + 1:02d}-{specification['seed']}-{specification['kind']}-think-{int(specification['thinking'])}"
        )
        directory.mkdir(mode=0o700)
        job = {
            **specification,
            "provider": provider,
            "model": model,
            "ollama_url": ollama_url,
            "implementation_sha256": identity,
            "model_digest": expected_digest,
        }
        write_json_atomically(directory / "job.json", job)
        execution = run_backend(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                str(directory / "job.json"),
            ],
            cwd=ROOT,
            run_dir=directory,
            timeout_seconds=timeout,
        )
        path = directory / "result.json"
        result = (
            json.loads(path.read_text())
            if path.exists()
            else {"passed": False, "error": "No complete probe result."}
        )
        result.update(return_code=execution.return_code, timed_out=execution.timed_out)
        if (
            implementation_identity() != identity
            or _model_digest(provider, model, ollama_url) != expected_digest
        ):
            result.update(
                passed=False, error="Source or model changed during the probe."
            )
        if execution.return_code != 0 or execution.timed_out:
            result["passed"] = False
        report["results"].append(result)
        write_json_atomically(output / "summary.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--provider", choices=["ollama", "apple"], default="ollama")
    parser.add_argument("--expected-model-digest")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seeds", default="270100,270101")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        job = json.loads(args.worker.read_text())
        return 0 if execute_one(job, args.worker.parent)["passed"] else 1
    if not args.model:
        parser.error("--model is required")
    seeds = [int(value) for value in args.seeds.split(",")]
    if not args.run:
        print(
            json.dumps(
                {
                    "capability_only": True,
                    "inference_started": False,
                    "jobs": plan(seeds, provider=args.provider),
                },
                indent=2,
            )
        )
        return 0
    if args.output is None or args.expected_model_digest is None:
        parser.error("--run requires --output and --expected-model-digest")
    report = run_plan(
        model=args.model,
        expected_digest=args.expected_model_digest,
        provider=args.provider,
        output=args.output,
        seeds=seeds,
        ollama_url=args.ollama_url,
        timeout=args.timeout_seconds,
    )
    return 0 if all(result["passed"] for result in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
