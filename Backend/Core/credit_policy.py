"""Origin-preserving open credit rules; never promote model advice to authority."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CREDIT_POLICY_VERSION = "declared-open-credit-v1"
RULE_FIELDS = ("alternatives", "partial_credit_boundaries", "follow_through_rules")
PERMISSIONS = {
    "equivalent-assessed-route": "Marker check: reward a valid alternative route where it demonstrates the same assessed knowledge or skill.",
    "equivalent-technical-method": "Accept equivalent pseudocode, terminology or a technically valid alternative method.",
    "equivalent-configured-route": "Accept an equivalent, technically accurate route.",
}


def alternative_permission(permission_id: str) -> dict[str, Any]:
    """Only known host-authored permissions can bypass answer-value checking."""
    return {
        "valid_alternatives": [PERMISSIONS[permission_id]],
        "alternative_permission_ids": [permission_id],
        "alternative_permission_version": CREDIT_POLICY_VERSION,
    }


class CreditRule(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["alternatives", "partial_credit_boundaries", "follow_through_rules"]
    origin: Literal["source-declared", "model-advisory", "closed-answer-validation"]
    content_kind: Literal["permission", "answer", "guidance"]
    text: str
    score: int | None = Field(default=None, ge=0, strict=True)
    cap: int | None = Field(default=None, ge=0, strict=True)
    dependencies: list[str] = Field(default_factory=list)
    raw: Any


def credit_rule(
    kind: str, origin: str, raw: Any, *, permission: bool = False
) -> CreditRule:
    payload = raw if isinstance(raw, dict) else {}
    text = (
        str(
            next(
                (
                    payload[key]
                    for key in ("text", "description", "condition", "rule", "point")
                    if payload.get(key)
                ),
                "",
            )
        )
        if payload
        else str(raw)
    )
    return CreditRule(
        kind=kind,
        origin=origin,
        content_kind="permission"
        if permission
        else "answer"
        if kind == "alternatives"
        else "guidance",
        text=text,
        score=payload.get("score"),
        cap=payload.get("cap"),
        dependencies=payload.get("dependencies", []),
        raw=raw,
    )


def collect_credit_rules(
    context: dict, result: dict, *, closed: bool, marks: int
) -> tuple[list[CreditRule], list[str]]:
    rules, warnings = [], []
    permissions = context.get("alternative_permission_ids", [])
    if not isinstance(permissions, list) or any(
        not isinstance(key, str) or key not in PERMISSIONS for key in permissions
    ):
        raise ValueError("unknown alternative permission metadata")
    if permissions and (
        context.get("alternative_permission_version") != CREDIT_POLICY_VERSION
        or context.get("valid_alternatives")
        != [PERMISSIONS[key] for key in permissions]
    ):
        raise ValueError(
            "alternative permission text or version differs from the host declaration"
        )
    for field in RULE_FIELDS:
        declared = context.get(
            "valid_alternatives" if field == "alternatives" else field, []
        )
        for origin, values in (
            ("source-declared", declared),
            (
                "closed-answer-validation"
                if closed and field == "alternatives"
                else "model-advisory",
                result.get(field, []),
            ),
        ):
            if values is None:
                continue
            if not isinstance(values, list):
                raise ValueError(f"{field} must be a list of credit rules")
            for value in values:
                rule = credit_rule(
                    field,
                    origin,
                    value,
                    permission=bool(permissions)
                    and origin == "source-declared"
                    and field == "alternatives",
                )
                rules.append(rule)
                if origin == "model-advisory" and any(
                    number is not None and number > marks
                    for number in (rule.score, rule.cap)
                ):
                    warnings.append(
                        f"Advisory {field} exceeds the item tariff: {value}"
                    )
                if origin == "model-advisory":
                    for source in rules:
                        if (
                            source.origin == "source-declared"
                            and source.kind == field
                            and source.text == rule.text
                            and (source.score, source.cap, source.dependencies)
                            != (rule.score, rule.cap, rule.dependencies)
                        ):
                            warnings.append(
                                f"Advisory {field} contradicts a declared rule: {value}"
                            )
    return rules, warnings


def declared_rule_metadata_present(rule: CreditRule, raw: dict, points: list) -> bool:
    """Preserve numerical caps/dependencies, not just their descriptive prose.

    Explicit structured rules are preferred. A scored point with the exact
    condition is also a valid legacy representation of a simple score boundary.
    This is structural comparison, not a semantic entailment claim.
    """
    if rule.score is None and rule.cap is None and not rule.dependencies:
        return True
    matches = []
    for value in raw.get(rule.kind, []):
        if isinstance(value, dict):
            other = credit_rule(rule.kind, "source-declared", value)
            if other.text == rule.text:
                matches.append(
                    (other.score, other.cap, other.dependencies)
                    == (rule.score, rule.cap, rule.dependencies)
                )
    if matches:
        return all(matches)
    if rule.cap is None and not rule.dependencies:
        return any(
            isinstance(point, dict)
            and rule.text.casefold() in str(point.get("text", "")).casefold()
            and point.get("marks") == rule.score
            for point in points
        )
    return False
