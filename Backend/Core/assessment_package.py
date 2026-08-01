from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from Backend.Core.assessment_quality import (
    assert_distinct_items,
    item_fingerprint,
)


def write_assessment_package(
    paper: Any,
    path: Path,
    *,
    subject: str,
    paper_number: str,
    preview: bool,
    provider: str | None,
    model: str | None,
) -> Path:
    """Write the renderer-independent item record used by release validation."""

    payload = _serialise(paper)
    items = _extract_items(
        payload,
        subject=subject,
        paper_number=paper_number,
    )
    if not preview:
        assert_distinct_items(items)
    form_id = _form_id(
        subject=subject,
        paper_number=paper_number,
        items=items,
    )
    document = {
        "schema_version": 1,
        "form_id": form_id,
        "subject": subject,
        "paper": paper_number,
        "seed": payload.get("seed"),
        "preview": preview,
        "provider": None if preview else provider,
        "model": None if preview else model,
        "items": items,
        "blueprint": payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def validate_assessment_package(
    path: Path,
    *,
    subject: str,
    paper_number: str,
    preview: bool,
    provider: str | None,
    model: str | None,
) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("generator returned an unsupported assessment package")
    expected = (subject, paper_number, preview)
    actual = (
        document.get("subject"),
        document.get("paper"),
        document.get("preview"),
    )
    if actual != expected:
        raise ValueError(
            f"assessment package identity {actual} does not match request {expected}"
        )
    if not preview and (
        document.get("provider") != provider or document.get("model") != model
    ):
        raise ValueError(
            "assessment package provider/model does not match the generation request"
        )
    items = document.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("assessment package has no items")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("assessment package contains an invalid item")
        prompt = str(item.get("prompt", "")).strip()
        if not prompt or item.get("fingerprint") != item_fingerprint(prompt):
            raise ValueError(
                f"assessment item {item.get('id')} has an invalid fingerprint"
            )
        if not isinstance(item.get("marks"), int) or int(item["marks"]) <= 0:
            raise ValueError(
                f"assessment item {item.get('id')} has invalid marks"
            )
        scheme = item.get("mark_scheme")
        if not isinstance(scheme, list) or not any(str(point).strip() for point in scheme):
            raise ValueError(
                f"assessment item {item.get('id')} has no usable mark scheme"
            )
    if not preview:
        assert_distinct_items(items)
    expected_form_id = _form_id(
        subject=subject,
        paper_number=paper_number,
        items=items,
    )
    if document.get("form_id") != expected_form_id:
        raise ValueError("assessment package form identity is invalid")
    return {
        "schema_version": document["schema_version"],
        "form_id": expected_form_id,
        "item_count": len(items),
        "fingerprints_verified": True,
        "mark_schemes_present": True,
    }


def _serialise(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        raw = value.model_dump(mode="json")
    elif isinstance(value, dict):
        raw = value
    else:
        raise TypeError("assessment package requires a Pydantic model or mapping")
    if not isinstance(raw, dict):
        raise TypeError("assessment package blueprint must serialise to an object")
    return raw


def _extract_items(
    blueprint: dict[str, Any],
    *,
    subject: str,
    paper_number: str,
) -> list[dict[str, Any]]:
    discovered: list[tuple[str, dict[str, Any], list[str]]] = []

    def walk(value: Any, path: list[str], inherited_stems: list[str]) -> None:
        if isinstance(value, dict):
            stems = inherited_stems
            stem = value.get("stem")
            if isinstance(stem, str) and stem.strip():
                stems = [*inherited_stems, stem.strip()]
            prompt = value.get("prompt")
            marks = value.get("marks")
            if isinstance(prompt, str) and prompt.strip() and isinstance(marks, int):
                discovered.append((".".join(path), value, stems))
            for key, child in value.items():
                walk(child, [*path, str(key)], stems)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, [*path, str(index)], inherited_stems)

    walk(blueprint, [], [])
    items: list[dict[str, Any]] = []
    for index, (path, raw, stems) in enumerate(discovered, start=1):
        prompt = str(raw["prompt"]).strip()
        item_id = str(
            raw.get("number")
            or raw.get("label")
            or raw.get("rule_id")
            or f"item-{index}"
        )
        scheme = _scheme_text(raw)
        items.append(
            {
                "id": f"{item_id}@{path}",
                "subject": subject,
                "paper": paper_number,
                "topic_id": raw.get("topic_id"),
                "marks": raw["marks"],
                "command_word": raw.get("command_word"),
                "prompt": prompt,
                "context": stems,
                "mark_scheme": scheme,
                "fingerprint": item_fingerprint(prompt),
                "provenance": raw.get("provenance", "generator-specific"),
            }
        )
    if not items:
        raise ValueError("assessment blueprint contains no marked question items")
    return items


def _scheme_text(raw: dict[str, Any]) -> list[str]:
    for key in ("mark_scheme", "indicative_content"):
        value = raw.get(key)
        if isinstance(value, list):
            result = [str(item).strip() for item in value if str(item).strip()]
            if result:
                return result
    marking = raw.get("marking")
    if isinstance(marking, dict):
        result: list[str] = []
        for key in ("points", "accept", "reject", "levels"):
            value = marking.get(key)
            if isinstance(value, list):
                result.extend(str(item).strip() for item in value if str(item).strip())
        if result:
            return result
    breakdown = str(raw.get("mark_breakdown", "")).strip()
    return [breakdown] if breakdown else []


def _form_id(
    *,
    subject: str,
    paper_number: str,
    items: list[dict[str, Any]],
) -> str:
    identity = {
        "subject": subject,
        "paper": paper_number,
        "items": [
            {
                "id": item.get("id"),
                "marks": item.get("marks"),
                "fingerprint": item.get("fingerprint"),
                "mark_scheme": item.get("mark_scheme"),
            }
            for item in items
        ],
    }
    digest = hashlib.sha256(
        json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"{subject}-{paper_number}-{digest[:20]}"
