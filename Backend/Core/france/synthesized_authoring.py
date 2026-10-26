"""Exact experimental exercise replay before production integration.

This does not grant publication: scoped reference validation, originality,
whole-assessment validation and printed-PDF checks remain separate gates.
"""

from hashlib import sha256
from pathlib import Path

from Backend.Core.france import expression_exercise, postfix_exercise
from Backend.Core.france.database_depth_authoring import _hash
from Backend.Core.france.expression_synthesis import build_case

VERSION = "fr-nsi-synthesized-authoring-v2"
FAMILIES = {"recursive": expression_exercise, "postfix": postfix_exercise}


def catalogue_digest():
    root = Path(__file__).parent
    return _hash(
        {
            name: sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "synthesized_authoring.py",
                "expression_exercise.py",
                "expression_synthesis.py",
                "expression_stack.py",
                "postfix_exercise.py",
                "tree_case_families.py",
                "database_case_prose.py",
                "database_depth_authoring.py",
                "nsi.py",
            )
        }
    )


def blueprint(family, seed, *, total="6"):
    if type(family) is not str or family not in FAMILIES:
        raise ValueError("Unknown synthesized exercise family")
    raw = FAMILIES[family].render_case(seed, total=total)
    return dict(
        topics=raw["topics"],
        query=(
            "piles notation postfixée compilation arbres récursivité "
            if family == "postfix"
            else "arbres expressions récursivité dépendances "
        )
        + raw["title"],
        minutes=raw["minutes"],
        technical_points=total,
        required_material_kind="table",
        required_curriculum_codes=sorted(
            {c for q in raw["questions"] for c in q["curriculum_codes"]}
        ),
        archetype_id="graph-and-tree",
        scenario_brief=raw["context"],
        part_briefs=[
            "A : interpréter, tracer et diagnostiquer le calcul.",
            "B : construire des algorithmes et justifier leur fonctionnement.",
        ],
        question_blueprint=[
            dict(
                id=q["id"],
                points=q["points"],
                estimated_minutes=q["estimated_minutes"],
                operation=q["operation"],
                difficulty=q["difficulty"],
                required_curriculum_code=q["curriculum_codes"][0],
                part_id="A" if i < 6 else "B",
            )
            for i, q in enumerate(raw["questions"])
        ],
    )


def author(family, seed, *, references, total="6", task=None):
    """Generate a complete checked exercise and deterministic provenance."""
    if type(family) is not str or family not in FAMILIES:
        raise ValueError("Unknown synthesized exercise family")
    if type(references) is not list or any(type(r) is not dict for r in references):
        raise ValueError("References must be a list of source records")
    case = build_case(seed)
    module = FAMILIES[family]
    raw = module.render_case(seed, total=total)
    try:
        expected_task = blueprint(family, seed, total=total)
        if task is not None and (
            type(task) is not dict or _hash(task) != _hash(expected_task)
        ):
            raise ValueError("Synthesized exercise blueprint mismatch")
        evidence = dict(
            version=VERSION,
            family=family,
            seed=seed,
            origin="application_owned",
            model_used=False,
            prose_version=module.VERSION,
            case_sha256=case["sha256"],
            catalogue_sha256=catalogue_digest(),
            reference_sha256=_hash(references),
            candidate_sha256=_hash(raw),
            task_sha256=_hash(expected_task),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Authoring data must be canonically serializable") from exc
    return raw, evidence


def replay(family, seed, references, candidate, evidence, *, total="6", task=None):
    """Recompute from source; an attacker-rehashed candidate is still refused."""
    raw, expected = author(family, seed, references=references, total=total, task=task)
    try:
        matches = (
            type(candidate) is dict
            and type(evidence) is dict
            and _hash(candidate) == _hash(raw)
            and _hash(evidence) == _hash(expected)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Malformed synthesized replay data") from exc
    if not matches:
        raise ValueError("Synthesized candidate or provenance does not replay")
    return raw
