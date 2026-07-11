from __future__ import annotations

import json
import re
from typing import Any

from Backend.Core.events import emit_progress


class HostedLLMClient:
    def __init__(self, *, provider: str, model: str, api_key: str) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key

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
        model, tokenizer = load(self.model)
        response = generate(model, tokenizer, prompt=prompt, max_tokens=4096, verbose=False)
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
            raw = json.loads(response.read().decode("utf-8"))
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
            raw = json.loads(response.read().decode("utf-8"))
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


def urllib_request(url: str, data: bytes, headers: dict[str, str]) -> Any:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        return urllib.request.urlopen(request, timeout=180)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Provider request failed: {error.code} {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach provider API: {error}") from error


def parse_json_object(text: str) -> dict[str, object]:
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


def _openai_output_text(raw: dict[str, object]) -> str:
    chunks: list[str] = []
    for item in raw.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                chunks.append(str(content.get("text", "")))
    return "".join(chunks)
