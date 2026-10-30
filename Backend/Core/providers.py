# Adapt model providers to the shared JSON response and validation interface.

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
import time
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse

from Backend.Core.events import emit, emit_progress
from Backend.Core.generation_diagnostics import (
    GenerationEvidenceError,
    ProviderOutputContractError,
)
from Backend.Core.generation_requests import GenerationRequest, OutputContract
from Backend.Core.mlx_batching import (
    BatchUnavailable,
    CoalescingRunner,
    generate_batch,
)
from Backend.Core.mlx_batching import (
    output_budget as mlx_output_budget,
)
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
        self.usage_records: list[dict[str, object]] = []
        self.base_url = _normalise_base_url(base_url)
        self.parallel_review_workers = (
            2
            if provider == "ollama"
            and os.environ.get("KELDIN_PARALLEL_LOCAL_REVIEWS") == "1"
            else 1
        )
        self.parallel_generation_workers = (
            self.parallel_review_workers
            if provider == "ollama"
            else 2
            if provider == "apple"
            and os.environ.get("KELDIN_PARALLEL_MLX_GENERATION") == "1"
            else 1
        )
        self._apple_model: Any | None = None
        self._apple_tokenizer: Any | None = None
        self._apple_structured_model: Any | None = None
        self._apple_lock = threading.Lock()
        self._apple_batcher_lock = threading.Lock()
        self._apple_batcher: (
            CoalescingRunner[tuple[str, dict] | tuple[str, dict, int], str] | None
        ) = None

    # Whether independent prompts may safely share this client.
    @property
    def supports_parallel_generation(self) -> bool:

        return self.provider in {"openai", "anthropic"}

    def generate_json(self, prompt: str, retries: int = 2) -> dict[str, object]:
        return self._generate_json(prompt, retries=retries)

    def generate_request(
        self, request: GenerationRequest, retries: int = 2
    ) -> dict[str, object]:
        if not isinstance(request, GenerationRequest):
            raise TypeError("structured generation requires a GenerationRequest")
        # Preserve legacy overrides and test doubles instead of bypassing their
        # generate_json implementation through an inherited structured method.
        if (
            getattr(self.generate_json, "__func__", None)
            is not _HOSTED_LEGACY_GENERATE_JSON
        ):
            return self.generate_json(request.prompt)
        return self._generate_json(request.prompt, retries=retries, request=request)

    def _generate_json(
        self, prompt: str, *, retries: int, request: GenerationRequest | None = None
    ) -> dict[str, object]:
        if not 1 <= retries <= 3:
            raise ValueError("Structured-output attempts must be between 1 and 3.")
        if self.provider == "deepseek" or (
            request is not None and request.operation == "french_nsi_authoring"
        ):
            # The French pipeline owns its one recorded structural regeneration.
            retries = 1
        current_prompt = prompt
        last_error: ValueError | None = None
        for attempt in range(retries):
            try:
                if self.provider == "deepseek":
                    if request is None:
                        raise ValueError(
                            "DeepSeek requires a typed JSON generation request."
                        )
                    return self._deepseek(request)
                if self.provider == "ollama":
                    if request is not None:
                        return self._ollama(
                            current_prompt,
                            schema=request.schema,
                            output_budget=request.output_budget,
                            seed=request.seed,
                            temperature=0 if attempt else request.temperature,
                            **(
                                {"french_nsi": True}
                                if request.operation == "french_nsi_authoring"
                                else {}
                            ),
                        )
                    return self._ollama(current_prompt)
                if self.provider == "openai":
                    if request is not None:
                        return self._openai(
                            current_prompt,
                            output_budget=request.output_budget,
                            **(
                                {"single_attempt": True}
                                if request.operation == "french_nsi_authoring"
                                else {}
                            ),
                        )
                    return self._openai(current_prompt)
                if self.provider == "anthropic":
                    if request is not None:
                        return self._anthropic(
                            current_prompt,
                            output_budget=request.output_budget,
                            **(
                                {"single_attempt": True}
                                if request.operation == "french_nsi_authoring"
                                else {}
                            ),
                        )
                    return self._anthropic(current_prompt)
                if self.provider == "apple":
                    if request is not None:
                        return self._apple(
                            current_prompt,
                            schema=request.schema,
                            identifiers=request.expected_ids,
                            output_budget=request.output_budget,
                        )
                    return self._apple(current_prompt)
                raise RuntimeError(f"Unsupported provider: {self.provider}")
            except ValueError as error:
                if (
                    isinstance(error, GenerationEvidenceError)
                    and error.details.get("kind") == "context_capacity"
                ):
                    raise
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
                if (
                    isinstance(error, GenerationEvidenceError)
                    and error.details.get("kind") == "provider_batch_contract"
                ):
                    current_prompt = prompt + (
                        "\n\nREPAIR INSTRUCTION: The question identifiers or count did not match "
                        "the requested batch. Return exactly one item for every supplied id, "
                        "copying each id unchanged. Do not invent or repeat questions."
                    )
        raise ValueError(
            "Provider could not return valid structured output."
        ) from last_error

    def _ollama(
        self,
        prompt: str,
        *,
        schema: dict | None = None,
        output_budget: int | None = None,
        seed: int | None = None,
        request_function: Any | None = None,
        strict_json: bool = False,
        temperature: float | None = None,
        french_nsi: bool = False,
    ) -> dict[str, object]:
        schema = _ollama_json_schema(prompt) if schema is None else schema
        budget = (
            _ollama_output_budget(schema) if output_budget is None else output_budget
        )
        if french_nsi and (type(budget) is not int or not 1 <= budget <= 16384):
            raise ValueError("French NSI output budget must be from 1 to 16384.")
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "think": None if french_nsi else False,
                "format": schema,
                **({"truncate": False, "shift": False} if french_nsi else {}),
                "options": {
                    "temperature": _ollama_temperature(prompt)
                    if temperature is None
                    else temperature,
                    "top_p": 0.9,
                    "num_ctx": 16384,
                    "num_predict": budget,
                    "repeat_last_n": 256,
                    "repeat_penalty": 1.0 if french_nsi else 1.15,
                    "seed": _ollama_seed(prompt) if seed is None else seed,
                },
            }
        ).encode("utf-8")
        try:
            request = (request_function or urllib_request)(
                f"{self.base_url}/api/chat",
                payload,
                {"Content-Type": "application/json"},
                **(
                    {"attempts": 1, "timeout_seconds": 600}
                    if french_nsi
                    else {"attempts": 2}
                ),
            )
            with request as response:
                raw = _read_json_response(response)
        except RuntimeError as error:
            from urllib.error import HTTPError

            cause = error.__cause__
            if (
                french_nsi
                and isinstance(cause, HTTPError)
                and cause.code in {400, 413}
                and any(
                    message in str(error).lower()
                    for message in (
                        "prompt is longer than the context length",
                        "input length exceeds the context length",
                        "exceeds the available context",
                    )
                )
            ):
                raise GenerationEvidenceError(
                    "Le contexte du modèle ne peut pas contenir cet exercice sans omission.",
                    details={
                        "kind": "context_capacity",
                        "provider": "ollama",
                        "http_status": cause.code,
                        "context_window": 16384,
                        "output_budget": budget,
                        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    },
                ) from error
            raise
        raw_dict = raw if isinstance(raw, dict) else {}
        diagnostic = {
            "kind": "provider_structure",
            "provider": "ollama",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "stop_reason": raw_dict.get("done_reason"),
            "done": raw_dict.get("done"),
            "output_tokens": raw_dict.get("eval_count"),
        }
        message = raw_dict.get("message")
        response_text = message.get("content") if isinstance(message, dict) else None
        if isinstance(response_text, str):
            diagnostic["raw_response"] = response_text
            diagnostic["raw_response_sha256"] = hashlib.sha256(
                response_text.encode("utf-8")
            ).hexdigest()
        if french_nsi:
            input_count, output_count = (
                raw_dict.get("prompt_eval_count"),
                raw_dict.get("eval_count"),
            )
            diagnostic.update(
                input_tokens=input_count,
                output_budget=budget,
                context_window=16384,
                truncate=False,
                shift=False,
            )
            if (
                type(input_count) is not int
                or input_count < 1
                or type(output_count) is not int
                or output_count < 0
                or input_count + budget > 16384
                or input_count + output_count > 16384
                or output_count > budget
            ):
                diagnostic["kind"] = "context_capacity"
                raise GenerationEvidenceError(
                    "Capacité du contexte non vérifiée ou insuffisante pour cet exercice. Aucun brouillon accepté.",
                    details=diagnostic,
                )
            emit_progress(
                f"Contexte du modèle : {input_count} jetons d'entrée, {output_count} de sortie, limite 16384.",
                stage="provider_context",
            )
        if raw_dict.get("done") is not True or raw_dict.get("done_reason") not in {
            None,
            "stop",
        }:
            raise GenerationEvidenceError(
                "Ollama returned incomplete structured output.", details=diagnostic
            )
        if not isinstance(response_text, str):
            raise GenerationEvidenceError(
                "Ollama returned no generated JSON text.", details=diagnostic
            )
        try:
            if strict_json or french_nsi:
                if len(response_text.encode("utf-8")) > 1_048_576:
                    raise ValueError("Model response exceeded the 1 MB JSON limit.")
                parsed = json.loads(
                    response_text, object_pairs_hook=_unique_json_fields
                )
                if not isinstance(parsed, dict):
                    raise ValueError("Model returned JSON, but not an object.")
                return parsed
            return parse_json_object(response_text)
        except ValueError as error:
            reason = str(raw_dict.get("done_reason") or "unknown")
            raise GenerationEvidenceError(
                f"Ollama returned invalid structured output (stop reason: {reason}).",
                details=diagnostic,
            ) from error

    def _apple(
        self,
        prompt: str,
        *,
        schema: dict | None = None,
        identifiers: tuple[str, ...] | None = None,
        output_budget: int | None = None,
    ) -> dict[str, object]:
        mlx_output_budget(output_budget)
        source_prompt = prompt
        schema = _ollama_json_schema(prompt) if schema is None else schema
        if schema.get("required"):
            # Keep the format visible to the model as well as the token decoder.
            prompt += "\n\nReturn JSON only, following OUTPUT_SCHEMA=" + json.dumps(
                schema, separators=(",", ":")
            )
        if self.parallel_generation_workers == 2:
            # Only the owner thread loads or uses the shared MLX model/tokenizer.
            with self._apple_batcher_lock:
                if self._apple_batcher is None:
                    self._apple_batcher = CoalescingRunner(self._run_apple_batch)
            job = (
                (prompt, schema)
                if output_budget is None
                else (prompt, schema, output_budget)
            )
            response = self._apple_batcher.call(job)
        else:
            response = (
                self._apple_response(prompt, schema)
                if output_budget is None
                else self._apple_response(prompt, schema, output_budget)
            )
        if schema.get("required"):
            # Never salvage a truncated constrained response or duplicate fields.
            if len(response.encode("utf-8")) > 1_048_576:
                raise ValueError("Model response exceeded the 1 MB JSON limit.")
            parsed = json.loads(response, object_pairs_hook=_unique_json_fields)
            if not isinstance(parsed, dict):
                raise ValueError("Model returned JSON, but not an object.")
        else:
            parsed = parse_json_object(response)
        identifiers = (
            _prompt_item_identifiers(source_prompt)
            if identifiers is None
            else identifiers
        )
        for field in ("questions", "reviews"):
            if identifiers and field in schema.get("required", []):
                items = parsed.get(field)
                actual = (
                    [
                        item.get("id") if isinstance(item, dict) else None
                        for item in items
                    ]
                    if isinstance(items, list)
                    else []
                )
                if (
                    len(actual) != len(identifiers)
                    or not all(isinstance(identifier, str) for identifier in actual)
                    or set(actual) != set(identifiers)
                ):
                    raise GenerationEvidenceError(
                        "MLX question identifiers or count did not match the requested batch.",
                        details={
                            "kind": "provider_batch_contract",
                            "provider": "apple",
                        },
                    )
        if self.parallel_generation_workers == 2 and schema.get("required"):
            from jsonschema import Draft202012Validator, ValidationError

            try:
                Draft202012Validator(schema).validate(parsed)
            except ValidationError as error:
                raise ValueError(
                    "MLX response did not match the required output schema."
                ) from error
        return parsed

    def _load_apple_model(self) -> None:
        try:
            from mlx_lm import load
        except ImportError:
            raise RuntimeError(
                "Apple MLX support is not ready. Open Settings, choose Apple "
                "MLX, then run the guided setup and try again."
            ) from None
        if self._apple_model is None or self._apple_tokenizer is None:
            self._apple_model, self._apple_tokenizer = load(
                resolve_local_mlx_model(self.model),
                tokenizer_config={"trust_remote_code": False, "local_files_only": True},
            )

    def _apple_response(
        self, prompt: str, schema: dict, output_budget: int | None = None
    ) -> str:
        budget = mlx_output_budget(output_budget)
        with self._apple_lock:
            self._load_apple_model()
            if schema.get("required"):
                return (
                    self._mlx_structured_response(prompt, schema)
                    if output_budget is None
                    else self._mlx_structured_response(prompt, schema, budget)
                )
            from mlx_lm import generate

            return generate(
                self._apple_model,
                self._apple_tokenizer,
                prompt=_mlx_json_prompt(self._apple_tokenizer, prompt),
                max_tokens=budget,
                verbose=False,
            )

    def _run_apple_batch(
        self,
        requests: list[tuple[str, dict] | tuple[str, dict, int]],
        cancelled: threading.Event,
    ) -> list[str | BaseException]:
        if len(requests) == 2 and all(
            request[1].get("required") for request in requests
        ):
            with self._apple_lock:
                self._load_apple_model()
                try:
                    return self._mlx_batch_structured_responses(requests, cancelled)
                except BatchUnavailable:
                    emit_progress(
                        "Apple MLX is using serial decoding for this model or prompt pair.",
                        stage="provider_serial_fallback",
                    )
        results: list[str | BaseException] = []
        for request in requests:
            if cancelled.is_set():
                from concurrent.futures import CancelledError

                results.append(CancelledError("MLX generation was cancelled."))
                continue
            try:
                results.append(self._apple_response(*request))
            except Exception as error:
                results.append(error)
        return results

    def _mlx_batch_structured_responses(
        self,
        requests: list[tuple[str, dict] | tuple[str, dict, int]],
        cancelled: threading.Event,
    ) -> list[str | BaseException]:
        try:
            import llguidance
            import outlines
            from outlines.backends.llguidance import LLGuidanceBackend
        except ImportError:
            raise RuntimeError(
                "Apple MLX structured output is not ready. Open Settings and run "
                "the guided setup, or update the app, then try again."
            ) from None
        if self._apple_structured_model is None:
            self._apple_structured_model = outlines.from_mlxlm(
                self._apple_model, self._apple_tokenizer
            )
            self._apple_structured_model.type_adapter.has_chat_template = False
        backend = LLGuidanceBackend(self._apple_structured_model)
        processors = []
        prompts = []
        for request in requests:
            prompt, schema = request[:2]
            decoder_schema = json.dumps(_mlx_decoder_schema(schema))
            grammar_error = llguidance.LLMatcher.validate_grammar(
                llguidance.grammar_from("json_schema", decoder_schema)
            )
            if grammar_error:
                # Retry individually so one invalid grammar cannot poison its
                # neighbour. The serial path applies the same strict decoder.
                raise BatchUnavailable("A request grammar needs individual validation.")
            processors.append(backend.get_json_schema_logits_processor(decoder_schema))
            prompts.append(_mlx_json_prompt(self._apple_tokenizer, prompt))
        options = {}
        if any(len(request) == 3 for request in requests):
            options["output_budgets"] = [
                mlx_output_budget(request[2] if len(request) == 3 else None)
                for request in requests
            ]
        return generate_batch(
            self._apple_model,
            self._apple_tokenizer,
            prompts,
            processors,
            cancelled,
            **options,
        )

    # Constrain syntax, public option values and batch IDs; validate correctness separately.
    def _mlx_structured_response(
        self, prompt: str, schema: dict, output_budget: int | None = None
    ) -> str:
        budget = mlx_output_budget(output_budget)

        try:
            import llguidance
            import outlines
            from jsonschema import Draft202012Validator, ValidationError
            from outlines.types import JsonSchema
        except ImportError:
            raise RuntimeError(
                "Apple MLX structured output is not ready. Open Settings and run "
                "the guided setup, or update the app, then try again."
            ) from None
        if self._apple_structured_model is None:
            self._apple_structured_model = outlines.from_mlxlm(
                self._apple_model, self._apple_tokenizer
            )
            # Outlines 1.3.3 otherwise applies the default thinking template.
            # Own formatting here so JSON starts in the model's answer channel,
            # with exactly one chat template and no mutation of its tokenizer.
            self._apple_structured_model.type_adapter.has_chat_template = False
        # A fresh decoder per call avoids carrying accepted tokens into repairs.
        # llguidance avoids the large finite-state compilation cost of bounded
        # strings/arrays in the default Outlines backend (see retained timings).
        decoder_schema = _mlx_decoder_schema(schema)
        grammar = llguidance.grammar_from("json_schema", json.dumps(decoder_schema))
        grammar_error = llguidance.LLMatcher.validate_grammar(grammar)
        if grammar_error:
            raise ValueError(
                f"MLX cannot constrain this response format: {grammar_error}"
            )
        response = self._apple_structured_model(
            _mlx_json_prompt(self._apple_tokenizer, prompt),
            JsonSchema(decoder_schema),
            backend="llguidance",
            max_tokens=budget,
            verbose=False,
        )
        if len(response.encode("utf-8")) > 1_048_576:
            raise ValueError("Model response exceeded the 1 MB JSON limit.")
        parsed = json.loads(response, object_pairs_hook=_unique_json_fields)
        try:
            Draft202012Validator(schema).validate(parsed)
        except ValidationError as error:
            raise ValueError(
                "MLX response did not match the required output schema."
            ) from error
        return response

    def _deepseek(self, request: GenerationRequest) -> dict[str, object]:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import ValidationError

        if self.model not in {"deepseek-flash", "deepseek-v4-pro"}:
            raise ValueError("Choose deepseek-flash or deepseek-v4-pro for DeepSeek.")
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise ValueError("Enter a DeepSeek API key before generating a draft.")
        key = self.api_key.strip()
        budget = _hosted_output_budget(
            request.output_budget,
            maximum=32768 if request.operation == "french_nsi_authoring" else 16384,
        )
        schema = request.schema
        _require_local_schema_references(schema)
        Draft202012Validator.check_schema(schema)
        payload = json.dumps(
            {
                "model": self.model,
                "input": request.prompt,
                "instructions": (
                    "Return exactly one valid JSON object matching OUTPUT_SCHEMA. "
                    "Do not use an outer Markdown code fence, JSON comments, or trailing commas. "
                    "Requested code fences and markup inside JSON string values are allowed; "
                    "escape quotes, backslashes and line breaks as required by JSON. "
                    "Preserve the language and content requirements of the user request. "
                    "\nOUTPUT_SCHEMA=\n"
                    + json.dumps(schema, ensure_ascii=False, allow_nan=False)
                ),
                "stream": False,
                # Reasoning and final JSON share the bounded output allowance.
                "reasoning": {
                    "effort": "low"
                    if request.operation == "french_nsi_authoring"
                    else "high"
                },
                "max_output_tokens": budget,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "keldin_generation",
                        "schema": schema,
                    }
                },
            }
        ).encode("utf-8")
        with urllib_request(
            "https://api.deepseek.com/responses",
            payload,
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            attempts=1,
            timeout_seconds=600,
            fixed_host="api.deepseek.com",
            secrets=(key,),
        ) as response:
            raw = _read_json_response(response)
        if not isinstance(raw, dict):
            raise GenerationEvidenceError(
                "DeepSeek returned no structured response.",
                details={"kind": "provider_structure", "provider": "deepseek"},
            )
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        inputs, outputs = usage.get("input_tokens"), usage.get("output_tokens")
        cached = usage.get("input_tokens_details", {})
        cached = cached.get("cached_tokens", 0) if isinstance(cached, dict) else 0
        reasoning = usage.get("output_tokens_details", {})
        reasoning = (
            reasoning.get("reasoning_tokens") if isinstance(reasoning, dict) else None
        )
        record = {
            "provider": "deepseek",
            "model": self.model,
            "response_id": str(raw.get("id", "")).replace(key, "[redacted]")[:200],
            "input_tokens": inputs if type(inputs) is int else None,
            "output_tokens": outputs if type(outputs) is int else None,
            "cached_tokens": cached if type(cached) is int else None,
            "reasoning_tokens": reasoning if type(reasoning) is int else None,
            "output_budget": budget,
            "returned_model": str(raw.get("model", "")).replace(key, "[redacted]")[
                :200
            ],
            "identity_matches": raw.get("model") == self.model,
        }
        self.usage_records.append(record)
        emit(
            "progress",
            stage="provider_usage",
            message="Réponse DeepSeek reçue; vérification en cours.",
            usage=record,
        )
        diagnostic = {
            "provider": "deepseek",
            "usage": record,
            "prompt_sha256": hashlib.sha256(request.prompt.encode()).hexdigest(),
        }
        if (
            raw.get("status") != "completed"
            or raw.get("error")
            or raw.get("incomplete_details")
        ):
            raise GenerationEvidenceError(
                "DeepSeek returned incomplete structured output.",
                details={**diagnostic, "kind": "provider_structure"},
            )
        if raw.get("model") != self.model:
            raise GenerationEvidenceError(
                "DeepSeek returned an unexpected model identity.",
                details={**diagnostic, "kind": "provider_identity"},
            )
        if (
            type(inputs) is not int
            or inputs < 1
            or type(outputs) is not int
            or not 1 <= outputs <= budget
            or type(cached) is not int
            or not 0 <= cached <= inputs
            or (
                reasoning is not None
                and (type(reasoning) is not int or not 0 <= reasoning <= outputs)
            )
        ):
            raise GenerationEvidenceError(
                "DeepSeek returned unverified token usage.",
                details={**diagnostic, "kind": "provider_usage"},
            )
        try:
            output = raw.get("output")
            if not isinstance(output, list) or any(
                not isinstance(item, dict)
                or item.get("type") not in {"message", "reasoning"}
                for item in output
            ):
                raise ValueError("Unexpected response items")
            messages = [item for item in output if item.get("type") == "message"]
            if (
                len(messages) != 1
                or messages[0].get("role") != "assistant"
                or messages[0].get("status") not in {None, "completed"}
            ):
                raise ValueError("Missing complete assistant response")
            parts = messages[0].get("content")
            if (
                not isinstance(parts, list)
                or not parts
                or any(
                    not isinstance(part, dict)
                    or part.get("type") != "output_text"
                    or not isinstance(part.get("text"), str)
                    for part in parts
                )
            ):
                raise ValueError("Missing output text")
            text = "".join(part["text"] for part in parts)
            if len(text.encode()) > 1_048_576:
                raise ValueError("Response too large")
        except ValueError as error:
            raise GenerationEvidenceError(
                "DeepSeek returned invalid structured output.",
                details={**diagnostic, "kind": "provider_structure"},
            ) from error
        try:
            candidate = json.loads(
                text,
                object_pairs_hook=_unique_json_fields,
                parse_constant=_reject_json_constant,
                parse_float=_finite_json_float,
            )
            if not isinstance(candidate, dict):
                raise ValueError("Response is not a JSON object")
            Draft202012Validator(schema).validate(candidate)
        except (ValueError, ValidationError) as error:
            if isinstance(error, ValidationError):
                failure = "schema_mismatch"
                path = [
                    part
                    if type(part) is int
                    else str(part).replace(key, "[redacted]")[:80]
                    for part in list(error.absolute_schema_path)[:24]
                ]
            else:
                failure, path = "invalid_json", []
            # No candidate text, values or verbose validator message enters the
            # typed error. Suppress its original parsing/validation traceback.
            raise ProviderOutputContractError(
                failure=failure,
                response_sha256=hashlib.sha256(text.encode()).hexdigest(),
                schema_path=path,
                diagnostic=diagnostic,
            ) from None
        return candidate

    def _openai(
        self,
        prompt: str,
        *,
        output_budget: int | None = None,
        single_attempt: bool = False,
    ) -> dict[str, object]:
        values = {
            "model": self.model,
            "input": prompt,
            "store": False,
            "text": {"format": {"type": "json_object"}},
        }
        if output_budget is not None:
            values["max_output_tokens"] = _hosted_output_budget(
                output_budget, minimum=16
            )
        payload = json.dumps(values).encode("utf-8")
        request = urllib_request(
            "https://api.openai.com/v1/responses",
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            fixed_host="api.openai.com",
            secrets=(self.api_key,),
            **({"attempts": 1, "timeout_seconds": 600} if single_attempt else {}),
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

    def _anthropic(
        self,
        prompt: str,
        *,
        output_budget: int | None = None,
        single_attempt: bool = False,
    ) -> dict[str, object]:
        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": 4096
                if output_budget is None
                else _hosted_output_budget(output_budget),
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
            fixed_host="api.anthropic.com",
            secrets=(self.api_key,),
            **({"attempts": 1, "timeout_seconds": 600} if single_attempt else {}),
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


_HOSTED_LEGACY_GENERATE_JSON = HostedLLMClient.generate_json


# Standalone subject generators use the same transport as the app.
class OllamaClient(HostedLLMClient):
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
    timeout_seconds: int = 180,
    fixed_host: str | None = None,
    secrets: tuple[str, ...] = (),
) -> Any:
    import urllib.error
    import urllib.request

    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 600:
        raise ValueError("Provider timeout must be an integer from 1 to 600 seconds.")
    open_request = urllib.request.urlopen
    if fixed_host is not None:
        target = urlparse(url)
        if (
            target.scheme != "https"
            or target.hostname != fixed_host
            or target.port not in (None, 443)
            or target.username
            or target.password
            or target.query
            or target.fragment
        ):
            raise ValueError("Provider destination must match its fixed HTTPS host.")

        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        open_request = urllib.request.build_opener(NoRedirect()).open
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return open_request(request, timeout=timeout_seconds)
        except urllib.error.HTTPError as error:
            last_error = error
            detail = error.read(2048).decode("utf-8", errors="ignore")
            for secret in secrets:
                if secret:
                    detail = detail.replace(secret, "[redacted]")
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


