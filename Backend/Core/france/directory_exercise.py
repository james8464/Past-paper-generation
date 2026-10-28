"""Original object-graph construction sequence, awaiting package acceptance."""

import hashlib
import json
from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.directory_case import (
    Dossier,
    build_case,
    distance_minimale,
    explorer,
)
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-directory-exercise-v1"


def render_case(seed):
    case = build_case(seed)
    digest = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
    items = [
        (
            "Partie A. La figure représente des raccourcis orientés. Donner un sommet isolé et un sommet accessible directement depuis deux dossiers distincts.",
            "e est isolé. c est accessible directement depuis a et b.",
            [("0.25", "Les sommets e et c sont identifiés avec leurs rôles.")],
            "apply", "SD-GRAPHE",
        ),
        (
            "Cette structure est-elle un arbre enraciné en r ? Donner deux raisons indépendantes tirées de la figure, dont un cycle explicite.",
            "Non : c possède deux prédécesseurs a et b ; le cycle a, c, d, a interdit également un arbre. e n'est pas accessible depuis r.",
            [("0.25", "Les deux prédécesseurs de c sont identifiés."),
             ("0.25", "Le cycle orienté a, c, d, a est donné.")],
            "justify", "SD-ARBRE",
        ),
        (
            "Construire un dictionnaire successeurs : chaque clé est un identifiant de sommet ; sa valeur est la liste des identifiants atteints par un arc sortant. Ranger les successeurs par identifiant croissant, y compris pour e.",
            "{'r': ['a', 'b'], 'a': ['c'], 'b': ['c'], 'c': ['d'], 'd': ['a'], 'e': []}.",
            [("0.25", "Les six clés et leurs arcs sont exacts."),
             ("0.25", "Les listes sont ordonnées et e possède une liste vide.")],
            "design", "SD-GRAPHE",
        ),
        (
            "On construit les objets par Dossier(identifiant, nom). Quels attributs doit créer le constructeur ? Pourquoi le seul nom ne suffit-il pas pour identifier un dossier ?",
            "identifiant, nom et une liste enfants vide propre à l'objet. a et b portent tous deux le nom Archives : leur identifiant les distingue.",
            [("0.25", "Les trois attributs et le défaut d'unicité du nom sont expliqués.")],
            "analyse", "SD-POO",
        ),
        (
            "Écrire le constructeur puis la méthode relier(self, autre). Cette méthode ajoute l'objet autre à enfants seulement si son identifiant n'y figure pas déjà. Montrer comment relier a et b au même objet c, sans créer deux copies de c.",
            _solution(Dossier)
            + "\na.relier(c) puis b.relier(c) utilisent exactement le même objet c.",
            [("0.25", "Le constructeur initialise une liste par instance et relier évite les doublons d'identifiant."),
             ("0.25", "Les deux appels partagent l'objet c sans le reconstruire.")],
            "design", "SD-POO",
        ),
        (
            "Partie B. Écrire explorer(depart, vus), où vus est une liste initialement vide, modifiée sur place. Ajouter l'identifiant du dossier avant de visiter récursivement ses enfants dans l'ordre de leur liste. Ne rien faire si cet identifiant est déjà présent. Justifier la place de l'ajout pour le cycle a, c, d, a.",
            _solution(explorer)
            + "\nL'ajout précède les appels : quand d revient vers a, a est déjà marqué, donc cette branche s'arrête.",
            [("0.25", "Le test d'appartenance porte sur l'identifiant."),
             ("0.25", "L'ajout précède la récursion."),
             ("0.25", "Chaque enfant est parcouru dans l'ordre imposé."),
             ("0.25", "L'arrêt sur le retour d vers a est justifié.")],
            "design", "LP-RECURSIVITE",
        ),
        (
            "Appliquer explorer à r sur le graphe initial. Donner la liste vus finale et indiquer pour chaque ajout quel appel l'a provoqué. Expliquer pourquoi c n'est pas ajouté une seconde fois depuis b.",
            "r, a, c, d, b. L'appel initial ajoute r ; r appelle a, a appelle c, c appelle d ; le retour d vers a est ignoré. Après ces retours, r appelle b ; son enfant c est déjà présent.",
            [("0.25", "L'ordre r, a, c, d, b est exact."),
             ("0.25", "Les retours vers a et c sont expliqués.")],
            "apply", "ALG-GRAPHES",
        ),
        (
            "Un programme remplace tous les tests et ajouts d'identifiant par des tests et ajouts de nom. Sur le graphe initial, quel objet ne sera alors pas visité ? Expliquer le défaut et proposer un test qui le détecte.",
            "b n'est pas visité : le nom Archives a déjà été ajouté pour a. Il faut conserver identifiant comme clé. Un test exige la présence de a ET b dans vus malgré leur nom identique.",
            [("0.25", "Le saut erroné de b est relié au nom partagé Archives."),
             ("0.25", "Un test distingue les identifiants a et b.")],
            "debug", "LP-DEBUG",
        ),
        (
            "On cherche le nombre minimal d'arcs depuis un départ vers un identifiant cible ; renvoyer None si aucun chemin n'existe. Donner les résultats pour (r,r), (r,d), (r,e) et (a,b), avec justification. Le rang de visite dans vus donne-t-il cette distance ?",
            "0, 3, None, None. r-a-c-d ou r-b-c-d utilise trois arcs ; e est isolé ; aucun arc ne rejoint b depuis a. Non : la position de b dans vus vaut 4, alors que r-b est un chemin d'un arc.",
            [("0.25", "Les quatre résultats sont corrects avec les chemins ou absences de chemin."),
             ("0.25", "b fournit un contre-exemple au rang de visite comme distance.")],
            "analyse", "ALG-GRAPHES",
        ),
        (
            "L'instruction from collections import deque est déjà exécutée : deque([x]) crée une file, append ajoute à droite et popleft retire à gauche. Compléter la fonction suivante. La file attente contient des couples (objet, distance). Marquer chaque identifiant dès son entrée dans la file. Expliquer pourquoi le premier retrait de la cible fournit une distance minimale.\n"
            + _solution(distance_minimale)
            .replace("attente.popleft()", "__A__")
            .replace("return dist", "return __B__")
            .replace("vus.add(cle)", "__C__")
            .replace("(lien, dist + 1)", "__D__"),
            _solution(distance_minimale)
            + "\nLa file retire les sommets par distance non décroissante. Chaque nouvel arc ajoute une unité ; marquer à l'entrée évite les réinsertions dues au cycle.",
            [("0.25", "A = attente.popleft() et B = dist."),
             ("0.25", "C = vus.add(cle) ; D = (lien, dist + 1)."),
             ("0.25", "L'ordre des distances dans la file justifie le premier retrait de la cible.")],
            "design", "ALG-GRAPHES",
        ),
        (
            "Repartir du graphe initial. Exécuter d.relier(e), puis calculer la distance de r à e. Exécuter ensuite r.relier(e), puis recalculer cette distance. Les enfants de a ont-ils changé ? Justifier les réponses en distinguant mutation d'un objet et copie.",
            "Après d.relier(e), la distance vaut 4 ; après r.relier(e), elle vaut 1. Les enfants de a restent [c]. Les liens partagent les objets existants ; modifier les enfants de d ou r ne modifie pas la liste enfants propre à a.",
            [("0.25", "Les distances successives 4 puis 1 sont correctes."),
             ("0.25", "La liste [c] de a reste inchangée, avec une justification par instance.")],
            "analyse", "SD-POO",
        ),
        (
            "Un autre constructeur place enfants = [] au niveau de la classe et n'affecte pas self.enfants. Expliquer le défaut en créant deux dossiers distincts puis en reliant un enfant à un seul d'entre eux. Donner la correction minimale.",
            "Les deux instances retrouvent la même liste de classe : ajouter un enfant par la première apparaît aussi depuis la seconde. Initialiser self.enfants = [] dans __init__ crée une liste distincte par instance.",
            [("0.25", "Le partage indésirable et la correction self.enfants = [] dans __init__ sont expliqués.")],
            "debug", "SD-POO",
        ),
    ]
    minutes = [3, 4, 4, 3, 4, 13, 6, 6, 5, 12, 6, 4]
    questions = []
    for index, (prompt, answer, credits, operation, code) in enumerate(items):
        questions.append(dict(
            id="1" + "abcdefghijkl"[index], prompt=prompt, answer=answer,
            points=str(sum(Decimal(value) for value, _ in credits)),
            marking=[dict(points=value, criterion=criterion) for value, criterion in credits],
            material_ids=["directory_graph", "directory_names"],
            curriculum_codes=[code], operation=operation,
            difficulty=4 if index in (5, 9, 10) else 3,
            estimated_minutes=minutes[index],
            verification=dict(kind="directory_case_contract", version=VERSION,
                              seed=seed, case_sha256=digest),
        ))
    raw = dict(
        id="1", title="Dossiers partagés et chemins dans un graphe",
        context="Un catalogue représente des dossiers par des objets Dossier. Les arcs sont des raccourcis orientés, pas des relations de contenance : cycles et liens partagés sont autorisés. Chaque identifiant désigne un seul objet ; les noms peuvent être identiques. Chaque arc compte pour une unité. Les listes enfants sont rangées par identifiant croissant dans le graphe initial ; relier ajoute ensuite en fin de liste. Les questions qui modifient le graphe le précisent ; les autres utilisent le graphe initial. La figure porte les identifiants et le tableau donne les noms. Rédiger le code et les justifications sur votre copie.",
        topics=["structures-donnees", "langages-programmation", "algorithmique"],
        minutes=70, target_points="6",
        materials=[
            dict(kind="weighted_graph", id="directory_graph", title="Raccourcis du catalogue",
                 nodes=[row[0] for row in case["nodes"]],
                 edges=[[a, b, 1] for a, b in case["links"]], directed=True),
            dict(kind="table", id="directory_names", title="Identifiants et noms des dossiers",
                 columns=["Identifiant", "Nom"], rows=case["nodes"]),
        ],
        questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw
