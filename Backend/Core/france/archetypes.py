"""Coherent, original exercise briefs for the French NSI written route."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class QuestionIntent:
    code: str
    part_id: str
    goal: str
    response_form: str
    operation: str
    difficulty: int


@dataclass(frozen=True)
class ExerciseArchetype:
    id: str
    topics: tuple[str, ...]
    query: str
    minutes: int
    material_kind: str
    context_briefs: tuple[str, ...]
    part_briefs: tuple[str, str, str]
    intents: tuple[QuestionIntent, ...]
    scenario_brief: str = ""

    @property
    def required_curriculum_codes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(intent.code for intent in self.intents))


ARCHETYPES = (
    ExerciseArchetype(
        id="graph-and-tree",
        topics=("structures-donnees", "algorithmique"),
        query="graphes parcours arbres recherche structures de données",
        minutes=70,
        material_kind="weighted_graph",
        context_briefs=(
            "Un service organise des trajets entre lieux et classe séparément des demandes dans un arbre binaire de recherche.",
            "Un réseau de collecte relie des postes; un arbre binaire distinct indexe les interventions à traiter.",
            "Une plateforme relie des étapes de transport; un arbre binaire séparé ordonne les identifiants des colis.",
        ),
        part_briefs=(
            "A : représenter et interpréter le graphe pondéré fourni, sans inventer d'arêtes.",
            "B : appliquer ou corriger un algorithme de parcours sur ce même graphe.",
            "C : utiliser un arbre binaire de recherche distinct, avec des données explicites et un lien narratif au service.",
        ),
        intents=(
            QuestionIntent(
                "SD-GRAPHE",
                "A",
                "Lire une représentation du graphe.",
                "réponse courte",
                "apply",
                2,
            ),
            QuestionIntent(
                "SD-GRAPHE",
                "A",
                "Comparer ou mettre à jour une représentation du graphe.",
                "justification brève",
                "analyse",
                2,
            ),
            QuestionIntent(
                "ALG-GRAPHES",
                "B",
                "Diagnostiquer un parcours de graphe avec un défaut réel.",
                "correction ciblée",
                "debug",
                3,
            ),
            QuestionIntent(
                "ALG-GRAPHES",
                "B",
                "Déterminer un parcours ou chemin à partir des données fournies.",
                "trace ou calcul",
                "apply",
                3,
            ),
            QuestionIntent(
                "ALG-ARBRES",
                "C",
                "Concevoir une étape bornée d'insertion ou de recherche dans l'arbre binaire.",
                "algorithme court",
                "design",
                4,
            ),
            QuestionIntent(
                "ALG-ARBRES",
                "C",
                "Justifier un résultat ou coût de parcours de cet arbre.",
                "raisonnement contextualisé",
                "justify",
                4,
            ),
        ),
    ),
    ExerciseArchetype(
        id="database-and-debugging",
        topics=("bases-donnees", "langages-programmation"),
        query="bases de données relations SQL anomalies tests débogage",
        minutes=70,
        material_kind="table",
        context_briefs=(
            "Un service gère des réservations et corrige les requêtes et procédures qui les mettent à jour.",
            "Une association suit des prêts de matériel et vérifie ses requêtes et tests logiciels.",
            "Un atelier enregistre des interventions et diagnostique un défaut dans son traitement des données.",
        ),
        part_briefs=(
            "A : examiner les relations, leurs clés et une anomalie de données concrète.",
            "B : interroger puis modifier les mêmes données avec du SQL vérifiable.",
            "C : diagnostiquer et tester un petit programme qui utilise ces données.",
        ),
        intents=(
            QuestionIntent(
                "BDD-ANOMALIES",
                "A",
                "Repérer une anomalie d'insertion, suppression ou mise à jour dans les données.",
                "réponse courte",
                "apply",
                2,
            ),
            QuestionIntent(
                "BDD-SQL-SELECT",
                "A",
                "Analyser une interrogation liée aux relations données.",
                "justification brève",
                "analyse",
                2,
            ),
            QuestionIntent(
                "BDD-SQL-SELECT",
                "B",
                "Corriger une requête SELECT ou JOIN réellement erronée.",
                "requête corrigée",
                "debug",
                3,
            ),
            QuestionIntent(
                "BDD-SQL-MUTATION",
                "B",
                "Écrire une mutation SQL bornée et vérifiable.",
                "requête SQL",
                "apply",
                3,
            ),
            QuestionIntent(
                "LP-DEBUG",
                "C",
                "Concevoir un test qui révèle un défaut concret du traitement.",
                "test court",
                "design",
                4,
            ),
            QuestionIntent(
                "LP-DEBUG",
                "C",
                "Justifier la correction du défaut avec les valeurs du contexte.",
                "raisonnement contextualisé",
                "justify",
                4,
            ),
        ),
    ),
    ExerciseArchetype(
        id="network-operation-and-security",
        topics=("architectures-reseaux",),
        query="réseaux routage processus chiffrement sécurité",
        minutes=70,
        material_kind="table",
        context_briefs=(
            "Un réseau de capteurs échange des données entre sites et doit rester fiable et confidentiel.",
            "Plusieurs locaux partagent des routeurs et des services; une panne et un échange sécurisé sont étudiés.",
            "Une organisation relie des antennes et analyse ses routes, ses processus et la protection des messages.",
        ),
        part_briefs=(
            "A : analyser des tables de routage ou des coûts fournis, sans données implicites.",
            "B : étudier des processus, ressources ou un interblocage dans le même système.",
            "C : choisir et justifier un mécanisme de chiffrement dans ce contexte précis.",
        ),
        intents=(
            QuestionIntent(
                "ASR-ROUTAGE",
                "A",
                "Calculer une route à partir de tables ou de coûts explicites.",
                "trace ou calcul",
                "apply",
                2,
            ),
            QuestionIntent(
                "ASR-ROUTAGE",
                "A",
                "Expliquer l'effet d'un changement de route ou de coût.",
                "justification brève",
                "analyse",
                2,
            ),
            QuestionIntent(
                "ASR-PROCESSUS",
                "B",
                "Diagnostiquer un état de processus ou un interblocage réel.",
                "correction ciblée",
                "debug",
                3,
            ),
            QuestionIntent(
                "ASR-PROCESSUS",
                "B",
                "Appliquer une règle d'ordonnancement aux processus donnés.",
                "trace ou calcul",
                "apply",
                3,
            ),
            QuestionIntent(
                "ASR-CRYPTO",
                "C",
                "Proposer un protocole d'échange de clé adapté aux participants.",
                "étapes courtes",
                "design",
                4,
            ),
            QuestionIntent(
                "ASR-CRYPTO",
                "C",
                "Justifier la confidentialité obtenue et ses limites dans le contexte.",
                "raisonnement contextualisé",
                "justify",
                4,
            ),
        ),
    ),
)


def archetype_for_seed(seed: int) -> tuple[ExerciseArchetype, ...]:
    """Vary the scenario brief while retaining each exercise's learning sequence."""
    return tuple(
        replace(
            archetype,
            scenario_brief=archetype.context_briefs[
                (seed + index) % len(archetype.context_briefs)
            ],
        )
        for index, archetype in enumerate(ARCHETYPES)
    )