def _hosted_output_budget(value: int, *, minimum: int = 1, maximum: int = 16384) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(
            f"Hosted output budget must be an integer from {minimum} to {maximum}."
        )
    return value


def _require_local_schema_references(value: object) -> None:
    if isinstance(value, dict):
        for name, child in value.items():
            if name in {"$ref", "$dynamicRef"} and (
                not isinstance(child, str) or not child.startswith("#")
            ):
                raise ValueError("DeepSeek schema references must remain local.")
            _require_local_schema_references(child)
    elif isinstance(value, list):
        for child in value:
            _require_local_schema_references(child)


def _reject_json_constant(_value: str) -> None:
    raise ValueError("Non-finite constants are not JSON values.")


def _finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("JSON number exceeds the finite float range.")
    return parsed


def _unique_json_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError(f"Model returned duplicate JSON field: {key}")
        value[key] = child
    return value


# Keep hybrid-model reasoning tags outside the JSON-only response channel.
def _mlx_json_prompt(tokenizer: Any, prompt: str) -> str:

    if not getattr(tokenizer, "has_chat_template", False):
        return prompt
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


# Defer only array uniqueness to validation; reject other unsupported rules.
def _mlx_decoder_schema(schema: dict) -> dict:

    result = {key: value for key, value in schema.items() if key != "uniqueItems"}
    if isinstance(schema.get("properties"), dict):
        result["properties"] = {
            name: _mlx_decoder_schema(value)
            for name, value in schema["properties"].items()
        }
    for key in ("items", "additionalProperties"):
        if isinstance(schema.get(key), dict):
            result[key] = _mlx_decoder_schema(schema[key])
    for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
        if isinstance(schema.get(key), list):
            result[key] = [_mlx_decoder_schema(value) for value in schema[key]]
    return result


