"""Experimental V33 whole-assessment path; V32 remains the public default.

Every package is reconstructed from app-owned source, including complete
questions, rubrics and provenance. This is not model authoring, publication
approval, or educational calibration. Originality remains an independent gate.
"""

import json
import re
from copy import deepcopy
from dataclasses import asdict
from urllib.parse import urlparse

from Backend.Core.education_context import NSI_2027, NSI_CONTEXT
from Backend.Core.france import (
    database_case_prose,
    synthesized_authoring,
    system_case_prose,
)
from Backend.Core.france.nsi import LANGUAGE_RUBRIC_2027, NSIExercise
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.france.verification import verify_contract
from Backend.Core.scoped_references import ReferenceHit, ReferenceIndex

VERSION = "fr-nsi-written-2027-v33"


def tasks_for_seed(seed):
    from Backend.Core.france.pipeline import _tasks_for_seed_v32

    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("V33 requires a signed 64-bit integer seed")
    family = "recursive" if seed % 2 == 0 else "postfix"
    tasks = _tasks_for_seed_v32(seed)
    tasks[0] = synthesized_authoring.blueprint(
        family, seed, total=tasks[0]["technical_points"]
    )
    return family, tasks


def _references(groups):
    if type(groups) is not list or len(groups) != 3:
        raise ValueError("V33 requires references for all three exercises")
    for group in groups:
        if type(group) is not list or not 2 <= len(group) <= 4:
            raise ValueError("Missing or excessive V33 reference evidence")
        categories = []
        for record in group:
            if type(record) is not dict:
                raise ValueError("Invalid reference record")
            try:
                hit = ReferenceHit(**record)
            except TypeError as error:
                raise ValueError("Invalid reference fields") from error
            if (
                any(
                    type(value) is not str or not value.strip()
                    for value in (
                        hit.source_id,
                        hit.source_sha256,
                        hit.text,
                        hit.url,
                        hit.category,
                    )
                )
                or not re.fullmatch(r"[a-f0-9]{64}", hit.source_sha256)
                or type(hit.page) is not int
                or hit.page < 1
                or urlparse(hit.url).scheme != "https"
                or not urlparse(hit.url).hostname
                or hit.category not in {"programme", "official_paper"}
            ):
                raise ValueError("Invalid V33 source provenance")
            categories.append(hit.category)
        if set(categories) != {"programme", "official_paper"}:
            raise ValueError("Programme and official-paper references are required")


