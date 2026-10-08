"""Finite, original French wording for the V17 graph/tree depth case."""

from __future__ import annotations

import json
from decimal import Decimal
from hashlib import sha256

from Backend.Core.france.graph_tree_binding import graph_edge_manifest
from Backend.Core.france.graph_tree_depth_contract import GraphTreeDepthContract

GRAPH_TREE_DEPTH_PROSE_VERSION = "fr-nsi-graph-tree-prose-v4"
_IDS = tuple(f"1{letter}" for letter in "abcdefghij")
_MINUTES = (6, 6, 8, 7, 8, 7, 7, 7, 7, 7)
_PARTS = "AAAABBBCCC"
_CODES = (
    "SD-GRAPHE",
    "SD-GRAPHE",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-GRAPHES",
    "ALG-ARBRES",
    "ALG-ARBRES",
    "ALG-ARBRES",
)
_OPERATIONS = (
    "apply",
    "analyse",
    "analyse",
    "justify",
    "apply",
    "debug",
    "justify",
    "apply",
    "analyse",
    "debug",
)
_SCENES = {
    "service": (
        "Parcours d'un réseau et recherche dans un arbre",
        "Un service relie six postes par un réseau pondéré. Un arbre binaire de recherche distinct classe les identifiants d'intervention.",
    ),
    "collecte": (
        "Trajets de collecte et arbre de recherche",
        "Une équipe de collecte relie six postes par un réseau pondéré. Un arbre binaire de recherche distinct classe les demandes.",
    ),
}
_QUESTIONS = {
    "1a": (
        "Quels sont les voisins de A dans `reseau` ? Donnez le degré de A et la somme des poids des arêtes qui lui sont incidentes.",
        "Relevez les voisins et le degré de A, puis calculez le total des poids des liaisons touchant A.",
    ),
    "1b": (
        "Calculez, arête par arête, le coût du détour A–C–E–F dans `reseau`.",
        "Quel est le poids total du trajet A–C–E–F ? Détaillez votre addition.",
    ),
    "1c": (
        "Depuis A, appliquez les deux premières fixations de Dijkstra : indiquez le sommet fixé, les distances provisoires et les prédécesseurs alors connus.",
        "Tracez les deux premières étapes de Dijkstra à partir de A, avec distances provisoires et prédécesseurs mis à jour.",
    ),
    "1d": (
        "Déduisez un chemin de poids minimal de A à F et justifiez son poids à partir des arêtes parcourues.",
        "Quel trajet de A à F a le coût minimal ? Donnez ses sommets et vérifiez la somme des poids.",
    ),
    "1e": (
        "Pour le parcours en largeur depuis A, donnez la file et l'ensemble des sommets déjà découverts après chacun des deux premiers retraits de la file.",
        "Après les retraits successifs de A puis du sommet suivant, indiquez la file et les sommets marqués visités.",
    ),
    "1f": (
        "Quelle erreur provoque le programme `parcours_largeur` fourni ? Corrigez uniquement le nom fautif.",
        "Repérez la variable mal orthographiée dans `parcours_largeur`, nommez l'exception et donnez le nom correct.",
    ),
    "1g": (
        "Après correction, donnez l'ordre complet du parcours en largeur et expliquez pourquoi un sommet n'entre pas deux fois dans la file.",
        "Écrivez l'ordre de visite du parcours corrigé ; justifiez le rôle du marquage dès l'enfilage.",
    ),
    "1h": (
        "Dans `arbre`, suivez la recherche pour insérer la clé {insert_key}, puis indiquez le parent et le côté du nouveau nœud.",
        "Quelles clés compare-t-on avant d'insérer {insert_key} dans `arbre` ? Où crée-t-on le nœud ?",
    ),
    "1i": (
        "Après cette insertion, donnez le parcours infixe de `arbre` et expliquez pourquoi ses clés sont ordonnées.",
        "Énumérez les clés visitées par le parcours gauche–racine–droite après insertion et reliez l'ordre obtenu à la propriété de l'ABR.",
    ),
    "1j": (
        "Dans la fonction `contient` fournie, corrigez la comparaison fautive. Tracez ensuite la recherche de {insert_key} après insertion et justifiez le résultat.",
        "Quel opérateur doit remplacer celui de `contient` ? Donnez le chemin de recherche de {insert_key} dans l'arbre complété et expliquez le résultat.",
    ),
}


