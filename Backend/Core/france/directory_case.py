# Object identity and graph traversal for the French practice catalogue
#
# Links represent shortcuts between directories, not filesystem containment
# two distinct directories may have the same displayed name

from collections import deque


# these solutions retain short lines for enlarged-print code listings
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


# record identifiers before following links, including back edges
def explorer(depart, vus):
    if depart.identifiant not in vus:
        vus.append(depart.identifiant)
        for enfant in depart.enfants:
            explorer(enfant, vus)


# return the fewest directed links, or None for an unreachable identifier
def distance_minimale(depart, cible):
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
# Allocate each object once so shared links preserve object identity
def build_objects(case):
    dossiers = {
        identifiant: Dossier(identifiant, nom)
        for identifiant, nom in case["nodes"]
    }
    for depart, arrivee in case["links"]:
        dossiers[depart].relier(dossiers[arrivee])
    return dossiers


# return one fixed family; changing its seed doesn't create novelty
def build_case(seed):
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