def _build(seed, references, history):
    # Late import keeps the legacy pipeline independent of this experimental path.
    from Backend.Core.france.pipeline import (
        _check_exercise_plan,
        _originality,
        digest,
        exercise_candidate_text,
    )

    family, tasks = tasks_for_seed(seed)
    _references(references)
    if (
        type(history) is not list
        or len(history) > 20
        or any(
            type(text) is not str or not text.strip() or len(text) > 100_000
            for text in history
        )
    ):
        raise ValueError("Invalid originality history")
    identity = dict(
        assessment=asdict(NSI_2027),
        prompt_version=VERSION,
        seed=seed,
        implementation_sha256=implementation_identity(),
        provider="application-owned",
        model="app-owned-v33",
        model_digest=digest({"origin": "application_owned", "version": VERSION}),
        blueprint=tasks,
        synthesized_family=family,
        reference_digest=digest(references),
        originality_history_digest=digest(history),
    )
    first, provenance = synthesized_authoring.author(
        family,
        seed,
        references=references[0],
        total=tasks[0]["technical_points"],
        task=tasks[0],
    )
    raw_exercises = [first] + [
        module.render_case(seed, total=task["technical_points"])
        for module, task in zip(
            (database_case_prose, system_case_prose), tasks[1:], strict=True
        )
    ]
    exercises, evidence = [], []
    previous = list(history)
    for position, (raw, task, sources) in enumerate(
        zip(raw_exercises, tasks, references, strict=True)
    ):
        exercise = NSIExercise.model_validate(raw)
        _check_exercise_plan(exercise, task, str(position + 1))
        checks = (
            [
                synthesized_authoring.verify_question(
                    q, family, seed, total=task["technical_points"]
                )
                for q in raw["questions"]
            ]
            if position == 0
            else [verify_contract(q.verification) for q in exercise.questions]
        )
        if any(check["state"] != "passed" for check in checks):
            raise ValueError("V33 deterministic content check failed")
        normalized = exercise.model_dump(mode="json")
        evidence.append(
            dict(
                origin="application_owned",
                model_used=False,
                run_identity_sha256=digest(identity),
                exercise_sha256=digest(normalized),
                candidate_sha256=digest(raw),
                references=deepcopy(sources),
                deterministic=checks,
                originality=_originality(exercise, sources, previous),
                synthesized_evidence=provenance if position == 0 else None,
            )
        )
        exercises.append(normalized)
        previous.append(exercise_candidate_text(exercise))
    NSI_2027.validate_credit([e["target_points"] for e in exercises], "2")
    if [e["id"] for e in exercises] != ["1", "2", "3"] or sum(
        e["minutes"] for e in exercises
    ) != 210:
        raise ValueError("Invalid V33 assessment structure")
    return dict(
        schema_version=2,
        assessment_policy=NSI_2027.id,
        education_context=NSI_CONTEXT.to_dict(),
        identity=identity,
        exercises=exercises,
        evidence=evidence,
        content_sha256=digest(exercises),
        language_points="2",
        language_rubric=deepcopy(LANGUAGE_RUBRIC_2027),
        originality_history=deepcopy(history),
        status="unreviewed_draft",
        teacher_review={"state": "not_run"},
        empirical_calibration={"state": "not_run"},
        visual_calibration={"state": "not_run"},
    )


def validate(package):
    from Backend.Core.france.pipeline import digest

    try:
        expected = _build(
            package["identity"]["seed"],
            [item["references"] for item in package["evidence"]],
            package["originality_history"],
        )
        if digest(package) != digest(expected):
            raise ValueError("V33 package does not replay exactly")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed V33 package") from error
    return dict(
        structural_checks="passed",
        teacher_review="not_run",
        empirical_calibration="not_run",
    )


def generate(*, index_path, seed, checkpoint, progress=None, previous_texts=None):
    from Backend.Core.france.pipeline import atomic_json, digest

    _, tasks = tasks_for_seed(seed)
    emit = progress or (lambda _message: None)
    references = []
    with ReferenceIndex(index_path, read_only=True) as index:
        for task in tasks:
            hits = []
            for category in ("programme", "official_paper"):
                hits.extend(
                    index.retrieve(
                        NSI_CONTEXT,
                        NSI_2027.curriculum_version,
                        task["query"],
                        categories=(category,),
                        limit=2,
                    )
                )
            references.append([asdict(hit) for hit in hits])
    history = [] if previous_texts is None else previous_texts
    request = dict(
        version=VERSION,
        seed=seed,
        source=implementation_identity(),
        references=digest(references),
        history=digest(history),
    )
    state = dict(request=request, package=None, failures=[])
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if (
            type(state) is not dict
            or set(state) != {"request", "package", "failures"}
            or digest(state["request"]) != digest(request)
        ):
            raise ValueError("V33 checkpoint identity mismatch")
        if state["package"] is not None:
            validate(state["package"])
            if digest(state["package"]) != digest(_build(seed, references, history)):
                raise ValueError("V33 checkpoint belongs to another request")
            return state["package"]
    emit("Construction des exercices vérifiés, sans appel à un modèle.")
    try:
        package = _build(seed, references, history)
        validate(package)
    except (ValueError, TypeError, KeyboardInterrupt, InterruptedError) as error:
        state["failures"].append(
            dict(
                error=str(error),
                cancelled=isinstance(error, (KeyboardInterrupt, InterruptedError)),
            )
        )
        atomic_json(checkpoint, state)
        raise
    state["package"] = package
    atomic_json(checkpoint, state)
    return package
