"""Five whole-paper families with immutable V34 source reuse.

Reconstruction certifies source integrity and retained-history screening,
not difficulty or learner timing.
"""

import json
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from Backend.Core.education_context import NSI_2027, NSI_CONTEXT
from Backend.Core.france import (
    allocation_exercise,
    channel_exercise,
    directory_exercise,
)
from Backend.Core.france import extended_pipeline as retained
from Backend.Core.france.nsi import LANGUAGE_RUBRIC_2027, NSIExercise
from Backend.Core.france.print_policy import V35_PRINT_POLICY
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.france.synthesized_pipeline import _references
from Backend.Core.scoped_references import ReferenceIndex

VERSION = "fr-nsi-written-2027-v35"
PRINT_POLICY = V35_PRINT_POLICY
FAMILIES = (*retained.FAMILIES, "directories-eligibility-channel")
FAMILY_COUNT = len(FAMILIES)
FamilyCatalogueExhausted = retained.FamilyCatalogueExhausted


def _family_seeds(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("V35 requires a signed 64-bit integer seed")
    candidates = []
    for offset in range(FAMILY_COUNT):
        family = (seed % FAMILY_COUNT + offset) % FAMILY_COUNT
        candidate = seed + (family - seed % FAMILY_COUNT) % FAMILY_COUNT
        # Five does not divide the signed range. Wrapping modulo 2**64 would
        # repeat a family near the boundary instead of trying all five once.
        if candidate >= 2**63:
            candidate -= FAMILY_COUNT
        candidates.append(candidate)
    return candidates


def _source(seed):
    _family_seeds(seed)
    family = seed % FAMILY_COUNT
    if family < retained.FAMILY_COUNT:
        legacy_seed = seed - (seed - family) % retained.FAMILY_COUNT
        if legacy_seed < -(2**63):
            legacy_seed += retained.FAMILY_COUNT
        _, source_seed, exercises = retained._source(legacy_seed)
        return family, source_seed, exercises
    return (
        family,
        seed,
        [
            module.render_case(seed)
            for module in (directory_exercise, allocation_exercise, channel_exercise)
        ],
    )


def _task(exercise, family):
    task = retained._task(exercise)
    if family == 4:
        first_b = {"1": 5, "2": 6, "3": 5}[exercise["id"]]
        for index, planned in enumerate(task["question_blueprint"]):
            planned["part_id"] = (
                "C"
                if exercise["id"] == "3" and index >= 10
                else "A"
                if index < first_b
                else "B"
            )
        if exercise["id"] == "3":
            task["part_briefs"].append(
                "C : distinguer contenu et sécurité des terminaux."
            )
    return task


def choose_fresh_seed(seed, *, previous_texts=None):
    from Backend.Core.france.originality import SimilarityRejected, screen_originality
    from Backend.Core.france.pipeline import exercise_candidate_text

    candidates = _family_seeds(seed)
    history = [] if previous_texts is None else previous_texts
    retained._validate_history(history)
    for candidate in candidates:
        try:
            for raw in _source(candidate)[2]:
                screen_originality(
                    exercise_candidate_text(NSIExercise.model_validate(raw)),
                    [],
                    previous_texts=history,
                )
        except SimilarityRejected:
            continue
        return candidate
    raise FamilyCatalogueExhausted(
        "Les cinq familles disponibles sont trop proches des sujets précédents. "
        "Aucun nouveau sujet n'a été créé."
    )


def _catalogue():
    from Backend.Core.france.pipeline import digest

    root = Path(__file__).parent
    names = (
        "expanded_pipeline.py",
        "directory_case.py",
        "directory_exercise.py",
        "allocation_case.py",
        "allocation_exercise.py",
        "channel_case.py",
        "channel_exercise.py",
    )
    return digest(
        {
            "retained_v34": retained._catalogue(),
            "expanded": {
                name: sha256((root / name).read_bytes()).hexdigest() for name in names
            },
        }
    )


def _build(seed, references, history):
    from Backend.Core.france.pipeline import (
        _check_exercise_plan,
        _originality,
        digest,
        exercise_candidate_text,
    )

    family, source_seed, raw_exercises = _source(seed)
    _references(references)
    retained._validate_history(history)
    tasks = [_task(exercise, family) for exercise in raw_exercises]
    identity = dict(
        assessment=asdict(NSI_2027),
        prompt_version=VERSION,
        print_policy=PRINT_POLICY,
        seed=seed,
        implementation_sha256=implementation_identity(),
        provider="application-owned",
        model="app-owned-v35",
        model_digest=digest({"origin": "application_owned", "version": VERSION}),
        blueprint=tasks,
        family=family,
        family_id=FAMILIES[family],
        source_seed=source_seed,
        catalogue_sha256=_catalogue(),
        reference_digest=digest(references),
        originality_history_digest=digest(history),
    )
    exercises, evidence, previous = [], [], list(history)
    for raw, task, sources in zip(raw_exercises, tasks, references, strict=True):
        exercise = NSIExercise.model_validate(raw)
        _check_exercise_plan(exercise, task, exercise.id)
        normalized = exercise.model_dump(mode="json")
        evidence.append(
            dict(
                origin="application_owned",
                model_used=False,
                run_identity_sha256=digest(identity),
                exercise_sha256=digest(normalized),
                candidate_sha256=digest(raw),
                references=deepcopy(sources),
                deterministic=[
                    dict(
                        state="passed",
                        scope="canonical_question_replay",
                        question_id=q["id"],
                        question_sha256=digest(q),
                    )
                    for q in raw["questions"]
                ],
                originality=_originality(exercise, sources, previous),
            )
        )
        exercises.append(normalized)
        previous.append(exercise_candidate_text(exercise))
    NSI_2027.validate_credit([e["target_points"] for e in exercises], "2")
    if [e["id"] for e in exercises] != ["1", "2", "3"] or sum(
        e["minutes"] for e in exercises
    ) != 210:
        raise ValueError("Invalid V35 paper structure")
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
            [e["references"] for e in package["evidence"]],
            package["originality_history"],
        )
        if digest(package) != digest(expected):
            raise ValueError("V35 package does not replay exactly")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed V35 package") from error
    return dict(
        structural_checks="passed",
        teacher_review="not_run",
        empirical_calibration="not_run",
    )


def generate(*, index_path, seed, checkpoint, progress=None, previous_texts=None):
    from Backend.Core.france.pipeline import atomic_json, digest

    family, _, exercises = _source(seed)
    history = [] if previous_texts is None else previous_texts
    retained._validate_history(history)
    references = []
    with ReferenceIndex(index_path, read_only=True) as index:
        for exercise in exercises:
            hits = []
            for category in ("programme", "official_paper"):
                hits.extend(
                    index.retrieve(
                        NSI_CONTEXT,
                        NSI_2027.curriculum_version,
                        _task(exercise, family)["query"],
                        categories=(category,),
                        limit=2,
                    )
                )
            references.append([asdict(hit) for hit in hits])
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
            or type(state["failures"]) is not list
            or any(
                type(f) is not dict
                or set(f) != {"error", "cancelled"}
                or type(f["error"]) is not str
                or type(f["cancelled"]) is not bool
                for f in state["failures"]
            )
        ):
            raise ValueError("V35 checkpoint identity mismatch")
        if state["package"] is not None:
            validate(state["package"])
            if digest(state["package"]) != digest(_build(seed, references, history)):
                raise ValueError("V35 checkpoint belongs to another request")
            return state["package"]
    (progress or (lambda _message: None))(
        "Construction des exercices vérifiés, sans appel à un modèle."
    )
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
