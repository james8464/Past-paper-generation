"""Student-visible materials and canonical answers from locked database facts."""

from __future__ import annotations

from Backend.Core.france.database_contract import DatabaseContract


def database_materials(contract: DatabaseContract) -> list[dict]:
    data = contract.to_dict()
    titles = {
        "agent": "Agents de l'atelier",
        "categorie": "Catégories d'incident",
        "incident": "Incidents enregistrés",
    }
    return [
        {
            "kind": "table",
            "id": name,
            "title": titles[name],
            "columns": table["columns"],
            "rows": [[str(value) for value in row] for row in table["rows"]],
        }
        for name in ("agent", "categorie", "incident")
        for table in (data["tables"][name],)
    ]


def canonical_database_answer(task_id: str, contract: DatabaseContract) -> str:
    data = contract.to_dict()
    expected = data["expected"]
    first_incident = data["tables"]["incident"]["rows"][0][0]
    first_category = expected["correct_join"][0][1]
    if task_id == "2a":
        return (
            "L'insertion proposée est invalide : id_agent = 999 ne désigne "
            "aucune ligne de la relation agent ; la clé étrangère serait rompue."
        )
    if task_id == "2b":
        return (
            f"Pour l'incident {first_incident}, la catégorie est {first_category} : "
            "la correspondance passe par incident.id_cat et categorie.id_cat."
        )
    if task_id == "2c":
        return (
            "Il faut joindre les catégories par id_cat, non par id_agent :\n"
            "```sql\n" + data["correct_sql"] + "\n```\n"
            f"La requête corrigée renvoie {len(expected['correct_join'])} lignes."
        )
    if task_id == "2d":
        return (
            "La mise à jour ciblée est :\n```sql\n" + data["update_sql"] + "\n```\n"
            f"Une ligne est modifiée (incident {first_incident}) ; "
            f"il y a ensuite {expected['closed_after_update']} incidents clos."
        )
    if task_id == "2e":
        statuses = [row[3] for row in data["tables"]["incident"]["rows"]]
        input_value = ",\n    ".join(
            "{'statut': '" + status + "'}" for status in statuses
        )
        return (
            "Un test révélateur est :\n```python\nassert nombre_clos([\n    "
            + input_value
            + f"\n]) == {expected['closed_before']}\n```\nLe programme fourni renvoie "
            f"{expected['faulty_python_count']} : l'assertion échoue."
        )
    if task_id == "2f":
        return (
            "Remplacer la condition fautive par :\n"
            "```python\nif incident['statut'] == 'clos':\n```\n"
            "La fonction corrigée renvoie "
            f"{expected['closed_before']} sur les quatre lignes affichées, "
            f"et non {expected['faulty_python_count']}."
        )
    raise ValueError("Unknown database task")
