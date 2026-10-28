# Experimental complete exercise over synthesized expression cases.
#
# Not a public generation route or originality qualification. Exact replay binds
# all prose and marking to checked case data; pedagogical timing is indicative.

import json
from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.expression_synthesis import build_case
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.tree_case_families import expression_value

VERSION = "fr-nsi-expression-exercise-v2"
MINUTES = (4, 5, 6, 6, 6, 7, 12, 8, 9, 7)


def combine_erronee(value, a, b):
    if value == "+":
        return a + b
    if value == "-":
        return b - a
    return a * b


def variation(old_nodes, new_nodes, root):
    old = expression_value(old_nodes, root)
    new = expression_value(new_nodes, root)
    return new - old


def _values(values, order):
    return "; ".join(f"{node} = {values[node]}" for node in order)


def render_case(seed, *, total="6"):
    if type(total) is not str or total not in {"5.5", "6", "6.5"}:
        raise ValueError("Unsupported synthesized expression allocation")
    case = build_case(seed)
    public, expected = case["public"], case["expected"]
    states = expected["states"]
    initial = states[0]
    rows = {row[0]: row[1:] for row in public["rows"]}
    internal = [node for node, row in rows.items() if row[1] is not None]
    leaf, operator = public["changes"]
    invalidated = expected["invalidated"]
    unaffected = sorted(set(rows) - set(invalidated))
    faulty = expected["reversed_subtraction"]

    def expression(node):
        value, left, right = rows[node]
        return (
            str(value)
            if left is None
            else f"({expression(left)} {value} {expression(right)})"
        )

    # A monospaced outline gives an explicit solution to the drawing task.
    # G/D labels preserve child orientation even for asymmetric tree shapes.
    outline = [f"n0 ({rows['n0'][0]})"]

    def branches(node, prefix=""):
        _, left, right = rows[node]
        if left is None:
            return
        for direction, child, continuation in (
            ("G", left, "|   "),
            ("D", right, "    "),
        ):
            outline.append(f"{prefix}+-- {direction}: {child} ({rows[child][0]})")
            branches(child, prefix + continuation)

    branches("n0")

    items = [
        (
            "Dessiner l'arbre initial en distinguant les fils gauches et droits. Donner sa taille et sa hauteur, comptée en arêtes, puis identifier ses feuilles.",
            "Arbre initial : G désigne le fils gauche, D le fils droit ; la valeur du nœud est entre parenthèses.\n```\n"
            + "\n".join(outline)
            + f"\n```\nTaille {initial['shape']['size']}, hauteur {initial['shape']['height']}. Feuilles : {', '.join(initial['shape']['leaves'])}.",
            [
                "Le dessin respecte tous les liens et leur orientation gauche/droite.",
                "Taille, hauteur en arêtes et feuilles sont correctes.",
            ],
            "apply",
        ),
        (
            "Traduire cet arbre en expression arithmétique entièrement parenthésée. Expliquer pourquoi la liste des valeurs des feuilles ne suffit pas à retrouver le calcul.",
            expression("n0")
            + ". Les opérateurs, les regroupements et l'ordre des opérandes sont nécessaires.",
            [
                "Les parenthèses reproduisent chaque sous-arbre et l'ordre des fils.",
                "La perte des opérations et de leur organisation est expliquée.",
            ],
            "analyse",
        ),
        (
            "Calculer les valeurs des nœuds internes de S0. Présenter les calculs dans un ordre où les deux opérandes sont connus avant chaque opération.",
            _values(
                initial["values"], [n for n in initial["postorder"] if n in internal]
            ),
            [
                "Toutes les valeurs des nœuds internes sont correctes.",
                "L'ordre des calculs respecte les dépendances entre fils et parent.",
            ],
            "apply",
        ),
        (
            "Un programmeur utilise la fonction suivante à chaque nœud interne : value est son opérateur, a le résultat du fils gauche et b celui du fils droit. Les feuilles conservent leur entier ; les nœuds sont traités après leurs deux fils.\n"
            + _solution(combine_erronee)
            + "\nTracer les calculs ainsi obtenus sur S0 et donner le résultat de la racine. Identifier les nœuds dont la valeur diffère du calcul correct et expliquer le défaut.",
            _values(faulty["values"], faulty["postorder"])
            + f". Résultat erroné : {faulty['answer']}. Nœuds différents : {', '.join(faulty['divergent_nodes'])}. La soustraction calcule droite moins gauche ; contrairement à + et *, elle n'est pas commutative.",
            [
                "La trace et le résultat erroné correspondent au programme fourni.",
                "Les valeurs affectées sont identifiées et l'inversion des opérandes est expliquée.",
            ],
            "debug",
        ),
        (
            f"Deux révisions se succèdent : S1 remplace la valeur de la feuille {leaf['node']} par {leaf['value']} ; S2 conserve S1 et remplace l'opérateur de {operator['node']} par {operator['value']}. Compléter le tableau pour tous les nœuds internes, sans revenir à S0 lors de la seconde révision.",
            "\n".join(
                state["id"] + " : " + _values(state["values"], internal)
                for state in states
            ),
            [
                "S1 propage correctement la nouvelle valeur de la feuille.",
                "S2 conserve la première révision et applique le nouvel opérateur.",
            ],
            "apply",
        ),
        (
            f"Toutes les valeurs de S0 sont mémorisées. Pour passer à S1, quels résultats faut-il invalider après la modification de {leaf['node']} ? Quels résultats peuvent être conservés ? Justifier sans refaire les calculs.",
            f"Invalider : {', '.join(invalidated)}. Conserver : {', '.join(unaffected)}. Seuls la feuille modifiée et ses ancêtres dépendent de cette modification.",
            [
                "La feuille modifiée et tous ses ancêtres sont invalidés.",
                "Les autres nœuds sont conservés avec une justification par les dépendances.",
            ],
            "analyse",
        ),
        (
            "Écrire une fonction récursive correcte expression_value(nodes, root) pour tout arbre non vide conforme à cette représentation. Traiter les trois opérateurs sans eval, sans résultat mémorisé et sans modifier nodes. Justifier la terminaison.",
            _solution(expression_value)
            + "\nChaque appel descend vers un fils d'un arbre fini ; les feuilles renvoient leur entier. La hauteur restante diminue strictement.",
            [
                "Une feuille renvoie son entier sans appel sur None.",
                "Les deux sous-arbres sont évalués récursivement.",
                "Les trois opérations conservent l'ordre des fils, sans eval ni mutation.",
                "La terminaison est justifiée sur un arbre fini.",
            ],
            "design",
        ),
        (
            "Tracer les retours des appels de votre fonction sur S0 : donner les identifiants dans l'ordre, puis la valeur retournée par chacun. Expliquer pourquoi la racine doit attendre les résultats de ses deux fils.",
            _values(initial["values"], initial["postorder"])
            + ". Cette trace correspond à la solution proposée, qui évalue le fils gauche en premier. Accepter un autre ordre cohérent avec la fonction du candidat, si chaque parent attend ses deux fils et si l'ordre des opérandes est conservé. Chaque parent combine les deux résultats de ses enfants ; n0 ne peut donc retourner sa valeur avant eux.",
            [
                "L'ordre des retours correspond à la fonction proposée et place chaque parent après ses deux fils.",
                "Chaque valeur retournée correspond au nœud concerné.",
                "La dépendance de la racine envers ses deux fils est expliquée.",
            ],
            "analyse",
        ),
        (
            "À l'aide de expression_value, écrire variation(old_nodes, new_nodes, root), qui renvoie le nouveau résultat moins l'ancien sans modifier les arbres. Calculer les variations de S0 vers S1 puis de S0 vers S2. Pourquoi additionner seulement les changements des feuilles ne suffit-il pas en général ?",
            _solution(variation)
            + f"\nVariations : {expected['variations'][0]} puis {expected['variations'][1]}. Les opérateurs transforment l'effet des changements ; en S2 un opérateur change aussi, ce qu'une somme de changements de feuilles ne représente pas.",
            [
                "Les deux évaluations sont composées dans l'ordre nouveau moins ancien, sans mutation.",
                "Les deux variations numériques sont exactes.",
                "L'effet des opérateurs et du changement d'opérateur est expliqué.",
            ],
            "design",
        ),
        (
            "Proposer deux petits arbres de test indépendants : une feuille négative, puis une soustraction où échanger les fils change le résultat. Donner les résultats attendus et le défaut que chaque test permet de détecter.",
            "Une feuille -3 doit donner -3 : test du cas de base et du signe. Un arbre 2-5 doit donner -3, alors que 5-2 donne 3 : test de l'ordre des fils. Tout exemple correct répondant à ces conditions convient.",
            [
                "Le test de feuille négative comprend son résultat et contrôle le cas de base.",
                "Le test non symétrique comprend son résultat et distingue l'ordre des fils.",
            ],
            "design",
        ),
    ]
    questions = []
    for index, (prompt, answer, criteria, operation) in enumerate(items):
        if total == "5.5" and index in (0, 1):
            criteria = [" ".join(criteria)]
        marking = [
            dict(
                points="0.5"
                if total == "6.5" and index in (6, 8) and i == 0
                else "0.25",
                criterion=criterion,
            )
            for i, criterion in enumerate(criteria)
        ]
        questions.append(
            dict(
                id="1" + "abcdefghij"[index],
                prompt=prompt,
                answer=answer,
                points=str(
                    sum(Decimal(item["points"]) for item in marking).normalize()
                ),
                marking=marking,
                material_ids=["tree_nodes"] + (["tree_states"] if index == 4 else []),
                curriculum_codes=["SD-ARBRE" if index == 0 else "ALG-ARBRES"],
                operation=operation,
                difficulty=4 if index in (6, 8) else 3,
                estimated_minutes=MINUTES[index],
                verification=dict(
                    kind="expression_synthesis_contract",
                    version=VERSION,
                    seed=seed,
                    case_sha256=case["sha256"],
                ),
            )
        )
    raw = dict(
        id="1",
        title="Réviser un arbre de calcul sans perdre ses dépendances",
        context="Un atelier représente un calcul par un arbre binaire. Chaque feuille contient un entier ; chaque nœud interne contient +, - ou * et possède exactement deux fils. nodes associe chaque identifiant à (valeur, fils_gauche, fils_droit). None indique l'absence d'un fils. La racine est n0. Une opération utilise d'abord la valeur du fils gauche, puis celle du fils droit. Les révisions changent des valeurs ou opérateurs, jamais les liens. Les réponses sont à rédiger sur votre copie.",
        topics=["structures-donnees", "algorithmique"],
        minutes=70,
        target_points=total,
        materials=[
            dict(
                kind="table",
                id="tree_nodes",
                title="Arbre initial S0",
                columns=["Identifiant", "Valeur", "Fils gauche", "Fils droit"],
                rows=[[str(v) for v in row] for row in public["rows"]],
            ),
            dict(
                kind="table",
                id="tree_states",
                title="Tableau de travail pour la question 1e",
                columns=["État", *internal],
                rows=[
                    [state, *["..."] * len(internal)] for state in ("S0", "S1", "S2")
                ],
            ),
        ],
        questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw


def verify_candidate(candidate, seed, *, total="6"):
    try:
        return json.dumps(candidate, sort_keys=True) == json.dumps(
            render_case(seed, total=total), sort_keys=True
        )
    except (TypeError, ValueError):
        return False
