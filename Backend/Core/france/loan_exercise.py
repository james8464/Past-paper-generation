# original relational/interval reasoning for an experimental fourth family

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.loan_case import ACTIVE_LOANS_QUERY, build_case
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-loan-exercise-v1"
MINUTES = (4, 5, 6, 7, 4, 8, 6, 6, 9, 6, 4, 5)


# these tested functions are also printed at 16 pt. Keep their lines short
# fmt: off
def actifs(exemplaires, emprunts, instant):
    resultat = {}
    for code, _titre in exemplaires:
        resultat[code] = []
    for pret in emprunts:
        identifiant, code = pret[0], pret[1]
        debut, retour = pret[3], pret[4]
        commence = debut <= instant
        en_cours = (
            retour is None or instant < retour
        )
        if commence and en_cours:
            resultat[code].append(identifiant)
    return resultat


def conflits(emprunts):
    resultat = []
    for i in range(len(emprunts)):
        a = emprunts[i]
        for j in range(i + 1, len(emprunts)):
            b = emprunts[j]
            avant = (
                b[4] is None or a[3] < b[4]
            )
            apres = (
                a[4] is None or b[3] < a[4]
            )
            meme = a[1] == b[1]
            if meme and avant and apres:
                paire = sorted([a[0], b[0]])
                resultat.append(paire)
    return sorted(resultat)
# fmt: on


