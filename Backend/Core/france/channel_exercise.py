# a fully specified blocking trace and endpoint-security distinction

import hashlib
import json
from decimal import Decimal

from Backend.Core.france.channel_case import recevoir, simulate
from Backend.Core.france.database_case_prose import _solution
from Backend.Core.france.nsi import NSIExercise

VERSION = "fr-nsi-channel-exercise-v1"


def render_case(seed):
    if type(seed) is not int or not -(2**63) <= seed < 2**63:
        raise ValueError("A signed 64-bit integer seed is required")
    schedule = ["P", "P", "C", "C", "P", "C", "P", "C"]
    trace = simulate(schedule)
    digest = hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()
    events = {
        "send A": "envoi de A", "send B": "envoi de B",
        "receive A": "réception de A", "receive B": "réception de B",
        "blocked full": "blocage sur case pleine",
        "blocked empty": "blocage sur case vide",
        "close": "fermeture", "eof": "fin de communication",
    }
    trace_answer = "\n".join(
        f"Étape {index} : {row['actor']}, {events[row['event']]}, case={row['slot'] if row['slot'] is not None else 'vide'}, fermé={'oui' if row['closed'] else 'non'}, positions={row['positions']}, bloqués={row['blocked']}."
        for index, row in enumerate(trace["trace"])
    )
    items = [
        (
            "Partie A. Distinguer un processus prêt, bloqué et terminé dans ce modèle. Le processus prêt exécute-t-il nécessairement immédiatement son instruction ?",
            "Prêt : son instruction peut être choisie. Bloqué : il attend une modification de la case ou sa fermeture. Terminé : il n'a plus d'instruction. Un processus prêt doit encore être choisi par l'ordonnanceur.",
            [("0.25", "Les trois états et la différence entre prêt et choisi sont corrects.")], "analyse", "ASR-PROCESSUS",
        ),
        (
            "Les opérations de test et de modification de la case sont supposées atomiques. Expliquer ce que cette hypothèse interdit pendant une étape ; cela signifie-t-il que les deux processus sont exécutés en même temps ?",
            "Un autre processus ne s'intercale pas entre le test et la modification d'une opération. Une seule opération est exécutée à chaque étape du modèle ; l'atomicité n'implique pas leur exécution simultanée.",
            [("0.25", "L'absence d'intercalage dans une opération est distinguée de la simultanéité.")], "justify", "ASR-PROCESSUS",
        ),
        (
            "Tracer les étapes 0 à 3 du calendrier : contenu de la case, positions (P,C), ensemble des processus bloqués après chaque étape. Préciser les instructions qui n'avancent pas.",
            "0 : A, (1,0), aucun bloqué. 1 : A, (1,0), P bloqué. 2 : vide, (1,1), aucun bloqué. 3 : vide, (1,1), C bloqué. Les positions restent inchangées aux étapes 1 et 3.",
            [("0.25", "Les contenus et positions aux quatre étapes sont corrects."),
             ("0.25", "Les blocages de P puis C et l'absence d'avancement sont corrects.")], "apply", "ASR-PROCESSUS",
        ),
        (
            "À l'étape 4, P envoie-t-il A, B, ou ferme-t-il le canal ? Relier la réponse à la position conservée lors du blocage et expliquer pourquoi C devient prêt sans avoir encore reçu de valeur.",
            "P réessaie l'envoi de B : sa position est restée 1 à l'étape 1. L'envoi remplit la case et réveille C, mais C ne reçoit B que lors de sa propre étape 5.",
            [("0.25", "B est relié à la position 1 conservée."),
             ("0.25", "Le réveil de C est distingué de l'exécution de sa réception.")], "analyse", "ASR-PROCESSUS",
        ),
        (
            "Compléter la trace jusqu'à l'étape 7. Donner la séquence des résultats de C et identifier l'événement qui permet de distinguer une attente d'une fin de communication.",
            trace_answer + "\nC reçoit [A, B, None]. La fermeture explicite permet la fin quand la case est vide ; une case vide ouverte implique seulement une attente.",
            [("0.25", "Les étapes 4 à 7, positions et contenus, sont exacts."),
             ("0.25", "La séquence A, B, None et le rôle de la fermeture sont expliqués.")], "apply", "ASR-PROCESSUS",
        ),
        (
            "Partie B. Compléter recevoir(case, ferme), fonction sans modification globale. Elle renvoie (état, valeur, nouvelle_case). Les états sont 'valeur', 'fin' et 'attente'. Une valeur présente doit être livrée même après fermeture. Le pilote n'avance C que pour les états valeur ou fin ; pour attente, C est bloqué et conserve sa position.\n"
            + _solution(recevoir)
            .replace("case is not None", "__A__")
            .replace('(\"valeur\", case, None)', "__B__")
            .replace("if ferme:", "if __C__:")
            .replace('(\"attente\", None, None)', "__D__"),
            _solution(recevoir)
            + "\nA teste la présence avant la fermeture ; B livre la valeur et vide la case ; C teste ferme ; D conserve l'attente sans résultat livré ni progression de C.",
            [("0.25", "A = case is not None, avant le test de fermeture."),
             ("0.25", "B = ('valeur', case, None)."),
             ("0.25", "C = ferme et le cas fin ne livre pas de valeur ordinaire."),
             ("0.25", "D = ('attente', None, None), sans avancement de C.")], "design", "ASR-PROCESSUS",
        ),
        (
            "P termine maintenant après son second envoi, sans fermer le canal. Sur le calendrier P, C, P, C, C, quels résultats C obtient-il ? Pourquoi reste-t-il bloqué ? Est-ce nécessairement un interblocage par attente circulaire de ressources ?",
            "C reçoit A puis B ; sa troisième réception attend sur une case vide ouverte. P est terminé et ne fermera jamais le canal. C reste donc bloqué, mais il n'existe pas ici de cycle d'attente entre plusieurs processus : c'est une fin de communication non signalée.",
            [("0.25", "A et B sont reçus puis C reste en attente faute de fermeture."),
             ("0.25", "L'attente permanente est distinguée d'un cycle d'interblocage.")], "analyse", "ASR-PROCESSUS",
        ),
        (
            "Revenir au modèle initial. Utiliser le calendrier P, C, P, P, C, C. Au moment de la fermeture, B est encore dans la case. Donner les deux résultats suivants de C. Quel défaut introduirait un test de fermeture placé avant le test de présence ?",
            "C reçoit B puis None. Tester ferme en premier renverrait fin alors que B attend encore : la valeur B serait perdue.",
            [("0.25", "B puis None sont obtenus dans cet ordre."),
             ("0.25", "La perte de B est reliée à l'ordre fautif des tests.")], "debug", "ASR-PROCESSUS",
        ),
        (
            "Une version fautive avance la position de P même si l'envoi trouve la case pleine. Rejouer le début P, P, C, P, C. Donner la valeur perdue et expliquer pourquoi la fermeture ne permet pas de la récupérer.",
            "P envoie A ; son envoi de B échoue mais sa position passe à 2. C reçoit A ; P ferme ; C reçoit None. B n'a jamais été placée dans la case. Une fermeture indique seulement qu'il n'y aura plus d'envoi ; elle ne recrée pas une valeur perdue.",
            [("0.25", "La trace fautive livre A puis None et perd B."),
             ("0.25", "La perte est causée par l'avancement après l'envoi bloqué, pas par la fermeture elle-même.")], "debug", "ASR-PROCESSUS",
        ),
        (
            "Justifier deux propriétés du modèle correct : la case ne contient jamais deux valeurs ; B ne peut être reçue avant A. Votre argument doit couvrir les envois réussis, les blocages et les réceptions, pas seulement le calendrier donné.",
            "Un envoi écrit seulement si la case est vide ; sinon il bloque sans changer la case. Une réception prend la valeur puis vide la case. P n'essaie B qu'après avoir envoyé A ; il ne peut écrire B avant qu'A ait été retirée. Les blocages n'écrivent aucune valeur et n'avancent aucune instruction.",
            [("0.25", "L'alternance écriture sur vide et lecture qui vide garantit la capacité unitaire."),
             ("0.25", "L'ordre du programme et l'absence d'avancement lors du blocage garantissent A avant B.")], "justify", "ASR-PROCESSUS",
        ),
        (
            "Partie C, indépendante des calendriers. Deux applications situées sur des machines distinctes chiffrent leurs messages. Distinguer chiffrement symétrique et asymétrique par les clés utilisées. Pour un chiffrement asymétrique visant la confidentialité vers C, quelle clé P utilise-t-il et quelle clé C garde-t-il secrète ?",
            "Le symétrique emploie une clé secrète partagée. L'asymétrique utilise une paire clé publique et clé privée. P chiffre vers C avec la clé publique de C ; C conserve sa clé privée pour déchiffrer. L'authenticité de la clé publique reçue doit être assurée séparément.",
            [("0.25", "Clé partagée et paire publique/privée sont distinguées."),
             ("0.25", "P utilise la clé publique de C ; la clé privée de C reste secrète.")], "analyse", "ASR-CRYPTO",
        ),
        (
            "Le transport est correctement chiffré, mais un logiciel malveillant sur C lit les messages après déchiffrement. Le chiffrement du transport suffit-il à protéger leur contenu dans ce cas ? Distinguer ce risque de l'observation des horaires et volumes de messages sur le réseau.",
            "Non : C doit déchiffrer pour utiliser les messages ; un logiciel compromis peut lire ce texte sur le terminal. Le chiffrement du transport ne protège pas à lui seul un terminal compromis. Sur le réseau, les horaires et volumes peuvent rester observables sans révéler directement le texte déchiffré.",
            [("0.25", "L'accès au texte après déchiffrement explique la limite sur le terminal."),
             ("0.25", "Les métadonnées horaires/volumes sont distinguées du contenu.")], "justify", "ASR-CRYPTO",
        ),
    ]
    minutes = [3, 3, 6, 6, 5, 12, 4, 6, 8, 6, 6, 5]
    questions = []
    for index, (prompt, answer, credits, operation, code) in enumerate(items):
        questions.append(dict(
            id="3" + "abcdefghijkl"[index], prompt=prompt, answer=answer,
            points=str(sum(Decimal(value) for value, _ in credits)),
            marking=[dict(points=value, criterion=criterion) for value, criterion in credits],
            material_ids=["channel_rules"] if index < 10 else [],
            curriculum_codes=[code], operation=operation,
            difficulty=4 if index in (5, 8, 9) else 3,
            estimated_minutes=minutes[index], verification=dict(
                kind="channel_case_contract", version=VERSION, seed=seed, case_sha256=digest),
        ))
    raw = dict(
        id="3", title="Communiquer sans perdre de valeur",
        context="Deux processus P et C communiquent par une case de capacité une valeur, initialement vide et ouverte. None représente l'absence de valeur ; seules A et B sont des valeurs ordinaires. P exécute envoyer A, envoyer B, fermer ; C exécute trois réceptions. Les positions initiales sont (0,0), et chaque opération réussie avance uniquement son processus d'une position. Fermer ne vide pas la case. Un envoi sur case pleine ou une réception sur case vide ouverte bloque sans avancer ; le changement de condition réveille le processus, qui réessaie ensuite la même instruction quand il est choisi. Un processus bloqué ou terminé ne peut être choisi. Chaque étape est atomique. Le calendrier initial est P, P, C, C, P, C, P, C, numéroté de 0 à 7. Les autres calendriers sont explicitement indiqués ; chaque question repart de l'état initial. Rédiger sur votre copie.",
        topics=["architectures-reseaux"], minutes=70, target_points="6",
        materials=[dict(
            kind="table", id="channel_rules", title="Opérations atomiques du modèle",
            columns=["Opération", "Condition", "Effet", "Réveil"],
            rows=[
                ["envoyer", "case vide", "déposer la valeur ; avancer P", "C prêt s'il était bloqué"],
                ["envoyer", "case pleine", "bloquer P ; ne pas avancer", "aucun"],
                ["recevoir", "valeur présente", "prendre puis vider ; avancer C", "P prêt s'il était bloqué"],
                ["recevoir", "vide et ouvert", "bloquer C ; ne pas avancer", "aucun"],
                ["recevoir", "vide et fermé", "renvoyer None ; avancer C", "aucun"],
                ["fermer", "ouvert", "marquer fermé ; avancer P ; garder la valeur", "C prêt s'il était bloqué"],
            ],
        )], questions=questions,
    )
    NSIExercise.model_validate(raw)
    return raw
