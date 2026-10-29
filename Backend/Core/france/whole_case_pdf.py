# Compare complete printed French exercises with their verified package.
#
# This is a content-integrity gate, not educational or visual calibration. It
# checks the entire exercise stream in order, so finding a few keywords is
# not enough. Whitespace and Markdown fences are presentation, not source facts.

import re
import unicodedata
from decimal import Decimal
from pathlib import Path

import pymupdf

from Backend.Core.france.expanded_pipeline import VERSION as EXPANDED_VERSION
from Backend.Core.france.extended_pipeline import VERSION as EXTENDED_VERSION
from Backend.Core.france.nsi import (
    LANGUAGE_RUBRIC_2027,
    NSIExercise,
    NSITableMaterial,
    NSIWeightedGraphMaterial,
)
from Backend.Core.france.pipeline import (
    CONTROLLED_WHOLE_CASE_PROMPT_VERSION,
    validate_package,
)
from Backend.Core.france.print_policy import (
    INTERNAL_REVIEW_POLICIES,
    V34_CORRECTION_GUIDANCE,
    V34_CREDIT_NOTICE,
    V34_FOOTER,
    V34_REVIEW_NOTICE,
)
from Backend.Core.france.synthesized_pipeline import VERSION as SYNTHESIZED_VERSION
from Backend.Core.legacy_migration import LEGACY_FRENCH_FOOTER


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


def _prose(text: str) -> str:
    return re.sub(r"```(?:python|sql)?", "", text)


def _heading(exercise: NSIExercise) -> str:
    points = exercise.target_points.replace(".", ",")
    return f"Exercice {exercise.id} ({points} points)"


def _expected_preface(correction: bool, *, print_policy: str | None = None) -> str:
    parts = [
        "BACCALAURÉAT GÉNÉRAL",
        "ÉPREUVE D’ENSEIGNEMENT DE SPÉCIALITÉ",
        "SESSION 2027",
        "NUMÉRIQUE ET SCIENCES INFORMATIQUES",
        "CORRIGÉ PROPOSÉ ET BARÈME INDICATIF"
        if correction
        else (
            "SUJET D’ENTRAÎNEMENT - NON OFFICIEL"
            if print_policy in INTERNAL_REVIEW_POLICIES
            else "SUJET D’ENTRAÎNEMENT — NON OFFICIEL"
        ),
        "Durée de l’épreuve : 3 heures 30",
        "Document de travail pour la relecture pédagogique."
        if correction
        else "L’usage de la calculatrice n’est pas autorisé.",
        "Réponses et crédits à vérifier avant toute évaluation."
        if correction
        else "Dès que ce sujet vous est remis, assurez-vous qu’il est complet.",
        V34_REVIEW_NOTICE
        if print_policy in INTERNAL_REVIEW_POLICIES
        else "Ce document doit être relu par un enseignant avant toute utilisation.",
        "Évaluation : 18 points techniques et 2 points pour la maîtrise de la langue.",
        "Trois exercices indépendants - corrigé proposé."
        if correction
        else "Le sujet est composé de trois exercices indépendants.",
        (
            V34_CREDIT_NOTICE
            if print_policy in INTERNAL_REVIEW_POLICIES
            else "Barème et variantes à confirmer par un enseignant."
        )
        if correction
        else "Le candidat traite les trois exercices.",
    ]
    if not correction:
        parts.extend(
            [
                "Rédigez vos réponses sur votre copie.",
                "Recopiez et complétez les tableaux demandés.",
            ]
        )
    else:
        parts.extend(
            [
                "Consignes générales de correction",
                V34_CORRECTION_GUIDANCE
                if print_policy in INTERNAL_REVIEW_POLICIES
                else "Barème indicatif : attribuer uniquement les crédits explicitement justifiés. Accepter une méthode équivalente correcte. Ne pas compter deux fois le même élément. Faire vérifier les réponses, variantes et cas limites par un enseignant avant toute utilisation évaluative.",
                "Maîtrise de la langue - 2 points sur l'ensemble de la copie",
                "Apprécier l'orthographe, la syntaxe, la précision du vocabulaire et l'organisation du raisonnement conformément à la grille nationale. La répartition détaillée entre ces dimensions n'est pas présentée comme officielle. Cette application ne note pas les copies des élèves.",
                "Appréciation globale",
                "Points indicatifs",
            ]
        )
        for band in LANGUAGE_RUBRIC_2027["bands"]:
            parts.extend(
                [
                    band["label"],
                    LANGUAGE_RUBRIC_2027["indicative_points"][band["id"]].replace(
                        ".", ","
                    ),
                ]
            )
        parts.append(
            "Profil indicatif du logiciel, non barème officiel : retenir une appréciation globale à partir des quatre dimensions officielles (orthographe, syntaxe, lexique et organisation du raisonnement)."
        )
    return _compact("\n".join(parts))