def render_case(seed, *, total="6"):
    if type(total) is not str or total != "6":
        raise ValueError("This loan exercise allocates exactly six points")
    case = build_case(seed)
    source = _solution(actifs)
    scaffold = (
        source.replace("resultat[code] = []", "__A__")
        .replace("debut <= instant", "__B__")
        .replace("retour is None or instant < retour", "__C__")
        .replace("resultat[code].append(identifiant)", "__D__")
    )
    query = ACTIVE_LOANS_QUERY.replace("?", "4")
    items = [
        (
            "Identifier les clés primaires et la clé étrangère. Le titre peut-il remplacer code comme clé primaire d'exemplaire ? Justifier avec les données, sans confondre un titre et une copie physique.",
            "exemplaire.code et emprunt.id sont les clés primaires. emprunt.exemplaire référence exemplaire.code. Atlas apparaît pour les copies 10 et 11 : le titre n'est pas unique et ne peut pas identifier une copie.",
            [
                "Les clés et le lien référentiel sont exacts.",
                "Le doublon Atlas réfute le choix du titre comme clé de copie.",
            ],
            "apply",
            "BDD-MODELE",
        ),
        (
            "À t = 4, dresser pour chaque copie la liste des identifiants d'emprunts actifs. En déduire les copies disponibles. Expliquer pourquoi les emprunts 101 et 102 ne se chevauchent pas malgré leur date commune.",
            "10 : [102] ; 11 : [103] ; 20 : [104] ; 30 : []. Seule 30 est disponible. 101 occupe [0,4[ et 102 commence à 4 : la fin exclue permet la remise en prêt à cet instant.",
            [
                "Les quatre listes et la disponibilité de 30 sont exactes.",
                "La borne de retour exclue explique l'absence de chevauchement 101/102.",
            ],
            "apply",
            "BDD-MODELE",
        ),
        (
            "Un programme annonce qu'une copie est disponible si elle possède au moins un ancien emprunt retourné avant ou à t = 4. Il utilise :\n```sql\nSELECT e.code\nFROM exemplaire AS e\nJOIN emprunt AS p\n ON p.exemplaire = e.code\nWHERE p.retour <= 4\nORDER BY e.code;\n```\nDonner son résultat et expliquer ses deux erreurs sur les copies 10 et 30.",
            "Il renvoie [10]. Le retour de 101 ne prouve pas l'absence d'un nouvel emprunt : 102 occupe déjà 10. La jointure interne exclut 30, qui n'a jamais été empruntée mais reste disponible.",
            [
                "Le résultat [10] est relié au retour de 101 malgré l'emprunt actif 102.",
                "L'absence de ligne d'emprunt pour 30 explique son exclusion incorrecte.",
            ],
            "debug",
            "BDD-SQL-SELECT",
        ),
        (
            "Compléter les quatre expressions pour lister le code, le titre et l'identifiant des emprunts actifs à t = 4 :\n```sql\nSELECT e.code, e.titre, p.id\nFROM exemplaire AS e\nJOIN emprunt AS p ON __A__\nWHERE __B__ AND (__C__ OR __D__)\nORDER BY e.code, p.id;\n```\nDonner les lignes obtenues. Une seconde requête SELECT code FROM exemplaire ORDER BY code donne tous les codes. Expliquer comment utiliser les deux résultats dans Python pour retrouver les copies disponibles sans perdre celles qui n'ont jamais été empruntées.",
            "```sql\n"
            + query
            + ";\n```\nA : p.exemplaire = e.code ; B : p.debut <= 4 ; C : p.retour IS NULL ; D : p.retour > 4. Lignes : (10, Atlas, 102), (11, Atlas, 103), (20, Boreal, 104). Initialiser tous les codes, puis marquer occupés ceux du résultat des prêts actifs : seul 30 reste disponible, même sans ligne d'emprunt historique.",
            [
                "La jointure et les conditions d'activité utilisent début inclus, retour exclu et IS NULL ; les trois lignes sont exactes.",
                "La liste de tous les codes permet de conserver 30 puis d'exclure les trois copies occupées, sans confondre absence de prêt actif et absence d'historique.",
            ],
            "design",
            "BDD-SQL-SELECT",
        ),
        (
            "On remplace p.retour IS NULL par p.retour = NULL. Pourquoi ce test n'identifie-t-il pas les retours absents en SQL ? Expliquer aussi pourquoi ne tester que retour IS NULL, sans le début, pourrait déclarer une copie occupée avant son prochain prêt.",
            "NULL représente une information absente ; une comparaison ordinaire avec NULL ne donne pas vrai. Il faut IS NULL. L'emprunt 102, sans retour, commence à 4 : sa seule absence de retour ne le rend pas actif à t = 3.",
            [
                "IS NULL est distingué de = NULL pour une valeur absente.",
                "Le début futur de 102 fournit le contre-exemple à l'oubli de debut <= t.",
            ],
            "analyse",
            "BDD-SQL-SELECT",
        ),
        (
            "Compléter actifs. exemplaires contient les couples (code, titre) ; emprunts contient (id, exemplaire, lecteur, debut, retour). Dans ces listes Python, None correspond au NULL de retour. La fonction doit créer un nouveau dictionnaire, conserver les copies sans prêt actif et ne modifier aucune liste reçue.\n"
            + scaffold,
            source,
            [
                "L'initialisation conserve chaque copie avec une liste distincte, y compris les copies jamais empruntées.",
                "Les deux bornes et le retour None sélectionnent les prêts actifs ; leur identifiant est ajouté sous la bonne copie, sans mutation des sources.",
            ],
            "design",
            "LP-DEBUG",
        ),
        (
            "On propose d'ajouter le prêt 105 pour la copie 11, lecteur Eli, début 5 et retour 7. Ses clés respectent-elles le schéma ? Quel conflit temporel subsiste ? Donner les identifiants et l'intervalle commun. Cette proposition est refusée et n'est pas ajoutée à la base.",
            "105 est une nouvelle clé primaire et la copie 11 existe : les contraintes de clés sont satisfaites. Les prêts 103 sur [1,6[ et 105 sur [5,7[ se recouvrent sur [5,6[. Une clé étrangère valide ne garantit pas l'absence de prêts simultanés pour une même copie.",
            [
                "Les contraintes de clés sont distinguées de la règle temporelle.",
                "Le conflit 103/105 et son intervalle [5,6[ sont identifiés malgré des clés valides.",
            ],
            "analyse",
            "BDD-ANOMALIES",
        ),
        (
            "Une vérification établit que 103 a été rendu à t = 5, et non à 6 comme enregistré. On corrige cette date, puis on enregistre le prêt de la copie 11 à Eli dès t = 5, identifiant 105, sans retour connu. Écrire les requêtes UPDATE et INSERT correspondantes. Pourquoi le nouveau prêt devient-il possible alors qu'il a été refusé dans la question précédente ?",
            "```sql\nUPDATE emprunt SET retour = 5\nWHERE id = 103;\nINSERT INTO emprunt (\n id, exemplaire, lecteur, debut, retour\n) VALUES (105, 11, 'Eli', 5, NULL);\n```\nAprès correction, 103 occupe [1,5[ et 105 commence à 5 : les intervalles ne se recouvrent plus. Le nouveau prêt est créé après cette correction, pas dans S0 inchangé.",
            [
                "L'UPDATE corrige le retour de 103 à 5 et l'INSERT fournit tous les champs de 105 avec début 5 et retour NULL.",
                "La nouvelle borne commune 5 explique pourquoi la correction préalable supprime le conflit, contrairement à la proposition sur S0.",
            ],
            "design",
            "BDD-SQL-MUTATION",
        ),
        (
            "Écrire conflits(emprunts), qui renvoie toutes les paires d'identifiants de prêts simultanés d'une même copie. Tester chaque paire de lignes une seule fois, sans comparer une ligne à elle-même. Deux intervalles positifs [a,b[ et [c,d[ se chevauchent si c < b et a < d ; un retour None ne fournit aucune borne de fin. Trier chaque paire puis la liste finale. Ne pas modifier emprunts.",
            _solution(conflits),
            [
                "Les paires de lignes sont parcourues une fois avec j > i et seuls les prêts de la même copie sont comparés.",
                "Les deux inégalités strictes, les retours None, le tri et l'absence de mutation sont respectés.",
            ],
            "design",
            "LP-MODULARITE",
        ),
        (
            "Pour une même copie, les prêts 1, 2, 3 occupent respectivement [0,10[, [2,3[ et [4,5[. Un algorithme trie par début et compare seulement deux lignes consécutives. Donner toutes les paires en conflit et montrer celle qu'il oublie. Combien de paires la double boucle de conflits teste-t-elle pour n prêts ?",
            "Les conflits sont [1,2] et [1,3] ; 2 et 3 ne se chevauchent pas. La comparaison des seuls voisins oublie [1,3]. La double boucle teste n(n-1)/2 paires, donc son coût est quadratique ; le tri final du résultat est un travail supplémentaire.",
            [
                "Les deux conflits et l'oubli de la paire non voisine sont démontrés sur les intervalles.",
                "n(n-1)/2 compte les tests de paires ; ce coût est distingué du tri du résultat.",
            ],
            "justify",
            "LP-DEBUG",
        ),
        (
            "Pourquoi supprimer directement la copie 10 alors que les prêts 101 et 102 la référencent viole-t-il la clé étrangère ? On veut conserver l'historique des prêts : expliquer pourquoi effacer d'abord ces deux lignes, bien que cela supprime l'obstacle référentiel, ne satisfait pas ce besoin.",
            "La suppression laisserait des prêts référençant une copie inexistante et doit être refusée par la contrainte. Effacer 101 et 102 détruirait l'historique demandé ; il faut conserver la copie ou prévoir une représentation d'archive adaptée, plutôt que confondre intégrité référentielle et conservation des données.",
            [
                "La référence invalide est expliquée.",
                "La suppression préalable des prêts est rejetée pour perte de l'historique, sans la présenter comme une solution au besoin donné.",
            ],
            "justify",
            "BDD-ANOMALIES",
        ),
        (
            "On utilise maintenant la base après la correction de 103 et l'insertion correcte de 105 à t = 5. Donner les copies disponibles à t = 6, puis expliquer le résultat pour 11, 20 et 30. Peut-on remplacer l'interrogation à l'instant demandé par une liste figée des copies déclarées libres à t = 4 ?",
            "20 et 30 sont disponibles. 11 n'est pas libre : 103 finit désormais à 5 mais 105 l'occupe depuis 5. 20 est revenue à 5 ; 30 n'a aucun prêt. Une liste calculée à 4 ne contiendrait que 30 et manquerait le retour de 20 ; la disponibilité dépend de l'instant et des données courantes.",
            [
                "Les disponibilités sont reliées aux trois situations : nouveau prêt de 11, retour de 20, absence de prêt de 30.",
                "Le contre-exemple du retour de 20 réfute la réutilisation d'une liste figée à 4.",
            ],
            "analyse",
            "BDD-SQL-SELECT",
        ),
    ]
    questions = []
    for index, ((prompt, answer, criteria, operation, code), minutes) in enumerate(
        zip(items, MINUTES, strict=True)
    ):
        questions.append(
            dict(
                id="2" + "abcdefghijkl"[index],
                prompt=prompt,
                answer=answer,
                points="0.5",
                marking=[dict(points="0.25", criterion=c) for c in criteria],
                material_ids=["exemplaire", "emprunt"],
                curriculum_codes=[code],
                operation=operation,
                difficulty=4 if index in (8, 9) else 2 if index < 2 else 3,
                estimated_minutes=minutes,
                verification=dict(
                    kind="loan_case_contract",
                    version=VERSION,
                    seed=seed,
                    task_id="2" + "abcdefghijkl"[index],
                ),
            )
        )
    exercise = dict(
        id="2",
        title="Retours et nouveaux prêts : une disponibilité à reconstruire",
        context=(
            "Une bibliothèque distingue les titres et leurs exemplaires physiques. Chaque prêt occupe une seule copie depuis debut inclus jusqu'à retour exclu. "
            "Les dates sont des entiers positifs ou nuls ; retour vaut NULL si le prêt n'est pas encore revenu. Un retour connu est strictement postérieur au début. "
            "Deux prêts d'une même copie ne doivent pas se chevaucher. Les questions portent sur un état cohérent du catalogue ; on ignore les accès concurrents. "
            "exemplaire(code, titre) a pour clé primaire code ; emprunt(id, exemplaire, lecteur, debut, retour) a pour clé primaire id et pour clé étrangère exemplaire vers exemplaire.code. "
            "Les titres et lecteurs sont du texte. Les deux tables suivantes constituent l'état initial S0. Sauf indication contraire, les questions repartent de S0. Les propositions refusées n'en modifient pas les lignes."
        ),
        topics=["bases-donnees", "langages-programmation"],
        minutes=70,
        target_points=total,
        materials=[
            dict(
                kind="table",
                id="exemplaire",
                title="exemplaire",
                columns=["code", "titre"],
                rows=[[str(v) for v in row] for row in case["copies"]],
            ),
            dict(
                kind="table",
                id="emprunt",
                title="emprunt",
                columns=["id", "exemplaire", "lecteur", "debut", "retour"],
                rows=[
                    ["NULL" if v is None else str(v) for v in row]
                    for row in case["loans"]
                ],
            ),
        ],
        questions=questions,
    )
    NSIExercise.model_validate(exercise)
    return exercise
