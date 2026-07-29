from __future__ import annotations

import json
import re
import threading
import time
from typing import Any

from Backend.Core.events import emit_progress


class HostedLLMClient:
    def __init__(self, *, provider: str, model: str, api_key: str) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self._apple_model: Any | None = None
        self._apple_tokenizer: Any | None = None
        self._apple_lock = threading.Lock()

    @property
    def supports_parallel_generation(self) -> bool:
        """Whether independent prompts may safely share this client."""

        return self.provider in {"openai", "anthropic"}

    def generate_json(self, prompt: str) -> dict[str, object]:
        if self.provider == "openai":
            return self._openai(prompt)
        if self.provider == "anthropic":
            return self._anthropic(prompt)
        if self.provider == "apple":
            return self._apple(prompt)
        raise RuntimeError(f"Unsupported provider: {self.provider}")

    def _apple(self, prompt: str) -> dict[str, object]:
        try:
            from mlx_lm import load, generate
        except ImportError:
            raise RuntimeError(
                "Apple MLX provider requires the 'mlx-lm' package.\n"
                "Install it with: pip install mlx-lm"
            ) from None
        # MLX model loading is expensive and can consume several gigabytes. Keep one
        # model per generation client, and serialize use because mlx-lm generation
        # mutates shared inference state.
        with self._apple_lock:
            if self._apple_model is None or self._apple_tokenizer is None:
                self._apple_model, self._apple_tokenizer = load(self.model)
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
        text = "".join(
            item.get("text", "")
            for item in raw_dict.get("content", [])
            if isinstance(item, dict) and item.get("type") == "text"
        )
        return parse_json_object(text)


def hosted_client(*, provider: str, dry_run: bool, model: str, api_key: str) -> HostedLLMClient | None:
    if provider == "ollama" or dry_run:
        return None
    emit_progress(f"Using {provider_title(provider)} model {model}", stage="provider", progress=0.04)
    return HostedLLMClient(provider=provider, model=model, api_key=api_key)


def provider_title(provider: str) -> str:
    return {"openai": "OpenAI", "anthropic": "Anthropic", "ollama": "Ollama", "apple": "Apple MLX"}.get(provider, provider.title())


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
                error.headers.get("Retry-After")
                if error.headers is not None
                else None
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
                    "Could not reach the provider API after "
                    f"{attempts} attempts."
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
        value = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model returned response with no JSON object.")
        try:
            value = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            raise ValueError("Model returned response that could not be parsed as JSON.") from None
    if not isinstance(value, dict):
        raise ValueError("Model returned JSON, but not an object.")
    return value


def _read_json_response(response: Any) -> object:
    payload = response.read(2_097_153)
    if len(payload) > 2_097_152:
        raise RuntimeError("Provider response exceeded the 2 MB limit.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Provider returned an invalid JSON response envelope.") from error


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
