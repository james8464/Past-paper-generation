"""Original V32 whole E2 sequences; not yet connected to the publication route.

Each case progresses from relational interpretation to an independently checked
algorithm and a discriminating boundary test. No generated solution is executed.
"""

import ast
import inspect
import json
from decimal import Decimal

from Backend.Core.france.database_case_families import (
    build_case,
    first_stock_deficit,
    remaining_places,
    sensor_extrema,
)
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-database-case-prose-v1"
_MINUTES = (3, 4, 5, 6, 5, 7, 6, 12, 6, 7, 5, 4)


def _solution(function):
    """Keep correction code identical to the tested application algorithm."""
    source = inspect.getsource(function)
    tree = ast.parse(source)
    node = tree.body[0]
    if ast.get_docstring(node):
        doc = node.body[0]
        lines = source.splitlines()
        source = "\n".join(lines[: doc.lineno - 1] + lines[doc.end_lineno :])
    return "```python\n" + source.rstrip() + "\n```"


def _item(prompt, answer, criteria, operation, code):
    return dict(
        prompt=prompt, answer=answer, criteria=criteria, operation=operation, code=code
    )


def _sensors(case):
    result = case["expected"]["result"]
    low, high = result[0][1:]
    return [
        _item(
            "Partie A — fiabilité des mesures. Peut-on employer zone comme clé primaire de capteur si plusieurs appareils surveillent la même zone ? Justifiez.",
            "Non : deux appareils peuvent partager une zone. id distingue chaque appareil.",
            ["Le défaut d'unicité de zone est expliqué."],
            "justify",
            "BDD-MODELE",
        ),
        _item(
            "Une nouvelle mesure porte id = 16, capteur = 9, minute = 30, temperature = 22, valide = 1. Distinguez la contrainte respectée par son identifiant de celle qui interdit son insertion dans les tables fournies.",
            "16 est un identifiant nouveau. Le capteur 9 n'existe pas : la clé étrangère refuse cette ligne.",
            ["L'identifiant 16 est nouveau.", "La référence 9 absente est identifiée."],
            "analyse",
            "BDD-MODELE",
        ),
        _item(
            "Construisez une requête donnant minute et temperature des relevés valides du capteur 1, du plus ancien au plus récent. Indiquez les lignes obtenues.",
            f"```sql\nSELECT minute, temperature\nFROM releve\nWHERE capteur=1 AND valide=1\nORDER BY minute;\n```\nRésultat : (0, {low}), (10, {high}).",
            [
                "Projection et deux filtres sont exacts.",
                "Tri et deux lignes sont exacts.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        _item(
            "On calcule le maximum du capteur 1 sans consulter valide. Donnez ce maximum, comparez-le au maximum exploitable, puis expliquez pourquoi la mesure exclue doit néanmoins être conservée.",
            f"Le maximum brut vaut 99, contre {high} pour les mesures valides. Conserver le relevé brut permet de retrouver l'anomalie et de contrôler son exclusion.",
            [
                "Les deux maxima sont distingués.",
                "La conservation pour audit est justifiée.",
            ],
            "analyse",
            "BDD-ANOMALIES",
        ),
        _item(
            "Partie B — bilan complet. Pour chaque capteur, donnez la température minimale et la maximale après contrôle. Écrivez « aucune mesure valide » lorsque ces valeurs ne sont pas définies.",
            f"Capteur 1 : {low}, {high}. Capteur 2 : {result[1][1]}, {result[1][2]}. Capteur 3 : aucune mesure valide.",
            [
                "Les extrema des capteurs 1 et 2 sont exacts.",
                "L'absence de valeur pour 3 n'est pas remplacée par zéro.",
            ],
            "apply",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Le bilan emploie FROM capteur c LEFT JOIN releve r ON r.capteur=c.id AND r.valide=1, puis GROUP BY c.id. Écrivez le SELECT et le tri nécessaires. Pourquoi déplacer r.valide=1 dans WHERE ferait-il disparaître le capteur 3 ? On rappelle qu'une comparaison avec NULL ne vaut pas vrai.",
            "```sql\nSELECT c.id,\n       MIN(r.temperature), MAX(r.temperature)\nFROM capteur c LEFT JOIN releve r\nON r.capteur=c.id AND r.valide=1\nGROUP BY c.id ORDER BY c.id;\n```\nPour 3, la jointure produit des colonnes r à NULL. WHERE r.valide=1 éliminerait cette ligne, alors que le filtre dans ON conserve le capteur.",
            [
                "MIN et MAX portent sur temperature.",
                "Le regroupement et le tri conservent une ligne par capteur.",
                "L'effet de WHERE sur la ligne à NULL est expliqué.",
            ],
            "justify",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Partie C — calcul en mémoire. Les observations sont des triplets (capteur, temperature, valide), avec valide booléen. Un programme initialise tous les minima et maxima à 0. Sur les deux mesures valides −8 et −12 d'un même appareil, quelle borne est fausse ? Proposez un état initial distinguant l'absence de mesure.",
            "Le maximum resterait 0, qui n'a pas été observé ; le minimum deviendrait −12. None distingue l'absence de mesure. La première mesure valide initialise ensuite les deux bornes.",
            [
                "Le maximum nul erroné est expliqué.",
                "None puis l'initialisation des deux bornes sont proposés.",
            ],
            "debug",
            "LP-DEBUG",
        ),
        _item(
            "Écrivez sensor_extrema(sensor_ids, observations). Les identifiants sont distincts et toutes les observations désignent un identifiant connu. Le résultat est un dictionnaire associant à chacun None ou un couple (minimum, maximum) calculé sur les seules observations valides. Parcourez observations une seule fois et ne modifiez aucun argument.",
            _solution(sensor_extrema),
            [
                "Tous les identifiants sont initialisés à None dans un nouveau dictionnaire.",
                "Les observations invalides sont ignorées.",
                "La première valeur initialise les deux bornes ; les suivantes actualisent min et max.",
                "Une seule lecture des observations, aucun argument modifié et retour complet.",
            ],
            "design",
            "LP-MODULARITE",
        ),
        _item(
            "Tracez votre dictionnaire après les relevés 11, 12 et 13, dans cet ordre, en ne montrant que l'entrée du capteur 1. Expliquez l'absence de changement au dernier relevé.",
            f"Après 11 : ({low}, {low}) ; après 12 : ({low}, {high}) ; après 13 : ({low}, {high}). Le relevé 13 est invalide.",
            [
                "Les trois états sont exacts.",
                "L'absence de changement est reliée à valide=0.",
            ],
            "apply",
            "LP-DEBUG",
        ),
        _item(
            "Une correction ultérieure valide le relevé 13. Écrivez l'UPDATE limité à cette mesure, puis donnez les nouvelles bornes du capteur 1. Cette hypothèse ne change pas les réponses précédentes.",
            f"```sql\nUPDATE releve SET valide=1 WHERE id=13;\n```\nLe minimum reste {low} ; le maximum devient 99.",
            ["L'UPDATE ne cible que 13.", "Les deux nouvelles bornes sont exactes."],
            "apply",
            "BDD-SQL-MUTATION",
        ),
        _item(
            "Quel invariant relie l'entrée d'un capteur aux observations déjà parcourues ? Formulez-le aussi lorsqu'aucune de ces observations n'est valide.",
            "Après chaque préfixe traité, l'entrée vaut les extrema des températures valides de ce capteur dans ce préfixe, ou None s'il n'en existe aucune.",
            ["Les extrema du préfixe et le cas sans valeur sont explicités."],
            "justify",
            "LP-MODULARITE",
        ),
        _item(
            "Construisez un test d'une seule observation qui distingue « aucun relevé valide » d'une température réellement égale à zéro. Donnez le résultat attendu.",
            "Avec sensor_ids=[1] et observations=[(1,0,True)], le résultat attendu est {1:(0,0)}, pas {1:None}.",
            ["Le test valide à zéro et le couple (0,0) attendu sont fournis."],
            "design",
            "LP-DEBUG",
        ),
    ]


def _bookings(case):
    return [
        _item(
            "Partie A — groupes et séances. Deux groupes peuvent réserver la même séance. Pourquoi seance ne peut-il donc pas remplacer code comme clé de reservation ?",
            "Plusieurs lignes ont le même numéro de séance ; code identifie une réservation, seance ne l'identifie pas.",
            ["La multiplicité des groupes empêche l'unicité de seance."],
            "justify",
            "BDD-MODELE",
        ),
        _item(
            "Calculez pour Atlas le nombre de réservations confirmées et le nombre de places occupées. Quelle confusion commettrait un rapport employant COUNT(*) pour mesurer les places ?",
            "Deux réservations confirmées occupent cinq places. COUNT(*) compte des groupes, pas leurs membres.",
            [
                "Deux groupes et cinq places sont calculés.",
                "La différence entre compter les lignes et sommer places est expliquée.",
            ],
            "analyse",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Affichez par SQL code et places des demandes encore en attente, classées par code. Donnez la sortie pour le festival.",
            "```sql\nSELECT code, places FROM reservation\nWHERE confirmee=0 ORDER BY code;\n```\nUne ligne : (13,2).",
            [
                "Le filtre confirmee=0 et les colonnes sont corrects.",
                "Le tri et la ligne (13,2) sont indiqués.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Pour Boreal, un rapport soustrait aussi les groupes non confirmés. Calculez la disponibilité qu'il affiche et la disponibilité correcte. Identifiez la réservation responsable de l'écart.",
            "Le rapport affiche 0 au lieu de 2 : il soustrait à tort les deux places de la réservation 13 en attente.",
            [
                "Les disponibilités 0 et 2 sont distinguées.",
                "La réservation 13 non confirmée explique l'écart.",
            ],
            "debug",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Partie B — alerte de surcapacité. Présentez les disponibilités des trois séances et désignez celle qui nécessite une intervention. Une valeur négative doit rester visible.",
            "Atlas : −1 ; Boreal : 2 ; Cirrus : 5. Atlas dépasse sa capacité d'une place.",
            [
                "Les trois disponibilités sont exactes.",
                "Atlas est signalé avec un dépassement d'une place.",
            ],
            "apply",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Établissez une requête retournant numero et disponibilité pour toutes les séances, même sans réservation. Utilisez LEFT JOIN ; COALESCE(x,0) remplace NULL par 0. Justifiez SUM plutôt que COUNT et le résultat de Cirrus.",
            "```sql\nSELECT s.numero,\n       s.capacite-COALESCE(SUM(r.places),0)\nFROM seance s LEFT JOIN reservation r\nON r.seance=s.numero AND r.confirmee=1\nGROUP BY s.numero, s.capacite\nORDER BY s.numero;\n```\nSUM additionne les membres des groupes. Cirrus conserve ses cinq places : aucune réservation ne contribue à la somme.",
            [
                "La jointure conserve toutes les séances et ne retient que les groupes confirmés.",
                "La soustraction emploie SUM et COALESCE correctement.",
                "SUM est justifié et Cirrus conserve cinq places.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Partie C — contrôle avant affichage. Une fonction calcule correctement les places libres, puis remplace chaque valeur négative par 0. Pourquoi le résultat pour Atlas ne permet-il plus de distinguer une séance exactement pleine d'une séance surchargée ? Proposez une correction.",
            "0 pourrait signifier quatre places occupées ou plus. Il faut conserver −1 pour Atlas, puis décider séparément de l'affichage de l'alerte.",
            [
                "La perte de distinction entre plein et surchargé est expliquée.",
                "Le résultat négatif est conservé, sans écrêtage.",
            ],
            "debug",
            "LP-DEBUG",
        ),
        _item(
            "Construisez remaining_places(capacities, reservations). capacities associe numéro de séance et capacité ; reservations contient (séance, places, confirmation), où confirmation est booléenne. Les séances existent et places est strictement positif. Retournez un nouveau dictionnaire des places libres, en une traversée des réservations. Les séances sans groupe restent présentes et les dépassements restent négatifs.",
            _solution(remaining_places),
            [
                "Le résultat est une copie indépendante de capacities.",
                "Seules les réservations confirmées sont décomptées.",
                "La taille du groupe est soustraite de sa séance, sans écrêter à zéro.",
                "Une traversée, séances sans groupe conservées et dictionnaire retourné.",
            ],
            "design",
            "LP-MODULARITE",
        ),
        _item(
            "La demande 13 devient confirmée, puis le groupe 14 annule sa confirmation. À chaque étape, recalculez les places libres de Boreal. Les deux actions s'appliquent successivement à la situation initiale.",
            "Initialement 2 places libres. Après confirmation de 13 : 0. Après annulation de 14 : 1. Le groupe 13 occupe deux places ; le groupe 14 en libère une.",
            [
                "Après confirmation, la disponibilité vaut 0.",
                "Après annulation, elle vaut 1 avec une place libérée.",
            ],
            "apply",
            "LP-DEBUG",
        ),
        _item(
            "Écrivez les deux UPDATE réalisant ces actions, sans supprimer les demandes. Expliquez pourquoi une annulation ne doit pas changer places ni le numéro de séance.",
            "```sql\nUPDATE reservation SET confirmee=1\nWHERE code=13;\nUPDATE reservation SET confirmee=0\nWHERE code=14;\n```\nSeul le statut change ; taille et séance restent disponibles pour l'historique de la demande.",
            [
                "Les deux statuts sont modifiés sur leurs seuls codes.",
                "Les autres attributs sont conservés pour l'historique.",
            ],
            "apply",
            "BDD-SQL-MUTATION",
        ),
        _item(
            "La contrainte places <= capacite, contrôlée séparément pour chaque réservation, empêcherait-elle toujours une surcapacité ? Utilisez Atlas pour répondre.",
            "Non : 2 et 3 sont chacun au plus 4, mais leur somme 5 dépasse 4. Il faut contrôler le total des groupes confirmés.",
            ["Le contre-exemple 2+3>4 réfute le contrôle ligne par ligne."],
            "justify",
            "BDD-SGBD",
        ),
        _item(
            "Donnez un test montrant qu'une demande non confirmée, même plus grande que la capacité, ne change pas le calcul des places libres.",
            "Pour capacities={1:3} et reservations=[(1,8,False)], le résultat est {1:3}.",
            ["Un groupe en attente supérieur à la capacité laisse celle-ci intacte."],
            "design",
            "LP-DEBUG",
        ),
    ]


def _stock(case):
    initial = case["public"]["tables"][0]["rows"][0][2]
    return [
        _item(
            "Partie A — journal des mouvements. Un mouvement doit désigner un article existant. Quel lien entre attributs permet au SGBD de vérifier cette obligation ?",
            "mouvement.article référence article.reference par une clé étrangère.",
            ["La clé étrangère et sa cible sont données."],
            "apply",
            "BDD-MODELE",
        ),
        _item(
            "Le journal interdit deux mouvements d'un même article au même instant. Cette règle exige-t-elle que tous les instants du journal soient distincts ? Appuyez votre réponse sur les données.",
            "Non : les mouvements 11, 13 et 15 ont l'instant 1, mais concernent des articles distincts. Seul le couple (article,instant) est unique.",
            [
                "L'unicité du couple, non de instant seul, est expliquée.",
                "Deux mouvements d'articles distincts au même instant sont cités.",
            ],
            "analyse",
            "BDD-MODELE",
        ),
        _item(
            "Extrayez numero et delta des mouvements de Lentille dans leur ordre chronologique, avec une requête SQL. Écrivez les deux lignes renvoyées.",
            f"```sql\nSELECT numero, delta FROM mouvement\nWHERE article=1 ORDER BY instant;\n```\n(11, {-initial - 2}), (12, 4).",
            [
                "La requête filtre l'article 1 et ordonne par instant.",
                "Les deux numéros et variations sont exacts.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Un audit regarde uniquement le stock final de Lentille. Calculez les stocks après chacun de ses mouvements et montrez pourquoi le verdict « aucun manque » serait faux.",
            f"Le stock initial {initial} devient −2 après 11 puis 2 après 12. Le réapprovisionnement tardif masque le manque antérieur.",
            [
                "Les stocks successifs −2 puis 2 sont exacts.",
                "Le solde final positif ne justifie pas la faisabilité de chaque étape.",
            ],
            "analyse",
            "LP-DEBUG",
        ),
        _item(
            "Partie B — rapprochement de clôture. Calculez le stock final de chaque article. Distinguez la grandeur calculée ici du premier mouvement impossible étudié ensuite.",
            "Lentille : 2 ; Pied : 4 ; Cable : 6. Le solde final additionne toutes les variations ; il ne localise pas la première rupture chronologique.",
            [
                "Les trois soldes 2,4,6 sont exacts.",
                "Solde final et localisation de la rupture sont distingués.",
            ],
            "apply",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Pour préparer ce rapprochement, écrivez une requête donnant reference et stock final de tous les articles, y compris ceux sans mouvement. Employez une jointure gauche et COALESCE(x,0), qui remplace NULL par zéro. Justifiez l'ajout du stock initial.",
            "```sql\nSELECT a.reference,\n       a.initial+COALESCE(SUM(m.delta),0)\nFROM article a LEFT JOIN mouvement m\nON m.article=a.reference\nGROUP BY a.reference, a.initial\nORDER BY a.reference;\n```\nLes variations sont relatives au stock initial, pas à zéro. Sans mouvement, la somme remplacée par zéro laisse le stock initial inchangé.",
            [
                "La jointure conserve les articles sans mouvement.",
                "SUM(delta), COALESCE et initial sont combinés correctement.",
                "La signification relative des variations et le cas sans mouvement sont justifiés.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        _item(
            "Partie C — validation chronologique. Un développeur trie delta par ordre décroissant avant l'audit. Sur Lentille, tracez cette version et expliquez ce que le tri détruit.",
            f"Il traite +4 avant {-initial - 2} : stocks {initial + 4} puis 2, jamais négatifs. Le tri efface l'ordre réel et avance artificiellement le réapprovisionnement.",
            [
                "Les deux stocks après tri sont exacts.",
                "L'inversion du réapprovisionnement et de la sortie est expliquée.",
            ],
            "debug",
            "LP-DEBUG",
        ),
        _item(
            "Écrivez first_stock_deficit(initial, movements). initial est positif ou nul ; movements est une suite de couples (identifiant, variation signée), déjà classée chronologiquement pour un seul article. Retournez l'identifiant du premier mouvement qui rend le stock négatif, ou None si tous sont possibles. Un stock nul est autorisé. N'altérez ni l'ordre ni les données.",
            _solution(first_stock_deficit),
            [
                "Un solde local est initialisé au stock de départ.",
                "Chaque variation est ajoutée dans l'ordre fourni.",
                "Le premier solde strictement négatif entraîne le retour de son identifiant.",
                "None est retourné après une traversée sans déficit, sans modifier l'entrée.",
            ],
            "design",
            "LP-MODULARITE",
        ),
        _item(
            "Avec un stock initial de 2 et les mouvements (41,−2), (57,+3), (63,−4), tracez les soldes examinés et donnez le retour. Pourquoi ne faut-il retourner ni 2 ni 3 ?",
            "Soldes 0,3,−1 ; retour 63. 2 serait un indice dans la liste, 3 un rang ; le contrat exige l'identifiant du mouvement.",
            [
                "Les soldes et le retour 63 sont exacts.",
                "L'identifiant est distingué de l'indice et du rang.",
            ],
            "apply",
            "LP-DEBUG",
        ),
        _item(
            "Dans une simulation indépendante, le réapprovisionnement 12 est avancé à l'instant 0. Écrivez l'UPDATE, puis donnez le verdict d'audit de Lentille. Ne modifiez aucune variation.",
            f"```sql\nUPDATE mouvement SET instant=0 WHERE numero=12;\n```\nLes stocks deviennent {initial + 4} puis 2 : aucun déficit, donc None.",
            [
                "Seul l'instant du mouvement 12 est remplacé par 0.",
                "Le nouvel ordre, ses soldes et le retour None sont cohérents.",
            ],
            "apply",
            "BDD-SQL-MUTATION",
        ),
        _item(
            "Avant de traiter le mouvement suivant, quelle somme représente le solde local ? Utilisez cette propriété pour justifier un arrêt au premier déficit.",
            "Le solde est initial plus la somme des variations déjà traitées. Au premier résultat négatif, les préfixes antérieurs étaient valides ; l'identifiant trouvé est donc bien le premier fautif.",
            ["L'invariant de préfixe justifie le caractère premier du déficit."],
            "justify",
            "LP-MODULARITE",
        ),
        _item(
            "Choisissez un test minimal qui réfute une version utilisant <= 0 au lieu de < 0. Précisez le résultat correct.",
            "initial=2, movements=[(7,−2)] : le solde vaut zéro, donc le retour correct est None, et non 7.",
            ["Un solde exactement nul distingue les deux comparaisons."],
            "design",
            "LP-DEBUG",
        ),
    ]


def render_case(seed):
    case = build_case(seed)
    public = case["public"]
    items = {"sensors": _sensors, "bookings": _bookings, "stock": _stock}[
        case["family"]
    ](case)
    materials = [
        dict(
            kind="table",
            id=table["name"],
            title=table["name"],
            columns=table["columns"],
            rows=[[str(value) for value in row] for row in table["rows"]],
        )
        for table in public["tables"]
    ]
    questions = []
    for index, item in enumerate(items):
        identifier = "2" + "abcdefghijkl"[index]
        questions.append(
            dict(
                id=identifier,
                prompt=item["prompt"],
                answer=item["answer"],
                points=str((Decimal("0.25") * len(item["criteria"])).normalize()),
                marking=[
                    dict(points="0.25", criterion=criterion)
                    for criterion in item["criteria"]
                ],
                material_ids=[m["id"] for m in materials],
                curriculum_codes=[item["code"]],
                operation=item["operation"],
                difficulty=4 if index == 7 else 2 if index < 3 else 3,
                estimated_minutes=_MINUTES[index],
                verification=dict(
                    kind="database_case_contract",
                    version=VERSION,
                    seed=seed,
                    case_sha256=case["sha256"],
                    task_id=identifier,
                ),
            )
        )
    candidate = dict(
        id="2",
        title=public["title"],
        context=public["context"] + "\n\n" + public["schema"],
        topics=["bases-donnees", "langages-programmation"],
        minutes=70,
        target_points="6",
        materials=materials,
        questions=questions,
    )
    NSIExercise.model_validate(candidate)
    return candidate


def verify_candidate(candidate, seed):
    """Closed app-owned content binding; never accept altered marking or sources."""
    try:
        return json.dumps(candidate, ensure_ascii=False, sort_keys=True) == json.dumps(
            render_case(seed), ensure_ascii=False, sort_keys=True
        )
    except (ValueError, TypeError, KeyError):
        return False