# Return a bounded top-level schema while leaving subject fields extensible.
def _legacy_schema_operation(prompt: str) -> str:
    if prompt.startswith("Independently solve"):
        return "solver"
    if "`questions` array" in prompt or "a `questions` array" in prompt:
        return "authoring"
    if "`reviews` must contain" in prompt:
        return "batch_review"
    if '"estimated_demand":"low|standard|high"' in prompt:
        return "difficulty"
    if '"approved":true|false' in prompt:
        return "review"
    if '"question_text": "string"' in prompt:
        return "edexcel"
    if '"stem": "string"' in prompt and '"parts": [' in prompt:
        return "aqa_cs"
    return ""


def _ollama_json_schema(
    prompt: str, *, contract: OutputContract | None = None
) -> dict[str, object]:

    operation = (
        contract.operation if contract is not None else _legacy_schema_operation(prompt)
    )
    short_text = {"type": "string", "maxLength": 240}
    text_list = {
        "type": "array",
        "items": short_text,
        "maxItems": 6,
    }
    object_items = {"type": "object", "additionalProperties": True}
    solver_item = contract.solver_item if contract is not None else {}
    if contract is None and prompt.startswith("Independently solve") and "\n" in prompt:
        try:
            payload = json.JSONDecoder().raw_decode(prompt.split("\n", 1)[1])[0]
            candidate = payload.get("item") if isinstance(payload, dict) else None
            if isinstance(candidate, dict):
                solver_item = candidate
        except ValueError:
            pass
    if solver_item:
        item = solver_item
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
    if operation == "solver":
        properties = {
            "steps": {"type": "array", "items": short_text, "maxItems": 16},
            "answer": {"type": "string", "minLength": 1, "maxLength": 2400},
            "mark_points": {"type": "array", "items": short_text, "maxItems": 16},
            "evidence_ids": text_list,
            "alternatives": {**text_list, "maxItems": 8},
            "partial_credit_boundaries": {**text_list, "maxItems": 8},
            "follow_through_rules": {**text_list, "maxItems": 8},
        }
        choices = solver_item.get("choices")
        if (
            solver_item.get("kind") == "multiple_choice"
            and not solver_item.get("response_slots")
            and isinstance(choices, list)
            and choices
            and all(isinstance(choice, str) and choice.strip() for choice in choices)
        ):
            # Constrain the format to public options, never to the private key.
            # Reconciliation still rejects a wrong answer or contradictory point.
            properties["has_single_valid_choice"] = {"type": "boolean"}
            option = {"type": "string", "enum": choices}
            properties["answer"] = option
            properties["mark_points"] = {
                "type": "array",
                "items": option,
                "minItems": 1,
                "maxItems": 1,
            }
            if solver_item.get("marks") == 1:
                # One selected option earns the single mark. Other options are
                # distractors, not alternative correct answers to invent.
                properties["alternatives"] = {**text_list, "maxItems": 0}
        required = list(properties)
    elif operation == "authoring":
        item_count = (
            len(contract.identifiers)
            if contract is not None
            else _prompt_item_count(prompt)
        )
        all_mark_schemes_locked = (
            contract.mark_schemes_locked
            if contract is not None
            else (
                '"mark_scheme_locked": true' in prompt
                and '"mark_scheme_locked": false' not in prompt
            )
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
                "id": {
                    "type": "string",
                    "maxLength": 64,
                    "enum": list(contract.identifiers),
                }
                if contract is not None
                else _batch_identifier_schema(prompt),
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
        if contract is not None and contract.authoring_shapes:
            variants = []
            for identifier, kind in contract.authoring_shapes:
                variant = deepcopy(question)
                fields = variant["properties"]
                fields["id"]["enum"] = [identifier]
                if kind == "multiple_choice":
                    fields["choices"].update(minItems=4, maxItems=4, uniqueItems=True)
                    fields["choices"]["items"] = {**short_text, "minLength": 1}
                    fields["correct_choice"] = {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 3,
                    }
                else:
                    fields["choices"].update(minItems=0, maxItems=0)
                    fields["correct_choice"] = {"type": "null"}
                variants.append(variant)
            question = variants[0] if len(variants) == 1 else {"anyOf": variants}
        properties = {
            "questions": {
                "type": "array",
                "items": question,
                "minItems": item_count,
                "maxItems": item_count,
            }
        }
        required = ["questions"]
    elif operation == "batch_review":
        item_count = (
            len(contract.identifiers)
            if contract is not None
            else _prompt_item_count(prompt)
        )
        review = {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "maxLength": 64,
                    "enum": list(contract.identifiers),
                }
                if contract is not None
                else _batch_identifier_schema(prompt),
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
    elif operation == "difficulty":
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
    elif operation == "open_credit":
        if contract is None:
            raise ValueError("semantic credit schema requires owned allocations")
        allocations = contract.credit_allocations
        criterion = {
            "type": "object",
            "properties": {
                "criterion_id": {
                    "type": "string",
                    "enum": [row[0] for row in allocations],
                },
                "decision": {
                    "type": "string",
                    "enum": ["supported", "unsupported", "uncertain"],
                },
                "answer_quote": {"type": "string", "maxLength": 2400},
                "scheme_quote": {"type": "string", "maxLength": 2400},
                "point_index": {
                    "type": "integer",
                    "enum": list(dict.fromkeys(row[1] for row in allocations)),
                },
                "marks": {
                    "type": "integer",
                    "enum": list(dict.fromkeys(row[2] for row in allocations)),
                },
            },
            "required": [
                "criterion_id",
                "decision",
                "answer_quote",
                "scheme_quote",
                "point_index",
                "marks",
            ],
            "additionalProperties": False,
        }
        properties = {
            "criteria": {
                "type": "array",
                "items": criterion,
                "minItems": len(allocations),
                "maxItems": len(allocations),
            },
            "issues": text_list,
            "advisory_conflicts": text_list,
        }
        required = ["criteria", "issues", "advisory_conflicts"]
    elif operation == "review":
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
    elif operation == "edexcel":
        immutable_marking = (
            contract.immutable_marking
            if contract is not None
            else "VERIFIED MARKING IS IMMUTABLE" in prompt
        )
        if immutable_marking:
            part_count = (
                contract.part_count
                if contract is not None
                else _edexcel_part_count(prompt)
            )
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
    elif operation == "aqa_cs":
        compact = (
            contract.immutable_marking
            if contract is not None
            else "VERIFIED MARKING IS IMMUTABLE" in prompt
        )
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
            (0 if contract.scenario_only else (contract.part_count if compact else 8))
            if contract is not None
            else (
                0
                if "Do not repeat, rewrite or answer the parts" in prompt
                else (_aqa_cs_part_count(prompt) if compact else 8)
            )
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


def _prompt_batch_items(prompt: str) -> list[object]:
    # Real batch declarations start a line. A quoted candidate may contain a
    # different marker; it must not override the enclosing review's identifiers.
    marker = re.search(r"(?m)^(?:BLUEPRINT_DATA|REVIEW_DATA)=\s*", prompt)
    if marker is None:
        marker = re.search(r"(?:BLUEPRINT_DATA|REVIEW_DATA)=\s*", prompt)
    if marker is None:
        return []
    try:
        items = json.JSONDecoder().raw_decode(prompt[marker.end() :])[0]
    except ValueError:
        return []
    return items if isinstance(items, list) else []


def _prompt_item_identifiers(prompt: str) -> list[str]:
    items = _prompt_batch_items(prompt)
    if items or any(marker in prompt for marker in ("BLUEPRINT_DATA=", "REVIEW_DATA=")):
        return list(
            dict.fromkeys(
                item["id"]
                for item in items
                if isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and re.fullmatch(r"\d+/\d+/\d+", item["id"])
            )
        )
    return list(dict.fromkeys(re.findall(r'"id"\s*:\s*"(\d+/\d+/\d+)"', prompt)))


def _batch_identifier_schema(prompt: str) -> dict[str, object]:
    result: dict[str, object] = {"type": "string", "maxLength": 64}
    identifiers = _prompt_item_identifiers(prompt)
    if identifiers:
        result["enum"] = identifiers
    return result


# Derive the exact batch cardinality already declared in prompt data.
#
# Ollama's grammar follows the supplied schema literally. Leaving a broad
# one-to-six range let otherwise capable local models stop after the first
# object in a multi-item batch, wasting several minutes on retries. The
# blueprint identifiers are generated by this process and occur once per
# requested item, so they give the required batch size.
def _prompt_item_count(prompt: str) -> int:

    count = len(_prompt_item_identifiers(prompt))
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
