"""Experimental V34: three retained families and one structurally new paper.

Source reconstruction binds complete prompts, answers, credit and materials.
This checks integrity, not educational equivalence or learner timing. The
public route stays on V32 until the new paper passes its release checks.
"""

import json
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from Backend.Core.education_context import NSI_2027, NSI_CONTEXT
from Backend.Core.france import (
    database_curriculum_prose,
    loan_exercise,
    postfix_exercise,
    round_robin_exercise,
    system_case_prose,
    tree_case_prose,
)
from Backend.Core.france.nsi import LANGUAGE_RUBRIC_2027, NSIExercise
from Backend.Core.france.print_policy import V34_PRINT_POLICY
from Backend.Core.france.source_identity import implementation_identity
from Backend.Core.france.synthesized_pipeline import _references
from Backend.Core.scoped_references import ReferenceIndex

VERSION = "fr-nsi-written-2027-v34"
FAMILY_COUNT = 4
FAMILIES = (
    "rank-sensors-routing",
    "expression-bookings-locks",
    "prefix-stock-delivery",
    "postfix-loans-scheduling",
)


def _source(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("V34 requires a signed 64-bit integer seed")
    family = seed % FAMILY_COUNT
    source_seed = seed - (seed - 270100 - family) % 3 if family < 3 else seed
    if source_seed < -(2**63):
        source_seed += 3
    modules = (
        (tree_case_prose, database_curriculum_prose, system_case_prose)
        if family < 3
        else (postfix_exercise, loan_exercise, round_robin_exercise)
    )
    return (
        family,
        source_seed,
        [module.render_case(source_seed, total="6") for module in modules],
    )


def _task(exercise):
    return dict(
        topics=exercise["topics"],
        query=" ".join(exercise["topics"]) + " " + exercise["title"],
        minutes=exercise["minutes"],
        technical_points=exercise["target_points"],
        required_material_kind="table",
        required_curriculum_codes=sorted(
            {code for q in exercise["questions"] for code in q["curriculum_codes"]}
        ),
        archetype_id={
            "1": "graph-and-tree",
            "2": "database-and-debugging",
            "3": "network-and-systems",
        }[exercise["id"]],
        scenario_brief=exercise["context"],
        part_briefs=[
            "A : interpréter les sources.",
            "B : construire, tracer et justifier.",
        ],
        question_blueprint=[
            dict(
                id=q["id"],
                points=q["points"],
                estimated_minutes=q["estimated_minutes"],
                operation=q["operation"],
                difficulty=q["difficulty"],
                required_curriculum_code=q["curriculum_codes"][0],
                part_id="A" if i < 4 else "B",
            )
            for i, q in enumerate(exercise["questions"])
        ],
    )


def _catalogue():
    from Backend.Core.france.pipeline import digest

    root = Path(__file__).parent
    names = (
        "extended_pipeline.py",
        "loan_case.py",
        "loan_exercise.py",
        "round_robin_case.py",
        "round_robin_exercise.py",
        "postfix_exercise.py",
        "expression_synthesis.py",
        "expression_stack.py",
        "tree_case_prose.py",
        "tree_case_families.py",
        "database_case_prose.py",
        "database_curriculum_prose.py",
        "database_case_families.py",
        "system_case_prose.py",
        "system_case_families.py",
        "nsi.py",
    )
    return digest(
        {name: sha256((root / name).read_bytes()).hexdigest() for name in names}
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
    if (
        type(history) is not list
        or len(history) > 20
        or any(
            type(text) is not str or not text.strip() or len(text) > 100_000
            for text in history
        )
    ):
        raise ValueError("Invalid originality history")
    tasks = [_task(exercise) for exercise in raw_exercises]
    identity = dict(
        assessment=asdict(NSI_2027),
        prompt_version=VERSION,
        print_policy=V34_PRINT_POLICY,
        seed=seed,
        implementation_sha256=implementation_identity(),
        provider="application-owned",
        model="app-owned-v34",
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
        raise ValueError("Invalid V34 paper structure")
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
            raise ValueError("V34 package does not replay exactly")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed V34 package") from error
    return {
        "structural_checks": "passed",
        "teacher_review": "not_run",
        "empirical_calibration": "not_run",
    }


def generate(*, index_path, seed, checkpoint, progress=None, previous_texts=None):
    from Backend.Core.france.pipeline import atomic_json, digest

    _, _, exercises = _source(seed)
    references = []
    with ReferenceIndex(index_path, read_only=True) as index:
        for exercise in exercises:
            hits = []
            for category in ("programme", "official_paper"):
                hits.extend(
                    index.retrieve(
                        NSI_CONTEXT,
                        NSI_2027.curriculum_version,
                        _task(exercise)["query"],
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
            or type(state["failures"]) is not list
            or any(
                type(f) is not dict
                or set(f) != {"error", "cancelled"}
                or type(f["error"]) is not str
                or type(f["cancelled"]) is not bool
                for f in state["failures"]
            )
        ):
            raise ValueError("V34 checkpoint identity mismatch")
        if state["package"] is not None:
            validate(state["package"])
            if digest(state["package"]) != digest(_build(seed, references, history)):
                raise ValueError("V34 checkpoint belongs to another request")
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
