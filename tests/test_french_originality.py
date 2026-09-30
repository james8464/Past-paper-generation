import pytest


def test_originality_screen_rejects_copied_and_identifier_renamed_material():
    from Backend.Core.france.originality import screen_originality

    reference = (
        "Une médiathèque organise les prêts de ses ouvrages. "
        "Chaque adhérent possède un identifiant et consulte un catalogue ordonné. "
        "Déterminer le résultat puis justifier la complexité de la recherche.\n"
        "```python\n"
        "def recherche(livres, cible):\n"
        "    for livre in livres:\n"
        "        if livre == cible:\n"
        "            return True\n"
        "    return False\n"
        "```"
    )
    with pytest.raises(ValueError, match="originalité"):
        screen_originality(reference, [reference])

    renamed = reference.replace("livres", "elements").replace("livre", "element")
    with pytest.raises(ValueError, match="originalité"):
        screen_originality(renamed, [reference])


def test_originality_screen_allows_common_instructions_and_distinct_context():
    from Backend.Core.france.originality import screen_originality

    candidate = (
        "Un observatoire côtier relie des capteurs par un graphe pondéré. "
        "Établir un itinéraire robuste, expliquer l'invariant puis discuter le coût. "
        "Justifier la réponse."
    )
    reference = (
        "Une bibliothèque conserve des prêts dans une base relationnelle. "
        "Écrire une requête avec jointure et expliquer la contrainte d'intégrité. "
        "Justifier la réponse."
    )
    evidence = screen_originality(candidate, [reference])
    assert evidence["state"] == "passed_calibrated_screen"
    assert evidence["calibration_set"] == "fr-nsi-labelled-v1"
    assert evidence["maximum_scores"]["prose_five_gram_jaccard"] < 0.45


def test_originality_screen_compares_previous_generations():
    from Backend.Core.france.originality import screen_originality

    previous = (
        "Un réseau de tramways relie Toulouse, Blagnac et Colomiers. "
        "Appliquer l'algorithme de Dijkstra et détailler chaque mise à jour."
    )
    with pytest.raises(ValueError, match="génération précédente"):
        screen_originality(previous, [], previous_texts=[previous])
