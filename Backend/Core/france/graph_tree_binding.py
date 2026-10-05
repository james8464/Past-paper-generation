"""Bind authored French questions to locked graph/tree facts."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256

from Backend.Core.france.graph_tree_contract import GraphTreeContract

_EDGE = re.compile(r"\b([A-F])\s*(?:-|–|→|->)\s*([A-F])\b")
_BFS_ANSWER = re.compile(
    r"(?:ordre\s+du\s+parcours\s+en\s+largeur|ordre\s+BFS)\s*[:=]\s*"
    r"([A-F](?:\s*(?:,|→|->)\s*[A-F]){2,})",
    re.IGNORECASE,
)


def _hash(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_answer(task_id: str, result: dict) -> str:
    if task_id == "1a":
        return (
            "Le plus court chemin est "
            + " → ".join(result["path"])
            + f", de poids total {result['weight']}."
        )
    if task_id == "1b":
        return (
            "Les voisins de A sont "
            + ", ".join(result["neighbours"])
            + f" ; la somme des poids incidents est {result['weight_sum']}."
        )
    if task_id == "1c":
        return "La variable mal orthographiée doit être remplacée par `voisin`."
    if task_id == "1d":
        return "L'ordre du parcours en largeur est " + " → ".join(result["order"]) + "."
    if task_id == "1e":
        parent = result["search_path"][-1]
        side = "gauche" if result["insert_key"] < parent else "droite"
        return (
            f"Pour insérer {result['insert_key']}, suivre "
            + " → ".join(str(key) for key in result["search_path"])
            + f", puis créer son nœud comme enfant {side} de {parent}."
        )
    if task_id == "1f":
        return (
            "Après insertion, le parcours infixe donne "
            + " → ".join(str(key) for key in result["inorder"])
            + ". Un ABR parcourt le sous-arbre gauche, la racine, puis le sous-arbre droit."
        )
    raise ValueError("Tâche de contrat inconnue")


def bind_graph_tree_contract(
    raw: dict, contract: GraphTreeContract
) -> tuple[dict, dict]:
    """Assemble locked materials without erasing the model's raw evidence."""
    data = contract.to_dict()
    if not isinstance(raw, dict) or raw.get("materials") not in (None, []):
        raise ValueError("Le modèle ne doit pas remplacer les supports verrouillés")
    context = raw.get("context")
    questions = raw.get("questions")
    if (
        not isinstance(context, str)
        or not context.strip()
        or "class Noeud" in context
        or not isinstance(questions, list)
        or [item.get("id") for item in questions if isinstance(item, dict)]
        != data["task_ids"]
        or len(questions) != len(data["task_ids"])
    ):
        raise ValueError("Contexte ou questions incompatibles avec le contrat")

    graph = data["graph"]
    tree = data["tree"]
    declared_edges = {tuple(sorted(edge[:2])) for edge in graph["edges"]}
    bound = deepcopy(raw)
    bound["materials"] = [
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
            "title": "Arbre des identifiants d'intervention",
            "columns": tree["columns"],
            "rows": [
                [str(value) if value is not None else "—" for value in row]
                for row in tree["rows"]
            ],
        },
    ]
    bound["context"] = (
        context.rstrip()
        + "\n\nLe tableau `arbre` décrit un ABR dont la racine est "
        + str(tree["root"])
        + ". Le symbole — signifie l'absence d'un enfant. "
        + "La clé à insérer est "
        + str(tree["insert_key"])
        + ". Les programmes utilisent la définition suivante :\n\n```python\n"
        + data["node_api"]
        + "\n```"
    )
    records = []
    for question, task_id in zip(bound["questions"], data["task_ids"], strict=True):
        if (
            question.get("contract_task_id") != task_id
            or question.get("claimed_result") != data["expected"][task_id]
        ):
            raise ValueError(
                f"Résultat déclaré incompatible avec le contrat : {task_id}"
            )
        prompt = question.get("prompt")
        answer = question.get("answer")
        if not isinstance(prompt, str) or not isinstance(answer, str):
            raise ValueError("Question et réponse textuelles requises")
        for start, end in _EDGE.findall(prompt + "\n" + answer):
            if tuple(sorted((start, end))) not in declared_edges:
                raise ValueError(f"Arête absente du graphe : {start}-{end}")
        if task_id == "1d":
            stated_order = _BFS_ANSWER.search(answer)
            if (
                stated_order
                and re.findall(r"[A-F]", stated_order.group(1))
                != data["expected"][task_id]["order"]
            ):
                raise ValueError(
                    "La réponse du parcours en largeur contredit le graphe"
                )
        records.append(
            {
                "task_id": task_id,
                "claimed_result": deepcopy(question["claimed_result"]),
                "canonical_result_sha256": _hash(data["expected"][task_id]),
                "authored_answer_sha256": _hash(answer),
                "authored_verification_sha256": _hash(question.get("verification")),
            }
        )
        question["answer"] = _canonical_answer(task_id, data["expected"][task_id])
        question["verification"] = {
            "kind": "graph_tree",
            "contract": data,
            "task_id": task_id,
            "expected": deepcopy(data["expected"][task_id]),
        }
        records[-1]["assembled_answer_sha256"] = _hash(question["answer"])
        records[-1]["assembled_verification_sha256"] = _hash(question["verification"])
        del question["contract_task_id"]
        del question["claimed_result"]
    return bound, {
        "contract_sha256": contract.digest,
        "materials_sha256": _hash(bound["materials"]),
        "questions": records,
    }
