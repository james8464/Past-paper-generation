"""Eligibility joins and a greedy counterexample for unpublished practice."""


def candidate_query():
    return """SELECT Tache.id, Equipe.id
FROM Tache
JOIN Habilitation ON Tache.domaine = Habilitation.domaine
JOIN Equipe ON Habilitation.equipe = Equipe.id
WHERE Equipe.active = 1
ORDER BY Tache.priorite, Tache.id, Equipe.id"""


def glouton(taches, candidats):
    resultat = []
    prises = []
    for tache in taches:
        equipe = next(
            (e for t, e in candidats if t == tache and e not in prises), None
        )
        if equipe is None:
            return None
        resultat.append((tache, equipe))
        prises.append(equipe)
    return resultat


def affecter(taches, candidats):
    """Backtrack on assignments; failed branches leave no shared state."""
    def chercher(rang, resultat, prises):
        if rang == len(taches):
            return resultat
        for tache, equipe in candidats:
            if tache == taches[rang] and equipe not in prises:
                solution = chercher(
                    rang + 1, [*resultat, (tache, equipe)], [*prises, equipe]
                )
                if solution is not None:
                    return solution
        return None

    return chercher(0, [], [])


def build_case(seed):
    """One structural family, with an inactive decoy and shared eligibility."""
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
equipe INTEGER REFERENCES Equipe(id), domaine TEXT NOT NULL,
PRIMARY KEY (equipe, domaine));""",
        "teams": [[1, "Aube", 1], [2, "Rive", 1], [3, "Pin", 1], [4, "Lac", 0]],
        "tasks": [[10, "son", 1], [11, "lumière", 2], [12, "image", 3]],
        "skills": [[1, "son"], [1, "lumière"], [2, "son"], [3, "image"], [4, "lumière"]],
    }
