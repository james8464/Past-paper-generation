"""Candidate-visible tables and answers for the controlled network exercise."""

from __future__ import annotations

from Backend.Core.france.network_contract import NetworkContract


def network_materials(contract: NetworkContract) -> list[dict]:
    data = contract.to_dict()
    return [
        {
            "kind": "table",
            "id": "links",
            "title": "Liaisons bidirectionnelles et coûts initiaux",
            "columns": ["Extrémité 1", "Extrémité 2", "Coût"],
            "rows": [[left, right, str(cost)] for left, right, cost in data["links"]],
        },
        {
            "kind": "table",
            "id": "processes",
            "title": "État simultané des processus",
            "columns": ["Processus", "Ressource détenue", "Ressource attendue"],
            "rows": data["processes"],
        },
    ]


def canonical_network_answer(task_id: str, contract: NetworkContract) -> str:
    data = contract.to_dict()
    before, after = data["expected"]["before"], data["expected"]["after"]
    if task_id == "3a":
        return (
            f"La route Central–R1–Station coûte {before['cost']} "
            f"contre {before['other_cost']} par R2 : elle est choisie."
        )
    if task_id == "3b":
        return (
            f"Après la hausse, Central–R1–Station coûte {after['other_cost']} "
            f"et Central–R2–Station coûte {after['cost']}. "
            "La route via R2 devient la moins coûteuse."
        )
    if task_id == "3c":
        return (
            "Interblocage : B détient A et attend B, tandis que C détient B "
            "et attend A. Chacun attend la ressource détenue par l'autre."
        )
    if task_id == "3d":
        return (
            "C libère B. Les deux processus demandent ensuite A avant B : "
            "C ne détient plus B en attendant A, donc le cycle est rompu."
        )
    if task_id == "3e":
        return (
            "1. Le capteur obtient la clé publique authentifiée. "
            "2. Il crée une clé de session aléatoire et la chiffre avec cette clé. "
            "3. La station la déchiffre avec sa clé privée ; les messages sont "
            "ensuite chiffrés symétriquement."
        )
    if task_id == "3f":
        return (
            "Un observateur passif ne lit ni la clé de session chiffrée ni les "
            "messages symétriques, si les primitives sont sûres. La clé publique "
            "authentifiée empêche sa substitution. Ni les métadonnées ni un "
            "terminal compromis ne sont protégés. Avec un secret prépartagé, "
            "un autre protocole serait possible."
        )
    raise ValueError("Unknown network task")
