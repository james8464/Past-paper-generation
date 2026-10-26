"""Experimental compilation/stack exercise; not a public generation route."""

from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.expression_stack import compile_tree, execute
from Backend.Core.france.expression_synthesis import build_case
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-postfix-exercise-v1"


def compiler(nodes, racine):
    valeur, gauche, droite = nodes[racine]
    if gauche is None:
        return [valeur]
    debut = compiler(nodes, gauche)
    suite = compiler(nodes, droite)
    return debut + suite + [valeur]


def calculer(instructions):
    pile = []
    for instruction in instructions:
        if type(instruction) is int:
            pile.append(instruction)
        else:
            droite = pile.pop()
            gauche = pile.pop()
            if instruction == "+":
                pile.append(gauche + droite)
            elif instruction == "-":
                pile.append(gauche - droite)
            else:
                pile.append(gauche * droite)
    return pile[0]


def valide(instructions):
    profondeur = 0
    operateurs = ("+", "-", "*")
    for mot in instructions:
        if type(mot) is int:
            profondeur += 1
        elif type(mot) is str and mot in operateurs:
            if profondeur < 2:
                return False
            profondeur -= 1
        else:
            return False
    return profondeur == 1


def render_case(seed):
    case = build_case(seed)
    rows = case["public"]["rows"]
    program = compile_tree(rows, "n0")
    result = execute(program)
    count = len(program)
    leaves = sum(type(token) is int for token in program)
    trace = "\n".join(
        f"Après {i + 1} ({token}) : {stack}"
        for i, (token, stack) in enumerate(zip(program, result["trace"], strict=True))
    )
    evaluation_scaffold = (
        _solution(calculer)
        .replace("pile.append(instruction)", "pile.append(__A__)")
        .replace("droite = pile.pop()", "droite = __B__")
        .replace("pile.append(gauche - droite)", "pile.append(__C__)")
        .replace("return pile[0]", "return __D__")
    )
    items = [
        (
            "Exécuter la séquence [2, 5, '-', -3, '*']. Représenter la pile après chaque instruction ; distinguer l'ordre de dépilement de l'ordre de la soustraction.",
            "[2], [2, 5], [-3], [-3, -3], [9]. On dépile 5 avant 2, mais on calcule 2 - 5. Le dernier résultat est 9.",
            [
                "Les cinq états de pile sont exacts.",
                "Le rôle du premier dépilement comme opérande droit est expliqué.",
            ],
            "apply",
            "SD-LINEAIRE",
        ),
        (
            "Produire les instructions de la machine pour l'arbre donné. Parcourir d'abord le sous-arbre gauche, puis le droit, puis émettre l'opérateur. Pourquoi un opérateur émis avant ses fils ne convient-il pas ?",
            f"{program}. Les résultats des deux fils doivent déjà se trouver sur la pile quand l'opérateur les consomme.",
            [
                "La séquence complète respecte le parcours demandé.",
                "La disponibilité des deux opérandes justifie la position de l'opérateur.",
            ],
            "analyse",
            "ALG-ARBRES",
        ),
        (
            "Vérifier la séquence obtenue en dressant un tableau : rang, instruction, pile après exécution. Déduire le résultat et la capacité minimale de pile nécessaire pour cette exécution.",
            trace
            + f"\nRésultat {result['answer']} ; capacité minimale {result['peak_depth']} cellules, atteinte pendant la trace.",
            [
                "La trace conserve tous les éléments de la pile dans le bon ordre.",
                "Le résultat final et le maximum de profondeur sont correctement déduits.",
            ],
            "apply",
            "SD-LINEAIRE",
        ),
        (
            "Un fichier reçu contient [4, '+', 7, '*']. Localiser la première instruction impossible. Expliquer pourquoi poursuivre avec 7 ne répare pas cette erreur et pourquoi le fichier [4, 7] est également invalide.",
            "L'instruction 2, '+', ne dispose que de [4] : deux opérandes sont nécessaires. Une valeur reçue plus tard ne peut corriger une instruction déjà inexécutable. [4, 7] laisse deux résultats au lieu d'un seul.",
            [
                "La première erreur est localisée avec l'état de pile qui la provoque.",
                "L'erreur de préfixe et l'excès de valeurs finales sont distingués.",
            ],
            "debug",
            "SD-LINEAIRE",
        ),
        (
            "Sans calculer les valeurs, donner la variation de profondeur produite par un entier et par un opérateur. Énoncer les deux conditions permettant de reconnaître une séquence exécutable qui produit exactement un résultat.",
            "Un entier ajoute 1 ; un opérateur retire deux éléments puis en ajoute un, soit -1. Avant chaque opérateur, la profondeur doit être au moins 2. À la fin elle doit être exactement 1. Les instructions doivent appartenir à l'alphabet autorisé.",
            [
                "Les variations +1 et -1 sont justifiées.",
                "La condition avant chaque opérateur et la condition finale sont toutes deux présentes.",
            ],
            "analyse",
            "SD-LINEAIRE",
        ),
        (
            "Un développeur remplace le traitement de '-' par a = pile.pop(), b = pile.pop(), puis pile.append(a - b). Donner un contre-exemple minimal, corriger l'expression et expliquer pourquoi des essais limités à '+' et '*' masqueraient le défaut.",
            "[2, 5, '-'] produit 3 au lieu de -3. Il faut empiler b - a : a est l'opérande droit. Addition et multiplication sont commutatives ; leurs résultats ne révèlent pas l'inversion.",
            [
                "Un contre-exemple distingue les deux résultats et la correction est b - a.",
                "La commutativité explique pourquoi les deux autres opérateurs masquent l'erreur.",
            ],
            "debug",
            "SD-LINEAIRE",
        ),
        (
            "Écrire compiler(nodes, racine), fonction récursive renvoyant une nouvelle liste d'instructions pour un arbre conforme au tableau. Ne pas modifier nodes. Justifier la terminaison et l'ordre des instructions renvoyées.",
            _solution(compiler)
            + "\nUne feuille fournit un entier. Pour un nœud interne, les deux listes de sous-arbres précèdent son opérateur. Chaque appel porte sur un sous-arbre strict d'un arbre fini : la récursion termine.",
            [
                "Le cas feuille renvoie une liste contenant son entier.",
                "Les deux sous-arbres sont compilés récursivement sans mutation.",
                "La concaténation place gauche, droite puis opérateur.",
                "La descente dans les sous-arbres finis justifie la terminaison.",
            ],
            "design",
            "ALG-ARBRES",
        ),
        (
            "Compléter les quatre expressions __A__, __B__, __C__ et __D__ dans calculer pour une séquence valide, sans modifier le reste du programme. Expliquer pourquoi le premier élément dépilé est l'opérande droit.\n"
            + evaluation_scaffold,
            _solution(calculer)
            + "\nA : instruction ; B : pile.pop() ; C : gauche - droite ; D : pile[0]. Le sous-arbre droit est compilé après le gauche : son résultat est donc au sommet lorsque l'opérateur est exécuté.",
            [
                "A et B empilent l'entier puis dépilent l'opérande droit.",
                "C conserve gauche moins droite et D renvoie le résultat unique.",
                "L'ordre de compilation explique pourquoi le résultat droit est dépilé en premier.",
            ],
            "design",
            "SD-LINEAIRE",
        ),
        (
            "Avant calculer, on souhaite rejeter les fichiers invalides sans effectuer aucune opération arithmétique sur leurs valeurs. Écrire valide(instructions), renvoyant un booléen, avec un compteur de profondeur et sans pile. Refuser les instructions inconnues et la séquence vide.",
            _solution(valide),
            [
                "Le compteur suit les variations de profondeur sans calcul des valeurs.",
                "Un opérateur sans deux valeurs disponibles ou une instruction inconnue provoque un refus.",
                "Le retour final exige exactement une valeur ; le fichier vide est refusé.",
            ],
            "design",
            "SD-LINEAIRE",
        ),
        (
            "Relier le nombre d'entiers et le nombre d'opérateurs d'une séquence valide. Vérifier cette relation sur votre compilation. En supposant append et pop de coût constant, donner le coût en temps de calculer pour m instructions et une borne de son espace supplémentaire.",
            f"Il faut un entier de plus que d'opérateurs : la profondeur finale vaut entiers moins opérateurs = 1. Ici {leaves} entiers et {count - leaves} opérateurs. Chaque instruction est traitée une fois : temps O(m). La pile peut contenir O(m) valeurs ; pour cette séquence le maximum observé est {result['peak_depth']}.",
            [
                "La relation entiers = opérateurs + 1 est justifiée et vérifiée sur le cas.",
                "Temps linéaire et espace au plus linéaire sont justifiés par les instructions et la pile.",
            ],
            "analyse",
            "SD-LINEAIRE",
        ),
    ]
    minutes = (4, 5, 7, 5, 6, 6, 12, 10, 10, 5)
    questions = []
    for i, (prompt, answer, criteria, operation, code) in enumerate(items):
        questions.append(
            dict(
                id="1" + "abcdefghij"[i],
                prompt=prompt,
                answer=answer,
                points=str(Decimal(len(criteria)) / 4),
                marking=[dict(points="0.25", criterion=c) for c in criteria],
                material_ids=["tree_nodes"] if i in (1, 2, 6, 9) else [],
                curriculum_codes=[code],
                operation=operation,
                difficulty=4 if i in (6, 7, 8) else 3,
                estimated_minutes=minutes[i],
                verification=dict(
                    kind="postfix_synthesis_contract",
                    version=VERSION,
                    seed=seed,
                    case_sha256=case["sha256"],
                ),
            )
        )
    raw = dict(
        id="1",
        title="Compiler un calcul pour une machine à pile",
        context="Une calculatrice reçoit des instructions en notation postfixée : un entier est empilé ; un opérateur retire d'abord l'opérande droit, puis le gauche, et empile le résultat gauche opérateur droit. La pile est initialement vide ; son sommet est à droite dans nos représentations. Seuls les entiers Python et les chaînes '+', '-' et '*' sont autorisés. Un programme valide ne manque jamais d'opérandes et laisse exactement un résultat. Le tableau décrit un arbre source : nodes associe un identifiant à (valeur, gauche, droite), None désigne un fils absent et n0 est la racine. Les calculs sont sur des entiers de taille supposée bornée. Rédiger sur votre copie.",
        topics=["structures-donnees", "algorithmique"],
        minutes=70,
        target_points="6",
        materials=[
            dict(
                kind="table",
                id="tree_nodes",
                title="Arbre source de la compilation",
                columns=["Identifiant", "Valeur", "Gauche", "Droite"],
                rows=[[str(v) for v in row] for row in rows],
            )
        ],
        questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw
