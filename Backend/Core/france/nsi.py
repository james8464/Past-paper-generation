"""Native French NSI authoring records and prompts, not translated A-level items."""

import json
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from Backend.Core.education_context import points

TOPICS = frozenset(
    {
        "structures-donnees",
        "bases-donnees",
        "architectures-reseaux",
        "langages-programmation",
        "algorithmique",
    }
)

# Capability identifiers are a compact, product-owned transcription of the
# official Terminale NSI programme. They keep each generated question tied to
# an assessable capability instead of treating a broad chapter name as proof.
CURRICULUM_OBJECTIVES = {
    "SD-INTERFACE": ("structures-donnees", "Spécifier une structure par son interface et distinguer l'implémentation."),
    "SD-POO": ("structures-donnees", "Définir une classe et utiliser ses attributs et méthodes."),
    "SD-LINEAIRE": ("structures-donnees", "Choisir et manipuler listes, piles, files ou dictionnaires."),
    "SD-ARBRE": ("structures-donnees", "Modéliser une situation par un arbre et en évaluer les mesures."),
    "SD-GRAPHE": ("structures-donnees", "Modéliser un graphe et passer entre ses représentations."),
    "BDD-MODELE": ("bases-donnees", "Identifier relations, attributs, domaines et contraintes de clés."),
    "BDD-ANOMALIES": ("bases-donnees", "Repérer redondances et anomalies d'insertion, suppression ou mise à jour."),
    "BDD-SGBD": ("bases-donnees", "Expliquer les services d'un système de gestion de bases de données."),
    "BDD-SQL-SELECT": ("bases-donnees", "Construire une interrogation SQL avec SELECT, FROM, WHERE et JOIN."),
    "BDD-SQL-MUTATION": ("bases-donnees", "Construire une requête SQL UPDATE, INSERT ou DELETE."),
    "ASR-SOC": ("architectures-reseaux", "Identifier les composants et avantages d'un système sur puce."),
    "ASR-PROCESSUS": ("architectures-reseaux", "Analyser processus, ordonnancement, ressources et interblocage."),
    "ASR-ROUTAGE": ("architectures-reseaux", "Déterminer une route selon RIP ou OSPF à partir de tables données."),
    "ASR-CRYPTO": ("architectures-reseaux", "Expliquer chiffrement symétrique, asymétrique et échange de clé."),
    "LP-CALCULABILITE": ("langages-programmation", "Raisonner sur programme-donnée, calculabilité et indécidabilité."),
    "LP-RECURSIVITE": ("langages-programmation", "Écrire et analyser un programme récursif."),
    "LP-MODULARITE": ("langages-programmation", "Exploiter une API et concevoir un module documenté."),
    "LP-PARADIGMES": ("langages-programmation", "Distinguer et choisir les paradigmes impératif, fonctionnel et objet."),
    "LP-DEBUG": ("langages-programmation", "Diagnostiquer un défaut et construire des tests pertinents."),
    "ALG-ARBRES": ("algorithmique", "Parcourir, rechercher et insérer dans un arbre binaire."),
    "ALG-GRAPHES": ("algorithmique", "Parcourir un graphe, détecter un cycle ou chercher un chemin."),
    "ALG-DIVISER": ("algorithmique", "Concevoir un algorithme diviser-pour-régner et raisonner sur son coût."),
    "ALG-DYNAMIQUE": ("algorithmique", "Concevoir une solution par programmation dynamique."),
    "ALG-BOYER": ("algorithmique", "Étudier la recherche textuelle de Boyer-Moore."),
}

COGNITIVE_OPERATIONS = frozenset(
    {"recall", "apply", "analyse", "design", "debug", "justify"}
)

