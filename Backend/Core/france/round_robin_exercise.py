"""Original scheduling questions for an experimental fourth paper family.

The public V32 route is unchanged. Proposed answers use a separately tested
scheduling model; they are not learner-calibrated or an official mark scheme.
"""

from decimal import Decimal

from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.nsi import NSIExercise
from Backend.Core.france.round_robin_case import build_case

VERSION = "fr-nsi-round-robin-exercise-v1"
MINUTES = (4, 7, 7, 6, 8, 8, 6, 7, 5, 5, 3, 4)
POINTS = (
    "0.25",
    "0.5",
    "0.5",
    "0.5",
    "1",
    "0.75",
    "0.5",
    "0.5",
    "0.5",
    "0.5",
    "0.25",
    "0.25",
)


def tranche(file, restants, t, quantum):
    processus = file.pop(0)
    reste = restants[processus]
    duree = min(quantum, reste)
    restants[processus] -= duree
    return processus, t + duree


def attentes(jobs, fins):
    resultat = {}
    for nom, arrivee, duree in jobs:
        sejour = fins[nom] - arrivee
        resultat[nom] = sejour - duree
    return resultat


def render_case(seed, *, total="6"):
    if type(total) is not str or total != "6":
        raise ValueError("This scheduling exercise allocates exactly six points")
    case = build_case(seed)
    baseline, revised = case["baseline"], case["revised"]
    trace = "\n".join(
        f"{name} : [{start}, {end}[ ; file ensuite : {queue}"
        for (name, start, end), queue in zip(
            baseline["slices"], baseline["ready_after"], strict=True
        )
    )
    scaffold = (
        _solution(tranche)
        .replace("file.pop(0)", "__A__")
        .replace("min(quantum, reste)", "__B__")
        .replace("restants[processus] -= duree", "__C__")
        .replace("t + duree", "__D__")
    )
    items = [
        (
            "Juste après t = 1, quels processus sont en cours d'exécution, prêts ou pas encore arrivés ? Aucun processus de ce modèle n'est bloqué en attente d'une ressource. Distinguer cet état de l'attente du processeur.",
            "A s'exécute, B est prêt, C et D ne sont pas encore arrivés. B attend le processeur, pas une ressource ou une entrée-sortie : il n'est pas bloqué.",
            [
                "Les quatre états sont corrects et l'attente du processeur est distinguée d'un blocage."
            ],
            "apply",
            "ASR-PROCESSUS",
        ),
        (
            "Compléter les sept lignes de la trace : processus exécuté, début, fin et file prête après chaque tranche. Conserver l'ordre de la file ; une tranche peut être plus courte que le quantum.",
            trace,
            [
                "Les sept intervalles et processus respectent le quantum et les durées restantes.",
                "Chaque file respecte l'ordre d'arrivée, y compris les arrivées aux bornes des tranches.",
            ],
            "apply",
            "ASR-PROCESSUS",
        ),
        (
            "Déduire les dates de fin des quatre processus. Le temps d'attente est ici la durée passée prêt sans exécution, de l'arrivée à la fin. Justifier la formule attente = fin - arrivée - durée CPU, puis calculer les quatre attentes et leur moyenne.",
            f"Fins : {baseline['finished']}. Attentes A = 6, B = 4, C = 2, D = 1 ; moyenne 13/4 = 3,25 unités. Sans entrée-sortie ni coût de commutation, le séjour fin-arrivée se partage uniquement entre exécution et attente du processeur.",
            [
                "Les dates de fin et les attentes 6, 4, 2, 1 donnent la moyenne 13/4.",
                "La formule est justifiée par la partition du séjour en temps CPU et attente, selon les hypothèses du modèle.",
            ],
            "analyse",
            "ASR-PROCESSUS",
        ),
        (
            "À t = 7, expliquer pourquoi la file est B, D, A. Un ordonnanceur incorrect remet A en file avant de traiter l'arrivée de D. Poursuivre sa trace après t = 7 et donner les nouvelles dates de fin de A et D. Quelles dates de fin restent inchangées ?",
            "B attend déjà ; D arrive à t = 7 ; A revient ensuite : B, D, A. Le programme incorrect produit B, A, D, puis B sur [7,8[, A sur [8,9[, D sur [9,11[. A finit à 9 au lieu de 11 et D à 11 au lieu de 10 ; B finit toujours à 8 et C à 5.",
            [
                "La bonne file B, D, A et la file incorrecte B, A, D sont expliquées par la convention de frontière.",
                "La trace fautive et les quatre conclusions sur les dates de fin sont correctes.",
            ],
            "debug",
            "ASR-PROCESSUS",
        ),
        (
            "La fonction tranche traite une file non vide de processus déjà prêts. restants associe à chacun une durée CPU strictement positive ; quantum est strictement positif. Elle retire le premier processus, modifie sa durée restante et renvoie son nom et la date de fin de tranche. Elle ne traite ni les nouvelles arrivées ni la remise en file. Compléter __A__, __B__, __C__ et __D__, puis justifier l'emploi de min.\n"
            + scaffold,
            _solution(tranche)
            + "\nmin évite d'exécuter un processus au-delà de sa durée restante. C n'a besoin que d'une unité malgré le quantum 2.",
            [
                "Le premier élément est retiré et la durée choisie est min(quantum, restants[processus]).",
                "La durée restante et la date finale sont mises à jour sans dépasser le travail restant ; min est justifié.",
            ],
            "design",
            "LP-DEBUG",
        ),
        (
            "Le programme principal appelle tranche puis doit réaliser les trois étapes suivantes :\n(1) remettre le processus à la fin de la file si sa durée restante est positive ;\n(2) ajouter les nouveaux processus dont l'arrivée est inférieure ou égale à la fin de tranche, dans l'ordre de la table ;\n(3) enregistrer sa date de fin si sa durée restante est nulle.\nDonner un ordre valide de ces étapes. Écrire le test et les instructions des étapes (1) et (3), avec les variables processus, fin, file, restants et fins. Pourquoi l'étape (2) utilise-t-elle <= plutôt que == ?",
            "Un ordre valide est (2), puis le test des étapes (1)/(3) :\n```python\nif restants[processus] > 0:\n    file.append(processus)\nelse:\n    fins[processus] = fin\n```\nL'étape (2) doit précéder (1). <= inclut aussi les processus arrivés pendant la tranche, pas seulement à sa fin. Chaque arrivée est ajoutée une seule fois grâce à un indice sur la table triée.",
            [
                "Les arrivées sont ajoutées avant la remise en file ; <= couvre l'intérieur et la borne de la tranche.",
                "Le test distingue durée restante positive et nulle, avec remise en file ou enregistrement exact de la fin.",
            ],
            "design",
            "LP-DEBUG",
        ),
        (
            "Écrire attentes(jobs, fins). jobs contient les triplets (nom, arrivée, durée CPU) et fins associe chaque nom à sa date de fin. La fonction renvoie un nouveau dictionnaire des attentes sans modifier ses arguments. Quel est son coût en fonction du nombre de processus, en supposant les accès au dictionnaire de coût constant ?",
            _solution(attentes)
            + "\nUne seule boucle réalise un nombre constant d'opérations par processus : coût linéaire en leur nombre.",
            [
                "Chaque attente est enregistrée sous le bon nom dans un nouveau dictionnaire, sans mutation des arguments.",
                "Le parcours unique justifie le coût linéaire sous l'hypothèse donnée.",
            ],
            "design",
            "LP-MODULARITE",
        ),
        (
            "On recommence depuis les données initiales avec un quantum de 1, sans conserver les durées restantes de la première exécution. Tracer les tranches jusqu'à la fin et comparer les dates de fin de C et D ainsi que la première date d'exécution de C. Peut-on en déduire que réduire le quantum améliore toutes les dates de fin ?",
            f"Tranches : {revised['slices']}. C commence à 3 au lieu de 4 et finit à 4 au lieu de 5 ; D finit à 11 au lieu de 10. Ce contre-exemple réfute une amélioration de toutes les dates de fin. Les deux simulations ignorent le coût de commutation.",
            [
                "La trace pour le quantum 1 et les comparaisons sur C sont exactes.",
                "D finit plus tard : l'affirmation universelle est réfutée, sans inventer un coût de commutation.",
            ],
            "analyse",
            "ASR-PROCESSUS",
        ),
        (
            "Vérifier que la somme des longueurs des tranches pour le quantum 2 est égale à la somme des durées CPU demandées. Le processeur est-il inactif entre t = 0 et la dernière fin ? Expliquer pourquoi les temps d'attente ne doivent pas être ajoutés aux durées CPU pour calculer cette durée totale.",
            "Les tranches durent 2+2+1+2+1+2+1 = 11, comme 5+3+1+2 = 11. Elles couvrent [0,11[ sans trou. L'attente d'un processus se déroule pendant l'exécution d'autres processus ; l'ajouter compterait plusieurs fois les mêmes instants.",
            [
                "Les deux sommes valent 11 et la trace ne contient aucun intervalle inactif.",
                "La simultanéité entre attentes et exécution explique le double comptage à éviter.",
            ],
            "justify",
            "ASR-PROCESSUS",
        ),
        (
            "On conserve un nombre fini de processus et des durées CPU finies strictement positives. Expliquer pourquoi l'algorithme finit avec un quantum entier strictement positif. Le seul fait que B attende A au début prouve-t-il un interblocage ? Justifier à partir du modèle de ressources donné.",
            "Chaque tranche exécute au moins une unité et diminue la somme entière des durées restantes. Cette somme est finie ; les périodes inactives ne durent que jusqu'à la prochaine arrivée de la liste finie. B prêt attend son tour, sans conserver de ressource exigée par A. Il n'y a aucun cycle d'attente de ressources dans ce modèle : ce n'est pas un interblocage.",
            [
                "Une quantité entière positive décroît à chaque tranche ; les arrivées et périodes inactives sont finies.",
                "L'attente en file est distinguée d'un cycle d'attente de ressources ; aucun interblocage n'est déduit du simple partage CPU.",
            ],
            "justify",
            "ASR-PROCESSUS",
        ),
        (
            "Pourquoi faut-il refuser quantum = 0 avant de lancer l'ordonnancement ? Décrire l'effet de cette valeur sur une tranche et sur l'argument de terminaison précédent.",
            "La tranche aurait une durée nulle : ni l'instant ni la durée restante ne progresseraient, et le processus serait remis en file indéfiniment. La décroissance utilisée dans la preuve disparaît.",
            [
                "L'absence de progrès et de décroissance explique le risque de boucle infinie et le refus de zéro."
            ],
            "debug",
            "LP-DEBUG",
        ),
        (
            "On ajoute E, arrivé à t = 20, demandant une unité CPU. Le reste des données et le quantum 2 sont inchangés. Donner la période d'inactivité supplémentaire, le nouvel intervalle d'exécution et l'attente de E. Quelle information doit utiliser le programme quand la file est vide mais que des arrivées restent à traiter ?",
            "Après la fin à t = 11, le processeur est inactif sur [11,20[. E s'exécute sur [20,21[, finit à 21 et attend 21-20-1 = 0. L'instant doit avancer jusqu'à la prochaine arrivée non encore traitée, sans prétendre exécuter une file vide.",
            [
                "L'intervalle inactif, l'exécution de E, son attente nulle et l'avancement à la prochaine arrivée sont cohérents."
            ],
            "analyse",
            "ASR-PROCESSUS",
        ),
    ]
    questions = []
    for index, (
        (prompt, answer, criteria, operation, code),
        credit,
        minutes,
    ) in enumerate(zip(items, POINTS, MINUTES, strict=True)):
        value = Decimal(credit)
        allocations = (
            [value]
            if len(criteria) == 1
            else [value - Decimal("0.25"), Decimal("0.25")]
        )
        if value == 1:
            allocations = [Decimal("0.5"), Decimal("0.5")]
        questions.append(
            dict(
                id="3" + "abcdefghijkl"[index],
                prompt=prompt,
                answer=answer,
                points=credit,
                marking=[
                    dict(points=str(p), criterion=c)
                    for p, c in zip(allocations, criteria, strict=True)
                ],
                material_ids=["processes"] + (["schedule_trace"] if index == 1 else []),
                curriculum_codes=[code],
                operation=operation,
                difficulty=4 if index in (5, 9) else 2 if index == 0 else 3,
                estimated_minutes=minutes,
                verification=dict(
                    kind="round_robin_case_contract",
                    version=VERSION,
                    task_id="3" + "abcdefghijkl"[index],
                    seed=seed,
                ),
            )
        )
    result = dict(
        id="3",
        title="Partager le processeur sans perdre les nouvelles arrivées",
        context=(
            "Un atelier lance quatre traitements sur un processeur unique. Le tableau donne leur arrivée et leur durée CPU totale, en unités de temps entières. "
            "On utilise un tourniquet avec un quantum de 2. Une file conserve les processus prêts, le premier à gauche. Un processus exécute au plus un quantum, ou moins s'il termine. "
            "Les arrivées pendant cette tranche ne l'interrompent pas. À sa fin, on ajoute les nouveaux arrivants par ordre du tableau, y compris ceux arrivés exactement à cet instant, puis on remet le processus exécuté en fin de file s'il lui reste du travail. "
            "Un processus terminé sort définitivement de la file. Au départ, seuls les processus déjà arrivés sont prêts. "
            "Les intervalles [début, fin[ incluent le début et excluent la fin. On ignore les entrées-sorties et le coût de changement de processus. "
            "Les questions suivantes réutilisent la trace et la convention d'arrivée ; les changements de quantum repartent toujours des données initiales."
        ),
        topics=["architectures-reseaux", "langages-programmation"],
        minutes=70,
        target_points=total,
        materials=[
            dict(
                kind="table",
                id="processes",
                title="Processus à ordonnancer",
                columns=["Nom", "Arrivée", "Durée CPU"],
                rows=[[str(v) for v in job] for job in case["jobs"]],
            ),
            dict(
                kind="table",
                id="schedule_trace",
                title="Trace à compléter pour 3b",
                columns=["Processus", "Début", "Fin", "File ensuite"],
                rows=[["...", "...", "...", "..."] for _ in baseline["slices"]],
            ),
        ],
        questions=questions,
    )
    NSIExercise.model_validate(result)
    return result
