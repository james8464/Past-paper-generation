# Eligibility joins and a greedy counterexample for French practice


def candidate_query():
    return """SELECT Tache.id, Equipe.id
FROM Tache
JOIN Habilitation ON Tache.domaine = Habilitation.domaine
JOIN Equipe ON Habilitation.equipe = Equipe.id
WHERE Equipe.active = 1
ORDER BY Tache.priorite, Tache.id, Equipe.id"""


# these solutions retain short lines for enlarged-print code listings
# fmt: off
def glouton(taches, candidats):
    sortie = []
    prises = []
    for tache in taches:
        choix = None
        for t, e in candidats:
            if (
                t == tache
                and e not in prises
            ):
                choix = e
                break
        if choix is None:
            return None
        sortie.append((tache, choix))
        prises.append(choix)
    return sortie


# Backtrack on assignments; failed branches leave no shared state
def affecter(taches, candidats):
    def chercher(rang, choix, prises):
        if rang == len(taches):
            return choix
        for t, e in candidats:
            ok = t == taches[rang]
            if ok and e not in prises:
                suite = [*choix, (t, e)]
                nouvelles = [*prises, e]
                reponse = chercher(
                    rang + 1,
                    suite,
                    nouvelles,
                )
                if reponse is not None:
                    return reponse
        return None

    return chercher(0, [], [])


# fmt: on
# one structural family, with an inactive decoy and shared eligibility
def build_case(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A signed 64-bit integer seed is required")
    return {
        "family": "team-eligibility",
        "schema": """CREATE TABLE Equipe (
id INTEGER PRIMARY KEY, nom TEXT NOT NULL,
active INTEGER NOT NULL CHECK (active IN (0, 1)));
CREATE TABLE Tache (
id INTEGER PRIMARY KEY, domaine TEXT NOT NULL, priorite INTEGER NOT NULL);
CREATE TABLE Habilitation (
equipe INTEGER NOT NULL REFERENCES Equipe(id), domaine TEXT NOT NULL,
PRIMARY KEY (equipe, domaine));""",
        "teams": [[1, "Aube", 1], [2, "Rive", 1], [3, "Pin", 1], [4, "Lac", 0]],
        "tasks": [[10, "son", 1], [11, "lumière", 2], [12, "image", 3]],
        "skills": [[1, "son"], [1, "lumière"], [2, "son"], [3, "image"], [4, "lumière"]],
    }