LANGUAGE_RUBRIC_2027 = {
    "source": "https://www.education.gouv.fr/sites/default/files/document/annexe-attendus-et-observables-redactionnels-520693.pdf",
    "points": "2",
    "allocation_status": "indicative_product_profile",
    "dimensions": {
        "orthographe": "Maîtrise des normes orthographiques lexicales et grammaticales.",
        "syntaxe": "Construction des phrases, syntaxe et ponctuation.",
        "lexique": "Justesse et richesse du lexique, notamment disciplinaire.",
        "organisation": "Cohérence de l'organisation et fil conducteur du raisonnement.",
    },
    "bands": [
        {"id": "tres_insuffisant", "label": "Très insuffisant"},
        {"id": "insuffisant", "label": "Insuffisant"},
        {"id": "satisfaisant", "label": "Satisfaisant"},
        {"id": "tres_satisfaisant", "label": "Très satisfaisant"},
    ],
    # The official annex defines observables, not a numerical conversion. This
    # holistic conversion is deliberately labelled as a product proposal.
    "indicative_points": {
        "tres_insuffisant": "0",
        "insuffisant": "0.5",
        "satisfaisant": "1.5",
        "tres_satisfaisant": "2",
    },
}


class Credit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    points: str
    criterion: str = Field(min_length=3, max_length=1200)

    @field_validator("points")
    @classmethod
    def valid_points(cls, value):
        if points(value) <= 0:
            raise ValueError("Crédit strictement positif requis")
        return value


class NSITableMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["table"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,31}$")
    title: str = Field(min_length=3, max_length=160)
    columns: tuple[str, ...] = Field(min_length=2, max_length=8)
    rows: tuple[tuple[str, ...], ...] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def rectangular(self):
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("Les colonnes du tableau doivent être uniques")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("Le tableau structuré doit être rectangulaire")
        if any(
            not value.strip() or len(value) > 180
            for row in (self.columns, *self.rows)
            for value in row
        ):
            raise ValueError("Cellule de tableau vide ou trop longue")
        return self


class NSIWeightedGraphMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["weighted_graph"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,31}$")
    title: str = Field(min_length=3, max_length=160)
    nodes: tuple[str, ...] = Field(min_length=2, max_length=12)
    edges: tuple[tuple[str, str, int], ...] = Field(min_length=1, max_length=30)
    directed: bool

    @model_validator(mode="after")
    def valid_graph(self):
        if len(set(self.nodes)) != len(self.nodes) or any(
            not node.strip() or len(node) > 24 for node in self.nodes
        ):
            raise ValueError("Les sommets doivent être uniques et courts")
        if any(
            start not in self.nodes
            or end not in self.nodes
            or start == end
            or type(weight) is not int
            or not 0 <= weight <= 10**6
            for start, end, weight in self.edges
        ):
            raise ValueError("Arête de figure invalide")
        pairs = [
            (start, end) if self.directed else tuple(sorted((start, end)))
            for start, end, _ in self.edges
        ]
        if len(set(pairs)) != len(pairs):
            raise ValueError("Arête de figure dupliquée")
        return self


NSIMaterial = Annotated[
    NSITableMaterial | NSIWeightedGraphMaterial,
    Field(discriminator="kind"),
]


class NSIQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[1-9][0-9]?[a-z]?$", max_length=3)
    prompt: str = Field(min_length=10, max_length=4000)
    points: str
    answer: str = Field(min_length=1, max_length=6000)
    marking: tuple[Credit, ...] = Field(min_length=1, max_length=12)
    material_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=6)
    curriculum_codes: tuple[str, ...] = Field(min_length=1, max_length=3)
    operation: Literal["recall", "apply", "analyse", "design", "debug", "justify"]
    difficulty: int = Field(strict=True, ge=1, le=4)
    estimated_minutes: int = Field(strict=True, ge=2, le=40)
    verification: dict[str, Any] = Field(default_factory=lambda: {"kind": "human"})

    @model_validator(mode="after")
    def credit_matches(self):
        if points(self.points) <= 0 or sum(
            points(item.points) for item in self.marking
        ) != points(self.points):
            raise ValueError("Le barème ne correspond pas aux points de la question")
        if len(json.dumps(self.verification, ensure_ascii=False)) > 16000:
            raise ValueError("Contrat de vérification trop long")
        if len(set(self.curriculum_codes)) != len(self.curriculum_codes) or any(
            code not in CURRICULUM_OBJECTIVES for code in self.curriculum_codes
        ):
            raise ValueError("Capacité absente du programme NSI")
        return self


