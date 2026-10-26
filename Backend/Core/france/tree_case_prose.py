"""Original E1 whole-case questions and indicative marking for draft V32."""

import json
from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.tree_case_families import (
    build_case,
    count_below,
    count_interval,
    decode_message,
    expression_value,
    transcode,
)

VERSION = "fr-nsi-tree-case-prose-v1"
MINUTES = (4, 5, 6, 6, 6, 7, 12, 8, 9, 7)


def _q(prompt, answer, criteria, operation="analyse", code="ALG-ARBRES"):
    return dict(
        prompt=prompt, answer=answer, criteria=criteria, operation=operation, code=code
    )


def _rank(case):
    p = case["public"]
    s0, s1, s2 = case["expected"]["states"]
    keys = s0["sorted_keys"]
    rows = {r[0]: r[1:] for r in p["rows"]}
    limit = p["limit"]
    target = limit - 3
    u, v = (item[1] for item in p["insertions"])
    low, high = s0["interval_bounds"]
    context = (
        "Un atelier classe les numéros entiers de ses colis dans un arbre binaire de recherche "
        "strict : toute clé à gauche est plus petite que la clé du nœud, toute clé à droite "
        "est plus grande. Chaque numéro apparaît une seule fois. Les identifiants r, a, b, etc. "
        "désignent les nœuds, pas les numéros de colis. Le dictionnaire nodes associe à chaque "
        "identifiant un triplet (clé, fils_gauche, fils_droit). None désigne un fils absent. "
        "La racine initiale est r. La hauteur est le nombre maximal d'arêtes de la racine à "
        "une feuille. Le responsable veut compter les colis situés avant une limite, puis "
        "réutiliser ce comptage pour préparer une tranche de numéros sans modifier l'index."
    )
    items = [
        _q(
            "À partir de l'index initial, donner les identifiants des feuilles et la hauteur. Justifier la hauteur par un chemin.",
            f"Feuilles : {s0['shape']['leaves']}. Hauteur 2, par exemple r-a-c.",
            (
                "Toutes les feuilles sont identifiées, sans confondre clés et identifiants.",
                "La hauteur 2 est justifiée avec la convention en arêtes.",
            ),
            "apply",
            "SD-ARBRE",
        ),
        _q(
            f"Rechercher le colis {target} en exploitant la propriété de l'ABR. Écrire les identifiants visités, les comparaisons successives et conclure.",
            f"r ({rows['r'][0]}) : aller à droite ; b ({rows['b'][0]}) : à gauche ; e ({rows['e'][0]}) : à droite, fils None. {target} est absent.",
            (
                "Le chemin r-b-e et les trois comparaisons sont corrects.",
                "L'absence est conclue au fils vide, pas à une simple différence de clés.",
            ),
        ),
        _q(
            "Donner les numéros dans l'ordre d'un parcours infixe. Expliquer pourquoi cet ordre permet de contrôler l'index, puis pourquoi ce contrôle ne suffit pas à garantir une faible hauteur.",
            f"{keys}. Le parcours gauche-nœud-droite est strictement croissant pour cet ABR. Une chaîne de clés croissantes reste un ABR mais peut avoir une hauteur n-1.",
            (
                "La liste infixe complète et strictement croissante est correcte.",
                "Un ABR dégénéré montre que l'ordre ne garantit pas l'équilibrage.",
            ),
        ),
        _q(
            f"On note rang_strict(L) le nombre de clés strictement inférieures à L. Calculer ce nombre pour L = {keys[0]}, {limit} et {keys[-1] + 1}, en précisant les clés comptées dans le cas intermédiaire.",
            f"Résultats : 0, {s0['answer']}, {len(keys)}. Au milieu : {s0['counted_keys']}. Une clé égale à L n'est pas comptée.",
            (
                "Les trois nombres respectent la borne strictement exclue.",
                "Les clés du cas intermédiaire sont toutes listées.",
            ),
            "apply",
        ),
        _q(
            f"Depuis S0, insérer le colis {u} (nœud u), puis le colis {v} (nœud v), sans rééquilibrage. Nommer le parent et le côté de chaque insertion, puis dessiner uniquement les deux branches modifiées. Ces états successifs sont S1 et S2.",
            f"u ({u}) devient fils droit de e ({rows['e'][0]}). v ({v}) devient fils gauche de d ({rows['d'][0]}). Les autres liens restent inchangés.",
            (
                "La première insertion est placée à droite de e avec sa clé.",
                "La seconde est placée à gauche de d et les branches existantes sont préservées.",
            ),
            "apply",
        ),
        _q(
            "On propose le programme incorrect suivant :\n"
            "```python\n"
            "def compte_errone(nodes, root, limit):\n"
            "    if root is None:\n"
            "        return 0\n"
            "    key, left, right = nodes[root]\n"
            "    n = compte_errone(nodes, left, limit)\n"
            "    if key < limit:\n"
            "        return 1 + n\n"
            "    return n\n"
            "```\n"
            f"Sur S0 et limit = {limit}, tracer les appels sur les nœuds non vides, donner le résultat et identifier toutes les clés admissibles oubliées.",
            f"Il renvoie 3 : les seuls nœuds visités sont r, a et c. Il oublie d ({rows['d'][0]}) dans le sous-arbre droit de a et e ({rows['e'][0]}) dans le sous-arbre droit de r. Ces deux clés respectent la limite. La bonne réponse est 5.",
            (
                "Le résultat erroné 3 est justifié par les appels sur r, a et c.",
                "Les deux nœuds d et e oubliés sont identifiés avec leurs clés admissibles.",
            ),
            "debug",
        ),
        _q(
            "Écrire entièrement count_below(nodes, root, limit). La fonction renvoie le nombre de clés strictement inférieures à limit, y compris si root vaut None. Exploiter l'ordre de l'ABR pour éviter un sous-arbre inutile ; ne modifier ni nodes ni ses triplets. Justifier la branche que l'on peut ignorer.",
            _solution(count_below)
            + "\nSi la clé est supérieure ou égale à limit, toutes les clés de droite sont également exclues. Sinon les deux sous-arbres peuvent contenir des clés admissibles.",
            (
                "Le cas None renvoie zéro avant tout accès au dictionnaire.",
                "La comparaison >= et l'exclusion du sous-arbre droit sont correctes et justifiées.",
                "L'autre branche additionne un et les deux appels récursifs.",
                "Le retour compte exactement les clés admises sans modifier l'index.",
            ),
            "design",
        ),
        _q(
            f"Utiliser count_below pour compléter les trois résultats S0, S1 et S2 avec limit = {limit}. Pour chaque insertion, expliquer la variation obtenue. La seule croissance de la taille d'un ABR suffirait-elle à garantir la même variation pour toute limite ?",
            f"S0 : {s0['answer']}, S1 : {s1['answer']}, S2 : {s2['answer']}. Les deux nouvelles clés sont inférieures à {limit}, donc chacune ajoute un. Une insertion supérieure ou égale à la limite n'ajouterait rien.",
            (
                "Les trois résultats 5, 6, 7 sont exacts.",
                "Chaque augmentation est reliée à la clé nouvellement insérée.",
                "La contre-condition clé >= limite explique pourquoi la taille seule ne suffit pas.",
            ),
        ),
        _q(
            f"En réutilisant count_below, écrire count_interval(nodes, root, low, high) qui compte les clés entières de l'intervalle fermé [low, high], avec low <= high. Ne parcourir aucune liste de clés supplémentaire. Justifier les bornes et donner le résultat sur S0 pour [{low}, {high}].",
            _solution(count_interval)
            + f"\nLe premier terme inclut high grâce à high+1 ; le second retire seulement les clés < low. Sur S0 : {s0['interval_count']}.",
            (
                "Deux appels au helper sont soustraits dans le bon ordre.",
                "high+1 et low sont justifiés par les bornes entières inclusives.",
                "Le résultat du cas S0 est exact, sans mutation ni liste de clés auxiliaire.",
            ),
            "design",
        ),
        _q(
            "Une collègue annonce que count_below est toujours logarithmique car l'index est un ABR. Réfuter cette affirmation en choisissant une limite qui impose de visiter tous les nœuds. Distinguer cette situation d'une recherche d'une seule clé dans un ABR équilibré.",
            "Si limit dépasse la plus grande clé, chaque nœud est visité : coût linéaire en n, même si l'arbre est équilibré. Une recherche d'une seule clé suit un seul chemin, de longueur logarithmique dans un ABR équilibré.",
            (
                "Une limite au-delà du maximum impose n visites et réfute le coût toujours logarithmique.",
                "Le comptage de plusieurs branches est distingué de la recherche sur un seul chemin.",
            ),
            "justify",
        ),
    ]
    return context, items


def _expression(case):
    s0 = case["expected"]["states"][0]
    context = (
        "Un logiciel d'atelier représente un coût par un arbre d'expression. Une feuille "
        "contient un entier, éventuellement négatif. Un nœud interne contient +, - ou * "
        "et possède exactement deux fils. L'opération combine la valeur du fils gauche "
        "puis celle du fils droit : leur ordre est important pour une soustraction. "
        "nodes associe chaque identifiant à (valeur, fils_gauche, fils_droit), avec None "
        "pour les fils absents. r est la racine ; la hauteur compte les arêtes. "
        "Le programme doit recalculer les coûts après une révision sans confondre une "
        "valeur enregistrée dans une feuille et la valeur calculée d'un sous-arbre."
    )
    return context, [
        _q(
            "Identifier les feuilles et les opérateurs internes. Donner la taille et la hauteur de cet arbre en justifiant les deux mesures.",
            "Feuilles a, b, c, d, e ; opérateurs r, l, s, m. Neuf nœuds, hauteur 3 (r-l-s-a).",
            (
                "Les cinq feuilles et quatre opérateurs sont correctement distingués.",
                "Taille 9 et hauteur 3 sont justifiées.",
            ),
            "apply",
            "SD-ARBRE",
        ),
        _q(
            "Traduire l'arbre initial en une expression arithmétique entièrement parenthésée. Expliquer ce qui serait perdu en remplaçant l'arbre par la seule liste de ses cinq entiers.",
            "((9 - 4) * 3) + (2 * 5). La liste des opérandes ne conserve ni les opérations, ni leur regroupement, ni leur ordre de combinaison.",
            (
                "L'expression parenthésée respecte exactement les fils gauches et droits.",
                "La perte de structure des opérations est expliquée.",
            ),
        ),
        _q(
            "Évaluer l'état initial S0. Présenter les valeurs calculées de s, l, m et r dans un ordre où chaque opérateur dispose déjà des valeurs de ses fils.",
            "s = 5 ; l = 15 ; m = 10 ; r = 25. Calculer les fils avant le parent est un parcours postfixe.",
            (
                "Les quatre valeurs intermédiaires sont exactes.",
                "L'ordre proposé respecte toutes les dépendances fils-parent.",
            ),
            "apply",
        ),
        _q(
            "Un évaluateur inverse les deux opérandes de chaque soustraction mais traite + et * correctement. Quel résultat donne-t-il sur S0 ? Pourquoi tester uniquement un arbre contenant des additions et multiplications ne révèle-t-il pas cette erreur ?",
            "s devient 4-9 = -5, l vaut -15 et r vaut -5. Addition et multiplication sont commutatives ; la soustraction ne l'est pas.",
            (
                "La propagation jusqu'au résultat erroné -5 est correcte.",
                "La commutativité explique pourquoi les tests proposés sont insuffisants.",
            ),
            "debug",
        ),
        _q(
            "On applique deux révisions successives : S1 remplace la feuille b par 7 ; S2 conserve cette révision et remplace l'opérateur m par -. Compléter un tableau des valeurs de s, l, m et r pour S0, S1 et S2. Ne pas repartir de S0 pour la seconde révision.",
            "S0 : 5, 15, 10, 25. S1 : 2, 6, 10, 16. S2 : 2, 6, -3, 3 (colonnes s, l, m, r).",
            (
                "La ligne S1 tient compte de b=7 et conserve m=10.",
                "La ligne S2 conserve S1 et propage m=-3 jusqu'à r=3.",
            ),
            "apply",
        ),
        _q(
            "Le logiciel garde en mémoire les valeurs calculées de tous les nœuds de S0. Après le changement de b en S1, quels résultats mémorisés doivent être invalidés ? Lesquels du sous-arbre de m restent utilisables ? Justifier à partir des dépendances, sans réévaluer tout l'arbre.",
            "b change ; les résultats de s, l et r dépendent de b et doivent être invalidés. m, d et e restent utilisables car leur sous-arbre ne contient pas b.",
            (
                "b et ses ancêtres s, l, r sont identifiés sans invalider une branche indépendante.",
                "La validité de m, d, e est justifiée par l'absence de dépendance envers b.",
            ),
        ),
        _q(
            "Construire expression_value(nodes, root), qui calcule récursivement la valeur de l'arbre non vide. Utiliser la représentation donnée, traiter les trois opérateurs et préserver l'ordre gauche-droite. Aucun eval ni résultat mémorisé ne doit être utilisé. Expliquer la terminaison sur un arbre fini.",
            _solution(expression_value)
            + "\nChaque appel descend vers un fils ; une feuille renvoie son entier. La hauteur diminue, donc les appels terminent.",
            (
                "Une feuille renvoie son entier sans appel sur None.",
                "Les deux sous-arbres sont évalués récursivement.",
                "Les trois opérations respectent l'ordre des opérandes, sans eval ni mutation.",
                "La terminaison est justifiée par la descente vers des feuilles d'un arbre fini.",
            ),
            "design",
        ),
        _q(
            "Tracer l'ordre de retour des appels de expression_value sur S0 : écrire les identifiants, puis la valeur renvoyée par chacun. Expliquer pourquoi la racine ne peut pas renvoyer sa réponse avant ses deux fils.",
            f"Ordre postfixe : {s0['postorder']}. Valeurs : {s0['values']}. Le calcul de r consomme les deux résultats l et m.",
            (
                "Les neuf identifiants sont donnés dans l'ordre des retours gauche-droite-parent.",
                "Toutes les valeurs renvoyées correspondent à leur nœud.",
                "La dépendance de la racine envers ses deux fils est explicitée.",
            ),
        ),
        _q(
            "Écrire variation(old_nodes, new_nodes, root) à l'aide de expression_value. Elle renvoie le nouveau coût moins l'ancien, sans modifier les dictionnaires. Donner les variations S0 vers S1 puis S0 vers S2 et expliquer pourquoi additionner directement les variations des seules feuilles ne suffit pas en général.",
            "```python\ndef variation(\n    old_nodes, new_nodes, root\n):\n    a = expression_value(old_nodes, root)\n    b = expression_value(new_nodes, root)\n    return b - a\n```\nVariations : -9 puis -22. La variation de b est +3, mais b intervient dans une soustraction puis une multiplication ; les opérateurs transforment son effet.",
            (
                "Les deux appels au helper sont soustraits dans l'ordre nouveau-ancien, sans mutation.",
                "Les variations -9 et -22 sont exactes.",
                "L'effet des opérateurs explique l'insuffisance de la somme des variations des feuilles.",
            ),
            "design",
        ),
        _q(
            "Pour vérifier un évaluateur, proposer un arbre réduit à une feuille négative et un arbre de soustraction dont l'ordre des fils compte. Donner pour chacun le résultat attendu et le défaut distinct qu'il peut révéler.",
            "Exemples : feuille -3 donne -3 (cas de base, entier signé) ; 2-5 donne -3 alors que 5-2 donne 3 (ordre des fils). Tout couple de tests remplissant ces objectifs convient.",
            (
                "Un test de feuille négative avec résultat exact contrôle le cas de base.",
                "Un test non symétrique avec résultat exact contrôle l'ordre de soustraction.",
            ),
            "design",
        ),
    ]


def _prefix(case):
    context = (
        "Un afficheur transmet les lettres A, B, C et D avec un code représenté par un "
        "arbre binaire. Chaque lettre occupe une feuille ; les nœuds internes ont deux "
        "fils et ne portent pas de lettre. Lire 0 fait descendre à gauche, lire 1 à droite. "
        "Dès qu'une feuille est atteinte, sa lettre est émise et le décodage repart de r "
        "pour le bit suivant. nodes associe un identifiant à (lettre, fils_gauche, fils_droit), "
        "où None désigne une absence. Le message vide est autorisé ; un caractère autre "
        "que 0 ou 1, ou une fin au milieu d'un code, constitue une erreur. Une mise à jour "
        "du code doit préserver les lettres transmises, pas nécessairement les bits."
    )
    return context, [
        _q(
            "Distinguer les nœuds internes des feuilles sur le tableau. Justifier pourquoi une lettre doit terminer un chemin et ne pas être placée sur un nœud interne dans ce protocole.",
            "Internes r, x, y ; feuilles a, b, c, d. Une lettre sur un nœud interne serait un préfixe d'un code plus long : on ne saurait pas s'il faut émettre ou poursuivre.",
            (
                "Les nœuds internes et les quatre feuilles sont identifiés.",
                "L'ambiguïté émission-poursuite justifie la position des lettres.",
            ),
            "justify",
            "SD-ARBRE",
        ),
        _q(
            "Déduire le code binaire de chacune des quatre lettres en indiquant son chemin depuis r. Calculer la longueur en bits du message ABCD, sans supposer que toutes les lettres ont la même longueur.",
            "A : 0 (r-a), B : 10 (r-x-b), C : 110 (r-x-y-c), D : 111 (r-x-y-d). ABCD occupe 1+2+3+3 = 9 bits.",
            (
                "Les quatre codes et chemins sont exacts.",
                "La longueur totale 9 est calculée avec les longueurs variables.",
            ),
            "apply",
        ),
        _q(
            "Décoder le flux 010110111 en séparant les mots de code. Pour chaque séparation, indiquer la lettre émise et le nœud où commence la lecture du mot suivant.",
            "0 | 10 | 110 | 111 donne ABCD. Chaque mot suivant repart de r, même si la feuille précédente n'était pas au même niveau.",
            (
                "Les quatre séparations et lettres sont exactes.",
                "Le retour à r est indiqué à chaque frontière de mot.",
            ),
            "apply",
        ),
        _q(
            "Comparer les flux 0, 01 et 010. Dire lesquels sont valides et ce qu'ils produisent. Pour le flux invalide, nommer le nœud atteint à la fin et expliquer pourquoi la lettre déjà décodée ne suffit pas à accepter tout le message.",
            "0 donne A ; 01 est invalide : après A, le dernier 1 mène au nœud interne x ; 010 donne AB. Le préfixe A valide ne rend pas complet le mot final.",
            (
                "Les trois verdicts et les messages valides A et AB sont corrects.",
                "La fin sur x explique l'erreur de troncature malgré un préfixe valide.",
            ),
        ),
        _q(
            "Un programme émet une lettre lorsqu'il atteint une feuille, mais oublie de revenir à la racine. Tracer son comportement sur 00 et localiser la première opération impossible. Proposer la correction de l'état courant.",
            "Le premier 0 atteint a et émet A. Le second tente de descendre depuis a, dont les fils sont None. Après toute émission, current doit redevenir root avant de lire le bit suivant.",
            (
                "L'échec au second bit est relié à la descente depuis une feuille.",
                "La remise à root après chaque lettre corrige précisément l'état.",
            ),
            "debug",
        ),
        _q(
            "S0 utilise le code initial. En S1, on échange uniquement les lettres des feuilles b et d ; les liens restent inchangés. Donner les nouveaux codes de B et D, puis décoder l'ancien flux 010110111 avec S1. Pourquoi conserver les mêmes bits ne conserve-t-il pas le message ?",
            "B devient 111 et D devient 10. L'ancien flux donne ADCB. Les chemins n'ont pas changé, mais leur association aux lettres a changé.",
            (
                "Les nouveaux codes B=111, D=10 et le message ADCB sont exacts.",
                "Le changement d'association chemin-lettre explique l'altération du message.",
            ),
        ),
        _q(
            "Écrire decode_message(nodes, root, bits). Renvoyer le texte décodé et ne modifier aucun nœud. Lever ValueError pour un caractère non binaire ou un mot final incomplet ; le flux vide doit renvoyer une chaîne vide. Justifier le test à effectuer après la boucle.",
            _solution(decode_message)
            + "\nAprès une lettre complète, current vaut root. Une autre valeur à la fin signifie qu'un mot est commencé mais non terminé.",
            (
                "Les bits sont contrôlés et les descentes 0-gauche/1-droite sont correctes.",
                "Chaque feuille produit une lettre puis une remise à la racine.",
                "Le test final détecte un mot incomplet et sa nécessité est justifiée.",
                "Le flux vide est accepté ; les erreurs lèvent ValueError et l'arbre n'est pas modifié.",
            ),
            "design",
        ),
        _q(
            "Après l'échange de S1, on veut transmettre à nouveau ABCD : cet état est S2. Construire son nouveau flux et tracer les quatre frontières de code. Comparer, dans un tableau S0/S1/S2, le flux lu et le texte reçu ; distinguer modification du code et modification du flux.",
            "S0 : 010110111 donne ABCD. S1 : mêmes bits donnent ADCB. S2 : 0 | 111 | 110 | 10, soit 011111010, donne ABCD avec le code modifié. S1 change le code ; S2 adapte les bits.",
            (
                "Les trois états associent correctement code, bits et texte.",
                "Le flux réparé et ses quatre frontières sont exacts.",
                "Les effets distincts du changement de code puis du recodage sont expliqués.",
            ),
        ),
        _q(
            "Écrire transcode(nodes, root, bits, new_codes) en réutilisant decode_message. new_codes associe chaque lettre de l'ancien alphabet à son nouveau mot de code valide. La fonction renvoie le nouveau flux conservant exactement les lettres du message. Donner son résultat pour le passage de S0 à S2 et expliquer pourquoi remplacer aveuglément 10 par 111 dans les bits ne convient pas.",
            _solution(transcode)
            + "\nRésultat : 011111010. La suite 10 peut apparaître à l'intérieur du code 110 de C ; un remplacement textuel modifierait une lettre qui ne devait pas changer. Il faut d'abord retrouver les frontières des lettres.",
            (
                "Le décodage ancien est suivi de la concaténation des nouveaux codes dans l'ordre des lettres.",
                "Le résultat 011111010 est exact et les paramètres restent inchangés.",
                "L'occurrence de 10 dans 110 fournit un contre-exemple au remplacement aveugle.",
            ),
            "design",
        ),
        _q(
            "Proposer deux tests supplémentaires du décodeur : l'un sur une succession de lettres à code court, l'autre sur un caractère interdit après un préfixe valide. Donner le résultat attendu et le défaut visé par chacun.",
            "000 doit donner AAA et contrôle les remises à la racine répétées. 010x doit lever ValueError même si AB a déjà été décodé ; il contrôle la validation de tout le flux.",
            (
                "Une répétition de codes courts avec résultat exact teste les remises à la racine.",
                "Un caractère interdit après un préfixe valide impose une erreur, pas un texte partiel accepté.",
            ),
            "design",
        ),
    ]


def render_case(seed, *, total="6"):
    if type(total) is not str or total not in {"5.5", "6", "6.5"}:
        raise ValueError("Unsupported whole-tree allocation")
    case = build_case(seed)
    context, items = {"rank": _rank, "expression": _expression, "prefix": _prefix}[
        case["family"]
    ](case)
    material = dict(
        kind="table",
        id="tree_nodes",
        title="Représentation initiale de l'arbre",
        columns=["Identifiant", "Valeur", "Fils gauche", "Fils droit"],
        rows=[[str(v) for v in row] for row in case["public"]["rows"]],
    )
    state_index = 4 if case["family"] == "expression" else 7
    columns = {
        "rank": ["État", "Nombre de clés", "Justification"],
        "expression": ["État", "s", "l", "m", "r"],
        "prefix": ["État", "Flux lu", "Texte reçu"],
    }[case["family"]]
    state_material = dict(
        kind="table",
        id="tree_states",
        title="Tableau de travail pour la question 1" + "abcdefghij"[state_index],
        columns=columns,
        rows=[[state, *["..."] * (len(columns) - 1)] for state in ("S0", "S1", "S2")],
    )
    questions = []
    for index, item in enumerate(items):
        criteria = item["criteria"]
        if total == "5.5" and index in (0, 1):
            criteria = (" ".join(criteria),)
        marking = [
            dict(
                points="0.5"
                if total == "6.5" and index in (6, 8) and i == 0
                else "0.25",
                criterion=c,
            )
            for i, c in enumerate(criteria)
        ]
        questions.append(
            dict(
                id="1" + "abcdefghij"[index],
                prompt=item["prompt"],
                answer=item["answer"],
                points=str(
                    sum((Decimal(c["points"]) for c in marking), Decimal(0)).normalize()
                ),
                marking=marking,
                material_ids=["tree_nodes"]
                + (["tree_states"] if index == state_index else []),
                curriculum_codes=[item["code"]],
                operation=item["operation"],
                difficulty=4 if index in (6, 8) else 2 if index < 3 else 3,
                estimated_minutes=MINUTES[index],
                verification=dict(
                    kind="tree_case_contract",
                    version=VERSION,
                    seed=seed,
                    case_sha256=case["sha256"],
                    task_id="1" + "abcdefghij"[index],
                    expected=case["expected"],
                ),
            )
        )
    raw = dict(
        id="1",
        title=case["public"]["title"],
        context=context,
        topics=["structures-donnees", "algorithmique"],
        minutes=70,
        target_points=total,
        materials=[material, state_material],
        questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw


def case_task(seed, total="6"):
    exercise = render_case(seed, total=total)
    return dict(
        topics=exercise["topics"],
        query="arbres binaires récursivité parcours tests " + exercise["title"],
        minutes=exercise["minutes"],
        technical_points=total,
        required_material_kind="table",
        required_curriculum_codes=sorted(
            {c for q in exercise["questions"] for c in q["curriculum_codes"]}
        ),
        archetype_id="graph-and-tree",
        scenario_brief=exercise["context"],
        part_briefs=[
            "A : interpréter et diagnostiquer un arbre.",
            "B : construire et composer des fonctions, puis justifier leurs résultats.",
        ],
        question_blueprint=[
            dict(
                id=q["id"],
                points=q["points"],
                estimated_minutes=q["estimated_minutes"],
                operation=q["operation"],
                difficulty=q["difficulty"],
                required_curriculum_code=q["curriculum_codes"][0],
                part_id="A" if i < 6 else "B",
            )
            for i, q in enumerate(exercise["questions"])
        ],
    )


def verify_candidate(candidate, seed, *, total="6"):
    try:
        return json.dumps(candidate, ensure_ascii=False, sort_keys=True) == json.dumps(
            render_case(seed, total=total), ensure_ascii=False, sort_keys=True
        )
    except (ValueError, TypeError, KeyError):
        return False
