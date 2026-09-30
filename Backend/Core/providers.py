from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from typing import Any
from urllib.parse import urlparse

from Backend.Core.events import emit_progress
from Backend.Core.generation_diagnostics import GenerationEvidenceError
from Backend.Core.mlx_setup import resolve_local_mlx_model
from Backend.Core.model_review import CANONICAL_COGNITIVE_OPERATIONS


class HostedLLMClient:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str,
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = _normalise_base_url(base_url)
        self._apple_model: Any | None = None
        self._apple_tokenizer: Any | None = None
        self._apple_lock = threading.Lock()

    @property
    def supports_parallel_generation(self) -> bool:
        """Whether independent prompts may safely share this client."""

        return self.provider in {"openai", "anthropic"}

    def generate_json(self, prompt: str, retries: int = 2) -> dict[str, object]:
        if not 1 <= retries <= 3:
            raise ValueError("Structured-output attempts must be between 1 and 3.")
        current_prompt = prompt
        last_error: ValueError | None = None
        for attempt in range(retries):
            try:
                if self.provider == "ollama":
                    return self._ollama(current_prompt)
                if self.provider == "openai":
                    return self._openai(current_prompt)
                if self.provider == "anthropic":
                    return self._anthropic(current_prompt)
                if self.provider == "apple":
                    return self._apple(current_prompt)
                raise RuntimeError(f"Unsupported provider: {self.provider}")
            except ValueError as error:
                last_error = error
                if attempt == retries - 1:
                    raise
                emit_progress(
                    "Provider returned invalid structured output; requesting a "
                    "shorter repaired response",
                    stage="provider_retry",
                )
                current_prompt = (
                    prompt + "\n\nREPAIR INSTRUCTION: Your previous response was not a "
                    "complete valid JSON object. Return the same requested object "
                    "again, with concise string fields, no Markdown, no commentary, "
                    "and no omitted closing brackets."
                )
        raise ValueError(
            "Provider could not return valid structured output."
        ) from last_error

    def _ollama(self, prompt: str) -> dict[str, object]:
        schema = _ollama_json_schema(prompt)
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": False,
                "format": schema,
                "options": {
                    "temperature": _ollama_temperature(prompt),
                    "top_p": 0.9,
                    "num_ctx": 16384,
                    "num_predict": _ollama_output_budget(schema),
                    "repeat_last_n": 256,
                    "repeat_penalty": 1.15,
                    "seed": _ollama_seed(prompt),
                },
            }
        ).encode("utf-8")
        request = urllib_request(
            f"{self.base_url}/api/chat",
            payload,
            {"Content-Type": "application/json"},
            attempts=2,
        )
        with request as response:
            raw = _read_json_response(response)
        raw_dict = raw if isinstance(raw, dict) else {}
        diagnostic = {
            "kind": "provider_structure",
            "provider": "ollama",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "stop_reason": raw_dict.get("done_reason"),
            "done": raw_dict.get("done"),
            "output_tokens": raw_dict.get("eval_count"),
        }
        if raw_dict.get("done") is not True or raw_dict.get("done_reason") not in {None, "stop"}:
            raise GenerationEvidenceError(
                "Ollama returned incomplete structured output.", details=diagnostic
            )
        message = raw_dict.get("message")
        response_text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(response_text, str):
            raise GenerationEvidenceError(
                "Ollama returned no generated JSON text.", details=diagnostic
            )
        try:
            return parse_json_object(response_text)
        except ValueError as error:
            reason = str(raw_dict.get("done_reason") or "unknown")
            raise GenerationEvidenceError(
                f"Ollama returned invalid structured output (stop reason: {reason}).",
                details=diagnostic,
            ) from error

    def _apple(self, prompt: str) -> dict[str, object]:
        try:
            from mlx_lm import generate, load
        except ImportError:
            raise RuntimeError(
                "Apple MLX support is not ready. Open Settings, choose Apple "
                "MLX, then run the guided setup and try again."
            ) from None
        # MLX model loading is expensive and can consume several gigabytes. Keep one
        # model per generation client, and serialize use because mlx-lm generation
        # mutates shared inference state.
        with self._apple_lock:
            if self._apple_model is None or self._apple_tokenizer is None:
                local_model = resolve_local_mlx_model(self.model)
                self._apple_model, self._apple_tokenizer = load(local_model)
            response = generate(
                self._apple_model,
                self._apple_tokenizer,
                prompt=prompt,
                max_tokens=4096,
                verbose=False,
            )
        return parse_json_object(response)

    def _openai(self, prompt: str) -> dict[str, object]:
        payload = json.dumps(
            {
                "model": self.model,
                "input": prompt,
                "store": False,
                "text": {"format": {"type": "json_object"}},
            }
        ).encode("utf-8")
        request = urllib_request(
            "https://api.openai.com/v1/responses",
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with request as response:
            raw = _read_json_response(response)
        raw_dict = raw if isinstance(raw, dict) else {}
        text = raw_dict.get("output_text") or _openai_output_text(raw_dict)
        if raw_dict.get("status") != "completed":
            raise GenerationEvidenceError(
                "OpenAI returned incomplete structured output.",
                details={
                    "kind": "provider_structure",
                    "provider": "openai",
                    "status": raw_dict.get("status"),
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                },
            )
        return parse_json_object(str(text))

    def _anthropic(self, prompt: str) -> dict[str, object]:
        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nReturn valid JSON only. Do not wrap it in Markdown.",
                    }
                ],
            }
        ).encode("utf-8")
        request = urllib_request(
            "https://api.anthropic.com/v1/messages",
            payload,
            {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        with request as response:
            raw = _read_json_response(response)
        raw_dict = raw if isinstance(raw, dict) else {}
        if raw_dict.get("stop_reason") not in {"end_turn", "stop_sequence"}:
            raise GenerationEvidenceError(
                "Anthropic returned incomplete structured output.",
                details={
                    "kind": "provider_structure",
                    "provider": "anthropic",
                    "stop_reason": raw_dict.get("stop_reason"),
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                },
            )
        text = "".join(
            item.get("text", "")
            for item in raw_dict.get("content", [])
            if isinstance(item, dict) and item.get("type") == "text"
        )
        return parse_json_object(text)


class OllamaClient(HostedLLMClient):
    """Standalone subject generators use the same transport as the app."""

    def __init__(self, base_url: str, model: str) -> None:
        super().__init__(provider="ollama", model=model, api_key="", base_url=base_url)


def hosted_client(
    *,
    provider: str,
    dry_run: bool,
    model: str,
    api_key: str,
    ollama_url: str = "http://localhost:11434",
) -> HostedLLMClient | None:
    if dry_run:
        return None
    emit_progress(
        f"Using {provider_title(provider)} model {model}",
        stage="provider",
        progress=0.04,
    )
    return HostedLLMClient(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=ollama_url,
    )


def provider_title(provider: str) -> str:
    return {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "ollama": "Ollama",
        "apple": "Apple MLX",
    }.get(provider, provider.title())


def urllib_request(
    url: str,
    data: bytes,
    headers: dict[str, str],
    *,
    attempts: int = 3,
) -> Any:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return urllib.request.urlopen(request, timeout=180)
        except urllib.error.HTTPError as error:
            last_error = error
            detail = error.read(2048).decode("utf-8", errors="ignore")
            retryable = error.code in {408, 409, 429, 500, 502, 503, 504}
            if not retryable or attempt == attempts - 1:
                raise RuntimeError(
                    f"Provider request failed with HTTP {error.code}: "
                    f"{_safe_provider_detail(detail)}"
                ) from error
            retry_after = (
                error.headers.get("Retry-After") if error.headers is not None else None
            )
            delay = _retry_delay(attempt, retry_after)
            emit_progress(
                f"Provider is busy; retrying in {delay:g} seconds",
                stage="provider_retry",
            )
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt == attempts - 1:
                raise RuntimeError(
                    f"Could not reach the provider API after {attempts} attempts."
                ) from error
            delay = _retry_delay(attempt, None)
            emit_progress(
                f"Provider connection interrupted; retrying in {delay:g} seconds",
                stage="provider_retry",
            )
            time.sleep(delay)
    raise RuntimeError("Provider request failed.") from last_error


def parse_json_object(text: str) -> dict[str, object]:
    if len(text.encode("utf-8")) > 1_048_576:
        raise ValueError("Model response exceeded the 1 MB JSON limit.")
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()
    try:
        value = json.loads(raw, object_pairs_hook=_unique_json_fields)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model returned response with no JSON object.") from None
        try:
            value = json.loads(
                raw[start : end + 1], object_pairs_hook=_unique_json_fields
            )
        except json.JSONDecodeError:
            raise ValueError(
                "Model returned response that could not be parsed as JSON."
            ) from None
    if not isinstance(value, dict):
        raise ValueError("Model returned JSON, but not an object.")
    return value


def _unique_json_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"Model returned duplicate JSON field: {key}")
        value[key] = child
    return value


def _ollama_json_schema(prompt: str) -> dict[str, object]:
    """Return a bounded top-level schema while leaving subject fields extensible."""

    short_text = {"type": "string", "maxLength": 240}
    text_list = {
        "type": "array",
        "items": short_text,
        "maxItems": 6,
    }
    object_items = {"type": "object", "additionalProperties": True}
    if prompt.startswith("Independently solve") and '"response_slots": [' in prompt:
        item = json.JSONDecoder().raw_decode(prompt.split("\n", 1)[1])[0]["item"]
        slots = item.get("response_slots") or []
        if slots:
            answers = {
                "type": "object",
                "properties": {
                    slot: {"type": "string", "minLength": 1, "maxLength": 240}
                    for slot in slots
                },
                "required": slots,
                "additionalProperties": False,
            }
            return {
                "type": "object",
                "properties": {
                    "steps": {"type": "array", "items": short_text, "maxItems": 16},
                    "answer": answers,
                    "mark_points": answers,
                    "evidence_ids": text_list,
                    "alternatives": text_list,
                    "partial_credit_boundaries": text_list,
                    "follow_through_rules": text_list,
                },
                "required": [
                    "steps",
                    "answer",
                    "mark_points",
                    "evidence_ids",
                    "alternatives",
                    "partial_credit_boundaries",
                    "follow_through_rules",
                ],
                "additionalProperties": False,
            }
    if prompt.startswith("Independently solve"):
        properties = {
            "steps": {"type": "array", "items": short_text, "maxItems": 16},
            "answer": {"type": "string", "minLength": 1, "maxLength": 2400},
            "mark_points": {"type": "array", "items": short_text, "maxItems": 16},
            "evidence_ids": text_list,
            "alternatives": {**text_list, "maxItems": 8},
            "partial_credit_boundaries": {**text_list, "maxItems": 8},
            "follow_through_rules": {**text_list, "maxItems": 8},
        }
        required = list(properties)
    elif "`questions` array" in prompt or "a `questions` array" in prompt:
        item_count = _prompt_item_count(prompt)
        all_mark_schemes_locked = (
            '"mark_scheme_locked": true' in prompt
            and '"mark_scheme_locked": false' not in prompt
        )
        mark_point = {
            "type": "object",
            "properties": {
                "text": {"type": "string", "maxLength": 400},
                "marks": {"type": "integer", "minimum": 0, "maximum": 100},
                "credit_type": {
                    "type": "string",
                    "enum": ["answer", "point", "level", "guidance"],
                },
                "assessment_objective": {
                    "anyOf": [
                        {
                            "type": "string",
                            "enum": ["AO1", "AO2", "AO3", "AO4"],
                        },
                        {"type": "null"},
                    ]
                },
                "alternatives": text_list,
                "allow": text_list,
                "do_not_accept": text_list,
                "ignore": text_list,
                "depends_on": text_list,
            },
            "required": [
                "text",
                "marks",
                "credit_type",
                "assessment_objective",
            ],
            "additionalProperties": False,
        }
        question = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "maxLength": 64},
                "prompt": {"type": "string", "maxLength": 1200},
                "choices": {
                    "type": "array",
                    "items": short_text,
                    "maxItems": 4,
                },
                "correct_choice": {
                    "anyOf": [
                        {"type": "integer", "minimum": 0, "maximum": 3},
                        {"type": "null"},
                    ]
                },
                "mark_scheme": {
                    "type": "array",
                    "items": mark_point,
                    "maxItems": 0 if all_mark_schemes_locked else 10,
                },
            },
            "required": [
                "id",
                "prompt",
                "choices",
                "correct_choice",
                "mark_scheme",
            ],
            "additionalProperties": False,
        }
        properties = {
            "questions": {
                "type": "array",
                "items": question,
                "minItems": item_count,
                "maxItems": item_count,
            }
        }
        required = ["questions"]
    elif "`reviews` must contain" in prompt:
        item_count = _prompt_item_count(prompt)
        review = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "maxLength": 64},
                "approved": {"type": "boolean"},
                "factual_issues": text_list,
                "marking_issues": text_list,
                "source_issues": text_list,
                "difficulty_issues": text_list,
                "ambiguity_issues": text_list,
            },
            "required": [
                "id",
                "approved",
                "factual_issues",
                "marking_issues",
                "source_issues",
                "difficulty_issues",
                "ambiguity_issues",
            ],
            "additionalProperties": False,
        }
        properties = {
            "reviews": {
                "type": "array",
                "items": review,
                "minItems": item_count,
                "maxItems": item_count,
            }
        }
        required = ["reviews"]
    elif '"estimated_demand":"low|standard|high"' in prompt:
        cognitive_operation = {
            "type": "string",
            "enum": list(CANONICAL_COGNITIVE_OPERATIONS),
        }
        properties = {
            "approved": {"type": "boolean"},
            "estimated_demand": {
                "type": "string",
                "enum": ["low", "standard", "high"],
            },
            "reasoning_steps": {"type": "integer", "minimum": 0, "maximum": 12},
            "tariff_fit": {"type": "boolean"},
            "command_word_fit": {"type": "boolean"},
            "context_fit": {"type": "boolean"},
            "profile_fit": {"type": "boolean"},
            "observed_cognitive_operations": {
                "type": "array",
                "items": cognitive_operation,
                "maxItems": 12,
                "uniqueItems": True,
            },
            "cognitive_operations_fit": {"type": "boolean"},
            "reasoning_range_fit": {"type": "boolean"},
            "shortcut_resistant": {"type": "boolean"},
            "timing_fit": {"type": "boolean"},
            "scaffolding_fit": {"type": "boolean"},
            "estimated_minutes": {
                "type": "number",
                "minimum": 0,
                "maximum": 180,
            },
            "issues": text_list,
        }
        required = [
            "approved",
            "estimated_demand",
            "reasoning_steps",
            "tariff_fit",
            "command_word_fit",
            "context_fit",
            "profile_fit",
            "observed_cognitive_operations",
            "cognitive_operations_fit",
            "reasoning_range_fit",
            "shortcut_resistant",
            "timing_fit",
            "scaffolding_fit",
            "estimated_minutes",
            "issues",
        ]
    elif '"approved":true|false' in prompt:
        properties = {
            "approved": {"type": "boolean"},
            "factual_issues": {"type": "array", "items": {"type": "string"}},
            "marking_issues": {"type": "array", "items": {"type": "string"}},
            "source_issues": {"type": "array", "items": {"type": "string"}},
            "difficulty_issues": {"type": "array", "items": {"type": "string"}},
            "ambiguity_issues": {"type": "array", "items": {"type": "string"}},
        }
        required = [
            "approved",
            "factual_issues",
            "marking_issues",
            "source_issues",
            "difficulty_issues",
            "ambiguity_issues",
        ]
    elif '"question_text": "string"' in prompt:
        if "VERIFIED MARKING IS IMMUTABLE" in prompt:
            part_count = _edexcel_part_count(prompt)
            part = {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "maxLength": 16},
                    "prompt": {"type": "string", "maxLength": 640},
                },
                "required": ["label", "prompt"],
                "additionalProperties": False,
            }
            properties = {
                "question_text": {"type": "string", "maxLength": 900},
                "graph_params": object_items,
                "parts": {
                    "type": "array",
                    "items": part,
                    "minItems": part_count,
                    "maxItems": part_count,
                },
            }
            required = list(properties)
        else:
            option = {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "maxLength": 8},
                    "text": {"type": "string", "maxLength": 240},
                },
                "required": ["label", "text"],
                "additionalProperties": False,
            }
            part = {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "maxLength": 16},
                    "prompt": {"type": "string", "maxLength": 800},
                    "mark_breakdown": {"type": "string", "maxLength": 160},
                    "mark_scheme": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 320},
                        "maxItems": 10,
                    },
                    "indicative_content": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 320},
                        "maxItems": 10,
                    },
                    "options": {"type": "array", "items": option, "maxItems": 4},
                    "correct_option": {"type": "string", "maxLength": 8},
                },
                "required": [
                    "label",
                    "prompt",
                    "mark_breakdown",
                    "mark_scheme",
                    "indicative_content",
                    "options",
                    "correct_option",
                ],
                "additionalProperties": False,
            }
            properties = {
                "question_text": {"type": "string", "maxLength": 1200},
                "source_text": {"type": "string", "maxLength": 2400},
                "source_reference": {"type": "string", "maxLength": 80},
                "mark_breakdown": {"type": "string", "maxLength": 160},
                "indicative_content": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 320},
                    "maxItems": 10,
                },
                "mark_scheme": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 320},
                    "maxItems": 10,
                },
                "graph_params": object_items,
                "parts": {"type": "array", "items": part, "maxItems": 6},
            }
            required = list(properties)
    elif '"stem": "string"' in prompt and '"parts": [' in prompt:
        compact = "VERIFIED MARKING IS IMMUTABLE" in prompt
        part_properties = {
            "label": {"type": "string", "maxLength": 16},
            "prompt": {"type": "string", "maxLength": 800},
        }
        if not compact:
            part_properties.update(
                {
                    "marking_points": {
                        "type": "array",
                        "items": {"type": "string", "maxLength": 320},
                        "maxItems": 8,
                    },
                    "accept": text_list,
                    "reject": text_list,
                }
            )
        part = {
            "type": "object",
            "properties": part_properties,
            "required": list(part_properties),
            "additionalProperties": False,
        }
        part_count = (
            0
            if "Do not repeat, rewrite or answer the parts" in prompt
            else (_aqa_cs_part_count(prompt) if compact else 8)
        )
        properties = {
            "stem": {"type": "string", "maxLength": 1000},
            "parts": {
                "type": "array",
                "items": part,
                "minItems": part_count if compact else 0,
                "maxItems": part_count,
            },
        }
        required = ["stem", "parts"]
    else:
        properties = {}
        required = []
    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": not bool(required),
    }
    if required:
        schema["required"] = required
    return schema


