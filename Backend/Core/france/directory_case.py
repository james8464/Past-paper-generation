"""Object identity and graph traversal for an unpublished French exercise.

Links represent shortcuts between directories, not filesystem containment.
Two distinct directories may have the same displayed name.
"""

from collections import deque


class Dossier:
    def __init__(self, identifiant, nom):
        self.identifiant = identifiant
        self.nom = nom
        self.enfants = []

    def relier(self, autre):
        if all(enfant.identifiant != autre.identifiant for enfant in self.enfants):
            self.enfants.append(autre)


def explorer(depart, vus):
    """Record identifiers before following links, including back edges."""
    if depart.identifiant not in vus:
        vus.append(depart.identifiant)
        for enfant in depart.enfants:
            explorer(enfant, vus)


def distance_minimale(depart, cible):
    """Return the fewest directed links, or None for an unreachable identifier."""
    attente = deque([(depart, 0)])
    vus = {depart.identifiant}
    while attente:
        courant, distance = attente.popleft()
        if courant.identifiant == cible:
            return distance
        for enfant in courant.enfants:
            if enfant.identifiant not in vus:
                vus.add(enfant.identifiant)
                attente.append((enfant, distance + 1))
    return None


def build_objects(case):
    """Allocate each object once so shared links preserve object identity."""
    dossiers = {
        identifiant: Dossier(identifiant, nom)
        for identifiant, nom in case["nodes"]
    }
    for depart, arrivee in case["links"]:
        dossiers[depart].relier(dossiers[arrivee])
    return dossiers


def build_case(seed):
    """Return one fixed family; changing its seed does not create novelty."""
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A signed 64-bit integer seed is required")
    return {
        "family": "directory-shortcuts",
        "nodes": [
            ["r", "Accueil"], ["a", "Archives"], ["b", "Archives"],
            ["c", "Plans"], ["d", "Tests"], ["e", "Notes"],
        ],
        "links": [
            ["r", "a"], ["r", "b"], ["a", "c"],
            ["b", "c"], ["c", "d"], ["d", "a"],
        ],
    }
