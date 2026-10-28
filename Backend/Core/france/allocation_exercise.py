# Relational eligibility followed by a constrained recursive assignment.

import hashlib
import json
import re
from decimal import Decimal

from Backend.Core.france.allocation_case import (
    affecter,
    build_case,
    candidate_query,
    glouton,
)
from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-allocation-exercise-v1"


def render_case(seed):
    case = build_case(seed)
    digest = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
    items = [
        (
            "Partie A. Identifier la clé primaire de chaque relation et la clé étrangère. Une équipe peut-elle posséder deux habilitations différentes ? Justifier à partir de la clé composée.",
            "Equipe.id et Tache.id sont les clés primaires simples ; (Habilitation.equipe, Habilitation.domaine) est composée. Habilitation.equipe référence Equipe.id. Une équipe peut avoir plusieurs domaines, mais pas deux lignes identiques pour le même domaine.",
            [("0.25", "Les trois clés, la référence et la conséquence de la clé composée sont exactes.")], "analyse", "BDD-MODELE",
        ),
        (
            "L'instruction INSERT INTO Habilitation VALUES (9, 'son') est-elle autorisée avec les données fournies ? Distinguer l'unicité de la paire et l'intégrité référentielle, en supposant les clés étrangères activées.",
            "La paire (9, son) est nouvelle, mais l'équipe 9 n'existe pas. La clé étrangère interdit donc l'insertion malgré l'absence de doublon.",
            [("0.25", "L'absence de doublon est distinguée de la référence absente."),
             ("0.25", "L'insertion est refusée pour l'équipe 9 inexistante.")], "justify", "BDD-MODELE",
        ),
        (
            "Écrire une requête donnant les identifiants et noms des équipes actives habilitées pour le son. Ranger les résultats par identifiant croissant et donner les lignes obtenues.",
            "SELECT Equipe.id, Equipe.nom FROM Equipe JOIN Habilitation ON Equipe.id = Habilitation.equipe WHERE Equipe.active = 1 AND Habilitation.domaine = 'son' ORDER BY Equipe.id;\nRésultat : (1, Aube), (2, Rive).",
            [("0.25", "La jointure et les deux conditions sont correctes."),
             ("0.25", "Les colonnes, le tri et les deux lignes sont exacts.")], "design", "BDD-SQL-SELECT",
        ),
        (
            "Sans modifier les habilitations, écrire une instruction qui rend l'équipe Rive inactive. Pourquoi mettre à jour sa ligne est-il préférable à supprimer puis recréer l'équipe ? Pour la suite, revenir aux données initiales.",
            "UPDATE Equipe SET active = 0 WHERE id = 2;\nL'identifiant et les habilitations restent conservés ; supprimer l'équipe peut violer les références existantes et perdrait son identité.",
            [("0.25", "La mise à jour cible seulement id = 2."),
             ("0.25", "La conservation des références ou de l'identité est expliquée.")], "design", "BDD-SQL-MUTATION",
        ),
        (
            "L'équipe Lac est habilitée pour la lumière. Peut-on lui attribuer la tâche 11 dans l'état initial ? Expliquer pourquoi une clé étrangère vers cette équipe ne suffirait pas à garantir une affectation valide.",
            "Non : active vaut 0 pour Lac. Une référence vérifie l'existence d'une équipe, pas son activité ni l'adéquation de son domaine à une tâche.",
            [("0.25", "L'inactivité de Lac et la limite d'une clé étrangère sont expliquées.")], "analyse", "BDD-MODELE",
        ),
        (
            "Construire une requête donnant les couples (identifiant de tâche, identifiant d'équipe) autorisés : équipe active et habilitation dans le domaine de la tâche. Trier d'abord par priorité de tâche, puis identifiant de tâche, puis identifiant d'équipe. Donner toutes les lignes, sans affecter encore les équipes.",
            candidate_query() + ";\nRésultat : (10, 1), (10, 2), (11, 1), (12, 3).",
            [("0.25", "Les deux jointures relient domaine et identifiant d'équipe."),
             ("0.25", "La sélection active et les trois clés de tri sont correctes."),
             ("0.25", "Les quatre couples et leur ordre sont exacts.")], "design", "BDD-SQL-SELECT",
        ),
        (
            "Partie B. On dispose des couples précédents dans candidats et de taches = [10, 11, 12]. Chaque tâche doit recevoir une équipe distincte. La fonction suivante choisit la première équipe disponible pour chaque tâche. Exécuter cette fonction puis expliquer pourquoi son échec ne démontre pas que l'affectation complète est impossible.\n" + _solution(glouton),
            "Elle attribue 10 à 1 puis renvoie None à la tâche 11, car 1 est déjà prise. Pourtant 10 à 2, 11 à 1, 12 à 3 est valide : c'est le premier choix qui doit être révisé.",
            [("0.25", "Le choix 10 vers 1 et l'arrêt sur 11 sont exacts."),
             ("0.25", "Une affectation complète valide réfute la conclusion d'impossibilité.")], "analyse", "LP-DEBUG",
        ),
        (
            "Compléter la fonction récursive suivante. chercher(rang, choix, prises) attribue les tâches avant rang ; prises contient leurs équipes. Les nouvelles listes sont des copies propres à la branche. A exprime le cas terminé ; B vérifie que le couple concerne la tâche courante et une équipe libre ; C donne les trois arguments du prochain appel. Donner aussi le résultat sur les données initiales.\n"
            + re.sub(r"rang \+ 1,\s*suite,\s*nouvelles,", "__C__,", _solution(affecter))
            .replace("rang == len(taches)", "__A__")
            .replace("ok and e not in prises", "__B__"),
            _solution(affecter) + "\nRésultat : [(10, 2), (11, 1), (12, 3)].",
            [("0.25", "Le cas terminé renvoie l'affectation construite."),
             ("0.25", "Le couple doit concerner la tâche courante et une équipe non prise."),
             ("0.25", "L'appel avance d'une tâche, conserve les listes de la branche et produit le résultat exact.")], "design", "LP-RECURSIVITE",
        ),
        (
            "Tracer les choix et retours récursifs avant l'obtention de la première solution. Préciser à quel moment l'équipe 1 redevient disponible après l'échec initial, sans instruction qui efface une liste partagée.",
            "La branche 10 vers 1 échoue sur 11. Son appel retourne None ; ses listes locales ne sont pas réutilisées. Le niveau initial essaie alors 10 vers 2, puis 11 vers 1, puis 12 vers 3. Les anciennes listes prises et choix sont restées inchangées.",
            [("0.25", "L'ordre d'essai, d'échec puis de reprise est exact."),
             ("0.25", "Les listes distinctes des branches expliquent la disponibilité retrouvée de 1.")], "apply", "LP-RECURSIVITE",
        ),
        (
            "Justifier que toute solution renvoyée attribue chaque tâche exactement une fois, respecte les habilitations et ne réutilise aucune équipe. Distinguer la propriété garantie par la requête de celles garanties par la récursion.",
            "La requête ne fournit que des couples actifs et habilités. Chaque niveau traite exactement taches[rang], puis avance d'un rang ; le cas terminé exige d'avoir traité toutes les tâches. Le test e not in prises interdit de réutiliser une équipe.",
            [("0.25", "L'activité et l'habilitation proviennent de la requête."),
             ("0.25", "L'avancement et le test prises garantissent complétude et unicité.")], "justify", "LP-RECURSIVITE",
        ),
        (
            "Rendre maintenant l'équipe 2 inactive et réexécuter la requête puis la recherche. Donner les couples restants et le résultat. Justifier l'impossibilité sans se limiter à constater que le programme échoue.",
            "Avec active = 0 pour l'équipe 2 : (10, 1), (11, 1), (12, 3). La recherche renvoie None. Les tâches 10 et 11 exigent toutes deux l'unique équipe 1 encore disponible pour elles ; une équipe ne pouvant recevoir deux tâches, aucune solution n'existe.",
            [("0.25", "Les trois couples restants et None sont exacts."),
             ("0.25", "Le conflit entre les tâches 10 et 11 prouve l'impossibilité.")], "justify", "BDD-SQL-SELECT",
        ),
        (
            "Proposer deux tests de frontière de affecter : aucune tâche à attribuer ; deux tâches dont la seule équipe candidate est la même. Donner les résultats attendus et expliquer pourquoi un échec ne doit pas modifier candidats pour un appel ultérieur.",
            "affecter([], []) renvoie [] : l'affectation vide est complète. affecter([10, 11], [(10, 1), (11, 1)]) renvoie None. candidats est seulement parcouru ; aucun couple n'est retiré pendant la recherche, donc une nouvelle invocation retrouve les données initiales.",
            [("0.25", "Les deux appels et leurs résultats [] et None sont corrects."),
             ("0.25", "L'absence de mutation de candidats est expliquée.")], "debug", "LP-DEBUG",
        ),
    ]
    minutes = [3, 4, 4, 4, 4, 10, 6, 11, 6, 6, 6, 6]
    questions = []
    for index, (prompt, answer, credits, operation, code) in enumerate(items):
        questions.append(dict(
            id="2" + "abcdefghijkl"[index], prompt=prompt, answer=answer,
            points=str(sum(Decimal(value) for value, _ in credits)),
            marking=[dict(points=value, criterion=criterion) for value, criterion in credits],
            material_ids=["equipe", "tache", "habilitation"], curriculum_codes=[code],
            operation=operation, difficulty=4 if index in (7, 8, 9) else 3,
            estimated_minutes=minutes[index], verification=dict(
                kind="allocation_case_contract", version=VERSION, seed=seed, case_sha256=digest),
        ))
    raw = dict(
        id="2", title="Attribuer des tâches à des équipes habilitées",
        context="Une régie attribue des tâches à des équipes. Chaque tâche exige exactement une équipe active habilitée dans son domaine ; chaque équipe reçoit au plus une tâche. La priorité fixe l'ordre de traitement, pas une possibilité d'omettre une tâche. Schéma : Equipe(id, nom, active), Tache(id, domaine, priorite), Habilitation(equipe, domaine). Equipe.id et Tache.id sont clés primaires ; (equipe, domaine) est la clé primaire de Habilitation ; equipe référence Equipe.id. active vaut 0 ou 1. Les contraintes de clés sont actives. Les données initiales sont restaurées après chaque question sauf indication contraire. La recherche récursive porte sur les trois tâches données. Rédiger sur votre copie.",
        topics=["bases-donnees", "langages-programmation"], minutes=70, target_points="6",
        materials=[
            dict(kind="table", id="equipe", title="equipe", columns=["id", "nom", "active"],
                 rows=[[str(value) for value in row] for row in case["teams"]]),
            dict(kind="table", id="tache", title="tache", columns=["id", "domaine", "priorite"],
                 rows=[[str(value) for value in row] for row in case["tasks"]]),
            dict(kind="table", id="habilitation", title="habilitation", columns=["equipe", "domaine"],
                 rows=[[str(value) for value in row] for row in case["skills"]]),
        ], questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw
