"""Original linked E3 reasoning sequences and indicative marking, draft V32."""

import json
from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.nsi import CURRICULUM_OBJECTIVES, NSIExercise
from Backend.Core.france.system_case_families import build_case

VERSION = "fr-nsi-system-case-prose-v2"
MINUTES = (4, 5, 6, 8, 7, 6, 7, 6, 5, 5, 5, 6)


# Short lines are intentional: these functions are printed in corrections.
# fmt: off
def tour(voisins, ancien, destination):
    nouveau = {}
    for sommet in ancien:
        meilleur = None
        for voisin, cout in voisins[sommet]:
            if ancien[voisin] is not None:
                valeur = cout + ancien[voisin]
                if (meilleur is None
                    or valeur < meilleur):
                    meilleur = valeur
        if sommet == destination:
            meilleur = 0
        nouveau[sommet] = meilleur
    return nouveau


def cycle_depuis(
    depart, proprietaires, attentes
):
    chemin = []
    courant = depart
    while courant in attentes:
        if courant in chemin:
            position = chemin.index(courant)
            return chemin[position:]
        chemin.append(courant)
        ressource = attentes[courant]
        if ressource not in proprietaires:
            return []
        courant = proprietaires[ressource]
    return []


def reassembler(evenements):
    tampon = {}
    suivant = 1
    sortie = []
    for _date, numero, texte in evenements:
        if numero >= suivant:
            tampon[numero] = texte
        while suivant in tampon:
            sortie.append(tampon.pop(suivant))
            suivant += 1
    return sortie
# fmt: on


def _q(prompt, answer, criteria, operation="analyse", code="ASR-PROCESSUS"):
    return dict(
        prompt=prompt, answer=answer, criteria=criteria, operation=operation, code=code
    )


def _table(identifier, title, columns, rows):
    return dict(
        kind="table",
        id=identifier,
        title=title,
        columns=columns,
        rows=[[str(value) for value in row] for row in rows],
    )


def _routing(case):
    public, expected = case["public"], case["expected"]
    context = (
        "Quatre routeurs A, B, C et D transmettent des mesures vers D. Les liaisons du tableau "
        "sont bidirectionnelles ; leurs coûts sont des entiers positifs. Avant la panne, les "
        "distances annoncées vers D sont A : 2, B : 1, C : 2, D : 0. La liaison B-D disparaît. "
        "On étudie le modèle de calcul fourni ci-dessous, pas une implémentation complète de RIP ou OSPF. "
        "À chaque tour simultané, chaque routeur autre que D prend le minimum de "
        "coût(vers voisin) + ancienne distance annoncée par ce voisin, sur les liaisons restantes. "
        "D conserve zéro ; None représente une destination inaccessible. Les valeurs du même tour "
        "ne sont jamais réutilisées pendant ce tour. Le prochain saut est le voisin réalisant ce "
        "minimum, avec priorité alphabétique en cas d'égalité."
    )
    materials = [
        _table(
            "system_source",
            "Liaisons avant la panne",
            ["Extrémité 1", "Extrémité 2", "Coût"],
            public["links"],
        ),
        _table(
            "system_states",
            "Tableau à compléter pour 3c",
            ["Tour", "A", "B", "C", "D"],
            [[i, "...", "...", "...", "..."] for i in (1, 2, 3)],
        ),
    ]
    items = [
        _q(
            "Donner la route minimale initiale de A vers D et vérifier son coût avec le tableau.",
            "A-B-D coûte 1 + 1 = 2 ; les autres routes simples coûtent au moins 4.",
            ("La route A-B-D et son coût 2 sont justifiés par les deux liaisons.",),
            "apply",
            "ASR-ROUTAGE",
        ),
        _q(
            "Au premier tour après la panne, B hésite entre A et C. Calculer ses deux estimations et choisir son prochain saut selon la règle donnée.",
            "Par A : 1 + 2 = 3 ; par C : 1 + 2 = 3. B choisit A, premier alphabétiquement.",
            ("Les deux coûts 3 et le choix A par départage sont corrects.",),
            "apply",
            "ASR-ROUTAGE",
        ),
        _q(
            "Compléter les trois tours du tableau. Pour A, détailler les deux minima successifs qui expliquent le changement entre les tours 1 et 2.",
            "Tours 1, 2, 3 : (2,3,2,0), (4,3,2,0), (4,3,2,0). Pour A : min(1+1,2+2)=2, puis min(1+3,2+2)=4.",
            (
                "Les trois lignes sont exactes, avec utilisation des anciennes annonces.",
                "Les deux calculs pour A expliquent la hausse de 2 à 4.",
            ),
            code="ASR-ROUTAGE",
        ),
        _q(
            "Écrire tour(voisins, ancien, destination). voisins associe à chaque sommet une liste de couples (voisin, coût), ancien contient les distances ou None. Renvoyer un nouveau dictionnaire d'un tour sans modifier les arguments ; ne pas calculer les prochains sauts.",
            _solution(tour),
            (
                "Un nouveau dictionnaire est construit sans modifier ancien.",
                "Chaque estimation additionne coût et ancienne distance du voisin accessible.",
                "Le minimum est conservé, ou None si aucun voisin n'est accessible.",
                "La destination conserve zéro ; tous les sommets sont retournés.",
            ),
            "design",
            "ALG-GRAPHES",
        ),
        _q(
            "Un programme remplace directement les valeurs dans ancien, dans l'ordre A, B, C, D. Au deuxième tour, calculer B et comparer au modèle simultané : l'égalité de ces deux nombres prouve-t-elle la correction du programme ? Justifier avec la valeur de A effectivement lue par B.",
            "Après A=4, B lit cette nouvelle valeur : min(1+4,1+2)=3, donc B reste 3. Ici la valeur de B coïncide malgré une lecture interdite : le modèle impose de lire A=2, valeur du tour précédent, et non A=4 calculée pendant ce tour.",
            (
                "B=3 est calculé sans affirmer à tort qu'il change dans cet exemple.",
                "L'utilisation d'une valeur du même tour est identifiée comme contraire à la simultanéité.",
            ),
            "debug",
            "LP-DEBUG",
        ),
        _q(
            "Après le premier tour, A choisit B et B choisit A. Tracer le début du trajet d'un paquet et expliquer pourquoi une distance annoncée finie ne prouve pas sa livraison.",
            "A-B-A-B… forme une boucle. L'annonce 2 de A utilise l'ancienne annonce de B, qui dépendait de la liaison disparue. Une estimation finie peut être périmée.",
            (
                "La boucle A-B-A est explicitement tracée.",
                "Le lien entre annonces anciennes et absence de livraison est expliqué.",
            ),
            "justify",
            "ASR-ROUTAGE",
        ),
        _q(
            "Après stabilisation, déterminer les prochains sauts de A, B et C et reconstruire la route de A. Vérifier le coût réel plutôt que recopier l'annonce de A.",
            "A choisit B à égalité avec C ; B choisit C ; C choisit D. A-B-C-D coûte 1+1+2=4, en accord avec l'annonce stabilisée.",
            (
                "Les sauts A→B, B→C, C→D et la route sont corrects.",
                "La somme 4 est vérifiée sur les liaisons survivantes.",
            ),
            code="ASR-ROUTAGE",
        ),
        _q(
            "Pour la suite seulement, chaque coût représente aussi une minute de transmission. Le réseau est stabilisé avant l'émission à t=2. Un processus attend le paquet, le traite pendant 2 minutes puis transmet un rapport en 1 minute. Donner arrivée, fin de traitement et arrivée du rapport ; distinguer l'attente du paquet d'un interblocage.",
            f"Arrivée {expected['arrival']}, fin {expected['process_end']}, rapport {expected['report_arrival']}. L'attente d'une donnée réseau n'est pas à elle seule un cycle d'attente de ressources entre processus.",
            (
                "Les trois dates 6, 8, 9 sont obtenues dans l'ordre causal.",
                "L'attente réseau n'est pas confondue avec un interblocage.",
            ),
        ),
        _q(
            "Le rapport doit arriver au plus tard à t=8. Quantifier le retard et proposer une réduction chiffrée du traitement qui suffit, sans changer les liaisons.",
            "Le rapport arrive à 9, donc une minute trop tard. Réduire le traitement de 2 à 1 minute donne 6+1+1=8 : l'échéance est respectée.",
            (
                "Le retard d'une minute est établi.",
                "Une durée de traitement d'au plus une minute est justifiée par le calcul.",
            ),
            "design",
        ),
        _q(
            "Le serveur D transmet sa clé publique, préalablement authentifiée. Expliquer comment A peut lui envoyer une clé de session secrète, puis chiffrer les mesures avec cette clé de session.",
            "A chiffre la clé de session avec la clé publique authentifiée de D ; seule la clé privée de D permet de la récupérer. Les mesures utilisent ensuite le chiffrement symétrique avec cette clé de session.",
            (
                "Clé publique de D et clé privée de D sont utilisées dans le bon sens.",
                "La clé de session sert ensuite au chiffrement symétrique des mesures.",
            ),
            code="ASR-CRYPTO",
        ),
        _q(
            "Pourquoi remplacer la clé publique reçue par celle d'un attaquant compromettrait-il l'échange précédent ? Indiquer le contrôle qui manque si A accepte toute clé reçue.",
            "A chiffrerait le secret pour l'attaquant, qui possède la clé privée correspondante. A doit vérifier que la clé appartient bien à D, par exemple à l'aide d'un certificat vérifié et du nom attendu.",
            (
                "L'attaquant pourrait récupérer la clé de session.",
                "L'authentification de la clé et de son destinataire est exigée.",
            ),
            "justify",
            "ASR-CRYPTO",
        ),
        _q(
            "Un responsable conclut : « le rapport est chiffré, donc il arrivera avant t=8 et restera secret même si D est compromis ». Réfuter séparément les deux parties avec les résultats du cas.",
            "Le chiffrement ne réduit pas le trajet : le scénario initial livre à t=9. Un D compromis peut exposer les données après déchiffrement, malgré un transport chiffré.",
            (
                "Le contre-exemple t=9 réfute la garantie de délai.",
                "La compromission de l'extrémité est distinguée de la protection du transport.",
            ),
            "justify",
            "ASR-CRYPTO",
        ),
    ]
    return context, materials, items, 2