def _prompt_item_count(prompt: str) -> int:
    """Derive the exact batch cardinality already declared in prompt data.

    Ollama's grammar follows the supplied schema literally. Leaving a broad
    one-to-six range let otherwise capable local models stop after the first
    object in a multi-item batch, wasting several minutes on retries. The
    blueprint identifiers are generated by this process and occur once per
    requested item, so they are a safe, inexpensive cardinality signal.
    """

    count = len(set(re.findall(r'"id"\s*:\s*"\d+/\d+/\d+"', prompt)))
    return min(6, max(1, count))


def _edexcel_part_count(prompt: str) -> int:
    parts_line = re.search(r"^Parts:\s*(.+)$", prompt, flags=re.MULTILINE)
    if parts_line is None or parts_line.group(1).strip().casefold() == "none":
        return 0
    return min(
        6,
        len(re.findall(r"\([a-z]\)\s+\d+\s+marks?\b", parts_line.group(1), re.I)),
    )


def _aqa_cs_part_count(prompt: str) -> int:
    return min(8, len(re.findall(r"^- Part\s+[^:]+:", prompt, re.MULTILINE)))


def _ollama_output_budget(schema: dict[str, object]) -> int:
    required = set(schema.get("required", []))
    if "questions" in required:
        count = _schema_array_count(schema, "questions")
        properties = schema.get("properties")
        questions = (
            properties.get("questions") if isinstance(properties, dict) else None
        )
        items = questions.get("items") if isinstance(questions, dict) else None
        item_properties = items.get("properties") if isinstance(items, dict) else None
        mark_scheme = (
            item_properties.get("mark_scheme")
            if isinstance(item_properties, dict)
            else None
        )
        if isinstance(mark_scheme, dict) and mark_scheme.get("maxItems") == 0:
            return min(1024, 256 + 256 * count)
        return min(4096, 1536 + 768 * count)
    if "reviews" in required:
        count = _schema_array_count(schema, "reviews")
        return min(2048, 512 + 256 * count)
    if "question_text" in required:
        if "mark_scheme" not in required and "source_text" not in required:
            return 384
        return 1536
    if "parts" in required:
        properties = schema.get("properties")
        parts = properties.get("parts") if isinstance(properties, dict) else None
        if isinstance(parts, dict) and parts.get("maxItems") == 0:
            return 256
        if isinstance(parts, dict):
            items = parts.get("items")
            item_properties = (
                items.get("properties") if isinstance(items, dict) else None
            )
            if (
                isinstance(item_properties, dict)
                and "marking_points" not in item_properties
            ):
                return 384
        return 1024
    if "approved" in required:
        return 640
    return 1536


