"""Object identity and graph traversal for an unpublished French exercise.

Links represent shortcuts between directories, not filesystem containment.
Two distinct directories may have the same displayed name.
"""

from collections import deque


# These solutions retain short lines for enlarged-print code listings.
# fmt: off
class Dossier:
    def __init__(self, identifiant, nom):
        self.identifiant = identifiant
        self.nom = nom
        self.enfants = []

    def relier(self, autre):
        cle = autre.identifiant
        for lien in self.enfants:
            if lien.identifiant == cle:
                return
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
        objet, dist = attente.popleft()
        if objet.identifiant == cible:
            return dist
        for lien in objet.enfants:
            cle = lien.identifiant
            if cle not in vus:
                vus.add(cle)
                attente.append(
                    (lien, dist + 1)
                )
    return None


# fmt: on
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
