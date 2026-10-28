"""V34 SQL stays within the core Terminale clauses; Python builds the reports.

The historical V32 catalogue and its replay hashes are left unchanged.
"""

import sqlite3

from Backend.Core.france import database_case_prose
from Backend.Core.france.database_case_families import _SCHEMAS, build_case
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-database-curriculum-prose-v1"
QUERIES = {
    "sensors": """SELECT c.id, r.temperature
FROM capteur AS c
JOIN releve AS r ON r.capteur = c.id
WHERE r.valide = 1
ORDER BY c.id, r.minute;""",
    "bookings": """SELECT s.numero, r.places
FROM seance AS s
JOIN reservation AS r
 ON r.seance = s.numero
WHERE r.confirmee = 1
ORDER BY s.numero, r.code;""",
    "stock": """SELECT a.reference, m.numero, m.delta
FROM article AS a
JOIN mouvement AS m
 ON m.article = a.reference
ORDER BY a.reference, m.instant;""",
}


def source_rows(seed):
    """Execute only the fixed query for this app-authored source family."""
    case = build_case(seed)
    with sqlite3.connect(":memory:") as database:
        database.executescript(_SCHEMAS[case["family"]])
        for table in case["public"]["tables"]:
            placeholders = ",".join("?" for _ in table["columns"])
            database.executemany(
                f"INSERT INTO {table['name']} VALUES ({placeholders})", table["rows"]
            )
        return [list(row) for row in database.execute(QUERIES[case["family"]])]


def render_case(seed, *, total="6"):
    exercise = database_case_prose.render_case(seed, total=total)
    case = build_case(seed)
    family = case["family"]
    prompt, conclusion, criteria = {
        "sensors": (
            "Écrire une requête donnant l'identifiant du capteur et la température de chaque relevé valide, dans l'ordre des capteurs puis des instants. Donner ses lignes. Pourquoi le résultat ne contient-il pas le capteur 3 ? Indiquer une seconde requête donnant tous les identifiants de capteurs, puis expliquer comment initialiser un bilan Python pour ne pas perdre ceux qui n'ont aucune mesure valide.",
            "La jointure ne trouve aucun relevé valide pour 3. SELECT id FROM capteur ORDER BY id; fournit aussi cet identifiant. Initialiser chaque entrée à None avant de parcourir les mesures conserve les capteurs sans mesure et distingue cette absence de zéro degré.",
            [
                "La projection, la jointure, le filtre valide et le tri sont corrects.",
                "Les lignes du résultat et l'absence du capteur 3 sont expliquées.",
                "La seconde requête et l'initialisation de chaque entrée à None conservent tous les capteurs sans inventer de mesure.",
            ],
        ),
        "bookings": (
            "Écrire une requête donnant, pour chaque groupe confirmé, le numéro de séance et les places demandées, triés par séance puis code de réservation. Donner ses lignes. Pourquoi Cirrus n'y apparaît-elle pas ? Écrire aussi la requête fournissant les numéros et capacités de toutes les séances, puis expliquer comment ces deux résultats permettent de conserver la capacité d'une séance sans réservation lors du calcul Python.",
            "Cirrus n'a aucun groupe confirmé. SELECT numero, capacite FROM seance ORDER BY numero; fournit toutes les capacités. Initialiser le dictionnaire avec ces capacités, puis soustraire les places de chaque ligne confirmée. Une séance sans groupe n'est jamais décrémentée ; la capacité de Cirrus reste 5.",
            [
                "La projection, la jointure, le filtre de confirmation et le tri sont corrects.",
                "Les trois groupes sont listés et l'absence de Cirrus est expliquée.",
                "La seconde requête et l'initialisation par les capacités conservent les séances sans groupe confirmé.",
            ],
        ),
        "stock": (
            "Écrire une requête donnant la référence d'article, le numéro et le delta de chaque mouvement, triés par article puis instant. Donner ses lignes. Écrire une seconde requête donnant référence et stock initial de tous les articles. Expliquer comment un bilan Python utilisant ces deux résultats peut conserver aussi un article sans mouvement, sans confondre ce bilan final avec l'audit chronologique suivant.",
            "SELECT reference, initial FROM article ORDER BY reference; donne les stocks initiaux. Initialiser le bilan avec ces valeurs, puis ajouter chaque delta à son article. Un article sans mouvement garde son stock initial. Le solde final ne révèle pas un stock négatif intermédiaire ; l'audit doit conserver l'ordre des mouvements.",
            [
                "La projection, la jointure et le tri des mouvements sont corrects.",
                "Les cinq lignes respectent leurs références, numéros et variations.",
                "La seconde requête et l'initialisation par les stocks expliquent le cas sans mouvement et la différence avec un audit chronologique.",
            ],
        ),
    }[family]
    question = exercise["questions"][5]
    question.update(
        prompt=prompt,
        answer="```sql\n"
        + QUERIES[family]
        + "\n```\n"
        + f"Lignes : {source_rows(seed)}.\n"
        + conclusion,
        marking=[dict(points="0.25", criterion=criterion) for criterion in criteria],
        operation="design",
    )
    for q in exercise["questions"]:
        q["verification"] = dict(
            kind="curriculum_database_case_contract",
            version=VERSION,
            seed=seed,
            task_id=q["id"],
        )
    NSIExercise.model_validate(exercise)
    return exercise