def _expected(
    exercise: NSIExercise, correction: bool, *, compact_correction: bool = False
) -> str:
    from Backend.Core.france.rendering import correction_prompt

    title = exercise.title.strip().rstrip(".")
    scope = (
        f"{title}."
        if title.lower().startswith("cet exercice")
        else f"Thème de l'exercice : « {title} »."
    )
    parts = [_heading(exercise), scope, _prose(exercise.context)]
    printed = set()
    for question in exercise.questions:
        for material in exercise.materials:
            if material.id not in question.material_ids or material.id in printed:
                continue
            if isinstance(material, NSIWeightedGraphMaterial):
                parts.extend(
                    [
                        material.title,
                        *[str(weight) for _, _, weight in material.edges],
                        *material.nodes,
                    ]
                )
                printed.add(material.id)
                continue
            if not isinstance(material, NSITableMaterial):
                raise ValueError("Type de document V32 non pris en charge")
            # The V32 publication layout suppresses internal E1/E3 identifiers.
            label = material.title
            if (
                exercise.id == "2"
                and material.id != "case_states"
                and material.title != material.id
            ):
                label += f" — {material.id}"
            parts.extend([label, *material.columns])
            for row in material.rows:
                parts.extend(row)
            printed.add(material.id)
        prompt = (
            correction_prompt(question.prompt)
            if correction and compact_correction
            else question.prompt
        )
        parts.extend([f"{question.id}.", _prose(prompt)])
        if correction:
            parts.extend(
                [
                    f"Réponse attendue — question {question.id}",
                    _prose(question.answer),
                    f"Barème indicatif — question {question.id}",
                ]
            )
            for marking in question.marking:
                suffix = "point" if Decimal(marking.points) <= 1 else "points"
                parts.extend(
                    [f"{marking.points.replace('.', ',')} {suffix}", marking.criterion]
                )
    if printed != {material.id for material in exercise.materials}:
        raise ValueError("Document V32 sans question associée")
    return _compact("\n".join(parts))


# Reject altered source, missing/extra content, or a swapped PDF role.
def validate_whole_case_pdf(path: Path, package: dict, *, correction: bool) -> None:
    if type(correction) is not bool:
        raise ValueError("Rôle du PDF invalide")
    validate_package(package)
    if package["identity"]["prompt_version"] not in {
        CONTROLLED_WHOLE_CASE_PROMPT_VERSION,
        SYNTHESIZED_VERSION,
        EXTENDED_VERSION,
        EXPANDED_VERSION,
    }:
        raise ValueError("Ce contrôle exige un sujet complet V32, V33, V34 ou V35")
    # Late import permits runtime to select this validator without a cycle.
    from Backend.Core.france.runtime import validate_pdf

    validate_pdf(path)
    exercises = [NSIExercise.model_validate(raw) for raw in package["exercises"]]
    print_policy = package["identity"].get("print_policy")
    footers = (
        {V34_FOOTER}
        if print_policy in INTERNAL_REVIEW_POLICIES
        else {
            LEGACY_FRENCH_FOOTER,
            "Keldin — entraînement non officiel — non relu",
        }
    )
    with pymupdf.open(path) as pdf:
        if package["identity"]["prompt_version"] == EXPANDED_VERSION:
            from Backend.Core.france.graph_pdf import validate_graph

            for exercise in exercises:
                for material in exercise.materials:
                    if isinstance(material, NSIWeightedGraphMaterial):
                        validate_graph(pdf, material)
        if any(
            abs(page.rect.width - 595.276) > 0.5 or abs(page.rect.height - 841.89) > 0.5
            for page in pdf
        ):
            raise ValueError("Toutes les pages du sujet V32 doivent être au format A4")
        for number, page in enumerate(pdf, 1):
            if package["identity"]["prompt_version"] in {
                EXTENDED_VERSION,
                EXPANDED_VERSION,
            }:
                body = page.get_text(clip=pymupdf.Rect(0, 0, page.rect.width, 760))
                if not body.strip():
                    raise ValueError(
                        f"Page {number} sans contenu dans le sujet vérifié"
                    )
            page_lines = [line.strip() for line in page.get_text().splitlines()]
            if sum(line in footers for line in page_lines) != 1:
                raise ValueError("Pied de page non officiel absent ou dupliqué")
            counters = [
                _compact(line)
                for line in page_lines
                if re.fullmatch(r"Page\s*:\s*\d+\s*/\s*\d+", line)
            ]
            if counters != [f"Page:{number}/{len(pdf)}"]:
                raise ValueError("Pagination du PDF incompatible avec ses pages")
        lines = [
            line.strip()
            for page in pdf
            for line in page.get_text().splitlines()
            if line.strip()
            and line.strip() not in footers
            and not re.fullmatch(r"Page\s*:\s*\d+\s*/\s*\d+", line.strip())
        ]
    text = _compact("\n".join(lines))
    headings = [_compact(_heading(exercise)) for exercise in exercises]
    if any(text.count(heading) != 1 for heading in headings):
        raise ValueError("En-têtes des exercices V32 absents ou dupliqués")
    positions = [text.index(heading) for heading in headings]
    if positions != sorted(positions):
        raise ValueError("Ordre des exercices V32 incorrect")
    if text[: positions[0]] != _expected_preface(correction, print_policy=print_policy):
        raise ValueError(
            "Couverture ou consignes V32 incompatibles avec le rôle du PDF"
        )
    for index, exercise in enumerate(exercises):
        end = positions[index + 1] if index + 1 < len(positions) else len(text)
        if text[positions[index] : end] != _expected(
            exercise,
            correction,
            compact_correction=package["identity"]["prompt_version"]
            in {EXTENDED_VERSION, EXPANDED_VERSION},
        ):
            raise ValueError(
                f"Contenu imprimé de l'exercice {exercise.id} incompatible avec le sujet vérifié"
            )
