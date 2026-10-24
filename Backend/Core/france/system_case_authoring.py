"""App-owned E3 whole-case provenance, with strict checkpoint replay."""

import json
from hashlib import sha256
from pathlib import Path

from Backend.Core.france.database_depth_authoring import _hash, _save
from Backend.Core.france.system_case_families import build_case
from Backend.Core.france.system_case_prose import VERSION, case_task, render_case


def catalogue_digest():
    root = Path(__file__).parent
    return _hash(
        {
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "system_case_authoring.py",
                "system_case_families.py",
                "system_case_prose.py",
                "database_case_prose.py",
            )
        }
    )


def _build(task, references, run_identity):
    if (
        not isinstance(run_identity, dict)
        or run_identity.get("prompt_version") != "fr-nsi-written-2027-v32"
    ):
        raise ValueError("Whole system authoring requires a V32 run identity")
    if any(
        not isinstance(run_identity.get(k), str) or not run_identity[k]
        for k in ("provider", "model_digest", "implementation_sha256")
    ):
        raise ValueError("Incomplete whole system run identity")
    if not isinstance(task, dict) or not isinstance(references, list):
        raise ValueError("Malformed whole system authoring inputs")
    seed = run_identity.get("seed")
    case = build_case(seed)
    total = task.get("technical_points")
    if _hash(task) != _hash(case_task(seed, total)):
        raise ValueError("Whole system blueprint mismatch")
    raw = render_case(seed, total=total)
    return raw, dict(
        origin="application_owned",
        model_used=False,
        prose_contract_version=VERSION,
        catalogue_sha256=catalogue_digest(),
        case_sha256=case["sha256"],
        task_sha256=_hash(task),
        reference_sha256=_hash(references),
        run_identity_sha256=_hash(run_identity),
        candidate_sha256=_hash(raw),
    )


def replay_case(task, references, evidence, *, run_identity):
    raw, expected = _build(task, references, run_identity)
    if not isinstance(evidence, dict) or _hash(evidence) != _hash(expected):
        raise ValueError("Whole system replay evidence mismatch")
    return raw


def author_case(task, references, path, *, run_identity):
    raw, evidence = _build(task, references, run_identity)
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        return replay_case(task, references, saved, run_identity=run_identity), saved
    _save(path, evidence)
    return raw, evidence