def _schema_array_count(schema: dict[str, object], name: str) -> int:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return 1
    value = properties.get(name)
    if not isinstance(value, dict):
        return 1
    count = value.get("maxItems", 1)
    return count if isinstance(count, int) and count > 0 else 1


def _ollama_temperature(prompt: str) -> float:
    if (
        "Act as an independent UK A-level assessment editor" in prompt
        or "Act as a second-pass UK A-level assessment editor" in prompt
        or "REPAIR INSTRUCTION" in prompt
    ):
        return 0
    attempt = re.search(r"\bAttempt:\s*(\d+)", prompt)
    return min(0.4, 0.15 + 0.1 * int(attempt.group(1))) if attempt else 0.2


def _ollama_seed(prompt: str) -> int:
    generation = re.search(r"\bGeneration seed:\s*(\d+)", prompt)
    attempt = re.search(r"\bAttempt:\s*(\d+)", prompt)
    if generation:
        return (
            int(generation.group(1))
            + 104_729 * int(attempt.group(1) if attempt else "1")
        ) % 2_147_483_647
    return 0


def _read_json_response(response: Any) -> object:
    payload = response.read(2_097_153)
    if len(payload) > 2_097_152:
        raise RuntimeError("Provider response exceeded the 2 MB limit.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "Provider returned an invalid JSON response envelope."
        ) from error


def _retry_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            return min(10.0, max(0.0, float(retry_after)))
        except ValueError:
            pass
    return min(8.0, float(2**attempt))


def _safe_provider_detail(value: str) -> str:
    compact = " ".join(value.split())
    compact = re.sub(
        r"(?i)\bauthorization\s*[:=]\s*(?:bearer\s+)?\S+",
        "Authorization [redacted]",
        compact,
    )
    compact = re.sub(
        r"(?i)\bbearer\s+\S+",
        "Bearer [redacted]",
        compact,
    )
    compact = re.sub(
        r"(?i)(api[_ -]?key)\s*[:=]\s*\S+",
        r"\1 [redacted]",
        compact,
    )
    return compact[:500] or "No error detail was returned."


def _openai_output_text(raw: dict[str, object]) -> str:
    chunks: list[str] = []
    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                chunks.append(str(content.get("text", "")))
    return "".join(chunks)


def _normalise_base_url(value: str) -> str:
    raw = value.strip().rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Provider base URL must be an http or https URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            "Provider base URL must not contain credentials, a query, or a fragment."
        )
    return raw