class NSIExercise(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[123]$")
    title: str = Field(min_length=3, max_length=160)
    context: str = Field(min_length=10, max_length=12000)
    topics: tuple[str, ...] = Field(min_length=1, max_length=5)
    minutes: int = Field(strict=True, ge=40, le=80)
    target_points: str
    materials: tuple[NSIMaterial, ...] = Field(default_factory=tuple, max_length=6)
    questions: tuple[NSIQuestion, ...] = Field(min_length=4, max_length=16)

    @field_validator("target_points")
    @classmethod
    def valid_target_points(cls, value):
        if points(value) <= 0:
            raise ValueError("Allocation technique strictement positive requise")
        return value

    @model_validator(mode="after")
    def validate_structure(self):
        if set(self.topics) - TOPICS or len(set(self.topics)) != len(self.topics):
            raise ValueError("Thème absent du programme NSI")
        identifiers = [question.id for question in self.questions]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Les identifiants de questions doivent être uniques")
        material_by_id = {material.id: material for material in self.materials}
        if len(material_by_id) != len(self.materials):
            raise ValueError("Les identifiants de figures doivent être uniques")
        for question in self.questions:
            if any(
                CURRICULUM_OBJECTIVES[code][0] not in self.topics
                for code in question.curriculum_codes
            ):
                raise ValueError("Capacité incompatible avec les thèmes du programme")
            if set(question.material_ids) - set(material_by_id):
                raise ValueError("Une question référence une figure absente")
            material_id = question.verification.get("material_id")
            if material_id is None:
                continue
            material = material_by_id.get(material_id)
            if material_id not in question.material_ids or material is None:
                raise ValueError("La vérification référence une figure absente")
            if question.verification.get("kind") == "shortest_path":
                if not isinstance(material, NSIWeightedGraphMaterial):
                    raise ValueError("La vérification de chemin exige une figure graphe")
                contract_edges = question.verification.get("edges")
                if contract_edges != [list(edge) for edge in material.edges] or (
                    question.verification.get("directed") is not material.directed
                ):
                    raise ValueError("La vérification et la figure graphe divergent")
        if self.credit != points(self.target_points):
            raise ValueError("Le crédit de l'exercice ne correspond pas à son allocation")
        covered_topics = {
            CURRICULUM_OBJECTIVES[code][0]
            for question in self.questions
            for code in question.curriculum_codes
        }
        if set(self.topics) - covered_topics:
            raise ValueError("Un thème annoncé du programme n'est pas évalué")
        if sum(question.estimated_minutes for question in self.questions) != self.minutes:
            raise ValueError("Le temps des questions ne correspond pas à l'exercice")
        operations = {question.operation for question in self.questions}
        demanding = {"analyse", "design", "debug", "justify"}
        if (
            sum(question.operation == "recall" for question in self.questions) > 1
            or len(operations) < 3
            or len(operations & demanding) < 2
            or not any(question.difficulty == 4 for question in self.questions)
        ):
            raise ValueError("Progression et demande cognitive insuffisantes")
        return self

    @property
    def credit(self) -> Decimal:
        return sum((points(question.points) for question in self.questions), Decimal(0))

    def candidate_view(self) -> dict:
        return self.model_dump(
            exclude={"questions": {"__all__": {"answer", "marking", "verification"}}},
            mode="json",
        )


def solver_prompt(exercise: NSIExercise) -> str:
    return (
        "Résous indépendamment cet exercice de spécialité NSI, Terminale, bac général. "
        "N'invente aucune donnée manquante. Signale toute ambiguïté ou impossibilité. "
        'Réponds en français, en JSON : {"answers": {identifiant: réponse détaillée}, '
        '"issues": [problèmes], "minutes": estimation}. Aucun corrigé n\'est fourni.\n'
        + json.dumps(exercise.candidate_view(), ensure_ascii=False)
    )