def graph_tree_depth_catalogue_digest() -> str:
    return sha256(
        json.dumps(
            {
                "version": GRAPH_TREE_DEPTH_PROSE_VERSION,
                "scenes": _SCENES,
                "questions": _QUESTIONS,
                "minutes": _MINUTES,
                "parts": _PARTS,
                "codes": _CODES,
                "operations": _OPERATIONS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def graph_tree_depth_selection_schema(contract: GraphTreeDepthContract) -> dict:
    if contract.to_dict()["task_ids"] != list(_IDS):
        raise ValueError("Incompatible graph/tree depth contract")

    def forms(suffix: str) -> dict:
        return {
            "type": "object",
            "properties": {
                task_id: {
                    "type": "string",
                    "enum": [f"{task_id}-{suffix}1", f"{task_id}-{suffix}2"],
                }
                for task_id in _IDS
            },
            "required": list(_IDS),
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": {
            "scene_id": {"type": "string", "enum": list(_SCENES)},
            "question_forms": forms("q"),
            "rubric_forms": forms("r"),
        },
        "required": ["scene_id", "question_forms", "rubric_forms"],
        "additionalProperties": False,
    }


def validate_graph_tree_depth_selection(
    contract: GraphTreeDepthContract, selection: dict
) -> dict:
    schema = graph_tree_depth_selection_schema(contract)["properties"]
    if not isinstance(selection, dict) or set(selection) != set(schema):
        raise ValueError("Graph/tree depth selection outside schema")
    if type(selection["scene_id"]) is not str or selection["scene_id"] not in _SCENES:
        raise ValueError("Unknown graph/tree depth scene")
    for field in ("question_forms", "rubric_forms"):
        chosen = selection[field]
        allowed = schema[field]["properties"]
        if not isinstance(chosen, dict) or set(chosen) != set(allowed):
            raise ValueError("Graph/tree depth selection fields mismatch")
        if any(
            type(chosen[key]) is not str or chosen[key] not in rule["enum"]
            for key, rule in allowed.items()
        ):
            raise ValueError("Unknown graph/tree depth wording ID")
    return selection


def _answer(task_id: str, result: dict, facts: dict) -> str:
    if task_id == "1a":
        return (
            "Les voisins de A sont "
            + ", ".join(result["neighbours"])
            + f" ; son degré est {result['degree']} et la somme des poids incidents vaut {result['incident_weight']}."
        )
    if task_id == "1b":
        weights = {
            frozenset((a, b)): weight for a, b, weight in facts["graph"]["edges"]
        }
        segments = (("A", "C"), ("C", "E"), ("E", "F"))
        addition = " + ".join(str(weights[frozenset(pair)]) for pair in segments)
        return f"Le détour A–C–E–F coûte {addition} = {result['weight']}."
    if task_id == "1c":
        lines = []
        for row in result["steps"]:
            distances = ", ".join(
                f"{node}={value if value is not None else '∞'}"
                for node, value in row["tentative"].items()
            )
            predecessors = ", ".join(
                f"{node}←{previous}" for node, previous in row["predecessors"].items()
            )
            lines.append(
                f"Après fixation de {row['settled']} : {distances} ; prédécesseurs {predecessors}."
            )
        return "\n".join(lines)
    if task_id == "1d":
        return (
            "Le chemin minimal est "
            + " → ".join(result["path"])
            + f", de poids {result['weight']}."
        )
    if task_id == "1e":
        return "\n".join(
            f"Après retrait de {row['dequeued']} : file {', '.join(row['queue'])} ; découverts {', '.join(row['visited'])}."
            for row in result["states"]
        )
    if task_id == "1f":
        return "Le nom `visin` n'est pas défini : NameError. Le remplacer par `voisin`."
    if task_id == "1g":
        return (
            "L'ordre de visite est "
            + " → ".join(result["order"])
            + ". Chaque sommet est marqué dès son ajout à la file, donc il n'est pas enfilé deux fois."
        )
    if task_id == "1h":
        return (
            f"Pour insérer {result['insert_key']}, suivre "
            + " → ".join(map(str, result["search_path"]))
            + f" ; créer l'enfant {result['side']} de {result['parent']}."
        )
    if task_id == "1i":
        return (
            "Le parcours infixe est "
            + " → ".join(map(str, result["inorder"]))
            + ". Dans un ABR, le sous-arbre gauche porte des clés inférieures et le sous-arbre droit des clés supérieures."
        )
    if task_id == "1j":
        return (
            "Remplacer `cle > noeud.valeur` par `cle < noeud.valeur` : "
            + " → ".join(map(str, result["search_path"]))
            + ". La clé insérée est trouvée ; les clés plus petites se cherchent à gauche."
        )
    raise ValueError("Unknown graph/tree depth task")


def _criteria(task_id: str, points: str, result: dict) -> tuple[str, ...]:
    two = {
        "1a": ("les voisins et le degré de A", "la somme des poids incidents"),
        "1b": ("les trois poids du détour A–C–E–F", "leur somme correcte"),
        "1d": ("les sommets d'un chemin minimal", "son poids total correct"),
        "1f": ("l'exception NameError causée par `visin`", "le nom corrigé `voisin`"),
        "1g": (
            "l'ordre complet de visite",
            "le marquage dès l'enfilage qui évite les doublons",
        ),
        "1h": (
            "les clés suivies pour l'insertion",
            "le parent et le côté du nouveau nœud",
        ),
        "1i": ("le parcours infixe après insertion", "la propriété d'ordre de l'ABR"),
    }
    if task_id in two:
        return two[task_id]
    if task_id == "1c":
        if points == "0.5":
            return (
                "les distances provisoires après A",
                "les distances provisoires après la deuxième fixation",
            )
        return (
            "les distances provisoires après A",
            "les prédécesseurs après A",
            "les distances provisoires après la deuxième fixation",
            "les prédécesseurs après la deuxième fixation",
        )
    if task_id == "1e":
        if points == "0.5":
            return (
                "la file après le premier retrait",
                "la file et les sommets découverts après le deuxième retrait",
            )
        return (
            "la file après le premier retrait",
            "les sommets découverts après le premier retrait",
            "la file après le deuxième retrait",
            "les sommets découverts après le deuxième retrait",
        )
    if task_id == "1j":
        if points == "0.5":
            return ("la comparaison corrigée", "la recherche réussie de la clé insérée")
        return (
            "la comparaison corrigée",
            "le chemin de recherche après insertion",
            "la recherche réussie",
            "la justification par l'ordre de l'ABR",
        )
    raise ValueError("Unknown graph/tree depth rubric")


def _rubric(task_id: str, points: str, result: dict, variant: int) -> list[dict]:
    criteria = _criteria(task_id, points, result)
    if len(criteria) != int(Decimal(points) * 4):
        raise ValueError("Graph/tree depth rubric and credit disagree")
    prefix = "Vérifier " if variant == 2 else "Accorder pour "
    return [{"points": "0.25", "criterion": prefix + item + "."} for item in criteria]


def render_graph_tree_depth_candidate(
    contract: GraphTreeDepthContract, selection: dict, task_specs: list[dict]
) -> dict:
    validate_graph_tree_depth_selection(contract, selection)
    if not isinstance(task_specs, list) or len(task_specs) != 10:
        raise ValueError("Graph/tree depth blueprint structure mismatch")
    totals = tuple(item.get("points") for item in task_specs if isinstance(item, dict))
    valid_profiles = {
        tuple("1" if task_id in extras else "0.5" for task_id in _IDS)
        for extras in ({"1c"}, {"1c", "1e"}, {"1c", "1e", "1j"})
    }
    if (
        any(not isinstance(item, dict) for item in task_specs)
        or [item.get("id") for item in task_specs] != list(_IDS)
        or totals not in valid_profiles
        or tuple(item.get("estimated_minutes") for item in task_specs) != _MINUTES
        or "".join(item.get("part_id", "") for item in task_specs) != _PARTS
        or tuple(item.get("required_curriculum_code") for item in task_specs) != _CODES
        or tuple(item.get("operation") for item in task_specs) != _OPERATIONS
    ):
        raise ValueError("Graph/tree depth blueprint credit or sequence mismatch")
    facts = contract.to_dict()
    graph, tree = facts["graph"], facts["tree"]
    title, lead = _SCENES[selection["scene_id"]]
    context = (
        lead
        + " Les liaisons du graphe `reseau` sont bidirectionnelles ; leurs poids sont indiqués sur la figure. "
        + "Si deux routes ont le même poids, retenir la suite de sommets première dans l'ordre alphabétique. "
        + "Pour les parcours, les voisins sont examinés dans l'ordre alphabétique et un sommet est marqué dès son enfilage.\n\n"
        + graph_edge_manifest(graph)
        + "\n\nLe programme suivant de parcours en largeur comporte une faute :\n\n```python\n"
        + facts["debug_case"]["faulty_code"]
        + "\n```\n\nL'arbre `arbre` est un ABR de racine "
        + str(tree["root"])
        + ". Le signe — désigne l'absence d'enfant ; la clé à insérer est "
        + str(tree["insert_key"])
        + ". La classe des nœuds est :\n\n```python\n"
        + facts["node_api"]
        + "\n```\n\nAprès insertion, étudier aussi cette fonction de recherche comportant une comparaison fautive :\n\n```python\n"
        + facts["search_code"]
        + "\n```"
    )
    materials = [
        {
            "kind": "weighted_graph",
            "id": graph["id"],
            "title": "Réseau pondéré des postes",
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "directed": graph["directed"],
        },
        {
            "kind": "table",
            "id": tree["id"],
            "title": "Arbre des identifiants",
            "columns": tree["columns"],
            "rows": [
                [str(value) if value is not None else "—" for value in row]
                for row in tree["rows"]
            ],
        },
    ]
    questions = []
    for task_id, plan in zip(_IDS, task_specs, strict=True):
        result = facts["expected"][task_id]
        prompt = _QUESTIONS[task_id][int(selection["question_forms"][task_id][-1]) - 1]
        questions.append(
            {
                "id": task_id,
                "prompt": prompt.format(insert_key=tree["insert_key"]),
                "points": plan["points"],
                "answer": _answer(task_id, result, facts),
                "marking": _rubric(
                    task_id,
                    plan["points"],
                    result,
                    int(selection["rubric_forms"][task_id][-1]),
                ),
                "material_ids": ["reseau"] if task_id <= "1g" else ["arbre"],
                "curriculum_codes": [plan["required_curriculum_code"]],
                "operation": plan["operation"],
                "difficulty": plan["difficulty"],
                "estimated_minutes": plan["estimated_minutes"],
                "verification": {
                    "kind": "graph_tree_depth_contract",
                    "contract": facts,
                    "task_id": task_id,
                    "expected": result,
                },
            }
        )
    return {
        "id": "1",
        "title": title,
        "context": context,
        "topics": ["structures-donnees", "algorithmique"],
        "minutes": 70,
        "target_points": str(
            sum((Decimal(item["points"]) for item in task_specs), Decimal()).normalize()
        ),
        "materials": materials,
        "questions": questions,
    }