def _locks(case):
    context = (
        "Un numériseur partage trois ressources exclusives : scanner, cache et journal. "
        "Le tableau donne l'état initial S0. Chaque processus attend au plus une ressource ; "
        "il garde celles qu'il possède jusqu'à sa fin ou son arrêt forcé. Un verrou ne peut "
        "pas être repris par son propriétaire. S attend le journal sans posséder de ressource. "
        "Un arc X→Y signifie que X attend une ressource détenue par Y. Une ressource libre "
        "ne crée aucun arc. Le réseau répond aux tests de connexion, mais aucun résultat "
        "de numérisation ne parvient au client. On cherche la cause puis une reprise sûre."
    )
    materials = [
        _table(
            "system_source",
            "État S0 des processus",
            ["Processus", "Possède", "Attend"],
            [
                ["P", "scanner", "cache"],
                ["Q", "cache", "scanner"],
                ["R", "journal", "scanner"],
                ["S", "aucune", "journal"],
            ],
        ),
        _table(
            "system_states",
            "Bilan à compléter pour 3f",
            [
                "État",
                "Ressources libérées",
                "Processus pouvant avancer",
                "Cycle restant",
            ],
            [
                ["S1 : Q arrêté", "...", "...", "..."],
                ["S2 : P terminé", "...", "...", "..."],
            ],
        ),
    ]
    items = [
        _q(
            "Construire les quatre arcs du graphe d'attente à partir du tableau S0.",
            "P→Q, Q→P, R→P, S→R.",
            (
                "Les quatre arcs ont le bon sens et aucun arc supplémentaire n'est ajouté.",
            ),
            "apply",
        ),
        _q(
            "Identifier les processus membres d'un cycle, puis ceux seulement bloqués derrière ce cycle.",
            "P et Q appartiennent au cycle P→Q→P. R attend P et S attend R : R et S sont bloqués mais ne font pas partie du cycle.",
            (
                "P/Q sont distingués de leurs dépendants R/S, sans assimiler toute attente à un cycle.",
            ),
        ),
        _q(
            "On propose d'arrêter seulement S. Expliquer pourquoi cela ne débloque ni P ni Q ; comparer avec l'arrêt de Q.",
            "S ne détient aucune ressource et ne participe pas au cycle : son arrêt ne libère rien d'utile à P/Q. Arrêter Q libère le cache, que P attend ; le cycle est rompu.",
            (
                "L'arrêt de S est réfuté par ses ressources et sa position dans le graphe.",
                "La libération du cache par Q explique le déblocage de P.",
            ),
            "justify",
        ),
        _q(
            "Écrire cycle_depuis(depart, proprietaires, attentes). proprietaires associe une ressource à son propriétaire ; attentes associe un processus à sa ressource demandée. Suivre les attentes et renvoyer les membres du cycle rencontré, sans les processus qui le précèdent ; renvoyer [] si la chaîne termine. Ne pas modifier les dictionnaires.",
            _solution(cycle_depuis),
            (
                "Le chemin est mémorisé sans modifier les entrées.",
                "La ressource attendue permet de retrouver son propriétaire.",
                "Une ressource libre ou un processus sans attente termine avec [].",
                "À répétition, seule la portion cyclique du chemin est retournée.",
            ),
            "design",
            "ALG-GRAPHES",
        ),
        _q(
            "Tracer cycle_depuis depuis R puis depuis S. Un élève renvoie tout le chemin lorsqu'il détecte une répétition : donner un résultat erroné possible et corriger précisément la règle.",
            "Depuis R : R,P,Q puis P déjà vu ; depuis S : S,R,P,Q puis P déjà vu. Dans les deux cas, renvoyer [P,Q]. Renvoyer [R,P,Q] depuis R serait faux ; couper le préfixe avant la première occurrence de P.",
            (
                "Les deux traces aboutissent au même cycle P/Q.",
                "Le préfixe non cyclique est retiré à l'indice de la répétition.",
            ),
            "debug",
            "LP-DEBUG",
        ),
        _q(
            "Compléter le bilan S1 après arrêt de Q, puis S2 après terminaison de P. Pour chaque état, préciser qui peut avancer et si un cycle reste présent.",
            "S1 : Q libère cache ; P peut le prendre, R attend encore scanner et S journal ; aucun cycle. S2 : P libère scanner et cache ; R peut avancer, S attend encore journal ; aucun cycle.",
            (
                "Les libérations et possibilités en S1 sont exactes.",
                "S2 distingue le déblocage de R de l'attente persistante de S.",
            ),
        ),
        _q(
            "À t=4, Q est arrêté. P, R puis S utilisent un seul processeur, sans préemption, pendant 3, 2 puis 1 minutes. Ils libèrent leurs ressources à leur terminaison. Tracer les intervalles d'exécution et les dates de libération du scanner puis du journal.",
            "P s'exécute de 4 à 7, R de 7 à 9, S de 9 à 10. Scanner est libéré par P à 7, puis par R à 9 ; journal est libéré par R à 9, puis par S à 10.",
            (
                "Les trois intervalles 4–7, 7–9, 9–10 sont corrects.",
                "Les libérations sont liées aux terminaisons des propriétaires successifs.",
            ),
            "apply",
        ),
        _q(
            "Le résultat de S met ensuite 2 minutes à revenir au client. Le client accepte une réponse jusqu'à t=11 inclus ; au-delà, il abandonne. Calculer l'arrivée et déterminer la plus petite réduction entière de la durée de P permettant une réponse à temps.",
            "Arrivée 10+2=12, une minute après l'échéance. Réduire P de 3 à 2 minutes donne les fins 6,8,9 puis une arrivée à 11 ; réduction minimale : une minute.",
            (
                "L'arrivée à 12 et le retard sont calculés.",
                "La réduction minimale d'une minute est vérifiée sur la nouvelle chaîne.",
            ),
            "design",
        ),
        _q(
            "Pour éviter la répétition de cet incident, tous les processus prennent leurs ressources dans l'ordre scanner, cache, journal. Expliquer pourquoi un cycle d'attente serait impossible si cette règle est respectée et si toutes les prises suivent cet ordre.",
            "Un processus ne peut attendre qu'une ressource située après celles qu'il détient. Un cycle imposerait une suite strictement croissante de rangs revenant au rang initial, ce qui est impossible.",
            (
                "Chaque attente augmente strictement le rang de ressource.",
                "Le retour au rang initial d'un cycle donne une contradiction.",
            ),
            "justify",
        ),
        _q(
            "Le client relance sa demande après son abandon. Expliquer pourquoi l'absence d'interblocage ne suffit pas à éviter deux numérisations ; proposer une information permettant de reconnaître la même demande.",
            "La première demande peut finir après l'abandon puis la relance être exécutée à nouveau. Un identifiant stable de demande, conservé avec le résultat déjà produit, permet de reconnaître la relance et réutiliser ce résultat.",
            (
                "La double exécution tardive est distinguée de l'interblocage.",
                "Un identifiant de demande et un résultat mémorisé permettent la détection.",
            ),
            "design",
            "SD-LINEAIRE",
        ),
        _q(
            "Le client chiffre sa demande avec la clé publique authentifiée du serveur. Qui peut la déchiffrer ? Cela prouve-t-il au serveur l'identité du client ? Justifier les deux réponses.",
            "Le détenteur de la clé privée du serveur peut déchiffrer. Cela ne prouve pas l'identité du client : la clé publique est publique et d'autres expéditeurs peuvent l'utiliser.",
            (
                "La clé privée du serveur est identifiée.",
                "L'accès public à la clé de chiffrement réfute l'authentification de l'expéditeur.",
            ),
            "justify",
            "ASR-CRYPTO",
        ),
        _q(
            "Distinguer trois objectifs : protéger le document pendant le transport, éviter une seconde exécution et supprimer le cycle P/Q. Associer à chacun un mécanisme du cas ; expliquer pourquoi le chiffrement seul ne remplit pas les trois.",
            "Transport : chiffrement avec clé correctement authentifiée. Réexécution : identifiant stable et résultat mémorisé. Cycle : ordre global de prise des ressources. Le chiffrement ne modifie ni les verrous ni l'historique d'exécution.",
            (
                "Les trois mécanismes sont associés aux bons objectifs.",
                "Le chiffrement est explicitement distingué de la gestion des verrous et des doublons.",
            ),
            "justify",
            "ASR-CRYPTO",
        ),
    ]
    return context, materials, items, 5


def _delivery(case):
    context = (
        "Une station transmet quatre opérations A, B, C, D, numérotées de 1 à 4. Le réseau peut "
        "retarder, réordonner ou dupliquer leur réception. Le tableau est le journal complet reçu. "
        "On étudie un mécanisme applicatif simplifié, pas l'implémentation de TCP. Un tampon associe "
        "les numéros reçus à leur texte ; suivant vaut initialement 1. Une opération ne peut être "
        "transmise au consommateur que lorsque tous les numéros précédents l'ont été. On retire alors "
        "du tampon toutes les opérations consécutives disponibles. Une copie déjà transmise est ignorée. "
        "Dans ce modèle, deux copies du même numéro contiennent toujours le même texte. Les événements "
        "sont triés par date ; à date égale, l'ordre du tableau s'applique."
    )
    materials = [
        _table(
            "system_source",
            "Journal des réceptions",
            ["Date", "Numéro", "Texte"],
            case["public"]["events"],
        ),
        _table(
            "system_states",
            "Trace à compléter pour 3c",
            ["Date", "suivant", "Numéros en tampon", "Textes transmis"],
            [[row[0], "...", "...", "..."] for row in case["public"]["events"]],
        ),
        _table(
            "system_execution",
            "Chronologie à compléter pour 3g",
            ["Opération", "Disponible", "Début", "Fin"],
            [[letter, "...", "...", "..."] for letter in "ABCD"],
        ),
    ]
    items = [
        _q(
            "À t=0, B est reçu. Expliquer pourquoi il ne peut pas encore être transmis au consommateur.",
            "B porte le numéro 2 alors que suivant=1 : A manque. B doit rester dans le tampon.",
            ("L'absence du numéro 1 impose de conserver B, malgré sa réception.",),
            code="SD-LINEAIRE",
        ),
        _q(
            "À t=1, une seconde copie de B arrive. Indiquer ce qui doit changer dans le tampon et justifier le choix d'un dictionnaire indexé par numéro plutôt que l'ajout systématique à une liste.",
            "Le tampon contient toujours une seule entrée 2:B. La clé numéro permet de remplacer ou reconnaître la même opération sans créer une seconde entrée à exécuter.",
            ("Une seule entrée 2:B et l'intérêt de l'unicité de clé sont expliqués.",),
            "justify",
            "SD-LINEAIRE",
        ),
        _q(
            "Compléter la trace après chaque réception. Quand une réception libère plusieurs opérations, les écrire dans leur ordre de transmission.",
            "t=0 : suivant1, [2], rien ; t=1 : 1,[2],rien ; t=3 : 3,[],A puis B ; t=4 : 3,[4],rien ; t=6 : 5,[],C puis D ; t=7 : 5,[],rien.",
            (
                "Les valeurs de suivant et les tampons des six lignes sont exacts.",
                "Les émissions groupées A/B et C/D sont ordonnées, sans doublon.",
            ),
            "apply",
            "SD-LINEAIRE",
        ),
        _q(
            "Écrire reassembler(evenements), qui renvoie la liste des textes transmis dans l'ordre. Chaque événement est [date, numero, texte]. Utiliser un dictionnaire tampon et un entier suivant ; ignorer les numéros déjà transmis, vider toute suite consécutive disponible et ne pas modifier evenements.",
            _solution(reassembler),
            (
                "Le tampon, suivant=1 et la sortie sont initialisés sans modifier l'entrée.",
                "Les numéros déjà transmis sont ignorés, les autres sont mémorisés par numéro.",
                "Une boucle retire toutes les entrées consécutives et incrémente suivant.",
                "La liste de sortie préserve l'ordre et ne contient pas de doublon.",
            ),
            "design",
            "SD-LINEAIRE",
        ),
        _q(
            "Un élève remplace la boucle qui vide le tampon par un seul if. Tracer l'effet à t=3 puis t=4 et expliquer pourquoi B est retardé inutilement.",
            "À t=3, seul A sort et suivant devient 2 ; B reste en tampon alors qu'il est disponible. À t=4, l'arrivée de D déclenche enfin la sortie de B ; suivant devient 3 et D reste en attente. La boucle devait vider A puis B dès t=3.",
            (
                "La sortie limitée à A à t=3 et à B à t=4 est tracée correctement.",
                "Le retard vient de l'absence de répétition, pas du réseau.",
            ),
            "debug",
            "LP-DEBUG",
        ),
        _q(
            "Après chaque événement, on affirme : la sortie contient exactement une fois les numéros 1 à suivant-1, dans cet ordre. Expliquer pourquoi l'ignorance des anciens numéros et l'émission du seul numéro suivant préservent cette propriété.",
            "Un numéro inférieur à suivant appartient déjà au préfixe et n'est pas réémis. Émettre suivant ajoute exactement le prochain numéro puis l'incrémenter prolonge le préfixe d'une unité, sans trou ni répétition.",
            (
                "L'ignorance des anciens numéros garantit l'absence de répétition.",
                "L'émission puis l'incrémentation prolongent le préfixe sans trou.",
            ),
            "justify",
            "SD-LINEAIRE",
        ),
        _q(
            "Un consommateur FIFO unique commence dès qu'il reçoit une opération ; chacune dure 2 minutes, sans préemption. Compléter la chronologie : disponibilité d'après 3c, début et fin d'exécution. Pour C, expliquer l'écart entre réception et exécution.",
            "Disponibilités de A,B,C,D : 3,3,6,6. Exécution : A de 3 à 5 ; B de 5 à 7 ; C de 7 à 9 ; D de 9 à 11. C arrive à 6 et devient disponible à 6, mais B occupe le processeur jusqu'à 7.",
            (
                "Les disponibilités 3,3,6,6 et les quatre intervalles FIFO sont exacts.",
                "Le décalage 6→7 de C est expliqué par l'occupation du consommateur.",
            ),
            code="ASR-PROCESSUS",
        ),
        _q(
            "Le consommateur envoie un accusé de fin après D ; son trajet dure 1 minute. L'émetteur attend jusqu'à t=11 inclus. Calculer l'arrivée de l'accusé et expliquer pourquoi un nouvel envoi peut se produire alors que les quatre opérations sont déjà exécutées.",
            "D finit à 11, l'accusé arrive à 12. L'émetteur n'a pas encore la confirmation à son échéance et peut relancer malgré la fin réelle du travail.",
            (
                "L'arrivée à 12 est calculée à partir de la fin de D.",
                "L'absence de confirmation est distinguée de l'absence d'exécution.",
            ),
            "justify",
            "ASR-PROCESSUS",
        ),
        _q(
            "On retire du journal la réception du numéro 3 à t=6. Donner la sortie finale et le contenu restant du tampon. Un consommateur qui attend alors du travail est-il nécessairement en interblocage ? Justifier.",
            "Sortie A,B ; suivant=3 ; tampon {4:D}. Il attend une donnée manquante, mais aucun cycle de ressources entre processus n'est établi : ce n'est pas nécessairement un interblocage.",
            (
                "Le préfixe A/B et l'entrée 4:D conservée sont exacts.",
                "L'attente de donnée n'est pas assimilée sans preuve à un cycle de verrous.",
            ),
            code="ASR-PROCESSUS",
        ),
        _q(
            "Proposer deux tests supplémentaires : un journal vide et un journal où le numéro 2 arrive avant le numéro 1, avec une copie tardive de 1. Donner les sorties attendues et le défaut détecté par le second test.",
            "[] donne []. [(0,2,B),(1,1,A),(2,1,A)] donne [A,B]. Le second vérifie à la fois le réordonnancement et l'absence de seconde exécution de A.",
            (
                "L'entrée vide et sa sortie vide sont correctes.",
                "Le second journal et sa sortie A/B testent réordonnancement et doublon tardif.",
            ),
            "design",
            "LP-DEBUG",
        ),
        _q(
            "Les opérations sont chiffrées avec une clé symétrique partagée uniquement par les deux extrémités. Un observateur passif lit les paquets sur le trajet. Distinguer le contenu qu'on cherche à cacher des informations de trafic qui peuvent rester visibles.",
            "Le texte des opérations est protégé contre cet observateur si le chiffrement est correctement employé. Les adresses, volumes et dates des échanges peuvent rester visibles : chiffrer ne signifie pas masquer tout le trafic.",
            (
                "La confidentialité du texte est liée à la clé secrète et au modèle passif.",
                "Au moins deux métadonnées visibles sont citées, sans prétendre cacher tout le trafic.",
            ),
            code="ASR-CRYPTO",
        ),
        _q(
            "Le tampon accepte deux copies identiques d'un même numéro. Expliquer pourquoi comparer leurs textes ne prouve pas leur origine et pourquoi le chiffrement du transport ne protège plus le texte après compromission du consommateur.",
            "Deux textes égaux peuvent être copiés : l'égalité n'authentifie pas l'expéditeur. Le consommateur doit disposer du texte en clair pour l'exécuter ; sa compromission peut donc exposer ce texte même si le trajet était chiffré.",
            (
                "L'égalité ou la duplication n'est pas une preuve d'origine.",
                "L'accès au texte après déchiffrement explique la limite sur l'extrémité compromise.",
            ),
            "justify",
            "ASR-CRYPTO",
        ),
    ]
    return context, materials, items, 2


def render_case(seed, *, total="6"):
    if type(total) is not str or total not in {"5.5", "6", "6.5"}:
        raise ValueError("Unsupported whole-system allocation")
    case = build_case(seed)
    context, materials, items, state_index = {
        "routing": _routing,
        "locks": _locks,
        "delivery": _delivery,
    }[case["family"]](case)
    questions = []
    for index, item in enumerate(items):
        criteria = item["criteria"]
        if total == "5.5" and index in (2, 4):
            criteria = (" ".join(criteria),)
        marking = [
            dict(
                points="0.5"
                if total == "6.5" and index in (10, 11) and i == 0
                else "0.25",
                criterion=c,
            )
            for i, c in enumerate(criteria)
        ]
        questions.append(
            dict(
                id="3" + "abcdefghijkl"[index],
                prompt=item["prompt"],
                answer=item["answer"],
                points=str(
                    sum((Decimal(c["points"]) for c in marking), Decimal()).normalize()
                ),
                marking=marking,
                material_ids=["system_source"]
                + (["system_states"] if index == state_index else [])
                + (
                    ["system_execution"]
                    if case["family"] == "delivery" and index == 6
                    else []
                ),
                curriculum_codes=[item["code"]],
                operation=item["operation"],
                difficulty=4 if index in (3, 7) else 2 if index < 2 else 3,
                estimated_minutes=MINUTES[index],
                verification=dict(
                    kind="system_case_contract",
                    version=VERSION,
                    seed=seed,
                    case_sha256=case["sha256"],
                    task_id="3" + "abcdefghijkl"[index],
                    expected=case["expected"],
                ),
            )
        )
    raw = dict(
        id="3",
        title=case["public"]["title"],
        context=context,
        topics=sorted({CURRICULUM_OBJECTIVES[item["code"]][0] for item in items}),
        minutes=70,
        target_points=total,
        materials=materials,
        questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw


def case_task(seed, total="6"):
    exercise = render_case(seed, total=total)
    return dict(
        topics=exercise["topics"],
        query="réseaux processus routage interblocage chiffrement " + exercise["title"],
        minutes=exercise["minutes"],
        technical_points=total,
        required_material_kind="table",
        required_curriculum_codes=sorted(
            {c for q in exercise["questions"] for c in q["curriculum_codes"]}
        ),
        archetype_id="network-operation-and-security",
        scenario_brief=exercise["context"],
        part_briefs=[
            "A : interpréter, construire et vérifier le mécanisme fourni.",
            "B : analyser la reprise et distinguer les garanties de sécurité.",
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
