"""Education-system identity, independent of interface locale and UK board models."""

import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class EducationContext:
    education_system: str
    country: str
    qualification: str
    pathway: str
    stage: str
    subject: str
    framework: str
    document_language: str

    def __post_init__(self):
        for name, value in asdict(self).items():
            if (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
            ):
                raise ValueError(f"Invalid education context {name}")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def points(value: str) -> Decimal:
    """Read exact, non-negative decimal credit from a JSON string."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,6}(?:\.\d{1,4})?", value):
        raise ValueError("Points must be a non-negative decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Invalid points") from error


@dataclass(frozen=True)
class CurriculumVersion:
    id: str
    context: EducationContext
    effective_from: str
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class AssessmentDefinition:
    id: str
    context: EducationContext
    curriculum_version: str
    rule_version: str
    session: int
    duration_minutes: int
    technical_points: str
    language_points: str
    total_points: str
    component_weight: str
    source_url: str

    def validate_context(
        self, context: EducationContext, *, session: int | None = None
    ):
        if context != self.context:
            raise ValueError("Assessment context does not match the selected framework")
        if session is not None and session != self.session:
            raise ValueError("Unsupported assessment session")

    def validate_credit(self, exercise_points: list[str], language_points: str):
        if len(exercise_points) != 3:
            raise ValueError("NSI requires three independent exercises")
        credit = [points(value) for value in exercise_points]
        if any(value <= 0 for value in credit) or sum(credit) != points(
            self.technical_points
        ):
            raise ValueError("Incorrect technical credit total")
        if points(language_points) != points(self.language_points):
            raise ValueError("Incorrect language credit total")
        if sum(credit) + points(language_points) != points(self.total_points):
            raise ValueError("Incorrect assessment credit total")


NSI_CONTEXT = EducationContext(
    education_system="fr-national",
    country="FR",
    qualification="bac-general",
    pathway="generale",
    stage="terminale",
    subject="nsi",
    framework="men-nsi",
    document_language="fr-FR",
)
NSI_CURRICULUM = CurriculumVersion(
    id="nsi-2019",
    context=NSI_CONTEXT,
    effective_from="2020-09-01",
    source_urls=("https://eduscol.education.fr/document/30010/download",),
)
NSI_2027 = AssessmentDefinition(
    id="fr-bac-general-nsi-written-2027",
    context=NSI_CONTEXT,
    curriculum_version="nsi-2019",
    rule_version="MENE2622643N",
    session=2027,
    duration_minutes=210,
    technical_points="18",
    language_points="2",
    total_points="20",
    component_weight="0.75",
    source_url="https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N",
)
